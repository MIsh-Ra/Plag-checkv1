import os
import time
import json
import logging
import requests
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

from .content_fetcher import fetch_page_text, compare_snippets, analyze_coherence
from .shingling import process_text_into_chunks

logger = logging.getLogger(__name__)


class SerperClient:
    """Search client with snippets-first approach, Redis caching, ddgs fallback."""

    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY", "")
        import redis
        try:
            self.cache = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                decode_responses=True
            )
        except Exception as e:
            logger.warning(f"Redis cache unavailable: {e}")
            self.cache = None

    def search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """
        Returns list of {url, snippet, title} dicts.
        Uses snippets directly to avoid robots.txt/scraping blocks.
        """
        from app.core.config import settings
        cache_key = f"serper_snippets:{query}"
        if self.cache:
            try:
                cached = self.cache.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception:
                pass

        results = []
        if self.api_key and self.api_key not in ("", "PASTE_YOUR_KEY_HERE"):
            try:
                response = requests.post(
                    "https://google.serper.dev/search",
                    headers={'X-API-KEY': self.api_key, 'Content-Type': 'application/json'},
                    data=json.dumps({"q": query, "num": num_results}),
                    timeout=settings.SERPER_TIMEOUT
                )
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("organic", []):
                        results.append({
                            "url": item.get("link", ""),
                            "title": item.get("title", ""),
                            "snippet": item.get("snippet", ""),
                        })
            except Exception as e:
                logger.warning(f"Serper API failed: {e}")

        # DuckDuckGo fallback using ddgs (renamed from duckduckgo_search)
        if not results:
            try:
                try:
                    from ddgs import DDGS
                except ImportError:
                    from duckduckgo_search import DDGS  # legacy name
                ddgs = DDGS()
                for r in ddgs.text(query, max_results=num_results) or []:
                    results.append({
                        "url": r.get("href", ""),
                        "title": r.get("title", ""),
                        "snippet": r.get("body", ""),
                    })
            except Exception as e:
                logger.warning(f"DuckDuckGo fallback failed: {e}")

        if self.cache and results:
            try:
                self.cache.setex(cache_key, 86400, json.dumps(results))
            except Exception:
                pass
        return results


def _build_matched_char_ranges(internal_matches: List[Dict[str, Any]]) -> List[tuple]:
    """Build sorted list of (char_start, char_end) for all internal matches."""
    ranges = []
    for m in internal_matches:
        start = m.get("submitted_start_char")
        end = m.get("submitted_end_char")
        if start is not None and end is not None and end > start:
            ranges.append((start, end))
    ranges.sort()
    return ranges


def _is_chunk_internally_matched(chunk: Dict[str, Any],
                                  matched_ranges: List[tuple],
                                  overlap_threshold: float = 0.5) -> bool:
    """
    Returns True if this chunk's character range overlaps with any internal match
    by more than overlap_threshold of the chunk's length.
    Implements FR-3.1: skip chunks already caught by internal similarity.
    """
    c_start = chunk.get("char_start", 0)
    c_end = chunk.get("char_end", 0)
    chunk_len = c_end - c_start
    if chunk_len <= 0:
        return False

    for m_start, m_end in matched_ranges:
        overlap = min(c_end, m_end) - max(c_start, m_start)
        if overlap > 0 and (overlap / chunk_len) >= overlap_threshold:
            return True
    return False


def select_suspicious_chunks(text: str,
                              internal_matches: Optional[List[Dict[str, Any]]] = None,
                              page_boundaries: Optional[List[tuple]] = None,
                              page_count: int = 1,
                              max_queries: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Select chunks suitable for web search:
    - Long enough (>= MIN_CHUNK_WORDS)
    - NOT already internally matched (FR-3.1)
    - Ranked by length; top N selected
    """
    from app.core.config import settings
    if max_queries is None:
        max_queries = settings.MAX_DRAGNET_SUSPICIOUS

    # Build matched ranges from internal results for fast overlap check
    matched_ranges = _build_matched_char_ranges(internal_matches or [])

    chunks = process_text_into_chunks(text, page_boundaries=page_boundaries, page_count=page_count)
    suspicious = []

    for c in chunks:
        words = c['text'].split()
        if len(words) < settings.MIN_CHUNK_WORDS:
            continue

        # Skip chunks already caught by internal similarity (FR-3.1)
        if matched_ranges and _is_chunk_internally_matched(c, matched_ranges):
            logger.debug(f"Skipping internally-matched chunk at char {c.get('char_start')}")
            continue

        suspicious.append((len(words), c))

    # Rank by length (longer = better search target)
    suspicious.sort(key=lambda x: x[0], reverse=True)
    return [s[1] for s in suspicious[:max_queries]]


def run_dragnet(document_id: str,
                text: str,
                internal_matches: Optional[List[Dict[str, Any]]] = None,
                page_boundaries: Optional[List[tuple]] = None,
                page_count: int = 1) -> List[Dict[str, Any]]:
    """
    Orchestrator for the Web Dragnet Engine.
    Uses search result snippets directly instead of full-page fetching to avoid robots.txt blocks.
    Deduplicates matches by submitted_text so the same chunk doesn't appear multiple times.
    """
    chunks_to_search = select_suspicious_chunks(
        text,
        internal_matches=internal_matches,
        page_boundaries=page_boundaries,
        page_count=page_count
    )

    logger.info(f"Web Dragnet: selected {len(chunks_to_search)} suspicious chunks "
                f"(after filtering {len(internal_matches or [])} internal matches).")

    from app.core.config import settings
    client = SerperClient()

    # submitted_text_hash -> best match dict (dedup by source chunk)
    best_by_chunk: Dict[str, Dict[str, Any]] = {}

    for chunk_dict in chunks_to_search:
        chunk_text = chunk_dict['text']
        chunk_hash = str(hash(chunk_text[:200]))  # stable key for this chunk

        query_words = getattr(settings, 'DRAGNET_QUERY_WORDS', 25)
        query = " ".join(chunk_text.split()[:query_words])
        search_results = client.search(query)
        time.sleep(0.5)  # rate limiting

        for result in search_results:
            url = result.get("url", "")
            snippet = result.get("snippet", "")
            title = result.get("title", "")

            if not url:
                continue

            # Use snippet directly (avoids robots.txt / JS-heavy pages)
            # Only fetch the full page if the snippet is too short to compare
            source_text = snippet
            if len(snippet.split()) < 20:
                fetched = fetch_page_text(url)
                if fetched:
                    source_text = fetched[:getattr(settings, 'SNIPPET_MAX_CHARS', 2000)]

            if not source_text:
                continue

            web_threshold = getattr(settings, 'WEB_MATCH_THRESHOLD', 0.15)
            score = compare_snippets(chunk_text, source_text)

            if score > web_threshold:
                domain = urlparse(url).netloc
                match = {
                    "type": "web",
                    "url": url,
                    "domain": domain,
                    "score": score,
                    "source_title": title or domain,
                    "source_text": source_text[:getattr(settings, 'SNIPPET_MAX_CHARS', 2000)],
                    "submitted_text": chunk_text,
                    "similarity_score": round(score * 100, 2),
                    "submitted_page": chunk_dict.get("page", 1),
                    "source_page": 1,
                    "submitted_start_char": chunk_dict.get("char_start", 0),
                    "submitted_end_char": chunk_dict.get("char_end", 0),
                    "is_coherent": False,
                }

                # Keep only the highest-scoring web match per submitted chunk
                existing = best_by_chunk.get(chunk_hash)
                if existing is None or score > existing["score"]:
                    best_by_chunk[chunk_hash] = match
                    logger.debug(f"Web match: chunk@{chunk_dict.get('page')} → {url} ({score:.2f})")

    matches = list(best_by_chunk.values())
    matches = analyze_coherence(matches)

    logger.info(f"Web Dragnet: {len(matches)} unique web matches found.")
    return matches


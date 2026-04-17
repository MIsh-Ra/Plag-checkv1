import os
import time
import json
import logging
import requests
from duckduckgo_search import DDGS

from .content_fetcher import fetch_page_text, compare_snippets, analyze_coherence
from .shingling import process_text_into_chunks

logger = logging.getLogger(__name__)

class SerperClient:
    """Ported with rate limiting, Redis caching (stubbed), DuckDuckGo fallback."""
    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY", "")
        # In a real app, this would use Redis
        self.cache = {}

    def search(self, query, num_results=5):
        if query in self.cache:
            return self.cache[query]

        links = []
        if self.api_key and self.api_key != "PASTE_YOUR_KEY_HERE":
            try:
                url = "https://google.serper.dev/search"
                payload = json.dumps({"q": query, "num": num_results})
                headers = {'X-API-KEY': self.api_key, 'Content-Type': 'application/json'}
                response = requests.post(url, headers=headers, data=payload, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("organic", []):
                        links.append(item["link"])
            except Exception as e:
                logger.warning(f"Serper API failed: {e}")
        
        if not links:
            try:
                ddgs = DDGS()
                results = ddgs.text(query, max_results=num_results)
                if results:
                    for r in results:
                        links.append(r['href'])
            except Exception as e:
                logger.warning(f"DuckDuckGo fallback failed: {e}")
        
        unique_links = list(set(links))
        self.cache[query] = unique_links
        return unique_links


def select_suspicious_chunks(text, internal_matches=None, max_queries=15):
    """4-layer filter to minimize API calls."""
    chunks = process_text_into_chunks(text)
    suspicious = []
    
    for c in chunks:
        # Filter 1: Skip if already internally matched
        # (Assuming we have that data)
        
        # Filter 2: Skip short/trivial chunks (<30 words)
        words = c['text'].split()
        if len(words) < 30:
            continue
            
        # Filter 3: Vocabulary diversity
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio > 0.85:
            # likely original
            continue
            
        # Filter 4: Density scoring
        density_score = 1.0 - unique_ratio
        suspicious.append((density_score, c['text']))
        
    # Rank by Suspiciousness
    suspicious.sort(key=lambda x: x[0], reverse=True)
    return [s[1] for s in suspicious[:max_queries]]


def run_dragnet(document_id, text, internal_matches=None):
    """Orchestrator for the Web Dragnet Engine."""
    chunks_to_search = select_suspicious_chunks(text, internal_matches)
    
    logger.info(f"Web Dragnet: selected {len(chunks_to_search)} suspicious chunks.")
    
    client = SerperClient()
    # Map each chunk to its discovered URLs
    chunk_url_pairs = []
    
    for chunk in chunks_to_search:
        # Use first 25 words for query
        query = " ".join(chunk.split()[:25])
        urls = client.search(query)
        for url in urls:
            chunk_url_pairs.append((chunk, url))
        time.sleep(1) # Rate limiting
        
    # Deduplicate by URL
    seen_urls = {}
    for chunk, url in chunk_url_pairs:
        if url not in seen_urls:
            seen_urls[url] = chunk  # Keep the first chunk that found this URL
            
    logger.info(f"Web Dragnet: Checking {len(seen_urls)} unique URLs.")
    
    matches = []
    for url, originating_chunk in seen_urls.items():
        web_content = fetch_page_text(url)
        if not web_content:
            continue
            
        # Compare the SPECIFIC CHUNK that led to this URL, not the entire document
        score = compare_snippets(originating_chunk, web_content)
        if score > 0.15:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            matches.append({
                "type": "web",
                "url": url,
                "domain": domain,
                "score": score,
                "source_title": domain,
                "source_text": web_content[:500], # snippet
                "submitted_text": originating_chunk,
                "similarity_score": score * 100,
                "submitted_page": 1,
                "source_page": 1,
                "is_coherent": False
            })
            
    matches = analyze_coherence(matches)
    return matches

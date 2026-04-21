import requests
from bs4 import BeautifulSoup
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class GrobidClient:
    def __init__(self, host: str = "http://localhost:8070"):
        self.api_url = f"{host}/api/processFulltextDocument"

    def process_pdf(self, file_bytes: bytes) -> Dict[str, Any]:
        """
        Send PDF bytes to Grobid and parse XML response.
        Returns structured data including page_texts with per-page text + char offsets.
        """
        try:
            files = {'input': file_bytes}
            from app.core.config import settings
            response = requests.post(self.api_url, files=files, timeout=settings.GROBID_TIMEOUT)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'xml')

            # Extract basic metadata
            title_node = soup.find('title', type='main')
            title = title_node.get_text(strip=True) if title_node else "Unknown Title"

            # Abstract
            abstract_node = soup.find('abstract') or soup.find('div', type='abstract')
            abstract = abstract_node.get_text(strip=True) if abstract_node else ""

            # Extract references
            references = []
            back = soup.find('back')
            if back:
                list_bibl = back.find('listBibl')
                if list_bibl:
                    for bibl in list_bibl.find_all('biblStruct'):
                        ref_title_node = bibl.find('title', level='m') or bibl.find('title', level='a')
                        ref_title = ref_title_node.get_text(strip=True) if ref_title_node else "Unknown Reference"
                        references.append({
                            "raw": bibl.get_text(strip=True),
                            "title": ref_title
                        })

            # ── Page-boundary-aware text extraction ──────────────────────────────
            # Grobid emits <pb n="X"> elements at page breaks within the body.
            # We walk all body content and bucket text into pages.
            body = soup.find('body')
            page_bucket: Dict[int, List[str]] = {}  # page_num -> [text chunks]
            current_page = 1

            if body:
                # Walk every element in document order
                for elem in body.descendants:
                    # Page-break marker
                    if elem.name == 'pb':
                        try:
                            n = int(elem.get('n', current_page + 1))
                            current_page = n
                        except (ValueError, TypeError):
                            current_page += 1
                        continue

                    # Collect text from leaf paragraph/head elements
                    if elem.name in ('p', 'head', 'note') and elem.parent.name not in ('p',):
                        txt = elem.get_text(separator=' ', strip=True)
                        if txt:
                            if current_page not in page_bucket:
                                page_bucket[current_page] = []
                            page_bucket[current_page].append(txt)

            # If Grobid gave us no <pb> markers, fall back to section-based buckets
            if not page_bucket:
                sections = []
                if body:
                    for div in body.find_all('div', recursive=False):
                        head = div.find('head')
                        content = [p.get_text(strip=True) for p in div.find_all('p', recursive=False) if p.get_text(strip=True)]
                        if content:
                            sections.append({
                                "heading": head.get_text(strip=True) if head else "Untitled Section",
                                "text": "\n".join(content)
                            })
                # Single-page fallback
                all_text = "\n\n".join(s["text"] for s in sections)
                page_bucket = {1: [all_text]} if all_text else {}
            else:
                # Build sections list from page buckets for compatibility
                sections = []
                for pnum in sorted(page_bucket.keys()):
                    sections.append({
                        "heading": f"Page {pnum}",
                        "text": "\n".join(page_bucket[pnum])
                    })

            # Build page_texts with cumulative char offsets
            page_texts = []
            page_boundaries = []
            cursor = 0
            separator = "\n\n"
            sep_len = len(separator)

            for pnum in sorted(page_bucket.keys()):
                page_text = "\n".join(page_bucket[pnum])
                char_start = cursor
                char_end = cursor + len(page_text)
                page_texts.append({
                    "page": pnum,
                    "text": page_text,
                    "char_start": char_start,
                    "char_end": char_end,
                })
                page_boundaries.append((char_start, char_end, pnum))
                cursor = char_end + sep_len

            body_text = separator.join(pt["text"] for pt in page_texts)

            # Confidence estimation
            confidence = 1.0
            if len(body_text) < 100:
                confidence = 0.3
            elif len(sections) < 2:
                confidence = 0.6

            # Get actual page count from <pb> elements
            page_breaks = soup.find_all('pb')
            actual_page_count = max(len(page_texts), max(1, len(page_breaks)) if page_breaks else 1)

            return {
                "title": title,
                "abstract": abstract,
                "sections": sections,
                "references": references,
                "body_text": body_text,
                "page_texts": page_texts,
                "page_boundaries": page_boundaries,
                "page_count": actual_page_count,
                "confidence": confidence,
            }

        except Exception as e:
            logger.error(f"Grobid processing error: {e}")
            raise RuntimeError(f"Grobid failed: {e}")

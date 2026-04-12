import requests
from bs4 import BeautifulSoup
import logging
from typing import Dict, Any, List

# Configure logger
logger = logging.getLogger(__name__)

class GrobidClient:
    def __init__(self, host: str = "http://localhost:8070"):
        self.api_url = f"{host}/api/processFulltextDocument"

    def process_pdf(self, file_bytes: bytes) -> Dict[str, Any]:
        """
        Send PDF bytes to Grobid at http://localhost:8070 and parse XML response.
        """
        try:
            files = {'input': file_bytes}
            response = requests.post(self.api_url, files=files)
            response.raise_for_status()
            
            # Parse XML response
            soup = BeautifulSoup(response.content, 'xml')
            
            # Extract basic metadata
            title_node = soup.find('title', type='main')
            title = title_node.get_text(strip=True) if title_node else "Unknown Title"
            
            # Robust abstract finding (TEI can have <abstract> or <div type="abstract">)
            abstract_node = soup.find('abstract') or soup.find('div', type='abstract')
            abstract = abstract_node.get_text(strip=True) if abstract_node else ""
            
            # Extract body text sections
            sections = []
            body = soup.find('body')
            if body:
                for div in body.find_all('div'):
                    head = div.find('head')
                    content = []
                    for p in div.find_all('p'):
                        content.append(p.get_text(strip=True))
                    
                    if content:
                        sections.append({
                            "heading": head.get_text(strip=True) if head else "Untitled Section",
                            "text": "\n".join(content)
                        })

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

            # Estimate confidence from output quality
            body_text = " ".join(s["text"] for s in sections)
            confidence = 1.0
            if len(body_text) < 100:  # Very little text extracted
                confidence = 0.3
            elif len(sections) < 2:
                confidence = 0.6

            return {
                "title": title,
                "abstract": abstract,
                "sections": sections,
                "references": references,
                "body_text": body_text,
                "page_count": len(sections),  # Estimate from section count
                "confidence": confidence
            }

        except Exception as e:
            logger.error(f"Grobid processing error: {e}")
            raise RuntimeError(f"Grobid failed: {e}")

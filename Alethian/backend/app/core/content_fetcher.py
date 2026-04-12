import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

from sentence_transformers import SentenceTransformer, util as st_util

# Load model independently — no cross-module dependency
try:
    _model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception:
    _model = None

def fetch_page_text(url, timeout=10):
    """Fetches and cleans HTML from a URL, with timeout."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        if "application/pdf" in response.headers.get('Content-Type', ''):
            return ""
        soup = BeautifulSoup(response.content, 'html.parser')
        # Cleanup
        for junk in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            junk.extract()
        text = soup.get_text()
        return '\n'.join(chunk for line in text.splitlines() for chunk in [line.strip()] if chunk)
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return ""

def compare_snippets(submitted_text, source_text):
    """Reuses sentence-transformers model from similarity module locally."""
    if not submitted_text or not source_text or not _model:
        return 0.0
    try:
        if len(source_text) < 20: 
            return 0.0
        emb1 = _model.encode(submitted_text, convert_to_tensor=True)
        emb2 = _model.encode(source_text, convert_to_tensor=True)
        score = st_util.cos_sim(emb1, emb2).item()
        return max(0.0, score)
    except Exception as e:
        logger.error(f"Error comparing snippets: {e}")
        return 0.0

def analyze_coherence(matches):
    """Groups matches by domain, flags ≥3 from same domain."""
    domain_counts = {}
    for m in matches:
        domain = urlparse(m['url']).netloc
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
    
    for m in matches:
        domain = urlparse(m['url']).netloc
        if domain_counts[domain] >= 3:
            m['is_coherent'] = True
        else:
            m['is_coherent'] = False
    return matches

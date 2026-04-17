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
    """Compare a submitted chunk against the best-matching window in a web page.
    
    Splits the source_text into overlapping ~200-word windows and returns the
    highest cosine similarity found. This prevents score dilution when comparing
    a small chunk against a large page.
    """
    if not submitted_text or not source_text or not _model:
        return 0.0
    try:
        if len(source_text) < 20: 
            return 0.0
        
        emb1 = _model.encode(submitted_text, convert_to_tensor=True)
        
        # Split source into overlapping windows for fair comparison
        source_words = source_text.split()
        window_size = 200
        step = 100
        
        if len(source_words) <= window_size:
            # Short page: compare directly
            emb2 = _model.encode(source_text, convert_to_tensor=True)
            return max(0.0, st_util.cos_sim(emb1, emb2).item())
        
        best_score = 0.0
        for i in range(0, len(source_words) - window_size + 1, step):
            window = " ".join(source_words[i:i + window_size])
            emb2 = _model.encode(window, convert_to_tensor=True)
            score = st_util.cos_sim(emb1, emb2).item()
            if score > best_score:
                best_score = score
        
        return max(0.0, best_score)
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

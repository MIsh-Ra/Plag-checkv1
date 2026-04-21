import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

from sentence_transformers import util as st_util
from app.core.embeddings import get_model

def fetch_page_text(url, timeout=None):
    """Fetches and cleans HTML from a URL, with robots.txt check and timeout."""
    from app.core.config import settings
    if timeout is None:
        timeout = settings.FETCHER_TIMEOUT
    headers = {'User-Agent': 'Alethian-Search-Bot/1.0'}
    try:
        from urllib.robotparser import RobotFileParser
        
        parsed_url = urlparse(url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots_url)
        try:
            rp.read()
            if not rp.can_fetch(headers['User-Agent'], url):
                logger.info(f"Blocked by robots.txt: {url}")
                return ""
        except Exception as e:
            pass # Ignore robots parser failure

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
    highest cosine similarity found via batch embedding.
    """
    _model = get_model()
    if not submitted_text or not source_text or _model is None:
        return 0.0
    try:
        from app.core.config import settings
        from app.core.embeddings import generate_embeddings_batch
        emb1 = _model.encode(submitted_text, convert_to_tensor=True)
        
        if len(source_text) < settings.MIN_SOURCE_TEXT_LENGTH: 
            return 0.0
        
        # Split source into overlapping windows for fair comparison
        source_words = source_text.split()
        window_size = settings.FETCHER_WINDOW_SIZE
        step = settings.FETCHER_WINDOW_STEP
        
        if len(source_words) <= window_size:
            # Short page: compare directly
            emb2 = _model.encode(source_text, convert_to_tensor=True)
            return max(0.0, st_util.cos_sim(emb1, emb2).item())
        
        windows = []
        for i in range(0, len(source_words) - window_size + 1, step):
            window = " ".join(source_words[i:i + window_size])
            windows.append(window)

        if not windows:
             return 0.0
             
        batch_embs = generate_embeddings_batch(windows)
        
        best_score = 0.0
        for emb2_list in batch_embs:
            # convert back to tensor for cosine similarity
            import torch
            emb2 = torch.tensor(emb2_list)
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

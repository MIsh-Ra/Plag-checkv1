import re
from app.core.embeddings import generate_embeddings_batch

def create_sliding_windows(text, window_size=None):
    """Reuses sliding-window approach from backup/text_processor.py"""
    if not text:
        return []

    from app.core.config import settings
    if window_size is None:
        window_size = getattr(settings, 'SHINGLING_WINDOW_SENTENCES', 5)

    text = " ".join(text.split())
    # Split text by punctuation boundaries
    sentences = re.split(r'(?<=[.!?]) +', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    windows = []
    
    if len(sentences) <= window_size:
        return [text] if text else []

    for i in range(len(sentences) - window_size + 1):
        chunk = " ".join(sentences[i:i + window_size])
        windows.append(chunk)
        
    return windows

def process_text_into_chunks(text, page_boundaries=None, page_count=1):
    """Full pipeline to chunk text and generate features.
    
    Args:
        text: Full document text
        page_boundaries: Optional list of (start_char, end_char, page_num) tuples
        page_count: Fallback page count to empty boundary case
    """
    windows = create_sliding_windows(text)
    
    # Pre-compute window metadata (offsets, pages) before batch embedding
    window_metadata = []
    search_offset = 0
    for w in windows:
        page = 1
        char_start = text.find(w, search_offset)
        if char_start == -1:
            # Edge case: window text was normalised differently than source.
            # Fall back to searching from the beginning.
            char_start = text.find(w)
        if char_start == -1:
            continue  # Skip windows that can't be located in source text
        char_end = char_start + len(w)
        search_offset = char_start + 1  # Advance past this match
        
        if page_boundaries:
            for start, end, pnum in page_boundaries:
                if start <= char_start < end:
                    page = pnum
                    break
        else:
            from app.core.config import settings
            chars_per_page = getattr(settings, 'SHINGLING_CHARS_PER_PAGE_ESTIMATE', 4000)
            page = min(page_count, (char_start // chars_per_page) + 1)
                    
        window_metadata.append({
            "text": w,
            "page": page,
            "char_start": char_start,
            "char_end": char_end
        })
    
    # Batch encode all windows at once (~3-10x faster)
    if not window_metadata:
        return []
    
    texts = [wm["text"] for wm in window_metadata]
    embeddings = generate_embeddings_batch(texts)
    
    results = []
    for wm, emb in zip(window_metadata, embeddings):
        wm["embedding"] = emb
        results.append(wm)
    
    return results

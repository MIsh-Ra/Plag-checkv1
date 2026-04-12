import re
from sentence_transformers import SentenceTransformer

# Load embedding model once per worker
try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception as e:
    model = None
    print(f"Failed to load SentenceTransformer: {e}")

def create_sliding_windows(text, window_size=3):
    """Reuses sliding-window approach from backup/text_processor.py"""
    if not text:
        return []

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

def generate_embedding(text):
    """Generates sentence embedding using all-MiniLM-L6-v2."""
    if not model:
        raise RuntimeError("Sentence model is not loaded.")
    return model.encode(text, convert_to_tensor=False).tolist()

def process_text_into_chunks(text, page_boundaries=None, page_count=1):
    """Full pipeline to chunk text and generate features.
    
    Args:
        text: Full document text
        page_boundaries: Optional list of (start_char, end_char, page_num) tuples
        page_count: Fallback page count to empty boundary case
    """
    windows = create_sliding_windows(text)
    results = []
    for w in windows:
        page = 1
        char_start = text.find(w)
        char_end = char_start + len(w)
        
        if page_boundaries:
            for start, end, pnum in page_boundaries:
                if start <= char_start < end:
                    page = pnum
                    break
        else:
            page = min(page_count, (char_start // 2500) + 1)
                    
        results.append({
            "text": w,
            "embedding": generate_embedding(w),
            "page": page,
            "char_start": char_start,
            "char_end": char_end
        })
    return results

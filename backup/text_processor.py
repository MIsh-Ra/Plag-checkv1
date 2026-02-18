import re

def create_sliding_windows(text, window_size=3):
    if not text:
        return []

    text = " ".join(text.split())
    sentences = re.split(r'(?<=[.!?]) +', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    windows = []
    
    if len(sentences) <= window_size:
        return [text]

    for i in range(len(sentences) - window_size + 1):
        chunk = " ".join(sentences[i:i + window_size])
        windows.append(chunk)
        
    return windows

def extract_search_query(text_chunk):
    words = text_chunk.split()
    query = " ".join(words[:25])
    return query

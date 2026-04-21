"""
Shared SentenceTransformer singleton.
Loaded lazily on first use to avoid import-time crashes (F-15)
and to work safely with Celery pre-fork workers (F-47).
"""
import threading
import logging

logger = logging.getLogger(__name__)

_model = None
_lock = threading.Lock()

def get_model():
    """Returns the shared SentenceTransformer instance, loading it on first call."""
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                from sentence_transformers import SentenceTransformer
                logger.info("Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
                _model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Model loaded successfully.")
    return _model

def generate_embedding(text):
    """Generate embedding for a single text string."""
    model = get_model()
    return model.encode(text, convert_to_tensor=False).tolist()

def generate_embeddings_batch(texts):
    """Generate embeddings for a list of texts (batched, ~3-10x faster)."""
    model = get_model()
    from app.core.config import settings
    return model.encode(texts, batch_size=settings.EMBEDDING_BATCH_SIZE, convert_to_tensor=False).tolist()

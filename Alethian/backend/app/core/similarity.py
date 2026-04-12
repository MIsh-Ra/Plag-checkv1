import os
import uuid
import redis
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from sentence_transformers import util
import difflib

from .shingling import process_text_into_chunks

logger = logging.getLogger(__name__)

# Legacy RedisLSHIndex Removed in Phase 4. Using Qdrant Exact Searches instead.

class QdrantManager:
    def __init__(self, host=None, port=6333):
        self.host = host or os.getenv("QDRANT_HOST", "localhost")
        self.port = int(os.getenv("QDRANT_PORT", port))
        self.client = QdrantClient(host=self.host, port=self.port)
        self.collection_name = "document_chunks"
        self._ensure_collection()
    
    def _ensure_collection(self):
        try:
            self.client.get_collection(self.collection_name)
        except Exception:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )

    def add_chunks(self, document_id, chunks):
        points = []
        for c in chunks:
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=c["embedding"],
                    payload={"document_id": document_id, "text": c["text"], "chunk_id": c.get("chunk_id", str(uuid.uuid4()))}
                )
            )
        if points:
            self.client.upsert(collection_name=self.collection_name, points=points)

    def search_exact(self, embedding, limit=5, score_threshold=0.95):
        """High-threshold search for exact matches."""
        return self.client.search(
            collection_name=self.collection_name,
            query_vector=embedding,
            limit=limit,
            score_threshold=score_threshold
        )
    
    def search_semantic(self, embedding, limit=5, score_threshold=0.85):
        """Lower-threshold search for paraphrase matches."""
        return self.client.search(
            collection_name=self.collection_name,
            query_vector=embedding,
            limit=limit,
            score_threshold=score_threshold
        )

# Remove _lsh and _chunk_store globals
_qdrant = QdrantManager()

def deduplicate(matches):
    unique = []
    seen = set()
    for m in matches:
        key = f"{m['submitted_start_char']}-{m['source_document_id']}"
        if key not in seen:
            seen.add(key)
            unique.append(m)
    return unique

def run_similarity(document_id, text, db_session, page_boundaries=None, page_count=1):
    chunks = process_text_into_chunks(text, page_boundaries, page_count=page_count)
    
    matched_results = []
    
    for chunk in chunks:
        # 1. Exact match search (high threshold)
        exact_matches = _qdrant.search_exact(chunk["embedding"])
        for m in exact_matches:
            payload = m.payload
            if payload and payload.get("document_id") != document_id:
                # We can skip SequenceMatcher here if threshold is high enough, but let's double check it purely
                sm = difflib.SequenceMatcher(None, chunk["text"], payload.get("text", ""))
                matched_results.append({
                    "type": "internal_exact" if sm.ratio() > 0.9 else "internal_paraphrase",
                    "submitted_text": chunk["text"],
                    "source_text": payload.get("text", ""),
                    "submitted_page": chunk["page"],        # ← real page
                    "source_page": payload.get("page", 1),  # ← stored page
                    "submitted_start_char": chunk["char_start"],
                    "submitted_end_char": chunk["char_end"],
                    "similarity_score": m.score * 100,
                    "source_document_id": payload.get("document_id"),
                    "source_title": payload.get("title", "Archive Document")
                })
        
        # 2. Semantic search (lower threshold, excludes already-matched)
        semantic_matches = _qdrant.search_semantic(chunk["embedding"])
        for m in semantic_matches:
             payload = m.payload
             if payload and payload.get("document_id") != document_id:
                 matched_results.append({
                     "type": "internal_paraphrase",
                     "submitted_text": chunk["text"],
                     "source_text": payload.get("text", ""),
                     "submitted_page": chunk["page"],
                     "source_page": payload.get("page", 1),
                     "submitted_start_char": chunk["char_start"],
                     "submitted_end_char": chunk["char_end"],
                     "similarity_score": m.score * 100,
                     "source_document_id": payload.get("document_id"),
                     "source_title": payload.get("title", "Archive Document")
                 })
                 
    return deduplicate(matched_results)

def index_document(document_id, text, title="Unknown Document", page_boundaries=None, page_count=1):
    chunks = process_text_into_chunks(text, page_boundaries, page_count=page_count)
    points = []
    for c in chunks:
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=c["embedding"],
            payload={
                "document_id": document_id,
                "text": c["text"],
                "title": title,
                "page": c["page"]
            }
        ))
    if points:
        _qdrant.client.upsert(collection_name=_qdrant.collection_name, points=points)
    
    return True

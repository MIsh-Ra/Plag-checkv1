from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.admin import AdminConfigResponse, AdminConfigUpdate, SimilarityThresholds, WebDragnetConfig, ApiStatus, ArchiveStats
from app.core.config import settings
from app.db.models import Document, Match

router = APIRouter()

# Global mock for config
_memory_config = {
    "similarity_thresholds": {
        "minhash_jaccard": 0.5,
        "semantic_cosine": 0.85,
        "web_match": 0.7
    },
    "web_dragnet": {
        "enabled": True,
        "queries_per_document": 20,
        "rate_limit_rpm": 60
    }
}

from app.api.dependencies import require_admin
from app.db.models import User

@router.get("/config", response_model=AdminConfigResponse)
def get_config(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    # Calculate stats dynamically
    doc_count = db.query(Document).count()
    return AdminConfigResponse(
        similarity_thresholds=SimilarityThresholds(**_memory_config["similarity_thresholds"]),
        web_dragnet=WebDragnetConfig(**_memory_config["web_dragnet"]),
        api_status=ApiStatus(serper="ok" if settings.SERPER_API_KEY else "missing_key"),
        archive_stats=ArchiveStats(
            total_documents=doc_count,
            total_shingles=doc_count * 125, # Dummy assumption
            last_indexed="Recently"
        )
    )

@router.patch("/config")
def update_config(update: AdminConfigUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    if update.similarity_thresholds:
        _memory_config["similarity_thresholds"]["semantic_cosine"] = update.similarity_thresholds.semantic_cosine
        _memory_config["similarity_thresholds"]["minhash_jaccard"] = update.similarity_thresholds.minhash_jaccard
        _memory_config["similarity_thresholds"]["web_match"] = update.similarity_thresholds.web_match
    return {"message": "Configuration updated"}

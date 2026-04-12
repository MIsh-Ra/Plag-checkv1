from pydantic import BaseModel, Field

class SimilarityThresholds(BaseModel):
    minhash_jaccard: float = Field(default=0.5, ge=0.0, le=1.0)
    semantic_cosine: float = Field(default=0.85, ge=0.0, le=1.0)
    web_match: float = Field(default=0.7, ge=0.0, le=1.0)

class WebDragnetConfig(BaseModel):
    enabled: bool = True
    queries_per_document: int = Field(default=20, ge=1, le=100)
    rate_limit_rpm: int = Field(default=60, ge=1)

class ApiStatus(BaseModel):
    serper: str = "ok"
    
class ArchiveStats(BaseModel):
    total_documents: int = 0
    total_shingles: int = 0
    last_indexed: str = ""

class AdminConfigResponse(BaseModel):
    similarity_thresholds: SimilarityThresholds
    web_dragnet: WebDragnetConfig
    api_status: ApiStatus
    archive_stats: ArchiveStats

class AdminConfigUpdate(BaseModel):
    serper_api_key: str = None
    similarity_thresholds: SimilarityThresholds = None

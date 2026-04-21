from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from .match import MatchResponse, SourceResponse

class SummaryStats(BaseModel):
    total_matches: int = 0
    internal_exact: int = 0
    internal_paraphrase: int = 0
    web_matches: int = 0
    unique_sources: int = 0
    avg_match_length_words: float = 0
    longest_match_words: int = 0
    longest_match_page: Optional[int] = None
    pages_with_matches: int = 0
    total_pages: int = 0
    excluded_matches: int = 0
    coherent_domains: List[str] = []

class HeatmapPageResponse(BaseModel):
    id: Optional[str] = None          # Optional — not present in inline serialization
    page_number: int
    density_score: float
    match_density: Optional[float] = None   # Frontend alias for density_score
    internal_density: Optional[float] = None
    web_density: Optional[float] = None
    color: Optional[str] = None
    match_count: Optional[int] = None
    dominant_type: Optional[str] = None
    hotspots: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

class PageDistribution(BaseModel):
    page: int
    internal_exact: int = 0
    internal_paraphrase: int = 0
    web: int = 0

class SourceBreakdownItem(BaseModel):
    name: str
    value: int

class Scores(BaseModel):
    originality_score: float
    similarity_score: float
    risk_level: str
    internal_contribution: float
    web_contribution: float

class ReviewInfo(BaseModel):
    status: Optional[str] = "unreviewed"
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    faculty_notes: Optional[str] = None
    verdict: Optional[str] = None

class ReportBase(BaseModel):
    score: Optional[float] = None
    risk_level: Optional[str] = None
    status: str = "unreviewed"

class ReportResponse(ReportBase):
    id: str
    document_id: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class FullReportResponse(BaseModel):
    document_id: str
    document_title: Optional[str] = None
    document_author: Optional[str] = None
    document_text: Optional[str] = None
    page_texts: Optional[List[Dict[str, Any]]] = []   # Per-page text with char offsets
    page_count: Optional[int] = None
    analyzed_at: datetime
    processing_time_seconds: Optional[int] = None

    scores: Scores
    summary_stats: SummaryStats
    source_breakdown: List[SourceBreakdownItem] = []
    sources: List[SourceResponse] = []
    matches: List[MatchResponse] = []
    heatmap: List[HeatmapPageResponse] = []
    page_distribution: List[Dict[str, Any]] = []
    review: ReviewInfo

    model_config = ConfigDict(from_attributes=True)
    
class ReportReviewRequest(BaseModel):
    verdict: str
    faculty_notes: Optional[str] = None
    digital_signature: str

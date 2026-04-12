from pydantic import BaseModel, ConfigDict
from typing import Optional, List

class SourceBase(BaseModel):
    url: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    type: Optional[str] = None
    domain: Optional[str] = None
    document_id: Optional[str] = None
    coverage_percent: Optional[float] = None
    match_count: Optional[int] = None
    pages_affected: Optional[List[int]] = None
    is_coherent_source: Optional[bool] = False

class SourceResponse(SourceBase):
    id: str
    model_config = ConfigDict(from_attributes=True)

class MatchBase(BaseModel):
    similarity: float
    submitted_text: str
    source_text: str
    is_excluded: bool
    comment: Optional[str] = None
    
    type: Optional[str] = None
    submitted_page: Optional[int] = None
    source_page: Optional[int] = None
    submitted_start_char: Optional[int] = None
    submitted_end_char: Optional[int] = None
    match_length_words: Optional[int] = None
    exclude_reason: Optional[str] = None
    color_code: Optional[str] = None

class MatchExcludeRequest(BaseModel):
    is_excluded: bool
    reason: Optional[str] = None

class MatchCommentRequest(BaseModel):
    comment: str

class MatchResponse(MatchBase):
    id: str
    report_id: str
    source: Optional[SourceResponse] = None

    model_config = ConfigDict(from_attributes=True)
    
class MatchSummary(BaseModel):
    id: str
    similarity: float

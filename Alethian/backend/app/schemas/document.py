from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.db.models import DocumentStatus

class DocumentBase(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    course_id: Optional[str] = None

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: str
    filename: str
    upload_date: datetime
    status: DocumentStatus
    is_archived: bool = False
    score: Optional[float] = None
    page_count: Optional[int] = None
    risk_level: Optional[str] = None
    originality_score: Optional[float] = None
    meta_data: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)

class DocumentDetailResponse(DocumentResponse):
    pass

class DocumentListResponse(BaseModel):
    total: int
    items: List[DocumentResponse]

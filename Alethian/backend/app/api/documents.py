from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import datetime
import json
import os
import sys
import re
import tempfile
import logging

logger = logging.getLogger(__name__)

from app.db.session import get_db
from app.db.models import Document, DocumentStatus
from app.schemas.document import DocumentListResponse, DocumentDetailResponse, DocumentResponse

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections = {}

    async def connect(self, websocket: WebSocket, document_id: str):
        await websocket.accept()
        if document_id not in self.active_connections:
            self.active_connections[document_id] = []
        self.active_connections[document_id].append(websocket)

    def disconnect(self, websocket: WebSocket, document_id: str):
        if document_id in self.active_connections:
            if websocket in self.active_connections[document_id]:
                self.active_connections[document_id].remove(websocket)

    async def broadcast_status(self, document_id: str, data: dict):
        if document_id in self.active_connections:
            for connection in self.active_connections[document_id]:
                try:
                    await connection.send_json(data)
                except:
                    pass

manager = ConnectionManager()

from app.api.dependencies import get_current_user
from app.db.models import User

from app.core.config import settings
from pathlib import Path

from app.core.rate_limit import limiter
from fastapi import Request

@router.post("/upload", response_model=DocumentResponse)
@limiter.limit("10/minute")
async def upload_document(
    request: Request,
    file: UploadFile = File(...), 
    course_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        content = await file.read()
        
        size_mb = len(content) / (1024 * 1024)
        if hasattr(settings, 'MAX_UPLOAD_SIZE_MB') and size_mb > getattr(settings, 'MAX_UPLOAD_SIZE_MB', 100):
            raise HTTPException(status_code=413, detail=f"File too large: {size_mb:.1f}MB")

        safe_name = re.sub(r'[^\w\-.]', '_', file.filename.split('/')[-1].split('\\')[-1])
        # Use a persistent upload directory shared between API and Celery worker
        if settings.UPLOAD_DIR:
            upload_dir = Path(settings.UPLOAD_DIR)
        else:
            upload_dir = Path(__file__).resolve().parents[3] / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = str(upload_dir / f"{uuid.uuid4()}_{safe_name}")
        with open(file_path, "wb") as f:
            f.write(content)
            
        doc_id = str(uuid.uuid4())
        new_doc = Document(
            id=doc_id,
            title="Unknown Title",
            author="Unknown",
            filename=file.filename,
            course_id=course_id,
            user_id=current_user.id,
            upload_date=datetime.datetime.now(datetime.timezone.utc),
            status=DocumentStatus.pending,
        )
        
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)
        
        # Run in Celery Worker
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
        try:
            from celery_worker import analyze_document
            analyze_document.delay(new_doc.id, file_path)
        except Exception as e:
            logger.warning(f"Failed to dispatch celery task: {e}")
        
        return new_doc
            
    except Exception as e:
        logger.exception("Upload handler error")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=DocumentListResponse)
async def list_documents(
    limit: int = 20, 
    offset: int = 0, 
    status: Optional[str] = None, 
    course_id: Optional[str] = None, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy.orm import joinedload
    query = db.query(Document).options(joinedload(Document.report)).filter(Document.user_id == current_user.id)
    if status:
        query = query.filter(Document.status == status)
    if course_id:
        query = query.filter(Document.course_id == course_id)
        
    total = query.count()
    docs = query.offset(offset).limit(limit).all()
    
    items = []
    for d in docs:
        d.score = d.report[0].score if d.report else 0.0
        d.risk_level = d.report[0].risk_level if d.report else None
        d.originality_score = d.report[0].score if d.report else None
        items.append(d)
        
    return {"total": total, "items": items}

@router.get("/{id}", response_model=DocumentDetailResponse)
async def get_document(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    doc.score = doc.report[0].score if doc.report else 0.0
    doc.risk_level = doc.report[0].risk_level if doc.report else None
    doc.originality_score = doc.report[0].score if doc.report else None
    return doc

@router.post("/batch")
@limiter.limit("5/minute")
async def process_batch(
    request: Request,
    files: List[UploadFile] = File(...),
    course_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return {"message": "Batch processing deferred", "files_received": len(files)}

@router.websocket("/{document_id}/status")
async def websocket_endpoint(websocket: WebSocket, document_id: str):
    """Real-time status updates via Redis pub/sub from celery_worker (M-04)."""
    import asyncio
    import json as _json
    import redis as _redis

    await manager.connect(websocket, document_id)

    redis_client = _redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        decode_responses=True
    )
    pubsub = redis_client.pubsub()
    pubsub.subscribe(f"doc_status:{document_id}")

    try:
        while True:
            msg = pubsub.get_message(ignore_subscribe_messages=True)
            if msg and msg["type"] == "message":
                data = _json.loads(msg["data"])
                await websocket.send_json(data)
                if data.get("stage") == "complete":
                    break
            await asyncio.sleep(0.2)
    except WebSocketDisconnect:
        pass
    finally:
        pubsub.unsubscribe(f"doc_status:{document_id}")
        pubsub.close()
        manager.disconnect(websocket, document_id)


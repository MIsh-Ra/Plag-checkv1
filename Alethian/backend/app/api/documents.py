from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import uuid
import datetime

from app.core.ingestion import GrobidClient
from app.db.session import get_db
from app.db.models import Document, DocumentStatus

router = APIRouter()

# Dependency: GrobidClient is stateless, can act as singleton for now
grobid_client = GrobidClient()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        content = await file.read()
        
        # 1. Process with Grobid
        processed_data = grobid_client.process_pdf(content)
        
        # 2. Create DB Record
        doc_id = str(uuid.uuid4())
        new_doc = Document(
            id=doc_id,
            title=processed_data.get("title", "Unknown"),
            author=processed_data.get("references", [{}])[0].get("author", "Unknown") if processed_data.get("references") else "Unknown", # Simple heuristic
            filename=file.filename,
            upload_date=datetime.datetime.now(datetime.timezone.utc),
            status=DocumentStatus.complete, # Since we processed it synchronously
            meta_data=processed_data
        )
        
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)
        
        return {
            "id": new_doc.id,
            "filename": new_doc.filename,
            "status": new_doc.status,
            "data": new_doc.meta_data
        }
            
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("")
async def list_documents(limit: int = 10, offset: int = 0, db: Session = Depends(get_db)):
    docs = db.query(Document).offset(offset).limit(limit).all()
    
    # Return strict JSON structure expected by frontend
    return [
        {
            "id": d.id,
            "title": d.title,
            "author": d.author,
            "status": d.status,
            "score": 0.0, # detailed score not yet implemented
            "uploaded_at": d.upload_date.isoformat()
        }
        for d in docs
    ]

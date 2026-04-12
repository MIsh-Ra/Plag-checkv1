from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional, List
import uuid

from app.db.session import get_db
from app.db.models import Report, Match, Document, HeatmapPage, Source
from app.schemas.report import FullReportResponse, HeatmapPageResponse, ReportReviewRequest
from app.schemas.match import MatchExcludeRequest, MatchCommentRequest
from app.core.report_engine import recalculate_after_exclusion, build_summary_stats, generate_source_breakdown, generate_heatmap

router = APIRouter()

def _build_report_data(document_id: str, db: Session) -> dict:
    report = db.query(Report).filter(Report.document_id == document_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    doc = report.document
    
    matches_dicts = [
        {
            "type": m.type,
            "is_excluded": m.is_excluded,
            "submitted_page": m.submitted_page,
            "source_id": m.source_id,
            "match_length_words": m.match_length_words,
            "submitted_text": m.submitted_text,
            "source_title": m.source.title if m.source else None,
        }
        for m in report.matches
    ]
        
    summary_stats = build_summary_stats(matches_dicts, doc.page_count or 1)
    
    source_ids = set(m.source_id for m in report.matches if m.source_id)
    sources = db.query(Source).filter(Source.id.in_(source_ids)).all() if source_ids else []
    
    # Enrich Sources + Generate Chart Data as required in Phase 8
    # Keep the original sources for the frontend SourcePanel to use
    report_sources = generate_source_breakdown(matches_dicts)
    page_distribution = generate_heatmap(matches_dicts, doc.page_count or 1)
    
    return {
        "document_id": document_id,
        "document_title": doc.title,
        "document_author": doc.author,
        "document_text": doc.content,
        "page_count": doc.page_count,
        "analyzed_at": report.created_at,
        "processing_time_seconds": report.processing_time_seconds or 0,
        "scores": {
            "originality_score": report.score,
            "similarity_score": 100 - report.score if report.score is not None else 0,
            "risk_level": report.risk_level or "low",
            "internal_contribution": 0.0, 
            "web_contribution": 0.0
        },
        "summary_stats": summary_stats,
        "source_breakdown": report_sources,
        "sources": sources,
        "matches": report.matches,
        "heatmap": report.heatmap_pages,
        "page_distribution": page_distribution,
        "review": {
            "status": report.status,
            "reviewed_by": report.reviewed_by,
            "reviewed_at": report.reviewed_at,
            "faculty_notes": report.faculty_notes,
            "verdict": report.verdict
        }
    }


from app.api.dependencies import get_current_user
from app.db.models import User

@router.get("/{document_id}", response_model=FullReportResponse)
def get_report(document_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    report = db.query(Report).join(Document).filter(Report.document_id == document_id, Document.user_id == current_user.id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return _build_report_data(document_id, db)

@router.get("/{document_id}/heatmap", response_model=List[HeatmapPageResponse])
def get_heatmap(document_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    report = db.query(Report).join(Document).filter(Report.document_id == document_id, Document.user_id == current_user.id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report.heatmap_pages

@router.patch("/{document_id}/matches/{match_id}")
def exclude_match(document_id: str, match_id: str, req: MatchExcludeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    report = db.query(Report).join(Document).filter(Report.document_id == document_id, Document.user_id == current_user.id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    match.is_excluded = req.is_excluded
    match.exclude_reason = req.reason
    db.commit()
    
    report = db.query(Report).filter(Report.document_id == document_id).first()
    new_score = recalculate_after_exclusion(report, match_id, db)
        
    return {"status": "success", "is_excluded": match.is_excluded, "updated_originality_score": new_score}

@router.post("/{document_id}/matches/{match_id}/comment")
def comment_match(document_id: str, match_id: str, req: MatchCommentRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    report = db.query(Report).join(Document).filter(Report.document_id == document_id, Document.user_id == current_user.id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    match.comment = req.comment
    db.commit()
    return {"status": "success", "comment": match.comment}

@router.post("/{document_id}/review")
def review_document(document_id: str, req: ReportReviewRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    report = db.query(Report).join(Document).filter(Report.document_id == document_id, Document.user_id == current_user.id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report.verdict = req.verdict
    report.faculty_notes = req.faculty_notes
    report.digital_signature = req.digital_signature
    report.status = "reviewed"
    db.commit()
    return {"status": "success", "message": "Document marked as reviewed"}

@router.get("/{document_id}/export/pdf")
def export_pdf(document_id: str, include_excluded: bool = False, branding: str = "default", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    report = db.query(Report).join(Document).filter(Report.document_id == document_id, Document.user_id == current_user.id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report_data = _build_report_data(document_id, db)
    
    # Normally we would use reportlab to build a PDF here.
    # For now we'll just mock returning a URL or sending a binary blob in a real implementation.
    # We will simulate writing the PDF. (To be updated further in Phase 9)
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    import io
    from fastapi.responses import StreamingResponse
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Page 1: Overview
    p.setFont("Helvetica-Bold", 24)
    p.drawString(50, height - 80, "Alethian Originality Report")
    
    p.setFont("Helvetica", 14)
    p.drawString(50, height - 120, f"Title: {report_data.get('document_title', 'Unknown')}")
    p.drawString(50, height - 150, f"Author: {report_data.get('document_author', 'Unknown')}")
    p.drawString(50, height - 180, f"Score: {report_data['scores']['originality_score']}%")
    p.drawString(50, height - 210, f"Risk Level: {report_data['scores']['risk_level'].upper()}")
    
    # Page 2: Matches
    p.showPage()
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, height - 80, "Identified Sources")
    
    p.setFont("Helvetica", 10)
    y = height - 120
    for i, src in enumerate(report_data.get('sources', [])):
        if y < 100:
            p.showPage()
            p.setFont("Helvetica", 10)
            y = height - 80
        name = getattr(src, 'title', None) or getattr(src, 'domain', 'Unknown')
        coverage = getattr(src, 'coverage_percent', 0) or 0
        p.drawString(50, y, f"{i+1}. {name} - {coverage}%")
        y -= 25
        
    p.save()
    
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=report_{document_id}.pdf"})

@router.get("/{document_id}/export/json")
def export_json(document_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    report_obj = db.query(Report).join(Document).filter(Report.document_id == document_id, Document.user_id == current_user.id).first()
    if not report_obj:
        raise HTTPException(status_code=404, detail="Report not found")
    report = _build_report_data(document_id, db)
    return report

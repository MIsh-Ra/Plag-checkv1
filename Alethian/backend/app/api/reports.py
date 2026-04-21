from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional, List
import uuid
import io
import datetime

from app.db.session import get_db
from app.db.models import Report, Match, Document, HeatmapPage, Source
from app.schemas.report import FullReportResponse, HeatmapPageResponse, ReportReviewRequest
from app.schemas.match import MatchExcludeRequest, MatchCommentRequest
from app.core.report_engine import (
    recalculate_after_exclusion, build_summary_stats, generate_source_breakdown,
    generate_heatmap, generate_page_distribution, calculate_contributions
)

router = APIRouter()


def _build_report_data(document_id: str, db: Session) -> dict:
    report = db.query(Report).filter(Report.document_id == document_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    doc = report.document

    matches_dicts = [
        {
            "id": m.id,
            "type": m.type,
            "is_excluded": m.is_excluded,
            "submitted_page": m.submitted_page,
            "source_id": m.source_id,
            "match_length_words": m.match_length_words,
            "submitted_text": m.submitted_text,
            "source_text": m.source_text,
            "source_title": m.source.title if m.source else None,
            "submitted_start_char": m.submitted_start_char,
            "submitted_end_char": m.submitted_end_char,
            "similarity_score": m.similarity,
            "similarity": m.similarity,
            "domain": m.source.domain if m.source else None,
            "is_coherent": False,
            "source": {
                "id": m.source.id if m.source else None,
                "title": m.source.title if m.source else None,
                "domain": m.source.domain if m.source else None,
                "type": m.source.type if m.source else None,
                "url": m.source.url if m.source else None,
                "coverage_percent": m.source.coverage_percent if m.source else None,
            } if m.source else None,
        }
        for m in report.matches
    ]

    page_count = doc.page_count or 1
    summary_stats = build_summary_stats(matches_dicts, page_count)
    contributions = calculate_contributions(matches_dicts, report.doc_word_count or 1)

    # Sources with all computed fields
    source_ids = set(m.source_id for m in report.matches if m.source_id)
    sources = db.query(Source).filter(Source.id.in_(source_ids)).all() if source_ids else []
    sources_serialized = [
        {
            "id": s.id,
            "type": s.type,
            "title": s.title,
            "domain": s.domain,
            "url": s.url,
            "coverage_percent": s.coverage_percent or 0.0,
            "match_count": s.match_count or 0,
            "pages_affected": s.pages_affected or [],
            "is_coherent_source": s.is_coherent_source or False,
        }
        for s in sources
    ]

    # Heatmap — from DB (already persisted at analysis time)
    heatmap_serialized = [
        {
            "page_number": h.page_number,
            "density_score": h.density_score,
            "match_density": h.density_score,        # frontend alias
            "internal_density": h.internal_density or 0.0,
            "web_density": h.web_density or 0.0,
            "color": h.color or "#22c55e",
            "match_count": h.match_count or 0,
            "dominant_type": h.dominant_type or "clean",
        }
        for h in sorted(report.heatmap_pages, key=lambda h: h.page_number)
    ]

    # page_distribution: correct shape for BarChart {page, internal_exact, internal_paraphrase, web}
    page_distribution = generate_page_distribution(matches_dicts, page_count)

    # source_breakdown for PieChart
    source_breakdown = generate_source_breakdown(matches_dicts)

    # page_texts for page-aware frontend rendering
    page_texts = doc.page_texts or []

    # Matches serialized fully for frontend
    matches_serialized = []
    for m in report.matches:
        matches_serialized.append({
            "id": m.id,
            "type": m.type,
            "is_excluded": m.is_excluded,
            "exclude_reason": m.exclude_reason,
            "comment": m.comment,
            "submitted_text": m.submitted_text,
            "source_text": m.source_text,
            "submitted_page": m.submitted_page,
            "source_page": m.source_page,
            "submitted_start_char": m.submitted_start_char,
            "submitted_end_char": m.submitted_end_char,
            "similarity_score": m.similarity,
            "similarity": m.similarity,
            "match_length_words": m.match_length_words,
            "color_code": m.color_code,
            "source_id": m.source_id,
            "source": {
                "id": m.source.id,
                "title": m.source.title,
                "domain": m.source.domain,
                "type": m.source.type,
                "url": m.source.url,
                "coverage_percent": m.source.coverage_percent,
            } if m.source else None,
        })

    return {
        "document_id": document_id,
        "document_title": doc.title,
        "document_author": doc.author,
        "document_text": doc.content,
        "page_texts": page_texts,
        "page_count": page_count,
        "analyzed_at": report.created_at,
        "processing_time_seconds": report.processing_time_seconds or 0,
        "scores": {
            "originality_score": report.score,
            "similarity_score": 100 - report.score if report.score is not None else 0,
            "risk_level": report.risk_level or "low",
            "internal_contribution": contributions["internal_contribution"],
            "web_contribution": contributions["web_contribution"],
        },
        "summary_stats": summary_stats,
        "source_breakdown": source_breakdown,
        "sources": sources_serialized,
        "matches": matches_serialized,
        "heatmap": heatmap_serialized,
        "page_distribution": page_distribution,
        "review": {
            "status": report.status,
            "reviewed_by": report.reviewed_by,
            "reviewed_at": report.reviewed_at,
            "faculty_notes": report.faculty_notes,
            "verdict": report.verdict,
        },
    }


from app.api.dependencies import get_current_user
from app.db.models import User


@router.get("/{document_id}", response_model=FullReportResponse)
def get_report(document_id: str, db: Session = Depends(get_db),
               current_user: User = Depends(get_current_user)):
    report = db.query(Report).join(Document).filter(
        Report.document_id == document_id,
        Document.user_id == current_user.id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return _build_report_data(document_id, db)


@router.get("/{document_id}/heatmap", response_model=List[HeatmapPageResponse])
def get_heatmap(document_id: str, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    report = db.query(Report).join(Document).filter(
        Report.document_id == document_id,
        Document.user_id == current_user.id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return [
        {
            "page_number": h.page_number,
            "density_score": h.density_score,
            "match_density": h.density_score,
            "internal_density": h.internal_density or 0.0,
            "web_density": h.web_density or 0.0,
            "color": h.color or "#22c55e",
            "match_count": h.match_count or 0,
        }
        for h in sorted(report.heatmap_pages, key=lambda h: h.page_number)
    ]


@router.patch("/{document_id}/matches/{match_id}")
def exclude_match(document_id: str, match_id: str, req: MatchExcludeRequest,
                  db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    report = db.query(Report).join(Document).filter(
        Report.document_id == document_id,
        Document.user_id == current_user.id
    ).first()
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
    return {"status": "success", "is_excluded": match.is_excluded,
            "updated_originality_score": new_score}


@router.post("/{document_id}/matches/{match_id}/comment")
def comment_match(document_id: str, match_id: str, req: MatchCommentRequest,
                  db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    report = db.query(Report).join(Document).filter(
        Report.document_id == document_id,
        Document.user_id == current_user.id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    match.comment = req.comment
    db.commit()
    return {"status": "success", "comment": match.comment}


@router.post("/{document_id}/review")
def review_document(document_id: str, req: ReportReviewRequest,
                    db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    report = db.query(Report).join(Document).filter(
        Report.document_id == document_id,
        Document.user_id == current_user.id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.verdict = req.verdict
    report.faculty_notes = req.faculty_notes
    report.digital_signature = req.digital_signature
    report.status = "reviewed"
    report.reviewed_at = datetime.datetime.now(datetime.timezone.utc)
    db.commit()
    return {"status": "success", "message": "Document marked as reviewed"}


@router.get("/{document_id}/export/pdf")
def export_pdf(document_id: str,
               include_excluded: bool = False,
               db: Session = Depends(get_db),
               current_user: User = Depends(get_current_user)):
    """
    Generate a comprehensive Alethian forensic PDF report per Report_Design_v2 spec.
    Phase 3 full implementation: cover page, source summary, match details.
    """
    report = db.query(Report).join(Document).filter(
        Report.document_id == document_id,
        Document.user_id == current_user.id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report_data = _build_report_data(document_id, db)
    from fastapi.responses import StreamingResponse
    buffer = _build_pdf(report_data, include_excluded=include_excluded)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=alethian_report_{document_id[:8]}.pdf"},
    )


def _build_pdf(report_data: dict, include_excluded: bool = False) -> io.BytesIO:
    """
    Full reportlab PDF matching Report_Design_v2 §5 specification.
    Page 1: Cover
    Page 2: Source Summary + Charts
    Pages 3+: Match Details (2-3 per page)
    Last Page: Footer hash
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, HRFlowable, KeepTogether
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    import hashlib

    buffer = io.BytesIO()
    PAGE_W, PAGE_H = A4
    MARGIN = 20 * mm

    # ── Colour constants matching Report_Design_v2 §3 ──────────────────────
    RED    = colors.HexColor("#ef4444")
    ORANGE = colors.HexColor("#f97316")
    BLUE   = colors.HexColor("#3b82f6")
    GREEN  = colors.HexColor("#22c55e")
    YELLOW = colors.HexColor("#eab308")
    DARK   = colors.HexColor("#0e0e0e")
    GREY   = colors.HexColor("#9ca3af")
    LIGHT  = colors.HexColor("#f3f4f6")
    WHITE  = colors.white

    MATCH_COLORS = {
        "internal_exact": RED,
        "internal_paraphrase": ORANGE,
        "web": BLUE,
    }

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN + 10 * mm,
    )

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=22,
                        textColor=DARK, spaceAfter=4, fontName="Helvetica-Bold")
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=14,
                        textColor=DARK, spaceAfter=4, fontName="Helvetica-Bold")
    h3 = ParagraphStyle("H3", parent=styles["Heading3"], fontSize=10,
                        textColor=DARK, spaceAfter=2, fontName="Helvetica-Bold")
    body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=9,
                          textColor=DARK, spaceAfter=2, fontName="Helvetica",
                          leading=14)
    label = ParagraphStyle("Label", parent=styles["Normal"], fontSize=7,
                           textColor=GREY, fontName="Helvetica", spaceAfter=1,
                           leading=10)
    mono = ParagraphStyle("Mono", parent=styles["Normal"], fontSize=8,
                          fontName="Courier", leading=12, textColor=DARK)
    center = ParagraphStyle("Center", parent=body, alignment=TA_CENTER)

    scores = report_data.get("scores", {})
    summary = report_data.get("summary_stats", {})
    originality = scores.get("originality_score") or 0
    similarity = scores.get("similarity_score") or 0
    risk = (scores.get("risk_level") or "low").upper()
    risk_color = RED if risk == "HIGH" else (YELLOW if risk == "MODERATE" else GREEN)

    matches = report_data.get("matches", [])
    if not include_excluded:
        matches = [m for m in matches if not m.get("is_excluded")]

    sources = report_data.get("sources", [])
    now = datetime.datetime.utcnow()
    report_hash = hashlib.sha256(
        f"{report_data.get('document_id')}{now.isoformat()}".encode()
    ).hexdigest()[:16].upper()

    story = []

    # ── PAGE 1: COVER ────────────────────────────────────────────────────────
    story.append(Spacer(1, 8 * mm))

    # Header bar (simulated with a coloured table cell)
    cover_header = Table(
        [[ Paragraph("ALETHIAN ORIGINALITY REPORT", ParagraphStyle(
            "CoverH", fontSize=20, textColor=WHITE, fontName="Helvetica-Bold",
            alignment=TA_CENTER
        ))]],
        colWidths=[PAGE_W - 2 * MARGIN],
        rowHeights=[18 * mm],
    )
    cover_header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(cover_header)
    story.append(Spacer(1, 8 * mm))

    # Document metadata table
    meta_data = [
        ["Document Title:", report_data.get("document_title") or "Unknown"],
        ["Author:", report_data.get("document_author") or "Unknown"],
        ["Analysis Date:", now.strftime("%B %d, %Y at %H:%M UTC")],
        ["Total Pages:", str(report_data.get("page_count") or "—")],
    ]
    meta_table = Table(meta_data, colWidths=[45 * mm, PAGE_W - 2 * MARGIN - 45 * mm])
    meta_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), DARK),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LIGHT, WHITE]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10 * mm))

    # Large score display
    score_block_data = [[
        Paragraph(f"{round(originality)}%",
                  ParagraphStyle("Score", fontSize=52, fontName="Helvetica-Bold",
                                 textColor=risk_color, alignment=TA_CENTER)),
        Paragraph(f"<b>{risk} RISK</b><br/>Originality Score",
                  ParagraphStyle("RiskLabel", fontSize=12, fontName="Helvetica-Bold",
                                 textColor=risk_color, alignment=TA_LEFT, leading=18)),
    ]]
    score_table = Table(score_block_data, colWidths=[55 * mm, PAGE_W - 2 * MARGIN - 55 * mm])
    score_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 1.5, risk_color),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 8 * mm))

    # Internal vs Web contribution bar (text-based since no chart lib)
    int_pct = scores.get("internal_contribution", 0)
    web_pct = scores.get("web_contribution", 0)
    contrib_data = [
        ["", "Contribution", "Sources", "Match Count"],
        ["Internal Archive", f"{int_pct:.1f}%",
         str(sum(1 for s in sources if s.get("type") == "internal")),
         str(summary.get("internal_exact", 0) + summary.get("internal_paraphrase", 0))],
        ["Web Dragnet", f"{web_pct:.1f}%",
         str(sum(1 for s in sources if s.get("type") == "web")),
         str(summary.get("web_matches", 0))],
    ]
    contrib_table = Table(contrib_data,
                          colWidths=[55 * mm, 35 * mm, 35 * mm, 45 * mm])
    contrib_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT, WHITE]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(contrib_table)
    story.append(Spacer(1, 8 * mm))

    # Summary stats table
    story.append(Paragraph("Summary Statistics", h2))
    story.append(HRFlowable(width="100%", thickness=1, color=DARK))
    story.append(Spacer(1, 3 * mm))
    stats_data = [
        ["Total Matches", str(summary.get("total_matches", 0)),
         "Unique Sources", str(summary.get("unique_sources", 0))],
        ["Internal Exact", str(summary.get("internal_exact", 0)),
         "Internal Paraphrase", str(summary.get("internal_paraphrase", 0))],
        ["Web Matches", str(summary.get("web_matches", 0)),
         "Pages with Matches", f"{summary.get('pages_with_matches', 0)} / {summary.get('total_pages', 0)}"],
        ["Avg Match Length", f"{summary.get('avg_match_length_words', 0):.0f} words",
         "Longest Match", f"{summary.get('longest_match_words', 0)} words (pg {summary.get('longest_match_page', '—')})"],
        ["Excluded Matches", str(summary.get("excluded_matches", 0)),
         "Coherent Domains", ", ".join(summary.get("coherent_domains", [])) or "None"],
    ]
    stats_table = Table(stats_data,
                        colWidths=[45 * mm, 40 * mm, 55 * mm, 30 * mm])
    stats_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LIGHT, WHITE]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 10 * mm))

    # Reviewer sign-off block
    story.append(Paragraph("Faculty Review", h2))
    story.append(HRFlowable(width="100%", thickness=1, color=DARK))
    story.append(Spacer(1, 3 * mm))
    review = report_data.get("review", {})
    review_data = [
        ["Reviewed By:", review.get("reviewed_by") or "___________________________"],
        ["Date:", review.get("reviewed_at") or "___________________________"],
        ["Verdict:", review.get("verdict") or "___________________________"],
        ["Signature:", "___________________________"],
    ]
    review_table = Table(review_data,
                         colWidths=[40 * mm, PAGE_W - 2 * MARGIN - 40 * mm])
    review_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, GREY),
    ]))
    story.append(review_table)
    story.append(PageBreak())

    # ── PAGE 2: SOURCE SUMMARY ───────────────────────────────────────────────
    story.append(Paragraph("Source Index", h1))
    story.append(HRFlowable(width="100%", thickness=2, color=DARK))
    story.append(Spacer(1, 5 * mm))

    if sources:
        src_header = [["#", "Source", "Type", "Coverage", "Matches", "Pages"]]
        src_rows = []
        for i, s in enumerate(sorted(sources, key=lambda x: -(x.get("coverage_percent") or 0))):
            src_rows.append([
                str(i + 1),
                (s.get("title") or s.get("domain") or "Unknown")[:45],
                s.get("type", "").upper(),
                f"{s.get('coverage_percent') or 0:.1f}%",
                str(s.get("match_count") or 0),
                ", ".join(str(p) for p in (s.get("pages_affected") or [])[:6]) or "—",
            ])
        src_table = Table(
            src_header + src_rows,
            colWidths=[8 * mm, 70 * mm, 20 * mm, 22 * mm, 18 * mm, 32 * mm],
        )
        src_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT, WHITE]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("ALIGN", (3, 0), (4, -1), "RIGHT"),
        ]))
        story.append(src_table)
    else:
        story.append(Paragraph("No sources identified.", body))

    story.append(PageBreak())

    # ── PAGES 3+: MATCH DETAILS ───────────────────────────────────────────────
    story.append(Paragraph("Match Details", h1))
    story.append(HRFlowable(width="100%", thickness=2, color=DARK))
    story.append(Spacer(1, 5 * mm))

    if not matches:
        story.append(Paragraph("No matches found.", body))
    else:
        for i, m in enumerate(matches):
            mtype = m.get("type", "web")
            mcolor = MATCH_COLORS.get(mtype, BLUE)
            mtype_label = mtype.replace("_", " ").upper()
            sim = round(m.get("similarity_score") or m.get("similarity") or 0)
            src = m.get("source") or {}
            src_name = src.get("title") or src.get("domain") or "Unknown Source"
            src_url = src.get("url") or ""

            submitted_text = (m.get("submitted_text") or "")[:600]
            source_text = (m.get("source_text") or "")[:600]

            match_block = []
            # Header bar for each match
            header_data = [[
                Paragraph(f"Match #{i+1} — {mtype_label}", ParagraphStyle(
                    "MHead", fontSize=9, fontName="Helvetica-Bold",
                    textColor=WHITE, alignment=TA_LEFT
                )),
                Paragraph(f"Page {m.get('submitted_page', '—')} · {sim}% similarity",
                          ParagraphStyle("MSub", fontSize=9, fontName="Helvetica",
                                         textColor=WHITE, alignment=TA_RIGHT)),
            ]]
            header_table = Table(
                header_data,
                colWidths=[(PAGE_W - 2 * MARGIN) * 0.65, (PAGE_W - 2 * MARGIN) * 0.35]
            )
            header_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), mcolor),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            match_block.append(header_table)

            # Source line
            match_block.append(
                Paragraph(f"<b>Source:</b> {src_name}"
                          + (f" — {src_url[:80]}" if src_url else ""), label)
            )
            match_block.append(Spacer(1, 2 * mm))

            # Side-by-side submitted vs source
            diff_data = [[
                Paragraph("<b>Submitted Text</b>", ParagraphStyle(
                    "DH", fontSize=8, fontName="Helvetica-Bold", textColor=DARK
                )),
                Paragraph("<b>Source Text</b>", ParagraphStyle(
                    "DH", fontSize=8, fontName="Helvetica-Bold", textColor=DARK
                )),
            ], [
                Paragraph(submitted_text or "—", mono),
                Paragraph(source_text or "—", mono),
            ]]
            col_w = (PAGE_W - 2 * MARGIN - 2 * mm) / 2
            diff_table = Table(diff_data, colWidths=[col_w, col_w])
            diff_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]))
            match_block.append(diff_table)

            if m.get("comment"):
                match_block.append(Spacer(1, 1 * mm))
                match_block.append(
                    Paragraph(f"<b>Faculty Note:</b> {m['comment']}", label)
                )
            if m.get("is_excluded"):
                match_block.append(
                    Paragraph(f"<i>Excluded — {m.get('exclude_reason', '')}</i>", label)
                )

            match_block.append(Spacer(1, 5 * mm))
            story.append(KeepTogether(match_block))

    story.append(PageBreak())

    # ── LAST PAGE: FOOTER / INTEGRITY ────────────────────────────────────────
    story.append(Spacer(1, 30 * mm))
    story.append(HRFlowable(width="100%", thickness=1, color=GREY))
    story.append(Spacer(1, 4 * mm))
    footer_text = [
        f"Generated by Alethian v2.0 — Local-First Plagiarism Detection System",
        f"Report generated: {now.strftime('%Y-%m-%d %H:%M UTC')}",
        f"Document ID: {report_data.get('document_id', '—')}",
        f"Integrity token: {report_hash}",
    ]
    for line in footer_text:
        story.append(Paragraph(line, ParagraphStyle(
            "Footer", fontSize=7, textColor=GREY,
            fontName="Courier", alignment=TA_CENTER
        )))

    # Page header/footer callback
    def _add_page_meta(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(GREY)
        title_short = (report_data.get("document_title") or "Report")[:50]
        canvas.drawString(MARGIN, 10 * mm,
                          f"Alethian Report — {title_short}")
        canvas.drawRightString(PAGE_W - MARGIN, 10 * mm,
                               f"Page {doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=_add_page_meta, onLaterPages=_add_page_meta)
    buffer.seek(0)
    return buffer


@router.get("/{document_id}/export/json")
def export_json(document_id: str, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    report_obj = db.query(Report).join(Document).filter(
        Report.document_id == document_id,
        Document.user_id == current_user.id
    ).first()
    if not report_obj:
        raise HTTPException(status_code=404, detail="Report not found")
    return _build_report_data(document_id, db)

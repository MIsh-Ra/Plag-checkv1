import os
import json
from celery import Celery
import time
import redis as _redis

redis_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")

celery_app = Celery(
    "worker",
    broker=redis_url,
    backend=redis_url
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

def _fallback_extract(file_path: str) -> str:
    """Emergency fallback using pypdf if Grobid fails or is unreachable."""
    try:
        import pypdf
        text = []
        with open(file_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text.append(extracted)
        return "\n\n".join(text)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Fallback extraction failed: {e}")
        return ""

@celery_app.task(bind=True, name="analyze_document")
def analyze_document(self, document_id: str, file_path: str):
    from app.db.session import SessionLocal
    from app.db.models import Document, DocumentStatus, Report, Match, Source, HeatmapPage
    from app.core.similarity import run_similarity, index_document
    from app.core.web_dragnet import run_dragnet
    from app.core.report_engine import calculate_originality, generate_heatmap
    from app.core.ingestion import GrobidClient
    from app.core.config import settings
    import logging

    logger = logging.getLogger(__name__)
    db = SessionLocal()

    # Redis client for status broadcasting (M-04)
    try:
        _status_redis = _redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True
        )
    except Exception:
        _status_redis = None

    def broadcast_status(stage: str, progress: int, message: str = ""):
        """Publish stage update to Redis pub/sub for WebSocket consumers."""
        if _status_redis:
            try:
                _status_redis.publish(
                    f"doc_status:{document_id}",
                    json.dumps({"stage": stage, "progress": progress, "message": message})
                )
            except Exception:
                pass

    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return

        # --- File Size Check ---
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if hasattr(settings, 'MAX_UPLOAD_SIZE_MB') and file_size_mb > getattr(settings, 'MAX_UPLOAD_SIZE_MB', 100):
             doc.status = DocumentStatus.failed
             db.commit()
             return {"error": f"File too large: {file_size_mb:.1f}MB"}

        # --- Stage 1: Ingestion ---
        doc.status = DocumentStatus.processing
        db.commit()
        logger.info(f"[{document_id}] Stage: ingestion")
        broadcast_status("ingesting", 10, "Parsing PDF with Grobid...")

        grobid = GrobidClient(host=settings.GROBID_URL)
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        
        try:
            parsed = grobid.process_pdf(file_bytes)
            text = parsed["body_text"]
            page_count = parsed.get("page_count", 1) or 1
            doc.title = str(parsed.get("title", doc.title))[:250] # Limit size safely
            doc.page_count = page_count
            
            if not text or len(text.strip()) < 50:
                raise ValueError("Grobid extracted very little or no text. Likely a non-standard layout.")
        except Exception as e:
            logger.warning(f"[{document_id}] Grobid failed or returned empty text, falling back to raw text extraction: {e}")
            text = _fallback_extract(file_path)
            page_count = max(1, len(text) // 3000)
            doc.page_count = page_count
        
        doc.content = text
        db.commit()

        # --- Stage 1.5: Index for future comparisons (moved before similarity) ---
        logger.info(f"[{document_id}] Stage: indexing")
        broadcast_status("indexing", 25, "Indexing document into archive...")
        index_document(document_id, text, title=doc.title, page_count=doc.page_count or 1)

        # --- Stage 2: Internal Similarity ---
        logger.info(f"[{document_id}] Stage: internal_similarity")
        broadcast_status("internal_similarity", 40, "Comparing against internal archive...")
        internal_matches = run_similarity(document_id, text, db, page_count=doc.page_count or 1)

        # --- Stage 3: Web Dragnet ---
        logger.info(f"[{document_id}] Stage: web_dragnet")
        broadcast_status("web_dragnet", 60, "Searching web sources...")
        web_matches = run_dragnet(document_id, text, internal_matches)

        # --- Stage 4: Report Generation ---
        logger.info(f"[{document_id}] Stage: report_generation")
        broadcast_status("report_generation", 85, "Generating originality report...")
        all_raw_matches = internal_matches + web_matches

        score = calculate_originality(all_raw_matches, len(text.split()))
        risk = "high" if score < 50 else ("moderate" if score < 80 else "low")
        
        report = Report(document_id=doc.id, score=score, risk_level=risk)
        db.add(report)
        db.flush()

        # Persist Sources
        source_map = {}
        for m in all_raw_matches:
            key = m.get("source_document_id") or m.get("url")
            if not key:
                continue
            if key not in source_map:
                src = Source(
                    type="web" if "web" in m.get("type", "web") else "internal",
                    url=m.get("url"),
                    title=m.get("source_title") or m.get("domain", "Unknown Source"),
                    domain=m.get("domain", ""),
                    document_id=doc.id,  # FK to the document being analyzed, not the matched source
                )
                db.add(src)
                db.flush()
                source_map[key] = src.id

        # Persist Matches
        for m in all_raw_matches:
            key = m.get("source_document_id") or m.get("url")
            match_record = Match(
                report_id=report.id,
                source_id=source_map.get(key),
                type=m.get("type", "web"),
                submitted_text=m.get("submitted_text", ""),
                source_text=m.get("source_text", ""),
                submitted_page=m.get("submitted_page", 1),
                source_page=m.get("source_page", 1),
                submitted_start_char=m.get("submitted_start_char", 0),
                submitted_end_char=m.get("submitted_end_char", 0),
                similarity=m.get("similarity_score", m.get("score", 0.0) * 100),
                match_length_words=len(m.get("submitted_text", "").split())
            )
            db.add(match_record)

        # Generate & Persist Heatmap
        heatmap = generate_heatmap(all_raw_matches, doc.page_count)
        for h in heatmap:
            hp = HeatmapPage(
                report_id=report.id,
                page_number=h["page_number"],
                density_score=h["density_score"],
                internal_density=h.get("internal_density", 0.0),
                web_density=h.get("web_density", 0.0),
                color=h.get("color", "#22c55e"),
                match_count=h.get("match_count", 0),
                dominant_type=h.get("dominant_type", "clean")
            )
            db.add(hp)


        doc.status = DocumentStatus.complete
        # Set doc originality metric denormalized mapping properties assuming these fields exist natively
        doc.score = score
        doc.risk_level = risk
        doc.originality_score = score

        db.commit()
        broadcast_status("complete", 100, "Analysis complete.")
    except Exception as e:
        logger.error(f"Failed worker operation {e}")
        db.rollback()
        try:
            doc = db.query(Document).filter(Document.id == document_id).first()
            if doc:
                doc.status = DocumentStatus.failed
                db.commit()
        except Exception:
            pass
        raise e
    finally:
        if file_path and os.path.exists(file_path):
             try:
                 os.remove(file_path)
             except OSError:
                 pass
        db.close()

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


@celery_app.task(bind=True, name="analyze_document")
def analyze_document(self, document_id: str, file_path: str):
    from app.db.session import SessionLocal
    from app.db.models import Document, DocumentStatus, Report, Match, Source, HeatmapPage
    from app.core.similarity import run_similarity, index_document
    from app.core.web_dragnet import run_dragnet
    from app.core.report_engine import calculate_originality, generate_heatmap
    from app.core.text_extraction import extract_text_from_pdf
    from app.core.config import settings
    import logging

    logger = logging.getLogger(__name__)
    db = SessionLocal()

    # Redis client for status broadcasting
    try:
        _status_redis = _redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True
        )
    except Exception:
        _status_redis = None

    def broadcast_status(stage: str, progress: int, message: str = ""):
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
        if file_size_mb > getattr(settings, 'MAX_UPLOAD_SIZE_MB', 100):
            doc.status = DocumentStatus.failed
            db.commit()
            return {"error": f"File too large: {file_size_mb:.1f}MB"}

        # --- Stage 1: Ingestion ---
        doc.status = DocumentStatus.processing
        db.commit()
        logger.info(f"[{document_id}] Stage: ingestion")
        broadcast_status("ingesting", 10, "Parsing PDF with Grobid...")

        parsed = extract_text_from_pdf(file_path, grobid_url=settings.GROBID_URL)
        text = parsed.get("body_text", "")
        page_texts = parsed.get("page_texts", [])        # [{page, text, char_start, char_end}]
        page_boundaries = parsed.get("page_boundaries", [])  # [(char_start, char_end, page_num)]

        doc.title = str(parsed.get("title", doc.title))[:250]
        doc.page_count = parsed.get("page_count", 1)

        if not text or len(text.strip()) < 50:
            logger.error(f"[{document_id}] All extraction methods failed.")
            doc.status = DocumentStatus.failed
            db.commit()
            return {"error": "No text could be extracted from this PDF."}

        logger.info(f"[{document_id}] Extracted via {parsed.get('extraction_method')} "
                    f"({len(text)} chars, {doc.page_count} pages, {len(page_texts)} page_texts)")

        doc.content = text
        doc.page_texts = page_texts  # persist page-indexed text
        db.commit()

        # --- Stage 1.5: Index for future comparisons ---
        logger.info(f"[{document_id}] Stage: indexing")
        broadcast_status("indexing", 25, "Indexing document into archive...")
        index_document(document_id, text, title=doc.title,
                       page_boundaries=page_boundaries, page_count=doc.page_count or 1)

        # --- Stage 2: Internal Similarity ---
        logger.info(f"[{document_id}] Stage: internal_similarity")
        broadcast_status("internal_similarity", 40, "Comparing against internal archive...")
        internal_matches = run_similarity(
            document_id, text, db,
            page_boundaries=page_boundaries,
            page_count=doc.page_count or 1
        )

        # --- Stage 3: Web Dragnet ---
        logger.info(f"[{document_id}] Stage: web_dragnet")
        broadcast_status("web_dragnet", 60, "Searching web sources...")
        web_matches = run_dragnet(
            document_id, text, internal_matches,
            page_boundaries=page_boundaries,
            page_count=doc.page_count or 1
        )

        # --- Stage 4: Report Generation ---
        logger.info(f"[{document_id}] Stage: report_generation")
        broadcast_status("report_generation", 85, "Generating originality report...")
        all_raw_matches = internal_matches + web_matches

        doc_word_count = len(text.split())
        score = calculate_originality(all_raw_matches, doc_word_count)
        risk = "high" if score < 50 else ("moderate" if score < 80 else "low")

        report = Report(
            document_id=doc.id,
            score=score,
            risk_level=risk,
            doc_word_count=doc_word_count
        )
        db.add(report)
        db.flush()

        # --- Persist Sources with computed coverage stats ---
        source_map = {}     # key -> source_id
        source_matches = {}  # key -> [match dicts]

        for m in all_raw_matches:
            key = m.get("source_document_id") or m.get("url")
            if not key:
                continue
            if key not in source_map:
                src = Source(
                    type="web" if m.get("type") == "web" else "internal",
                    url=m.get("url"),
                    title=m.get("source_title") or m.get("domain", "Unknown Source"),
                    domain=m.get("domain", ""),
                    document_id=m.get("source_document_id"),
                    report_document_id=doc.id,
                )
                db.add(src)
                db.flush()
                source_map[key] = src.id
                source_matches[key] = []
            source_matches[key].append(m)

        # Compute coverage_percent, match_count, pages_affected per source
        for key, src_id in source_map.items():
            src_obj = db.query(Source).filter(Source.id == src_id).first()
            if not src_obj:
                continue
            ms = source_matches[key]
            src_obj.match_count = len(ms)
            src_obj.pages_affected = sorted(set(m.get("submitted_page", 1) for m in ms))
            # coverage = sum of matched words / total doc words
            total_matched_words = sum(len(m.get("submitted_text", "").split()) for m in ms)
            src_obj.coverage_percent = round(
                min(100.0, (total_matched_words / max(1, doc_word_count)) * 100), 2
            )

        # --- Persist Matches ---
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

        # --- Generate & Persist Heatmap ---
        heatmap = generate_heatmap(all_raw_matches, doc.page_count, doc_word_count=doc_word_count)
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
        doc.risk_level = risk
        doc.originality_score = score

        db.commit()

        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass

        broadcast_status("complete", 100, "Analysis complete.")

    except Exception as e:
        logger.error(f"Failed worker operation: {e}", exc_info=True)
        db.rollback()

        # Rollback Qdrant inserts
        try:
            from app.core.similarity import _get_qdrant
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            qdrant = _get_qdrant()
            if qdrant:
                qdrant.client.delete(
                    collection_name=qdrant.collection_name,
                    points_selector=Filter(
                        must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
                    )
                )
        except Exception as delete_ex:
            logger.error(f"Failed to rollback Qdrant changes: {delete_ex}")

        try:
            doc = db.query(Document).filter(Document.id == document_id).first()
            if doc:
                doc.status = DocumentStatus.failed
                db.commit()
        except Exception:
            pass
        raise e
    finally:
        db.close()

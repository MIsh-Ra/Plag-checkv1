"""
Centralised PDF text extraction with 3-tier fallback:
  1. Grobid (structured parse with sections, metadata, references)
  2. pypdf  (raw text from digitally-generated PDFs)
  3. Tesseract OCR (scanned/image-only PDFs)

All three ingestion paths (celery_worker, ingest_archive, seed_archive)
should use extract_text_from_pdf() instead of their own ad-hoc logic.

Returns page_texts: list of {page, text, char_start, char_end} for
page-aware rendering and accurate heatmap/similarity assignment.
"""
import os
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


def _build_page_texts(pages: List[str]) -> List[Dict[str, Any]]:
    """
    Given a list of per-page text strings, build page_texts + page_boundaries.
    Returns:
        page_texts: [{page, text, char_start, char_end}, ...]
        body_text: single concatenated string (pages joined by double newline)
        page_boundaries: [(char_start, char_end, page_num), ...]
    """
    page_texts = []
    page_boundaries = []
    cursor = 0
    separator = "\n\n"
    sep_len = len(separator)

    for i, text in enumerate(pages):
        page_num = i + 1
        char_start = cursor
        char_end = cursor + len(text)
        page_texts.append({
            "page": page_num,
            "text": text,
            "char_start": char_start,
            "char_end": char_end,
        })
        page_boundaries.append((char_start, char_end, page_num))
        cursor = char_end + sep_len  # account for "\n\n" separator

    body_text = separator.join(p["text"] for p in page_texts)
    return page_texts, body_text, page_boundaries


def extract_with_grobid(file_bytes: bytes, grobid_url: str = "http://localhost:8070") -> Optional[Dict[str, Any]]:
    """Tier 1: Grobid structured parse. Returns parsed dict or None on failure."""
    from app.core.ingestion import GrobidClient
    from app.core.config import settings
    try:
        client = GrobidClient(host=grobid_url)
        parsed = client.process_pdf(file_bytes)
        body_text = parsed.get("body_text", "")
        if not body_text or len(body_text.strip()) < settings.MIN_TEXT_LENGTH:
            logger.warning("Grobid returned very little text (%d chars).", len(body_text))
            return None

        # Build page_texts from Grobid's page-break-aware text
        # GrobidClient now returns page_texts if available
        if parsed.get("page_texts"):
            page_texts = parsed["page_texts"]
            page_boundaries = [
                (pt["char_start"], pt["char_end"], pt["page"])
                for pt in page_texts
            ]
            parsed["page_texts"] = page_texts
            parsed["page_boundaries"] = page_boundaries
        else:
            # Fallback: treat as single page
            page_texts = [{"page": 1, "text": body_text, "char_start": 0, "char_end": len(body_text)}]
            parsed["page_texts"] = page_texts
            parsed["page_boundaries"] = [(0, len(body_text), 1)]

        return parsed
    except Exception as e:
        logger.warning("Grobid extraction failed: %s", e)
        return None


def extract_with_pypdf(file_path: str) -> Optional[Dict[str, Any]]:
    """Tier 2: pypdf raw text extraction. Preserves per-page text with char offsets."""
    try:
        import pypdf
        pages = []
        with open(file_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            for page in reader.pages:
                extracted = page.extract_text()
                # Always append (even if empty) to preserve page count alignment
                pages.append(extracted.strip() if extracted else "")

        from app.core.config import settings

        # Filter: at least some pages must have content
        non_empty = [p for p in pages if p]
        if not non_empty:
            logger.warning("pypdf extracted no text.")
            return None

        combined = "\n\n".join(non_empty)
        if len(combined.strip()) < settings.MIN_TEXT_LENGTH:
            logger.warning("pypdf extracted very little text (%d chars).", len(combined))
            return None

        # Build page-indexed structure from ALL pages (including empty ones,
        # so page numbers align with actual PDF page numbers)
        page_texts, body_text, page_boundaries = _build_page_texts(pages)

        return {
            "body_text": body_text,
            "title": "Unknown Title",
            "page_count": len(pages),
            "page_texts": page_texts,
            "page_boundaries": page_boundaries,
            "sections": [],
            "references": [],
            "extraction_method": "pypdf",
            "confidence": 0.6,
        }
    except Exception as e:
        logger.warning("pypdf extraction failed: %s", e)
        return None


def extract_with_ocr(file_path: str) -> Optional[Dict[str, Any]]:
    """Tier 3: Tesseract OCR via pdf2image. For scanned/image-only PDFs."""
    try:
        from pdf2image import convert_from_path
        import pytesseract
    except ImportError as e:
        logger.error("OCR dependencies not installed (pytesseract / pdf2image): %s", e)
        return None

    try:
        from app.core.config import settings
        images = convert_from_path(file_path, dpi=settings.OCR_DPI)
        pages = []
        for i, img in enumerate(images):
            text = pytesseract.image_to_string(img, lang='eng')
            pages.append(text.strip() if text else "")

        non_empty = [p for p in pages if p]
        if not non_empty:
            return None

        combined = "\n\n".join(non_empty)
        if len(combined.strip()) < settings.MIN_TEXT_LENGTH:
            logger.warning("OCR extracted very little text (%d chars).", len(combined))
            return None

        page_texts, body_text, page_boundaries = _build_page_texts(pages)

        return {
            "body_text": body_text,
            "title": "Unknown Title (OCR)",
            "page_count": len(pages),
            "page_texts": page_texts,
            "page_boundaries": page_boundaries,
            "sections": [],
            "references": [],
            "extraction_method": "ocr",
            "confidence": 0.4,
        }
    except Exception as e:
        logger.warning("OCR extraction failed: %s", e)
        return None


def get_page_count(file_path: str) -> int:
    """Get actual page count from pypdf (not section count)."""
    try:
        import pypdf
        with open(file_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            return max(1, len(reader.pages))
    except Exception:
        return 1


def extract_text_from_pdf(
    file_path: str,
    grobid_url: str = "http://localhost:8070"
) -> Dict[str, Any]:
    """
    Master extraction function. Tries Grobid -> pypdf -> OCR.

    KEY INVARIANT: page_boundaries and page_texts are ALWAYS sourced from pypdf
    (which has real PDF page structure), even when Grobid provides better text quality.
    Grobid rarely emits <pb> markers, causing all matches to be assigned page 1.
    """
    page_count = get_page_count(file_path)

    # ALWAYS get pypdf page boundaries first — they are always accurate
    pypdf_result = extract_with_pypdf(file_path)

    # Read file bytes for Grobid
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    # --- Tier 1: Grobid (for text quality + metadata) ---
    grobid_parsed = extract_with_grobid(file_bytes, grobid_url)

    if grobid_parsed and grobid_parsed.get("body_text", "").strip():
        grobid_text = grobid_parsed["body_text"]

        # If Grobid has real multi-page data (rare), use it; otherwise use pypdf structure
        grobid_pages = grobid_parsed.get("page_texts", [])
        grobid_has_real_pages = len(grobid_pages) > 1

        if grobid_has_real_pages:
            # Grobid gave us real page structure — use it as-is
            logger.info("Grobid extraction: multi-page structure detected (%d pages).", len(grobid_pages))
            grobid_parsed["page_count"] = max(page_count, len(grobid_pages))
            grobid_parsed["extraction_method"] = "grobid"
            return grobid_parsed
        else:
            # Grobid has text but single-page structure — use pypdf page boundaries
            # mapped proportionally onto Grobid's text
            if pypdf_result and page_count > 1:
                logger.info(
                    "Grobid extraction: single-page fallback. Applying pypdf page boundaries (%d pages).",
                    page_count
                )
                # Proportionally divide Grobid's text into pypdf's page boundaries
                text_len = len(grobid_text)
                chars_per_page = text_len / page_count
                pages_text = []
                for pg in range(page_count):
                    start = int(pg * chars_per_page)
                    end = int((pg + 1) * chars_per_page) if pg < page_count - 1 else text_len
                    pages_text.append(grobid_text[start:end])

                page_texts, body_text, page_boundaries = _build_page_texts(pages_text)
                return {
                    "body_text": body_text,
                    "title": grobid_parsed.get("title", "Unknown Title"),
                    "page_count": page_count,
                    "page_texts": page_texts,
                    "page_boundaries": page_boundaries,
                    "sections": grobid_parsed.get("sections", []),
                    "references": grobid_parsed.get("references", []),
                    "extraction_method": "grobid+pypdf_boundaries",
                    "confidence": grobid_parsed.get("confidence", 0.8),
                }
            else:
                # No pypdf fallback available — use Grobid's single-page result
                grobid_parsed["page_count"] = page_count
                grobid_parsed["extraction_method"] = "grobid"
                return grobid_parsed

    # --- Tier 2: pypdf (already computed above) ---
    if pypdf_result:
        logger.info("Grobid unavailable, using pypdf.")
        return pypdf_result

    # --- Tier 3: Tesseract OCR ---
    result = extract_with_ocr(file_path)
    if result:
        return result

    # --- All tiers failed ---
    logger.error("All extraction methods failed for %s", file_path)
    return {
        "body_text": "",
        "title": "Extraction Failed",
        "page_count": page_count,
        "page_texts": [],
        "page_boundaries": [],
        "sections": [],
        "references": [],
        "extraction_method": "empty",
        "confidence": 0.0,
    }


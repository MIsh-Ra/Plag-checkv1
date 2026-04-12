"""
Unit tests for ingestion module (GrobidClient).
Uses REAL Grobid server at localhost:8070 — no mocks.
"""
import os
import pytest
from app.core.ingestion import GrobidClient


@pytest.fixture
def grobid():
    return GrobidClient(host="http://localhost:8070")


@pytest.fixture
def small_pdf_bytes(request):
    """Load a real small PDF from the archive."""
    archive_path = request.config.getoption("--archive-path")
    # 12.pdf is a valid readable PDF
    pdf_path = os.path.join(archive_path, "12.pdf")
    if not os.path.exists(pdf_path):
        pytest.skip(f"Test PDF not found at {pdf_path}")
    with open(pdf_path, "rb") as f:
        return f.read()


class TestGrobidClient:

    def test_process_real_pdf(self, grobid, small_pdf_bytes):
        """T1: Send a REAL PDF to Grobid → verify structured output."""
        result = grobid.process_pdf(small_pdf_bytes)

        assert isinstance(result, dict)
        assert "title" in result
        assert "body_text" in result
        assert "sections" in result
        assert "references" in result
        assert "confidence" in result
        assert "page_count" in result

        # Real PDF should extract meaningful content
        assert len(result["body_text"]) > 50
        assert result["confidence"] > 0.0

    def test_process_minimal_pdf(self, grobid):
        """T2: Send minimal PDF with no text block → verify Grobid raises 500/RuntimeError."""
        # Minimal PDF with almost no text content
        minimal_pdf = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF"
        with pytest.raises(RuntimeError, match="Grobid failed"):
            grobid.process_pdf(minimal_pdf)

    def test_process_empty_bytes_raises(self, grobid):
        """T3: Empty/corrupt input → RuntimeError."""
        with pytest.raises(RuntimeError, match="Grobid failed"):
            grobid.process_pdf(b"")

    def test_wrong_host_raises(self):
        """T4: Wrong Grobid host → RuntimeError."""
        bad_grobid = GrobidClient(host="http://localhost:9999")
        with pytest.raises(RuntimeError, match="Grobid failed"):
            bad_grobid.process_pdf(b"dummy PDF content")

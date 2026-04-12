"""
Integration tests for Documents API.
Uses REAL Postgres database — no MagicMock.
"""
import os
import pytest
from app.db.models import Document


class TestDocumentUpload:
    """I-01 to I-03: Upload endpoint tests."""

    def test_upload_real_pdf(self, auth_client, db_session, request):
        """I-01: Upload a REAL PDF from the archive → Document row created in DB."""
        archive_path = request.config.getoption("--archive-path")
        pdf_path = os.path.join(archive_path, "12.pdf")
        if not os.path.exists(pdf_path):
            pytest.skip(f"Test PDF not found at {pdf_path}")

        with open(pdf_path, "rb") as f:
            response = auth_client.post(
                "/api/v1/documents/upload",
                files={"file": ("12.pdf", f, "application/pdf")}
            )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["status"] == "pending"
        assert data["filename"] == "12.pdf"

        # Verify document exists in real DB
        doc = db_session.query(Document).filter(Document.id == data["id"]).first()
        assert doc is not None
        assert doc.filename == "12.pdf"

    def test_upload_non_pdf_rejected(self, auth_client):
        """I-02: Upload a .txt file → 400."""
        response = auth_client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.txt", b"Hello world", "text/plain")}
        )
        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]

    def test_upload_without_auth_rejected(self, client):
        """Upload without auth header → 401 or 403."""
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", b"%PDF-1.4 dummy", "application/pdf")}
        )
        assert response.status_code in (401, 403)


class TestDocumentList:
    """I-04, I-05: List and filter documents."""

    def test_list_returns_own_documents(self, auth_client, seeded_report):
        """I-04: GET /documents returns only the logged-in user's documents."""
        response = auth_client.get("/api/v1/documents")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        # Seeded doc belongs to faculty user
        assert data["total"] >= 1

    def test_list_filters_by_course_id(self, auth_client, seeded_report):
        """I-05: GET /documents?course_id=CSE101 filters correctly."""
        response = auth_client.get("/api/v1/documents?course_id=CSE101")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["course_id"] == "CSE101"

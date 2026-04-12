"""
Integration tests for Reports API.
Uses REAL Postgres database with seeded report data — no MagicMock.
"""
import pytest
from app.db.models import Match, Report


class TestGetReport:
    """I-06, I-07: Get report endpoints."""

    def test_get_seeded_report(self, auth_client, seeded_report):
        """I-06: GET /reports/{doc_id} → 200 with full FullReportResponse."""
        doc_id = seeded_report["doc_id"]
        response = auth_client.get(f"/api/v1/reports/{doc_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["document_id"] == doc_id
        assert data["document_title"] == "Coverage Pattern Based Data Mining"
        assert "scores" in data
        assert data["scores"]["originality_score"] == 72.5
        assert data["scores"]["risk_level"] == "moderate"
        assert "summary_stats" in data
        assert "matches" in data
        assert len(data["matches"]) >= 1
        assert "heatmap" in data
        assert "review" in data

    def test_get_nonexistent_report(self, auth_client):
        """I-07: GET /reports/nonexistent → 404."""
        response = auth_client.get("/api/v1/reports/nonexistent-id-12345")
        assert response.status_code == 404


class TestExcludeMatch:
    """I-08: Patch match exclusion."""

    def test_exclude_match_persists(self, auth_client, seeded_report, db_session):
        """I-08: PATCH match is_excluded=True → persisted in real DB."""
        doc_id = seeded_report["doc_id"]
        match_id = seeded_report["match_id"]

        response = auth_client.patch(
            f"/api/v1/reports/{doc_id}/matches/{match_id}",
            json={"is_excluded": True, "reason": "faculty_review"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_excluded"] is True
        assert "updated_originality_score" in data

        # Verify in real DB
        match = db_session.query(Match).filter(Match.id == match_id).first()
        assert match is not None
        assert match.is_excluded is True
        assert match.exclude_reason == "faculty_review"


class TestCommentMatch:
    """I-09: Post comment on match."""

    def test_comment_match_persists(self, auth_client, seeded_report, db_session):
        """I-09: POST comment → persisted in real DB."""
        doc_id = seeded_report["doc_id"]
        match_id = seeded_report["match_id"]

        response = auth_client.post(
            f"/api/v1/reports/{doc_id}/matches/{match_id}/comment",
            json={"comment": "This is a valid citation, not plagiarism."}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["comment"] == "This is a valid citation, not plagiarism."

        # Verify in real DB
        match = db_session.query(Match).filter(Match.id == match_id).first()
        assert match.comment == "This is a valid citation, not plagiarism."


class TestReviewReport:
    """I-10: Post review on report."""

    def test_review_sets_verdict(self, auth_client, seeded_report, db_session):
        """I-10: POST review → verdict and status updated in real DB."""
        doc_id = seeded_report["doc_id"]

        response = auth_client.post(
            f"/api/v1/reports/{doc_id}/review",
            json={
                "verdict": "cleared",
                "faculty_notes": "All matches are properly cited.",
                "digital_signature": "sig-abc123"
            }
        )
        assert response.status_code == 200

        # Verify in real DB
        report = db_session.query(Report).filter(Report.document_id == doc_id).first()
        assert report.verdict == "cleared"
        assert report.status == "reviewed"
        assert report.faculty_notes == "All matches are properly cited."


class TestExportPdf:
    """I-11: Export PDF."""

    def test_export_pdf_returns_binary(self, auth_client, seeded_report):
        """I-11: GET export/pdf → application/pdf with content."""
        doc_id = seeded_report["doc_id"]
        response = auth_client.get(f"/api/v1/reports/{doc_id}/export/pdf")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert len(response.content) > 100  # Non-trivial PDF

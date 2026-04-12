"""
Integration tests for Auth and Admin APIs.
Uses REAL Postgres database with real bcrypt-hashed passwords — no MagicMock.
"""
import pytest
from jose import jwt
from app.core.config import settings


class TestAdminRBAC:
    """I-12, I-13: Role-based access control."""

    def test_faculty_cannot_access_admin_config(self, auth_client):
        """I-12: Faculty → GET /admin/config → 403."""
        response = auth_client.get("/api/v1/admin/config")
        assert response.status_code == 403

    def test_admin_can_access_config(self, admin_client):
        """I-13: Admin → GET /admin/config → 200 with valid schema."""
        response = admin_client.get("/api/v1/admin/config")
        assert response.status_code == 200
        data = response.json()
        assert "similarity_thresholds" in data
        assert "web_dragnet" in data
        assert "api_status" in data
        assert "archive_stats" in data


class TestAuthLogin:
    """I-14, I-15: Login with real users in real DB."""

    def test_login_valid_credentials(self, client):
        """I-14: Login with faculty@test.edu / testpass123 → real JWT."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "faculty@test.edu", "password": "testpass123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["role"] == "faculty"
        assert data["user_id"] == "test-faculty-id"

        # Decode and verify the JWT is valid
        decoded = jwt.decode(data["access_token"], settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        assert decoded["sub"] == "faculty@test.edu"
        assert decoded["role"] == "faculty"

    def test_login_wrong_password(self, client):
        """I-15: Wrong password → 401."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "faculty@test.edu", "password": "wrong_password"}
        )
        assert response.status_code == 401
        assert "Incorrect" in response.json()["detail"]

    def test_login_nonexistent_user_auto_reg_disabled(self, client):
        """Login with unknown user when auto-registration is disabled → 401."""
        # Save original, disable auto-reg
        original = settings.ALLOW_AUTO_REGISTRATION
        settings.ALLOW_AUTO_REGISTRATION = False
        try:
            response = client.post(
                "/api/v1/auth/login",
                json={"username": "nonexistent@test.edu", "password": "anypass"}
            )
            assert response.status_code == 401
        finally:
            settings.ALLOW_AUTO_REGISTRATION = original

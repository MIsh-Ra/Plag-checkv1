"""
Global test configuration for Alethian V2.
Connects to real Docker infrastructure (Postgres, Redis, Qdrant, Grobid).
Zero MagicMock — every fixture uses real services.
"""
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone

from app.db.models import Base, User, UserRole, Document, DocumentStatus, Report, Match, Source, HeatmapPage
from app.db.session import get_db
from app.api.dependencies import get_current_user
from app.main import app
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------------------------------------------------------------------
# Pytest custom options
# ---------------------------------------------------------------------------
def pytest_addoption(parser):
    parser.addoption(
        "--mock-serper", action="store_true", default=False,
        help="Mock Serper API calls instead of using real API key"
    )
    parser.addoption(
        "--archive-path", action="store",
        default=os.path.join(os.path.dirname(__file__), "..", "..", "..", "Alethian_documents"),
        help="Path to the Alethian_documents archive directory"
    )


# ---------------------------------------------------------------------------
# Database engine — connects to real Docker Postgres on port 5433
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER', 'alethian')}"
    f":{os.getenv('POSTGRES_PASSWORD', 'alethian_pass')}"
    f"@{os.getenv('POSTGRES_HOST', 'localhost')}"
    f":{os.getenv('POSTGRES_PORT', '5433')}"
    f"/{os.getenv('POSTGRES_DB', 'alethian_db')}"
)

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# Session-scoped: create tables + seed users (runs once per test session)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables and seed base users. Runs once before any test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        # Seed faculty user
        faculty = User(
            id="test-faculty-id",
            username="faculty@test.edu",
            email="faculty@test.edu",
            hashed_password=pwd_context.hash("testpass123"),
            full_name="Test Faculty",
            role=UserRole.faculty
        )
        # Seed admin user
        admin = User(
            id="test-admin-id",
            username="admin@test.edu",
            email="admin@test.edu",
            hashed_password=pwd_context.hash("adminpass123"),
            full_name="Test Admin",
            role=UserRole.admin
        )
        db.add(faculty)
        db.add(admin)
        db.commit()
    finally:
        db.close()

    yield

    # Cleanup after all tests
    Base.metadata.drop_all(bind=engine)


# ---------------------------------------------------------------------------
# Function-scoped: fresh DB session per test with rollback
# ---------------------------------------------------------------------------
@pytest.fixture(scope="function")
def db_session():
    """Provide a real DB session that rolls back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ---------------------------------------------------------------------------
# User fixtures — return real ORM objects from DB
# ---------------------------------------------------------------------------
@pytest.fixture
def faculty_user(db_session):
    return db_session.query(User).filter(User.id == "test-faculty-id").first()


@pytest.fixture
def admin_user(db_session):
    return db_session.query(User).filter(User.id == "test-admin-id").first()


# ---------------------------------------------------------------------------
# JWT token helpers
# ---------------------------------------------------------------------------
def _make_token(username: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=60)
    return jwt.encode(
        {"sub": username, "role": role, "exp": expire},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )


@pytest.fixture
def faculty_token():
    return _make_token("faculty@test.edu", "faculty")


@pytest.fixture
def admin_token():
    return _make_token("admin@test.edu", "admin")


# ---------------------------------------------------------------------------
# FastAPI TestClient with real DB session override
# ---------------------------------------------------------------------------
@pytest.fixture
def client(db_session):
    """TestClient wired to real Postgres via dependency override."""
    def _get_test_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_test_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def auth_client(client, faculty_token):
    """TestClient with faculty auth header pre-set."""
    client.headers["Authorization"] = f"Bearer {faculty_token}"
    return client


@pytest.fixture
def admin_client(client, admin_token):
    """TestClient with admin auth header pre-set."""
    client.headers["Authorization"] = f"Bearer {admin_token}"
    return client


# ---------------------------------------------------------------------------
# Seeded report fixture — creates a realistic Document + Report + Matches
# ---------------------------------------------------------------------------
@pytest.fixture
def seeded_report(db_session):
    """Create a realistic document with report, matches, sources, and heatmap in real DB."""
    import uuid as _uuid

    doc_id = str(_uuid.uuid4())
    report_id = str(_uuid.uuid4())
    source_id = str(_uuid.uuid4())
    match_id = str(_uuid.uuid4())

    doc = Document(
        id=doc_id,
        title="Coverage Pattern Based Data Mining",
        author="Khandelwal, Archit",
        filename="18UCC164.pdf",
        user_id="test-faculty-id",
        status=DocumentStatus.complete,
        page_count=15,
        course_id="CSE101",
        originality_score=72.5,
        risk_level="moderate"
    )
    db_session.add(doc)
    db_session.flush()

    source = Source(
        id=source_id,
        type="internal",
        title="Archive Document: Machine Learning Fundamentals",
        domain="internal",
        document_id=doc_id
    )
    db_session.add(source)
    db_session.flush()

    report = Report(
        id=report_id,
        document_id=doc_id,
        score=72.5,
        risk_level="moderate",
        status="unreviewed",
        processing_time_seconds=45
    )
    db_session.add(report)
    db_session.flush()

    match = Match(
        id=match_id,
        report_id=report_id,
        source_id=source_id,
        type="internal_exact",
        submitted_text="Data mining is the process of discovering patterns in large data sets involving methods at the intersection of machine learning, statistics, and database systems.",
        source_text="Data mining is the process of discovering patterns in large data sets involving methods at the intersection of machine learning, statistics, and database systems.",
        similarity=95.0,
        submitted_page=3,
        source_page=1,
        submitted_start_char=500,
        submitted_end_char=700,
        match_length_words=28,
        is_excluded=False
    )
    db_session.add(match)
    db_session.flush()

    heatmap = HeatmapPage(
        id=str(_uuid.uuid4()),
        report_id=report_id,
        page_number=1,
        density_score=0.15,
        internal_density=0.15,
        web_density=0.0,
        color="#eab308",
        match_count=1,
        dominant_type="internal"
    )
    db_session.add(heatmap)
    db_session.flush()

    return {
        "doc_id": doc_id,
        "report_id": report_id,
        "source_id": source_id,
        "match_id": match_id,
        "doc": doc,
        "report": report,
        "match": match,
        "source": source
    }


# ---------------------------------------------------------------------------
# Archive path fixture
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def archive_path(request):
    return request.config.getoption("--archive-path")


# ---------------------------------------------------------------------------
# Mock serper flag fixture
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_serper(request):
    return request.config.getoption("--mock-serper")

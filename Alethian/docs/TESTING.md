# Testing Guide

Alethian V2 uses a **100% zero-mock** testing architecture. Every test runs against real infrastructure — no `MagicMock`, no `unittest.mock`, no `@patch`. The test suite validates against real PostgreSQL, Redis, Qdrant, Grobid, and SentenceTransformer.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Run](#quick-run)
- [Test Architecture](#test-architecture)
- [Backend Tests](#backend-tests)
- [Frontend Tests](#frontend-tests)
- [Configuration Options](#configuration-options)
- [Writing New Tests](#writing-new-tests)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

1. **Docker & Docker Compose** — for infrastructure services
2. **Python 3.10+** with `pip`
3. **Node.js 18+** with `npm`
4. **~2GB free disk** — for SentenceTransformer model download on first run
5. **Alethian_documents/** — archive directory with real PDFs + `metadata.json`

### Install Python Test Dependencies

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
# Key test packages: pytest, pytest-cov, pytest-asyncio, httpx
```

---

## Quick Run

### One Command

```bash
cd Alethian
bash run_full_tests.sh
```

This will:
1. Start Docker infrastructure (Postgres, Redis, Qdrant, Grobid)
2. Wait for all services to be healthy
3. Seed the archive with 5 real PDFs
4. Run all 29 backend unit tests
5. Run all 23 backend integration/E2E tests
6. Generate a coverage report
7. Run all 12 frontend tests

### Selective Runs

```bash
cd backend
source venv/bin/activate

# Unit tests only
PYTHONPATH=. python -m pytest tests/unit/ -v

# Integration tests only
PYTHONPATH=. python -m pytest tests/system/ -v

# Single test file
PYTHONPATH=. python -m pytest tests/unit/test_shingling.py -v

# Single test
PYTHONPATH=. python -m pytest tests/unit/test_shingling.py::TestGenerateEmbedding::test_embedding_shape_and_values -v

# With coverage
PYTHONPATH=. python -m pytest tests/ --cov=app --cov-report=term-missing
```

---

## Test Architecture

### Zero-Mock Philosophy

Every test fixture connects to **real services**:

```
conftest.py
├── setup_database()        → Real Postgres (creates tables, seeds users with bcrypt)
├── db_session()            → Real SQLAlchemy session with transaction rollback
├── client()                → FastAPI TestClient wired to real DB
├── auth_client()           → Pre-authenticated (faculty JWT)
├── admin_client()          → Pre-authenticated (admin JWT)
├── seeded_report()         → Real Document + Report + Match + Source + HeatmapPage
├── faculty_user()          → Real ORM User object from DB
├── admin_user()            → Real ORM User object from DB
├── archive_path()          → Path to real PDF archive
└── mock_serper()           → Boolean flag for Serper API toggle
```

### Infrastructure Mapping

| Service | Docker Port | Host Port | Used By |
|:--------|:------------|:----------|:--------|
| PostgreSQL | 5432 | **5433** | conftest.py, all integration tests |
| Redis | 6379 | **6379** | celery_worker.py, WebSocket tests |
| Qdrant | 6333 | **6333** | test_similarity.py, seed_archive.py |
| Grobid | 8070 | **8070** | test_ingestion.py, seed_archive.py |

### Transaction Isolation

Each test function gets its own database session wrapped in a transaction that **rolls back** after the test completes. This ensures:
- Tests don't pollute each other
- Test order doesn't matter
- Parallel execution is safe (future enhancement)

```python
@pytest.fixture(scope="function")
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()    # ← All changes undone
    connection.close()
```

---

## Backend Tests

### Unit Tests (29 tests)

| File | Module Tested | Tests | Real Infrastructure |
|:-----|:-------------|------:|:--------------------|
| `test_shingling.py` | `core/shingling.py` | 6 | SentenceTransformer (all-MiniLM-L6-v2) |
| `test_similarity.py` | `core/similarity.py` | 5 | Qdrant at localhost:6333 |
| `test_web_dragnet.py` | `core/web_dragnet.py` | 8 | Serper API (toggleable) + DuckDuckGo |
| `test_report_engine.py` | `core/report_engine.py` | 6 | None (pure math/logic) |
| `test_ingestion.py` | `core/ingestion.py` | 4 | Grobid at localhost:8070 + real PDFs |

#### test_shingling.py
- `TestCreateSlidingWindows` — empty input, short text, correct window count, window_size=1
- `TestGenerateEmbedding` — real 384-dim vectors, cosine similarity of related texts
- `TestProcessTextIntoChunks` — full pipeline with page boundary assignment

#### test_similarity.py
- `TestQdrantManager` — collection creation, upsert + search, paraphrase detection
- `TestDeduplicate` — duplicate removal, unique preservation

#### test_web_dragnet.py
- `TestSelectSuspiciousChunks` — short text filtering, max_queries cap, density sorting
- `TestSerperClient` — real API search (skipped if `--mock-serper`), cache, DDG fallback (real)
- `TestAnalyzeCoherence` — domain coherence flagging (≥3 matches = coherent)

#### test_report_engine.py
- `TestCalculateOriginality` — 100% for no matches, partial scores, exclusion handling
- `TestGenerateHeatmap` — page count, green/red colors, dominant type
- `TestBuildSummaryStats` — match type counting, averages, excluded filtering
- `TestGenerateSourceBreakdown` — domain grouping, archive aggregation

#### test_ingestion.py
- Sends real PDF from archive → verifies title, body_text, sections, confidence
- Minimal PDF → sparse output
- Empty bytes → RuntimeError
- Wrong host → RuntimeError

### Integration/E2E Tests (23 tests)

| File | API Tested | Tests | Key Assertions |
|:-----|:-----------|------:|:---------------|
| `test_api_documents.py` | Documents | 5 | Real PDF upload, DB verification, auth enforcement |
| `test_api_reports.py` | Reports | 6 | FullReportResponse schema, match exclusion, review |
| `test_api_auth_and_admin.py` | Auth + Admin | 5 | Real bcrypt login, JWT decoding, RBAC |
| `test_e2e_workflows.py` | All | 7 | Login→Upload→List chain, cross-user isolation |

---

## Frontend Tests

```bash
cd frontend
npm test -- --run
```

| File | Component | Tests | Description |
|:-----|:----------|------:|:------------|
| `Login.test.jsx` | Login | 2 | Renders form, submits credentials |
| `Dashboard.test.jsx` | Dashboard | 1 | Renders document list |
| `ReportView.test.jsx` | ReportView | 2 | Score header, match list |
| `MatchCard.test.jsx` | MatchCard | 2 | Renders match details, type badge |
| `FilterBar.test.jsx` | FilterBar | 1 | Filter dropdowns |
| `ExportMenu.test.jsx` | ExportMenu | 1 | Export buttons |
| `reportStore.test.js` | Zustand store | 2 | State transitions |
| `client.test.js` | API client | 1 | Axios configuration |

---

## Configuration Options

### Command-Line Flags

| Flag | Default | Description |
|:-----|:--------|:------------|
| `--mock-serper` | `False` | Use DDG fallback instead of real Serper API |
| `--archive-path` | `../../Alethian_documents` | Path to PDF archive directory |

### Environment Variables

| Variable | Default | Description |
|:---------|:--------|:------------|
| `MOCK_SERPER` | `false` | Same as `--mock-serper` (used in `run_full_tests.sh`) |
| `ARCHIVE_PATH` | `./Alethian_documents` | Same as `--archive-path` (used in `run_full_tests.sh`) |
| `POSTGRES_PORT` | `5433` | Host port for test Postgres |

### Example: DGX Server

```bash
# Run tests against DGX archive
ARCHIVE_PATH=~/crawler_stuff/Downloads MOCK_SERPER=true bash run_full_tests.sh
```

---

## Writing New Tests

### Rules

1. **No MagicMock** — import from real modules, connect to real services
2. **Use fixtures** — `db_session`, `auth_client`, `admin_client`, `seeded_report`
3. **Use `flush()` not `commit()`** — preserves transaction rollback isolation
4. **Skip gracefully** — use `pytest.skip()` when archive PDFs aren't available
5. **Use `xfail` for flaky external services** — e.g., DuckDuckGo

### Template

```python
"""Tests for my_module. Uses REAL infrastructure — no mocks."""
import pytest
from app.core.my_module import my_function


class TestMyFunction:
    def test_basic_case(self, db_session):
        """Descriptive docstring with test ID."""
        result = my_function(db_session)
        assert result is not None

    def test_with_seeded_data(self, auth_client, seeded_report):
        """Tests against seeded report in real DB."""
        doc_id = seeded_report["doc_id"]
        response = auth_client.get(f"/api/v1/reports/{doc_id}")
        assert response.status_code == 200
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Alethian Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Start Infrastructure
        run: |
          cd Alethian/infrastructure
          docker compose up -d
          sleep 30  # Wait for Grobid

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install Backend
        run: |
          cd Alethian/backend
          pip install -r requirements.txt

      - name: Run Backend Tests
        run: |
          cd Alethian/backend
          PYTHONPATH=. python -m pytest tests/ -v --mock-serper --cov=app

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Run Frontend Tests
        run: |
          cd Alethian/frontend
          npm ci
          npm test -- --run
```

---

## Troubleshooting

### "Connection refused" on Postgres

```bash
# Verify Docker is running
docker ps | grep alethian_postgres

# Check port mapping
docker port alethian_postgres
# Should show 5432/tcp -> 0.0.0.0:5433
```

### "Grobid failed" in ingestion tests

```bash
# Grobid takes ~30s to start. Check health:
curl http://localhost:8070/api/isalive
# Should return: true

# If not, check logs:
docker logs alethian_grobid
```

### SentenceTransformer slow on first run

The model (~80MB) downloads on first run. Subsequent runs use the cached version at `~/.cache/torch/sentence_transformers/`.

### "Test PDF not found" skips

Ensure `Alethian_documents/` exists with PDFs:
```bash
ls Alethian_documents/*.pdf | head -5
# Should list PDF files
```

### Qdrant connection refused

```bash
# Check Qdrant is running
curl http://localhost:6333/dashboard
```

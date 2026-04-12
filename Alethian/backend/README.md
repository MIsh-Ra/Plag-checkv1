# Alethian Backend

FastAPI-based REST API server with Celery worker for asynchronous document analysis.

---

## Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Environment Variables

The backend reads from `Alethian/.env` (three directories up from `app/core/config.py`). See `.env.example` for all options. Critical variables:

| Variable | Default | Description |
|:---------|:--------|:------------|
| `POSTGRES_USER` | `alethian` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `alethian_pass` | PostgreSQL password |
| `POSTGRES_DB` | `alethian_db` | Database name |
| `POSTGRES_HOST` | `localhost` | DB host (`postgres` in Docker) |
| `POSTGRES_PORT` | `5432` | DB port (mapped to `5433` externally) |
| `REDIS_HOST` | `localhost` | Redis host |
| `QDRANT_HOST` | `localhost` | Qdrant host |
| `GROBID_URL` | `http://localhost:8070` | Grobid server URL |
| `SERPER_API_KEY` | _(empty)_ | Google Serper API key for web search |
| `JWT_SECRET` | `change-me-in-production` | JWT signing secret |
| `ALLOW_AUTO_REGISTRATION` | `True` | Allow new user self-registration on login |

---

## Running

```bash
# API Server (development)
PYTHONPATH=. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Celery Worker (separate terminal)
PYTHONPATH=. celery -A celery_worker worker --loglevel=info

# Both are required for document processing to work.
```

---

## API Endpoints

### Authentication (`/api/v1/auth`)

| Method | Path | Description |
|:-------|:-----|:------------|
| `POST` | `/login` | Login with username/password → JWT token |

### Documents (`/api/v1/documents`)

| Method | Path | Description | Auth |
|:-------|:-----|:------------|:-----|
| `POST` | `/upload` | Upload PDF for analysis | Faculty |
| `GET` | `/` | List user's documents (paginated, filterable) | Faculty |
| `GET` | `/{id}` | Get single document detail | Faculty (owner) |
| `POST` | `/batch` | Batch upload (deferred) | Faculty |
| `WS` | `/{document_id}/status` | Real-time processing progress | — |

### Reports (`/api/v1/reports`)

| Method | Path | Description | Auth |
|:-------|:-----|:------------|:-----|
| `GET` | `/{doc_id}` | Full originality report | Faculty (owner) |
| `GET` | `/{doc_id}/heatmap` | Page-level heatmap data | Faculty (owner) |
| `PATCH` | `/{doc_id}/matches/{match_id}` | Exclude/include a match | Faculty (owner) |
| `POST` | `/{doc_id}/matches/{match_id}/comment` | Add comment to a match | Faculty (owner) |
| `POST` | `/{doc_id}/review` | Submit faculty review verdict | Faculty (owner) |
| `GET` | `/{doc_id}/export/pdf` | Export report as PDF | Faculty (owner) |
| `GET` | `/{doc_id}/export/json` | Export report as JSON | Faculty (owner) |

### Admin (`/api/v1/admin`)

| Method | Path | Description | Auth |
|:-------|:-----|:------------|:-----|
| `GET` | `/config` | Get system configuration | Admin |
| `PATCH` | `/config` | Update similarity thresholds | Admin |

---

## Document Processing Pipeline

When a PDF is uploaded, the Celery worker executes this pipeline:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  1. Ingest   │────▶│ 2. Internal  │────▶│ 3. Web       │────▶│ 4. Report    │────▶│ 5. Index     │
│  (Grobid)    │     │   Similarity │     │   Dragnet    │     │   Generation │     │  (Qdrant)    │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
     10%                   40%                  60%                  85%                  100%

Broadcasts progress via Redis pub/sub → WebSocket → Frontend
```

### Stage Details

1. **Ingestion** — Sends PDF bytes to Grobid, which extracts title, authors, sections, references, and body text from TEI-XML. Falls back to `pdftotext` if Grobid is unreachable.

2. **Internal Similarity** — Chunks the body text into sliding windows, generates 384-dim embeddings via SentenceTransformer (`all-MiniLM-L6-v2`), and queries Qdrant for exact (≥0.95 cosine) and paraphrase (≥0.85 cosine) matches. Uses `difflib.SequenceMatcher` to confirm exact matches.

3. **Web Dragnet** — Selects suspicious chunks (≥30 words, low vocabulary diversity), queries Serper/DDG with the first 25 words, fetches and extracts text from discovered URLs, then compares semantically. Flags domains with ≥3 matches as "coherent sources."

4. **Report Generation** — Calculates originality score, generates page-level heatmaps, persists matches with source attribution, creates Source and HeatmapPage records.

5. **Indexing** — Indexes the new document's chunks in Qdrant for future comparisons.

---

## Database Schema

```
users ──────┐
            │ 1:N
documents ──┤
            │ 1:1
reports ────┤
            │ 1:N          1:N
            ├── matches ─── sources
            │
            └── heatmap_pages
```

### Key Models

| Model | Table | Primary Fields |
|:------|:------|:---------------|
| `User` | `users` | id, username, email, hashed_password, role (admin/faculty/student) |
| `Document` | `documents` | id, title, author, filename, status, user_id, page_count, originality_score |
| `Report` | `reports` | id, document_id, score, risk_level, status, verdict, faculty_notes |
| `Match` | `matches` | id, report_id, source_id, type, submitted_text, source_text, similarity |
| `Source` | `sources` | id, type, url, title, domain, document_id |
| `HeatmapPage` | `heatmap_pages` | id, report_id, page_number, density_score, color, dominant_type |

---

## Authentication

- **JWT-based** — Tokens are issued on login and included via `Authorization: Bearer <token>` header.
- **Roles** — `admin` (full access), `faculty` (own documents), `student` (future).
- **Auto-registration** — When `ALLOW_AUTO_REGISTRATION=True`, unknown usernames are automatically registered on first login. Disable in production.
- **Password hashing** — bcrypt via `passlib`.

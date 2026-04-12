# Alethian Development Roadmap v2.0

This document outlines the phased execution plan for building the Alethian v2 Plagiarism Detection System. It reflects the **current state** of the project and the **updated scope** (Internal Similarity + Web Dragnet + Expressive Report).

---

## Current Project Status Summary

| Phase | Status | Notes |
|---|---|---|
| Phase 1: Infrastructure | ✅ **Complete** | Docker (Postgres, Redis, Qdrant, Grobid), `.env` config |
| Phase 2: Frontend (Mocked) | ✅ **Complete** | React+Vite, Login, Dashboard, ReportView, AdminPanel with mock data |
| Phase 3.1: Backend Scaffold | ✅ **Complete** | FastAPI app, SQLAlchemy, Pydantic settings |
| Phase 3.2: Ingestion Engine | ✅ **Complete** | Grobid integration, PDF parsing, DB persistence |
| Phase 3.3: Reference Validation | ❌ **Removed** | Out of v2 scope |
| Phase 4.1: Internal Similarity | 🔲 **Not Started** | NEW priority |
| Phase 4.2: Web Dragnet | 🔲 **Not Started** | NEW priority |
| Phase 4.3: AI Forensics | ❌ **Removed** | Out of v2 scope |
| Phase 5: Report Engine | 🔲 **Not Started** | NEW: Extensive report (better than Turnitin) |
| Phase 6: Frontend v2 | 🔲 **Not Started** | Rebuild report UI with heatmap, charts, diff |
| Phase 7: Integration & QA | 🔲 **Not Started** | End-to-end testing |

---

## Phase 3 (Continued): Backend — Internal Similarity Engine

**Goal:** Implement the core plagiarism detection engine for peer-to-peer comparison.
**Prerequisites:** Phase 3.2 (Ingestion) ✅

- [ ] **3.4 Text Shingling Module** (`core/shingling.py`)
    - Implement 5-word sliding window shingle generation.
    - Implement MinHash signature computation (128 permutations, `datasketch` library).
    - Implement sentence-level embedding generation (`sentence-transformers`).

- [ ] **3.5 Similarity Engine** (`core/similarity.py`)
    - Implement Redis LSH index storage and querying.
    - Implement Qdrant vector storage and nearest-neighbor search.
    - Implement paragraph-level alignment for matched documents.
    - Implement batch comparison (all-vs-all within a course/cohort).

- [ ] **3.6 Database Schema Update** (`db/models.py`)
    - Add `Reports`, `Matches`, `Sources`, `HeatmapPages` models.
    - Add `course_id` field to `Documents`.
    - Migration script for existing data.

- [ ] **3.7 Celery Integration**
    - Create `similarity_task` in Celery worker.
    - Wire ingestion → similarity pipeline.
    - Add archive indexing (add to Redis/Qdrant after analysis).

---

## Phase 4: Backend — Web Dragnet Engine

**Goal:** Implement internet plagiarism detection via Google Search API.
**Prerequisites:** Phase 3 Internal Similarity ✅

- [ ] **4.1 Serper Client** (`core/web_dragnet.py`)
    - Implement `SerperClient` with rate limiting, caching, and retry logic.
    - Implement suspicious chunk selection (dense, uncited passages not matched internally).

- [ ] **4.2 Content Fetcher** (`core/content_fetcher.py`)
    - Fetch and extract text from source URLs.
    - Compare fetched content against submitted text (TF-IDF or fuzzy matching).

- [ ] **4.3 Source Coherence Analysis**
    - Detect ≥3 chunks mapping to the same domain.
    - Flag as "Systematic Web Plagiarism."

- [ ] **4.4 Celery Integration**
    - Create `web_dragnet_task` in Celery worker.
    - Wire similarity → web dragnet pipeline.
    - Implement graceful degradation (mark as "Pending" if Serper is down).

---

## Phase 5: Backend — Report Engine

**Goal:** Build the report scoring, aggregation, and export system.
**Prerequisites:** Phase 3 + Phase 4 ✅

- [ ] **5.1 Report Generator** (`core/report_engine.py`)
    - Aggregate findings from similarity + web dragnet into a unified report JSON.
    - Calculate originality score (percentage of unmatched content).
    - Generate per-page heatmap data (match density + dominant type).
    - Build source breakdown (unique sources, coverage percentages).
    - Build chart data (pie chart, bar chart distributions).

- [ ] **5.2 Report API Endpoints** (`api/reports.py`)
    - `GET /reports/{document_id}` — Full report data.
    - `GET /reports/{document_id}/heatmap` — Heatmap data.
    - `PATCH /reports/{document_id}/matches/{match_id}` — Exclude/restore with score recalculation.
    - `POST /reports/{document_id}/matches/{match_id}/comment` — Add faculty comment.
    - `POST /reports/{document_id}/review` — Mark as reviewed.
    - `GET /reports/{document_id}/export/pdf` — PDF export.
    - `GET /reports/{document_id}/export/json` — JSON export.

- [ ] **5.3 PDF Generation**
    - Server-side PDF rendering with cover page, charts, source list, match details.
    - Institutional branding support.

---

## Phase 6: Frontend v2 — Report Dashboard Rebuild

**Goal:** Rebuild the frontend report view to be more expressive than Turnitin.
**Prerequisites:** Phase 5 Report API ✅

- [ ] **6.1 State Management**
    - Install Zustand, create `reportStore.js` for report state, filters, and excludes.
    - Implement `useWebSocket` hook for real-time progress.

- [ ] **6.2 Report Components**
    - `ScoreHeader.jsx` — Originality score with risk badge.
    - `Heatmap.jsx` — Page thumbnail strip with color-coded density.
    - `DiffViewer.jsx` — Side-by-side submitted vs. source text.
    - `TextOverlay.jsx` — Full document text with inline color highlights.
    - `SourcePanel.jsx` — Source list with coverage bar charts.
    - `FilterBar.jsx` — Match type toggles.
    - `MatchCard.jsx` — Individual match detail with exclude/comment actions.
    - `PieChart.jsx` + `BarChart.jsx` — Source breakdown and per-page distribution.
    - `ExportMenu.jsx` — PDF/JSON/Print export options.

- [ ] **6.3 Dashboard Updates**
    - Add risk-level indicators (🔴🟡🟢) to document list.
    - Add course ID filter.
    - Add real-time progress bar via WebSocket.

- [ ] **6.4 Responsive & Print**
    - Mobile-friendly report summary.
    - Print-friendly CSS layout.

---

## Phase 7: Integration & QA

**Goal:** End-to-end testing with real documents and final polish.

- [ ] **7.1 API Integration**
    - Switch frontend from mock API to real Axios endpoints.
    - Verify authentication flow (JWT).
    - Test upload → progress → report rendering flow.

- [ ] **7.2 End-to-End Testing**
    - Test with a known plagiarized PDF (internal copy from archive).
    - Test with a PDF copied from a known web source.
    - Test batch comparison (multiple similar submissions).
    - Test report export (PDF and JSON).

- [ ] **7.3 Archive Seeding**
    - Script to bulk-import past theses into the local archive.
    - Verify MinHash + vector indices are populated correctly.

- [ ] **7.4 Deployment Preparation**
    - Finalize `docker-compose.yml` for production (resource limits, restart policies).
    - Update `README.md` with full deployment instructions.
    - Performance benchmarking (50-page thesis target: <5 minutes).

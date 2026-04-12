# Alethian v2 — Implementation Plan

**Version:** 2.0  
**Date:** April 9, 2026  
**Scope:** Internal Similarity + Web Dragnet + Expressive Report

---

## Current State

| What's Done | What's Remaining |
|---|---|
| ✅ Docker infra (Postgres, Redis, Qdrant, Grobid) | 🔲 DGX Archive ingestion pipeline |
| ✅ Frontend scaffold with mock data | 🔲 Internal Similarity Engine |
| ✅ FastAPI + Pydantic settings | 🔲 Web Dragnet Engine |
| ✅ Grobid ingestion + PDF parsing + DB persistence | 🔲 Report Engine |
| ✅ **Proven prototype** in `backup/` (web search, similarity, chunking) | 🔲 Frontend v2 (report components) |

> **Scope Change:** Reference Validation and AI Forensics are **removed**. Focus is **Internal Similarity + Web Dragnet + Expressive Report**.

> **Existing Code to Reuse from `backup/`:**
> - `web_engine.py` — Working Serper.dev client + DuckDuckGo fallback + HTML content fetcher
> - `similarity_checker.py` — `all-MiniLM-L6-v2` semantic comparison (proven)
> - `text_processor.py` — 3-sentence sliding window chunker + query extraction
> - `main.py` — End-to-end orchestration (proven flow)

---

## Phase 0: DGX Archive Ingestion

### Context
The institutional archive lives on the **DGX server** (`172.22.2.20`) as a **DSpace repository**. Documents are PDFs (~1GB total as of now). The Alethian system will also run on the same DGX in production. For local testing, the archive can be SCP'd (~1GB).

### Metadata Structure (Dublin Core — DSpace)
Each document has the following metadata, scraped from the DSpace XMLUI HTML:

| Field | Source Tag | Example |
|---|---|---|
| **Author** | `DC.creator` | `SEEKARWAR, DAKSHYA (18UME063)` |
| **Title** | `DC.title` | `ZERO VOLTAGE FLUCTUATION SMAW` |
| **Abstract** | `DCTERMS.abstract` | Full abstract text |
| **Department** | `DC.publisher` | `Department of Mechanical-Mechatronics Engineering, LNMIIT Jaipur` |
| **Subject/Keywords** | `DC.subject` | `ZERO VOLTAGE FLUCTUATION` |
| **Type** | `DC.type` | `Thesis` |
| **Date Issued** | `DCTERMS.issued` | `2020-12` |
| **Date Accepted** | `DCTERMS.dateAccepted` | `2022-10-19T07:39:03Z` |
| **Language** | `DC.language` | `en` |
| **PDF URL** | `citation_pdf_url` | `http://172.22.2.20:8080/xmlui/bitstream/123456789/2843/1/18UME063.pdf` |
| **Handle/URI** | `DC.identifier` | `http://hdl.handle.net/123456789/2843` |
| **Supervisor** | `DC.description` | `Under Guidance of: Dr. MANOJ KUMAR` |

### Implementation

#### [NEW] `scripts/ingest_archive.py`
Batch importer that:
1. **Scrapes DSpace XMLUI** — Crawls `http://172.22.2.20:8080/xmlui/` listing pages, extracts Dublin Core meta tags from each item page.
2. **Downloads PDFs** — Fetches from `citation_pdf_url` to local storage.
3. **Processes via Grobid** — Extracts structured text from each PDF.
4. **Indexes for similarity** — Generates MinHash signatures → Redis, sentence embeddings → Qdrant.
5. **Stores metadata** — Persists document record + metadata in PostgreSQL.
6. **Incremental** — Tracks processed handles to avoid re-ingesting.

#### [MODIFY] `backend/app/db/models.py`
Add `ArchiveMetadata` JSON column to `Document` model to store Dublin Core fields:
```python
archive_metadata = Column(JSONB, nullable=True)
# {
#   "dc_creator": "SEEKARWAR, DAKSHYA (18UME063)",
#   "dc_title": "ZERO VOLTAGE FLUCTUATION SMAW",
#   "dc_abstract": "...",
#   "dc_department": "Department of Mechanical-Mechatronics Engineering...",
#   "dc_subject": "ZERO VOLTAGE FLUCTUATION",
#   "dc_type": "Thesis",
#   "dc_date_issued": "2020-12",
#   "dc_supervisor": "Dr. MANOJ KUMAR",
#   "dc_handle": "http://hdl.handle.net/123456789/2843",
#   "dc_pdf_url": "http://172.22.2.20:8080/xmlui/bitstream/..."
# }
```

#### Testing Strategy
- SCP ~1GB archive to local machine for development.
- Test ingestion script on a small batch (10–20 theses) first.
- Verify MinHash and vector indices populate correctly.

---

## Phase 1: Data Layer Expansion

### [MODIFY] `backend/app/db/models.py`
- Add models: `User`, `Report`, `Match`, `Source`, `HeatmapPage`
- Add `course_id`, `is_archived`, `archive_metadata` columns to `Document`

### [NEW] `backend/app/schemas/` directory
- `document.py` — Upload request/response, list with pagination
- `report.py` — Full report response, heatmap data, review request
- `match.py` — Match exclusion, comment request/response
- `admin.py` — Config get/update

---

## Phase 2: Internal Similarity Engine

### [NEW] `backend/app/core/shingling.py`
- Reuses sliding-window approach from `backup/text_processor.py` (3-sentence windows)
- Adds MinHash signature generation (`datasketch`, 128 permutations)
- Adds sentence embedding generation (reuses `backup/similarity_checker.py` model: `all-MiniLM-L6-v2`)

### [NEW] `backend/app/core/similarity.py`
- `RedisLSHIndex` — Store/query MinHash signatures
- `QdrantManager` — Store/query sentence vectors
- `paragraph_align()` — Exact text alignment for matched docs
- `run_similarity(document_id)` — Orchestrator
- `index_document(document_id)` — Add to archive after analysis

### Dependencies
Add to `requirements.txt`: `datasketch`, `sentence-transformers`, `qdrant-client`

---

## Phase 3: Web Dragnet Engine (Builds on `backup/`)

### Suspicious Chunk Detection Strategy

**Goal:** Minimize API calls. Only query Serper for chunks that are genuinely suspicious.

**4-Layer Filtering Pipeline:**

| Step | Filter | What It Catches | API Call? |
|---|---|---|---|
| 1 | **Already matched internally** | Skip — already flagged by Phase 2 | ❌ |
| 2 | **Short/trivial chunks** | Skip <30 words, headings, references, tables, TOC | ❌ |
| 3 | **Vocabulary diversity** | Skip if unique_words/total_words > 0.7 (likely original) | ❌ |
| 4 | **Density scoring** | Rank remaining by suspiciousness: long unbroken passages without citations, low sentence variety, formulaic structure. Query only **top-N** | ✅ (top-N only) |

**Configurable limit:** Max N queries per document (default: 15–20). Admin-adjustable.

**Result:** For a 50-page thesis, ~15 API calls instead of hundreds.

### [NEW] `backend/app/core/web_dragnet.py`
Refactors `backup/web_engine.py` + `backup/main.py`:
- `SerperClient` — Ported with: rate limiting, Redis caching, DuckDuckGo fallback
- `select_suspicious_chunks(text, internal_matches)` — 4-layer filter
- `run_dragnet(document_id)` — Orchestrator

### [NEW] `backend/app/core/content_fetcher.py`
Refactors `backup/web_engine.py:download_url_text()`:
- `fetch_page_text(url)` — Same HTML cleanup, added timeout + caching
- `compare_snippets(submitted, source)` — From `backup/similarity_checker.py`
- `analyze_coherence(matches)` — Group by domain, flag ≥3 from same

---

## Phase 4: Report Engine + API

### [NEW] `backend/app/core/report_engine.py`
- `calculate_originality(matches, doc_word_count)` → 0–100%
- `generate_heatmap(matches, page_count)` → per-page data
- `build_source_breakdown(matches)` → unique sources + coverage
- `build_chart_data(matches)` → pie + bar chart data
- `recalculate_after_exclusion(report_id, match_id)`

### [NEW] `backend/app/api/reports.py`
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/reports/{document_id}` | Full report |
| GET | `/reports/{document_id}/heatmap` | Heatmap data |
| PATCH | `/reports/{document_id}/matches/{match_id}` | Exclude/restore match |
| POST | `/reports/{document_id}/matches/{match_id}/comment` | Faculty comment |
| POST | `/reports/{document_id}/review` | Mark reviewed |
| GET | `/reports/{document_id}/export/pdf` | PDF export |
| GET | `/reports/{document_id}/export/json` | JSON export |

### [MODIFY] `backend/app/api/documents.py`
- Add `course_id` to upload, status/score to list response
- WebSocket endpoint for progress

### [MODIFY] `backend/celery_worker.py`
- `analyze_document` task: ingestion → similarity → dragnet → report

---

## Phase 5: Frontend v2 — Report Rebuild

### [NEW] 10 Report Components (`frontend/src/components/report/`)
| Component | Purpose |
|---|---|
| `ScoreHeader.jsx` | Originality score + risk badge + summary stats |
| `Heatmap.jsx` | Page thumbnail strip, color-coded by density |
| `DiffViewer.jsx` | Side-by-side submitted vs. source text |
| `TextOverlay.jsx` | Full text with inline color highlights |
| `SourcePanel.jsx` | Ranked source list + coverage bars |
| `FilterBar.jsx` | Match type toggles |
| `MatchCard.jsx` | Individual match with exclude/comment actions |
| `PieChart.jsx` | Source breakdown (Recharts) |
| `BarChart.jsx` | Per-page distribution (Recharts) |
| `ExportMenu.jsx` | PDF/JSON/Print buttons |

### [MODIFY] `ReportView.jsx` — Full rewrite: three-panel layout
### [MODIFY] `Dashboard.jsx` — Risk indicators, WebSocket progress, course filter
### [NEW] `stores/reportStore.js` (Zustand), `hooks/useWebSocket.js`, `hooks/useReport.js`
### Dependencies: `recharts`, `zustand`

---

## Verification Plan

### Automated Tests
```bash
cd Alethian && python -m pytest tests/unit/ -v
cd Alethian && bash tests/run_tests.sh
```

### Manual Verification
1. **Archive ingestion** — Ingest 10 DSpace theses, verify Redis + Qdrant populated
2. **Internal similarity** — Upload a thesis already in archive, verify matches
3. **Web dragnet** — Upload web-copied content, verify matches found
4. **Suspicious chunk filtering** — Verify only top-N chunks get API calls
5. **Report** — Verify score, heatmap, charts, source list render correctly
6. **Exclude match** — Verify score recalculates
7. **Export PDF** — Verify cover page, charts, match details
8. **Full E2E** — Login → Upload → Progress → Report → Export

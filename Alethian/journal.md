# Alethian Change Journal

> **Purpose**: Audit trail for all modifications made outside the original spec.  
> Every code change MUST have a corresponding entry here before the change is made.

---

## Backfilled Entries (Uncommitted changes as of 2026-04-18 03:57 IST)

These entries were retroactively documented from `git diff --cached` on 2026-04-18. All changes below were made during conversations on 2026-04-17 while setting up the local dev environment and fixing UI bugs.

---

### Entry 1
- **Date/Time**: 2026-04-17 ~21:00 IST
- **File Modified**: `Alethian/backend/app/api/documents.py`
- **What Changed**:
  - Moved `import sys`, `import re`, `import tempfile` to top-level (were inline imports inside the upload handler).
  - Added `import logging` and module-level `logger = logging.getLogger(__name__)`.
  - Replaced hardcoded `/tmp/` path with `os.path.join(tempfile.gettempdir(), ...)` for Windows compatibility.
  - Replaced `print("Failed to dispatch celery task:", e)` with `logger.warning(f"Failed to dispatch celery task: {e}")`.
  - Added `logger.exception("Upload handler error")` in the outer exception handler.
- **Why**: The original code used Unix-only `/tmp/` paths, which fail on Windows. Inline imports were moved to module level for clarity. Print statements were replaced with proper logging for production readiness.

---

### Entry 2
- **Date/Time**: 2026-04-17 ~21:00 IST
- **File Modified**: `Alethian/backend/celery_worker.py`
- **What Changed**:
  - Replaced `_fallback_extract` implementation: removed `subprocess.run(["pdftotext", ...])` dependency and replaced with `pypdf.PdfReader` for pure-Python PDF text extraction.
  - Added logging to the fallback extractor.
  - Removed commented-out `doc.meta_data` block (dead code).
  - Added a validation check: if Grobid returns very little text (`len(text.strip()) < 50`), raise an error to trigger the fallback path.
  - Updated the Grobid failure log message to mention "or returned empty text".
- **Why**: `pdftotext` is a system binary (`poppler-utils`) not available on Windows without extra installation. `pypdf` is a pure-Python alternative already suitable for the project. The empty-text guard prevents silent failures when Grobid parses a PDF but extracts nothing useful.

---

### Entry 3
- **Date/Time**: 2026-04-17 ~21:00 IST
- **File Modified**: `Alethian/backend/requirements.txt`
- **What Changed**:
  - Added `pypdf` as a new dependency.
- **Why**: Required by the updated `_fallback_extract` in `celery_worker.py` (Entry 2). Replaces the external `pdftotext` system dependency.

---

### Entry 4
- **Date/Time**: 2026-04-17 ~21:15 IST
- **File Modified**: `Alethian/frontend/src/hooks/useReport.js`
- **What Changed**:
  - Added `documentData` state alongside existing `report` state.
  - Renamed internal `fetchReport` to `fetchData`.
  - Now fetches the document status via `Client.documents.get(id)` first, then only fetches the report if the document status is `'complete'` or `'ready'`.
  - Exposed `documentData` in the return value.
- **Why**: The original hook assumed the report was always available immediately. When a document is still processing, the report endpoint returns 404, causing the ReportView to show "Report not found" instead of a processing indicator. By fetching document status first, the UI can distinguish between "still processing" and "genuinely missing".

---

### Entry 5
- **Date/Time**: 2026-04-17 ~21:15 IST
- **File Modified**: `Alethian/frontend/src/pages/Dashboard.jsx`
- **What Changed**:
  - Expanded processing status detection from just `'processing'` to `['pending', 'ingesting', 'analyzing', 'processing']`.
  - Added a dedicated error/failed status badge (`bg-red-100` with `AlertTriangle` icon).
  - Added null-safe `displayScore` fallback (`score || 0`) for the risk badges.
  - Changed document title display to prefer `doc.filename` over `doc.title`, with `'Unknown Document'` fallback.
  - Added `'Unknown'` fallback for `doc.author`.
  - Updated the progress bar condition to match the expanded processing statuses array.
- **Why**: Newly uploaded documents start in `'pending'` status, not `'processing'`. The original code only checked for `'processing'`, so pending/ingesting documents showed a misleading "High Risk" badge (because `score` was `null`/`0`, which is `< 50`). The `doc.title` was also showing "Unknown Title" because the backend sets the real title only after Grobid parsing completes.

---

### Entry 6
- **Date/Time**: 2026-04-17 ~21:15 IST
- **File Modified**: `Alethian/frontend/src/pages/ReportView.jsx`
- **What Changed**:
  - Added `Loader2` import from `lucide-react`.
  - Added `useWebSocket` hook import.
  - Destructured `documentData` from `useReport(id)` and `wsStatus` from `useWebSocket(id)`.
  - Added a full processing-state screen: if the document status is in `['pending', 'ingesting', 'analyzing', 'processing']`, shows a spinner, status message, progress bar (from WebSocket), and back-to-dashboard button instead of the report.
  - Moved the "Report not found" fallback to after the processing check.
- **Why**: When a user clicks "View Report" on a still-processing document, the page showed "Report not found" because no report exists yet. Now it shows a live processing screen with real-time progress from the WebSocket connection.

---

### Entry 7
- **Date/Time**: 2026-04-17 ~21:30 IST
- **File Modified**: `Alethian/generate_test_pdfs.py` **(NEW FILE)**
- **What Changed**:
  - Created a script using `fpdf` to generate three test PDFs:
    1. `Test_1_Web_Plagiarism.pdf` — Text copied from Wikipedia (Quantum Mechanics).
    2. `Test_2_Internal_Original.pdf` — Original fictional content about a "Quantum-Neuro Interface".
    3. `Test_3_Internal_Paraphrased.pdf` — Paraphrased version of Test 2.
- **Why**: Needed test documents to validate the plagiarism detection pipeline end-to-end. Test 1 targets web dragnet detection, Tests 2+3 target internal similarity detection.

---

### Entry 8
- **Date/Time**: 2026-04-17 ~21:30 IST
- **Files Added**:
  - `Alethian/test_pdfs/Test_1_Web_Plagiarism.pdf`
  - `Alethian/test_pdfs/Test_2_Internal_Original.pdf`
  - `Alethian/test_pdfs/Test_3_Internal_Paraphrased.pdf`
- **What Changed**: Generated binary PDF files from `generate_test_pdfs.py`.
- **Why**: Output of Entry 7. These are the actual test fixtures for manual upload testing.

---

## Fix: Plagiarism Detection Returning "100% Clean" (2026-04-18)

Investigation found three root causes why all test PDFs report 100% originality despite containing plagiarised content. See implementation_plan.md for full diagnosis.

---

### Entry 9
- **Date/Time**: 2026-04-18 04:00 IST
- **File Modified**: `Alethian/backend/app/core/web_dragnet.py`
- **What Changed**:
  - In `select_suspicious_chunks`, raised the `unique_ratio` filter threshold from `0.7` to `0.85`.
  - Previously, any chunk with >70% unique words was skipped. Academic/technical text routinely hits 70–80% unique words due to specialised vocabulary, so nearly all chunks were being discarded before any web search was attempted.
- **Why**: Test 1 (Wikipedia Quantum Mechanics text) produced chunks with unique ratios of 0.700–0.750. The 0.7 threshold meant only 1 of 3 chunks passed the filter, and the other 2 (including highly plagiarised content) were silently skipped. Raising to 0.85 ensures technical prose is not wrongly classified as "likely original".

---

### Entry 10
- **Date/Time**: 2026-04-18 04:00 IST
- **File Modified**: `Alethian/backend/app/core/content_fetcher.py`
- **What Changed**:
  - Rewrote `compare_snippets` to split `source_text` (the fetched web page) into overlapping windows of ~200 words, compute cosine similarity of each window against the submitted chunk, and return the maximum score.
  - Previously, the function encoded the entire web page as a single embedding and compared it to the small chunk. A 50-word chunk vs. a 5000-word page produces a heavily diluted embedding, so the similarity score always fell below the 0.15 threshold in `run_dragnet`.
- **Why**: Verified with test script: a known-matching chunk scored 0.98 against a short page but only 0.08 against the same text buried in a long page. The windowed approach finds the best-matching segment within the page.

---

### Entry 11
- **Date/Time**: 2026-04-18 04:00 IST
- **File Modified**: `Alethian/backend/celery_worker.py`
- **What Changed**:
  - Moved the `index_document(...)` call from Stage 5 (after report generation, line 189) to Stage 1.5 (immediately after text extraction and before `run_similarity`, around line 114).
  - `run_similarity` already filters out `document_id == current_doc`, so self-matches are not a concern.
- **Why**: When uploading Test 2 (original) and Test 3 (paraphrased) in sequence, Test 3's similarity check ran before Test 2 had been indexed (indexing was the last step). Moving indexing earlier ensures that each document is in the archive before subsequent documents check against it.

---

## Fix: ReportView UI Bugs (2026-04-18)

Fixing multiple UI bugs reported by the user regarding layout, alignment, component rendering, and filter wiring.

---

### Entry 12
- **Date/Time**: 2026-04-18 04:20 IST
- **File Modified**: `Alethian/frontend/src/App.css`
- **What Changed**: Removed the `#root` CSS block which contained `text-align: center`, `max-width`, `margin`, and `padding`.
- **Why**: The default Vite template styles were forcing center alignment on all text in the document viewer and constraining the app width, conflicting with Tailwind's layout utility classes.

---

### Entry 13
- **Date/Time**: 2026-04-18 04:20 IST
- **File Modified**: `Alethian/frontend/src/pages/ReportView.jsx`
- **What Changed**: 
  - Restructured the center `<main>` panel to use a flex-col layout with two distinct scrollable panes: the top for the `TextOverlay` and a fixed `h-1/3` bottom pane for the `DiffViewer`.
  - Wired up `filterTypes` from `useReportStore` to actually filter the `matches` array before rendering `MatchCard` components and selecting the `selectedMatch`.
- **Why**: 
  - The `DiffViewer` was previously just appended below the text. Without a proper flex layout, scrolling caused it to visually overlap the text. A split-pane view provides the "side-by-side" / separated layout the user expects.
  - The `FilterBar` was updating state but `ReportView` wasn't consuming that state to filter the rendered list.

---

### Entry 14
- **Date/Time**: 2026-04-18 04:20 IST
- **File Modified**: `Alethian/frontend/src/components/report/PieChart.jsx`
- **What Changed**: Replaced the hardcoded fixed-size pie chart with a `ResponsiveContainer`. Added `Cell` mapping with a `COLORS` array for distinct slice colors, and added a `Legend`.
- **Why**: The pie chart was an unreadable single-color block and lacked a legend explaining what the sections meant.

---

### Entry 15
- **Date/Time**: 2026-04-18 04:20 IST
- **File Modified**: `Alethian/frontend/src/components/report/Heatmap.jsx`
- **What Changed**: Changed the heatmap container from `flex flex-wrap` to `grid grid-cols-5`. Applied `aspect-[3/4]` to the page blocks and rendered the page number inside each block.
- **Why**: When a document had only 1 page, the heatmap rendered as a tiny standalone square which didn't look like a "grid". Enforcing a grid layout with paper-ratio blocks and visible page numbers makes the UI intent clear.

---

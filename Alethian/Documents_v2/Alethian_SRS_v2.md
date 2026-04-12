# Software Requirements Specification (SRS)
## Project Name: Alethian
**Version:** 2.0  
**Date:** April 9, 2026  
**Document Status:** Final Draft  
**Scope Change:** Focused on Internal Similarity + Web Dragnet detection with an expressive, Turnitin-class reporting system.

---

## 1. Introduction

### 1.1 Purpose
This document defines the functional and non-functional requirements for **Alethian v2**, a Local-First Plagiarism Detection System. Alethian v2 focuses on two core detection capabilities — **Internal Similarity** (peer-to-peer copying against a local archive) and **Web Dragnet** (systematic internet plagiarism detection) — combined with an **expressive, faculty-facing report** that surpasses the clarity and thoroughness of commercial tools like Turnitin.

### 1.2 Scope
Alethian v2 is a self-hosted web application deployed on institutional hardware. It processes academic documents (PDFs) through a streamlined pipeline:

1.  **Ingestion:** Hybrid extraction of text and structure from PDFs.
2.  **Internal Similarity:** Comparison against a private, local archive of past student submissions using syntactic (MinHash/LSH) and semantic (vector embeddings) methods.
3.  **Web Dragnet:** Targeted search of suspicious content against the open internet using Google Search API, with source coherence analysis.
4.  **Presentation & Report:** A decoupled, interactive dashboard for faculty review, producing an expressive forensic report with side-by-side evidence, heatmaps, and exportable signed PDF summaries.

### 1.3 Out of Scope (Deferred to Future Versions)
*   **Reference Validation (API Mesh):** Citation existence verification, hallucination detection, retraction checking.
*   **AI Forensics:** Binoculars metric, perplexity/burstiness analysis, AI-generated text detection.

### 1.4 Definitions, Acronyms, and Abbreviations
| Term | Definition |
|---|---|
| **LSH** | Locality Sensitive Hashing — algorithm for rapid near-duplicate document detection |
| **MinHash** | A probabilistic technique for computing Jaccard similarity of sets |
| **Source Coherence** | Detection of multiple copied text chunks originating from a single un-cited domain |
| **Shingle** | A contiguous subsequence of tokens (words) used for text fingerprinting |
| **Similarity Score** | A 0–100% metric indicating the proportion of a document that matches known sources |
| **Originality Score** | Inverse of Similarity Score (100 - Similarity%) — the "clean" portion |
| **SPA** | Single Page Application (React.js) |
| **Heatmap** | A page-by-page color visualization showing density of matched content |

---

## 2. Overall Description

### 2.1 Product Perspective
Alethian v2 operates as a standalone system within the university's intranet. It interacts with:
*   **Internal Storage:** For archiving past theses and building a comparison corpus.
*   **External APIs:** Serper.dev (Google Search) for web plagiarism detection — transient data only.
*   **LMS (Future Scope):** Potential integration with Moodle/Canvas.

### 2.2 User Classes and Characteristics
| Role | Capabilities |
|---|---|
| **Faculty/Reviewers** | Upload documents, view detailed plagiarism reports, toggle forensic layers, side-by-side comparison, export signed PDF summaries |
| **Administrators** | Manage system configuration, API keys, user access roles, similarity thresholds |
| **System** | Background service accounts handling ingestion, indexing, and analysis |

### 2.3 Operating Environment
| Component | Specification |
|---|---|
| **Server** | Ubuntu 24.04 LTS (High-Performance "Fat Node") |
| **Client** | Modern Web Browsers (Chrome, Firefox, Edge) |
| **Network** | Institutional Intranet (Local-First) |
| **GPU** | Optional — only needed if OCR fallback (Llama-3-Vision) is enabled |

---

## 3. System Features (Functional Requirements)

### 3.1 Layer 1: The Ingestion Engine
**Description:** Converts unstructured PDF binary data into normalized, structured JSON for downstream analysis.

| ID | Requirement |
|---|---|
| **FR-1.1** | The system shall accept PDF file uploads up to 100MB. |
| **FR-1.2** | The system shall utilize **Grobid** as the primary parser for structured text/reference extraction. |
| **FR-1.3** | If Grobid confidence is `< 0.8` (e.g., scanned images), the system shall route the document to **Llama-3-Vision** for OCR fallback. |
| **FR-1.4** | Output shall be a normalized JSON: `{Title, Authors, Abstract, Body_Text[page_indexed], References_List}`. |
| **FR-1.5** | The system shall segment body text into **shingles** (5-word sliding window) for downstream fingerprinting. |
| **FR-1.6** | The system shall persist the raw text and shingles to the database immediately after ingestion. |

### 3.2 Layer 2: Internal Similarity (The Memory)
**Description:** Detects plagiarism against the local archive of all past submissions at the institution. This is the primary detection engine for peer-to-peer copying.

| ID | Requirement |
|---|---|
| **FR-2.1** | The system shall generate a **MinHash Signature** (128 permutations) for each document and store it in the **Redis** LSH index. |
| **FR-2.2** | On new submission, the system shall query Redis for near-duplicates (Jaccard similarity > 0.5). |
| **FR-2.3** | For every matched pair, the system shall perform **paragraph-level alignment** to identify the exact copied sections and their page numbers. |
| **FR-2.4** | For paragraphs not caught by MinHash (paraphrased content), the system shall generate **sentence-level vector embeddings** (e.g., `all-MiniLM-L6-v2`) and query the **Qdrant** database for semantic matches (cosine similarity > 0.85). |
| **FR-2.5** | Each match shall record: `source_document_id`, `source_page`, `source_text`, `submitted_page`, `submitted_text`, `match_type` (exact/paraphrase), `similarity_score`. |
| **FR-2.6** | After analysis, the submitted document's fingerprints shall be added to the archive for future comparisons. |
| **FR-2.7** | The system shall support **batch comparison** across an entire submission cohort (e.g., all papers from a course) to detect inter-student copying. |

### 3.3 Layer 3: Web Dragnet (The Hunter)
**Description:** Detects systematic copying from the open internet. Operates on text chunks that were not flagged by Internal Similarity.

| ID | Requirement |
|---|---|
| **FR-3.1** | The system shall isolate **"Suspicious Chunks"** — text segments not matched in Layer 2 that exhibit high textual density (long unbroken passages without citations). |
| **FR-3.2** | The system shall query **Serper.dev** (Google Search API) with shingle-based queries (≈50 words per query). |
| **FR-3.3** | For each search result, the system shall **fetch and compare** the source page content against the submitted chunk to confirm the match and compute a snippet-level similarity score. |
| **FR-3.4** | The system shall perform **Source Coherence Analysis**: if ≥3 chunks map to the same un-cited domain, the submission is flagged for **"Systematic Web Plagiarism."** |
| **FR-3.5** | Each web match shall record: `source_url`, `source_domain`, `source_snippet`, `submitted_page`, `submitted_text`, `match_score`. |
| **FR-3.6** | The system shall implement **rate limiting** and **caching** to prevent Serper API quota exhaustion and avoid re-querying known URLs. |
| **FR-3.7** | If Serper API is unreachable, the system shall degrade gracefully: complete internal checks and mark web checks as "Pending." |

### 3.4 Layer 4: Presentation & Reporting (The Interface)
**Description:** Provides an interactive, forensic-grade dashboard that enables faculty to deeply understand every finding. The report is designed to be **more expressive and comprehensive than Turnitin**.

#### 3.4.1 Dashboard & Navigation
| ID | Requirement |
|---|---|
| **FR-4.1** | The frontend shall be a **React.js SPA** with Shadcn/ui components and Tailwind CSS. |
| **FR-4.2** | The dashboard shall show a list of all submitted documents with: status badge, originality score, risk level, upload date. |
| **FR-4.3** | Real-time progress indicators via **WebSocket** (e.g., "Checking Internal Archive… 45%"). |

#### 3.4.2 The Report View — Core Features
| ID | Requirement |
|---|---|
| **FR-4.4** | **Side-by-Side Diff View:** Clicking a flagged sentence on the left renders the matched source evidence on the right (original text, source document name, page number, similarity score). |
| **FR-4.5** | **Color-Coded Text Overlay:** The full document text shall be rendered with inline color-coding: Red = exact internal match, Orange = paraphrase match, Blue = web match, Green = original content. |
| **FR-4.6** | **Interactive Heatmap:** A page-by-page thumbnail strip where each page is color-coded by match density, serving as a visual "fingerprint" of the document's integrity. |
| **FR-4.7** | **Source Panel:** A dedicated right panel showing all unique sources found (internal archive documents + web URLs), ranked by coverage percentage. |
| **FR-4.8** | **Match Type Filter:** Toggles to show/hide by category: Internal Exact, Internal Paraphrase, Web Match. |

#### 3.4.3 Report Statistics & Analytics
| ID | Requirement |
|---|---|
| **FR-4.9** | **Originality Score:** A single headline metric (0–100%) displayed prominently at the top. |
| **FR-4.10** | **Source Breakdown Pie Chart:** Proportion of matched content by source (each internal doc and web domain gets a slice). |
| **FR-4.11** | **Match Distribution Bar Chart:** Number of matches per page, visualizing plagiarism density across the document. |
| **FR-4.12** | **Summary Statistics Table:** Total matches, matches by type, average match length, longest match, unique sources count. |

#### 3.4.4 Report Export
| ID | Requirement |
|---|---|
| **FR-4.13** | **PDF Export:** Faculty shall be able to export a **signed, branded PDF summary** of the full report including: cover page with scores, source list, highlighted text excerpts, charts, and institutional branding. |
| **FR-4.14** | **JSON Export:** Machine-readable export of all findings for integration with LMS or institutional records. |
| **FR-4.15** | **Print View:** A printer-friendly layout of the report optimized for A4/Letter paper. |

#### 3.4.5 Faculty Actions
| ID | Requirement |
|---|---|
| **FR-4.16** | Faculty shall be able to **exclude** specific matches (e.g., common phrases, properly cited quotations) and recalculate the score. |
| **FR-4.17** | Faculty shall be able to **annotate** findings with comments before exporting. |
| **FR-4.18** | Faculty shall be able to mark a report as **"Reviewed"** with their digital signature. |

---

## 4. External Interface Requirements

### 4.1 User Interfaces
*   **Web Portal:** Clean, modern interface supporting drag-and-drop uploads with instant file validation.
*   **Real-time Feedback:** WebSocket integration displaying live progress stepper.
*   **Report View:** Three-panel layout (findings list | document text | evidence context).

### 4.2 Software Interfaces
| Interface | Technology | Purpose |
|---|---|---|
| Backend API | FastAPI (Python 3.12) | REST endpoints |
| Vector DB | Qdrant (gRPC) | Semantic vector search |
| Cache/LSH | Redis (TCP) | MinHash index, caching, task queue |
| Relational DB | PostgreSQL (TCP) | Users, documents, reports, matches |
| Task Queue | Celery + Redis | Async job processing |
| External API | Serper.dev (HTTPS) | Google Search for web dragnet |

### 4.3 Hardware Interfaces
*   **GPU (Optional):** Required only if Llama-3-Vision OCR fallback is enabled for scanned PDFs.
*   **Storage:** SSD recommended for the vector database and document archive to ensure sub-second query times.

---

## 5. Non-Functional Requirements

### 5.1 Performance
| Metric | Target |
|---|---|
| **Throughput** | Process a 50-page thesis (both layers) in under **5 minutes** |
| **Concurrency** | Job queue supports **50+ concurrent submissions** without degradation |
| **Query Latency** | Internal similarity queries return in under **2 seconds** |
| **Report Rendering** | Report view loads in under **3 seconds** for a completed analysis |

### 5.2 Safety & Privacy
*   **Local Sovereignty:** No student body text shall be transmitted to third-party storage or AI training providers.
*   **Transient Analysis:** Serper queries use only short, anonymized shingles (≈50 words). No PII.
*   **Archive Security:** The local archive is encrypted at rest and accessible only to authorized system processes.

### 5.3 Reliability
*   **Availability:** 99.9% uptime during the academic year.
*   **Fault Tolerance:** If Serper API is unreachable, the system completes Internal Similarity and marks Web Dragnet as "Pending."
*   **Data Durability:** Document archives backed up daily with point-in-time recovery.

### 5.4 Maintainability
*   **Containerization:** All services Dockerized, orchestrated via Docker Compose.
*   **Modularity:** Web search provider (Serper) is abstracted behind an interface to allow swapping (e.g., Brave Search, SearXNG) without core code changes.
*   **Logging:** Structured JSON logging for all pipeline stages. Each analysis job has a traceable job ID.

---

## 6. Technical Stack Strategy

| Layer | Component | Technology |
|---|---|---|
| **Frontend** | Framework | React.js (Vite) |
| | Styling | Tailwind CSS + Shadcn/ui |
| | State | Zustand |
| | Charting | Recharts / Chart.js |
| | PDF Export | jsPDF + html2canvas |
| **Backend** | API Framework | FastAPI (Python 3.12) |
| | Task Queue | Celery + Redis |
| | Text Processing | NLTK / spaCy (shingling, tokenization) |
| | Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| | MinHash | datasketch library |
| **Data** | Vector DB | Qdrant (On-Disk Indexing) |
| | Relational DB | PostgreSQL |
| | Cache/LSH | Redis |
| **Infrastructure** | PDF Parsing | Grobid (Docker) |
| | OCR Fallback | Llama-3-Vision (Quantized) — Optional |
| | Orchestration | Docker Compose |

---

## 7. Appendices
*   **A:** API Key Management Policy (Serper.dev).
*   **B:** Institutional Data Retention Policy.
*   **C:** Report Design Specification (see `Report_Design_v2.md`).

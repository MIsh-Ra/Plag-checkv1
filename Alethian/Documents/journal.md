# Alethian Project Journal

> **INSTRUCTIONS:**
> 1. This file is an APPEND-ONLY log of all significant project activities.
> 2. NEVER delete or modify past entries.
> 3. Add new entries at the bottom with a timestamp and clear description.
> 4. Record key decisions, completed phases, and created artifacts.

---

## 2026-02-05: Project Initiation & Planning (Phase 0)

### 1. Requirements & Analysis
- Analyzed `Alethian_SRS.md`.
- Identified core layers: Ingestion, Validation, Similarity, Web Dragnet, Forensics.

### 2. System Design & Diagrams
- Created `Alethian/Documents/Diagrams.md`.
- Generated System Architecture, DFDs (Levels 0-2), ERD, Use Cases, Sequence Diagrams, and Class Diagrams.
- **Decision:** Converted all diagrams to ASCII wireframe format for universal readability.

### 3. UI Design
- Created `Alethian/Documents/UI_WireFrame.md`.
- Designed ASCII wireframes for Login, Faculty Dashboard, Report View (Split-Diff), and Admin Panel.

### 4. Technical Specifications
- Created `Alethian/Documents/API_Spec.md`: Defined REST endpoints for Auth, Documents, and Reports.
- Created `Alethian/Documents/Directory_Structure.md`: Defined comprehensive file tree for Backend/Frontend/Infra.

### 5. Roadmap Strategy
- Created `Alethian/Documents/Development_Roadmap.md`.
- **Strategic Decision:** Adopted a **Frontend-First** strategy (Phase 2) to prioritize user feedback before building complex backend logic.

---

## 2026-02-05: Phase 1 - Infrastructure Execution

### Phase 1.1: Repository Setup
- Initialized directory structure under `Alethian/` (`backend`, `frontend`, `infrastructure`).
- Configured `.gitignore` for Python, Node.js, and Docker artifacts.

### Phase 1.2: Orchestration
- Created `Alethian/infrastructure/docker-compose.yml`.
- Defined services:
    - **PostgreSQL** (Port 5432)
    - **Redis** (Port 6379)
    - **Qdrant** (Port 6333)
    - **Grobid** (Port 8070)

### Phase 1.3: Configuration
- Created `Alethian/.env.example` with template variables.
- **Refinement:** Updated `docker-compose.yml` to reference a single centralized `.env` file in the project root (`../.env`) to avoid duplication.
- **Status:** Phase 1 Complete. Infrastructure is ready for deployment.

## 2026-02-05: Phase 2 - Frontend Implementation

### Phase 2.1: Frontend Scaffolding
- Initialized React + Vite project in `Alethian/frontend`.
- Installed dependencies: React Router, Axios, TailwindCSS, Lucide, Shadcn utlities.
- **Workaround:** Manually created `tailwind.config.js`, `postcss.config.js`, and `index.css` due to `npx` path resolution issues.
- Configured Global CSS variables for Shadcn/ui dark/light mode.

### Phase 2.2: Mock API & Routing
- Configured **React Router** in `App.jsx` with routes: `/login`, `/dashboard`, `/report/:id`, `/admin`.
- Created placeholder pages for all routes.
- Created `src/api/mock_client.js` implementing the full `API_Spec.md` contract with simulated latency and "fake" data (including a hallucinated citation scenario).

### Phase 2.3: Page Implementation
- Implemented **Login Page (`Login.jsx`)**: Functional form with mock authentication logic navigating to Dashboard/Admin.
- Implemented **Dashboard (`Dashboard.jsx`)**: User-specific greeting, File Upload zone, and Document List with dynamic status badges (Ingesting/Ready/Score).
- Implemented **Report View (`ReportView.jsx`)**: Complex split-screen interface.
    - **Sidebar:** Filterable list of findings (Citations & Similarity).
    - **Main View / Diff:** Dynamic highlighting of selected segments vs. evidence.
    - **Logic:** Handles "Hallucination" vs "Verified" status with distinct UI states (Red/Green).

### Phase 2.4: Admin Panel Implementation
- Implemented **Admin Panel (`AdminPanel.jsx`)**:
    - Manage API Keys (Semantic Scholar, Serper) with status indicators (Active/Quota Exceeded).
    - Adjustable Similarity Threshold slider.
    - Simulated "Save Configuration" with toast notifications.

### Phase 2 Verification
- **Automated Browser Test:** Successfully verified the full end-to-end flow.
    - Login -> Dashboard -> Upload -> Report Analysis -> Admin Config.
    - **Issues Resolved:** Fixed initial crash by installing missing `tailwindcss-animate` and downgrading to Tailwind v3 for compatibility.
- **Status:** Phase 2 Complete. Frontend is ready.

### Documentation Update
- Created `README.md` in `Alethian/` root.
- Documented Quick Start for Docker Infrastructure.
- Documented Frontend setup (Mock Mode) and credentials.
- Added placeholder instructions for Backend setup (Phase 3).

### Documentation: Remote Workflow
- Created `Alethian/Documents/Remote_Development.md`.
- Documented VS Code Remote-SSH workflow for seamless "local feel, remote execution" development.
- Documented SSH Port Forwarding for browser testing.

## 2026-02-19: Phase 2 - Project Analysis & Planning

### 1. Analysis
- **Documentation Review:** Verified `Alethian_SRS.md`, `Development_Roadmap.md`, `Directory_Structure.md`, and `API_Spec.md`. Confirmed project scope and local-first architecture usage.
- **Codebase Exploration:** Verified directory structure for `backend/`, `frontend/`, and `infrastructure/`. Confirmed alignment with the roadmap.

### 2. Planning
- **Security Strategy:** Initiated security planning focusing on:
    -   **Data Sovereignty:** Ensuring PDF content never leaves the local network.
    -   **Anonymization:** Only hashed/snippet data sent to external APIs (Serper/Semantic Scholar).
    -   **Authentication:** JWT-based access for Faculty/Admin roles.
- **API Specification Update:** Planned updates to `API_Spec.md` to formally document external service dependencies (Semantic Scholar, Unpaywall, Serper) and their data contracts.

---

## 2026-02-19: Layer 1 - Ingestion Engine Implementation

### 1. Implementation
-   **Backend Logic:** Implemented `GrobidClient` (`backend/app/core/ingestion.py`) to interface with the local Grobid service.
-   **API Endpoint:** Created `POST /documents/upload` (`backend/app/api/documents.py`) to handle file uploads and trigger ingestion.
-   **Frontend:** Replaced mock API with real Axios client (`frontend/src/api/client.js`) and integrated it into `Dashboard.jsx`.

### 2. Challenges & Resolutions
-   **Dependency Management:** Initial attempts to run tests failed due to missing `fastapi` and `requests` modules in the test environment.
    -   *Fix:* Explicitly installed missing packages and ensured the virtual environment was correctly activated.
-   **XML Parsing Error:** The initial `ingestion.py` logic failed to extract the abstract from the Grobid TEI XML response.
    -   *Issue:* The test case used a `<div type="abstract">` structure, but the code only looked for `<abstract>`.
    -   *Fix:* Updated parsing logic to robustly check for both tag variations (`soup.find('abstract') or soup.find('div', type='abstract')`).

### 3. Verification
-   **System Tests:** Created a new system test suite in `tests/system/phase1/`.
-   **Automation:** Developed `tests/run_tests.sh` for consistent execution.
-   **Status:** All tests passed after the XML parsing fix.
-   **Note:** Moved `tests/` directory to project root (`Alethian/tests/`) to separate test infrastructure from backend source code.

## 2026-02-19: Database Integration (PostgreSQL)

### 1. Configuration & Schema
-   **Infrastructure:** Configured `backend/app/core/config.py` to load secure credentials from `.env` using `pydantic-settings`.
-   **Connection:** Established SQLAlchemy session management in `backend/app/db/session.py`.
-   **Schema:** Defined `Document` model in `backend/app/db/models.py`. The table includes a `meta_data` JSON column to store the rich output from Grobid.

### 2. API Integration
-   **Upload Endpoint:** Modified `POST /documents/upload` to persist the uploaded document in the database immediately after parsing.
-   **List Endpoint:** Updated `GET /documents` to serve real data from the database, enabling true persistence across server restarts.

### 3. Verification
-   **Testing:** Updated `tests/system/phase1/test_ingestion.py` to mock the database dependency (`get_db`), ensuring tests run quickly without requiring a live database during CI/CD.
-   **Status:** All tests passed.

---

## 2026-03-12: Phase 1 Testing, Bug Fixes & Demo Preparation

### 1. Backend System Tests
-   Ran `tests/run_tests.sh` — all 3 tests passed (`test_upload_document_success`, `test_upload_invalid_file_type`, `test_grobid_failure_handling`).
-   Eliminated **5 deprecation warnings** that were cluttering test output:
    -   `backend/app/core/config.py`: Migrated from Pydantic `class Config` to `model_config = SettingsConfigDict(...)`.
    -   `backend/app/db/models.py`: Updated `declarative_base()` import from `sqlalchemy.ext.declarative` → `sqlalchemy.orm`. Replaced `datetime.utcnow()` → `datetime.now(datetime.timezone.utc)`.
    -   `backend/app/api/documents.py`: Same `utcnow()` fix.
    -   `backend/app/main.py`: Replaced deprecated `@app.on_event("startup")` with a `lifespan` async context manager.

### 2. Critical Bug Fixes
-   **`.env` path resolution:** `config.py` used a relative `env_file=".env"` which broke tests running from `Alethian/` root. Fixed by resolving the path absolutely using `Path(__file__).resolve().parents[3] / ".env"`.
-   **Vite v7 `allowedHosts` issue:** Vite v7 introduced a security feature that silently drops HTTP requests from hosts not in its allowlist. TCP connections succeeded but the server returned 0 bytes — pages never loaded in any browser. Fixed by adding `server: { allowedHosts: true }` to `frontend/vite.config.js`.
-   **Docker port conflict:** Postgres port 5432 was occupied by another container (`auction_postgres_dev`). Remapped to host port 5433 in `docker-compose.yml` and updated `.env`.

### 3. Frontend MockClient Migration
-   `Dashboard.jsx` was already using the real `Client`, but **3 pages still imported `MockClient`**:
    -   `Login.jsx`, `ReportView.jsx`, `AdminPanel.jsx` — all updated to import from `../api/client`.

### 4. API-Level Integration Verification
-   `GET /` → `{"message": "Alethian API is running"}` ✅
-   `GET /api/v1/documents` → `[]` (empty DB) ✅
-   `POST /upload` with `.txt` → Correctly rejected: `"Only PDF files are allowed"` ✅
-   `POST /upload` with real PDF → Grobid processed and returned structured data ✅
-   Grobid `/api/isalive` → HTTP 200 ✅

### 5. Live Upload Verification
-   Manually uploaded `IndiVision` paper through the frontend.
-   Confirmed Grobid extracted title, abstract, 4 sections, and references from the PDF.
-   Data persisted correctly in PostgreSQL.

### 6. Demo Scripts
-   Created `scripts/demo.sh`: One-click orchestrator that clears ports, starts Docker containers, launches Backend and Frontend in separate `kitty` terminal windows, and opens a Grobid output monitor.
-   Created `scripts/demo_monitor.sh`: Polls the database for new uploads and pretty-prints the Grobid-parsed output (title, abstract, sections, references) in real time.

---

> [!IMPORTANT]
> **REMINDER TO SELF:**
> 1.  **Always update this journal** after every significant task or phase completion.
> 2.  **Document Failures:** Don't just record success. detailed debugging steps (like the missing `fastapi` module or the specific XML parsing error) are crucial for future troubleshooting.
> 3.  **Test Scripts:** Maintain the `tests/` directory at the project root. Ensure `run_tests.sh` works in a standard environment. **Do not modify scripts just to pass tests; they must reflect reality.**


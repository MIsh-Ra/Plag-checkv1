# Alethian Development Roadmap

This document outlines the phased execution plan for building the Alethian Research Integrity System. It follows a **Frontend-First** strategy to ensure early visualization and user feedback, backed by a robust, privacy-centric engine.

---

## Phase 1: Infrastructure & Setup (Foundation)
**Goal:** Establish the operational environment and repository structure.

- [-] **1.1 Repository Initialization**
    - Initialize Git repo.
    - Create `backend/`, `frontend/`, `infrastructure/` directories per `Directory_Structure.md`.
- [-] **1.2 Docker Orchestration**
    - Create `infrastructure/docker-compose.yml`.
    - Service definitions:
        - `postgres` (User Data).
        - `redis` (Task Queue & LSH Cache).
        - `qdrant` (Vector Database).
        - `grobid/grobid` (PDF Parsing).
- [-] **1.3 Environment Configuration**
    - Set up `.env` templates for API keys and DB credentials.

---

## Phase 2: Frontend Implementation (The Dashboard)
**Goal:** Build a fully interactive UI using mocked data to validate user experience.

- [ ] **2.1 Frontend Scaffolding**
    - Initialize React + Vite project in `frontend/`.
    - Install Tailwind CSS & Shadcn/ui.
    - Configure Router (React Router).
- [ ] **2.2 Mock API Layer**
    - Create `src/api/mock_client.js`.
    - Implement fake responses for `/auth/login`, `/documents`, and `/reports/{id}` based on `API_Spec.md`.
- [ ] **2.3 Page Implementation**
    - **Login Page:** Clean, institutional design.
    - **Dashboard:** Drag-and-drop upload area + Analysis list (with mock progress bars).
    - **Report View:**
        - Implement **Split-View Diff Component** (Left: Text, Right: Evidence).
        - Implement "Traffic Light" citation cards.
- [ ] **2.4 Admin Panel**
    - Settings forms for API Keys and Thresholds (mock save).

---

## Phase 3: Backend Core & Ingestion (Layers 1 & 2)
**Goal:** Establish the FastAPI application and the document processing pipeline.

- [ ] **3.1 Backend Scaffolding**
    - Initialize FastAPI project in `backend/`.
    - Configure SQLAlchemy (Postgres) and Redis connection.
- [ ] **3.2 Layer 1: Ingestion Engine**
    - Implement `GrobidClient` to send PDFs to the local Grobid container.
    - Implement `DocumentNormalizer` to convert XML/TEI to JSON.
    - *Fallback:* Integrate Llama-3-Vision for scanned PDFs (if confident score is low).
- [ ] **3.3 Layer 2: Reference Validation**
    - Implement `SemanticScholarClient`.
    - Build logic to check citation existence and retraction status.
- [ ] **3.4 Task Queue Integration**
    - Set up Celery workers to handle Ingestion and Validation asynchronously.
    - Expose `POST /documents/upload` endpoint (real implementation).

---

## Phase 4: Backend Advanced Analysis (Layers 3, 4, 5)
**Goal:** Implement the deep forensic capabilities of the system.

- [ ] **4.1 Layer 3: Internal Similarity**
    - Implement **MinHash** generation and Redis storage.
    - Implement **Qdrant** client for vector embedding storage/search.
- [ ] **4.2 Layer 4: Web Dragnet**
    - Implement `SerperClient` (Google Search API).
    - Build **Source Coherence** logic (>3 chunks from same domain).
- [ ] **4.3 Layer 5: AI Forensics**
    - Set up local LLM inference (or mock with API for dev speed).
    - Implement **Binoculars Metric** calculation logic.
- [ ] **4.4 Reporting Engine**
    - Aggregator logic to compile findings from all 5 layers into a single JSON report.

---

## Phase 5: Integration & QA
**Goal:** Connect the real backend to the frontend and verify system integrity.

- [ ] **5.1 API Integration**
    - Switch Frontend API client from `mock_client.js` to real `axios` endpoints.
    - Verify Authentication flow (JWT).
    - Test File Upload -> Progress WebSocket -> Report Rendering flow.
- [ ] **5.2 End-to-End Testing**
    - Test full submission cycle with a known plagiarized PDF.
    - Test "Admin Config" updates reflecting in system behavior.
- [ ] **5.3 Deployment Preparation**
    - Finalize `docker-compose.yml` for production (resource limits, restart policies).
    - Write `README.md` with deployment instructions.

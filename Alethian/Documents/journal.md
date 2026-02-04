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

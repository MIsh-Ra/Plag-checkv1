# Alethian Project Directory Structure v2.0

```text
Alethian/
├── Documents_v2/                   # Updated documentation (SRS, Diagrams, Wireframes, Spec)
│   ├── Alethian_SRS_v2.md
│   ├── API_Spec_v2.md
│   ├── Diagrams_v2.md
│   ├── MermaidDiagrams_v2.md
│   ├── Directory_Structure_v2.md
│   ├── Security_Architecture_v2.md
│   ├── UI_WireFrame_v2.md
│   ├── Development_Roadmap_v2.md
│   └── Report_Design_v2.md
├── Documents/                      # Original v1 documentation (archived)
├── infrastructure/                 # DevOps & Deployment
│   ├── docker-compose.yml
│   ├── nginx/
│   │   └── nginx.conf
│   └── postgres/
│       └── init.sql
├── backend/                        # Python FastAPI Backend
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # App Entrypoint + Lifespan
│   │   ├── api/                    # API Routes (v1)
│   │   │   ├── auth.py
│   │   │   ├── documents.py        # Upload, List, Details
│   │   │   ├── reports.py          # Report CRUD, Export, Heatmap
│   │   │   └── admin.py            # Config CRUD
│   │   ├── core/                   # Business Logic & Engines
│   │   │   ├── config.py           # Pydantic Settings
│   │   │   ├── ingestion.py        # Layer 1: Grobid/Llama PDF Parsing
│   │   │   ├── shingling.py        # Text shingling & MinHash generation
│   │   │   ├── similarity.py       # Layer 2: Redis LSH + Qdrant Vectors
│   │   │   ├── web_dragnet.py      # Layer 3: Serper Search + Coherence
│   │   │   ├── content_fetcher.py  # Fetch & compare web page content
│   │   │   └── report_engine.py    # Score calculation, heatmap, charts
│   │   ├── db/                     # Database Models & Connections
│   │   │   ├── session.py
│   │   │   └── models.py           # Users, Documents, Reports, Matches, Sources
│   │   └── schemas/                # Pydantic Request/Response Models
│   │       ├── document.py
│   │       ├── report.py
│   │       ├── match.py
│   │       └── admin.py
│   └── celery_worker.py            # Task Queue Worker
├── frontend/                       # React.js Frontend
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.js
│   ├── public/
│   └── src/
│       ├── api/                    # API Client (Axios)
│       │   └── client.js
│       ├── assets/
│       ├── components/
│       │   ├── layout/             # Navbar, Sidebar, Layout
│       │   ├── dashboard/          # Upload Zone, Document Cards
│       │   └── report/             # Core report components
│       │       ├── DiffViewer.jsx       # Side-by-side comparison
│       │       ├── TextOverlay.jsx      # Color-coded full text
│       │       ├── Heatmap.jsx          # Page thumbnail strip
│       │       ├── SourcePanel.jsx      # Source list + coverage
│       │       ├── ScoreHeader.jsx      # Originality score display
│       │       ├── PieChart.jsx         # Source breakdown
│       │       ├── BarChart.jsx         # Per-page distribution
│       │       ├── MatchCard.jsx        # Individual match detail
│       │       ├── FilterBar.jsx        # Match type toggles
│       │       └── ExportMenu.jsx       # PDF/JSON/Print export
│       ├── pages/
│       │   ├── Login.jsx
│       │   ├── Dashboard.jsx
│       │   ├── ReportView.jsx          # Main report page (3-panel)
│       │   └── AdminPanel.jsx
│       ├── hooks/
│       │   ├── useWebSocket.js         # Real-time status hook
│       │   └── useReport.js            # Report data fetching
│       ├── stores/
│       │   └── reportStore.js          # Zustand state (filters, excludes)
│       └── App.jsx
├── scripts/
│   ├── demo.sh
│   ├── demo_monitor.sh
│   └── seed_archive.py                # Seed local archive with test docs
├── tests/
│   ├── run_tests.sh
│   ├── system/
│   │   └── phase1/
│   │       └── test_ingestion.py
│   └── unit/
│       ├── test_similarity.py
│       ├── test_web_dragnet.py
│       └── test_report_engine.py
├── .env.example
├── .gitignore
└── README.md
```

### Key Changes from v1
| Area | v1 | v2 |
|---|---|---|
| **Backend Core** | `validation.py`, `forensics.py` | **Removed.** Replaced by `shingling.py`, `content_fetcher.py`, `report_engine.py` |
| **Schemas** | Flat | Structured into `document.py`, `report.py`, `match.py`, `admin.py` |
| **Frontend Report** | Single `ReportView.jsx` | Decomposed into 10 focused components under `components/report/` |
| **Frontend State** | Local state | Zustand store for report state + WebSocket hooks |
| **Tests** | Phase 1 only | Added unit tests for similarity, web dragnet, and report engine |

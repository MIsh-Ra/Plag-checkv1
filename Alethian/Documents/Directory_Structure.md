# Alethian Project Directory Structure

```text
Alethian/
├── Documents/                  # Documentation (SRS, Diagrams, Wireframes, Spec)
│   ├── Alethian_SRS.md
│   ├── Diagrams.md
│   ├── UI_WireFrame.md
│   ├── API_Spec.md
│   └── Directory_Structure.md
├── infrastructure/             # DevOps & Deployment
│   ├── docker-compose.yml
│   ├── nginx/
│   │   └── nginx.conf
│   └── postgres/
│       └── init.sql
├── backend/                    # Python FastAPI Backend
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # App Entrypoint
│   │   ├── api/                # API Routes (v1)
│   │   │   ├── auth.py
│   │   │   ├── documents.py
│   │   │   ├── reports.py
│   │   │   └── admin.py
│   │   ├── core/               # Business Logic & Engines
│   │   │   ├── config.py
│   │   │   ├── ingestion.py    # Layer 1: Grobid/Llama
│   │   │   ├── validation.py   # Layer 2: API Mesh
│   │   │   ├── similarity.py   # Layer 3: Redis/Qdrant
│   │   │   ├── web_dragnet.py  # Layer 4: Serper
│   │   │   └── forensics.py    # Layer 5: AI Detection
│   │   ├── db/                 # Database Models & Connections
│   │   │   ├── session.py
│   │   │   └── models.py
│   │   └── schemas/            # Pydantic Models (Req/Res)
│       └── celery_worker.py    # Task Queue Worker
└── frontend/                   # React.js Frontend
    ├── Dockerfile
    ├── package.json
    ├── vite.config.js
    ├── public/
    └── src/
        ├── api/                # Axios API Clients
        ├── assets/
        ├── components/
        │   ├── layout/         # Navbar, Sidebar
        │   ├── dashboard/      # Cards, Lists
        │   └── report/         # DiffViewer, TrafficLights
        ├── pages/
        │   ├── Login.jsx
        │   ├── Dashboard.jsx
        │   ├── ReportView.jsx
        │   └── AdminPanel.jsx
        └── App.jsx
```

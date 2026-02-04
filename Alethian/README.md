# Alethian Research Integrity System

**Alethian** is a local-first, privacy-centric plagiarism and AI-generation detection system designed for academic institutions. It provides a multi-layered forensic analysis of documents without exposing sensitive data to external cloud retention.

## 🚀 Quick Start (Infrastructure)

The core infrastructure (Database, Vector DB, Redis, PDF Parser) is containerized.

### Prerequisites
- Docker & Docker Compose
- Node.js v18+
- Python 3.10+

### Start Infrastructure
```bash
cd infrastructure
# Copy env template
cp ../.env.example ../.env
# Start services (Postgres, Redis, Qdrant, Grobid)
docker-compose up -d
```

---

## 💻 Frontend Development (The Dashboard)

The frontend is a React + Vite application using TailwindCSS and Shadcn/ui.
Currently, it runs in **Mock Mode** (no backend required).

```bash
cd frontend

# Install dependencies
npm install

# Start Development Server
npm run dev
```
> Access at: `http://localhost:5173`
>
> **Mock Credentials:**
> - User: `faculty@university.edu` / `123456`
> - Admin: `admin@university.edu` / `admin`

---

## ⚙️ Backend Development (Core Engine)

*Note: Backend implementation is in progress (Phase 3).*

The backend is built with FastAPI and manages document ingestion, analysis layers, and reporting.

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start API Server
uvicorn app.main:app --reload
```

---

## 📂 Project Structure

- `frontend/`: React UI (Vite, Tailwind, Axios).
- `backend/`: FastAPI application (Ingestion, Analysis Layers, API).
- `infrastructure/`: Docker Compose and config for services.
- `Documents/`: Design docs, API Specs, and Wireframes.

#!/bin/bash
# ============================================================================
#  Alethian Phase 1 Demo Launcher
#  One-click script to bring up the full stack for a live demonstration.
#  Usage: bash scripts/demo.sh
# ============================================================================

set -e

# ── Configuration ──────────────────────────────────────────────────────────
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
INFRA_DIR="$PROJECT_ROOT/infrastructure"
MONITOR_SCRIPT="$PROJECT_ROOT/scripts/demo_monitor.sh"

BACKEND_PORT=8000
FRONTEND_PORT=5173
POSTGRES_HOST_PORT=5433

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

banner() {
    echo ""
    echo -e "${CYAN}${BOLD}"
    echo "  ╔═══════════════════════════════════════════════════╗"
    echo "  ║         ALETHIAN - Demo Launcher v1.0            ║"
    echo "  ║     Local-First Research Integrity System         ║"
    echo "  ╚═══════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

log()  { echo -e "  ${GREEN}✔${NC} $1"; }
warn() { echo -e "  ${YELLOW}⚠${NC} $1"; }
err()  { echo -e "  ${RED}✘${NC} $1"; }
step() { echo -e "\n${BOLD}[$1]${NC} $2"; }

# ── Step 1: Kill stale processes on required ports ─────────────────────────
cleanup_ports() {
    step "1/7" "Cleaning up stale processes..."

    for PORT in $FRONTEND_PORT $BACKEND_PORT; do
        PIDS=$(ss -tlnp 2>/dev/null | grep ":${PORT} " | grep -oP 'pid=\K[0-9]+' | sort -u)
        if [ -n "$PIDS" ]; then
            for PID in $PIDS; do
                kill -9 "$PID" 2>/dev/null && warn "Killed stale process $PID on port $PORT"
            done
            sleep 1
        fi
    done

    # Also kill any stale node/vite processes from this project
    pkill -f "vite.*--host" 2>/dev/null || true
    sleep 1
    log "Ports $FRONTEND_PORT and $BACKEND_PORT are free."
}

# ── Step 2: Start Docker infrastructure ────────────────────────────────────
start_docker() {
    step "2/7" "Starting Docker infrastructure..."

    if ! docker info > /dev/null 2>&1; then
        err "Docker is not running! Please start Docker first."
        exit 1
    fi

    cd "$INFRA_DIR"
    docker compose up -d 2>&1 | tail -6

    # Wait for Postgres
    echo -n "  Waiting for Postgres"
    for i in $(seq 1 15); do
        if PGPASSWORD=alethian_pass psql -h localhost -p $POSTGRES_HOST_PORT -U alethian -d alethian_db -c "SELECT 1" > /dev/null 2>&1; then
            echo ""
            log "PostgreSQL is ready on port $POSTGRES_HOST_PORT"
            break
        fi
        echo -n "."
        sleep 2
    done

    # Wait for Grobid (it takes a while to warm up)
    echo -n "  Waiting for Grobid"
    for i in $(seq 1 30); do
        if curl -s http://localhost:8070/api/isalive > /dev/null 2>&1; then
            echo ""
            log "Grobid is ready on port 8070"
            break
        fi
        echo -n "."
        sleep 3
    done

    # Check Redis and Qdrant
    if curl -s http://localhost:6333 > /dev/null 2>&1; then
        log "Qdrant is ready on port 6333"
    fi

    log "All containers are running."
}

# ── Step 3: Seed demo users ────────────────────────────────────────────────
seed_demo_users() {
    step "3/7" "Seeding demo users..."

    cd "$BACKEND_DIR"

    if [ ! -f "venv/bin/activate" ]; then
        err "venv not found at $BACKEND_DIR/venv. Run: python3 -m venv venv && pip install -r requirements.txt"
        exit 1
    fi

    source venv/bin/activate

    echo "  Running seeder..."
    PYTHONPATH="$BACKEND_DIR" python3 - <<'PYEOF'
import sys
try:
    from app.db.session import SessionLocal, engine
    from app.db.models import User, UserRole, Base
    from passlib.context import CryptContext

    Base.metadata.create_all(bind=engine)
    pwd = CryptContext(schemes=['bcrypt'])
    db = SessionLocal()

    users = [
        {'username': 'faculty@university.edu', 'email': 'faculty@university.edu',
         'password': '123456', 'full_name': 'Demo Faculty', 'role': UserRole.faculty},
        {'username': 'admin@university.edu', 'email': 'admin@university.edu',
         'password': 'admin', 'full_name': 'System Admin', 'role': UserRole.admin},
    ]

    for u in users:
        existing = db.query(User).filter(User.email == u['email']).first()
        if not existing:
            db.add(User(
                username=u['username'], email=u['email'],
                hashed_password=pwd.hash(u['password']),
                full_name=u['full_name'], role=u['role']
            ))
            print(f"  ✅ Created: {u['email']} (password: {u['password']})")
        else:
            print(f"  ℹ️  Exists:  {u['email']} (skipped)")

    db.commit()
    db.close()
    print("  Demo users ready.")
except Exception as e:
    print(f"  ❌ Seeding failed: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF

    if [ $? -eq 0 ]; then
        log "Demo users seeded successfully."
    else
        err "User seeding FAILED — check the error above. Backend will return 401 until users exist."
    fi
}


# ── Step 4: Open Backend terminal ──────────────────────────────────────────
start_backend() {
    step "4/7" "Starting FastAPI Backend..."

    kitty --title "🔧 Alethian Backend (port $BACKEND_PORT)" \
          --detach \
          bash -c "
            cd '$BACKEND_DIR'
            source venv/bin/activate
            echo ''
            echo '═══════════════════════════════════════════'
            echo '  Alethian Backend Server'
            echo '  http://localhost:$BACKEND_PORT'
            echo '═══════════════════════════════════════════'
            echo ''
            uvicorn app.main:app --reload --port $BACKEND_PORT 2>&1
            echo ''
            echo 'Server stopped. Press Enter to close.'
            read
          "

    # Wait for backend to be healthy
    echo -n "  Waiting for Backend"
    for i in $(seq 1 15); do
        if curl -s http://localhost:$BACKEND_PORT/ > /dev/null 2>&1; then
            echo ""
            log "Backend is live at http://localhost:$BACKEND_PORT"
            break
        fi
        echo -n "."
        sleep 1
    done
}

# ── Step 5: Open Celery Worker terminal ────────────────────────────────────
start_celery_worker() {
    step "5/7" "Starting Celery Worker..."

    kitty --title "⚙️  Alethian Celery Worker" \
          --detach \
          bash -c "
            cd '$BACKEND_DIR'
            source venv/bin/activate
            echo ''
            echo '═══════════════════════════════════════════'
            echo '  Alethian Celery Worker'
            echo '  Processing pipeline: Grobid → Similarity → Dragnet → Report'
            echo '═══════════════════════════════════════════'
            echo ''
            PYTHONPATH='$BACKEND_DIR' celery -A celery_worker worker --loglevel=info --concurrency=2 2>&1
            echo ''
            echo 'Worker stopped. Press Enter to close.'
            read
          "

    # Give the worker a moment to connect to Redis
    sleep 2
    log "Celery worker is running (check its terminal for task logs)."
}

# ── Step 6: Open Frontend terminal ─────────────────────────────────────────
start_frontend() {
    step "6/7" "Starting Vite Frontend..."

    kitty --title "🌐 Alethian Frontend (port $FRONTEND_PORT)" \
          --detach \
          bash -c "
            cd '$FRONTEND_DIR'
            echo ''
            echo '═══════════════════════════════════════════'
            echo '  Alethian Frontend (React + Vite)'
            echo '  http://localhost:$FRONTEND_PORT'
            echo '═══════════════════════════════════════════'
            echo ''
            npm run dev -- --host 0.0.0.0 2>&1
            echo ''
            echo 'Server stopped. Press Enter to close.'
            read
          "

    # Wait for frontend to respond
    echo -n "  Waiting for Frontend"
    for i in $(seq 1 10); do
        if curl -s --max-time 2 http://127.0.0.1:$FRONTEND_PORT/ > /dev/null 2>&1; then
            echo ""
            log "Frontend is live at http://localhost:$FRONTEND_PORT"
            break
        fi
        echo -n "."
        sleep 1
    done
}

# ── Step 7: Open Pipeline Monitor ──────────────────────────────────────────
start_monitor() {
    step "7/7" "Opening Pipeline Monitor..."

    kitty --title "🔬 Alethian Pipeline Monitor" \
          --detach \
          bash "$MONITOR_SCRIPT"

    log "Pipeline monitor is watching for uploads."
}

# ── Summary ────────────────────────────────────────────────────────────────
print_summary() {
    echo ""
    echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}  Demo is ready! 🚀${NC}"
    echo ""
    echo -e "  ${BOLD}Frontend:${NC}  http://localhost:$FRONTEND_PORT"
    echo -e "  ${BOLD}Backend:${NC}   http://localhost:$BACKEND_PORT"
    echo -e "  ${BOLD}Grobid:${NC}    http://localhost:8070"
    echo ""
    echo -e "  ${BOLD}Login Credentials:${NC}"
    echo -e "    Faculty: ${CYAN}faculty@university.edu${NC} / ${CYAN}123456${NC}"
    echo -e "    Admin:   ${CYAN}admin@university.edu${NC}   / ${CYAN}admin${NC}"
    echo ""
    echo -e "  ${BOLD}Terminal Windows:${NC}"
    echo "    🔧 Backend   — API request logs"
    echo "    ⚙️  Worker    — Celery task logs (raw processing pipeline)"
    echo "    🌐 Frontend  — Vite dev server"
    echo "    🔬 Monitor   — Live pipeline status tracker"
    echo ""
    echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════${NC}"
    echo ""
}

# ── Main ───────────────────────────────────────────────────────────────────
banner
cleanup_ports
start_docker
seed_demo_users
start_backend
start_celery_worker
start_frontend
start_monitor
print_summary

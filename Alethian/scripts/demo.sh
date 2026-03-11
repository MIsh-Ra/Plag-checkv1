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
    step "1/5" "Cleaning up stale processes..."

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
    step "2/5" "Starting Docker infrastructure..."

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

# ── Step 3: Open Backend terminal ──────────────────────────────────────────
start_backend() {
    step "3/5" "Starting FastAPI Backend..."

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

# ── Step 4: Open Frontend terminal ─────────────────────────────────────────
start_frontend() {
    step "4/5" "Starting Vite Frontend..."

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

# ── Step 5: Open Grobid Output Monitor ─────────────────────────────────────
start_monitor() {
    step "5/5" "Opening Grobid Output Monitor..."

    kitty --title "📄 Grobid Output Monitor" \
          --detach \
          bash "$MONITOR_SCRIPT"

    log "Monitor is watching for uploads."
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
    echo "    🔧 Backend   — Shows API request logs"
    echo "    🌐 Frontend  — Shows Vite dev server"
    echo "    📄 Monitor   — Shows Grobid parsed output after upload"
    echo ""
    echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════${NC}"
    echo ""
}

# ── Main ───────────────────────────────────────────────────────────────────
banner
cleanup_ports
start_docker
start_backend
start_frontend
start_monitor
print_summary

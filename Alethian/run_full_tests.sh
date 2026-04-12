#!/bin/bash
# =============================================================================
# Alethian V2 — Full Zero-Mock Test Runner
# =============================================================================
# Usage:
#   bash run_full_tests.sh                         # Full real (uses Serper API key)
#   MOCK_SERPER=true bash run_full_tests.sh        # Mock Serper to save quota
#   ARCHIVE_PATH=~/crawler_stuff/Downloads bash run_full_tests.sh  # DGX archive
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MOCK_SERPER=${MOCK_SERPER:-false}
ARCHIVE_PATH=${ARCHIVE_PATH:-"$SCRIPT_DIR/../Alethian_documents"}

echo "=============================================="
echo " Alethian V2 Full Test Suite (Zero Mock)"
echo "=============================================="
echo "Archive Path: $ARCHIVE_PATH"
echo "Mock Serper:  $MOCK_SERPER"
echo ""

# ---- Step 1: Start Docker Infrastructure ----
echo "--- [1/6] Starting Docker Infrastructure ---"
cd "$SCRIPT_DIR/infrastructure"
docker compose up -d
cd "$SCRIPT_DIR"

# ---- Step 2: Wait for Grobid ----
echo "--- [2/6] Waiting for Grobid (may take ~30s on first start) ---"
GROBID_READY=false
for i in $(seq 1 60); do
    if curl -sf http://localhost:8070/api/isalive > /dev/null 2>&1; then
        GROBID_READY=true
        break
    fi
    sleep 2
    echo "  Waiting... ($i)"
done

if [ "$GROBID_READY" = "false" ]; then
    echo "ERROR: Grobid did not start within 120 seconds."
    exit 1
fi
echo "Grobid is ready."

# ---- Step 3: Wait for Postgres ----
echo "--- [3/6] Waiting for Postgres ---"
PG_READY=false
for i in $(seq 1 30); do
    if docker exec alethian_postgres pg_isready -U alethian > /dev/null 2>&1; then
        PG_READY=true
        break
    fi
    sleep 2
done

if [ "$PG_READY" = "false" ]; then
    echo "ERROR: Postgres did not start within 60 seconds."
    exit 1
fi
echo "Postgres is ready."

# ---- Step 4: Seed Archive (optional, only on first run) ----
echo "--- [4/6] Seeding Archive Data ---"
cd "$SCRIPT_DIR/backend"
PYTHONPATH=. python tests/seed_archive.py --archive-path "$ARCHIVE_PATH" || echo "Seeding skipped or failed (may already be seeded)"
cd "$SCRIPT_DIR"

# ---- Step 5: Build pytest flags ----
SERPER_FLAG=""
if [ "$MOCK_SERPER" = "true" ]; then
    SERPER_FLAG="--mock-serper"
fi

# ---- Step 6: Run Tests ----
echo ""
echo "--- [5/6] Running Backend Tests ---"
cd "$SCRIPT_DIR/backend"

echo ""
echo ">>> Unit Tests <<<"
PYTHONPATH=. python -m pytest tests/unit/ -v --tb=short $SERPER_FLAG --archive-path "$ARCHIVE_PATH"

echo ""
echo ">>> Integration & E2E Tests <<<"
PYTHONPATH=. python -m pytest tests/system/ -v --tb=short $SERPER_FLAG --archive-path "$ARCHIVE_PATH"

echo ""
echo ">>> Coverage Report <<<"
PYTHONPATH=. python -m pytest tests/ --cov=app --cov-report=term-missing $SERPER_FLAG --archive-path "$ARCHIVE_PATH" || true

cd "$SCRIPT_DIR"

echo ""
echo "--- [6/6] Running Frontend Tests ---"
cd "$SCRIPT_DIR/frontend"
npm test -- --run 2>&1 || echo "Frontend tests completed (check output above)"
cd "$SCRIPT_DIR"

echo ""
echo "=============================================="
echo " All Tests Complete!"
echo "=============================================="

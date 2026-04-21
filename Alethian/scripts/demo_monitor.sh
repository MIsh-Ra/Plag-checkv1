#!/bin/bash
# ============================================================================
#  Alethian Pipeline Monitor
#  Watches for new document uploads and tracks processing through all stages:
#    Upload → Grobid Ingestion → Internal Similarity → Web Dragnet → Report
#  This script is launched by demo.sh in its own terminal window.
# ============================================================================

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DB_HOST="localhost"
DB_PORT="5433"
DB_USER="alethian"
DB_PASS="alethian_pass"
DB_NAME="alethian_db"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# ── Helpers ────────────────────────────────────────────────────────────────
psql_query() {
    PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
        -t -A -c "$1" 2>/dev/null
}

timestamp() { date '+%H:%M:%S'; }

stage_icon() {
    case "$1" in
        pending)    echo "⏳" ;;
        processing) echo "🔬" ;;
        complete)   echo "✅" ;;
        failed)     echo "❌" ;;
        *)          echo "❓" ;;
    esac
}

risk_color() {
    case "$1" in
        high)     echo "$RED" ;;
        moderate) echo "$YELLOW" ;;
        low)      echo "$GREEN" ;;
        *)        echo "$NC" ;;
    esac
}

# ── Banner ─────────────────────────────────────────────────────────────────
clear
echo -e "${CYAN}${BOLD}"
echo "  ╔═══════════════════════════════════════════════════════╗"
echo "  ║       🔬 ALETHIAN PIPELINE MONITOR                    ║"
echo "  ║   Real-time document processing tracker               ║"
echo "  ╚═══════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "  ${DIM}Tracks: Upload → Grobid → Similarity → Dragnet → Report${NC}"
echo -e "  ${DIM}Press Ctrl+C to stop monitoring.${NC}"
echo ""

# ── Wait for DB ────────────────────────────────────────────────────────────
echo -n -e "  ${DIM}Connecting to database"
for i in $(seq 1 20); do
    if psql_query "SELECT 1" > /dev/null 2>&1; then
        echo -e "${NC}"
        echo -e "  ${GREEN}✔${NC} Connected to PostgreSQL."
        break
    fi
    echo -n "."
    sleep 2
done

# Check Celery / Redis
if redis-cli -p 6379 ping > /dev/null 2>&1; then
    echo -e "  ${GREEN}✔${NC} Redis broker is up."
else
    echo -e "  ${YELLOW}⚠${NC} Redis not reachable — Celery tasks won't run."
fi

# Check Grobid
if curl -sf http://localhost:8070/api/isalive > /dev/null 2>&1; then
    echo -e "  ${GREEN}✔${NC} Grobid is ready."
else
    echo -e "  ${YELLOW}⚠${NC} Grobid not ready — PDF ingestion may fail."
fi

# ── Baseline — mark existing docs as seen ──────────────────────────────────
SEEN_IDS=$(psql_query "SELECT string_agg(id, ',') FROM documents;" | tr -d ' ')
TRACKING_IDS=""  # Docs currently in-progress that we're tracking

if [ -n "$SEEN_IDS" ]; then
    COUNT=$(psql_query "SELECT COUNT(*) FROM documents;")
    echo -e "  ${DIM}Found $COUNT existing document(s) — monitoring new ones only.${NC}"
fi

echo ""
echo -e "  ${YELLOW}${BOLD}▶ READY — Upload a PDF at http://localhost:5173${NC}"
echo ""

# ── Display a new upload ───────────────────────────────────────────────────
display_new_upload() {
    local DOC_ID="$1"
    local INFO=$(psql_query "SELECT filename, title, page_count, status FROM documents WHERE id = '$DOC_ID';")
    local FILENAME=$(echo "$INFO" | cut -d'|' -f1)
    local TITLE=$(echo "$INFO" | cut -d'|' -f2)
    local PAGES=$(echo "$INFO" | cut -d'|' -f3)
    local STATUS=$(echo "$INFO" | cut -d'|' -f4)

    echo -e "${GREEN}${BOLD}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓${NC}"
    echo -e "${GREEN}${BOLD}┃  📥 NEW UPLOAD DETECTED                    $(timestamp)  ┃${NC}"
    echo -e "${GREEN}${BOLD}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛${NC}"
    echo -e "  ${BOLD}File:${NC}   $FILENAME"
    echo -e "  ${BOLD}ID:${NC}     ${DIM}$DOC_ID${NC}"
    echo -e "  ${BOLD}Status:${NC} $(stage_icon $STATUS) $STATUS"
    echo ""
}

# ── Display a status change ────────────────────────────────────────────────
display_status_update() {
    local DOC_ID="$1"
    local OLD_STATUS="$2"
    local NEW_STATUS="$3"
    local FILENAME="$4"
    local TS=$(timestamp)

    echo -e "  ${CYAN}[$TS]${NC} $(stage_icon $NEW_STATUS) ${BOLD}$FILENAME${NC}: $OLD_STATUS → ${BOLD}$NEW_STATUS${NC}"
}

# ── Display final report ──────────────────────────────────────────────────
display_report() {
    local DOC_ID="$1"

    local DOC=$(psql_query "SELECT filename, title, page_count, originality_score, risk_level, CHAR_LENGTH(COALESCE(content,'')) FROM documents WHERE id = '$DOC_ID';")
    local FILENAME=$(echo "$DOC" | cut -d'|' -f1)
    local TITLE=$(echo "$DOC" | cut -d'|' -f2)
    local PAGES=$(echo "$DOC" | cut -d'|' -f3)
    local SCORE=$(echo "$DOC" | cut -d'|' -f4)
    local RISK=$(echo "$DOC" | cut -d'|' -f5)
    local TEXT_LEN=$(echo "$DOC" | cut -d'|' -f6)
    local RCOL=$(risk_color "$RISK")

    # Match counts
    local REPORT_ID=$(psql_query "SELECT id FROM reports WHERE document_id = '$DOC_ID' ORDER BY id DESC LIMIT 1;")
    local MATCH_COUNT="0"
    local INTERNAL_COUNT="0"
    local WEB_COUNT="0"
    if [ -n "$REPORT_ID" ]; then
        MATCH_COUNT=$(psql_query "SELECT COUNT(*) FROM matches WHERE report_id = '$REPORT_ID';")
        INTERNAL_COUNT=$(psql_query "SELECT COUNT(*) FROM matches WHERE report_id = '$REPORT_ID' AND type LIKE 'internal%';")
        WEB_COUNT=$(psql_query "SELECT COUNT(*) FROM matches WHERE report_id = '$REPORT_ID' AND type = 'web';")
    fi

    echo ""
    echo -e "${CYAN}${BOLD}┌──────────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${CYAN}${BOLD}│  📊 ANALYSIS COMPLETE                      $(timestamp)  │${NC}"
    echo -e "${CYAN}${BOLD}└──────────────────────────────────────────────────────────────────┘${NC}"
    echo -e "  ${BOLD}File:${NC}       $FILENAME"
    [ -n "$TITLE" ] && [ "$TITLE" != "$FILENAME" ] && echo -e "  ${BOLD}Title:${NC}      $TITLE"
    echo -e "  ${BOLD}Pages:${NC}      ${PAGES:-?}"
    echo -e "  ${BOLD}Extracted:${NC}  $TEXT_LEN characters"
    echo ""
    echo -e "  ${BOLD}Originality:${NC} ${RCOL}${BOLD}${SCORE}%${NC}"
    echo -e "  ${BOLD}Risk Level:${NC}  ${RCOL}${BOLD}${RISK}${NC}"
    echo -e "  ${BOLD}Matches:${NC}     $MATCH_COUNT total (${RED}$INTERNAL_COUNT internal${NC}, ${MAGENTA}$WEB_COUNT web${NC})"
    echo ""
    echo -e "  ${DIM}View full report: http://localhost:5173/report/$DOC_ID${NC}"
    echo -e "${CYAN}──────────────────────────────────────────────────────────────────${NC}"
    echo ""
    echo -e "  ${DIM}Waiting for next upload...${NC}"
    echo ""
}

# ── Display failure ────────────────────────────────────────────────────────
display_failure() {
    local DOC_ID="$1"
    local FILENAME=$(psql_query "SELECT filename FROM documents WHERE id = '$DOC_ID';")

    echo ""
    echo -e "${RED}${BOLD}┌──────────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${RED}${BOLD}│  ❌ ANALYSIS FAILED                        $(timestamp)  │${NC}"
    echo -e "${RED}${BOLD}└──────────────────────────────────────────────────────────────────┘${NC}"
    echo -e "  ${BOLD}File:${NC} $FILENAME"
    echo -e "  ${BOLD}ID:${NC}   ${DIM}$DOC_ID${NC}"
    echo -e "  ${DIM}Check Celery worker logs for details.${NC}"
    echo -e "${RED}──────────────────────────────────────────────────────────────────${NC}"
    echo ""
    echo -e "  ${DIM}Waiting for next upload...${NC}"
    echo ""
}

# ── Track state for in-progress docs ──────────────────────────────────────
# Format: "DOC_ID:LAST_STATUS:FILENAME"
declare -A DOC_STATES

# ── Main polling loop ──────────────────────────────────────────────────────
while true; do

    # --- Detect new uploads ---
    if [ -n "$SEEN_IDS" ]; then
        NEW_ROWS=$(psql_query "SELECT id FROM documents WHERE id NOT IN ($(echo $SEEN_IDS | sed "s/,/','/g" | sed "s/^/'/;s/$/'/")) ORDER BY upload_date ASC;")
    else
        NEW_ROWS=$(psql_query "SELECT id FROM documents ORDER BY upload_date ASC;")
    fi

    if [ -n "$NEW_ROWS" ]; then
        while IFS= read -r NEW_ID; do
            NEW_ID=$(echo "$NEW_ID" | tr -d ' ')
            [ -z "$NEW_ID" ] && continue

            # Add to seen
            if [ -n "$SEEN_IDS" ]; then
                SEEN_IDS="$SEEN_IDS,$NEW_ID"
            else
                SEEN_IDS="$NEW_ID"
            fi

            # Get initial info
            local_status=$(psql_query "SELECT status FROM documents WHERE id = '$NEW_ID';" | tr -d ' ')
            local_filename=$(psql_query "SELECT filename FROM documents WHERE id = '$NEW_ID';" | tr -d ' ')

            display_new_upload "$NEW_ID"

            # Start tracking this doc
            DOC_STATES["$NEW_ID"]="$local_status|$local_filename"

        done <<< "$NEW_ROWS"
    fi

    # --- Poll status changes for tracked docs ---
    for DOC_ID in "${!DOC_STATES[@]}"; do
        OLD_ENTRY="${DOC_STATES[$DOC_ID]}"
        OLD_STATUS=$(echo "$OLD_ENTRY" | cut -d'|' -f1)
        FILENAME=$(echo "$OLD_ENTRY" | cut -d'|' -f2)

        CURRENT_STATUS=$(psql_query "SELECT status FROM documents WHERE id = '$DOC_ID';" | tr -d ' ')

        if [ "$CURRENT_STATUS" != "$OLD_STATUS" ]; then
            display_status_update "$DOC_ID" "$OLD_STATUS" "$CURRENT_STATUS" "$FILENAME"

            if [ "$CURRENT_STATUS" = "complete" ]; then
                display_report "$DOC_ID"
                unset DOC_STATES["$DOC_ID"]
            elif [ "$CURRENT_STATUS" = "failed" ]; then
                display_failure "$DOC_ID"
                unset DOC_STATES["$DOC_ID"]
            else
                DOC_STATES["$DOC_ID"]="$CURRENT_STATUS|$FILENAME"
            fi
        fi
    done

    sleep 1.5
done

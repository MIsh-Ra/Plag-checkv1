#!/bin/bash
# ============================================================================
#  Alethian Grobid Output Monitor
#  Watches for new document uploads and displays Grobid-parsed output.
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

clear
echo -e "${CYAN}${BOLD}"
echo "  ╔═══════════════════════════════════════════════════╗"
echo "  ║         📄 Grobid Output Monitor                  ║"
echo "  ║     Watching for new document uploads...          ║"
echo "  ╚═══════════════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "  ${DIM}Upload a PDF through the frontend to see Grobid's output here.${NC}"
echo -e "  ${DIM}Press Ctrl+C to stop monitoring.${NC}"
echo ""

# Track documents we've already seen
SEEN_IDS=""

# Get current document count to establish baseline
get_doc_count() {
    PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
        -t -c "SELECT COUNT(*) FROM documents;" 2>/dev/null | tr -d ' '
}

# Get the latest document ID not in our seen list
get_latest_doc() {
    local where_clause=""
    if [ -n "$SEEN_IDS" ]; then
        where_clause="WHERE id NOT IN ($SEEN_IDS)"
    fi

    PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
        -t -c "SELECT id FROM documents $where_clause ORDER BY upload_date DESC LIMIT 1;" 2>/dev/null | tr -d ' '
}

# Pretty-print a document's Grobid output
display_document() {
    local DOC_ID="$1"

    # Fetch document metadata
    local DOC_INFO=$(PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
        -t -c "SELECT json_build_object(
            'id', id,
            'filename', filename,
            'title', title,
            'status', status,
            'upload_date', upload_date,
            'meta_data', meta_data
        ) FROM documents WHERE id = '$DOC_ID';" 2>/dev/null | tr -d '\n')

    if [ -z "$DOC_INFO" ]; then
        return
    fi

    local TIMESTAMP=$(date '+%H:%M:%S')

    echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}${BOLD}  📥 NEW UPLOAD DETECTED  ${DIM}[$TIMESTAMP]${NC}"
    echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # Use Python to pretty-print the JSON
    echo "$DOC_INFO" | python3 -c "
import json, sys, textwrap

data = json.loads(sys.stdin.read())
meta = data.get('meta_data', {})

# Document Info
print(f'  \033[1m📁 File:\033[0m     {data.get(\"filename\", \"N/A\")}')
print(f'  \033[1m🆔 ID:\033[0m       {data.get(\"id\", \"N/A\")}')
print(f'  \033[1m📅 Uploaded:\033[0m  {data.get(\"upload_date\", \"N/A\")}')
print(f'  \033[1m📊 Status:\033[0m   {data.get(\"status\", \"N/A\")}')
print()

if not meta:
    print('  \033[33m⚠ No Grobid metadata available.\033[0m')
    sys.exit(0)

# Title
title = meta.get('title', 'N/A')
print(f'  \033[1;36m═══ GROBID PARSED OUTPUT ═══\033[0m')
print()
print(f'  \033[1mTitle:\033[0m')
for line in textwrap.wrap(title, width=70):
    print(f'    {line}')
print()

# Abstract
abstract = meta.get('abstract', '')
if abstract:
    print(f'  \033[1mAbstract:\033[0m')
    for line in textwrap.wrap(abstract, width=70):
        print(f'    {line}')
    print()

# Sections
sections = meta.get('sections', [])
if sections:
    print(f'  \033[1mSections Extracted: ({len(sections)})\033[0m')
    for i, sec in enumerate(sections, 1):
        heading = sec.get('heading', 'Untitled')
        text = sec.get('text', '')
        preview = text[:150].replace(chr(10), ' ') + ('...' if len(text) > 150 else '')
        print(f'    \033[35m{i}. {heading}\033[0m')
        for line in textwrap.wrap(preview, width=66):
            print(f'       \033[2m{line}\033[0m')
    print()

# References
refs = meta.get('references', [])
if refs:
    print(f'  \033[1mReferences Extracted: ({len(refs)})\033[0m')
    for i, ref in enumerate(refs, 1):
        ref_title = ref.get('title', 'Unknown')
        print(f'    {i}. {ref_title}')
    print()
else:
    print(f'  \033[2mReferences: None extracted\033[0m')
    print()

print(f'  \033[1;32m✔ Ingestion complete.\033[0m')
" 2>/dev/null

    echo ""
    echo -e "${DIM}  Waiting for next upload...${NC}"
    echo ""
}

# ── Wait for DB to be available ────────────────────────────────────────────
echo -n -e "  ${DIM}Connecting to database"
for i in $(seq 1 20); do
    if PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1" > /dev/null 2>&1; then
        echo -e "${NC}"
        echo -e "  ${GREEN}✔${NC} Connected to database."
        break
    fi
    echo -n "."
    sleep 2
done

# Mark all existing documents as "seen"
EXISTING=$(PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
    -t -c "SELECT string_agg('''' || id || '''', ',') FROM documents;" 2>/dev/null | tr -d ' ')

if [ -n "$EXISTING" ] && [ "$EXISTING" != "" ]; then
    SEEN_IDS="$EXISTING"
    COUNT=$(get_doc_count)
    echo -e "  ${DIM}Found $COUNT existing document(s) in database (skipping).${NC}"
fi

echo ""
echo -e "  ${YELLOW}${BOLD}▶ Ready! Upload a PDF at http://localhost:5173 to see the output.${NC}"
echo ""

# ── Main polling loop ──────────────────────────────────────────────────────
while true; do
    NEW_ID=$(get_latest_doc)

    if [ -n "$NEW_ID" ]; then
        # Add to seen list
        if [ -n "$SEEN_IDS" ]; then
            SEEN_IDS="$SEEN_IDS,'$NEW_ID'"
        else
            SEEN_IDS="'$NEW_ID'"
        fi

        display_document "$NEW_ID"
    fi

    sleep 2
done

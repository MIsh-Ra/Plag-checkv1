#!/usr/bin/env python3
import json, re, shutil
from pathlib import Path

METADATA_FILE = Path("/home/23uec552/crawler_stuff/Downloads/metadata.json")
BASE_DIR = Path("/home/23uec552/crawler_stuff/Downloads")

# output dirs
BTP_DIR = BASE_DIR / "classified/btp_reports"
INTERN_DIR = BASE_DIR / "classified/internship_reports"
FACULTY_DIR = BASE_DIR / "classified/faculty_papers"

for d in [BTP_DIR, INTERN_DIR, FACULTY_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# roll number patterns
ROLL_PATTERN = re.compile(
    r'\b(Y\d{2}UC|BY\d{2}|\d{2}UEC|\d{2}UCS|\d{2}UCC|\d{2}UME|\d{2}UMM)\d+\b',
    re.IGNORECASE
)
BY_PATTERN = re.compile(r'\bBY\d{2}\b', re.IGNORECASE)

def classify(entry):
    authors = " ".join(entry.get("authors", []))
    filename = " ".join(entry.get("files", []))

    if BY_PATTERN.search(authors) or BY_PATTERN.search(filename):
        return INTERN_DIR
    elif ROLL_PATTERN.search(authors) or ROLL_PATTERN.search(filename):
        return BTP_DIR
    else:
        return FACULTY_DIR

metadata = json.loads(METADATA_FILE.read_text())
seen = set()
counts = {"btp_reports": 0, "internship_reports": 0, "faculty_papers": 0}

for entry in metadata:
    dest_dir = classify(entry)
    for filepath in entry.get("files", []):
        src = Path(filepath)
        if not src.exists() or str(src) in seen:
            continue
        seen.add(str(src))
        dest = dest_dir / src.name
        shutil.copy2(src, dest)
        counts[dest_dir.name] += 1
        print(f"[{dest_dir.name}] {src.name}")

print(f"\nDone.")
print(f"  BTP reports:        {counts['btp_reports']}")
print(f"  Internship reports: {counts['internship_reports']}")
print(f"  Faculty papers:     {counts['faculty_papers']}")
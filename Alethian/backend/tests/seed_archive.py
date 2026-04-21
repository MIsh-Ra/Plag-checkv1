"""
Archive Seeder — runs the REAL full pipeline on selected PDFs from Alethian_documents.
Grobid parse → SentenceTransformer embed → Qdrant index → Report generation.

Usage:
    cd backend
    PYTHONPATH=. python tests/seed_archive.py --archive-path /path/to/Alethian_documents
"""
import os
import sys
import json
import argparse
import uuid
import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure the app modules are importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.models import Base, Document, DocumentStatus, Report, Match, Source, HeatmapPage, User, UserRole
from app.core.shingling import process_text_into_chunks
from app.core.similarity import index_document
from app.core.report_engine import calculate_originality, generate_heatmap, build_summary_stats


def get_engine():
    db_url = (
        f"postgresql://{os.getenv('POSTGRES_USER', 'alethian')}"
        f":{os.getenv('POSTGRES_PASSWORD', 'alethian_pass')}"
        f"@{os.getenv('POSTGRES_HOST', 'localhost')}"
        f":{os.getenv('POSTGRES_PORT', '5433')}"
        f"/{os.getenv('POSTGRES_DB', 'alethian_db')}"
    )
    return create_engine(db_url)


def select_pdfs(archive_path, max_files=10, max_size_mb=1.5):
    """Pick small PDFs from the archive for speed."""
    metadata_path = os.path.join(archive_path, "metadata.json")
    if not os.path.exists(metadata_path):
        print(f"ERROR: metadata.json not found at {metadata_path}")
        return []

    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    selected = []
    seen_filenames = set()

    for entry in metadata:
        if len(selected) >= max_files:
            break

        # Extract filename from the files list
        files = entry.get("files", [])
        if not files:
            continue

        # The metadata stores paths like /home/23uec552/crawler_stuff/Downloads/filename.pdf
        # We need just the filename to find it locally
        original_path = files[0]
        filename = os.path.basename(original_path)

        if filename in seen_filenames:
            continue

        local_path = os.path.join(archive_path, filename)
        if not os.path.exists(local_path):
            continue

        size_mb = os.path.getsize(local_path) / (1024 * 1024)
        if size_mb > max_size_mb:
            continue

        seen_filenames.add(filename)
        selected.append({
            "filename": filename,
            "local_path": local_path,
            "title": entry.get("title", "Unknown Title"),
            "authors": entry.get("authors", []),
            "date": entry.get("date", ""),
            "source_url": entry.get("source_url", "")
        })

    return selected



def seed(archive_path, max_files=50):
    engine = get_engine()
    
    # Create all tables first before connecting
    from app.db.models import Base
    Base.metadata.create_all(bind=engine)
    
    Session = sessionmaker(bind=engine)
    db = Session()

    pdfs = select_pdfs(archive_path, max_files=max_files)
    if not pdfs:
        print("No suitable PDFs found in archive. Exiting.")
        return

    print(f"Selected {len(pdfs)} PDFs for seeding:")
    for p in pdfs:
        print(f"  - {p['filename']} ({p['title']})")

    # Ensure test faculty user exists
    faculty = db.query(User).filter(User.username == "faculty@test.edu").first()
    if not faculty:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        faculty = User(
            id="test-faculty-id",
            username="faculty@test.edu",
            email="faculty@test.edu",
            hashed_password=pwd_context.hash("testpass123"),
            full_name="Test Faculty",
            role=UserRole.faculty
        )
        db.add(faculty)
        db.commit()

    seeded_ids = []

    for pdf_info in pdfs:
        doc_id = str(uuid.uuid4())
        print(f"\n--- Processing: {pdf_info['filename']} ---")

        # Step 1: Extract text via 3-tier fallback (Grobid → pypdf → OCR)
        from app.core.text_extraction import extract_text_from_pdf
        parsed = extract_text_from_pdf(pdf_info["local_path"],
                                        grobid_url=os.getenv("GROBID_URL", "http://localhost:8070"))
        body_text = parsed.get("body_text", "")
        if len(body_text) < 50:
            print(f"  All extraction failed ({len(body_text)} chars, "
                  f"method={parsed.get('extraction_method')}). Skipping.")
            continue
        print(f"  Extracted: title='{parsed.get('title')}', "
              f"{len(parsed.get('sections', []))} sections, "
              f"method={parsed.get('extraction_method')}, "
              f"confidence={parsed.get('confidence')}")
              
        # Duplicate test strings if they are too small to chunk (F-05)
        if len(body_text.split()) < 300:
             body_text = (body_text + " ") * 10

        # Step 2: Create Document in DB
        doc = Document(
            id=doc_id,
            title=parsed.get("title") or pdf_info["title"],
            author=", ".join(pdf_info["authors"][:2]) if pdf_info["authors"] else "Unknown",
            filename=pdf_info["filename"],
            content=body_text,
            user_id="test-faculty-id",
            status=DocumentStatus.complete,
            page_count=parsed.get("page_count", 1),
            course_id="SEED",
            originality_score=None,
            risk_level=None,
        )
        db.add(doc)
        db.flush()

        # Step 3: Index in Qdrant (real embeddings)
        try:
            index_document(doc_id, body_text, title=doc.title)
            print(f"  Qdrant: indexed chunks for doc {doc_id}")
        except Exception as e:
            print(f"  Qdrant indexing FAILED: {e}")

        # Step 4: Create a synthetic report (since we don't run cross-doc similarity here)
        report_id = str(uuid.uuid4())
        source_id = str(uuid.uuid4())
        match_id = str(uuid.uuid4())

        source = Source(
            id=source_id,
            type="internal",
            title=f"Archive: {pdf_info['title']}",
            domain="internal",
            document_id=doc_id,
        )
        db.add(source)
        db.flush()

        # Create a synthetic match from extracted text
        match_text = body_text[:200] if len(body_text) > 200 else body_text
        match = Match(
            id=match_id,
            report_id=report_id,
            source_id=source_id,
            type="internal_exact",
            submitted_text=match_text,
            source_text=match_text,
            similarity=92.0,
            submitted_page=1,
            source_page=1,
            match_length_words=len(match_text.split()),
            is_excluded=False,
        )

        matches_dicts = [{
            "type": "internal_exact",
            "is_excluded": False,
            "submitted_text": match_text,
            "submitted_page": 1,
            "source_id": source_id,
            "match_length_words": len(match_text.split()),
            "source_title": source.title,
        }]

        word_count = len(body_text.split())
        score = calculate_originality(matches_dicts, word_count)
        risk = "high" if score < 50 else ("moderate" if score < 80 else "low")

        report = Report(
            id=report_id,
            document_id=doc_id,
            score=score,
            risk_level=risk,
            status="unreviewed",
            processing_time_seconds=30,
        )
        db.add(report)
        db.flush()
        db.add(match)
        db.flush()

        # Heatmap
        heatmap_data = generate_heatmap(matches_dicts, doc.page_count or 1)
        for hp in heatmap_data:
            db.add(HeatmapPage(
                id=str(uuid.uuid4()),
                report_id=report_id,
                page_number=hp["page_number"],
                density_score=hp["density_score"],
                internal_density=hp["internal_density"],
                web_density=hp["web_density"],
                color=hp["color"],
                match_count=hp["match_count"],
                dominant_type=hp["dominant_type"],
            ))

        # Update document scores
        doc.originality_score = score
        doc.risk_level = risk

        db.commit()
        seeded_ids.append(doc_id)
        print(f"  Report: score={score:.1f}, risk={risk}")

    db.close()
    print(f"\n=== Seeded {len(seeded_ids)} documents ===")
    for did in seeded_ids:
        print(f"  {did}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Alethian test database from real archive")
    parser.add_argument("--archive-path", required=True, help="Path to Alethian_documents directory")
    args = parser.parse_args()
    seed(args.archive_path)

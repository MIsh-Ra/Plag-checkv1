import os
import sys
import json
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging
import argparse
import re
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))
from app.core.similarity import index_document

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Alethian-Ingestor/2.0"}
DELAY = 1.0

def get_soup(session, url):
    try:
        r = session.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        logger.error(f"[FAIL] {url}: {e}")
        return None

def extract_metadata(soup):
    metadata = {}
    meta_tags = soup.find_all('meta')
    for tag in meta_tags:
        name = tag.get('name')
        content = tag.get('content')
        if name and content:
            if name.startswith('DC.') or name.startswith('DCTERMS.') or name == 'citation_pdf_url':
                key = name.replace('.', '_').lower()
                metadata[key] = content
    return metadata

def process_and_index(filepath, metadata):
    logger.info(f"Processing and indexing {filepath} (Stub - Grobid PDF parse goes here)")
    # Extract text using Grobid or PyMuPDF, then index it
    # dummy_text = extract_text_from_pdf(filepath)
    # document_id = generate_uuid()
    # index_document(document_id, dummy_text)
    pass

def save_to_db(metadata, filepath):
    logger.info("Saving metadata to Postgres DB (Stub)")
    pass

def ingest_archive(base_url, outdir, limit=1000):
    save_dir = Path(outdir)
    save_dir.mkdir(parents=True, exist_ok=True)
    
    metadata_file = save_dir / "ingest_metadata.json"
    visited_file = save_dir / "ingest_visited.txt"

    visited = set()
    if visited_file.exists():
        visited = set(visited_file.read_text().splitlines())

    all_metadata = []
    if metadata_file.exists():
        try:
            all_metadata = json.loads(metadata_file.read_text())
        except Exception as e:
            logger.warning(f"Failed to load metadata json: {e}")
            all_metadata = []

    already_downloaded = set(f for m in all_metadata for f in m.get("files", []))

    session = requests.Session()
    to_visit = [base_url]
    discovered = set(to_visit)

    logger.info("Phase 1: Discovering all handle pages...")
    handle_pages = []
    while to_visit and len(handle_pages) < limit:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)

        soup = get_soup(session, url)
        if not soup:
            continue

        for a in soup.find_all("a", href=True):
            href = urljoin(url, a["href"])
            if not href.startswith(base_url.rsplit('/', 1)[0]): 
                continue
            if "/handle/" in href and href not in discovered:
                href = href.split("?")[0]
                discovered.add(href)
                to_visit.append(href)
                if re.search(r'/handle/[0-9]+/[0-9]+$', href):
                    handle_pages.append(href)

        sys.stdout.write(f"  queued={len(to_visit)} visited={len(visited)} found_items={len(handle_pages)}\r")
        sys.stdout.flush()
        time.sleep(DELAY / 2)

    logger.info(f"\nPhase 1 done. Found {len(handle_pages)} item pages.")
    logger.info("Phase 2: Extracting metadata and downloading PDFs...")

    count = 0
    for url in set(handle_pages):
        if count >= limit:
            break
        count += 1
        
        soup = get_soup(session, url)
        if not soup:
            continue

        metadata = extract_metadata(soup)
        metadata["source_url"] = url
        metadata["files"] = []

        pdf_urls = []
        if "citation_pdf_url" in metadata:
            pdf_urls.append(metadata["citation_pdf_url"])
        else:
            bitstreams = soup.find_all("a", href=re.compile(r"/bitstream/"))
            pdf_urls.extend([urljoin(url, a["href"]) for a in bitstreams if a["href"].lower().split("?")[0].endswith(".pdf")])

        for file_url in pdf_urls:
            filename = file_url.split("/")[-1].split("?")[0]
            filename = re.sub(r"[^\w\.\-]", "_", filename)
            save_path = save_dir / filename

            if save_path.exists() or str(save_path) in already_downloaded:
                logger.info(f"[SKIP] {filename} already exists.")
                metadata["files"].append(str(save_path))
                continue

            try:
                r = session.get(file_url, headers=HEADERS, timeout=60, stream=True)
                r.raise_for_status()
                with open(save_path, "wb") as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)
                logger.info(f"[OK] Downloaded {filename}")
                metadata["files"].append(str(save_path))
                
                process_and_index(str(save_path), metadata)
                save_to_db(metadata, str(save_path))
                
            except Exception as e:
                logger.error(f"[FAIL] {file_url}: {e}")

            time.sleep(DELAY)

        if metadata["files"]:
            all_metadata.append(metadata)
            already_downloaded.update(metadata["files"])
            metadata_file.write_text(json.dumps(all_metadata, indent=2))

        with open(visited_file, "a") as vf:
            vf.write(url + "\n")

    logger.info("Ingestion complete.")

def main():
    parser = argparse.ArgumentParser(description="Ingest DGX DSpace Archive")
    parser.add_argument("--url", default="http://172.22.2.20:8080/xmlui/", help="Base URL for DSpace")
    parser.add_argument("--limit", type=int, default=50, help="Number of items to ingest limit")
    parser.add_argument("--outdir", default="./archive_pdfs", help="Directory to save PDFs")
    args = parser.parse_args()

    ingest_archive(args.url, args.outdir, limit=args.limit)

if __name__ == "__main__":
    main()

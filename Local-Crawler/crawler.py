#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time, json, re
from pathlib import Path

BASE_URL = "http://172.22.2.20:8080/jspui/"
SAVE_DIR = Path("/home/23uec552/crawler_stuff/Downloads")
METADATA_FILE = SAVE_DIR / "metadata.json"
VISITED_FILE = SAVE_DIR / "visited.txt"

HEADERS = {"User-Agent": "BTP-Crawler/1.0"}
DELAY = 1.0

def get_soup(session, url):
    try:
        r = session.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print(f"[FAIL] {url}: {e}")
        return None

def crawl():
    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    visited = set()
    if VISITED_FILE.exists():
        visited = set(VISITED_FILE.read_text().splitlines())

    metadata = []
    if METADATA_FILE.exists():
        try:
            metadata = json.loads(METADATA_FILE.read_text())
        except Exception as e:
            print(f"[WARN] Failed to load metadata.json: {e}; starting fresh")
            metadata = []

    already_downloaded = set(f for entry in metadata for f in entry.get("files", []))

    session = requests.Session()
    to_visit = [urljoin(BASE_URL, "handle/123456789/5")]
    discovered = set(to_visit)

    print("[*] Phase 1: discovering all handle pages...")
    while to_visit:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)

        soup = get_soup(session, url)
        if not soup:
            continue

        for a in soup.find_all("a", href=True):
            href = urljoin(url, a["href"])
            if not href.startswith(BASE_URL):
                continue
            if "/handle/" in href and href not in discovered:
                href = href.split("?")[0]
                discovered.add(href)
                to_visit.append(href)

        print(f"  queued={len(to_visit)} visited={len(visited)}", end="\r")
        time.sleep(DELAY)

    print(f"\n[*] Phase 1 done. {len(visited)} pages discovered.")
    print("[*] Phase 2: downloading PDFs from item pages...")

    for url in list(visited):
        if "/handle/" not in url:
            continue

        soup = get_soup(session, url)
        if not soup:
            continue

        bitstream_links = soup.find_all("a", href=re.compile(r"/bitstream/"))
        if not bitstream_links:
            time.sleep(DELAY)
            continue

        meta = {"source_url": url, "files": []}

        title_tag = soup.find("meta", attrs={"name": "DC.title"})
        if title_tag:
            meta["title"] = title_tag.get("content", "")

        author_tags = soup.find_all("meta", attrs={"name": "DC.creator"})
        meta["authors"] = [t.get("content", "") for t in author_tags]

        date_tag = soup.find("meta", attrs={"name": "DCTERMS.issued"})
        if date_tag:
            meta["date"] = date_tag.get("content", "")

        for link in bitstream_links:
            file_url = urljoin(url, link["href"])
            if not file_url.lower().split("?")[0].endswith(".pdf"):
                continue

            filename = file_url.split("/")[-1].split("?")[0]
            filename = re.sub(r"[^\w\.\-]", "_", filename)
            save_path = SAVE_DIR / filename

            if save_path.exists() or str(save_path) in already_downloaded:
                print(f"[SKIP] {filename}")
                meta["files"].append(str(save_path))
                continue

            try:
                r = session.get(file_url, headers=HEADERS, timeout=60, stream=True)
                r.raise_for_status()
                with open(save_path, "wb") as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)
                print(f"[OK]   {filename}")
                meta["files"].append(str(save_path))
            except Exception as e:
                print(f"[FAIL] {file_url}: {e}")

            time.sleep(DELAY)

        if meta["files"]:
            metadata.append(meta)
            already_downloaded.update(meta["files"])
            METADATA_FILE.write_text(json.dumps(metadata, indent=2))

        with open(VISITED_FILE, "a") as vf:
            vf.write(url + "\n")

        time.sleep(DELAY)

    print(f"\n[DONE] PDFs saved to {SAVE_DIR}")
    print(f"[DONE] Metadata at {METADATA_FILE}")

if __name__ == "__main__":
    crawl()
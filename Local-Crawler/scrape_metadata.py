#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json, time
from pathlib import Path

BASE_URL = "http://172.22.2.20:8080/jspui/"
SAVE_DIR = Path("/home/23uec552/crawler_stuff/Downloads")
METADATA_FILE = SAVE_DIR / "metadata.json"

HEADERS = {"User-Agent": "BTP-Crawler/1.0"}
DELAY = 0.5  # faster since no downloading

def get_soup(session, url):
    try:
        r = session.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print(f"[FAIL] {url}: {e}")
        return None

metadata = json.loads(METADATA_FILE.read_text())

# build a url -> entry map for easy lookup
url_map = {}
for entry in metadata:
    url = entry["source_url"].split("#")[0]
    url_map[url] = entry

session = requests.Session()
updated = 0

for url, entry in url_map.items():
    soup = get_soup(session, url)
    if not soup:
        continue

    # scrape metadata table
    table = soup.find("table", class_="table")
    if table:
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) == 2:
                key = cells[0].get_text(strip=True).lower().replace(".", "_").replace(" ", "_")
                val = cells[1].get_text(strip=True)
                if key and val and key not in entry:
                    entry[key] = val

    updated += 1
    print(f"[{updated}/{len(url_map)}] {url}", end="\r")
    time.sleep(DELAY)

METADATA_FILE.write_text(json.dumps(metadata, indent=2))
print(f"\nDone. Updated {updated} entries.")
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import json
import os
from dotenv import load_dotenv

load_dotenv()

SERPER_API_KEY = os.getenv("SERPER_API_KEY")

def search_google(query, num_results=5):

    print(f"[SEARCHING] Query: {query[:40]}...")
    links = []

    if SERPER_API_KEY != "PASTE_YOUR_KEY_HERE":
        try:
            url = "https://google.serper.dev/search"
            payload = json.dumps({
                "q": query,
                "num": num_results
            })
            headers = {
                'X-API-KEY': SERPER_API_KEY,
                'Content-Type': 'application/json'
            }

            response = requests.request("POST", url, headers=headers, data=payload)
            
            if response.status_code == 200:
                data = response.json()
                if "organic" in data:
                    for item in data["organic"]:
                        links.append(item["link"])
            else:
                print(f"  > Serper API Error: {response.status_code}")
                pass 

        except Exception as e:
            pass
    else:
        print("  > No Serper Key detected. Using DuckDuckGo...")


    if not links:
        if SERPER_API_KEY != "PASTE_YOUR_KEY_HERE":
            print("  > Serper returned 0 results. Switching to DuckDuckGo...")
        
        try:
            ddgs = DDGS()
            results = ddgs.text(query, region='wt-wt', max_results=num_results)
            if results:
                for r in results:
                    links.append(r['href'])
        except Exception as e:
            print(f"  > DuckDuckGo failed: {e}")

    # Remove duplicates
    unique_links = list(set(links))
    print(f"  > Found {len(unique_links)} links.")
    return unique_links

def download_url_text(url):

    print(f"[FETCHING] Downloading: {url}")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if "application/pdf" in response.headers.get('Content-Type', ''): return ""
        soup = BeautifulSoup(response.content, 'html.parser')
        for junk in soup(["script", "style", "nav", "footer", "header", "aside", "form"]): junk.extract()
        text = soup.get_text()
        return '\n'.join(chunk for line in text.splitlines() for chunk in [line.strip()] if chunk)
    except: return ""
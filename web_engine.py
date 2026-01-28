import requests
from bs4 import BeautifulSoup
from googlesearch import search as google_search
from duckduckgo_search import DDGS
import time

def search_google(query, num_results=3):
    print(f"[SEARCHING] Query: {query[:40]}...")
    links = []
    
    try:
        results = google_search(query, num_results=num_results, sleep_interval=2, advanced=True)
        for result in results:
            links.append(result.url)
    except Exception as e:
        print(f"  > Google Search failed: {e}")

    if not links:
        print("  > Google returned 0 results. Switching to DuckDuckGo...")
        try:
            ddgs = DDGS()
            results = ddgs.text(query, max_results=num_results)
            if results:
                for r in results:
                    links.append(r['href'])
        except Exception as e:
            print(f"  > DuckDuckGo failed: {e}")

    unique_links = list(set(links))
    print(f"  > Found {len(unique_links)} links.")
    return unique_links

def download_url_text(url):
    print(f"[FETCHING] Downloading: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code != 200:
            return ""

        soup = BeautifulSoup(response.content, 'html.parser')
        
        for junk in soup(["script", "style", "nav", "footer", "header", "aside"]):
            junk.extract()
            
        text = soup.get_text()
        
        lines = (line.strip() for line in text.splitlines())
        clean_text = '\n'.join(chunk for chunk in lines if chunk)
        
        return clean_text
        
    except Exception:
        return ""

import text_processor
import web_engine
import similarity_checker
import time

def check_internet_plagiarism(student_text):
    print("\n--- STEP 1: PROCESSING TEXT ---")

    windows = text_processor.create_sliding_windows(student_text, window_size=3)
    print(f"Broken text into {len(windows)} search chunks.")
    
    potential_urls = []
    
    print("\n--- STEP 2: SEARCHING THE WEB ---")

    for i, window in enumerate(windows[:2]): 
        print(f"Processing Chunk {i+1}/{len(windows)}...")
        query = text_processor.extract_search_query(window)
        

        urls = web_engine.search_google(query)
        potential_urls.extend(urls)
        
        time.sleep(1)

    unique_urls = list(set(potential_urls))
    print(f"\nFound {len(unique_urls)} unique sources to check.")
    
    print("\n--- STEP 3: DOWNLOADING & COMPARING ---")
    report = []
    

    for url in unique_urls:
        # Download
        web_content = web_engine.download_url_text(url)
        
        if not web_content:
            continue
            

        score = similarity_checker.calculate_similarity(student_text, web_content)

        if score > 0.15:
            report.append({
                "url": url,
                "score": score
            })
            print(f"  [!] MATCH FOUND: {int(score*100)}% with {url}")
        else:
            print(f"  [OK] Low similarity ({int(score*100)}%) with {url}")

    return report


if __name__ == "__main__":

    submission = """
    Bulbasaur is generally considered one of the most popular and widely liked Pokémon, having ranked highly in official popularity polls.[5] Series producer Junichi Masuda has also specifically mentioned Bulbasaur as one of his favorite Pokémon. Its role in the anime has been suggested to have played a factor into its popularity.
    """
    
    print("STARTING PLAGIARISM CHECK...")
    final_report = check_internet_plagiarism(submission)
    
    print("\n========= FINAL REPORT =========")
    if not final_report:
        print("No plagiarism detected.")
    else:

        final_report.sort(key=lambda x: x['score'], reverse=True)
        
        for item in final_report:
            print(f"ALERT: {int(item['score']*100)}% match found.")
            print(f"SOURCE: {item['url']}")
            print("-" * 30)
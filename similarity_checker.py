from sentence_transformers import SentenceTransformer, util
import warnings

warnings.filterwarnings("ignore")

print("Loading AI Model (all-MiniLM-L6-v2)...")
model = SentenceTransformer('all-MiniLM-L6-v2')

def calculate_similarity(text1, text2):
    if not text1 or not text2:
        return 0.0
    
    if len(text2) < 20: 
        return 0.0

    try:
        embedding_1 = model.encode(text1, convert_to_tensor=True)
        embedding_2 = model.encode(text2, convert_to_tensor=True)
        
        score = util.cos_sim(embedding_1, embedding_2).item()
        
        return max(0.0, score)
        
    except Exception as e:
        print(f"Similarity Error: {e}")
        return 0.0

if __name__ == "__main__":
    print("\n--- TESTING SEMANTIC AI ---")
    
    student = "The quick brown fox jumps over the lazy dog."
    
    match_text = "The quick brown fox jumps over the lazy dog."
    score1 = calculate_similarity(student, match_text)
    print(f"Exact Match:   {int(score1*100)}%")

    synonym_text = "A fast brown fox leaps above a tired canine."
    score2 = calculate_similarity(student, synonym_text)
    print(f"Synonym Check: {int(score2*100)}% (Should be high)")
    
    diff_text = "Python is a programming language used for data science."
    score3 = calculate_similarity(student, diff_text)
    print(f"Random Text:   {int(score3*100)}% (Should be low)")

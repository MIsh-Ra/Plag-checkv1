from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import warnings

warnings.filterwarnings("ignore")

def calculate_similarity(text1, text2):
    if not text1 or not text2:
        return 0.0
    
    if len(text2) < 50: 
        return 0.0

    documents = [text1, text2]
    
    try:
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(documents)
        
        similarity_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        
        return similarity_matrix[0][0]
        
    except Exception as e:
        print(f"Similarity Error: {e}")
        return 0.0

if __name__ == "__main__":
    print("--- TESTING SIMILARITY ---")
    
    student_essay = "The mitochondria is the powerhouse of the cell."
    
    web_source_1 = "The mitochondria is the powerhouse of the cell."
    score1 = calculate_similarity(student_essay, web_source_1)
    print(f"Exact Match Score: {score1:.2f}")
    
    web_source_2 = "Python is a great programming language for data science."
    score2 = calculate_similarity(student_essay, web_source_2)
    print(f"Different Topic Score: {score2:.2f}")
    
    web_source_3 = "Mitochondria act as the powerhouses for cells, generating energy."
    score3 = calculate_similarity(student_essay, web_source_3)
    print(f"Paraphrased Score: {score3:.2f}")

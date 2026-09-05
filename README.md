
# Alethian
 
A self-hosted plagiarism detection system for academic integrity checking.
 
## Overview
 
Alethian is a BTP (B.Tech project) that detects plagiarism in academic submissions by comparing them against a corpus of documents. It combines semantic similarity detection with information retrieval techniques to identify potential instances of copied or heavily paraphrased content.
 
## Tech Stack
 
- **Backend**: FastAPI, Celery, Redis
- **Database**: PostgreSQL (metadata), Qdrant (vector storage)
- **Frontend**: React
- **NLP**: Sentence Transformers (all-MiniLM-L6-v2) for embedding generation
- **Document Processing**: Grobid (for PDF parsing)
## Architecture
 
### Phase 1: Data Collection
- Built a web crawler for LNMIIT's DSpace repository
- Scraped and processed 500+ PDFs into the knowledge base
- Structured document extraction using Grobid
### Phase 2: Full Stack Implementation
- **Backend**: FastAPI endpoints for submission processing, search, and result retrieval
- **Task Queue**: Celery + Redis for async document embedding and plagiarism analysis
- **Vector Store**: Qdrant for semantic similarity search using sentence embeddings
- **Frontend**: React UI for submitting documents and viewing plagiarism reports
## How It Works
 
1. Submit a document (PDF or text)
2. Backend processes the document through Grobid for text extraction
3. Content is split into sentences and embedded using all-MiniLM-L6-v2
4. Celery job queues the embeddings for storage and search
5. Qdrant performs similarity search across the corpus
6. Results are returned with similarity scores and matched document references
## Key Features
 
- **Self-Hosted**: Full control over data and infrastructure
- **Semantic Search**: Beyond exact string matching—catches paraphrased content (within limitations)
- **Scalable**: Async processing with Celery allows handling of multiple concurrent submissions
- **Vector-Based**: Leverages modern embeddings for nuanced similarity detection
## Known Limitations
 
- **Sophisticated Paraphrasing**: May miss highly creative rewrites or significant structural changes
- **Domain Sensitivity**: Performance depends on corpus relevance; works best on academic writing
- **No Semantic Understanding**: Embeddings capture surface-level similarity, not deep meaning
## Development Notes
 
- **Evaluation Metrics**: Phase 1 defense highlighted the need for formal metrics (precision, recall, F1 on test sets)
- **Data Sovereignty**: All data remains on-premises; no external APIs used
- **Real-World Validation**: Tested with LNMIIT's DSpace corpus (500+ documents)

 
## Project Status
 
- Phase 1: Completed (crawler + corpus building)
- Phase 2: Completed (full stack + defense)
- Current: Ready for integration or further optimization
---
 

 

# Alethian System Diagrams v2.0

This document contains the architectural and design diagrams for the Alethian v2 Plagiarism Detection System (Internal Similarity + Web Dragnet).

## 1. System Architecture Diagram

```text
+-------------------------------------------------------------------------+
|                           Client Workstation                            |
| +---------------------------------------------------------------------+ |
| |                         Web Browser (SPA)                           | |
| +-----------------------------------+---------------------------------+ |
+-------------------------------------|-----------------------------------+
                                      | HTTPS / WebSocket
+-------------------------------------v-----------------------------------+
|                Institutional Server (Ubuntu 'Fat Node')                 |
|                                                                         |
| +----------------------+   +------------------------------------------+ |
| | Presentation Layer   |   |        Application & Logic Layer         | |
| | +------------------+ |   | +-----------------+  +-----------------+ | |
| | | React.js Frontend|<----->| FastAPI Backend |<---> Celery Queue  | | |
| | +------------------+ |   | +--------+--------+  +--------+--------+ | |
| +----------------------+   +----------|--------------------|---------+ |
|                                       |                    |            |
| +----------------------+   +----------v----------+  +------v----------+ |
| |   Data Persistence   |   | Text Processing     |  | External Data   | |
| | +------------------+ |   | +-----------------+ |  | +-------------+ | |
| | | Postgres (Data)  | |   | | Grobid (PDF)    | |  | | Redis (LSH) | | |
| | +------------------+ |   | +-----------------+ |  | +-------------+ | |
| | +------------------+ |   | +-----------------+ |  | +-------------+ | |
| | | Qdrant (Vector)  | |   | | Sentence-Trans. | |  | | (Cache)     | | |
| | +------------------+ |   | +-----------------+ |  | +-------------+ | |
| +----------------------+   +---------------------+  +-----------------+ |
+-------------------------------------|-----------------------------------+
                                      | HTTPS (Transient)
+-------------------------------------v-----------------------------------+
|                        External API                                     |
| +--------------------------------------------------------------------+ |
| |                         Serper.dev (Google Search)                  | |
| +--------------------------------------------------------------------+ |
+-------------------------------------------------------------------------+
```

---

## 2. Data Flow Diagrams (DFD)

### 2.1 Level 0 DFD (Context Diagram)

```text
      +--------------+                           +-----------------+
      |              | --(Upload PDF)---------->  |                 |
      | User/Faculty |                           | Alethian System |
      |              | <--(Plagiarism Report)--- |                 |
      +--------------+                           +--------+--------+
                                                          |
                                      +-------------------+-------------------+
                                      |                                       |
                             (Web Search Query)                      (Compare History)
                                      |                                       |
                           +----------v---------+                    +--------v--------+
                           |  Serper.dev API     |                    |  Local Archive  |
                           +--------------------+                    +-----------------+
```

### 2.2 Level 1 DFD (System Overview)

```text
+------+    +-----------------------------+
| User | -> | 1.0 Ingestion Engine        | (PDF -> JSON + Shingles)
+------+    +--------------+--------------+
                           |
            +--------------v--------------+
            | 2.0 Internal Similarity     | <---> [Local Archive (Redis/Qdrant)]
            +--------------+--------------+
                           |
            +--------------v--------------+
            | 3.0 Web Dragnet             | <---> [Serper.dev API]
            +--------------+--------------+
                           |
            +--------------v--------------+      +----------------+
            | 4.0 Report Generation       | ---> | Document Store | -> User
            +-----------------------------+      +----------------+
```

### 2.3 Level 2 DFD: Layer 1 (The Ingestion Engine)

```text
[PDF File]
    |
    v
[Grobid Parser] -> (XML/TEI)
    |
    v
< Confidence > 0.8? >-------NO------> [Llama-3-Vision OCR]
    |                                         |
   YES                                        |
    |                                     (Raw Text)
    v                                         |
[Document Normalizer] <-----------------------+
    |
    v
[Normalized JSON + Shingles]
    |
    +--> [PostgreSQL] (persist document)
    +--> [Redis] (store MinHash signatures)
    +--> [Qdrant] (store sentence embeddings)
```

### 2.4 Level 2 DFD: Layer 2 (Internal Similarity)

```text
[Body Text]
    |
    v
[MinHash Generator] -> [Redis LSH Index] -> < LSH Match (Jaccard > 0.5)? >
                                                  /      \
                                                YES      NO
                                                 |        |
                                                 v        v
                                     [Paragraph Aligner]  [Sentence Embedder]
                                         |                     |
                                         v                     v
                                   [Exact Matches]        [Qdrant Vector DB]
                                   (page, text, score)         |
                                                               v
                                                    < Cosine Sim > 0.85? >
                                                      /              \
                                                    YES              NO
                                                     |                |
                                                     v                v
                                              [Paraphrase Match] [Mark as Original]
                                              (page, text, score)

           All matches --> [PostgreSQL: Report Matches Table]
```

### 2.5 Level 2 DFD: Layer 3 (Web Dragnet)

```text
[Text Not Matched in Layer 2]
    |
    v
[Suspicious Chunk Selector] -> (Dense/uncited passages)
    |
    v
[Serper.dev API] -> [Search Results (URLs)]
                          |
                          v
                 [Content Fetcher & Comparator]
                          |
                          v
                 [Source Coherence Analyzer]
                          |
                          v
            < >=3 Chunks from Same Domain? >
                /                     \
              YES                     NO
               |                       |
               v                       v
      [Flag: Systematic        [Individual Match]
       Web Plagiarism]

           All matches --> [PostgreSQL: Report Matches Table]
```

### 2.6 Report Generation Flow

```text
[All Matches from Layer 2 + 3]
    |
    +---> [Score Calculator] --> Originality Score (0-100%)
    |
    +---> [Source Aggregator] --> Unique source list + coverage %
    |
    +---> [Heatmap Generator] --> Per-page match density
    |
    +---> [Chart Data Builder] --> Pie chart, bar chart data
    |
    v
[Final Report JSON] --> [PostgreSQL]
    |
    +--> [React Dashboard] (real-time)
    +--> [PDF Generator] (on-demand export)
    +--> [JSON Export] (on-demand)
```

---

## 3. Entity-Relationship Diagram (ERD)

```text
[Users]
  | id (PK)
  | email
  | role
  | created_at
  |
  +---||--o{ [Documents]
               | id (PK)
               | title
               | filename
               | page_count
               | course_id
               | uploaded_at
               |
               +---||--|| [Reports]
                            | id (PK)
                            | originality_score
                            | risk_level
                            | status
                            | reviewed_by (FK -> Users)
                            | review_notes
                            | reviewed_at
                            |
                            +---||--o{ [Matches]
                            |            | id (PK)
                            |            | type (internal_exact|internal_paraphrase|web)
                            |            | submitted_text
                            |            | submitted_page
                            |            | source_text
                            |            | source_page
                            |            | similarity_score
                            |            | is_excluded
                            |            | faculty_comment
                            |            |
                            |            }
                            |            | (refers to)
                            |            |
                            |          [Sources]
                            |            | id (PK)
                            |            | type (internal|web)
                            |            | name
                            |            | url (nullable)
                            |            | domain (nullable)
                            |            | document_id (FK, nullable)
                            |            | coverage_percent
                            |
                            +---||--o{ [HeatmapPages]
                                         | page_num
                                         | match_density
                                         | dominant_type
```

---

## 4. Use Case Diagram

```text
                   +----------------------------------+
                   |         Alethian System          |
                   |                                  |
                   |  (UC1: Upload PDF) <-----------+ |
                   |                                | |
                   |  (UC2: View Report Dashboard)<-+ |
+--------+        |                                | |
| Faculty|------->|  (UC3: Side-by-Side Diff)  <---+ |
+--------+        |                                | |
                   |  (UC4: Exclude Match)      <--+ |
                   |                                | |
                   |  (UC5: Annotate Finding)   <--+ |
                   |                                | |
                   |  (UC6: Export PDF/JSON)    <---+ |
                   |                                | |
                   |  (UC7: Mark as Reviewed)   <--+ |
                   |                                  |
                   |  (UC8: Configure API Keys) <----+----+
                   |                                 |    |
                   |  (UC9: Adjust Thresholds) <-----+    |
+-------------+    |                                 | +-------+
| Administrator|-->|  (UC10: Manage Users)     <-----+ | Admin |
+-------------+    |                                   +-------+
                   |                                  |
                   +----------------------------------+
```

---

## 5. Sequence Diagrams

### 5.1 Full Submission Pipeline

```text
User         API          Queue        Ingestion    Similarity   Web Dragnet  DB
 |            |            |               |            |            |         |
 |--Upload--->|            |               |            |            |         |
 |            |--Create--->|               |            |            |         |
 |            |            |--Process----->|            |            |         |
 |            |            |<--JSON--------|            |            |         |
 |            |            |               |            |            |         |
 |            |            |--CheckSim---->|            |            |         |
 |            |            |               |--MinHash-->|            |         |
 |            |            |               |--Vectors-->|            |         |
 |            |            |               |            |            |--Save-->|
 |            |            |               |            |            |         |
 |            |            |--Dragnet----->|            |            |         |
 |            |            |               |            |--Search--->|         |
 |            |            |               |            |            |--Save-->|
 |            |            |               |            |            |         |
 |            |            |--GenReport--->|            |            |         |
 |            |            |               |            |            |--Save-->|
 |            |--Notify--->|               |            |            |--Done-->|
```

### 5.2 Faculty Report Review & Export

```text
Faculty       Dashboard      API           DB            PDF Generator
   |             |            |             |                |
   |--Select---->|            |             |                |
   |             |--Get Data->|             |                |
   |             |            |--Fetch----->|                |
   |             |            |<--JSON------|                |
   |             |<--Render---|             |                |
   |             |            |             |                |
   |--Clk Match->|            |             |                |
   |             |--ShowDiff->|             |                |
   |             |            |             |                |
   |--Exclude--->|            |             |                |
   |             |--Patch---->|             |                |
   |             |            |--Update---->|                |
   |             |<--NewScore-|             |                |
   |             |            |             |                |
   |--Export---->|            |             |                |
   |             |--Request-->|             |                |
   |             |            |--Generate-->|                |
   |             |            |             |<--PDF Blob-----|
   |             |<--Downld---|             |                |
```

---

## 6. Class Diagram

```text
+-----------------------+           +-----------------------+
|   DocumentProcessor   |           |       Document        |
+-----------------------+           +-----------------------+
| +process(pdf)         |---------->| +UUID id              |
| +normalize(raw)       | creates   | +String title         |
| +generate_shingles()  |           | +List~Page~ pages     |
| -route_to_ocr()       |           | +JSON metadata        |
+-----------------------+           +-----------------------+

+-----------------------+           +------------------+
|   SimilarityEngine    |---------->|   LocalArchive   |
+-----------------------+  queries  +------------------+
| +minhash(text)        |           | +Redis LSH Index |
| +vector_search(text)  |           | +Qdrant Vectors  |
| +paragraph_align()    |           +------------------+
| +batch_compare()      |
+-----------------------+

+-----------------------+           +------------------+
|      WebDragnet       |---------->|   SerperClient   |
+-----------------------+  queries  +------------------+
| +isolate_chunks()     |
| +search_web()         |           +------------------+
| +fetch_and_compare()  |---------->| ContentFetcher   |
| +coherence_analysis() |  fetches  +------------------+
+-----------------------+

+-----------------------+           +------------------+
|   ReportGenerator     |---------->|  PDFExporter     |
+-----------------------+  exports  +------------------+
| +aggregate_findings() |
| +compute_score()      |
| +generate_heatmap()   |
| +build_charts()       |
| +export_pdf()         |
| +export_json()        |
+-----------------------+
```

---

## 7. Deployment Diagram

```text
    +------------------+
    | Client Workstation|
    | +--------------+ |
    | |  Browser     | |
    | +-------+------+ |
    +---------|--------+
              | HTTPS
    +---------v-----------------------------------------+
    | Institutional Server (Docker Host)                |
    |                                                   |
    |  +----------------+    +-------------------+      |
    |  | Frontend Cont. |    | Backend Cont.     |      |
    |  | [Nginx/Vite]   |--->| [FastAPI]         |      |
    |  +----------------+    +---------+---------+      |
    |                                  |                |
    |         +------------------------+-------+        |
    |         |                        |       |        |
    |  +------v-------+         +------v------v------+  |
    |  | Data Conts.  |         | Processing Conts.  |  |
    |  | [Postgres]   |         | [Grobid Service]   |  |
    |  | [Redis]      |         |                    |  |
    |  | [Qdrant]     |         |                    |  |
    |  +--------------+         +----------+---------+  |
    |                                      |            |
    +--------------------------------------|------------+
                                           | HTTPS
                            +--------------v-------------+
                            | External API               |
                            | [Serper.dev]               |
                            +----------------------------+
```

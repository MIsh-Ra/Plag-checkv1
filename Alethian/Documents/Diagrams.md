# Alethian System Diagrams

This document contains the architectural and design diagrams for the Alethian Local-First Research Integrity System, based on the SRS Version 1.0.

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
| +----------------------+   +----------|--------------------|----------+ |
|                                       |                    |            |
| +----------------------+   +----------v----------+  +------v----------+ |
| |   Data Persistence   |   | AI & Compute Engines|  | External Data   | |
| | +------------------+ |   | +-----------------+ |  | +-------------+ | |
| | | Postgres (Data)  | |   | | Grobid (PDF)    | |  | | Redis (LSH) | | |
| | +------------------+ |   | +-----------------+ |  | +-------------+ | |
| | +------------------+ |   | +-----------------+ |  | +-------------+ | |
| | | Qdrant (Vector)  | |   | | Llama/Falcon    | |  | | (Cache)     | | |
| | +------------------+ |   | +-----------------+ |  | +-------------+ | |
| +----------------------+   +---------------------+  +-----------------+ |
+-------------------------------------|-----------------------------------+
                                      | HTTPS (Transient)
+-------------------------------------v-----------------------------------+
|                        External API Mesh                                |
| +-------------------+  +--------------------+  +----------------------+ |
| | Semantic Scholar  |  |     Unpaywall      |  |      Serper.dev      | |
| +-------------------+  +--------------------+  +----------------------+ |
+-------------------------------------------------------------------------+
```

---

## 2. Data Flow Diagrams (DFD)

### 2.1 Level 0 DFD (Context Diagram)

```text
      +--------------+                           +-----------------+
      |              | --(Upload PDF)----------> |                 |
      | User/Faculty |                           | Alethian System |
      |              | <--(Validation Report)--- |                 |
      +--------------+                           +--------+--------+
                                                          |
                                      +-------------------+-------------------+
                                      |                                       |
                            (Query Citation/Web)                      (Compare History)
                                      |                                       |
                           +----------v---------+                    +--------v--------+
                           | External API Mesh  |                    |  Local Archive  |
                           +--------------------+                    +-----------------+
```

### 2.2 Level 1 DFD (System Overview)

```text
+------+    +-----------------------------+
| User | -> | 1.0 Ingestion Engine        | (PDF -> JSON)
+------+    +--------------+--------------+
                           |
            +--------------v--------------+
            | 2.0 Reference Validation    | <---> [External Data Sources]
            +--------------+--------------+
                           |
            +--------------v--------------+
            | 3.0 Internal Similarity     | <---> [Local Archive]
            +--------------+--------------+
                           |
            +--------------v--------------+
            | 4.0 Web Dragnet             | <---> [External Data Sources]
            +--------------+--------------+
                           |
            +--------------v--------------+
            | 5.0 AI Forensics            |
            +--------------+--------------+
                           |
            +--------------v--------------+      +----------------+
            | 6.0 Report Generation       | ---> | Document Store | -> User
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
[Normalized JSON Object]
```

### 2.4 Level 2 DFD: Layer 2 (Reference Validation)

```text
[Normalized JSON] -> [Citation Extractor] -> [Extracted References]
                                                      |
                                                      v
                                            [Semantic Scholar API]
                                                      |
                                                      v
                                             < Found in API? >
                                              /             \
                                            NO              YES
                                            |                |
                                            v                v
                                     [Flag: Hallucin.]  < Is Retracted? >
                                                             /        \
                                                           YES        NO
                                                            |          |
                                                            v          v
                                                   [Flag: Retracted] [Unpaywall API]
                                                                       |
                                                                       v
                                                               < Abstract Match > 0.4? >
                                                                  /               \
                                                                NO                YES
                                                                |                  |
                                                                v                  v
                                                         [Flag: Misrep.]     [Mark Verified]
```

### 2.5 Level 2 DFD: Layer 3 (Internal Similarity)

```text
[Body Text]
    |
    v
[MinHash Generator] -> [Redis LSH Index] -> < LSH Match? >
                                                 /      \
                                               YES      NO
                                                |        |
                                                v        v
                                          [Flag: Exact] [Qdrant Embedder]
                                                         |
                                                         v
                                                    [Qdrant Vector DB]
                                                         |
                                                         v
                                                 < Similarity > 0.85? >
                                                   /              \
                                                 YES              NO
                                                  |                |
                                                  v                v
                                            [Flag: Para.]    [Safe/Novel]
```

### 2.6 Level 2 DFD: Layer 4 (Web Dragnet)

```text
[Safe Text]
    |
    v
[Suspicious Chunker] -> (Low Perplexity Chunks)
    |
    v
[Serper.dev API] -> [Search Results]
                          |
                          v
               [Source Coherence Analyzer]
                          |
                          v
            < >3 Chunks from Same Domain? >
               /                     \
             YES                     NO
              |                       |
              v                       v
     [Flag: Web Plag.]           [No Action]
```

### 2.7 Level 2 DFD: Layer 5 (AI Forensics)

```text
[Body Text] -> [Tokenizer]
                   |
        +----------+----------+
        |                     |
[Llama-3 (Observer)]  [Falcon-7B (Performer)]
        |                     |
        +----------+----------+
                   |
        [Calculate Binoculars Metric] -> [Generate Plots] -> [Report]
                   ^
                   |
      [Calculate Burstiness/Perplexity] <--- [Body Text]
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
               | uploaded_at
               |
               +---||--|| [Reports]
                            | id (PK)
                            | total_score
                            | status
                            | metadata
                            |
                            +---||--o{ [Citations]
                            |            | id (PK)
                            |            | status
                            |            | coherence_score
                            |            |
                            |            }
                            |            | (matches external)
                            |            |
                            |          [ReferenceSources]
                            |            | doi (PK)
                            |            | title
                            |            | is_retracted
                            |
                            +---||--o{ [Segments]
                                         | id (PK)
                                         | page_num
                                         | text_content
                                         | type
                                         | anomaly_score
                                         |
                                         }
                                         | (found in)
                                         |
                                       [WebMatches]
                                         | id (PK)
                                         | url
                                         | domain
                                         | search_score
```

---

## 4. Use Case Diagrams

```text
                   +----------------------------------+
                   |         Alethian System          |
                   |                                  |
                   |  (UC1: Upload PDF Thesis) <---+  |
                   |                               |  |
                   |  (UC2: View Analysis Report) <+-+|
+--------+         |                               | ||
| Faculty|-------->|  (UC3: Export Signed PDF) <---+ ||
+--------+         |                               | ||
                   |  (UC4: Toggle Diff View) <----+ ||
                   |                                 ||
                   |                                 ||
                   |  (UC5: Configure API Keys) <----++------+
                   |                                 |       |
                   |  (UC6: Adjust Thresholds) <-----+       |
+-------------+    |                                 |   +-------+
| Administrator|-->|  (UC7: Manage User Roles) <-----+   | Admin |
+-------------+    |                                 |   +-------+
                   |                                 |
                   +---------------------------------+
```

---

## 5. Sequence Diagrams

### 5.1 Scenario 1: Full Submission Pipeline

```text
User         API          Queue        Ingestion    Reference    Similarity   Forensics    Web          DB
 |            |            |               |            |            |            |            |         |
 |--Upload--->|            |               |            |            |            |            |         |
 |            |--Create--->|               |            |            |            |            |         |
 |            |            |--Process----->|            |            |            |            |         |
 |            |            |<--JSON--------|            |            |            |            |         |
 |            |            |               |            |            |            |            |         |
 |            |            |--Validate---->|            |            |            |            |         |
 |            |            |               |--Check---->|            |            |            |         |
 |            |            |               |            |            |            |            |--Save-->|
 |            |            |--CheckSim---->|            |            |            |            |         |
 |            |            |               |            |--Search--->|            |            |         |
 |            |            |               |            |            |            |            |--Save-->|
 |            |            |--Analyze----->|            |            |            |            |         |
 |            |            |               |            |            |--Binoc.--> |            |         |
 |            |            |               |            |            |            |            |--Save-->|
 |            |            |               |            |            |            |            |         |
 |            |            |--Dragnet----->|            |            |            |            |         |
 |            |            |               |            |            |            |--Search--->|         |
 |            |            |               |            |            |            |            |--Save-->|
 |            |            |               |            |            |            |            |         |
 |            |--Notify--->|               |            |            |            |            |--Done-->|
```

### 5.2 Scenario 2: Faculty Report Review & Export

```text
Faculty       Dashboard      API           DB            Generator
   |             |            |             |                |
   |--Select---->|            |             |                |
   |             |--Get Data->|             |                |
   |             |            |--Fetch----->|                |
   |             |            |<--JSON------|                |
   |             |<--Render---|             |                |
   |             |            |             |                |
   |--Clk Red--->|            |             |                |
   |             |--ShowDiff->|             |                |
   |--Verify---->|            |             |                |
   |             |            |             |                |
   |--Export---->|            |             |                |
   |             |--Request-->|             |                |
   |             |            |--Gen-------->|                |
   |             |            |             |<--PDF Blob-----|
   |             |<--Downld---|             |                |
```

### 5.3 Scenario 3: Ingestion Fallback Handling

```text
Queue       Grobid       Llama-3-Vision     Normalizer
  |           |                |                |
  |--Parse--->|                |                |
  |<--TEI-----|                |                |
  |           |                |                |
  +---[ALT: Conf < 0.8]--------+                |
  |           |                |                |
  |--OCR Req------------------>|                |
  |           |                |                |
  |<--Raw Text-----------------|                |
  |           |                |                |
  |--Normalize--------------------------------->|
  |           |                |                |
  +---[ELSE: Conf >= 0.8]------+                |
  |           |                |                |
  |--Normalize--------------------------------->|
  |           |                |                |
  |<--Final JSON--------------------------------|
```

### 5.4 Scenario 4: Admin Configuration

```text
Admin        API        KeyVault       DB
  |           |            |            |
  |--Update-->|            |            |
  |           |--Validate->|            |
  |           |<--OK-------|            |
  |           |            |            |
  |--Set Thr->|            |            |
  |           |--Update--->|            |
  |           |            |--Commit--->|
  |           |<--Confirm--|            |
  |<--Done----|            |            |
```

---

## 6. Class Diagrams

```text
+-----------------------+           +-----------------------+
|   DocumentProcessor   |           |       Document        |
+-----------------------+           +-----------------------+
| +process(pdf)         |---------->| +UUID id              |
| +normalize(raw)       | creates   | +String title         |
| -route_to_ocr()       |           | +List~Page~ pages     |
+-----------------------+           +-----------------------+

+-----------------------+           +-----------------------+
|   CitationValidator   |           |       Citation        |
+-----------------------+           +-----------------------+
| +extract(text)        |---------->| +String raw_text      |
| +validate(citation)   | validates | +Boolean hallucinated |
| +check_retraction()   |           | +Boolean retracted    |
+-----------------------+           +-----------------------+
        ^
        | (uses)
+-------+-------+
| APIMeshClient |
+---------------+

+-----------------------+           +------------------+
|   SimilarityEngine    |---------->|   LocalArchive   |
+-----------------------+  uses     +------------------+
| +minhash(text)        |
| +vector_search(text)  |
+-----------------------+

+-----------------------+           +------------------+
|      WebDragnet       |---------->|   SerperClient   |
+-----------------------+  uses     +------------------+
| +isolate_chunks()     |
| +search_web()         |
+-----------------------+

+-----------------------+           +------------------+
|   ForensicAnalyzer    |---------->|  LocalLLMClient  |
+-----------------------+  uses     +------------------+
| +calc_binoculars()    |
| +burstiness()         |
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
    |  | Data Conts.  |         | AI Containers      |  |
    |  | [Postgres]   |         | [Grobid Service]   |  |
    |  | [Redis]      |         | [vLLM Inference]   |  |
    |  | [Qdrant]     |         |                    |  |
    |  +--------------+         +----------+---------+  |
    |                                      |            |
    +--------------------------------------|------------+
                                           | HTTPS
                            +--------------v-------------+
                            | External Cloud APIs        |
                            | [S2, Unpaywall, Serper]    |
                            +----------------------------+
```

# Alethian System Diagrams v2.0 (Mermaid)

This document contains the architectural and design diagrams for the Alethian v2 Plagiarism Detection System, using Mermaid syntax for rich rendering.

## 1. System Architecture Diagram

```mermaid
graph TD
    subgraph Client_Workstation ["Client Workstation"]
        Browser["Web Browser (SPA)"]
    end

    subgraph Institutional_Server ["Institutional Hardware (Ubuntu 'Fat Node')"]
        direction TB
        subgraph Frontend_Layer ["Presentation Layer"]
            UI["React.js Frontend"]
        end
        
        subgraph Backend_Layer ["Application & Logic Layer"]
            API["FastAPI Backend"]
            Celery["Celery Task Queue"]
        end
        
        subgraph Data_Layer ["Data Persistence"]
            Postgres[("PostgreSQL\n(Users, Documents, Reports)")]
            Redis[("Redis\n(LSH Index + Cache)")]
            Qdrant[("Qdrant\n(Vector Embeddings)")]
        end
        
        subgraph Processing_Layer ["Text Processing"]
            Grobid["Grobid Service\n(PDF Parsing)"]
            SentTrans["Sentence-Transformers\n(Embedding Generation)"]
        end
    end

    subgraph External_Cloud ["External API"]
        Serper["Serper.dev\n(Google Search API)"]
    end

    %% Flows
    Browser <-->|HTTPS/WebSocket| UI
    UI <-->|REST| API
    API <-->|Task Dispatch| Celery
    
    API <-->|SQL| Postgres
    API <-->|Key-Value| Redis
    
    Celery <-->|Read/Write| Postgres
    Celery <-->|LSH Index| Redis
    Celery <-->|Vector Search| Qdrant
    
    Celery -->|Parse PDF| Grobid
    Celery -->|Generate Embeddings| SentTrans
    
    Celery <-->|Web Dragnet| Serper

    classDef external fill:#eee,stroke:#999,stroke-width:2px,stroke-dasharray: 5 5;
    classDef storage fill:#ff9,stroke:#333,stroke-width:2px;
    classDef processing fill:#f9f,stroke:#333,stroke-width:2px;
    
    class Serper external;
    class Postgres,Redis,Qdrant storage;
    class Grobid,SentTrans processing;
```

---

## 2. Data Flow Diagrams (DFD)

### 2.1 Level 0 DFD (Context Diagram)

```mermaid
graph LR
    User(Faculty / Reviewer)
    System[Alethian System]
    Serper["Serper.dev\n(Google Search)"]
    LocalDocs[Local Document Archive]

    User -->|Upload PDF| System
    User -->|Request Report| System
    System -->|Plagiarism Report| User
    System -->|Real-time Status| User

    System <-->|Search Suspicious Chunks| Serper
    System <-->|Compare Against History| LocalDocs
```

### 2.2 Level 1 DFD (System Overview)

```mermaid
graph TD
    %% Entities
    User((User))
    DocStore[("Report Store")]
    Serper[("Serper.dev")]
    Archive[("Local Archive\n(Redis + Qdrant)")]

    %% Processes
    P1[1.0 Ingestion Engine]
    P2[2.0 Internal Similarity]
    P3[3.0 Web Dragnet]
    P4[4.0 Report Generation]

    %% Data Flows
    User -->|PDF File| P1
    P1 -->|Structured JSON + Shingles| P2
    
    P2 <-->|MinHash/Vectors| Archive
    P2 -->|Internal Matches| P4
    P2 -->|Unmatched Chunks| P3
    
    P3 <-->|Search Queries| Serper
    P3 -->|Web Matches| P4
    
    P4 -->|Final Report| DocStore
    DocStore -->|View Dashboard| User
```

### 2.3 Level 2 DFD: Layer 1 (The Ingestion Engine)

```mermaid
graph TD
    Input[PDF File]
    Grobid[Grobid Parser]
    ConfCheck{Confidence > 0.8?}
    Vision[Llama-3-Vision OCR]
    Norm[Document Normalizer]
    Shingler[Shingle Generator]
    JSON[Normalized JSON]
    DB[("PostgreSQL")]
    RedisStore[("Redis LSH")]
    QdrantStore[("Qdrant Vectors")]

    Input --> Grobid
    Grobid -->|XML/TEI| ConfCheck
    ConfCheck -- Yes --> Norm
    ConfCheck -- No --> Vision
    Vision -->|Raw Text| Norm
    Norm --> JSON
    JSON --> Shingler
    Shingler --> DB
    Shingler --> RedisStore
    Shingler --> QdrantStore
```

### 2.4 Level 2 DFD: Layer 2 (Internal Similarity)

```mermaid
graph TD
    Text[Body Text Input]
    MinHash[MinHash Generator]
    Redis[Redis LSH Index]
    LSHMatch{Jaccard > 0.5?}
    
    Aligner[Paragraph Aligner]
    VecEmbed[Sentence Embedder]
    VecDB[Qdrant Vector DB]
    SemMatch{Cosine Sim > 0.85?}
    
    FlagExact["Flag: Exact Copy\n(page, text, score)"]
    FlagPara["Flag: Paraphrase\n(page, text, score)"]
    Safe[Original Content]
    DB[("Save to Matches Table")]

    Text --> MinHash
    MinHash --> Redis
    Redis --> LSHMatch
    
    LSHMatch -- Yes --> Aligner
    Aligner --> FlagExact
    
    LSHMatch -- No --> VecEmbed
    VecEmbed --> VecDB
    VecDB --> SemMatch
    
    SemMatch -- Yes --> FlagPara
    SemMatch -- No --> Safe
    
    FlagExact --> DB
    FlagPara --> DB
```

### 2.5 Level 2 DFD: Layer 3 (Web Dragnet)

```mermaid
graph TD
    Input["Unmatched Text\n(Passed Layer 2)"]
    Chunker[Suspicious Chunk Selector]
    Serper[Serper.dev API]
    Results[Search Results]
    Fetcher[Content Fetcher]
    Comparator[Text Comparator]
    Coherence[Source Coherence Analyzer]
    
    Threshold{">=3 Chunks\nfrom Same Domain?"}
    FlagWeb["Flag: Web Match\n(url, text, score)"]
    FlagCoherent["Flag: Systematic\nWeb Plagiarism"]
    DB[("Save to Matches Table")]

    Input --> Chunker
    Chunker -->|Dense Passages| Serper
    Serper --> Results
    Results --> Fetcher
    Fetcher -->|Source Text| Comparator
    Comparator --> FlagWeb
    FlagWeb --> Coherence
    Coherence --> Threshold
    
    Threshold -- Yes --> FlagCoherent
    Threshold -- No --> DB
    FlagCoherent --> DB
    FlagWeb --> DB
```

### 2.6 Report Generation Flow

```mermaid
graph TD
    Internal[Internal Similarity Matches]
    Web[Web Dragnet Matches]
    
    Aggregator[Match Aggregator]
    Scorer[Score Calculator]
    HeatmapGen[Heatmap Generator]
    SourceGen[Source Aggregator]
    ChartGen[Chart Data Builder]
    
    Report[("Final Report JSON")]
    Dashboard[React Dashboard]
    PDFGen[PDF Generator]
    JSONExport[JSON Export]

    Internal --> Aggregator
    Web --> Aggregator
    
    Aggregator --> Scorer
    Aggregator --> HeatmapGen
    Aggregator --> SourceGen
    Aggregator --> ChartGen
    
    Scorer --> Report
    HeatmapGen --> Report
    SourceGen --> Report
    ChartGen --> Report
    
    Report --> Dashboard
    Report --> PDFGen
    Report --> JSONExport
```

---

## 3. Entity-Relationship Diagram (ERD)

```mermaid
erDiagram
    Users ||--o{ Documents : uploads
    Documents ||--|| Reports : generates
    Reports ||--o{ Matches : contains
    Reports ||--o{ Sources : lists
    Reports ||--o{ HeatmapPages : "has pages"
    
    Matches }|--|| Sources : "refers to"

    Users {
        uuid id PK
        string email
        string role "Faculty|Admin"
        timestamp created_at
    }

    Documents {
        uuid id PK
        string title
        string filename
        int page_count
        string course_id "nullable"
        timestamp uploaded_at
        uuid uploader_id FK
    }

    Reports {
        uuid id PK
        uuid document_id FK
        float originality_score
        float similarity_score
        string risk_level "high|moderate|low"
        string status "pending|analyzing|complete"
        string review_status "unreviewed|reviewed"
        uuid reviewed_by FK
        text review_notes
        timestamp reviewed_at
        jsonb summary_stats
        int processing_time_seconds
    }

    Matches {
        uuid id PK
        uuid report_id FK
        uuid source_id FK
        string type "internal_exact|internal_paraphrase|web"
        text submitted_text
        int submitted_page
        int submitted_start_char
        int submitted_end_char
        text source_text
        int source_page
        float similarity_score
        int match_length_words
        boolean is_excluded
        string exclude_reason
        text faculty_comment
        string color_code
    }

    Sources {
        uuid id PK
        uuid report_id FK
        string type "internal|web"
        string name
        uuid source_document_id FK "nullable"
        string url "nullable"
        string domain "nullable"
        float coverage_percent
        int match_count
        boolean is_coherent_source
    }

    HeatmapPages {
        uuid id PK
        uuid report_id FK
        int page_num
        float match_density
        float internal_density
        float web_density
        string color
        int match_count
    }
```

---

## 4. Use Case Diagram

```mermaid
graph LR
    subgraph "Alethian System"
        direction TB
        UC1(Upload PDF)
        UC2(View Report Dashboard)
        UC3(Side-by-Side Diff)
        UC4(Exclude Match)
        UC5(Annotate Finding)
        UC6(Export PDF/JSON)
        UC7(Mark as Reviewed)
        UC8(Filter by Match Type)
        UC9(View Heatmap)
        UC10(Configure API Keys)
        UC11(Adjust Thresholds)
        UC12(Manage Users)
    end

    Faculty((Faculty))
    Admin((Administrator))

    Faculty --> UC1
    Faculty --> UC2
    Faculty --> UC3
    Faculty --> UC4
    Faculty --> UC5
    Faculty --> UC6
    Faculty --> UC7
    Faculty --> UC8
    Faculty --> UC9
    
    Admin --> UC10
    Admin --> UC11
    Admin --> UC12
    Admin --> UC2
```

---

## 5. Sequence Diagrams

### 5.1 Full Submission Pipeline

```mermaid
sequenceDiagram
    participant U as User
    participant API as Backend API
    participant Q as Task Queue
    participant Ing as 1. Ingestion
    participant Sim as 2. Similarity Engine
    participant Web as 3. Web Dragnet
    participant Rep as 4. Report Generator
    participant DB as PostgreSQL
    participant Redis as Redis
    participant Qdrant as Qdrant

    U->>API: Upload PDF
    API->>DB: Create Document (status: ingesting)
    API->>Q: Dispatch Job
    API-->>U: WebSocket: "Parsing document..."
    
    Q->>Ing: Process PDF (Grobid)
    Ing-->>Q: Return JSON + Shingles
    Q->>DB: Store document text
    Q->>Redis: Store MinHash signatures
    Q->>Qdrant: Store sentence embeddings
    API-->>U: WebSocket: "Checking internal archive..."
    
    Q->>Sim: Run Internal Similarity
    Sim->>Redis: Query LSH Index
    Sim->>Qdrant: Query Vector DB
    Sim-->>DB: Save internal matches
    API-->>U: WebSocket: "Searching the web..."
    
    Q->>Web: Run Web Dragnet (on unmatched chunks)
    Web->>Web: Query Serper.dev
    Web->>Web: Fetch & compare sources
    Web-->>DB: Save web matches
    API-->>U: WebSocket: "Generating report..."
    
    Q->>Rep: Generate Report
    Rep->>DB: Aggregate matches
    Rep->>DB: Calculate scores & heatmap
    Rep->>DB: Save final report
    
    Q-->>U: WebSocket: "Analysis complete!"
```

### 5.2 Faculty Report Interaction

```mermaid
sequenceDiagram
    participant Fac as Faculty
    participant UI as Dashboard
    participant API as Backend API
    participant DB as Database
    participant Gen as PDF Generator

    Fac->>UI: Select Document
    UI->>API: GET /reports/{doc_id}
    API->>DB: Fetch report + matches + sources + heatmap
    DB-->>API: Return JSON
    API-->>UI: Full report data
    UI->>UI: Render Score, Heatmap, Sources, Matches

    Fac->>UI: Click match in findings list
    UI->>UI: Highlight text + show diff + load evidence

    Fac->>UI: Click "Exclude Match"
    UI->>API: PATCH /reports/{id}/matches/{mid}
    API->>DB: Update match (excluded=true)
    API->>API: Recalculate originality score
    API-->>UI: Updated score
    UI->>UI: Re-render score + dim match

    Fac->>UI: Click "Export PDF"
    UI->>API: GET /reports/{id}/export/pdf
    API->>Gen: Generate PDF (cover, charts, matches)
    Gen-->>API: PDF Blob
    API-->>Fac: Download PDF
```

### 5.3 Ingestion Fallback

```mermaid
sequenceDiagram
    participant Q as Task Queue
    participant Grobid as Grobid Parser
    participant Llama as Llama-3-Vision
    participant Norm as Normalizer
    participant Shingler as Shingle Generator

    Q->>Grobid: Parse PDF
    Grobid-->>Q: Return TEI + Confidence Score
    
    alt Confidence < 0.8
        Q->>Llama: OCR Processing Request
        Llama->>Llama: Vision Extraction
        Llama-->>Q: Return Raw Text
        Q->>Norm: Normalize Raw Text
    else Confidence >= 0.8
        Q->>Norm: Normalize TEI Data
    end
    
    Norm-->>Q: Structured JSON
    Q->>Shingler: Generate shingles + embeddings
    Shingler-->>Q: MinHash signatures + vectors
```

---

## 6. Class Diagram

```mermaid
classDiagram
    class DocumentProcessor {
        +process(pdf_file)
        +normalize_output(raw_data)
        +generate_shingles(text)
        -route_to_ocr(low_confidence_doc)
    }

    class SimilarityEngine {
        +generate_minhash(text)
        +query_lsh_index(signature)
        +generate_embeddings(text)
        +search_vectors(vector)
        +paragraph_align(text_a, text_b)
        +batch_compare(doc_list)
    }

    class WebDragnet {
        +isolate_suspicious_chunks(text, internal_matches)
        +search_web(query)
        +fetch_source_content(url)
        +compare_texts(submitted, source)
        +analyze_source_coherence(web_matches)
    }

    class ReportGenerator {
        +aggregate_findings(internal_matches, web_matches)
        +calculate_originality_score(matches, doc_length)
        +generate_heatmap(matches, page_count)
        +build_source_breakdown(matches)
        +build_chart_data(matches)
        +recalculate_after_exclusion(report_id, match_id)
    }

    class PDFExporter {
        +generate_cover_page(report)
        +render_charts(report)
        +render_match_details(matches)
        +export(report) PDF
    }
    
    class Document {
        +UUID id
        +String title
        +List~Page~ pages
        +JSON metadata
        +String course_id
    }
    
    class Report {
        +UUID id
        +Float originality_score
        +String risk_level
        +List~Match~ matches
        +List~Source~ sources
        +List~HeatmapPage~ heatmap
    }

    class Match {
        +UUID id
        +String type
        +String submitted_text
        +String source_text
        +Float similarity_score
        +Boolean is_excluded
    }

    DocumentProcessor -- Document : creates
    SimilarityEngine -- Match : generates
    WebDragnet -- Match : generates
    ReportGenerator -- Report : compiles
    PDFExporter -- Report : exports
    
    SimilarityEngine --|> RedisLSHClient
    SimilarityEngine --|> QdrantClient
    WebDragnet --|> SerperClient
    WebDragnet --|> ContentFetcher
```

---

## 7. Deployment Diagram

```mermaid
graph TD
    subgraph Client_Node ["Client Workstation"]
        Browser[Web Browser]
    end

    subgraph Server_Node ["Institutional Fat Node (Ubuntu 24.04 LTS)"]
        subgraph Docker_Host ["Docker Engine"]
            subgraph Container_Frontend ["frontend-container"]
                Nginx[Nginx / Vite Server]
            end
            
            subgraph Container_Backend ["backend-container"]
                FastAPI[FastAPI Service]
                CeleryWorker[Celery Worker]
            end
            
            subgraph Container_Data ["Data Containers"]
                PG[PostgreSQL]
                RD[Redis]
                QD[Qdrant]
            end
            
            subgraph Container_Processing ["Processing Containers"]
                GrobidService[Grobid Service]
            end
        end
    end
    
    subgraph Cloud ["Internet / External"]
        APIs["Serper.dev"]
    end

    Browser -- HTTPS --> Nginx
    Nginx -- Proxy_Pass --> FastAPI
    
    FastAPI -- TCP --> PG
    FastAPI -- TCP --> RD
    
    CeleryWorker -- TCP --> PG
    CeleryWorker -- TCP --> RD
    CeleryWorker -- TCP --> QD
    CeleryWorker -- HTTP --> GrobidService
    
    CeleryWorker -- HTTPS --> APIs
```

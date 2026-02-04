# Alethian System Diagrams

This document contains the architectural and design diagrams for the Alethian Local-First Research Integrity System, based on the SRS Version 1.0.

## 1. System Architecture Diagram
This diagram illustrates the high-level architecture of Alethian, highlighting the separation between the execution environment (Institutional Server), the client interface, and the transient external API mesh.

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
        
        subgraph Backend_Layer ["Application & logic Layer"]
            API["FastAPI Backend"]
            Celery["Celery Task Queue"]
        end
        
        subgraph Data_Layer ["Data Persistence"]
            Postgres[("PostgreSQL\n(User Data & Reports)")]
            Redis[("Redis\n(Cache & Local Archive/LSH)")]
            Qdrant[("Qdrant\n(Vector Database)")]
        end
        
        subgraph Compute_Layer ["AI & Compute Engines"]
            Grobid["Grobid Service\n(PDF Parsing)"]
            Llama["Local LLM Inference\n(Llama-3-Vision / Falcon-7B)"]
        end
    end

    subgraph External_Cloud ["External API Mesh (Transient)"]
        S2["Semantic Scholar API"]
        Unpaywall["Unpaywall API"]
        Serper["Serper.dev\n(Google Search API)"]
    end

    %% Flows
    Browser <-->|HTTPS/WebSocket| UI
    UI <-->|REST| API
    API <-->|Task Dispatch| Celery
    
    API <-->|SQL| Postgres
    API <-->|Key-Value/LSH| Redis
    
    Celery <-->|Read/Write| Postgres
    Celery <-->|Read/Write| Redis
    Celery <-->|Vector Search| Qdrant
    
    Celery -->|Parse PDF| Grobid
    Celery -->|OCR/Forensics| Llama
    
    Celery <-->|Validate Refs| S2
    Celery <-->|Open Access Check| Unpaywall
    Celery <-->|Web Dragnet| Serper

    classDef specific fill:#f9f,stroke:#333,stroke-width:2px;
    classDef external fill:#eee,stroke:#999,stroke-width:2px,stroke-dasharray: 5 5;
    classDef storage fill:#ff9,stroke:#333,stroke-width:2px;
    
    class S2,Unpaywall,Serper external;
    class Postgres,Redis,Qdrant storage;
    class Grobid,Llama specific;
```

---

## 2. Data Flow Diagrams (DFD)

### 2.1 Level 0 DFD (Context Diagram)
The highest-level view of the system, showing the interaction between the core actors and the Alethian system.

```mermaid
graph LR
    User(Faculty / Reviewer)
    System[Alethian System]
    ExtAPIs[External API Mesh\n(Semantic Scholar, Unpaywall, Serper)]
    LocalDocs[Local Document Archive]

    User -->|Upload PDF| System
    User -->|Request Report| System
    System -->|Validation Report| User
    System -->|Real-time Status| User

    System <-->|Query Citation/Web Data| ExtAPIs
    System <-->|Compare against History| LocalDocs
```

### 2.2 Level 1 DFD (System Overview)
Expands the system process into its major logical pipeline stages.

```mermaid
graph TD
    %% Entities
    User((User))
    DocStore[("Document Store")]
    ExtData[("External Data Sources")]
    Archive[("Local Archive")]

    %% Processes
    P1[1.0 Ingestion Engine]
    P2[2.0 Reference Validation]
    P3[3.0 Internal Similarity]
    P4[4.0 Web Dragnet]
    P5[5.0 AI Forensics]
    P6[6.0 Report Generation]

    %% Data Flows
    User -->|PDF File| P1
    P1 -->|Structured JSON| P2
    P1 -->|Structured JSON| P3
    P1 -->|Structured JSON| P5
    
    P2 <-->|Metadata Query| ExtData
    P2 -->|Citation Analysis| P6
    
    P3 <-->|MinHash/Vectors| Archive
    P3 -->|Internal Matches| P6
    P3 -->|Unmatched Chunks| P4
    
    P4 <-->|Search Query| ExtData
    P4 -->|Web Plagiarism Findings| P6
    
    P5 -->|Perplexity Scores| P6
    
    P6 -->|Final Report| DocStore
    DocStore -->|View Dashboard| User
```

### 2.3 Level 2 DFD: Layer 1 (The Ingestion Engine)
Detailed flow of the PDF processing and structural extraction.

```mermaid
graph TD
    Input[PDF File]
    Grobid[Grobid Parser]
    ConfCheck{Confidence > 0.8?}
    Vision[Llama-3-Vision OCR]
    Norm[Document Normalizer]
    JSON[Normalized JSON Object]

    Input --> Grobid
    Grobid -->|XML/TEI| ConfCheck
    ConfCheck -- Yes --> Norm
    ConfCheck -- No --> Vision
    Vision -->|Raw Text| Norm
    Norm --> JSON
```

### 2.4 Level 2 DFD: Layer 2 (Reference Validation)
The API Mesh workflow for verifying citations.

```mermaid
graph TD
    JSON[Normalized JSON]
    Extractor[Citation Extractor]
    Refs[Extracted References]
    S2[Semantic Scholar API]
    Unpaywall[Unpaywall API]
    
    CheckExist{Found in API?}
    MetaCheck{Is Retracted?}
    ContentCheck{Abstract Match > 0.4?}
    
    FlagHallu[Flag: Potential Hallucination]
    FlagRetract[Flag: Retracted Source]
    FlagMisrep[Flag: Citation Misrepresentation]
    Valid[Mark as Verified]

    JSON --> Extractor
    Extractor --> Refs
    Refs --> S2
    S2 --> CheckExist
    
    CheckExist -- No --> FlagHallu
    CheckExist -- Yes --> MetaCheck
    
    MetaCheck -- Yes --> FlagRetract
    MetaCheck -- No --> Unpaywall
    
    Unpaywall -->|Get Fulltext/Abstract| ContentCheck
    ContentCheck -- No --> FlagMisrep
    ContentCheck -- Yes --> Valid
```

### 2.5 Level 2 DFD: Layer 3 (Internal Similarity)
Local plagiarism detection against institutional archives.

```mermaid
graph TD
    Text[Body Text Input]
    MinHash[MinHash Generator]
    Redis[Redis LSH Index]
    LSHMatch{LSH Match?}
    
    VecEmbed[Qdrant Embedder]
    VecDB[Qdrant Vector DB]
    SemMatch{Vector Similarity > 0.85?}
    
    FlagExact[Flag: Exact Copy]
    FlagPara[Flag: Paraphrased Copy]
    Safe[Safe / Novel Content]

    Text --> MinHash
    MinHash --> Redis
    Redis --> LSHMatch
    
    LSHMatch -- Yes --> FlagExact
    LSHMatch -- No --> VecEmbed
    
    VecEmbed --> VecDB
    VecDB --> SemMatch
    
    SemMatch -- Yes --> FlagPara
    SemMatch -- No --> Safe
```

### 2.6 Level 2 DFD: Layer 4 (Web Dragnet)
Targeted web search for systematic plagiarism.

```mermaid
graph TD
    SafeText[Text (Passed Layer 3)]
    Chunker[Suspicious Chunker]
    Serper[Serper.dev API]
    Results[Search Results]
    Coherence[Source Coherence Analyzer]
    
    Threshold{>3 Chunks from Same Domain?}
    FlagWeb[Flag: Systematic Web Plagiarism]
    Clean[No Action]

    SafeText --> Chunker
    Chunker -->|Low Perplexity Chunks| Serper
    Serper --> Results
    Results --> Coherence
    Coherence --> Threshold
    
    Threshold -- Yes --> FlagWeb
    Threshold -- No --> Clean
```

### 2.7 Level 2 DFD: Layer 5 (AI Forensics)
Statistical analysis for AI-generated text detection.

```mermaid
graph TD
    Text[Body Text]
    Tokenizer[Tokenizer]
    Llama[Llama-3 (Observer)]
    Falcon[Falcon-7B (Performer)]
    
    Metric[Calculate Binoculars Metric]
    Stats[Calculate Burstiness & Perplexity]
    
    Viz[Generate Plots]
    Report[Forensic Layer Report]

    Text --> Tokenizer
    Tokenizer --> Llama
    Tokenizer --> Falcon
    
    Llama --> Metric
    Falcon --> Metric
    
    Metric --> Viz
    Text --> Stats
    Stats --> Viz
    Viz --> Report
```

---

## 3. Entity-Relationship Diagram (ERD)
This diagram models the data entities stored in PostgreSQL and their diverse relationships.

```mermaid
erDiagram
    Users ||--o{ Documents : uploads
    Documents ||--|| Reports : generates
    Reports ||--o{ Citations : contains
    Reports ||--o{ Segments : "flags segments"
    
    Citations }|--|| ReferenceSources : "matches external"
    Segments }|--|| WebMatches : "found in"
    
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
        timestamp uploaded_at
        uuid uploader_id FK
    }

    Reports {
        uuid id PK
        uuid document_id FK
        float total_score
        string status "Pending|Complete"
        jsonb metadata "Authors/Abstract"
    }

    Citations {
        uuid id PK
        uuid report_id FK
        string raw_text
        string status "Verified|Hallucinated|Retracted"
        float coherence_score
    }
    
    ReferenceSources {
        string doi PK
        string title
        string venue
        boolean is_retracted
    }

    Segments {
        uuid id PK
        uuid report_id FK
        int page_num
        string text_content
        string type "Similarity|AI_Forensic"
        float anomaly_score
    }

    WebMatches {
        uuid id PK
        uuid segment_id FK
        string url
        string domain
        float search_score
    }
```

---

## 4. Use Case Diagrams
Visualizes the functional interactions of different user actors with the system.

```mermaid
graph LR
    subgraph "Alethian System"
        direction TB
        UC1(Upload PDF Thesis)
        UC2(View Analysis Report)
        UC3(Export Signed PDF)
        UC4(Toggle Diff View)
        UC5(Configure API Keys)
        UC6(Adjust Thresholds)
        UC7(Manage User Roles)
    end

    Faculty((Faculty / Reviewer))
    Admin((Administrator))

    Faculty --> UC1
    Faculty --> UC2
    Faculty --> UC3
    Faculty --> UC4
    
    Admin --> UC5
    Admin --> UC6
    Admin --> UC7
    Admin --> UC2
```

---

## 5. Sequence Diagrams

### 5.1 Scenario 1: Full Submission Pipeline
The orchestration of the multi-stage analysis pipeline upon document submission.

```mermaid
sequenceDiagram
    participant U as User
    participant API as Backend API
    participant Q as Task Queue
    participant Ing as 1. Ingestion
    participant Ref as 2. Ref Validation
    participant Sim as 3. Sim Engine
    participant Web as 4. Web Dragnet
    participant AI as 5. AI Forensics
    participant DB as Postgres

    U->>API: Upload PDF
    API->>DB: Create Document Record (Pending)
    API->>Q: Dispatch Job
    Q->>Ing: Process PDF
    Ing-->>Q: Return JSON Structure
    
    par Parallel Execution
        Q->>Ref: Validate Citations
        Ref->>Ref: Check S2/Unpaywall
        Ref-->>DB: Save Citation Flags
        
        Q->>Sim: Check Internal Sim
        Sim->>Sim: MinHash & Vector Search
        Sim-->>DB: Save Similarity Segments
        
        Q->>AI: Analyze Forensics
        AI->>AI: Llama/Falcon Binoculars
        AI-->>DB: Save Forensice Scores
    end
    
    Q->>Web: Run Web Dragnet (on filtered chunks)
    Web-->>DB: Save Web Matches
    
    Q->>DB: Mark Report as Complete
    Q-->>U: Notify Completion (WebSocket)
```

### 5.2 Scenario 2: Faculty Report Review & Export
The workflow for a reviewer analyzing a report and generating a visual summary.

```mermaid
sequenceDiagram
    participant Fac as Faculty
    participant UI as Dashboard
    participant API as Backend API
    participant DB as Database
    participant Gen as PDF Generator

    Fac->>UI: Select Document
    UI->>API: Get Report Data
    API->>DB: Fetch Flags & Segments
    DB-->>API: Return JSON
    API-->>UI: Render Dashboard

    Fac->>UI: Click "Red Flag"
    UI->>UI: Show Diff vs Source
    Fac->>UI: Verify Finding

    Fac->>UI: Click "Export PDF"
    UI->>API: Request Signed PDF
    API->>Gen: Generate Summary
    Gen-->>API: Return PDF Blob
    API-->>Fac: Download PDF
```

### 5.3 Scenario 3: Ingestion Fallback Handling
The fallback mechanism when Grobid fails to parse a scanned document.

```mermaid
sequenceDiagram
    participant Q as Task Queue
    participant Grobid as Grobid Parser
    participant Llama as Llama-3-Vision
    participant Norm as Normalizer

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
    
    Norm-->>Q: Return Final JSON
```

### 5.4 Scenario 4: Admin Configuration
Administrative updates to system configuration.

```mermaid
sequenceDiagram
    participant Admin
    participant API
    participant Vault as Key Manager
    participant DB

    Admin->>API: Update Serper API Key
    API->>Vault: Validate & Encrypt Key
    Vault-->>API: Success
    
    Admin->>API: Set Similarity Threshold (0.8 -> 0.9)
    API->>DB: Update Config Table
    DB-->>API: Confirmed
    API-->>Admin: "Settings Updated"
```

---

## 6. Class Diagrams
The static structure of the system's core components and logic classes.

```mermaid
classDiagram
    class DocumentProcessor {
        +process(pdf_file)
        +normalize_output(raw_data)
        -route_to_ocr(low_confidence_doc)
    }

    class CitationValidator {
        +extract_citations(text)
        +validate_existence(citation)
        +check_retraction(doi)
        +verify_content_match(abstract, context)
        -query_semantic_scholar()
    }

    class SimilarityEngine {
        +generate_minhash(text)
        +query_lsh_index(signature)
        +generate_embeddings(text)
        +search_vectors(vector)
    }

    class WebDragnet {
        +isolate_suspicious_chunks(text)
        +search_web(query)
        +analyze_source_coherence(urls)
    }

    class ForensicAnalyzer {
        +calculate_binoculars(text)
        +compute_burstiness(text)
        +detect_style_anomalies(text)
    }

    class ReportGenerator {
        +aggregate_findings(flags)
        +calculate_total_score()
        +generate_pdf_summary()
    }
    
    class Document {
        +UUID id
        +String title
        +List~Page~ pages
        +JSON metadata
    }
    
    class Citation {
        +String raw_text
        +String doi
        +Boolean is_hallucinated
        +Boolean is_retracted
    }

    DocumentProcessor -- Document : creates
    CitationValidator -- Citation : validates
    ReportGenerator -- Document : summarizes
    
    DocumentProcessor ..> IngestionEngine
    CitationValidator --|> APIMeshClient
    SimilarityEngine --|> LocalArchive
    WebDragnet --|> SerperClient
    ForensicAnalyzer --|> LocalLLMClient
```

---

## 7. Deployment Diagram
Illustrates the physical deployment view, emphasizing the containerized services orchestrated via Docker Compose on the institutional server.

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
            
            subgraph Container_AI ["AI Containers"]
                GrobidService[Grobid Service]
                LLMService[vLLM Inference Server]
            end
        end
    end
    
    subgraph Cloud ["Internet / External"]
        APIs[Semantic Scholar / Serper / Unpaywall]
    end

    Browser -- HTTPS --> Nginx
    Nginx -- Proxy_Pass --> FastAPI
    
    FastAPI -- TCP --> PG
    FastAPI -- TCP --> RD
    
    CeleryWorker -- TCP --> QD
    CeleryWorker -- HTTP --> GrobidService
    CeleryWorker -- HTTP --> LLMService
    
    CeleryWorker -- HTTPS --> APIs
```

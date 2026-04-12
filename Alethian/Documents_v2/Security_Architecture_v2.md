# Alethian Security Architecture v2.0

## 1. Core Security Philosophy: Local Sovereignty
Alethian is designed as a **Local-First** system. The primary security objective is to ensure that sensitive institutional data (student theses, research papers) never leaves the university's controlled infrastructure.

### 1.1 Data Residency
- **Student Data:** Full text of submitted documents is stored **only** on local storage and the local PostgreSQL database.
- **Vector Embeddings:** Generated locally using `sentence-transformers` and stored in a local Qdrant instance.
- **MinHash Signatures:** Stored in local Redis instance.
- **Transmission:** No full-text data is ever transmitted to external APIs.

---

## 2. Authentication & Authorization

### 2.1 Identity Management
- **Token-Based Auth:** Uses **JWT (JSON Web Tokens)** for stateless authentication.
- **Algorithm:** HS256 (HMAC with SHA-256).
- **Expiration:** Short-lived access tokens (15–60 min) with refresh token rotation.

### 2.2 Role-Based Access Control (RBAC)
| Role | Permissions |
|---|---|
| **Faculty** | Upload documents, view reports, exclude matches, annotate findings, mark as reviewed, export reports |
| **Administrator** | All Faculty permissions + manage configuration, API keys, user roles, thresholds |
| **System Service** | Internal background workers (Celery) with isolated service privileges |

---

## 3. External Service Interactions
Alethian v2 interacts with only **one** external API: **Serper.dev** for web plagiarism detection. All interactions are strictly **Metadata-Only**.

### 3.1 Privacy-Preserving Queries
- **Serper.dev (Google Search):**
    - **Input:** Shingled text chunks (≈50 words) identified as "suspicious" by internal heuristics.
    - **Risk Mitigation:**
        - Only text segments that were not matched internally are queried.
        - Queries are randomized and throttled to prevent timing attacks.
        - No Personally Identifiable Information (PII) is included.
        - Results are cached to minimize repeat queries.
    - **Maximum exposure:** ≈20 shingles × 50 words = ≈1,000 words per document (out of tens of thousands).

### 3.2 Data Flow Classification
| Data | Location | Transmitted Externally? |
|---|---|---|
| Full document text | Local PostgreSQL | **Never** |
| Vector embeddings | Local Qdrant | **Never** |
| MinHash signatures | Local Redis | **Never** |
| Plagiarism matches | Local PostgreSQL | **Never** |
| Short text shingles | Serper API | **Yes** (transient, ≈50 words each) |

---

## 4. Infrastructure Security

### 4.1 Container Isolation
- **Docker Network:** Backend, Database, and Cache services communicate over an internal Docker bridge network (`alethian-net`). Only Nginx ingress and necessary ports are exposed to the host.
- **Least Privilege:** Containers run with non-root users where possible.

### 4.2 Secrets Management
- **Environment Variables:** All sensitive keys (Serper API token, DB passwords, JWT secret) are injected via `.env` file at runtime.
- **Exclusion:** `.env` is strictly `.gitignore`'d to prevent accidental leakage.

### 4.3 Input Validation
- **File Uploads:** Strict MIME type validation (PDF only) and filename sanitization to prevent path traversal.
- **Grobid XML:** XML parsing hardened against XXE (XML External Entity) attacks.
- **API Input:** All Pydantic models enforce strict type validation and size limits.

### 4.4 Archive Security
- **Access Control:** Only authorized Celery workers and the reporting API can read from the document archive.
- **Encryption at Rest:** PostgreSQL and Qdrant data directories should use disk-level encryption (LUKS/dm-crypt).

---

## 5. Report Security

### 5.1 Digital Signatures
- Faculty reviews include a digital signature (hashed faculty ID + timestamp) to prevent tampering with the reviewed status.
- Exported PDF reports include an embedded hash for integrity verification.

### 5.2 Access Control
- Reports are only accessible to the uploader and administrators.
- Report export generates a one-time download token valid for 5 minutes.

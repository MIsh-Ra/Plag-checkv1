# Alethian Security Architecture

## 1. Core Security Philosophy: Local Sovereignty
Alethian is designed as a **Local-First** system. The primary security objective is to ensure that sensitive institutional data (student theses, research papers) never leaves the university's controlled infrastructure.

### 1.1 Data Residency
- **Student Data:** Full text of submitted documents is stored **only** on local storage (MinIO/Local Filesystem) and the local PostgreSQL database.
- **Vector Embeddings:** Generated locally using on-premise models and stored in a local Qdrant instance.
- **Transmission:** No full-text data is ever transmitted to external APIs.

---

## 2. Authentication & Authorization

### 2.1 Identity Management
- **Token-Based Auth:** Uses **JWT (JSON Web Tokens)** for stateless authentication.
- **Algorithm:** HS256 (HMAC with SHA-256).
- **Expiration:** Short-lived access tokens (15-60 min) with refresh token rotation.

### 2.2 Role-Based Access Control (RBAC)
- **Faculty:** Can upload documents, view reports, and verify citations.
- **Administrator:** Can manage system configuration, API keys, and user roles.
- **System Service:** Internal background workers (Celery) operate with isolated service privileges.

---

## 3. External Service Interactions
Alethian interacts with external APIs (Semantic Scholar, Serper, Unpaywall) to validate claims. These interactions are strictly **Metadata-Only**.

### 3.1 Privacy-Preserving Queries
- **Semantic Scholar / Unpaywall:**
    - **Input:** Citation strings (e.g., "Smith et al., 2020") or DOIs.
    - **Output:** Publication metadata (Title, Authors, Venue, Retraction Status).
    - **Risk:** Minimal. Only the *references* cited by the student are exposed, not the student's original work.
- **Serper.dev (Google Search):**
    - **Input:** Shingled text chunks (3-5 sentences) identified as "suspicious" by internal heuristics.
    - **Risk Mitigation:**
        - Only text segments with high burstiness/low perplexity are queried.
        - Randomization of query timing to prevent timing attacks.
        - No Personally Identifiable Information (PII) is included in queries.

---

## 4. Infrastructure Security

### 4.1 Container Isolation
- **Docker Network:** Backend, Database, and Cache services communicate over an internal Docker bridge network (`alethian-net`). Only the Nginx ingress and necessary API ports are exposed to the host.
- **Least Privilege:** Containers run with non-root users where possible.

### 4.2 Secrets Management
- **Environment Variables:** All sensitive keys (API tokens, Database passwords, JWT secret) are injected via `.env` file at runtime.
- **Exclusion:** `.env` is strictly `.gitignore`'d to prevent accidental leakage.

### 4.3 Input Validation
- **File Uploads:** Strict checking of file MIME types (PDF only) and sanitization of filenames to prevent path traversal attacks.
- **Grobid XML:** XML parsing is hardened to prevent XXE (XML External Entity) attacks.

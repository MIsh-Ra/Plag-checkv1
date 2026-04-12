# Alethian API Specification v2.0

## Base URL
`http://localhost:8000/api/v1`

## Authentication

### Login
**POST** `/auth/login`
- **Request Body:**
  ```json
  {
    "username": "faculty@university.edu",
    "password": "securepassword"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "access_token": "ey...",
    "token_type": "bearer",
    "role": "faculty",
    "user_id": "uuid-..."
  }
  ```

---

## Documents

### Upload Document
**POST** `/documents/upload`
- **Content-Type:** `multipart/form-data`
- **Form Data:**
  - `file`: (Binary PDF, max 100MB)
  - `course_id`: (Optional string — for batch/cohort comparison)
- **Response (201 Created):**
  ```json
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "filename": "thesis_v1.pdf",
    "status": "ingesting",
    "created_at": "2026-04-09T10:00:00Z"
  }
  ```

### List Documents
**GET** `/documents`
- **Query Params:**
  - `limit`: int (default 20)
  - `offset`: int (default 0)
  - `status`: string filter (`ingesting`, `analyzing`, `complete`, `error`)
  - `course_id`: string filter
- **Response (200 OK):**
  ```json
  {
    "total": 45,
    "items": [
      {
        "id": "...",
        "title": "Analysis of Deep Learning...",
        "author": "J. Doe",
        "status": "complete",
        "originality_score": 85.5,
        "risk_level": "moderate",
        "uploaded_at": "2026-04-01T10:00:00Z",
        "page_count": 48
      }
    ]
  }
  ```

### Get Document Details
**GET** `/documents/{id}`
- **Response (200 OK):**
  ```json
  {
    "id": "...",
    "title": "Analysis of...",
    "author": "J. Doe",
    "filename": "thesis_v1.pdf",
    "page_count": 48,
    "status": "complete",
    "uploaded_at": "2026-04-01T10:00:00Z",
    "metadata": {
      "abstract": "...",
      "sections": ["Introduction", "Methods", "..."]
    }
  }
  ```

### Get Document Processing Status (WebSocket)
**WS** `/documents/{id}/status`
- **Server Push Events:**
  ```json
  {
    "stage": "internal_similarity",
    "progress": 65,
    "message": "Checking internal archive... 65%",
    "timestamp": "2026-04-01T10:01:30Z"
  }
  ```

---

## Reports

### Get Full Report
**GET** `/reports/{document_id}`
- **Response (200 OK):**
  ```json
  {
    "document_id": "...",
    "originality_score": 85.5,
    "risk_level": "moderate",
    "status": "complete",
    "summary": {
      "total_matches": 12,
      "internal_exact_matches": 3,
      "internal_paraphrase_matches": 4,
      "web_matches": 5,
      "unique_sources": 6,
      "avg_match_length_words": 45,
      "longest_match_words": 120,
      "pages_with_matches": [2, 5, 12, 13, 14, 28]
    },
    "sources": [
      {
        "id": "src-1",
        "type": "internal",
        "name": "Thesis_2024_KWest.pdf",
        "document_id": "...",
        "coverage_percent": 4.2,
        "match_count": 3
      },
      {
        "id": "src-2",
        "type": "web",
        "name": "medium.com",
        "url": "https://medium.com/...",
        "domain": "medium.com",
        "coverage_percent": 2.1,
        "match_count": 2
      }
    ],
    "matches": [
      {
        "id": "match-1",
        "type": "internal_exact",
        "submitted_text": "The data clearly shows a linear trend...",
        "submitted_page": 12,
        "submitted_start_char": 1450,
        "submitted_end_char": 1580,
        "source_id": "src-1",
        "source_text": "The data clearly shows a linear trend...",
        "source_page": 8,
        "similarity_score": 0.95,
        "is_excluded": false,
        "faculty_comment": null
      }
    ],
    "heatmap": [
      {
        "page": 1,
        "match_density": 0.0,
        "color": "#22c55e"
      },
      {
        "page": 2,
        "match_density": 0.35,
        "color": "#f97316"
      }
    ],
    "page_match_distribution": [
      {"page": 1, "internal_exact": 0, "internal_paraphrase": 0, "web": 0},
      {"page": 2, "internal_exact": 1, "internal_paraphrase": 0, "web": 1}
    ]
  }
  ```

### Get Report Heatmap Data
**GET** `/reports/{document_id}/heatmap`
- **Response (200 OK):**
  ```json
  [
    {"page": 1, "density": 0.0, "dominant_type": null},
    {"page": 2, "density": 0.35, "dominant_type": "internal_exact"},
    {"page": 3, "density": 0.12, "dominant_type": "web"}
  ]
  ```

### Exclude/Restore a Match
**PATCH** `/reports/{document_id}/matches/{match_id}`
- **Request Body:**
  ```json
  {
    "is_excluded": true,
    "reason": "Properly cited quotation"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "match_id": "match-1",
    "is_excluded": true,
    "updated_originality_score": 87.3
  }
  ```

### Add Faculty Comment to Match
**POST** `/reports/{document_id}/matches/{match_id}/comment`
- **Request Body:**
  ```json
  {
    "comment": "Student confirmed this was a shared methodology section."
  }
  ```
- **Response (201 Created):** `{"message": "Comment added"}`

### Mark Report as Reviewed
**POST** `/reports/{document_id}/review`
- **Request Body:**
  ```json
  {
    "verdict": "reviewed",
    "faculty_notes": "Minor similarity in methodology section, acceptable.",
    "digital_signature": "base64-encoded-sig"
  }
  ```
- **Response (200 OK):** `{"message": "Report marked as reviewed"}`

### Export Report as PDF
**GET** `/reports/{document_id}/export/pdf`
- **Query Params:**
  - `include_excluded`: bool (default false)
  - `branding`: string (`default`, `minimal`)
- **Response (200 OK):** `application/pdf` (Binary download)

### Export Report as JSON
**GET** `/reports/{document_id}/export/json`
- **Response (200 OK):** Full JSON report body (same structure as Get Full Report)

---

## Administrative

### Get Configuration
**GET** `/admin/config`
- **Requires:** Admin Role
- **Response (200 OK):**
  ```json
  {
    "similarity_thresholds": {
      "minhash_jaccard": 0.5,
      "semantic_cosine": 0.85,
      "web_match": 0.7
    },
    "web_dragnet": {
      "enabled": true,
      "queries_per_document": 20,
      "rate_limit_rpm": 60
    },
    "api_status": {
      "serper": "ok"
    },
    "archive_stats": {
      "total_documents": 1250,
      "total_shingles": 450000,
      "last_indexed": "2026-04-08T22:00:00Z"
    }
  }
  ```

### Update Configuration
**PATCH** `/admin/config`
- **Requires:** Admin Role
- **Request Body:**
  ```json
  {
    "serper_api_key": "new_key_...",
    "similarity_thresholds": {
      "semantic_cosine": 0.9
    }
  }
  ```
- **Response (200 OK):** `{"message": "Configuration updated"}`

---

## 5. External Service Interface (Backend → Serper)

### Serper.dev (Google Search Dragnet)
- **Primary Use:** Detecting plagiarism from the open web.
- **Endpoint Used:** `POST https://google.serper.dev/search`
- **Payload:**
  ```json
  {
    "q": "\"suspicious text shingle approximately fifty words\"",
    "num": 5
  }
  ```
- **Data Transmitted:** Short, randomized text shingles (≈50 words). **No student PII.**
- **Constraints:**
  - Maximum 20 queries per document (configurable).
  - Rate limiting: 60 requests/minute (configurable).
  - Results cached in Redis to avoid redundant queries.

---

## Error Responses

All endpoints follow a consistent error format:
```json
{
  "detail": "Human-readable error message",
  "error_code": "MACHINE_READABLE_CODE",
  "timestamp": "2026-04-09T10:00:00Z"
}
```

| HTTP Code | Scenario |
|---|---|
| 400 | Invalid request (bad file type, missing fields) |
| 401 | Authentication failure |
| 403 | Insufficient permissions (e.g., faculty accessing admin) |
| 404 | Document/Report not found |
| 413 | File too large (>100MB) |
| 429 | Rate limit exceeded |
| 503 | External service unavailable (Serper down) |

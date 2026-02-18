# Alethian API Specification v1.0

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
    "role": "faculty"
  }
  ```

---

## Documents (Theses)

### Upload Document
**POST** `/documents/upload`
- **Content-Type:** `multipart/form-data`
- **Form Data:**
  - `file`: (Binary PDF)
- **Response (201 Created):**
  ```json
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "filename": "thesis_v1.pdf",
    "status": "pending"
  }
  ```

### List Documents
**GET** `/documents`
- **Query Params:**
  - `limit`: int (default 10)
  - `offset`: int (default 0)
- **Response (200 OK):**
  ```json
  [
    {
      "id": "...",
      "title": "Analysis of...",
      "author": "J. Doe",
      "status": "complete",
      "score": 85.5,
      "uploaded_at": "2026-02-05T10:00:00Z"
    }
  ]
  ```

### Get Document Details
**GET** `/documents/{id}`
- **Response (200 OK):** (Document metadata and overall status)

---

## Reports (Analysis Results)

### Get Full Report
**GET** `/reports/{document_id}`
- **Response (200 OK):**
  ```json
  {
    "document_id": "...",
    "total_score": 85.5,
    "citations": [
      {
        "id": 1,
        "text": "Smith 2029",
        "status": "hallucinated",
        "page": 12
      }
    ],
    "segments": [
      {
        "type": "internal_similarity",
        "score": 0.92,
        "source": "Local Archive: Thesis_2021",
        "text_content": "..."
      }
    ]
  }
  ```

### Export PDF Summary
**GET** `/reports/{document_id}/export`
- **Response (200 OK):** `application/pdf` (Binary download)

---

## Administrative

### Get Configuration
**GET** `/admin/config`
- **Requires:** Admin Role
- **Response (200 OK):**
  ```json
  {
    "threshold_similarity": 0.8,
    "api_status": {
      "semantic_scholar": "ok",
      "serper": "error_quota"
    }
  }
  ```

### Update Configuration (API Keys)
**PATCH** `/admin/config`
- **Requires:** Admin Role
- **Request Body:**
  ```json
  {
    "serper_api_key": "new_key_...",
    "threshold_similarity": 0.9
  }
  ```
- **Response (200 OK):** `{"message": "Configuration updated"}`

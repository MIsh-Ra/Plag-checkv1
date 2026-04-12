# API Reference

Complete REST API reference for Alethian V2. Base URL: `http://localhost:8000/api/v1`

---

## Authentication

All protected endpoints require a JWT token in the `Authorization` header:

```
Authorization: Bearer <token>
```

### POST `/auth/login`

Authenticate and receive a JWT token.

**Request Body:**
```json
{
  "username": "faculty@university.edu",
  "password": "your_password"
}
```

**Response `200`:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "role": "faculty",
  "user_id": "uuid-string"
}
```

**Errors:**
| Status | Detail |
|:-------|:-------|
| 401 | Incorrect username or password |

---

## Documents

### POST `/documents/upload`

Upload a PDF document for analysis. Rate limited to 10 requests/minute.

**Auth:** Faculty

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|:------|:-----|:---------|:------------|
| `file` | File | Yes | PDF file (max 100MB) |
| `course_id` | string | No | Course identifier for filtering |

**Response `200`:**
```json
{
  "id": "uuid-string",
  "title": "Unknown Title",
  "author": "Unknown",
  "filename": "thesis.pdf",
  "status": "pending",
  "upload_date": "2026-04-09T12:00:00Z",
  "course_id": "CSE101",
  "user_id": "uuid-string"
}
```

**Errors:**
| Status | Detail |
|:-------|:-------|
| 400 | Only PDF files are allowed |
| 413 | File too large |
| 403 | Not authenticated |

---

### GET `/documents`

List the authenticated user's documents. Paginated and filterable.

**Auth:** Faculty

**Query Parameters:**

| Param | Type | Default | Description |
|:------|:-----|:--------|:------------|
| `limit` | int | 20 | Results per page |
| `offset` | int | 0 | Pagination offset |
| `status` | string | — | Filter by status |
| `course_id` | string | — | Filter by course |

**Response `200`:**
```json
{
  "total": 42,
  "items": [
    {
      "id": "uuid",
      "title": "Data Mining Approaches",
      "filename": "thesis.pdf",
      "status": "complete",
      "upload_date": "2026-04-09T12:00:00Z",
      "originality_score": 78.5,
      "risk_level": "moderate",
      "course_id": "CSE101"
    }
  ]
}
```

---

### GET `/documents/{id}`

Get a single document's details.

**Auth:** Faculty (owner only)

**Response `200`:** Same schema as list item, with full detail.

**Errors:**
| Status | Detail |
|:-------|:-------|
| 404 | Document not found |

---

### WebSocket `/documents/{document_id}/status`

Real-time processing progress updates via WebSocket.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/documents/{document_id}/status');
```

**Messages received (JSON):**
```json
{ "stage": "ingesting",           "progress": 10,  "message": "Parsing PDF with Grobid..." }
{ "stage": "internal_similarity", "progress": 40,  "message": "Comparing against internal archive..." }
{ "stage": "web_dragnet",         "progress": 60,  "message": "Searching web sources..." }
{ "stage": "report_generation",   "progress": 85,  "message": "Generating originality report..." }
{ "stage": "complete",            "progress": 100, "message": "Analysis complete." }
```

Connection closes automatically after `"complete"` stage.

---

## Reports

### GET `/reports/{document_id}`

Get the full originality report for a document.

**Auth:** Faculty (owner only)

**Response `200` — `FullReportResponse`:**
```json
{
  "document_id": "uuid",
  "document_title": "Data Mining Approaches",
  "document_author": "Khandelwal, A.",
  "page_count": 15,
  "analyzed_at": "2026-04-09T12:30:00Z",
  "processing_time_seconds": 45,
  "scores": {
    "originality_score": 78.5,
    "similarity_score": 21.5,
    "risk_level": "moderate",
    "internal_contribution": 0.0,
    "web_contribution": 0.0
  },
  "summary_stats": {
    "total_matches": 12,
    "internal_exact": 3,
    "internal_paraphrase": 5,
    "web_matches": 4,
    "unique_sources": 8,
    "avg_match_length_words": 25.3,
    "longest_match_words": 85,
    "pages_with_matches": 7,
    "total_pages": 15,
    "excluded_matches": 0
  },
  "source_breakdown": [
    { "name": "example.com", "value": 50 },
    { "name": "Archive", "value": 30 }
  ],
  "sources": [ { "id": "uuid", "type": "internal", "title": "...", "domain": "..." } ],
  "matches": [
    {
      "id": "uuid",
      "report_id": "uuid",
      "type": "internal_exact",
      "submitted_text": "matched text from submission",
      "source_text": "matching text from source",
      "similarity": 95.0,
      "is_excluded": false,
      "submitted_page": 3,
      "source_page": 1,
      "match_length_words": 28,
      "source": { "id": "uuid", "type": "internal", "title": "..." }
    }
  ],
  "heatmap": [
    {
      "id": "uuid",
      "page_number": 1,
      "density_score": 0.15,
      "internal_density": 0.15,
      "web_density": 0.0,
      "color": "#eab308",
      "match_count": 2,
      "dominant_type": "internal"
    }
  ],
  "page_distribution": [ ... ],
  "review": {
    "status": "unreviewed",
    "reviewed_by": null,
    "reviewed_at": null,
    "faculty_notes": null,
    "verdict": null
  }
}
```

---

### GET `/reports/{document_id}/heatmap`

Page-level density heatmap data.

**Auth:** Faculty (owner only)

**Response `200`:** Array of `HeatmapPageResponse` objects.

---

### PATCH `/reports/{document_id}/matches/{match_id}`

Exclude or include a match. Triggers originality score recalculation.

**Auth:** Faculty (owner only)

**Request Body:**
```json
{
  "is_excluded": true,
  "reason": "properly cited"
}
```

**Response `200`:**
```json
{
  "status": "success",
  "is_excluded": true,
  "updated_originality_score": 85.3
}
```

---

### POST `/reports/{document_id}/matches/{match_id}/comment`

Add a faculty comment to a match.

**Auth:** Faculty (owner only)

**Request Body:**
```json
{
  "comment": "This is a valid citation, not plagiarism."
}
```

**Response `200`:**
```json
{
  "status": "success",
  "comment": "This is a valid citation, not plagiarism."
}
```

---

### POST `/reports/{document_id}/review`

Submit a faculty review verdict for the document.

**Auth:** Faculty (owner only)

**Request Body:**
```json
{
  "verdict": "cleared",
  "faculty_notes": "All matches are properly cited.",
  "digital_signature": "sig-abc123"
}
```

**Response `200`:**
```json
{
  "status": "success",
  "message": "Document marked as reviewed"
}
```

---

### GET `/reports/{document_id}/export/pdf`

Download the report as a PDF file.

**Auth:** Faculty (owner only)

**Query Parameters:**

| Param | Type | Default | Description |
|:------|:-----|:--------|:------------|
| `include_excluded` | bool | false | Include excluded matches |
| `branding` | string | "default" | PDF branding template |

**Response:** `application/pdf` binary stream

---

### GET `/reports/{document_id}/export/json`

Download the full report data as JSON.

**Auth:** Faculty (owner only)

**Response `200`:** Same as `GET /reports/{document_id}`

---

## Admin

### GET `/admin/config`

Get current system configuration.

**Auth:** Admin only

**Response `200`:**
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
    "total_documents": 563,
    "total_shingles": 70375,
    "last_indexed": "Recently"
  }
}
```

---

### PATCH `/admin/config`

Update similarity thresholds.

**Auth:** Admin only

**Request Body:**
```json
{
  "similarity_thresholds": {
    "semantic_cosine": 0.90,
    "minhash_jaccard": 0.55,
    "web_match": 0.75
  }
}
```

**Response `200`:**
```json
{
  "message": "Configuration updated"
}
```

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Human-readable error message"
}
```

| Status | Meaning |
|:-------|:--------|
| 400 | Bad request (invalid input) |
| 401 | Authentication failed |
| 403 | Insufficient permissions |
| 404 | Resource not found |
| 413 | Payload too large |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

---

## Rate Limits

| Endpoint | Limit |
|:---------|:------|
| `POST /documents/upload` | 10/minute per IP |
| `POST /documents/batch` | 5/minute per IP |
| All other endpoints | No limit |

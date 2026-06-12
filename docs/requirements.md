# Requirements

## Project Overview

A REST API service that accepts document uploads, stores document metadata, processes document content, and exposes processing results through APIs.

The goal is to simulate a real-world data ingestion and processing platform using production-minded engineering practices while remaining practical enough to implement within a 3-hour coding exercise.

---

## Business Requirements

Users need a system where they can:

1. Upload text documents.
2. Track document processing progress.
3. Retrieve processing results.
4. Browse previously uploaded documents.
5. Query system health.

The system should be designed to support future processing workloads such as OCR, AI summarization, image analysis, video transcoding, and ML inference.

---

## Functional Requirements

### FR1 — Upload Document

Users can upload a text document.

- Supported file types: `.txt`
- Each upload creates a new document record

**API:** `POST /documents`

**Response:**
```json
{
  "document_id": "uuid",
  "status": "pending"
}
```

---

### FR2 — Store Document Metadata

For every uploaded document, store:

| Field | Type | Description |
|-------|------|-------------|
| document_id | UUID string | Unique identifier |
| filename | string | Original filename |
| file_size | integer | Size in bytes |
| content_type | string | MIME type |
| status | string | Current processing state |
| created_at | datetime | Upload timestamp |
| updated_at | datetime | Last state change timestamp |

---

### FR3 — Process Document

The system processes uploaded documents and generates analysis results.

Processing includes:

- Word count
- Line count
- Top keywords
- Summary placeholder

**Example result:**
```json
{
  "word_count": 1200,
  "line_count": 87,
  "keywords": ["python", "api", "database"],
  "summary": "placeholder"
}
```

---

### FR4 — Retrieve Document Metadata

**API:** `GET /documents/{id}`

Returns document metadata and current status.

---

### FR5 — List Documents

**API:** `GET /documents`

Supports:
- Pagination via `page` and `page_size` query params
- Optional filtering via `status` query param

**Examples:**
```
GET /documents?page=1&page_size=20
GET /documents?status=completed
```

---

### FR6 — Retrieve Processing Status

**API:** `GET /documents/{id}/status`

**Response:**
```json
{
  "status": "completed"
}
```

**Possible states:**

| State | Meaning |
|-------|---------|
| pending | Uploaded, not yet processed |
| processing | Processing in progress |
| completed | Processing finished successfully |
| failed | Processing encountered an error |

---

### FR7 — Retrieve Processing Results

**API:** `GET /documents/{id}/result`

Returns the processing output for a completed document.

---

### FR8 — Health Check

**API:** `GET /health`

**Response:**
```json
{
  "status": "healthy"
}
```

---

## Non-Functional Requirements

### Reliability

- Validate all inputs at the API boundary
- Return proper HTTP status codes
- Handle invalid requests gracefully
- Provide meaningful error messages

Key error codes:

| Code | Condition |
|------|-----------|
| 400 | Invalid file type or malformed request |
| 404 | Document not found |
| 409 | Result requested before processing is complete |
| 413 | File exceeds size limit |

### Maintainability

Clear separation of concerns across four layers:

- **API Layer** — route handlers, request/response serialization
- **Service Layer** — business logic, orchestration
- **Repository Layer** — data access abstraction
- **Persistence Layer** — database and file storage

### Testability

Automated testing with pytest covering:

- All API endpoints
- Document processing logic
- Error handling paths
- Input validation

### Observability

- Request logging on every call
- Processing logging per document
- Health endpoint for uptime monitoring

### Deployability

- Runs locally via `uvicorn`
- Docker-based deployment
- Compatible with DigitalOcean App Platform

### Configurability

All environment-sensitive values externalized:

- `DATABASE_URL` — SQLite path or future Postgres URL
- `UPLOAD_DIR` — file storage path
- `MAX_FILE_SIZE_MB` — upload size limit

---

## Constraints

- Only `.txt` files supported in MVP
- Maximum file size: 10 MB
- Each upload creates a new document (no deduplication)
- Processing results stored separately from document metadata

---

## Assumptions

- Single-instance deployment for MVP; horizontal scaling is a future concern
- Synchronous processing is acceptable for MVP given `.txt` file sizes
- SQLite is sufficient for MVP; PostgreSQL migration is a documented future path
- Local filesystem storage is acceptable for MVP; object storage is a documented future path
- No authentication or authorization required for MVP

---

## Future Enhancements

| Area | Enhancement |
|------|-------------|
| File types | PDF, DOCX, images, video |
| Processing | OCR, AI summarization, ML inference, image analysis |
| Auth | API key or OAuth-based authentication |
| Storage | DigitalOcean Spaces / S3-compatible object storage |
| Database | PostgreSQL for production workloads |
| Processing model | Async background workers via Celery + Redis |
| Architecture | Queue-based worker separation (see architecture.md) |

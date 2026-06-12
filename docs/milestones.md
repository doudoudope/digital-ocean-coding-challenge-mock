# Milestones

## Overview

| # | Milestone | Goal |
|---|-----------|------|
| M1 | Project Skeleton | `GET /health` returns 200 |
| M2 | Upload + Metadata | `POST /documents` stores file and metadata |
| M3 | Processing + Results | `GET /documents/{id}/result` returns analysis |
| M4 | Read APIs | All GET endpoints functional |
| M5 | Validation + Error Handling | Bad inputs return proper error responses |
| M6 | Tests | Full pytest suite passes |
| M7 | Docker + Deployment | Service running publicly on DigitalOcean |
| M8 | Production Enhancements | Observability, config hardening, async processing |

---

## M1 — Project Skeleton

**Goal:** Runnable FastAPI application with database initialization and a working health endpoint.

### Scope

- Project directory structure
- `requirements.txt`
- `app/config.py` — externalized settings
- `app/models/db.py` — SQLAlchemy engine, session, `Base`, `get_db`, `init_db`
- `app/api/health.py` — `GET /health`
- `app/main.py` — app init, lifespan, router registration
- `tests/conftest.py` — TestClient, isolated test DB, dependency override
- `tests/test_health.py`

### Files Expected

```
app/__init__.py
app/main.py
app/config.py
app/api/__init__.py
app/api/health.py
app/models/__init__.py
app/models/db.py
tests/__init__.py
tests/conftest.py
tests/test_health.py
requirements.txt
```

### Acceptance Criteria

- [ ] `uvicorn app.main:app --reload` starts without errors
- [ ] `GET /health` returns `{"status": "healthy"}` with HTTP 200
- [ ] `pytest tests/test_health.py` passes with no warnings

### Manual Test Steps

```bash
uvicorn app.main:app --reload
curl http://127.0.0.1:8000/health
# Expected: {"status":"healthy"}
```

---

## M2 — Upload + Metadata

**Goal:** Accept a `.txt` file upload, save it to disk, and persist document metadata to the database.

### Scope

- `app/models/document.py` — `Document` ORM model
- `app/schemas/document.py` — `DocumentUploadResponse` Pydantic schema
- `app/repositories/document_repo.py` — `create`, `get_by_id`
- `app/services/document_service.py` — upload orchestration
- `app/storage/local_storage.py` — `save_file`
- `app/api/documents.py` — `POST /documents`
- `app/main.py` — register documents router

### Files Expected

```
app/models/document.py
app/schemas/document.py
app/repositories/document_repo.py
app/services/document_service.py
app/storage/__init__.py
app/storage/local_storage.py
app/api/documents.py
```

### Acceptance Criteria

- [ ] `POST /documents` with a valid `.txt` file returns HTTP 201 with `document_id` and `status: "pending"`
- [ ] A row exists in the `documents` table after upload
- [ ] The file exists on disk at `UPLOAD_DIR/{document_id}.txt`

### Manual Test Steps

```bash
echo "hello world" > test.txt
curl -X POST http://127.0.0.1:8000/documents \
  -F "file=@test.txt"
# Expected: {"document_id": "<uuid>", "status": "pending"}
```

---

## M3 — Processing + Results

**Goal:** Process an uploaded document synchronously and store analysis results. The result endpoint returns processing output.

### Scope

- `app/models/result.py` — `DocumentResult` ORM model
- `app/schemas/result.py` — `DocumentResultResponse` Pydantic schema
- `app/repositories/result_repo.py` — `create`, `get_by_document_id`
- `app/services/processing_service.py` — word count, line count, keyword extraction
- `app/services/document_service.py` — trigger processing after upload, update status
- `app/api/documents.py` — `GET /documents/{id}/result`

### Files Expected

```
app/models/result.py
app/schemas/result.py
app/repositories/result_repo.py
app/services/processing_service.py
```

### Acceptance Criteria

- [ ] After a successful upload, the document status is `completed`
- [ ] `GET /documents/{id}/result` returns `word_count`, `line_count`, `keywords`, `summary`
- [ ] `word_count` and `line_count` are accurate for the uploaded file
- [ ] `keywords` is a non-empty list
- [ ] `summary` is `"placeholder"`

### Manual Test Steps

```bash
curl -X POST http://127.0.0.1:8000/documents -F "file=@test.txt"
# Note the document_id

curl http://127.0.0.1:8000/documents/<document_id>/result
# Expected: {"word_count":2,"line_count":1,"keywords":[...],"summary":"placeholder"}
```

---

## M4 — Read APIs

**Goal:** All remaining GET endpoints are functional.

### Scope

- `GET /documents/{id}` — return full document metadata
- `GET /documents/{id}/status` — return current status
- `GET /documents` — return paginated list with optional status filter
- `app/schemas/document.py` — `DocumentResponse`, `DocumentListResponse`
- `app/repositories/document_repo.py` — `list_documents` with pagination and filter
- `app/services/document_service.py` — retrieve, list logic

### Files Expected

No new files; extensions to existing `documents.py`, `document_repo.py`, `document_service.py`, `document schemas`.

### Acceptance Criteria

- [ ] `GET /documents/{id}` returns all 7 metadata fields with HTTP 200
- [ ] `GET /documents/{id}` returns HTTP 404 for unknown ID
- [ ] `GET /documents/{id}/status` returns `{"status": "..."}` with HTTP 200
- [ ] `GET /documents` returns `items`, `total`, `page`, `page_size`
- [ ] `GET /documents?status=completed` returns only completed documents
- [ ] `GET /documents?page=1&page_size=5` respects pagination

### Manual Test Steps

```bash
# Upload two documents first
curl -X POST http://127.0.0.1:8000/documents -F "file=@test.txt"
curl -X POST http://127.0.0.1:8000/documents -F "file=@test.txt"

curl http://127.0.0.1:8000/documents
# Expected: items array with 2 entries, total: 2

curl http://127.0.0.1:8000/documents?status=completed
# Expected: both documents (processing is synchronous)

curl http://127.0.0.1:8000/documents/<id>
# Expected: full metadata object

curl http://127.0.0.1:8000/documents/<id>/status
# Expected: {"status": "completed"}

curl http://127.0.0.1:8000/documents/nonexistent-id
# Expected: HTTP 404
```

---

## M5 — Validation + Error Handling

**Goal:** Invalid inputs return proper HTTP error responses with meaningful messages.

### Scope

- File type validation — reject non-`.txt` files with HTTP 400
- File size validation — reject files over `MAX_FILE_SIZE_MB` with HTTP 413
- 404 handling for all document endpoints
- 409 response when result is requested on a non-completed document
- Consistent error response shape across all endpoints

### Files Expected

No new files; changes to `app/api/documents.py` and `app/services/document_service.py`.

### Acceptance Criteria

- [ ] Uploading a `.pdf` or `.jpg` returns HTTP 400 with an error message
- [ ] Uploading a file over 10 MB returns HTTP 413
- [ ] `GET /documents/bad-id` returns HTTP 404
- [ ] `GET /documents/bad-id/status` returns HTTP 404
- [ ] `GET /documents/bad-id/result` returns HTTP 404
- [ ] `GET /documents/{id}/result` for a `pending` document returns HTTP 409
- [ ] All error responses include a `detail` field

### Manual Test Steps

```bash
# Wrong file type
echo "data" > test.pdf
curl -X POST http://127.0.0.1:8000/documents -F "file=@test.pdf"
# Expected: HTTP 400

# Large file (generate 11 MB file)
dd if=/dev/zero bs=1M count=11 | tr '\0' 'a' > big.txt
curl -X POST http://127.0.0.1:8000/documents -F "file=@big.txt"
# Expected: HTTP 413

# Not found
curl http://127.0.0.1:8000/documents/does-not-exist
# Expected: HTTP 404

# Result before completion (hard to test with sync processing;
# verify the 409 path exists in code and is covered by tests)
```

---

## M6 — Tests

**Goal:** Full pytest suite covers all endpoints, processing logic, and error cases.

### Scope

- `tests/test_documents.py` — upload, retrieve, list, status, result, all error paths
- `tests/test_processing.py` — unit tests for `processing_service.py`
- All tests use the test DB from `conftest.py`
- No external dependencies (no real files on disk required in unit tests)

### Files Expected

```
tests/test_documents.py
tests/test_processing.py
```

### Acceptance Criteria

- [ ] `pytest` passes with no failures
- [ ] Upload happy path covered
- [ ] 400 (wrong type), 413 (too large), 404 (not found), 409 (not ready) covered
- [ ] List pagination and status filter covered
- [ ] `word_count`, `line_count`, `keywords` logic tested with known input
- [ ] No test touches the real database or real filesystem

### Manual Test Steps

```bash
pytest -v
# Expected: all tests pass, no warnings
```

---

## M7 — Docker + Deployment

**Goal:** Service is containerized, runs cleanly in Docker, and is accessible publicly on DigitalOcean App Platform.

### Scope

- `Dockerfile`
- `.env.example`
- `.dockerignore`
- DigitalOcean App Platform configuration

### Files Expected

```
Dockerfile
.dockerignore
.env.example
```

### Acceptance Criteria

- [ ] `docker build -t doc-service .` succeeds
- [ ] `docker run -p 8080:8080 doc-service` starts without errors
- [ ] `curl http://localhost:8080/health` returns `{"status":"healthy"}`
- [ ] Service is deployed to DigitalOcean App Platform
- [ ] `GET /health` returns 200 at the public App Platform URL

### Manual Test Steps

```bash
docker build -t doc-service .
docker run -p 8080:8080 doc-service
curl http://localhost:8080/health
# Expected: {"status":"healthy"}

# After deploying to App Platform:
curl https://<your-app>.ondigitalocean.app/health
# Expected: {"status":"healthy"}
```

---

## M8 — Production Enhancements

**Goal:** Improve observability, configuration hardening, and document the async processing path. Does not need to be fully production-ready — demonstrate the thinking.

### Scope (prioritized)

1. **Structured logging** — replace `basicConfig` with JSON-formatted log output including `document_id`, `status`, `duration_ms` on processing events
2. **Request logging middleware** — log method, path, status code, and duration on every request
3. **Environment variable validation** — fail fast on startup if required config is missing or invalid
4. **Background processing sketch** — implement processing as a `BackgroundTask` (FastAPI built-in); return `status: "pending"` immediately and process after response
5. **`.env.example`** — document all supported environment variables

### Files Expected

```
app/middleware/logging.py   (or inline in main.py)
.env.example
```

### Acceptance Criteria

- [ ] Every request produces a log line with method, path, status, duration
- [ ] Processing events log `document_id` and outcome
- [ ] Invalid config causes a clear startup error, not a runtime crash
- [ ] (If background task implemented) Upload returns `status: "pending"` immediately; status transitions to `completed` after processing

### Manual Test Steps

```bash
uvicorn app.main:app --reload
curl -X POST http://127.0.0.1:8000/documents -F "file=@test.txt"
# Expected: structured log lines visible in terminal for request + processing

curl http://127.0.0.1:8000/documents/<id>/status
# If background task: may briefly show "processing" before "completed"
```

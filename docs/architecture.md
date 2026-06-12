# Architecture

## High-Level Architecture Diagram

### MVP (Current)

```
┌─────────────────────────────────────────────────────┐
│                      Client                         │
└────────────────────────┬────────────────────────────┘
                         │ HTTP
                         ▼
┌─────────────────────────────────────────────────────┐
│                  FastAPI Service                     │
│                                                     │
│   ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│   │ API Layer│  │ Service  │  │  Processing      │  │
│   │ (routes) │→ │  Layer   │→ │  Service         │  │
│   └──────────┘  └──────────┘  └──────────────────┘  │
│                      │                              │
│              ┌───────┴────────┐                     │
│              ▼                ▼                     │
│   ┌─────────────────┐  ┌─────────────────┐         │
│   │  Document Repo  │  │  Result Repo    │         │
│   └────────┬────────┘  └────────┬────────┘         │
└────────────┼────────────────────┼──────────────────┘
             ▼                    ▼
     ┌──────────────┐     ┌──────────────┐
     │   SQLite DB  │     │  Local File  │
     │  (metadata + │     │   Storage    │
     │   results)   │     │  (/uploads)  │
     └──────────────┘     └──────────────┘
```

### Future Production Architecture

```
┌─────────┐     ┌─────────────┐     ┌──────────┐     ┌──────────────┐
│ Client  │────▶│ API Service │────▶│  Queue   │────▶│Worker Service│
└─────────┘     └─────────────┘     │(Redis/   │     └──────┬───────┘
                                    │ Kafka)   │            │
                                    └──────────┘     ┌──────▼───────┐
                                                     │  PostgreSQL  │
                                                     │  DO Spaces   │
                                                     └──────────────┘
```

---

## Component Responsibilities

| Component | Responsibility |
|-----------|---------------|
| **API Layer** (`app/api/`) | Receive HTTP requests, validate input, serialize responses, delegate to services |
| **Service Layer** (`app/services/`) | Orchestrate business logic, coordinate between repositories and processing |
| **Processing Service** (`app/services/processing_service.py`) | Execute document analysis: word count, line count, keyword extraction |
| **Repository Layer** (`app/repositories/`) | Abstract all database access; services never touch the ORM directly |
| **Storage Layer** (`app/storage/`) | Abstract file I/O; services never touch the filesystem directly |
| **Models** (`app/models/`) | SQLAlchemy ORM definitions and database session management |
| **Schemas** (`app/schemas/`) | Pydantic models for request/response validation and serialization |
| **Config** (`app/config.py`) | Centralized settings loaded from environment variables |

---

## API Design

### Endpoints

| Method | Path | Description | Success Code |
|--------|------|-------------|--------------|
| POST | `/documents` | Upload a document | 201 |
| GET | `/documents` | List documents (paginated) | 200 |
| GET | `/documents/{id}` | Get document metadata | 200 |
| GET | `/documents/{id}/status` | Get processing status | 200 |
| GET | `/documents/{id}/result` | Get processing results | 200 |
| GET | `/health` | Health check | 200 |

### Error Codes

| Code | Condition |
|------|-----------|
| 400 | Unsupported file type or malformed request |
| 404 | Document not found |
| 409 | Result requested but processing not complete |
| 413 | File exceeds `MAX_FILE_SIZE_MB` limit |

### Request / Response Contracts

**POST /documents**
- Request: `multipart/form-data`, field name `file`
- Response:
```json
{ "document_id": "uuid", "status": "pending" }
```

**GET /documents**
- Query params: `page` (default 1), `page_size` (default 20), `status` (optional)
- Response:
```json
{
  "items": [ { ...document metadata... } ],
  "total": 45,
  "page": 1,
  "page_size": 20
}
```

**GET /documents/{id}/result**
- Response:
```json
{
  "word_count": 1200,
  "line_count": 87,
  "keywords": ["python", "api", "database"],
  "summary": "placeholder"
}
```

---

## Database Schema

### Table: `documents`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | VARCHAR | PK | UUID string |
| filename | VARCHAR | NOT NULL | Original uploaded filename |
| file_size | INTEGER | NOT NULL | Bytes |
| content_type | VARCHAR | NOT NULL | e.g. `text/plain` |
| status | VARCHAR | NOT NULL | pending / processing / completed / failed |
| created_at | DATETIME | NOT NULL | Set on insert |
| updated_at | DATETIME | NOT NULL | Updated on every state change |

**Index:** `documents.status` — supports filtered list queries.

### Table: `document_results`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | INTEGER | PK (auto) | |
| document_id | VARCHAR | FK → documents.id | |
| word_count | INTEGER | | |
| line_count | INTEGER | | |
| keywords | TEXT | | JSON-serialized list |
| summary | TEXT | | Placeholder for now |
| created_at | DATETIME | NOT NULL | |

**Index:** `document_results.document_id` — supports lookup by document.

---

## Project Structure

```
app/
├── __init__.py
├── main.py                    # App init, lifespan, router registration
├── config.py                  # Settings via pydantic-settings
├── api/
│   ├── __init__.py
│   ├── health.py              # GET /health
│   └── documents.py           # All /documents routes
├── services/
│   ├── document_service.py    # Upload, retrieve, list logic
│   └── processing_service.py  # Word count, line count, keywords
├── repositories/
│   ├── document_repo.py       # CRUD for documents table
│   └── result_repo.py         # CRUD for document_results table
├── models/
│   ├── __init__.py
│   ├── db.py                  # Engine, session, Base, get_db, init_db
│   ├── document.py            # Document ORM model
│   └── result.py              # DocumentResult ORM model
├── schemas/
│   ├── document.py            # Pydantic schemas for documents
│   └── result.py              # Pydantic schemas for results
└── storage/
    └── local_storage.py       # File save/read abstraction
tests/
├── __init__.py
├── conftest.py                # TestClient, test DB, dependency overrides
├── test_health.py
├── test_documents.py          # Upload, retrieve, list, status, result
└── test_processing.py         # Processing logic unit tests
docs/
├── requirements.md
├── architecture.md
└── milestones.md
Dockerfile
requirements.txt
.env.example
```

---

## Data Flow

### Document Upload

```
POST /documents (multipart file)
  │
  ├── [API] Validate file type (.txt) and size (≤ 10 MB)
  │
  ├── [Service] Generate UUID document_id
  │
  ├── [Storage] Save file to UPLOAD_DIR/{document_id}.txt
  │
  ├── [Repo] Insert documents row (status: pending)
  │
  ├── [Processing] Run analysis (word count, line count, keywords)
  │
  ├── [Repo] Update documents row (status: completed)
  │
  ├── [Repo] Insert document_results row
  │
  └── Return { document_id, status: "completed" }
```

### Document Retrieval

```
GET /documents/{id}/result
  │
  ├── [Repo] Fetch document by ID → 404 if not found
  │
  ├── [Service] Check status → 409 if not completed
  │
  ├── [Repo] Fetch document_results by document_id
  │
  └── Return result payload
```

---

## Deployment Strategy

### Local

```bash
uvicorn app.main:app --reload
```

### Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### DigitalOcean App Platform

1. Connect GitHub repository
2. Set run command: `uvicorn app.main:app --host 0.0.0.0 --port 8080`
3. Set environment variables: `DATABASE_URL`, `UPLOAD_DIR`, `MAX_FILE_SIZE_MB`
4. Deploy and verify `GET /health` at public URL

**Known limitation:** SQLite on App Platform uses ephemeral disk — data does not persist across deploys. Acceptable for demo; PostgreSQL is the production path.

---

## Scalability Considerations

### Current Bottlenecks

| Bottleneck | Impact |
|------------|--------|
| Synchronous processing in request cycle | Long documents block the HTTP response |
| SQLite | Single-writer; cannot scale horizontally |
| Local file storage | Not accessible across multiple instances |
| Single process | No parallelism for concurrent uploads |

### Scaling Path

1. **Processing** → move to background task (thread pool → Celery worker)
2. **Database** → migrate to PostgreSQL via `DATABASE_URL` env var change
3. **File storage** → swap `local_storage.py` for DigitalOcean Spaces client
4. **API** → run multiple uvicorn workers behind a load balancer

The `status` field on `documents` and the `storage/` abstraction layer exist specifically to enable steps 1 and 3 without breaking API contracts.

---

## Trade-offs and Design Decisions

### Decision: Synchronous processing in MVP

- **Rationale:** Eliminates queue, worker, and broker infrastructure. Text files process in milliseconds — latency impact is negligible for MVP.
- **Future evolution:** Add a background task (initially `asyncio` or `ThreadPoolExecutor`, later Celery) and set status to `processing` before returning the upload response. The API contract does not change.

---

### Decision: SQLite for persistence

- **Rationale:** Zero infrastructure, file-based, adequate for single-instance demo workloads.
- **Future evolution:** Change `DATABASE_URL` to a PostgreSQL connection string. SQLAlchemy abstracts the difference; no application code changes required.

---

### Decision: Local filesystem for file storage

- **Rationale:** No external dependencies for MVP.
- **Future evolution:** Replace `local_storage.py` implementation with a DigitalOcean Spaces / S3 client. The `storage/` abstraction layer ensures no code above it changes.

---

### Decision: UUID document IDs

- **Rationale:** Avoids sequential ID enumeration on a public API. Safe to expose in URLs.
- **Future evolution:** No change needed.

---

### Decision: Results stored in a separate table

- **Rationale:** Keeps metadata queries fast and decouples the result schema from the document schema. Results can evolve independently (new fields, versioning) without touching the documents table.
- **Future evolution:** Add result versioning or multiple result types per document without schema changes to `documents`.

---

### Decision: `status` field on documents even for synchronous MVP

- **Rationale:** Makes the async upgrade non-breaking. Clients can already poll `GET /documents/{id}/status` — the polling behavior works correctly whether processing is sync or async.
- **Future evolution:** Set status to `processing` before returning the upload response; complete it asynchronously in a worker.

# Document Ingestion & Processing Service

A production-style REST API for uploading, processing, and querying text documents. Built as a DigitalOcean App Platform coding challenge.

## High Level Design

```
Client
  │
  │  X-API-Key header
  ▼
FastAPI Web Service ──── PostgreSQL (users, documents, results)
  │         │
  │         └─────────── Redis
  │                        ├── Task queue (Celery broker)
  │                        ├── Result cache (Cache Aside, TTL 1h)
  │                        ├── User cache (TTL 5min)
  │                        └── Daily upload quota (INCR, TTL 24h)
  │
  └── Celery Worker (async)
        └── Processes document → writes result → updates status
```

**Upload flow:** POST /documents returns immediately with `status: pending`. The worker processes the file asynchronously; clients poll GET /status or fetch GET /result once complete.

**Auth flow:** Every request validates `X-API-Key` → Redis user cache → PostgreSQL fallback. Free-tier users have a daily upload quota enforced via Redis atomic increment.

**No shared filesystem:** File content is base64-encoded into the Celery task message so the Web and Worker containers are fully independent.

## API

All endpoints except `GET /health` require `X-API-Key` header.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/documents` | Upload a `.txt` file |
| GET | `/documents` | List documents (scoped to authenticated user) |
| GET | `/documents/{id}` | Get document metadata |
| GET | `/documents/{id}/status` | Get processing status |
| GET | `/documents/{id}/result` | Get processing result |

### Upload limits by tier

| Tier | Max file size | Daily uploads |
|------|--------------|---------------|
| free | 2 MB | 10 |
| paid | 50 MB | unlimited |

### Example requests

```bash
# Upload a document
curl -X POST https://<your-app>.ondigitalocean.app/documents \
  -H "X-API-Key: sk-..." \
  -F "file=@document.txt"

# Get result
curl https://<your-app>.ondigitalocean.app/documents/{id}/result \
  -H "X-API-Key: sk-..."
```

### Error responses

| Status | Meaning |
|--------|---------|
| 400 | Unsupported file type (only `.txt` accepted) |
| 401 | Invalid or inactive API key |
| 403 | Document belongs to another user |
| 409 | Document not yet processed |
| 413 | File exceeds tier size limit |
| 422 | Missing `X-API-Key` header |
| 429 | Daily upload limit reached (free tier) |

## Local Development

**Prerequisites:** Python 3.11+, Redis running on `localhost:6379`

```bash
# Install dependencies
pip install -r requirements.txt

# Start the API
uvicorn app.main:app --reload

# Start the Celery worker (separate terminal)
celery -A app.celery_app worker --loglevel=info
```

The app defaults to SQLite (`documents.db`) locally. Set `DATABASE_URL` and `REDIS_URL` in a `.env` file to use PostgreSQL/Redis.

```
DATABASE_URL=postgresql://user:pass@localhost:5432/documents
REDIS_URL=redis://localhost:6379/0
```

## Running Tests

```bash
pytest tests/ -v
```

Tests use SQLite in-memory, a mocked Redis client, and Celery in eager mode — no external services needed.

## Creating Users

Users are created directly in the database (no registration endpoint). Use the provided script:

```bash
# Create a paid user
python scripts/create_user.py paid alice@example.com

# Create a free user
python scripts/create_user.py free bob@example.com
```

The script prints the generated `sk-...` API key.

**On DigitalOcean:** connect via the App Platform Console → `psql $DATABASE_URL`, then:

```sql
INSERT INTO users (id, api_key, tier, email, is_active, created_at)
VALUES (
  gen_random_uuid()::text,
  'sk-<your-32-char-key>',
  'paid',
  'alice@example.com',
  true,
  NOW()
);
```

## Deployment (DigitalOcean App Platform)

The app is deployed as three components:

| Component | Type | Notes |
|-----------|------|-------|
| `digital-ocean-codi` (web) | Web Service | `uvicorn app.main:app` |
| `digital-ocean-codi` (worker) | Worker | `celery -A app.celery_app worker` |
| `postgresqldb` | Dev Database | PostgreSQL 17 |
| `db-vk-nyc1` | Managed Database | Valkey (Redis-compatible) |

**Required environment variables:**

| Variable | Source |
|----------|--------|
| `DATABASE_URL` | Auto-injected by DO (`postgresqldb`) |
| `REDIS_URL` | Set manually from Valkey connection string |

> Note: DigitalOcean injects `postgres://` but SQLAlchemy requires `postgresql://` — the app fixes this automatically via a `field_validator` in `Settings`.

## Project Structure

```
app/
├── api/            # FastAPI route handlers
├── dependencies/   # Auth dependencies (get_current_user, quota, ownership)
├── models/         # SQLAlchemy ORM models
├── repositories/   # DB query functions
├── schemas/        # Pydantic request/response models
├── services/       # Business logic
├── storage/        # Local file storage
├── tasks/          # Celery tasks
├── cache.py        # Redis client singleton
├── celery_app.py   # Celery instance
├── config.py       # Settings (pydantic-settings)
└── main.py         # FastAPI app + lifespan

scripts/
└── create_user.py  # Create users directly in DB

tests/
├── conftest.py     # Fixtures (test DB, mock Redis, eager Celery, test user)
├── test_documents.py
├── test_health.py
└── test_processing.py
```

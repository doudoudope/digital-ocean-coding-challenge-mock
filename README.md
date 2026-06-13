# Document Ingestion & Processing Service

A production-style REST API for uploading, processing, and querying text documents. Built as a DigitalOcean App Platform coding challenge.

## Architecture

```
Client
  │
  ▼
FastAPI (Web Service)
  ├── PostgreSQL       — document metadata, results, users
  ├── Redis (Valkey)   — async task queue, result cache, daily quota
  └── Celery (Worker)  — background document processing
```

**Key design decisions:**
- Document processing runs asynchronously via Celery so uploads return immediately
- File content is base64-encoded in the task message — no shared filesystem between Web and Worker containers
- Cache Aside pattern for GET /result — Redis TTL 1 hour, falls back to DB on miss
- API key auth with per-user Redis cache (TTL 5 min) to avoid DB lookup on every request
- Daily upload quota stored in Redis (`INCR` + `EXPIRE 86400`) — fast atomic increments

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

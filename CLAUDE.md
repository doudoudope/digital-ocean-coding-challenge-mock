# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A FastAPI REST API for asynchronous document ingestion and processing, built as a DigitalOcean
App Platform coding challenge. Clients upload `.txt` files; a Celery worker processes them in
the background; results are retrieved via polling. Auth is API-key based with Redis-cached user
lookups and per-user daily upload quotas for free-tier users.

## Commands

```bash
# Start the API server
uvicorn app.main:app --reload

# Start the Celery worker (separate terminal)
celery -A app.celery_app worker --loglevel=info

# Run all tests (no external services needed)
pytest tests/ -v

# Run a single test file or test
pytest tests/test_documents.py -v
pytest tests/test_documents.py::test_upload_document -v

# Create a user (prints the generated sk-... API key)
python scripts/create_user.py paid alice@example.com
python scripts/create_user.py free bob@example.com
```

## Working Style

- **Think before coding.** State assumptions. If multiple interpretations exist, surface them
  and ask before proceeding.
- **Simplicity first.** Minimum code that solves the problem. No abstractions for single-use
  code, no flexibility that wasn't requested.
- **Surgical changes.** Touch only what the task requires. Match existing style; don't refactor
  what isn't broken.
- **Verify before claiming done.** Define a check before implementing — a test, a runnable
  command, or a measurement — and confirm it passes.
- **Restructure end-to-end.** When moving, renaming, or removing structure, trace it from repo
  root through build/deploy paths (Dockerfile, Procfile, configs). If the reason for
  surrounding structure no longer holds, remove it in the same pass — no orphaned files or
  stale config left as follow-ups.

## Architecture

FastAPI + Celery + Redis + SQLAlchemy. Upload flow: `POST /documents` returns immediately with
`status: pending`; the worker processes asynchronously; clients poll
`GET /documents/{id}/status` or fetch `GET /documents/{id}/result` once complete.

**Key design decisions:**

- **No shared filesystem**: file content is base64-encoded into the Celery task message so web
  and worker containers are fully independent.
- **Cache-aside**: user auth (`user:{api_key}`, TTL 5min) and results (`result:{doc_id}`,
  TTL 1h) are cached in Redis; failures are silently bypassed — the DB is authoritative.
- **Quota**: free-tier daily upload count uses Redis `INCR`+`EXPIRE` on
  `quota:{user_id}:{date}`. Check is in `check_upload_quota`; increment is in
  `increment_upload_quota`, called manually in the route after a successful upload.
- **`postgres://` fix**: DigitalOcean injects `postgres://` URIs; `Settings.fix_postgres_scheme`
  rewrites to `postgresql://` for SQLAlchemy 2.x.

**Layers:** `app/api/` (routes) → `app/dependencies/auth.py` (auth, quota, ownership checks)
→ `app/services/` (business logic) → `app/repositories/` (all DB queries) → `app/models/`
(SQLAlchemy ORM) and `app/schemas/` (Pydantic).

**Test setup:** `tests/conftest.py` uses SQLite + a `MagicMock` Redis client (default: cache
miss) + `task_always_eager=True` so no external services are needed. The `test_user` fixture
is `paid` tier; override `tier` in individual tests to exercise quota logic.

## Guardrails

`tests/` defines what "done" means — make the tests pass, never weaken them. Local dev needs
no `.env`; copy `.env.example` to `.env` only when switching to PostgreSQL/Redis.

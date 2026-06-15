1. set up git repo
2. check if claude is avaliable : 
which claude
claude --version
node --version
npm --version
brew install node
npm install -g @anthropic-ai/claude-code

 Set up .claude/settings.json with standard guardrails — allow pytest/pip/python/uvicorn/curl/docker/redis-cli/safe git
  commands, deny git push/commit/rm -rf/.env reads. Update .gitignore to use .claude/* so settings.json gets tracked.

{
  "permissions": {
    "allow": [
      "Bash(pip install *)",
      "Bash(pip install -r *)",
      "Bash(python *)",
      "Bash(pytest *)",
      "Bash(uvicorn *)",
      "Bash(curl *)",
      "Bash(docker build *)",
      "Bash(docker run *)",
      "Bash(docker rm *)",
      "Bash(docker compose up *)",
      "Bash(docker compose down)",
      "Bash(docker compose logs *)",
      "Bash(docker ps *)",
      "Bash(redis-cli *)",
      "Bash(git status)",
      "Bash(git diff *)",
      "Bash(git log *)",
      "Bash(git add *)",
      "Bash(git restore *)",
      "Bash(gh run list *)",
      "Bash(gh run view *)",
      "Bash(gh pr view *)"
    ],
    "deny": [
      "Read(./**/.env)",
      "Read(./**/.env.*)",
      "Read(./**/__pycache__/**)",
      "Read(./**/.pytest_cache/**)",
      "Read(./**/.venv/**)",
      "Bash(rm -rf *)",
      "Bash(rm -fr *)",
      "Bash(git push *)",
      "Bash(git commit *)",
      "Bash(git reset --hard *)",
      "Bash(docker system prune *)"
    ]
  }
}





For this backend service I used FastAPI with Python.
  ▎
  ▎ At the top level, app/ holds the application code, tests/ holds the test suite, and a few deployment files sit at the root — Procfile, requirements.txt, and a Dockerfile.

  ▎ Inside app/, I used a layered architecture:
  ▎ - api/ handles the HTTP layer — routing, request parsing, and response formatting. No business logic lives here.
  ▎ - dependencies/ uses FastAPI's dependency injection for auth, quota enforcement, and ownership checks. These are composable — any route can pick up whichever it needs.
  ▎ - services/ is where all business logic lives.
  ▎ - repositories/ centralizes all database operations. The service layer never touches SQLAlchemy directly.
  ▎ - models/ are SQLAlchemy classes that map directly to database tables.
  ▎ - schemas/ are Pydantic models that define what the API accepts and returns — kept separate from models so the DB structure and API contract can evolve independently.
  ▎ - tasks/ holds the Celery async task for document processing.
  ▎ - cache.py is a Redis singleton shared across the entire app.
  ▎ - config.py reads all configuration from environment variables via pydantic-settings — one place, no scattered constants.
  ▎ - main.py is the entry point where everything is wired together.

Let me walk you through the data flow. I'll start with the simplest version of the service first, and then show you what I added on top and why."

 "The biggest bottleneck in the MVP is that processing blocks the web server. While the file is being analyzed, the server is tied up and can't handle other requests. For a file processing service this is unacceptable.
 
So the first thing I did was move processing off the request path using Celery with Redis as the message broker. 
Now when the service receives an upload request, it does three lightweight things: validates the file, writes a pending record to the database, and drops a task into the Redis queue. That's under 100ms. The web server immediately returns a 201 with the document ID and status  pending. The Celery worker picks up the task independently, processes the file, and updates the status to completed.

 "Before the service processes any request, it needs to verify who's calling. I implemented API key authentication — every request includes an X-API-Key header, which the service validates against the database.

I chose API keys because they were the fastest thing to implement in the time constraint — no login flow, no token management, just insert a key into the DB and you're done.

However, if this service is truly user-facing, I would switch to JWT

Users have two tiers — free and paid — which control two things: file size limit and daily upload quota.

Once a document is processed, clients often call GET /documents/{id}/result multiple times. Every one of those calls was hitting the database. Since results are immutable once written, this is a perfect candidate for caching."

I used Cache Aside pattern. On a read: check Redis first, if it's a miss go to DB, then write the result back to Redis . The write path — when the worker  saves the result — only touches the DB. Cache gets populated lazily on the first read."
the worker owns the DB write, the web service owns the cache
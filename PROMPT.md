# Project: Document Ingestion & Processing Service

## Overview

Build a REST API service that accepts document uploads, stores document metadata, processes document content, and exposes processing results through APIs.

The goal is to simulate a real-world data ingestion and processing platform.

This project should be designed using production-minded engineering practices while remaining practical enough to implement within a 3-hour coding exercise.

The implementation should demonstrate both:

1. Functional correctness
2. Production-ready thinking

The system does not need to be fully production-ready, but the design should clearly explain how it could evolve to support larger workloads and stricter operational requirements.

---

# Business Requirements

Users need a system where they can:

1. Upload text documents.
2. Track document processing progress.
3. Retrieve processing results.
4. Browse previously uploaded documents.
5. Query system health.

The system should be designed to support future processing workloads such as:

* OCR
* AI summarization
* Image analysis
* Video transcoding
* ML inference

---

# Functional Requirements

## FR1 - Upload Document

Users can upload a text document.

Supported file types:

* .txt

API:

POST /documents

Response:

```json
{
  "document_id": "123",
  "status": "pending"
}
```

---

## FR2 - Store Document Metadata

For every uploaded document, store:

* document_id
* filename
* file_size
* content_type
* status
* created_at
* updated_at

---

## FR3 - Process Document

The system should process uploaded documents and generate analysis results.

Processing includes:

* Word Count
* Line Count
* Top Keywords
* Summary Placeholder

Example:

```json
{
  "word_count": 1200,
  "line_count": 87,
  "keywords": [
    "python",
    "api",
    "database"
  ],
  "summary": "placeholder"
}
```

---

## FR4 - Retrieve Document Metadata

API:

GET /documents/{id}

Returns document metadata and current status.

---

## FR5 - List Documents

API:

GET /documents

Support:

* pagination
* optional status filtering

Examples:

GET /documents?page=1&page_size=20

GET /documents?status=completed

---

## FR6 - Retrieve Processing Status

API:

GET /documents/{id}/status

Response:

```json
{
  "status": "completed"
}
```

Possible states:

* pending
* processing
* completed
* failed

---

## FR7 - Retrieve Processing Results

API:

GET /documents/{id}/result

Returns processing output.

---

## FR8 - Health Check

API:

GET /health

Response:

```json
{
  "status": "healthy"
}
```

---

# Constraints

* Only .txt files supported for MVP
* Maximum file size: 10 MB
* Each upload creates a new document
* Processing results should be stored separately from document metadata

---

# Non-Functional Requirements

## Reliability

The system should:

* Validate inputs
* Return proper HTTP status codes
* Handle invalid requests gracefully
* Provide meaningful error messages

Examples:

* 400 Bad Request
* 404 Not Found
* 413 Payload Too Large

---

## Maintainability

The codebase should use clear separation of concerns.

Suggested layers:

* API Layer
* Service Layer
* Repository Layer
* Persistence Layer

---

## Testability

Automated testing should be included.

Recommended coverage:

* API endpoints
* Processing logic
* Error handling
* Validation

Suggested framework:

* pytest

---

## Observability

The service should include:

* request logging
* processing logging
* health endpoint

---

## Deployability

The application should:

* Run locally
* Support Docker-based deployment
* Be deployable to DigitalOcean App Platform

---

## Configurability

Configuration should be externalized where appropriate.

Examples:

* database path
* file storage path
* file size limits

---

# Implementation Strategy

This project should be implemented incrementally.

The primary goal is to deliver a working MVP that satisfies all functional requirements.

After the MVP is complete, additional improvements should be implemented to address non-functional requirements and demonstrate production-ready thinking.

The project should clearly distinguish between:

1. MVP Features (must-have)
2. Production Enhancements (nice-to-have)

---

# Phase 1: MVP

The MVP should focus on:

* Functional correctness
* Simplicity
* Fast implementation

Suggested technologies:

* FastAPI
* SQLite
* SQLAlchemy
* Local file storage

The MVP should satisfy all functional requirements.

Avoid introducing unnecessary complexity.

Examples of technologies that should NOT be included in the MVP unless required:

* Redis
* Kafka
* Celery
* Kubernetes
* Distributed systems

The goal is to deliver a complete working system as quickly as possible.

---

# Phase 2: Deployment

After the MVP is complete:

1. Add Docker support
2. Containerize the application
3. Deploy to DigitalOcean App Platform
4. Verify public access
5. Verify health endpoint

The deployment phase should happen before advanced production enhancements.

The goal is to ensure the service can run successfully in a clean environment.

---

# Phase 3: Production-Oriented Enhancements

After deployment succeeds, incrementally improve the system.

Potential enhancements include:

## Reliability

* Better error handling
* Input validation
* File size limits
* Structured exception handling

## Testing

* Additional unit tests
* Integration tests
* End-to-end API tests

## Observability

* Structured logging
* Request tracing
* Processing metrics

## Configuration

* Environment variables
* Settings management

## Scalability

* Background processing
* Queue-based architecture
* Worker processes

## Storage

* DigitalOcean Spaces
* S3-compatible object storage

## Database

* PostgreSQL migration path

---

# Future Architecture

Current MVP:

Client
→ FastAPI
→ SQLite
→ Local File Storage

Future Production Architecture:

Client
→ API Service
→ Queue
→ Worker Service
→ PostgreSQL
→ DigitalOcean Spaces

---

# Architecture Review Expectations

The implementation does not need to include all production features.

However, the design should explain:

* Current bottlenecks
* Scaling strategy
* Future architecture
* Trade-offs made during implementation

The ability to explain these decisions is more important than implementing every production feature.

---

# Your Task

You are a senior backend engineer conducting a design review.

Please help me:

1. Identify functional requirements.
2. Identify non-functional requirements.
3. Suggest API design.
4. Suggest database schema.
5. Suggest project structure.
6. Propose an MVP architecture.
7. Propose a deployment strategy.
8. Break implementation into milestones.
9. Prioritize MVP delivery first.
10. Prioritize deployment after MVP completion.
11. Suggest production enhancements after deployment.
12. Do not generate code yet.
13. Prefer simplicity over production-grade complexity.

High level design
https://link.excalidraw.com/l/8rzXlKtSNFV/70Lh348gyyn
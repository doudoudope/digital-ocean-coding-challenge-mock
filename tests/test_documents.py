import io
import uuid

from app.repositories import document_repo


def txt_file(content: str = "hello world") -> dict:
    return {"file": ("test.txt", io.BytesIO(content.encode()), "text/plain")}


# ---------------------------------------------------------------------------
# POST /documents — happy path
# ---------------------------------------------------------------------------

def test_upload_returns_201(client, tmp_upload_dir):
    response = client.post("/documents", files=txt_file())
    assert response.status_code == 201


def test_upload_response_shape(client, tmp_upload_dir):
    response = client.post("/documents", files=txt_file())
    body = response.json()
    assert "document_id" in body
    assert body["status"] == "pending"


def test_upload_response_document_id_is_uuid(client, tmp_upload_dir):
    response = client.post("/documents", files=txt_file())
    document_id = response.json()["document_id"]
    # Raises ValueError if not a valid UUID
    uuid.UUID(document_id)


def test_upload_each_call_creates_unique_id(client, tmp_upload_dir):
    id1 = client.post("/documents", files=txt_file()).json()["document_id"]
    id2 = client.post("/documents", files=txt_file()).json()["document_id"]
    assert id1 != id2


# ---------------------------------------------------------------------------
# POST /documents — database record
# ---------------------------------------------------------------------------

def test_upload_creates_db_record(client, tmp_upload_dir, db_session):
    content = "hello world"
    response = client.post("/documents", files=txt_file(content))
    document_id = response.json()["document_id"]

    doc = document_repo.get_by_id(db_session, document_id)
    assert doc is not None


def test_upload_stores_correct_metadata(client, tmp_upload_dir, db_session):
    content = "hello world\nsecond line"
    response = client.post("/documents", files=txt_file(content))
    document_id = response.json()["document_id"]

    doc = document_repo.get_by_id(db_session, document_id)
    assert doc.filename == "test.txt"
    assert doc.file_size == len(content.encode())
    assert doc.content_type == "text/plain"
    assert doc.status == "completed"


def test_upload_sets_timestamps(client, tmp_upload_dir, db_session):
    response = client.post("/documents", files=txt_file())
    document_id = response.json()["document_id"]

    doc = document_repo.get_by_id(db_session, document_id)
    assert doc.created_at is not None
    assert doc.updated_at is not None


# ---------------------------------------------------------------------------
# POST /documents — file storage
# ---------------------------------------------------------------------------

def test_upload_saves_file_to_disk(client, tmp_upload_dir):
    content = "stored content"
    response = client.post("/documents", files=txt_file(content))
    document_id = response.json()["document_id"]

    saved = tmp_upload_dir / f"{document_id}.txt"
    assert saved.exists()


def test_upload_file_content_is_preserved(client, tmp_upload_dir):
    content = "exact content check"
    response = client.post("/documents", files=txt_file(content))
    document_id = response.json()["document_id"]

    saved = tmp_upload_dir / f"{document_id}.txt"
    assert saved.read_bytes() == content.encode()


# ---------------------------------------------------------------------------
# GET /documents/{id}/result — happy path
# ---------------------------------------------------------------------------

def test_get_result_returns_200(client, tmp_upload_dir):
    document_id = client.post("/documents", files=txt_file()).json()["document_id"]
    response = client.get(f"/documents/{document_id}/result")
    assert response.status_code == 200


def test_get_result_shape(client, tmp_upload_dir):
    document_id = client.post("/documents", files=txt_file()).json()["document_id"]
    body = client.get(f"/documents/{document_id}/result").json()
    assert "word_count" in body
    assert "line_count" in body
    assert "keywords" in body
    assert "summary" in body


def test_get_result_word_count(client, tmp_upload_dir):
    document_id = client.post("/documents", files=txt_file("one two three four")).json()["document_id"]
    body = client.get(f"/documents/{document_id}/result").json()
    assert body["word_count"] == 4


def test_get_result_line_count(client, tmp_upload_dir):
    document_id = client.post("/documents", files=txt_file("line one\nline two\nline three")).json()["document_id"]
    body = client.get(f"/documents/{document_id}/result").json()
    assert body["line_count"] == 3


def test_get_result_keywords_is_list(client, tmp_upload_dir):
    document_id = client.post("/documents", files=txt_file("python api database python")).json()["document_id"]
    body = client.get(f"/documents/{document_id}/result").json()
    assert isinstance(body["keywords"], list)


def test_get_result_summary_is_placeholder(client, tmp_upload_dir):
    document_id = client.post("/documents", files=txt_file()).json()["document_id"]
    body = client.get(f"/documents/{document_id}/result").json()
    assert body["summary"] == "placeholder"


# ---------------------------------------------------------------------------
# GET /documents/{id}/result — error cases
# ---------------------------------------------------------------------------

def test_get_result_not_found(client, tmp_upload_dir):
    response = client.get("/documents/nonexistent-id/result")
    assert response.status_code == 404


def test_get_result_not_found_has_detail(client, tmp_upload_dir):
    response = client.get("/documents/nonexistent-id/result")
    assert "detail" in response.json()


def test_get_result_returns_409_when_not_completed(client, db_session):
    from datetime import datetime, timezone
    from app.models.document import Document

    doc = Document(
        id="pending-doc-id",
        filename="pending.txt",
        file_size=10,
        content_type="text/plain",
        status="pending",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(doc)
    db_session.commit()

    response = client.get("/documents/pending-doc-id/result")
    assert response.status_code == 409
    assert "detail" in response.json()


# ---------------------------------------------------------------------------
# GET /documents/{id} — document metadata
# ---------------------------------------------------------------------------

def test_get_document_returns_200(client, tmp_upload_dir):
    document_id = client.post("/documents", files=txt_file()).json()["document_id"]
    response = client.get(f"/documents/{document_id}")
    assert response.status_code == 200


def test_get_document_returns_all_fields(client, tmp_upload_dir):
    document_id = client.post("/documents", files=txt_file()).json()["document_id"]
    body = client.get(f"/documents/{document_id}").json()
    assert body["document_id"] == document_id
    assert body["filename"] == "test.txt"
    assert body["file_size"] == len("hello world".encode())
    assert body["content_type"] == "text/plain"
    assert body["status"] == "completed"
    assert "created_at" in body
    assert "updated_at" in body


def test_get_document_not_found(client, tmp_upload_dir):
    response = client.get("/documents/nonexistent-id")
    assert response.status_code == 404


def test_get_document_not_found_has_detail(client, tmp_upload_dir):
    response = client.get("/documents/nonexistent-id")
    assert "detail" in response.json()


# ---------------------------------------------------------------------------
# GET /documents/{id}/status
# ---------------------------------------------------------------------------

def test_get_status_returns_200(client, tmp_upload_dir):
    document_id = client.post("/documents", files=txt_file()).json()["document_id"]
    response = client.get(f"/documents/{document_id}/status")
    assert response.status_code == 200


def test_get_status_returns_completed(client, tmp_upload_dir):
    document_id = client.post("/documents", files=txt_file()).json()["document_id"]
    body = client.get(f"/documents/{document_id}/status").json()
    assert body == {"status": "completed"}


def test_get_status_not_found(client, tmp_upload_dir):
    response = client.get("/documents/nonexistent-id/status")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /documents — list + pagination + filter
# ---------------------------------------------------------------------------

def test_list_returns_200(client, tmp_upload_dir):
    response = client.get("/documents")
    assert response.status_code == 200


def test_list_response_shape(client, tmp_upload_dir):
    body = client.get("/documents").json()
    assert "items" in body
    assert "total" in body
    assert "page" in body
    assert "page_size" in body


def test_list_returns_uploaded_documents(client, tmp_upload_dir):
    client.post("/documents", files=txt_file())
    client.post("/documents", files=txt_file())
    body = client.get("/documents").json()
    assert body["total"] == 2
    assert len(body["items"]) == 2


def test_list_default_pagination(client, tmp_upload_dir):
    body = client.get("/documents").json()
    assert body["page"] == 1
    assert body["page_size"] == 20


def test_list_pagination_limits_items(client, tmp_upload_dir):
    for _ in range(3):
        client.post("/documents", files=txt_file())
    body = client.get("/documents?page=1&page_size=2").json()
    assert len(body["items"]) == 2
    assert body["total"] == 3
    assert body["page_size"] == 2


def test_list_page_2(client, tmp_upload_dir):
    for _ in range(3):
        client.post("/documents", files=txt_file())
    body = client.get("/documents?page=2&page_size=2").json()
    assert len(body["items"]) == 1


def test_list_filter_by_status(client, tmp_upload_dir):
    client.post("/documents", files=txt_file())
    body = client.get("/documents?status=completed").json()
    assert body["total"] >= 1
    assert all(item["status"] == "completed" for item in body["items"])


def test_list_filter_by_status_no_match(client, tmp_upload_dir):
    client.post("/documents", files=txt_file())
    body = client.get("/documents?status=pending").json()
    assert body["total"] == 0
    assert body["items"] == []


# ---------------------------------------------------------------------------
# M5 — file type validation (400)
# ---------------------------------------------------------------------------

def bad_file(name: str, mime: str) -> dict:
    return {"file": (name, io.BytesIO(b"data"), mime)}


def test_upload_rejects_pdf(client, tmp_upload_dir):
    response = client.post("/documents", files=bad_file("report.pdf", "application/pdf"))
    assert response.status_code == 400


def test_upload_rejects_jpg(client, tmp_upload_dir):
    response = client.post("/documents", files=bad_file("photo.jpg", "image/jpeg"))
    assert response.status_code == 400


def test_upload_rejects_no_extension(client, tmp_upload_dir):
    response = client.post("/documents", files=bad_file("noextension", "text/plain"))
    assert response.status_code == 400


def test_upload_bad_type_returns_detail(client, tmp_upload_dir):
    response = client.post("/documents", files=bad_file("report.pdf", "application/pdf"))
    assert "detail" in response.json()


# ---------------------------------------------------------------------------
# M5 — file size validation (413)
# ---------------------------------------------------------------------------

def test_upload_rejects_oversized_file(client, tmp_upload_dir, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "max_file_size_mb", 0)
    # Force re-evaluation of the limit inside the router module
    import app.api.documents as docs_module
    monkeypatch.setattr(docs_module, "_MAX_BYTES", 0)
    response = client.post("/documents", files=txt_file("any content"))
    assert response.status_code == 413


def test_upload_oversized_returns_detail(client, tmp_upload_dir, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "max_file_size_mb", 0)
    import app.api.documents as docs_module
    monkeypatch.setattr(docs_module, "_MAX_BYTES", 0)
    response = client.post("/documents", files=txt_file("any content"))
    assert "detail" in response.json()

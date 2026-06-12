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
    assert doc.status == "pending"


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

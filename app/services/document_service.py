import base64
import uuid

from sqlalchemy.orm import Session

from app.models.document import Document
from app.repositories import document_repo
from app.schemas.document import DocumentListResponse, DocumentUploadResponse
from app.storage import local_storage


def upload_document(
    filename: str,
    content_type: str,
    content: bytes,
    db: Session,
) -> DocumentUploadResponse:
    document_id = str(uuid.uuid4())
    local_storage.save_file(document_id, content)

    document = Document(
        id=document_id,
        filename=filename,
        file_size=len(content),
        content_type=content_type,
        status="pending",
    )
    document_repo.create(db, document)

    # Encode content as base64 string so it passes over Redis without filesystem dependency
    content_b64 = base64.b64encode(content).decode("ascii")

    # Import here to avoid circular imports at module load time
    from app.tasks.document_tasks import process_document
    process_document.delay(document_id, content_b64)

    return DocumentUploadResponse(document_id=document_id, status="pending")


def list_documents(
    db: Session,
    page: int,
    page_size: int,
    status: str | None,
) -> DocumentListResponse:
    items, total = document_repo.list_documents(db, page, page_size, status)
    return DocumentListResponse(items=items, total=total, page=page, page_size=page_size)

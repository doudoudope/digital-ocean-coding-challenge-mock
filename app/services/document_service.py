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
    file_path = local_storage.save_file(document_id, content)

    document = Document(
        id=document_id,
        filename=filename,
        file_size=len(content),
        content_type=content_type,
        status="pending",
    )
    document_repo.create(db, document)

    # Import here to avoid circular imports at module load time
    from app.tasks.document_tasks import process_document
    process_document.delay(document_id, file_path)

    return DocumentUploadResponse(document_id=document_id, status="pending")


def list_documents(
    db: Session,
    page: int,
    page_size: int,
    status: str | None,
) -> DocumentListResponse:
    items, total = document_repo.list_documents(db, page, page_size, status)
    return DocumentListResponse(items=items, total=total, page=page, page_size=page_size)

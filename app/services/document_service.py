import uuid

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.result import DocumentResult
from app.repositories import document_repo, result_repo
from app.schemas.document import DocumentListResponse, DocumentUploadResponse
from app.services import processing_service
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

    result_data = processing_service.process(content.decode("utf-8", errors="replace"))

    result = DocumentResult(
        document_id=document_id,
        word_count=result_data["word_count"],
        line_count=result_data["line_count"],
        keywords=result_data["keywords"],
        summary=result_data["summary"],
    )
    result_repo.create(db, result)
    document_repo.update_status(db, document_id, "completed")

    return DocumentUploadResponse(document_id=document_id, status="completed")


def list_documents(
    db: Session,
    page: int,
    page_size: int,
    status: str | None,
) -> DocumentListResponse:
    items, total = document_repo.list_documents(db, page, page_size, status)
    return DocumentListResponse(items=items, total=total, page=page, page_size=page_size)

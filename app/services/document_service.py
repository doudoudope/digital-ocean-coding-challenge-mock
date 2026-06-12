import uuid

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.document import Document
from app.repositories import document_repo
from app.schemas.document import DocumentUploadResponse
from app.storage import local_storage


async def upload_document(file: UploadFile, db: Session) -> DocumentUploadResponse:
    content = await file.read()
    document_id = str(uuid.uuid4())

    local_storage.save_file(document_id, content)

    document = Document(
        id=document_id,
        filename=file.filename,
        file_size=len(content),
        content_type=file.content_type or "text/plain",
        status="pending",
    )
    document_repo.create(db, document)

    return DocumentUploadResponse(document_id=document_id, status="pending")

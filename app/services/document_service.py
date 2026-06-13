import base64
import logging
import uuid

from sqlalchemy.orm import Session

from app import cache
from app.models.document import Document
from app.repositories import document_repo, result_repo
from app.schemas.document import DocumentListResponse, DocumentUploadResponse
from app.schemas.result import DocumentResultResponse
from app.storage import local_storage

logger = logging.getLogger(__name__)

_RESULT_CACHE_TTL = 3600


def upload_document(
    filename: str,
    content_type: str,
    content: bytes,
    user_id: str,
    db: Session,
) -> DocumentUploadResponse:
    document_id = str(uuid.uuid4())
    local_storage.save_file(document_id, content)

    document = Document(
        id=document_id,
        user_id=user_id,
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


def get_result(document_id: str, db: Session) -> DocumentResultResponse | None:
    cache_key = f"result:{document_id}"
    try:
        cached = cache.redis_client.get(cache_key)
        if cached:
            logger.info("cache hit for document %s", document_id)
            return DocumentResultResponse.model_validate_json(cached)
    except Exception as exc:
        logger.warning("cache read failed, falling back to DB: %s", exc)

    result = result_repo.get_by_document_id(db, document_id)
    if result is None:
        return None

    response = DocumentResultResponse.model_validate(result)
    try:
        cache.redis_client.setex(cache_key, _RESULT_CACHE_TTL, response.model_dump_json())
        logger.info("cache set for document %s (ttl=%ds)", document_id, _RESULT_CACHE_TTL)
    except Exception as exc:
        logger.warning("cache write failed: %s", exc)

    return response


def list_documents(
    db: Session,
    page: int,
    page_size: int,
    status: str | None,
    user_id: str | None = None,
) -> DocumentListResponse:
    items, total = document_repo.list_documents(db, page, page_size, status, user_id)
    return DocumentListResponse(items=items, total=total, page=page, page_size=page_size)

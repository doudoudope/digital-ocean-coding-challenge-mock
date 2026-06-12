import logging

from app.celery_app import celery
from app.models.db import SessionLocal
from app.models.result import DocumentResult
from app.repositories import document_repo, result_repo
from app.services import processing_service

logger = logging.getLogger(__name__)


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def process_document(self, document_id: str, file_path: str) -> None:
    db = SessionLocal()
    try:
        with open(file_path, "rb") as f:
            content = f.read()

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
        logger.info("document %s processed successfully", document_id)
    except Exception as exc:
        logger.error(
            "document %s failed (attempt %d/%d): %s",
            document_id,
            self.request.retries + 1,
            self.max_retries + 1,
            exc,
        )
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60)
        document_repo.update_status(db, document_id, "failed")
    finally:
        db.close()

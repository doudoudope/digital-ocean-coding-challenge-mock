from celery import Celery

from app.config import settings

celery = Celery(
    "document_processor",
    broker=settings.redis_url,
    include=["app.tasks.document_tasks"],
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_backend=None,
    timezone="UTC",
    enable_utc=True,
)

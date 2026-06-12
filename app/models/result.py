from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text

from app.models.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DocumentResult(Base):
    __tablename__ = "document_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    word_count = Column(Integer, nullable=False)
    line_count = Column(Integer, nullable=False)
    keywords = Column(Text, nullable=False)  # JSON-serialized list
    summary = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=_utcnow)


Index("ix_document_results_document_id", DocumentResult.document_id)

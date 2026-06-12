from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.document import Document


def create(db: Session, document: Document) -> Document:
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def get_by_id(db: Session, document_id: str) -> Document | None:
    return db.query(Document).filter(Document.id == document_id).first()


def update_status(db: Session, document_id: str, status: str) -> None:
    db.query(Document).filter(Document.id == document_id).update(
        {"status": status, "updated_at": datetime.now(timezone.utc)}
    )
    db.commit()

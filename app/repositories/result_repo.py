from sqlalchemy.orm import Session

from app.models.result import DocumentResult


def create(db: Session, result: DocumentResult) -> DocumentResult:
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def get_by_document_id(db: Session, document_id: str) -> DocumentResult | None:
    return (
        db.query(DocumentResult)
        .filter(DocumentResult.document_id == document_id)
        .first()
    )

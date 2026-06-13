from sqlalchemy.orm import Session

from app.models.user import User


def get_by_api_key(db: Session, api_key: str) -> User | None:
    return db.query(User).filter(User.api_key == api_key).first()

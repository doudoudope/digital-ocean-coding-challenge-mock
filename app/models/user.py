from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, String

from app.models.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    api_key = Column(String, unique=True, nullable=False, index=True)
    tier = Column(String, nullable=False, default="free")
    email = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=_utcnow)

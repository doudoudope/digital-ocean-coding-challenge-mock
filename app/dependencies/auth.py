import logging
from datetime import date

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app import cache
from app.config import settings
from app.models.db import get_db
from app.models.document import Document
from app.repositories import document_repo, user_repo
from app.schemas.user import CurrentUser

logger = logging.getLogger(__name__)

_USER_CACHE_TTL = 300  # 5 minutes


def get_current_user(
    x_api_key: str = Header(...),
    db: Session = Depends(get_db),
) -> CurrentUser:
    try:
        raw = cache.redis_client.get(f"user:{x_api_key}")
        if raw:
            return CurrentUser.model_validate_json(raw)
    except Exception as exc:
        logger.warning("user cache read failed: %s", exc)

    user = user_repo.get_by_api_key(db, x_api_key)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")

    current_user = CurrentUser.model_validate(user)
    try:
        cache.redis_client.setex(f"user:{x_api_key}", _USER_CACHE_TTL, current_user.model_dump_json())
    except Exception as exc:
        logger.warning("user cache write failed: %s", exc)

    return current_user


def check_upload_quota(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if user.tier == "free":
        today = date.today().isoformat()
        quota_key = f"quota:{user.id}:{today}"
        try:
            count = int(cache.redis_client.get(quota_key) or 0)
            if count >= settings.free_daily_upload_limit:
                raise HTTPException(
                    status_code=429,
                    detail=f"Daily upload limit of {settings.free_daily_upload_limit} reached",
                )
        except HTTPException:
            raise
        except Exception as exc:
            logger.warning("quota check failed, allowing request: %s", exc)
    return user


def get_owned_document(
    document_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Document:
    document = document_repo.get_by_id(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return document


def increment_upload_quota(user: CurrentUser) -> None:
    if user.tier != "free":
        return
    today = date.today().isoformat()
    quota_key = f"quota:{user.id}:{today}"
    try:
        pipe = cache.redis_client.pipeline()
        pipe.incr(quota_key)
        pipe.expire(quota_key, 86400)
        pipe.execute()
    except Exception as exc:
        logger.warning("quota increment failed: %s", exc)

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.dependencies.auth import (
    check_upload_quota,
    get_current_user,
    get_owned_document,
    increment_upload_quota,
)
from app.models.db import get_db
from app.models.document import Document
from app.schemas.document import DocumentListResponse, DocumentResponse, DocumentUploadResponse
from app.schemas.result import DocumentResultResponse
from app.schemas.user import CurrentUser
from app.services import document_service

router = APIRouter(prefix="/documents")

_ALLOWED_EXTENSIONS = {".txt"}


@router.post("", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(check_upload_quota),
):
    filename = file.filename or ""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{ext}'. Only .txt files are accepted.")

    content = await file.read()
    max_mb = settings.paid_max_file_size_mb if user.tier == "paid" else settings.free_max_file_size_mb
    if len(content) > max_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File size {len(content)} bytes exceeds the {max_mb} MB limit for {user.tier} tier.",
        )

    result = document_service.upload_document(
        filename=filename,
        content_type=file.content_type or "text/plain",
        content=content,
        user_id=user.id,
        db=db,
    )
    increment_upload_quota(user)
    return result


@router.get("", response_model=DocumentListResponse)
def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    return document_service.list_documents(db, page, page_size, status, user.id)


@router.get("/{document_id}/status")
def get_status(document: Document = Depends(get_owned_document)):
    return {"status": document.status}


@router.get("/{document_id}/result", response_model=DocumentResultResponse)
def get_result(
    document: Document = Depends(get_owned_document),
    db: Session = Depends(get_db),
):
    if document.status != "completed":
        raise HTTPException(status_code=409, detail="Document processing not complete")
    result = document_service.get_result(document.id, db)
    if result is None:
        raise HTTPException(status_code=404, detail="Result not found")
    return result


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document: Document = Depends(get_owned_document)):
    return document

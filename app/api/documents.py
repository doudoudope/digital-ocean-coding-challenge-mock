from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.models.db import get_db
from app.schemas.document import DocumentUploadResponse
from app.services import document_service

router = APIRouter(prefix="/documents")


@router.post("", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    return await document_service.upload_document(file, db)

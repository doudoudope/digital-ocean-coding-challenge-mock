from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.models.db import get_db
from app.repositories import document_repo, result_repo
from app.schemas.document import DocumentUploadResponse
from app.schemas.result import DocumentResultResponse
from app.services import document_service

router = APIRouter(prefix="/documents")


@router.post("", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    return await document_service.upload_document(file, db)


@router.get("/{document_id}/result", response_model=DocumentResultResponse)
def get_result(document_id: str, db: Session = Depends(get_db)):
    document = document_repo.get_by_id(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.status != "completed":
        raise HTTPException(status_code=409, detail="Document processing not complete")
    result = result_repo.get_by_document_id(db, document_id)
    return result

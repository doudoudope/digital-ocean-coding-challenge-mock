import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.models import document as _document_models  # noqa: F401 - register with Base
from app.models.db import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Document Ingestion Service", lifespan=lifespan)

app.include_router(health_router)
app.include_router(documents_router)

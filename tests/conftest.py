import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models.db import Base, get_db

TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def mock_cache(monkeypatch):
    from unittest.mock import MagicMock
    mock = MagicMock()
    mock.get.return_value = None  # default: cache miss
    monkeypatch.setattr("app.cache.redis_client", mock)
    return mock


@pytest.fixture(autouse=True)
def celery_eager(monkeypatch):
    from app.celery_app import celery as celery_app
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    # Route the Celery task's DB session to the test database
    monkeypatch.setattr("app.tasks.document_tasks.SessionLocal", TestingSessionLocal)
    yield
    celery_app.conf.task_always_eager = False
    celery_app.conf.task_eager_propagates = False


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def tmp_upload_dir(tmp_path, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    return tmp_path

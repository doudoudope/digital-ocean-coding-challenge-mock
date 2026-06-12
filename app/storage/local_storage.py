import os

from app.config import settings


def get_file_path(document_id: str) -> str:
    return os.path.join(settings.upload_dir, f"{document_id}.txt")


def save_file(document_id: str, content: bytes) -> str:
    os.makedirs(settings.upload_dir, exist_ok=True)
    path = get_file_path(document_id)
    with open(path, "wb") as f:
        f.write(content)
    return path

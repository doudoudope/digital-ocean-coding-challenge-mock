import os

from app.config import settings


def save_file(document_id: str, content: bytes) -> str:
    os.makedirs(settings.upload_dir, exist_ok=True)
    path = os.path.join(settings.upload_dir, f"{document_id}.txt")
    with open(path, "wb") as f:
        f.write(content)
    return path

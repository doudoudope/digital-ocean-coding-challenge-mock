from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env"}

    database_url: str = "sqlite:///./documents.db"
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 10
    redis_url: str = "redis://localhost:6379/0"

    @field_validator("database_url")
    @classmethod
    def fix_postgres_scheme(cls, v: str) -> str:
        # DO injects postgres:// but SQLAlchemy 2.x requires postgresql://
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v


settings = Settings()

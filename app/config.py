from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env"}

    database_url: str = "sqlite:///./documents.db"
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 10
    redis_url: str = "redis://localhost:6379/0"


settings = Settings()

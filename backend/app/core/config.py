from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    app_name: str = "ModelOps Doctor API"
    app_description: str = (
        "A full-stack MLOps platform for model monitoring, "
        "drift detection, health scoring, and diagnosis reports."
    )
    app_version: str = "0.1.0"

    environment: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    postgres_user: str = "modelops_user"
    postgres_password: str = "modelops_password"
    postgres_db: str = "modelops_doctor"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    celery_task_always_eager: bool = False

    storage_path: str = "./storage"
    mlflow_tracking_uri: str = "http://localhost:5000"

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:"
            f"{self.postgres_password}@{self.postgres_host}:"
            f"{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

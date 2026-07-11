from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

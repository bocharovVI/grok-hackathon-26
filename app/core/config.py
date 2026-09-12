from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Literal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg2://medical:medical@localhost:5432/medical_history"
    cors_origins: list[str] = ["http://localhost:5173"]
    public_api_url: str = "http://localhost:8000"
    xai_api_key: str = ""
    xai_model: str = "grok-4.6"
    xai_timeout_seconds: float = Field(default=300, gt=0, le=300)
    xai_reasoning_effort: Literal["", "low", "medium", "high", "xhigh"] = "low"
    max_upload_bytes: int = Field(default=10 * 1024 * 1024, gt=0)
    max_pdf_pages: int = Field(default=10, ge=1, le=20)
    session_days: int = Field(default=7, ge=1)

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return "postgresql+psycopg2://" + value[len(prefix):]
        return value


settings = Settings()

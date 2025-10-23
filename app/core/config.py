from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any

from pydantic import Field, HttpUrl, PostgresDsn, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration sourced from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    app_name: str = Field("AI-Powered Recommendation Engine", description="Human readable app name.")
    environment: str = Field("development", description="Runtime environment identifier.")
    debug: bool = Field(False, description="Enable FastAPI debug mode.")
    api_v1_prefix: str = Field("/api/v1", description="Prefix for versioned API routes.")
    docs_url: str | None = Field("/docs", description="Swagger UI path; set None to disable.")
    redoc_url: str | None = Field("/redoc", description="ReDoc path; set None to disable.")
    openapi_url: str | None = Field("/openapi.json", description="OpenAPI schema path.")

    secret_key: str = Field("change-me-super-secret", description="JWT signing secret.")
    access_token_expires_minutes: int = Field(30, ge=5, description="Access token lifetime in minutes.")
    refresh_token_expires_minutes: int = Field(60 * 24 * 7, ge=60, description="Refresh token lifetime in minutes.")

    backend_cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost", "http://localhost:8000"],
        description="Allowed CORS origins for browser clients.",
    )
    trusted_hosts: list[str] = Field(
        default_factory=lambda: ["*"],
        description="List of trusted hostnames for ASGI TrustedHostMiddleware.",
    )

    database_url: PostgresDsn = Field(
        "postgresql+asyncpg://app:app@postgres:5432/ai_recs",
        description="Primary PostgreSQL DSN (asyncpg driver).",
    )
    sync_database_url: PostgresDsn = Field(
        "postgresql+psycopg://app:app@postgres:5432/ai_recs",
        description="Synchronous PostgreSQL DSN for Alembic migrations.",
    )
    redis_url: Annotated[str, Field(pattern=r"^redis://.+")] = Field(
        "redis://redis:6379/0", description="Redis connection URL."
    )

    celery_broker_url: str = Field("redis://redis:6379/1", description="Celery broker URL.")
    celery_result_backend: str = Field("redis://redis:6379/2", description="Celery result backend URL.")

    prometheus_multiproc_dir: Path = Field(
        Path("/tmp/prometheus"),
        description="Directory for Prometheus multiprocess metrics.",
    )

    otlp_endpoint: HttpUrl | None = Field(
        None,
        description="Optional OTLP endpoint for OpenTelemetry exporters.",
    )

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, value: Any, info: ValidationInfo) -> list[str]:
        """
        Ensure CORS origins are normalized to a list, supporting comma-separated strings.
        """

        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        if isinstance(value, list):
            return value
        raise ValueError("backend_cors_origins must be a list or a comma separated string.")


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""

    return Settings()


settings = get_settings()

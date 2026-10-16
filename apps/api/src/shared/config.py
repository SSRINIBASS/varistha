"""Application settings and configuration."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Varistha API configuration loaded from environment or .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = (
        "postgresql+asyncpg://varistha:varistha_dev_password@localhost:5432/varistha"
    )
    secret_key: str = "dev-secret-key-change-in-production"  # noqa: S105
    encryption_key: str | None = None
    environment: str = "development"
    log_level: str = "info"
    auth_enabled: bool = False


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()

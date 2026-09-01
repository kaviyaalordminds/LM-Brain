"""
Planner Agent — Configuration

Uses pydantic-settings for environment-aware configuration.
No secrets are ever logged.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Service identity
    service_name: str = "planner"
    service_version: str = "1.0.0"

    # Server
    host: str = "127.0.0.1"
    port: int = 8002
    debug: bool = False

    # Logging
    log_level: str = "INFO"

    # Planning defaults
    default_max_retries: int = 2
    default_retry_allowed: bool = True


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

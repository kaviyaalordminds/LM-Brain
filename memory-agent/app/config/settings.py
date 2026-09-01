"""
Memory Agent — Configuration

All settings are read from environment variables.
No secrets are ever hardcoded here.

Usage:
    from app.config.settings import get_settings
    settings = get_settings()
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings, resolved from environment variables.
    Defaults are safe for local development with mock adapters.
    """

    # ── Application ────────────────────────────────────────────────────────
    app_env: str = Field(default="development", description="development | staging | production")
    log_level: str = Field(default="INFO", description="DEBUG | INFO | WARNING | ERROR")

    # ── Obsidian Adapter ───────────────────────────────────────────────────
    # Options: 'mock', 'local', or 'real'
    obsidian_adapter: str = Field(
        default="mock",
        description="Adapter type: 'mock', 'local', or 'real'",
    )
    obsidian_vault_path: str = Field(
        default="",
        description="Absolute path to the company Obsidian vault (used when obsidian_adapter=local or real)",
    )

    # ── Research Provider ──────────────────────────────────────────────────
    research_provider: str = Field(
        default="mock",
        description="Provider type: 'mock' or 'jina'",
    )
    # Never log this value.
    research_api_key: str = Field(
        default="",
        description="API key for the external research provider (never log this)",
    )
    research_timeout_seconds: int = Field(
        default=30,
        description="Timeout in seconds for external research calls",
    )

    # ── Server ─────────────────────────────────────────────────────────────
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8001)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()

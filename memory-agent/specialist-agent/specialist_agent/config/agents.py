"""
Specialist Agent — Environment-Driven Settings

All configuration is read from environment variables.
No secrets are ever hardcoded here.
Missing providers produce controlled "not configured" states.

Environment variables:
  SPECIALIST_ENV           — development | staging | production
  MEMORY_AGENT_URL         — Memory Agent base URL (default: http://localhost:8001)
  IMAGE_MODEL_PROVIDER     — Provider name for image generation (e.g. comfyui, dalle)
  IMAGE_MODEL_NAME         — Model name for image generation
  IMAGE_MODEL_ENDPOINT     — Endpoint URL for image model
  CODE_MODEL_PROVIDER      — Provider name for code/LLM (e.g. ollama, openai)
  CODE_MODEL_NAME          — Model name for coding tasks
  CODE_MODEL_ENDPOINT      — Endpoint URL for code model
  SPECIALIST_MAX_RETRIES   — Default max retries (default: 2)
  SPECIALIST_TIMEOUT       — Default task timeout in seconds (default: 300)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class SpecialistSettings:
    """Environment-driven settings for the Specialist Agent layer."""

    # Application environment
    env: str = "development"

    # Memory Agent connection
    memory_agent_url: str = "http://localhost:8001"
    memory_agent_timeout: int = 30

    # Image model configuration (optional)
    image_model_provider: str = ""
    image_model_name: str = ""
    image_model_endpoint: str = ""

    # Code/LLM model configuration (optional)
    code_model_provider: str = ""
    code_model_name: str = ""
    code_model_endpoint: str = ""

    # Default execution constraints
    default_max_retries: int = 2
    default_timeout_seconds: int = 300

    # ── Computed properties ─────────────────────────────────────────────

    @property
    def image_model_configured(self) -> bool:
        """True only if all three image model fields are non-empty."""
        return bool(
            self.image_model_provider.strip()
            and self.image_model_endpoint.strip()
        )

    @property
    def code_model_configured(self) -> bool:
        """True only if all three code model fields are non-empty."""
        return bool(
            self.code_model_provider.strip()
            and self.code_model_endpoint.strip()
        )


@lru_cache(maxsize=1)
def get_specialist_settings() -> SpecialistSettings:
    """Return cached environment-driven settings. No values are hardcoded."""
    return SpecialistSettings(
        env=os.getenv("SPECIALIST_ENV", "development"),
        memory_agent_url=os.getenv("MEMORY_AGENT_URL", "http://localhost:8001"),
        memory_agent_timeout=int(os.getenv("MEMORY_AGENT_TIMEOUT", "30")),
        image_model_provider=os.getenv("IMAGE_MODEL_PROVIDER", ""),
        image_model_name=os.getenv("IMAGE_MODEL_NAME", ""),
        image_model_endpoint=os.getenv("IMAGE_MODEL_ENDPOINT", ""),
        code_model_provider=os.getenv("CODE_MODEL_PROVIDER", ""),
        code_model_name=os.getenv("CODE_MODEL_NAME", ""),
        code_model_endpoint=os.getenv("CODE_MODEL_ENDPOINT", ""),
        default_max_retries=int(os.getenv("SPECIALIST_MAX_RETRIES", "2")),
        default_timeout_seconds=int(os.getenv("SPECIALIST_TIMEOUT", "300")),
    )

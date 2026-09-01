"""
Memory Agent — FastAPI Application Entry Point

Wires together all components:
  - Settings
  - Obsidian adapter (mock or real, based on config)
  - Research provider (mock or real, based on config)
  - Core services
  - MemoryAgent
  - API routes
  - Structured logging
"""

from __future__ import annotations

import logging
import logging.config
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.adapters.obsidian_adapter import LocalObsidianAdapter, MockObsidianAdapter, ObsidianAdapter
from app.adapters.research_provider import JinaResearchProvider, MockResearchProvider, ResearchProvider
from app.api.routes.memory import router as memory_router
from app.config.settings import get_settings
from app.core.memory_agent import MemoryAgent
from app.core.memory_writer import MemoryWriter
from app.core.research import ResearchService
from app.core.retrieval import RetrievalService
from app.core.validation import ValidationLayer

settings = get_settings()


# ─────────────────────────────────────────────────────────────────────────────
# Logging configuration
# ─────────────────────────────────────────────────────────────────────────────


def configure_logging() -> None:
    """Configure structured logging. Never logs secrets."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        stream=sys.stdout,
    )
    # Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


# ─────────────────────────────────────────────────────────────────────────────
# Adapter factory
# ─────────────────────────────────────────────────────────────────────────────


def build_obsidian_adapter() -> ObsidianAdapter:
    """
    Return the correct ObsidianAdapter based on configuration.

    # INTEGRATION POINT
    When settings.obsidian_adapter in ("local", "real"), LocalObsidianAdapter
    indexes and searches the local Markdown vault files (*.md).
    """
    adapter_mode = settings.obsidian_adapter.lower()
    if adapter_mode in ("local", "real"):
        return LocalObsidianAdapter(vault_path=settings.obsidian_vault_path)
    return MockObsidianAdapter()


def build_research_provider() -> ResearchProvider:
    """
    Return the correct ResearchProvider based on configuration.

    Supports:
      - 'mock': MockResearchProvider (in-memory test provider)
      - 'jina' / 'web': JinaResearchProvider (real external web & reader research)
    """
    provider_mode = settings.research_provider.lower().strip()
    if provider_mode in ("jina", "web"):
        if not settings.research_api_key or not settings.research_api_key.strip():
            raise ValueError(
                "RESEARCH_API_KEY is required when RESEARCH_PROVIDER=jina. "
                "Please configure RESEARCH_API_KEY in .env or environment variables."
            )
        return JinaResearchProvider(
            api_key=settings.research_api_key,
            timeout_seconds=float(settings.research_timeout_seconds),
        )
    elif provider_mode == "mock":
        return MockResearchProvider()
    else:
        raise ValueError(
            f"Unsupported RESEARCH_PROVIDER='{settings.research_provider}'. "
            f"Supported options are: 'mock', 'jina'."
        )


# ─────────────────────────────────────────────────────────────────────────────
# Application lifecycle
# ─────────────────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialise and tear down application components."""
    configure_logging()
    logger = logging.getLogger(__name__)
    logger.info(
        "memory_agent.startup",
        extra={
            "env": settings.app_env,
            "obsidian_adapter": settings.obsidian_adapter,
            "research_provider": settings.research_provider,
        },
    )

    # Build adapters
    obsidian = build_obsidian_adapter()
    research_provider = build_research_provider()

    # Build core services
    retrieval = RetrievalService()
    research_svc = ResearchService(provider=research_provider)
    validation = ValidationLayer()
    writer = MemoryWriter(obsidian=obsidian)

    # Build Memory Agent and store in app state
    app.state.memory_agent = MemoryAgent(
        obsidian=obsidian,
        retrieval=retrieval,
        research_svc=research_svc,
        validation=validation,
        writer=writer,
    )

    logger.info("memory_agent.ready")
    yield

    logger.info("memory_agent.shutdown")


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI application
# ─────────────────────────────────────────────────────────────────────────────


def create_app() -> FastAPI:
    app = FastAPI(
        title="Memory Agent",
        description=(
            "Knowledge layer for the Autonomous AI Workforce. "
            "Provides Obsidian search, controlled external research, "
            "evidence validation, and approved-only memory write."
        ),
        version="0.1.0",
        lifespan=lifespan,
        # Serialise all response models using field aliases (camelCase)
        response_model_by_alias=True,
    )

    # CORS — restrict in production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.app_env == "development" else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Memory routes
    app.include_router(memory_router)

    # Health check
    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "memory-agent"}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.app_env == "development",
    )

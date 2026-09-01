"""
Planner Agent — FastAPI Application

Production-ready service entrypoint.
Base routes mounted at /api/v1.
Interactive API documentation available at /docs and /openapi.json.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.planning import router as api_router
from app.config.settings import get_settings
from app.models.plan import ErrorResponse

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("planner.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    logger.info("Planner Agent starting up (service=%s, version=%s)", settings.service_name, settings.service_version)
    yield
    logger.info("Planner Agent shutting down")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Planner Agent API",
        version=settings.service_version,
        description=(
            "Autonomous AI Workforce — Planner Agent Service.\n\n"
            "Receives natural-language user requests and produces validated, "
            "dependency-resolved execution plans for the Master Orchestrator."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        openapi_url="/openapi.json",
        redoc_url="/redoc",
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -----------------------------------------------------------------------
    # Exception Handlers
    # -----------------------------------------------------------------------

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle Pydantic validation errors with structured 422 response."""
        errors = []
        for err in exc.errors():
            loc = " -> ".join(str(l) for l in err.get("loc", []))
            msg = err.get("msg", "Invalid value")
            errors.append(f"{loc}: {msg}")

        logger.warning("Validation error on %s: %s", request.url.path, errors)
        payload = ErrorResponse(
            error_code="INVALID_REQUEST",
            message="Request validation failed.",
            details=errors,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=payload.model_dump(by_alias=True),
        )

    # Mount API routes
    app.include_router(api_router)

    return app


app = create_app()

"""
Memory Agent — API Routes

Thin HTTP layer over the MemoryAgent service.
No business logic lives here — only request validation, delegation, and error translation.

Endpoints:
  POST /api/v1/memory/search
  POST /api/v1/memory/research
  POST /api/v1/memory/validate
  POST /api/v1/memory/write
  GET  /api/v1/memory/context/{taskId}
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.adapters.obsidian_adapter import ObsidianAdapterError
from app.adapters.research_provider import ResearchProviderError, ResearchTimeoutError
from app.core.memory_agent import MemoryAgent, MemoryAgentError
from app.core.memory_writer import DuplicateKnowledgeError, WriteRejectedError
from app.core.research import ResearchError
from app.models.memory import (
    ApprovalStatus,
    ContextResponse,
    ErrorResponse,
    ResearchRequest,
    ResearchResponse,
    SearchRequest,
    SearchResponse,
    ValidateRequest,
    ValidateResponse,
    WriteRequest,
    WriteResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/memory", tags=["memory"])


# ─────────────────────────────────────────────────────────────────────────────
# Dependency: resolve MemoryAgent from app state
# ─────────────────────────────────────────────────────────────────────────────


def get_memory_agent(request: Request) -> MemoryAgent:
    """Retrieve the MemoryAgent singleton from FastAPI app state."""
    agent: MemoryAgent | None = getattr(request.app.state, "memory_agent", None)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Memory Agent not initialised.",
        )
    return agent


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/memory/search
# ─────────────────────────────────────────────────────────────────────────────


@router.post(
    "/search",
    response_model=SearchResponse,
    response_model_by_alias=True,
    summary="Search internal Obsidian knowledge base",
)
async def search_memory(
    body: SearchRequest,
    agent: MemoryAgent = Depends(get_memory_agent),
) -> SearchResponse:
    """
    Search the internal Obsidian/company knowledge base.
    If auto_research=True and knowledge gaps exist, automatically research, validate,
    write to Obsidian, and return enriched knowledge.
    """
    try:
        if body.auto_research:
            return await agent.search_or_research(
                query=body.query,
                task_id=body.task_id,
            )
        return await agent.search(
            query=body.query,
            task_id=body.task_id,
            context=body.context,
            filters=body.filters or None,
            task_scope=body.task_scope,
        )
    except MemoryAgentError as exc:
        logger.error("api.memory.search.error", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("api.memory.search.unexpected")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during memory search: {exc}",
        )


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/memory/research
# ─────────────────────────────────────────────────────────────────────────────


@router.post(
    "/research",
    response_model=ResearchResponse,
    summary="Controlled external research",
)
async def research_memory(
    body: ResearchRequest,
    agent: MemoryAgent = Depends(get_memory_agent),
) -> ResearchResponse:
    """
    Initiate controlled external research.
    """
    try:
        return await agent.research(
            query=body.query,
            task_id=body.task_id,
            task_scope=body.task_scope,
        )
    except ResearchError as exc:
        logger.warning("api.memory.research.error", extra={"error": str(exc)})
        if "timed out" in str(exc).lower():
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=str(exc),
            )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("api.memory.research.unexpected")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during research: {exc}",
        )


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/memory/validate
# ─────────────────────────────────────────────────────────────────────────────


@router.post(
    "/validate",
    response_model=ValidateResponse,
    summary="Validate evidence before trusting it",
)
async def validate_memory(
    body: ValidateRequest,
    agent: MemoryAgent = Depends(get_memory_agent),
) -> ValidateResponse:
    """
    Validate a list of evidence items using deterministic rules.
    """
    try:
        result = agent.validate(
            evidence=body.evidence,
            query=body.query,
            context=body.context,
        )
        return ValidateResponse(
            status=result.status,
            reason=result.reason,
            approved=result.approved,
            assessment=result.assessment,
        )
    except Exception as exc:
        logger.exception("api.memory.validate.unexpected")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during validation: {exc}",
        )


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/memory/write
# ─────────────────────────────────────────────────────────────────────────────


@router.post(
    "/write",
    response_model=WriteResponse,
    summary="Write approved knowledge to Obsidian",
)
async def write_memory(
    body: WriteRequest,
    agent: MemoryAgent = Depends(get_memory_agent),
) -> WriteResponse:
    """
    Write approved content to the Obsidian knowledge base.
    """
    try:
        try:
            approval = ApprovalStatus(body.approval_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid approvalStatus value: '{body.approval_status}'.",
            )

        return await agent.write(
            content=body.content,
            evidence_refs=body.evidence_refs,
            approval_status=approval,
            target_note=body.target_note,
            task_id=body.task_id,
        )
    except HTTPException:
        raise
    except ObsidianAdapterError as exc:
        logger.error("api.memory.write.adapter_error", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Obsidian unavailable: {exc}",
        )
    except Exception as exc:
        logger.exception("api.memory.write.unexpected")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during write: {exc}",
        )


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/memory/context/{taskId}
# ─────────────────────────────────────────────────────────────────────────────


@router.get(
    "/context/{taskId}",
    response_model=ContextResponse,
    summary="Retrieve memory context for a task",
)
async def get_context(
    taskId: str,
    agent: MemoryAgent = Depends(get_memory_agent),
) -> ContextResponse:
    """
    Return all cached memory context for the given task ID.
    """
    try:
        return await agent.retrieve_context(taskId)
    except Exception as exc:
        logger.exception("api.memory.context.unexpected")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error retrieving context: {exc}",
        )

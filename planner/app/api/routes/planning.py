"""
Planner Agent — API Routes

REST endpoints for plan generation, retrieval, validation, status, and health.
Base path: /api/v1
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.core.store import BasePlanStore, InMemoryPlanStore
from app.models.plan import (
    ErrorResponse,
    HealthResponse,
    Plan,
    PlanRequest,
    PlanStatus,
    PlanStatusResponse,
    PlanValidationResponse,
    StepStatus,
)
from app.planner import Planner

logger = logging.getLogger("planner.api")

router = APIRouter(prefix="/api/v1", tags=["planning"])

# Shared singleton store and planner instance
_store = InMemoryPlanStore()
_planner = Planner(store=_store)


def get_planner() -> Planner:
    return _planner


def get_store() -> BasePlanStore:
    return _store


# ---------------------------------------------------------------------------
# Health Endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns service name, status, and version.",
)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service="planner", version="1.0.0")


# ---------------------------------------------------------------------------
# Create Plan Endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/plans",
    response_model=Plan,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new execution plan",
    description="Accepts a natural-language request, decomposes it, assigns specialists, and builds a validated DAG.",
    responses={
        201: {"description": "Plan created successfully."},
        422: {"model": ErrorResponse, "description": "Validation error in request payload."},
        400: {"model": ErrorResponse, "description": "Planning error or invalid DAG."},
    },
)
async def create_plan(
    request: PlanRequest,
    planner: Annotated[Planner, Depends(get_planner)],
) -> Plan:
    try:
        plan = planner.create_plan(request)
        return plan
    except ValueError as e:
        logger.warning("Invalid planning request: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Unexpected error during plan creation: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal planning error.",
        )


# ---------------------------------------------------------------------------
# Get Plan Endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/plans/{plan_id}",
    response_model=Plan,
    summary="Retrieve a plan by ID",
    description="Returns the full Plan object including all steps, dependencies, parallel groups, and verification criteria.",
    responses={
        200: {"description": "Plan found."},
        404: {"model": ErrorResponse, "description": "Plan not found."},
    },
)
async def get_plan(
    plan_id: Annotated[str, Path(description="Unique plan identifier")],
    planner: Annotated[Planner, Depends(get_planner)],
) -> Plan:
    plan = planner.get_plan(plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan '{plan_id}' not found.",
        )
    return plan


# ---------------------------------------------------------------------------
# Validate Existing Plan Endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/plans/{plan_id}/validate",
    response_model=PlanValidationResponse,
    summary="Validate an existing plan",
    description="Re-checks all 15 structural validation rules against a stored plan.",
    responses={
        200: {"description": "Validation completed."},
        404: {"model": ErrorResponse, "description": "Plan not found."},
    },
)
async def validate_plan_endpoint(
    plan_id: Annotated[str, Path(description="Unique plan identifier")],
    planner: Annotated[Planner, Depends(get_planner)],
) -> PlanValidationResponse:
    plan = planner.get_plan(plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan '{plan_id}' not found.",
        )
    is_valid, errors = planner.validate_existing_plan(plan_id)
    return PlanValidationResponse(
        plan_id=plan_id,
        valid=is_valid,
        status=plan.status,
        errors=errors,
        warnings=[],
    )


# ---------------------------------------------------------------------------
# Plan Status Endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/plans/{plan_id}/status",
    response_model=PlanStatusResponse,
    summary="Get plan status and progress summary",
    description="Returns high-level status, step count, completed step count, and any validation errors.",
    responses={
        200: {"description": "Status retrieved."},
        404: {"model": ErrorResponse, "description": "Plan not found."},
    },
)
async def get_plan_status(
    plan_id: Annotated[str, Path(description="Unique plan identifier")],
    planner: Annotated[Planner, Depends(get_planner)],
) -> PlanStatusResponse:
    plan = planner.get_plan(plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan '{plan_id}' not found.",
        )
    completed = sum(1 for s in plan.steps if s.status == StepStatus.COMPLETED)
    failed = sum(1 for s in plan.steps if s.status == StepStatus.FAILED)

    return PlanStatusResponse(
        plan_id=plan.plan_id,
        request_id=plan.request_id,
        status=plan.status,
        step_count=len(plan.steps),
        completed_steps=completed,
        failed_steps=failed,
        validation_errors=plan.validation_errors,
    )

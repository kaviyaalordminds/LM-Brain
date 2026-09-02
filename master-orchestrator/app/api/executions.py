import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional

from app.dependencies import get_orchestrator

router = APIRouter()

class CreateExecutionRequest(BaseModel):
    user_request: str
    context: dict = {}

@router.post("/api/v1/executions", status_code=202)
async def create_execution(req: CreateExecutionRequest, background_tasks: BackgroundTasks):
    orchestrator = get_orchestrator()
    execution = await orchestrator.create_execution(
        user_request=req.user_request,
        context=req.context
    )
    # Launch planning and execution in background
    background_tasks.add_task(orchestrator.start_execution, execution.execution_id)
    return {
        "execution_id": execution.execution_id,
        "status": execution.status.value if hasattr(execution.status, "value") else str(execution.status)
    }

@router.get("/api/v1/executions/{execution_id}")
async def get_execution(execution_id: str):
    orchestrator = get_orchestrator()
    execution = await orchestrator.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    return execution.model_dump(mode="json")

@router.get("/api/v1/executions/{execution_id}/status")
async def get_execution_status(execution_id: str):
    orchestrator = get_orchestrator()
    execution = await orchestrator.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    return {
        "execution_id": execution.execution_id,
        "status": execution.status.value if hasattr(execution.status, "value") else str(execution.status),
        "phase": execution.phase.value if hasattr(execution.phase, "value") else str(execution.phase),
        "plan_id": execution.plan_id,
        "plan_version": execution.plan_version,
        "completed_steps": execution.completed_steps,
        "failed_steps": execution.failed_steps,
        "blocked_steps": execution.blocked_steps,
        "running_steps": execution.running_steps,
        "pending_steps": execution.pending_steps,
        "error": execution.error
    }

@router.get("/api/v1/executions/{execution_id}/events")
async def get_execution_events(execution_id: str):
    orchestrator = get_orchestrator()
    events = await orchestrator.get_events(execution_id)
    return [e.model_dump(mode="json") if hasattr(e, "model_dump") else e for e in events]


from fastapi import APIRouter, HTTPException
from app.dependencies import get_orchestrator

router = APIRouter()

@router.post("/api/v1/executions/{execution_id}/pause")
async def pause_execution(execution_id: str):
    orchestrator = get_orchestrator()
    execution = await orchestrator.pause(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    return {
        "execution_id": execution.execution_id,
        "status": execution.status.value if hasattr(execution.status, "value") else str(execution.status)
    }

@router.post("/api/v1/executions/{execution_id}/resume")
async def resume_execution(execution_id: str):
    orchestrator = get_orchestrator()
    execution = await orchestrator.resume(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    return {
        "execution_id": execution.execution_id,
        "status": execution.status.value if hasattr(execution.status, "value") else str(execution.status)
    }

@router.post("/api/v1/executions/{execution_id}/cancel")
async def cancel_execution(execution_id: str):
    orchestrator = get_orchestrator()
    execution = await orchestrator.cancel(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    return {
        "execution_id": execution.execution_id,
        "status": execution.status.value if hasattr(execution.status, "value") else str(execution.status)
    }


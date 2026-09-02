from fastapi import APIRouter

router = APIRouter()

@router.post("/api/v1/executions/{execution_id}/pause")
async def pause_execution(execution_id: str):
    return {"status": "PAUSED"}

@router.post("/api/v1/executions/{execution_id}/resume")
async def resume_execution(execution_id: str):
    return {"status": "RUNNING"}

@router.post("/api/v1/executions/{execution_id}/cancel")
async def cancel_execution(execution_id: str):
    return {"status": "CANCELLED"}

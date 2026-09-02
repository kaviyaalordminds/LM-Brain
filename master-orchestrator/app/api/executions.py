from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class CreateExecutionRequest(BaseModel):
    user_request: str
    context: dict = {}

@router.post("/api/v1/executions", status_code=202)
async def create_execution(req: CreateExecutionRequest):
    return {"execution_id": "exec-123", "status": "CREATED"}

@router.get("/api/v1/executions/{execution_id}")
async def get_execution(execution_id: str):
    return {"execution_id": execution_id, "status": "CREATED"}

@router.get("/api/v1/executions/{execution_id}/status")
async def get_execution_status(execution_id: str):
    return {"status": "CREATED"}

@router.get("/api/v1/executions/{execution_id}/events")
async def get_execution_events(execution_id: str):
    return []

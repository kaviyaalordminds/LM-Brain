from fastapi import APIRouter, Response, status
from app.dependencies import get_orchestrator

router = APIRouter()

@router.get("/api/v1/health")
@router.get("/health")
async def health():
    return {"status": "healthy", "service": "master-orchestrator"}

@router.get("/api/v1/ready")
@router.get("/ready")
async def ready(response: Response):
    orchestrator = get_orchestrator()
    planner_ok = await orchestrator.planner.check_health()
    memory_ok = await orchestrator.engine.memory_client.check_health()
    
    is_ready = planner_ok and memory_ok
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        
    return {
        "status": "ready" if is_ready else "not_ready",
        "dependencies": {
            "planner": "up" if planner_ok else "down",
            "memory": "up" if memory_ok else "down"
        }
    }


from fastapi import APIRouter

router = APIRouter()

@router.get("/api/v1/health")
async def health():
    return {"status": "healthy", "services": {}}

@router.get("/api/v1/ready")
async def ready():
    return {"status": "ready"}

from fastapi import FastAPI
from app.api.executions import router as executions_router
from app.api.control import router as control_router
from app.api.health import router as health_router

app = FastAPI(title="Master Orchestrator")

app.include_router(executions_router)
app.include_router(control_router)
app.include_router(health_router)

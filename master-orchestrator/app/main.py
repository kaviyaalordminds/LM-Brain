from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.executions import router as executions_router
from app.api.control import router as control_router
from app.api.health import router as health_router
from app.api.metrics import router as metrics_router
from app.dependencies import get_orchestrator

app = FastAPI(title="Master Orchestrator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(executions_router)
app.include_router(control_router)
app.include_router(health_router)
app.include_router(metrics_router)

@app.on_event("startup")
async def on_startup():
    orchestrator = get_orchestrator()
    recovered = await orchestrator.recover_interrupted_workflows()
    if recovered:
        import logging
        logging.info(f"[CRASH_RECOVERY] Interrupted workflows recovered: {recovered}")



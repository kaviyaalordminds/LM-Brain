from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from app.dependencies import get_orchestrator
from app.models.execution import ExecutionStatus

router = APIRouter()

@router.get("/metrics", response_class=PlainTextResponse)
async def get_metrics():
    """
    Exposes clean operational Prometheus-compatible metrics without external agents.
    """
    orchestrator = get_orchestrator()
    executions = orchestrator.repo.list_executions(limit=1000)

    total_executions = len(executions)
    completed = sum(1 for e in executions if e.status == ExecutionStatus.COMPLETED)
    failed = sum(1 for e in executions if e.status == ExecutionStatus.FAILED)
    cancelled = sum(1 for e in executions if e.status == ExecutionStatus.CANCELLED)
    active = sum(1 for e in executions if e.status in (ExecutionStatus.RUNNING, ExecutionStatus.PLANNING, ExecutionStatus.RECOVERING))

    total_steps = sum(len(e.completed_steps) + len(e.failed_steps) + len(e.running_steps) for e in executions)
    completed_steps = sum(len(e.completed_steps) for e in executions)
    failed_steps = sum(len(e.failed_steps) for e in executions)

    lines = [
        "# HELP executions_total Total number of executions registered in the orchestrator",
        "# TYPE executions_total counter",
        f"executions_total {total_executions}",
        "# HELP executions_completed Total number of successfully completed executions",
        "# TYPE executions_completed counter",
        f"executions_completed {completed}",
        "# HELP executions_failed Total number of failed executions",
        "# TYPE executions_failed counter",
        f"executions_failed {failed}",
        "# HELP executions_cancelled Total number of cancelled executions",
        "# TYPE executions_cancelled counter",
        f"executions_cancelled {cancelled}",
        "# HELP executions_active Current number of active executions",
        "# TYPE executions_active gauge",
        f"executions_active {active}",
        "# HELP steps_total Total number of steps scheduled across all workflows",
        "# TYPE steps_total counter",
        f"steps_total {total_steps}",
        "# HELP steps_completed Total number of steps verified and completed",
        "# TYPE steps_completed counter",
        f"steps_completed {completed_steps}",
        "# HELP steps_failed Total number of steps failed",
        "# TYPE steps_failed counter",
        f"steps_failed {failed_steps}",
    ]
    return "\n".join(lines) + "\n"

import asyncio
import datetime
import uuid
from typing import Any, Dict, List, Optional

from app.models.execution import Execution, ExecutionStatus, ExecutionPhase
from app.models.events import ExecutionEvent, EventType
from app.policies.failure_policy import FailureType

class MasterOrchestrator:
    """
    Central Autonomous Control Plane of the Multi-Agent AI Workforce.
    Coordinates lifecycle, planning delegation, DAG scheduling, specialist execution,
    verification, artifact lineage, audit events, and persistence.
    """

    def __init__(self, repo, engine, planner, event_store=None, event_bus=None, replanner=None):
        self.repo = repo
        self.engine = engine
        self.planner = planner
        self.event_store = event_store
        self.event_bus = event_bus
        self.replanner = replanner
        self._background_tasks: Dict[str, asyncio.Task] = {}

    def _emit_event(
        self,
        event_type: EventType,
        execution: Execution,
        step_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> ExecutionEvent:
        event = ExecutionEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            execution_id=execution.execution_id,
            plan_id=execution.plan_id,
            plan_version=execution.plan_version,
            step_id=step_id,
            correlation_id=execution.correlation_id,
            timestamp=datetime.datetime.utcnow().isoformat(),
            payload=payload or {}
        )
        if self.event_store:
            self.event_store.append(event)
        if self.event_bus:
            self.event_bus.publish(event)
        return event

    async def create_execution(self, user_request: str, context: dict = None) -> Execution:
        exec_id = str(uuid.uuid4())
        req_id = str(uuid.uuid4())
        now = datetime.datetime.utcnow().isoformat()
        
        execution = Execution(
            execution_id=exec_id,
            request_id=req_id,
            user_request=user_request,
            status=ExecutionStatus.CREATED,
            phase=ExecutionPhase.INTENT_NORMALIZATION,
            created_at=now,
            updated_at=now,
            correlation_id=exec_id,
            metadata={"context": context or {}}
        )
        self.repo.save_execution(execution)
        self._emit_event(EventType.EXECUTION_CREATED, execution, payload={"user_request": user_request})
        return execution

    async def start_execution(self, execution_id: str) -> None:
        """
        Orchestrates planning via Planner, saves plan, and launches DAG execution in the background.
        """
        execution = self.repo.get_execution(execution_id)
        if not execution:
            return

        # 1. Planning phase
        execution.status = ExecutionStatus.PLANNING
        execution.phase = ExecutionPhase.PLANNING
        execution.updated_at = datetime.datetime.utcnow().isoformat()
        self.repo.update_execution(execution)
        self._emit_event(EventType.PLAN_REQUESTED, execution)

        try:
            plan = await self.planner.create_plan(
                user_request=execution.user_request,
                context=execution.metadata.get("context", {}),
                request_id=execution.request_id
            )
        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.phase = ExecutionPhase.FINALIZING
            execution.error = f"Planning failed: {str(e)}"
            execution.updated_at = datetime.datetime.utcnow().isoformat()
            self.repo.update_execution(execution)
            self._emit_event(EventType.EXECUTION_FAILED, execution, payload={"error": execution.error})
            return

        plan_id = plan.get("plan_id") or plan.get("planId") or f"plan-{uuid.uuid4()}"
        execution.plan_id = plan_id
        execution.plan_version = 1
        execution.status = ExecutionStatus.PLANNED
        execution.updated_at = datetime.datetime.utcnow().isoformat()
        self.repo.save_plan_version(plan)
        self.repo.update_execution(execution)
        self._emit_event(EventType.PLAN_RECEIVED, execution, payload={"plan_id": plan_id, "step_count": len(plan.get("steps", []))})

        # 2. Launch background execution task
        task = asyncio.create_task(self._run_workflow(execution_id, plan))
        self._background_tasks[execution_id] = task

    async def _run_workflow(self, execution_id: str, plan: dict):
        try:
            result = await self.engine.run(execution_id, plan)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            execution = self.repo.get_execution(execution_id)
            if execution:
                execution.status = ExecutionStatus.FAILED
                execution.error = str(e)
                execution.updated_at = datetime.datetime.utcnow().isoformat()
                self.repo.update_execution(execution)
                self._emit_event(EventType.EXECUTION_FAILED, execution, payload={"error": str(e)})

    async def pause(self, execution_id: str) -> Optional[Execution]:
        execution = self.repo.get_execution(execution_id)
        if execution and execution.status in (ExecutionStatus.RUNNING, ExecutionStatus.PLANNING, ExecutionStatus.CREATED):
            execution.status = ExecutionStatus.PAUSED
            execution.updated_at = datetime.datetime.utcnow().isoformat()
            self.repo.update_execution(execution)
            self._emit_event(EventType.EXECUTION_PAUSED, execution)
        return execution

    async def resume(self, execution_id: str) -> Optional[Execution]:
        execution = self.repo.get_execution(execution_id)
        if execution and execution.status == ExecutionStatus.PAUSED:
            execution.status = ExecutionStatus.RUNNING
            execution.updated_at = datetime.datetime.utcnow().isoformat()
            self.repo.update_execution(execution)
            self._emit_event(EventType.EXECUTION_RESUMED, execution)
        return execution

    async def cancel(self, execution_id: str) -> Optional[Execution]:
        execution = self.repo.get_execution(execution_id)
        if execution:
            execution.status = ExecutionStatus.CANCELLED
            execution.updated_at = datetime.datetime.utcnow().isoformat()
            self.repo.update_execution(execution)
            if execution_id in self._background_tasks:
                self._background_tasks[execution_id].cancel()
            self.engine.scheduler.cancel(execution_id)
            self._emit_event(EventType.EXECUTION_CANCELLED, execution)
        return execution

    async def get_execution(self, execution_id: str) -> Optional[Execution]:
        return self.repo.get_execution(execution_id)

    async def get_events(self, execution_id: str) -> list:
        if self.event_store:
            return self.event_store.get_events(execution_id)
        return []

    async def health_check(self) -> dict:
        planner_ok = await self.planner.check_health() if hasattr(self.planner, "check_health") else True
        return {
            "status": "healthy",
            "services": {
                "planner": "up" if planner_ok else "down"
            }
        }


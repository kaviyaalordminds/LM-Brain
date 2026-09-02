import asyncio
import datetime
import uuid
from typing import Any, Dict, List, Optional, Set

from app.models.execution import Execution, ExecutionStatus, ExecutionPhase
from app.models.state import StepLifecycle
from app.models.events import ExecutionEvent, EventType
from app.models.artifacts import LineageArtifact, TrustState
from app.models.dispatch import AttemptStatus
from app.policies.failure_policy import FailureClassifier, FailureType
from app.policies.retry_policy import RetryPolicy
from app.policies.trust_policy import TrustPolicy
from app.verification.result_verifier import ResultVerifier

class ExecutionResult:
    def __init__(self, status: ExecutionStatus, error: Optional[str] = None):
        self.status = status
        self.error = error

class ExecutionEngine:
    """
    Real DAG Execution Engine.
    Executes tasks according to topological dependencies, concurrently scheduling
    independent ready steps up to max_concurrent_tasks.
    Runs each task through:
    Scheduling -> Memory Context -> Dispatch -> Verification -> Artifact Registration -> State Update.
    """

    def __init__(
        self,
        scheduler,
        dispatcher,
        state_manager,
        repo=None,
        event_store=None,
        event_bus=None,
        memory_client=None,
        verifier=None,
        recovery_manager=None,
        replanner=None
    ):
        self.scheduler = scheduler
        self.dispatcher = dispatcher
        self.state_manager = state_manager
        self.repo = repo
        self.event_store = event_store
        self.event_bus = event_bus
        self.memory_client = memory_client
        self.verifier = verifier or ResultVerifier()
        self.recovery_manager = recovery_manager
        self.replanner = replanner
        self._active_tasks: Dict[str, asyncio.Task] = {}

    def _emit_event(
        self,
        event_type: EventType,
        execution: Execution,
        step_id: Optional[str] = None,
        task_id: Optional[str] = None,
        attempt_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> ExecutionEvent:
        event = ExecutionEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            execution_id=execution.execution_id,
            plan_id=execution.plan_id,
            plan_version=execution.plan_version,
            step_id=step_id,
            task_id=task_id,
            attempt_id=attempt_id,
            correlation_id=execution.correlation_id,
            timestamp=datetime.datetime.utcnow().isoformat(),
            payload=payload or {}
        )
        if self.event_store:
            self.event_store.append(event)
        if self.event_bus:
            self.event_bus.publish(event)
        return event

    async def run(self, execution_id: str, plan: dict) -> ExecutionResult:
        execution = self.repo.get_execution(execution_id) if self.repo else None
        if not execution:
            return ExecutionResult(ExecutionStatus.FAILED, f"Execution {execution_id} not found")

        plan_id = plan.get("plan_id") or plan.get("planId") or "unknown"
        execution.plan_id = plan_id
        execution.status = ExecutionStatus.RUNNING
        execution.phase = ExecutionPhase.SCHEDULING
        execution.updated_at = datetime.datetime.utcnow().isoformat()
        if self.repo:
            self.repo.update_execution(execution)

        # Extract steps & dependencies
        raw_steps = plan.get("steps", [])
        steps_by_id = {}
        for s in raw_steps:
            sid = s.get("step_id") or s.get("stepId")
            if sid:
                steps_by_id[sid] = s
        
        dependencies = plan.get("dependencies", {})
        # Normalize dependencies keys/values
        norm_dependencies = {}
        for k, v in dependencies.items():
            norm_dependencies[k] = v or []
        for sid in steps_by_id:
            if sid not in norm_dependencies:
                norm_dependencies[sid] = steps_by_id[sid].get("dependencies", [])

        # Initialize all steps to PENDING in StateManager
        for sid in steps_by_id:
            try:
                self.state_manager.states[f"{execution_id}:{sid}"] = StepLifecycle.PENDING
            except Exception:
                pass
        execution.pending_steps = list(steps_by_id.keys())
        if self.repo:
            self.repo.update_execution(execution)

        in_flight_tasks: Dict[str, asyncio.Task] = {}
        step_attempts_count: Dict[str, int] = {sid: 0 for sid in steps_by_id}

        # Main DAG execution loop
        while True:
            # Check pause / cancel status
            latest_exec = self.repo.get_execution(execution_id) if self.repo else execution
            if latest_exec and latest_exec.status == ExecutionStatus.PAUSED:
                await asyncio.sleep(0.5)
                continue
            if latest_exec and latest_exec.status == ExecutionStatus.CANCELLED:
                # Cancel running in-flight tasks
                for sid, t in list(in_flight_tasks.items()):
                    t.cancel()
                self._emit_event(EventType.EXECUTION_CANCELLED, execution, payload={"reason": "Cancelled by user"})
                return ExecutionResult(ExecutionStatus.CANCELLED, "Execution cancelled")

            # Evaluate scheduler for ready steps
            ready_steps = self.scheduler.tick(execution_id, self.state_manager.states, norm_dependencies)

            # Filter out steps already running or completed
            runnable_steps = [
                s for s in ready_steps
                if s not in in_flight_tasks
                and self.state_manager.states.get(f"{execution_id}:{s}") in (StepLifecycle.PENDING, StepLifecycle.READY)
            ]

            # Dispatch runnable steps up to max_concurrent_tasks
            available_slots = max(0, self.scheduler.max_concurrent_tasks - len(in_flight_tasks))
            steps_to_dispatch = runnable_steps[:available_slots]

            for sid in steps_to_dispatch:
                curr_st = self.state_manager.states.get(f"{execution_id}:{sid}")
                try:
                    if curr_st == StepLifecycle.PENDING:
                        self.state_manager.transition(execution_id, sid, StepLifecycle.READY)
                        self._emit_event(EventType.STEP_READY, execution, step_id=sid)
                    self.state_manager.transition(execution_id, sid, StepLifecycle.QUEUED)
                    self._emit_event(EventType.STEP_QUEUED, execution, step_id=sid)
                except Exception as e:
                    pass

                # Launch async task for step execution
                task = asyncio.create_task(
                    self._execute_step(execution, steps_by_id[sid], norm_dependencies, step_attempts_count)
                )
                in_flight_tasks[sid] = task


            # If no tasks are in-flight and no steps can run, check if we're done or deadlocked
            if not in_flight_tasks:
                all_completed = all(
                    self.state_manager.states.get(f"{execution_id}:{sid}") == StepLifecycle.COMPLETED
                    for sid in steps_by_id
                )
                any_failed = any(
                    self.state_manager.states.get(f"{execution_id}:{sid}") == StepLifecycle.FAILED
                    for sid in steps_by_id
                )
                any_blocked = any(
                    self.state_manager.states.get(f"{execution_id}:{sid}") == StepLifecycle.BLOCKED
                    for sid in steps_by_id
                )

                any_runnable_or_pending = any(
                    self.state_manager.states.get(f"{execution_id}:{sid}") in (StepLifecycle.PENDING, StepLifecycle.READY)
                    for sid in steps_by_id
                )

                if all_completed:
                    execution.status = ExecutionStatus.COMPLETED
                    execution.phase = ExecutionPhase.FINALIZING
                    execution.updated_at = datetime.datetime.utcnow().isoformat()
                    if self.repo:
                        self.repo.update_execution(execution)
                    self._emit_event(EventType.EXECUTION_COMPLETED, execution)
                    return ExecutionResult(ExecutionStatus.COMPLETED)
                elif any_runnable_or_pending:
                    # Some steps are pending/ready (e.g. recovering or retrying), continue loop
                    await asyncio.sleep(0.05)
                    continue
                else:
                    execution.status = ExecutionStatus.FAILED
                    execution.phase = ExecutionPhase.FINALIZING
                    execution.error = execution.error or "Workflow terminated due to unresolvable step failures"
                    execution.updated_at = datetime.datetime.utcnow().isoformat()
                    if self.repo:
                        self.repo.update_execution(execution)
                    self._emit_event(EventType.EXECUTION_FAILED, execution, payload={"error": execution.error})
                    return ExecutionResult(ExecutionStatus.FAILED, execution.error)


            # Wait for at least one in-flight task to complete
            done, _ = await asyncio.wait(in_flight_tasks.values(), return_when=asyncio.FIRST_COMPLETED)
            # Remove completed tasks from in_flight_tasks
            for sid, t in list(in_flight_tasks.items()):
                if t in done:
                    del in_flight_tasks[sid]

    async def _execute_step(
        self,
        execution: Execution,
        step: dict,
        norm_dependencies: dict,
        step_attempts_count: dict
    ) -> bool:
        sid = step.get("step_id") or step.get("stepId")
        attempt_num = step_attempts_count.get(sid, 0)
        step_attempts_count[sid] = attempt_num + 1

        # Transition QUEUED -> DISPATCHED -> RUNNING
        try:
            self.state_manager.transition(execution.execution_id, sid, StepLifecycle.DISPATCHED)
            self._emit_event(EventType.STEP_DISPATCHED, execution, step_id=sid)
            self.state_manager.transition(execution.execution_id, sid, StepLifecycle.RUNNING)
            self._emit_event(EventType.STEP_STARTED, execution, step_id=sid)
        except Exception:
            pass

        if sid not in execution.running_steps:
            execution.running_steps.append(sid)
        if sid in execution.pending_steps:
            execution.pending_steps.remove(sid)
        if self.repo:
            self.repo.update_execution(execution)

        # 1. Fetch memory context if required
        memory_ctx = {}
        if step.get("memory_required") or step.get("memoryRequired"):
            if self.memory_client:
                try:
                    q = f"{step.get('title', '')} {step.get('description', '')}"
                    mem_res = await self.memory_client.search(q, task_id=sid)
                    memory_ctx = mem_res
                    self._emit_event(
                        EventType.MEMORY_CONTEXT_FETCHED,
                        execution,
                        step_id=sid,
                        payload={"query": q, "found": mem_res.get("found", False)}
                    )
                except Exception as e:
                    memory_ctx = {"error": str(e), "unavailable": True}

        # 2. Dispatch to Specialist
        attempt = await self.dispatcher.dispatch(
            execution.execution_id,
            step,
            attempt_num,
            memory_ctx,
            plan_id=execution.plan_id or "",
            plan_version=execution.plan_version
        )
        if self.repo:
            self.repo.save_attempt(attempt)

        # 3. Verification phase
        try:
            self.state_manager.transition(execution.execution_id, sid, StepLifecycle.VERIFYING)
            self._emit_event(
                EventType.VERIFICATION_STARTED,
                execution,
                step_id=sid,
                attempt_id=attempt.attempt_id
            )
        except Exception:
            pass

        task_result = attempt.result or {}
        gate_result = self.verifier.verify(task_result, step, attempt)

        if gate_result.passed:
            # Step passed verification
            try:
                self.state_manager.transition(execution.execution_id, sid, StepLifecycle.COMPLETED)
            except Exception:
                pass
            
            if sid in execution.running_steps:
                execution.running_steps.remove(sid)
            if sid not in execution.completed_steps:
                execution.completed_steps.append(sid)
            
            self._emit_event(
                EventType.VERIFICATION_PASSED,
                execution,
                step_id=sid,
                attempt_id=attempt.attempt_id
            )
            self._emit_event(
                EventType.STEP_COMPLETED,
                execution,
                step_id=sid,
                attempt_id=attempt.attempt_id
            )

            # Register verified artifacts
            for raw_art in task_result.get("artifacts", []):
                art_id = raw_art.get("artifact_id") or str(uuid.uuid4())
                artifact = LineageArtifact(
                    artifact_id=art_id,
                    execution_id=execution.execution_id,
                    plan_id=execution.plan_id or "unknown",
                    plan_version=execution.plan_version,
                    step_id=sid,
                    task_id=attempt.attempt_id,
                    attempt_id=attempt.attempt_id,
                    specialist_id=step.get("specialist_id") or step.get("specialistId"),
                    artifact_type=raw_art.get("type", "document"),
                    path=raw_art.get("path", ""),
                    url=raw_art.get("url", ""),
                    content=raw_art.get("content", ""),
                    is_mock=raw_art.get("is_mock", False),
                    parent_artifact_ids=[],
                    source_evidence_refs=[],
                    trust_state=TrustState.APPROVED,
                    verification_status="PASSED",
                    created_at=datetime.datetime.utcnow().isoformat()
                )
                if self.repo:
                    self.repo.save_artifact(artifact)
                if art_id not in execution.artifacts:
                    execution.artifacts.append(art_id)
                self._emit_event(
                    EventType.ARTIFACT_CREATED,
                    execution,
                    step_id=sid,
                    attempt_id=attempt.attempt_id,
                    payload={"artifact_id": art_id, "type": artifact.artifact_type}
                )

            if self.repo:
                self.repo.update_execution(execution)
            return True

        else:
            # Verification or Execution failed
            raw_err = attempt.error or gate_result.fail_reason()
            f_type = FailureClassifier.classify(raw_err, error_code=attempt.failure_type)
            
            try:
                self.state_manager.transition(execution.execution_id, sid, StepLifecycle.FAILED)
            except Exception:
                pass

            if sid in execution.running_steps:
                execution.running_steps.remove(sid)
            if sid not in execution.failed_steps:
                execution.failed_steps.append(sid)
            
            execution.error = f"Step {sid} failed: [{f_type.value}] {raw_err}"

            self._emit_event(
                EventType.VERIFICATION_FAILED,
                execution,
                step_id=sid,
                attempt_id=attempt.attempt_id,
                payload={"failure_type": f_type.value, "reason": raw_err}
            )
            self._emit_event(
                EventType.STEP_FAILED,
                execution,
                step_id=sid,
                attempt_id=attempt.attempt_id,
                payload={"failure_type": f_type.value, "error": raw_err}
            )

            # Check retry policy
            fp = step.get("failure_policy") or step.get("failurePolicy") or {}
            max_retries = fp.get("max_retries") or fp.get("maxRetries") or 2
            
            if RetryPolicy.should_retry(f_type, attempt_num, max_retries):
                # Schedule retry
                backoff = RetryPolicy.backoff_seconds(attempt_num)
                self._emit_event(
                    EventType.RETRY_SCHEDULED,
                    execution,
                    step_id=sid,
                    payload={"attempt": attempt_num + 1, "backoff_seconds": backoff}
                )
                await asyncio.sleep(min(backoff, 2.0))  # Capped for local test performance
                # Transition FAILED -> READY for retry
                try:
                    self.state_manager.transition(execution.execution_id, sid, StepLifecycle.READY)
                except Exception:
                    pass
                if sid in execution.failed_steps:
                    execution.failed_steps.remove(sid)
                if sid not in execution.pending_steps:
                    execution.pending_steps.append(sid)
                if self.repo:
                    self.repo.update_execution(execution)
                return False
            else:
                # Permanent failure: block downstream steps
                if self.recovery_manager:
                    blocked = self.recovery_manager.compute_downstream_blocked(sid, norm_dependencies)
                    for b in blocked:
                        try:
                            self.state_manager.transition(execution.execution_id, b, StepLifecycle.BLOCKED)
                        except Exception:
                            self.state_manager.states[f"{execution.execution_id}:{b}"] = StepLifecycle.BLOCKED
                        if b not in execution.blocked_steps:
                            execution.blocked_steps.append(b)
                        if b in execution.pending_steps:
                            execution.pending_steps.remove(b)

                if self.repo:
                    self.repo.update_execution(execution)
                return False


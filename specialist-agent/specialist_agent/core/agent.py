"""
Specialist Agent — Generic Runtime

SpecialistAgent is the ONE generic runtime that all ten specialists use.
Each specialist is an instance of this class with a different AgentConfig.

The runtime manages:
  - Identity and role
  - Lifecycle state machine
  - Task assignment
  - Context loading (via MemoryClient)
  - Tool resolution (via ToolRegistry)
  - Model resolution (via ModelRegistry)
  - Permission enforcement
  - Execution delegation to Executor
  - Verification
  - Retry / reflection loop
  - Event emission
  - Termination

IMPORTANT:
  This class does NOT implement any specialist-specific business logic.
  Specialist behaviour is encoded only in AgentConfig.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from specialist_agent.config.agent_config import AgentConfig
from specialist_agent.contracts.events import AgentEvent, EventType
from specialist_agent.contracts.result import ErrorRecord, TaskResult, TaskStatus
from specialist_agent.contracts.task import TaskRequest
from specialist_agent.core.errors import (
    InvalidTransitionError,
    ModelUnavailableError,
    PermissionDeniedError,
    RetryLimitExceededError,
    TaskValidationError,
)
from specialist_agent.core.lifecycle import AgentLifecycle, AgentState
from specialist_agent.core.verifier import BaseVerifier, StandardVerifier
from specialist_agent.models.base import ModelCapability
from specialist_agent.models.registry import ModelRegistry
from specialist_agent.permissions.policy import PermissionPolicy, build_policy
from specialist_agent.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class SpecialistAgent:
    """
    Generic Specialist Agent Runtime.

    One class. Ten configurations. Zero code duplication.

    Instantiation
    -------------
    Use SpecialistAgentRegistry.spawn_agent(agent_type) rather than
    constructing this directly — the registry wires up all dependencies.
    """

    def __init__(
        self,
        config: AgentConfig,
        tool_registry: ToolRegistry,
        model_registry: ModelRegistry,
        verifier: BaseVerifier | None = None,
        memory_client: Any | None = None,
        agent_id: str | None = None,
    ) -> None:
        self._config = config
        self._tool_registry = tool_registry
        self._model_registry = model_registry
        self._verifier = verifier or StandardVerifier()
        self._memory_client = memory_client

        # Identity
        self._agent_id = agent_id or str(uuid.uuid4())
        self._agent_type = config.agent_type

        # Lifecycle
        self._lifecycle = AgentLifecycle(
            agent_id=self._agent_id,
            on_transition=self._on_state_change,
        )

        # Permission policy
        self._policy = build_policy(self._agent_id, config.agent_type)

        # Event log
        self._events: list[AgentEvent] = []

        # Current task
        self._current_task: TaskRequest | None = None
        self._current_result: TaskResult | None = None

        logger.info(
            "agent.created",
            extra={
                "agent_id": self._agent_id,
                "agent_type": self._agent_type,
                "display_name": config.display_name,
            },
        )

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def agent_id(self) -> str:
        return self._agent_id

    @property
    def agent_type(self) -> str:
        return self._agent_type

    @property
    def config(self) -> AgentConfig:
        return self._config

    @property
    def state(self) -> AgentState:
        return self._lifecycle.state

    @property
    def policy(self) -> PermissionPolicy:
        return self._policy

    @property
    def events(self) -> list[AgentEvent]:
        return list(self._events)

    @property
    def result(self) -> TaskResult | None:
        """The final result (available after COMPLETED or TERMINATED)."""
        return self._current_result

    # ------------------------------------------------------------------
    # Lifecycle — spawn
    # ------------------------------------------------------------------

    def spawn(self) -> None:
        """Move from READY to SPAWNED. Emits AGENT_SPAWNED event."""
        self._lifecycle.transition(AgentState.SPAWNED)
        self._emit(EventType.AGENT_SPAWNED, message=f"Agent {self._agent_type} spawned.")

    # ------------------------------------------------------------------
    # Lifecycle — assign
    # ------------------------------------------------------------------

    def assign(self, task: TaskRequest) -> None:
        """
        Assign a task to this agent.

        Validates the task contract, then transitions to ASSIGNED.
        """
        self._validate_task(task)
        self._current_task = task
        self._current_result = TaskResult(
            task_id=task.task_id,
            agent_id=self._agent_id,
            agent_type=self._agent_type,
        )

        self._lifecycle.transition(AgentState.ASSIGNED)
        self._emit(
            EventType.TASK_ASSIGNED,
            task_id=task.task_id,
            message=f"Task assigned: {task.instruction[:80]}",
        )

    # ------------------------------------------------------------------
    # Lifecycle — execute (full pipeline)
    # ------------------------------------------------------------------

    def execute(self) -> TaskResult:
        """
        Run the full execution pipeline:
          ASSIGNED → RUNNING → VERIFYING → COMPLETED → TERMINATED
        (or failure path with retry).

        Returns the final TaskResult.
        """
        if self._current_task is None or self._current_result is None:
            raise RuntimeError("No task assigned. Call assign() before execute().")

        task = self._current_task
        result = self._current_result
        max_retries = min(
            task.constraints.max_retries,
            self._config.max_retries,
        )

        retry_count = 0
        while True:
            # ── RUNNING ────────────────────────────────────────────────
            self._lifecycle.transition(AgentState.RUNNING)
            result.mark_started()
            self._emit(EventType.AGENT_RUNNING, task_id=task.task_id)

            # Load memory context
            self._load_context(task, result)

            # Resolve tools
            resolved_tools = self._resolve_tools(task, result)

            # Resolve model
            model_ok = self._resolve_model(task, result)
            if not model_ok:
                # Model unavailable — fail immediately (no retry helps here)
                self._lifecycle.transition(AgentState.VERIFYING)
                self._emit(
                    EventType.VERIFICATION_STARTED,
                    task_id=task.task_id,
                    message="Skipping verification — model unavailable.",
                )
                self._lifecycle.transition(AgentState.FAILED)
                self._emit(EventType.AGENT_ERROR, task_id=task.task_id)
                break

            # Execute the agent's actual work
            try:
                self._run_task(task, result, resolved_tools)
            except Exception as exc:  # noqa: BLE001
                result.mark_failed(
                    error_code="EXECUTION_ERROR",
                    message=str(exc),
                    stage="running",
                )
                self._emit(EventType.AGENT_ERROR, task_id=task.task_id, error=str(exc))

            # ── VERIFYING ──────────────────────────────────────────────
            self._lifecycle.transition(AgentState.VERIFYING)
            self._emit(EventType.VERIFICATION_STARTED, task_id=task.task_id)

            if task.constraints.require_verification:
                verification = self._verifier.verify(task, result)
                result.verification = verification

                if verification.passed:
                    self._emit(EventType.VERIFICATION_PASSED, task_id=task.task_id)
                    result.mark_completed(output=result.output)
                    self._lifecycle.transition(AgentState.COMPLETED)
                    self._emit(EventType.TASK_COMPLETED, task_id=task.task_id)
                    break
                else:
                    self._emit(
                        EventType.VERIFICATION_FAILED,
                        task_id=task.task_id,
                        reason=verification.reason,
                    )
                    self._lifecycle.transition(AgentState.FAILED)

            else:
                # Verification skipped (dry_run or constraint says not required)
                result.mark_completed(output=result.output)
                self._lifecycle.transition(AgentState.COMPLETED)
                self._emit(EventType.TASK_COMPLETED, task_id=task.task_id)
                break

            # ── FAIL / RETRY path ──────────────────────────────────────
            if retry_count >= max_retries:
                self._emit(
                    EventType.AGENT_ERROR,
                    task_id=task.task_id,
                    message=f"Retry limit ({max_retries}) exceeded.",
                )
                # Ensure result is explicitly marked FAILED
                if result.status != TaskStatus.FAILED:
                    result.mark_failed(
                        error_code="RETRY_LIMIT_EXCEEDED",
                        message=f"Verification failed after {max_retries} retries.",
                        stage="retry",
                    )
                break

            # ── REFLECTING ─────────────────────────────────────────────
            self._lifecycle.transition(AgentState.REFLECTING)
            self._emit(EventType.REFLECTION_STARTED, task_id=task.task_id)
            reflection_note = self._reflect(task, result)
            result.metadata["reflection"] = reflection_note

            # ── RETRYING ───────────────────────────────────────────────
            retry_count += 1
            result.retry_count = retry_count
            result.errors.clear()   # Clear errors for fresh retry
            self._lifecycle.transition(AgentState.RETRYING)
            self._emit(
                EventType.RETRY_STARTED,
                task_id=task.task_id,
                attempt=retry_count,
                reason=reflection_note,
            )

        # ── TERMINATE ──────────────────────────────────────────────────
        if not self._lifecycle.is_terminal():
            self._lifecycle.transition(AgentState.TERMINATED)
        self._emit(EventType.AGENT_TERMINATED, task_id=task.task_id)

        return result

    # ------------------------------------------------------------------
    # Lifecycle — cancel
    # ------------------------------------------------------------------

    def cancel(self) -> None:
        """Cancel the agent. Transitions to CANCELLED then TERMINATED."""
        if not self._lifecycle.is_terminal():
            try:
                self._lifecycle.transition(AgentState.CANCELLED)
                self._lifecycle.transition(AgentState.TERMINATED)
            except InvalidTransitionError:
                pass
        self._emit(EventType.AGENT_CANCELLED, message="Agent cancelled.")

    # ------------------------------------------------------------------
    # Internal — task validation
    # ------------------------------------------------------------------

    def _validate_task(self, task: TaskRequest) -> None:
        """Validate the TaskRequest before accepting it."""
        if task.agent_type and task.agent_type != self._agent_type:
            raise TaskValidationError(
                f"Task agent_type '{task.agent_type}' does not match this agent '{self._agent_type}'.",
                agent_id=self._agent_id,
            )
        if not task.instruction.strip():
            raise TaskValidationError("Instruction must not be empty.", agent_id=self._agent_id)

    # ------------------------------------------------------------------
    # Internal — context loading
    # ------------------------------------------------------------------

    def _load_context(self, task: TaskRequest, result: TaskResult) -> None:
        """Load relevant memory context from the Memory Agent if configured."""
        if not self._config.use_memory_context or self._memory_client is None:
            return

        import asyncio

        self._emit(EventType.MEMORY_REQUESTED, task_id=task.task_id, query=task.instruction[:80])

        try:
            async def _search() -> Any:
                return await self._memory_client.search(
                    query=task.instruction, task_id=task.task_id
                )

            ctx = asyncio.run(_search())
            if ctx.found:
                self._emit(
                    EventType.MEMORY_RETURNED,
                    task_id=task.task_id,
                    count=ctx.count,
                    trust_level=ctx.trust_level,
                )
                # Inject context into task context (trust level preserved)
                task.context.context_items.extend(ctx.results)
                task.context.trust_level = ctx.trust_level
            else:
                self._emit(EventType.MEMORY_NOT_FOUND, task_id=task.task_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "agent.context_load_failed",
                extra={"agent_id": self._agent_id, "error": str(exc)[:200]},
            )

    # ------------------------------------------------------------------
    # Internal — tool resolution
    # ------------------------------------------------------------------

    def _resolve_tools(self, task: TaskRequest, result: TaskResult) -> list[str]:
        """Determine which tools this agent will use for this task."""
        allowed = set(task.tools_allowed) if task.tools_allowed else set(self._config.tools)
        available = []
        for tool_name in allowed:
            if self._tool_registry.has_tool(tool_name):
                try:
                    self._policy.require(
                        __import__(
                            "specialist_agent.permissions.policy",
                            fromlist=["Permission"],
                        ).Permission(
                            self._tool_registry._tools[tool_name].permission_level
                        )
                    )
                    available.append(tool_name)
                    self._emit(EventType.TOOL_REQUESTED, task_id=task.task_id, tool=tool_name)
                except PermissionDeniedError:
                    self._emit(EventType.TOOL_DENIED, task_id=task.task_id, tool=tool_name)
        return available

    # ------------------------------------------------------------------
    # Internal — model resolution
    # ------------------------------------------------------------------

    def _resolve_model(self, task: TaskRequest, result: TaskResult) -> bool:
        """
        Check model availability for required capabilities.

        Returns True if at least one required capability has an available model,
        or if no model capability is required.
        Returns False (and marks result as failed) if a required model is missing.
        """
        if not self._config.required_model_capabilities:
            return True

        for cap in self._config.required_model_capabilities:
            provider, status = self._model_registry.resolve_or_not_configured(cap)
            if provider is not None:
                self._emit(
                    EventType.MODEL_RESOLVED,
                    task_id=task.task_id,
                    capability=cap.value,
                    provider=provider.name,
                )
                return True

        # No model available for any required capability
        cap_names = [c.value for c in self._config.required_model_capabilities]
        self._emit(
            EventType.MODEL_UNAVAILABLE,
            task_id=task.task_id,
            capabilities=cap_names,
        )
        result.mark_failed(
            error_code="MODEL_UNAVAILABLE",
            message=(
                f"No model provider configured for capabilities: {cap_names}. "
                "Configure the appropriate model provider to enable this agent."
            ),
            stage="model_resolution",
        )
        return False

    # ------------------------------------------------------------------
    # Internal — run task
    # ------------------------------------------------------------------

    def _run_task(self, task: TaskRequest, result: TaskResult, tools: list[str]) -> None:
        """
        Execute the agent's task.

        This method uses available tools and models to perform the work.
        For agents without configured models, this produces a controlled failure.
        """
        # Attempt to execute using the primary required capability (if any)
        if self._config.required_model_capabilities:
            cap = self._config.required_model_capabilities[0]
            model_response = self._model_registry.generate(
                capability=cap,
                prompt=task.instruction,
                context=task.context.context_items,
                tools=tools,
            )
            if not model_response.success:
                result.mark_failed(
                    error_code=model_response.error_code or "MODEL_ERROR",
                    message=model_response.error or "Model execution failed.",
                    stage="running",
                )
                return
            result.output = str(model_response.output)
        else:
            # Agent type doesn't need a model (e.g. pure tool-based agent)
            result.output = f"Task executed by {self._agent_type} agent. Instruction: {task.instruction}"

    # ------------------------------------------------------------------
    # Internal — reflection
    # ------------------------------------------------------------------

    def _reflect(self, task: TaskRequest, result: TaskResult) -> str:
        """
        Generate a corrected execution plan for the retry.

        In this phase the agent analyses its errors and produces a note
        describing why it failed and what to do differently.
        """
        error_summary = "; ".join(e.message for e in result.errors[:3]) if result.errors else "Unknown"
        return (
            f"Reflection: task '{task.instruction[:60]}' failed. "
            f"Errors: {error_summary}. "
            "Retry will re-attempt with same parameters."
        )

    # ------------------------------------------------------------------
    # Internal — event emission
    # ------------------------------------------------------------------

    def _emit(self, event_type: EventType, task_id: str | None = None, **metadata: Any) -> None:
        event = AgentEvent.create(
            event_type=event_type,
            agent_id=self._agent_id,
            task_id=task_id or (self._current_task.task_id if self._current_task else None),
            message=metadata.pop("message", ""),
            **metadata,
        )
        self._events.append(event)
        logger.debug(
            "agent.event",
            extra={
                "agent_id": self._agent_id,
                "event_type": event_type.value,
                "task_id": event.task_id,
            },
        )

    def _on_state_change(
        self, agent_id: str, from_state: AgentState, to_state: AgentState
    ) -> None:
        """Observer callback invoked by AgentLifecycle on every transition."""
        logger.info(
            "agent.state_change",
            extra={
                "agent_id": agent_id,
                "from": from_state.value,
                "to": to_state.value,
            },
        )

    def __repr__(self) -> str:
        return (
            f"SpecialistAgent(id={self._agent_id!r}, "
            f"type={self._agent_type!r}, "
            f"state={self._lifecycle.state.value})"
        )

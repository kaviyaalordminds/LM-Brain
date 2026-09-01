"""
Specialist Agent — Executor

The Executor is a standalone helper that wires together the registry
and provides a convenient run_task() function.

This is the primary entry point for:
  - The manual test runner
  - Future Master Orchestrator integration

Usage:
  executor = Executor(registry)
  result = executor.run_task(task_request)
"""

from __future__ import annotations

import logging

from specialist_agent.contracts.result import TaskResult, TaskStatus
from specialist_agent.contracts.task import TaskRequest
from specialist_agent.core.registry import SpecialistAgentRegistry
from specialist_agent.core.errors import AgentError

logger = logging.getLogger(__name__)


class Executor:
    """
    Standalone task executor.

    Wires task execution from the SpecialistAgentRegistry.
    Each call to run_task spawns a fresh agent instance.

    This class is the primary integration point for the future
    Master Orchestrator.
    """

    def __init__(self, registry: SpecialistAgentRegistry) -> None:
        self._registry = registry

    def run_task(self, task: TaskRequest) -> TaskResult:
        """
        Execute *task* on the appropriate specialist agent.

        Pipeline:
          1. Spawn agent from registry.
          2. Agent.spawn() → SPAWNED
          3. Agent.assign(task) → ASSIGNED
          4. Agent.execute() → RUNNING → VERIFY → COMPLETE/FAIL → TERMINATE

        Returns the final TaskResult.
        """
        logger.info(
            "executor.run_task",
            extra={"task_id": task.task_id, "agent_type": task.agent_type},
        )

        try:
            agent = self._registry.spawn_agent(task.agent_type)
            agent.spawn()
            agent.assign(task)
            result = agent.execute()
            logger.info(
                "executor.task_complete",
                extra={
                    "task_id": task.task_id,
                    "status": result.status.value,
                    "agent_id": agent.agent_id,
                },
            )
            return result

        except AgentError as exc:
            logger.error(
                "executor.agent_error",
                extra={"task_id": task.task_id, "error": str(exc)},
            )
            result = TaskResult(
                task_id=task.task_id,
                agent_id="unknown",
                agent_type=task.agent_type,
                status=TaskStatus.FAILED,
            )
            result.mark_failed(
                error_code="AGENT_ERROR",
                message=str(exc),
                stage="executor",
            )
            return result

        except Exception as exc:  # noqa: BLE001
            logger.error(
                "executor.unexpected_error",
                extra={"task_id": task.task_id},
                exc_info=True,
            )
            result = TaskResult(
                task_id=task.task_id,
                agent_id="unknown",
                agent_type=task.agent_type,
                status=TaskStatus.FAILED,
            )
            result.mark_failed(
                error_code="UNEXPECTED_ERROR",
                message=str(exc),
                stage="executor",
            )
            return result

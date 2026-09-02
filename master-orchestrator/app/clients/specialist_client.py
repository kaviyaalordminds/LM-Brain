import asyncio
import sys
from pathlib import Path
from typing import Any, Dict

# Ensure specialist-agent is in Python path if not already
specialist_agent_path = Path("C:/Lordminds/Multiagent/specialist-agent")
if specialist_agent_path.exists() and str(specialist_agent_path) not in sys.path:
    sys.path.insert(0, str(specialist_agent_path))

class SpecialistUnavailableError(Exception): pass
class SpecialistDispatchError(Exception): pass

class SpecialistClient:
    """
    In-process adapter for the real Specialist Agent Executor.
    Calls `Executor(registry).run_task(TaskRequest)`.
    Never fakes output. If model is unavailable, reports MODEL_UNAVAILABLE honest failure.
    """

    def __init__(self, memory_client=None):
        self.memory_client = memory_client
        self._executor = None
        self._registry = None
        self._init_runtime()

    def _init_runtime(self):
        try:
            from specialist_agent.run_test import build_tool_registry, build_model_registry
            from specialist_agent.core.registry import SpecialistAgentRegistry
            from specialist_agent.core.executor import Executor
            from specialist_agent.agents import ALL_AGENT_CONFIGS

            tool_registry = build_tool_registry()
            model_registry = build_model_registry()
            self._registry = SpecialistAgentRegistry(tool_registry, model_registry, memory_client=self.memory_client)
            self._registry.register_all(ALL_AGENT_CONFIGS)
            self._executor = Executor(self._registry)
        except Exception as e:
            # If specialist package cannot be imported, runtime will raise on dispatch
            self._executor = None
            self._init_error = str(e)

    async def dispatch(self, task_request_dict: dict) -> dict:
        if self._executor is None:
            raise SpecialistUnavailableError(f"Specialist runtime unavailable: {getattr(self, '_init_error', 'Not initialized')}")

        try:
            from specialist_agent.contracts.task import TaskRequest, TaskContext, TaskConstraints, ExpectedOutput

            # Parse into strongly typed TaskRequest contract
            ctx_data = task_request_dict.get("context", {})
            constraints_data = task_request_dict.get("constraints", {})
            expected_data = task_request_dict.get("expected_output", {})

            task_req = TaskRequest(
                task_id=task_request_dict.get("task_id"),
                agent_type=task_request_dict.get("agent_type"),
                instruction=task_request_dict.get("instruction"),
                context=TaskContext(
                    context_items=ctx_data.get("context_items", []),
                    trust_level=ctx_data.get("trust_level", "RETRIEVED"),
                    extra=ctx_data.get("extra", {})
                ),
                constraints=TaskConstraints(
                    max_duration_seconds=constraints_data.get("max_duration_seconds", 300),
                    max_retries=constraints_data.get("max_retries", 2),
                    require_verification=constraints_data.get("require_verification", True),
                    dry_run=constraints_data.get("dry_run", False)
                ),
                expected_output=ExpectedOutput(
                    output_type=expected_data.get("output_type", "text"),
                    artifact_types=expected_data.get("artifact_types", []),
                    description=expected_data.get("description", "")
                ),
                tools_allowed=task_request_dict.get("tools_allowed", []),
                metadata=task_request_dict.get("metadata", {})
            )

            # Run in threadpool since Executor is synchronous
            result = await asyncio.to_thread(self._executor.run_task, task_req)
            return result.model_dump(mode="json")
        except Exception as e:
            raise SpecialistDispatchError(f"Error dispatching task to specialist {task_request_dict.get('agent_type')}: {str(e)}") from e

    async def check_health(self, specialist_id: str) -> bool:
        if self._registry is None:
            return False
        try:
            cfg = self._registry.get_agent_config(specialist_id)
            return cfg is not None
        except Exception:
            return False


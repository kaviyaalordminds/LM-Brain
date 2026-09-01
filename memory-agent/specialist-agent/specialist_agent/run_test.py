"""
Specialist Agent — Manual Test Runner

Usage:
  python -m specialist_agent.run_test --agent image_generation \
         --task "Generate a futuristic electric car"

  python -m specialist_agent.run_test --agent web_development \
         --task "Create a simple responsive company homepage"

  python -m specialist_agent.run_test --agent research \
         --task "Find current best practices for securing REST APIs"

  python -m specialist_agent.run_test --list

The test runner:
  1. Builds a minimal ToolRegistry and ModelRegistry from env config.
  2. Registers all 10 specialist agent configs.
  3. Spawns the requested agent.
  4. Assigns the task.
  5. Executes the pipeline.
  6. Verifies the result.
  7. Prints a detailed report.
  8. Terminates.

IMPORTANT:
  If no model is configured for an agent, the output clearly states:
  MODEL NOT CONFIGURED — not a fake success.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys

from specialist_agent.agents import ALL_AGENT_CONFIGS
from specialist_agent.config.agents import get_specialist_settings
from specialist_agent.contracts.task import TaskRequest
from specialist_agent.core.executor import Executor
from specialist_agent.core.registry import SpecialistAgentRegistry
from specialist_agent.models.registry import ModelRegistry
from specialist_agent.tools.database import DatabaseTool
from specialist_agent.tools.filesystem import FilesystemTool
from specialist_agent.tools.http import HttpTool
from specialist_agent.tools.image_generation import ImageGenerationTool
from specialist_agent.tools.registry import ToolRegistry
from specialist_agent.tools.research import ResearchTool
from specialist_agent.tools.shell import ShellTool

logging.basicConfig(
    level=logging.WARNING,   # Keep noise low for manual runs
    format="%(levelname)-8s | %(name)s | %(message)s",
)


def build_tool_registry() -> ToolRegistry:
    """Build a ToolRegistry populated with all available tools."""
    registry = ToolRegistry()

    settings = get_specialist_settings()

    registry.register(FilesystemTool())
    registry.register(ShellTool())
    registry.register(HttpTool())
    registry.register(DatabaseTool(connection_string=None))

    # Image generation — configure from env
    registry.register(
        ImageGenerationTool(
            provider_name=settings.image_model_provider or None,
            endpoint=settings.image_model_endpoint or None,
            model_name=settings.image_model_name or None,
        )
    )

    # Research tool (no memory client for standalone runner)
    registry.register(ResearchTool(memory_client=None))

    return registry


def build_model_registry() -> ModelRegistry:
    """Build a ModelRegistry. No providers registered — all show NOT_CONFIGURED."""
    # When real providers are available, register them here.
    # For now, the registry is empty → MODEL_UNAVAILABLE for all capabilities.
    return ModelRegistry()


def build_registry() -> SpecialistAgentRegistry:
    """Wire up the full SpecialistAgentRegistry with all 10 agent configs."""
    tool_registry = build_tool_registry()
    model_registry = build_model_registry()
    registry = SpecialistAgentRegistry(tool_registry, model_registry)
    registry.register_all(ALL_AGENT_CONFIGS)
    return registry


def print_header(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def print_result(result: object) -> None:
    from specialist_agent.contracts.result import TaskResult
    assert isinstance(result, TaskResult)

    print_header(f"TASK RESULT — {result.agent_type.upper()}")
    print(f"  task_id   : {result.task_id}")
    print(f"  agent_id  : {result.agent_id}")
    print(f"  status    : {result.status.value}")
    print(f"  progress  : {result.progress:.0%}")
    if result.duration_seconds is not None:
        print(f"  duration  : {result.duration_seconds:.2f}s")
    print(f"  retries   : {result.retry_count}")

    if result.output:
        print(f"\n  OUTPUT:\n    {result.output[:400]}")

    if result.artifacts:
        print(f"\n  ARTIFACTS ({len(result.artifacts)}):")
        for art in result.artifacts:
            tag = "[MOCK]" if art.is_mock else "[REAL]"
            print(f"    {tag} type={art.type.value} path={art.path or ''} url={art.url or ''}")

    print(f"\n  VERIFICATION: {result.verification.verdict.value}")
    print(f"    reason: {result.verification.reason}")
    for chk in result.verification.checks:
        icon = "✓" if chk.verdict.value == "PASS" else "✗"
        print(f"    {icon} {chk.name}: {chk.reason}")

    if result.errors:
        print(f"\n  ERRORS ({len(result.errors)}):")
        for err in result.errors:
            print(f"    [{err.error_code}] {err.message}")
            if err.error_code == "MODEL_UNAVAILABLE":
                print()
                print("  +--------------------------------------------------+")
                print("  |  MODEL NOT CONFIGURED                            |")
                print("  |  No image/code/LLM provider is set up.          |")
                print("  |  Set the appropriate MODEL env vars to enable.   |")
                print("  +--------------------------------------------------+")
                print()

    print(f"\n  EVENTS ({len(result.metadata.get('events', []))} logged)")
    print("=" * 60)


def run_test(agent_type: str, task_instruction: str) -> int:
    """
    Run a single agent test.

    Returns 0 on success (COMPLETED), 1 on failure.
    """
    print_header(f"SPECIALIST AGENT TEST RUNNER")
    print(f"  Agent : {agent_type}")
    print(f"  Task  : {task_instruction[:80]}")
    print()

    registry = build_registry()

    if agent_type not in registry:
        print(f"  ERROR: Unknown agent type '{agent_type}'.")
        print(f"  Available: {sorted(ALL_AGENT_CONFIGS)}")
        return 1

    task = TaskRequest(
        agent_type=agent_type,
        instruction=task_instruction,
        constraints={"max_retries": 1, "require_verification": True, "dry_run": False,
                     "max_duration_seconds": 60},
    )

    executor = Executor(registry)
    result = executor.run_task(task)
    print_result(result)

    return 0 if result.status.value in {"completed", "COMPLETED"} else 1


def list_agents() -> None:
    """Print a summary of all registered agent types."""
    registry = build_registry()
    print_header("REGISTERED SPECIALIST AGENTS")
    for entry in registry.list_agents():
        print(f"\n  [{entry['agent_type']}]")
        print(f"    display_name : {entry['display_name']}")
        print(f"    role         : {entry['role']}")
        print(f"    capabilities : {', '.join(entry['capabilities'])}")
        print(f"    tools        : {', '.join(entry['tools'])}")
        print(f"    max_retries  : {entry['max_retries']}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="python -m specialist_agent.run_test",
        description="Manual Specialist Agent Test Runner",
    )
    parser.add_argument(
        "--agent",
        type=str,
        help="Agent type to test (e.g. image_generation, web_development)",
    )
    parser.add_argument(
        "--task",
        type=str,
        default="",
        help="Task instruction to send to the agent.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all registered agent types and exit.",
    )

    args = parser.parse_args()

    if args.list:
        list_agents()
        return 0

    if not args.agent:
        parser.print_help()
        return 1

    if not args.task:
        print(f"ERROR: --task is required when specifying an agent.")
        return 1

    return run_test(args.agent, args.task)


if __name__ == "__main__":
    sys.exit(main())

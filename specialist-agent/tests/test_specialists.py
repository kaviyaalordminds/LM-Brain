"""
Tests for all 10 specialist agent definitions.

Covers:
  - Each agent uses the generic SpecialistAgent runtime
  - Image agent: MODEL_UNAVAILABLE when no model configured
  - Image agent: No fake artifacts produced
  - Research agent: Trust hierarchy preserved
  - Web dev agent: Fails cleanly when no code model
  - All agents: No ADMIN permission
  - Verification pass/fail
  - Retry with limit
  - Termination
  - Tool and model registry handling
"""

from __future__ import annotations

import pytest

from specialist_agent.agents import ALL_AGENT_CONFIGS
from specialist_agent.core.agent import SpecialistAgent
from specialist_agent.core.executor import Executor
from specialist_agent.core.lifecycle import AgentState
from specialist_agent.core.registry import SpecialistAgentRegistry
from specialist_agent.contracts.result import TaskStatus
from specialist_agent.contracts.task import TaskRequest
from specialist_agent.models.registry import ModelRegistry
from specialist_agent.models.providers import MockModelProvider
from specialist_agent.models.base import ModelCapability
from specialist_agent.permissions.policy import Permission
from specialist_agent.tools.registry import ToolRegistry
from specialist_agent.tools.filesystem import FilesystemTool
from specialist_agent.tools.shell import ShellTool
from specialist_agent.tools.image_generation import ImageGenerationTool
from specialist_agent.tools.research import ResearchTool
from specialist_agent.tools.http import HttpTool
from specialist_agent.tools.database import DatabaseTool
from specialist_agent.core.verifier import MockVerifier


def make_empty_registry() -> SpecialistAgentRegistry:
    """Registry with no model providers — all capabilities report NOT_CONFIGURED."""
    tool_registry = ToolRegistry()
    tool_registry.register(FilesystemTool())
    tool_registry.register(ShellTool())
    tool_registry.register(HttpTool())
    tool_registry.register(DatabaseTool())
    tool_registry.register(ImageGenerationTool(provider_name=None, endpoint=None))
    tool_registry.register(ResearchTool(memory_client=None))

    model_registry = ModelRegistry()
    # No providers registered → MODEL_UNAVAILABLE for all

    registry = SpecialistAgentRegistry(tool_registry, model_registry)
    registry.register_all(ALL_AGENT_CONFIGS)
    return registry


def make_mock_registry() -> SpecialistAgentRegistry:
    """Registry with mock model providers for testing execution."""
    tool_registry = ToolRegistry()
    tool_registry.register(FilesystemTool())
    tool_registry.register(ShellTool())
    tool_registry.register(HttpTool())
    tool_registry.register(DatabaseTool())
    tool_registry.register(ImageGenerationTool(provider_name=None, endpoint=None))
    tool_registry.register(ResearchTool(memory_client=None))

    model_registry = ModelRegistry()
    # Register mock providers for all capabilities
    for cap in ModelCapability:
        model_registry.register(MockModelProvider(capability=cap))

    registry = SpecialistAgentRegistry(tool_registry, model_registry)
    registry.register_all(ALL_AGENT_CONFIGS)
    return registry


class TestAllTenSpecialistsExist:
    """Verify all 10 specialist definitions are present."""

    @pytest.mark.parametrize("agent_type", [
        "web_development", "image_generation", "backend", "database",
        "api_integration", "security", "testing", "devops", "ai_ml", "research",
    ])
    def test_specialist_registered(self, agent_type: str):
        assert agent_type in ALL_AGENT_CONFIGS, f"Missing specialist: {agent_type}"

    def test_exactly_ten_specialists(self):
        assert len(ALL_AGENT_CONFIGS) == 10


class TestAllAgentsSameRuntime:
    """All 10 specialists must be instances of SpecialistAgent."""

    @pytest.mark.parametrize("agent_type", list(ALL_AGENT_CONFIGS.keys()))
    def test_uses_specialist_agent_runtime(self, agent_type: str):
        registry = make_empty_registry()
        agent = registry.spawn_agent(agent_type)
        assert type(agent) is SpecialistAgent


class TestImageGenerationAgent:
    """
    Critical: Image agent must never fabricate images.
    When no model is configured → MODEL_UNAVAILABLE.
    """

    def test_image_agent_model_unavailable_no_fake(self):
        """PART 24: Generate image of electric car with no model → MODEL_UNAVAILABLE."""
        registry = make_empty_registry()
        executor = Executor(registry)

        task = TaskRequest(
            agent_type="image_generation",
            instruction="Generate an image of a futuristic electric car",
            constraints={"max_retries": 0, "require_verification": False,
                         "dry_run": False, "max_duration_seconds": 30},
        )
        result = executor.run_task(task)

        # Must fail — not complete
        assert result.status == TaskStatus.FAILED, (
            f"Image agent must FAIL when no model configured, got: {result.status}"
        )

        # Must have MODEL_UNAVAILABLE error code
        error_codes = [e.error_code for e in result.errors]
        assert "MODEL_UNAVAILABLE" in error_codes, (
            f"Expected MODEL_UNAVAILABLE error code, got: {error_codes}"
        )

    def test_image_agent_produces_no_fake_artifacts(self):
        """No artifact should be produced when model is unavailable."""
        registry = make_empty_registry()
        executor = Executor(registry)

        task = TaskRequest(
            agent_type="image_generation",
            instruction="Generate a beautiful sunset over the ocean",
            constraints={"max_retries": 0, "require_verification": False,
                         "dry_run": False, "max_duration_seconds": 30},
        )
        result = executor.run_task(task)

        # No real artifacts (is_mock=False) must exist
        real_artifacts = [a for a in result.artifacts if not a.is_mock]
        assert real_artifacts == [], (
            f"Image agent must not produce real artifacts when model unavailable. "
            f"Got: {real_artifacts}"
        )

    def test_image_agent_no_admin_permission(self):
        registry = make_empty_registry()
        agent = registry.spawn_agent("image_generation")
        assert not agent.policy.has(Permission.ADMIN)


class TestWebDevelopmentAgent:
    """PART 25: Web development agent test."""

    def test_web_dev_fails_cleanly_without_code_model(self):
        """Without a code model, web dev agent should fail cleanly — not fake code."""
        registry = make_empty_registry()
        executor = Executor(registry)

        task = TaskRequest(
            agent_type="web_development",
            instruction="Create a simple responsive company homepage",
            constraints={"max_retries": 0, "require_verification": False,
                         "dry_run": False, "max_duration_seconds": 30},
        )
        result = executor.run_task(task)
        assert result.status == TaskStatus.FAILED
        error_codes = [e.error_code for e in result.errors]
        assert "MODEL_UNAVAILABLE" in error_codes

    def test_web_dev_with_mock_model_completes(self):
        """With a mock model, web dev agent should complete the lifecycle."""
        registry = make_mock_registry()
        executor = Executor(registry)

        task = TaskRequest(
            agent_type="web_development",
            instruction="Create a simple responsive company homepage",
            constraints={"max_retries": 0, "require_verification": False,
                         "dry_run": False, "max_duration_seconds": 30},
        )
        result = executor.run_task(task)
        assert result.status == TaskStatus.COMPLETED


class TestResearchAgent:
    """PART 26: Research agent trust hierarchy test."""

    def test_research_agent_has_no_write_permission(self):
        """Research agent must not be able to write directly to Obsidian."""
        registry = make_empty_registry()
        agent = registry.spawn_agent("research")
        assert not agent.policy.has(Permission.WRITE), (
            "Research agent must NOT have WRITE permission — "
            "it cannot write directly to Obsidian."
        )

    def test_research_agent_config_trust_rule_documented(self):
        config = ALL_AGENT_CONFIGS["research"]
        assert "UNVERIFIED" in config.metadata.get("trust_rule", ""), (
            "Research agent config must document the UNVERIFIED trust rule."
        )

    def test_research_agent_capability_includes_external_research(self):
        config = ALL_AGENT_CONFIGS["research"]
        assert "external_research" in config.capabilities


class TestSecurityAgent:
    def test_security_agent_restrictive_permissions(self):
        registry = make_empty_registry()
        agent = registry.spawn_agent("security")
        assert agent.policy.has(Permission.READ)
        assert agent.policy.has(Permission.AUDIT)
        assert not agent.policy.has(Permission.EXECUTE)
        assert not agent.policy.has(Permission.WRITE)
        assert not agent.policy.has(Permission.ADMIN)


class TestVerificationAndRetry:
    def _make_agent(self, verifier=None):
        from specialist_agent.config.agent_config import AgentConfig
        from specialist_agent.models.base import ModelCapability

        config = AgentConfig(
            agent_type="testing",
            display_name="Testing Agent",
            description="Test agent",
            role="Tester",
            capabilities=["unit_testing"],
            required_model_capabilities=[],   # No model needed
            max_retries=2,
        )
        agent = SpecialistAgent(
            config=config,
            tool_registry=ToolRegistry(),
            model_registry=ModelRegistry(),
            verifier=verifier or MockVerifier(should_pass=True),
        )
        return agent

    def test_verification_pass_leads_to_completed(self):
        agent = self._make_agent(verifier=MockVerifier(should_pass=True))
        task = TaskRequest(
            agent_type="testing",
            instruction="Run unit tests",
            constraints={"max_retries": 2, "require_verification": True,
                         "dry_run": False, "max_duration_seconds": 60},
        )
        agent.spawn()
        agent.assign(task)
        result = agent.execute()
        assert result.status == TaskStatus.COMPLETED

    def test_verification_fail_leads_to_retry_then_failed(self):
        """When verifier always fails, retry limit is hit and result is FAILED."""
        agent = self._make_agent(verifier=MockVerifier(should_pass=False, reason="Always fails"))
        task = TaskRequest(
            agent_type="testing",
            instruction="Run regression tests",
            constraints={"max_retries": 1, "require_verification": True,
                         "dry_run": False, "max_duration_seconds": 60},
        )
        agent.spawn()
        agent.assign(task)
        result = agent.execute()
        assert result.status == TaskStatus.FAILED
        assert result.retry_count == 1   # max_retries=1

    def test_retry_limit_is_respected(self):
        """Retry count must never exceed max_retries."""
        agent = self._make_agent(verifier=MockVerifier(should_pass=False))
        max_retries = 2
        task = TaskRequest(
            agent_type="testing",
            instruction="Run tests",
            constraints={"max_retries": max_retries, "require_verification": True,
                         "dry_run": False, "max_duration_seconds": 60},
        )
        agent.spawn()
        agent.assign(task)
        result = agent.execute()
        assert result.retry_count <= max_retries

    def test_termination_result_available_after_terminate(self):
        """Result must remain available after agent terminates."""
        agent = self._make_agent(verifier=MockVerifier(should_pass=True))
        task = TaskRequest(
            agent_type="testing",
            instruction="Test something",
            constraints={"max_retries": 0, "require_verification": True,
                         "dry_run": False, "max_duration_seconds": 60},
        )
        agent.spawn()
        agent.assign(task)
        result = agent.execute()
        assert result is not None
        assert agent.state == AgentState.TERMINATED
        # Result still accessible after termination
        assert agent.result is not None
        assert agent.result.task_id == task.task_id


class TestSpecialistCapabilities:
    """Verify each specialist has the correct capabilities defined."""

    @pytest.mark.parametrize("agent_type,expected_cap", [
        ("web_development", "frontend_development"),
        ("image_generation", "image_generation"),
        ("backend", "backend_services"),
        ("database", "database_schema"),
        ("api_integration", "rest_api_integration"),
        ("security", "security_review"),
        ("testing", "unit_testing"),
        ("devops", "docker"),
        ("ai_ml", "ai_integration"),
        ("research", "external_research"),
    ])
    def test_capability_present(self, agent_type: str, expected_cap: str):
        config = ALL_AGENT_CONFIGS[agent_type]
        assert expected_cap in config.capabilities, (
            f"Agent '{agent_type}' missing capability '{expected_cap}'. "
            f"Has: {config.capabilities}"
        )

    def test_no_agent_is_admin(self):
        """No specialist should have ADMIN permission."""
        registry = make_empty_registry()
        for agent_type in ALL_AGENT_CONFIGS:
            agent = registry.spawn_agent(agent_type)
            assert not agent.policy.has(Permission.ADMIN), (
                f"Agent '{agent_type}' should NOT have ADMIN permission."
            )

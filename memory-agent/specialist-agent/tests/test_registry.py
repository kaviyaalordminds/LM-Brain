"""
Tests for SpecialistAgentRegistry.

Covers:
  - Agent registration and retrieval
  - list_agents()
  - validate_capability()
  - spawn_agent()
  - Unknown agent type error
  - All 10 specialist types registered
"""

from __future__ import annotations

import pytest

from specialist_agent.agents import ALL_AGENT_CONFIGS
from specialist_agent.core.errors import AgentError
from specialist_agent.core.registry import SpecialistAgentRegistry
from specialist_agent.models.registry import ModelRegistry
from specialist_agent.tools.registry import ToolRegistry


def make_registry() -> SpecialistAgentRegistry:
    registry = SpecialistAgentRegistry(
        tool_registry=ToolRegistry(),
        model_registry=ModelRegistry(),
    )
    registry.register_all(ALL_AGENT_CONFIGS)
    return registry


class TestSpecialistAgentRegistry:
    def test_all_ten_agents_registered(self):
        registry = make_registry()
        assert len(registry) == 10

    def test_get_agent_returns_config(self):
        registry = make_registry()
        config = registry.get_agent("image_generation")
        assert config.agent_type == "image_generation"
        assert config.display_name == "Image Generation Agent"

    def test_get_agent_config_alias(self):
        registry = make_registry()
        config = registry.get_agent_config("web_development")
        assert config.agent_type == "web_development"

    def test_unknown_agent_type_raises(self):
        registry = make_registry()
        with pytest.raises(AgentError, match="Unknown agent type"):
            registry.get_agent("nonexistent_agent")

    def test_list_agents_returns_ten(self):
        registry = make_registry()
        agents = registry.list_agents()
        assert len(agents) == 10

    def test_list_agents_contains_required_keys(self):
        registry = make_registry()
        for entry in registry.list_agents():
            assert "agent_type" in entry
            assert "display_name" in entry
            assert "role" in entry
            assert "capabilities" in entry

    def test_contains_operator(self):
        registry = make_registry()
        assert "research" in registry
        assert "unknown" not in registry

    def test_validate_capability_true(self):
        registry = make_registry()
        assert registry.validate_capability("image_generation", "image_generation") is True

    def test_validate_capability_false(self):
        registry = make_registry()
        assert registry.validate_capability("security", "image_generation") is False

    def test_validate_capability_unknown_agent_raises(self):
        registry = make_registry()
        with pytest.raises(AgentError):
            registry.validate_capability("nonexistent", "some_cap")

    def test_spawn_agent_returns_specialist_agent(self):
        from specialist_agent.core.agent import SpecialistAgent
        from specialist_agent.core.lifecycle import AgentState

        registry = make_registry()
        agent = registry.spawn_agent("research")
        assert isinstance(agent, SpecialistAgent)
        assert agent.agent_type == "research"
        assert agent.state == AgentState.READY

    def test_each_agent_type_spawnable(self):
        registry = make_registry()
        for agent_type in ALL_AGENT_CONFIGS:
            agent = registry.spawn_agent(agent_type)
            assert agent.agent_type == agent_type

    def test_all_agents_use_same_runtime(self):
        """All specialists must be instances of SpecialistAgent — not ten different classes."""
        from specialist_agent.core.agent import SpecialistAgent

        registry = make_registry()
        for agent_type in ALL_AGENT_CONFIGS:
            agent = registry.spawn_agent(agent_type)
            assert type(agent) is SpecialistAgent, (
                f"Agent '{agent_type}' must use SpecialistAgent runtime, "
                f"got {type(agent).__name__}"
            )

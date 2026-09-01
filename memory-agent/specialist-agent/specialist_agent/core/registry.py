"""
Specialist Agent — Registry

The SpecialistAgentRegistry is the central directory of all
specialist agent types.

The future Master Orchestrator will use this registry to:
  - list available agents
  - validate capabilities
  - spawn agent instances

The registry does NOT run tasks — it only manages agent definitions
and instantiation.
"""

from __future__ import annotations

import logging

from specialist_agent.config.agent_config import AgentConfig
from specialist_agent.core.agent import SpecialistAgent
from specialist_agent.core.errors import AgentError
from specialist_agent.models.registry import ModelRegistry
from specialist_agent.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class SpecialistAgentRegistry:
    """
    Central registry for specialist agent types.

    Registers AgentConfig definitions and spawns live SpecialistAgent instances.

    Usage
    -----
    registry = SpecialistAgentRegistry(tool_registry, model_registry)
    registry.register(web_dev_config)
    agent = registry.spawn_agent("web_development")
    """

    def __init__(
        self,
        tool_registry: ToolRegistry,
        model_registry: ModelRegistry,
        memory_client: object | None = None,
    ) -> None:
        self._tool_registry = tool_registry
        self._model_registry = model_registry
        self._memory_client = memory_client
        self._configs: dict[str, AgentConfig] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, config: AgentConfig) -> None:
        """Register an AgentConfig for the given agent_type."""
        self._configs[config.agent_type] = config
        logger.debug("registry.registered", extra={"agent_type": config.agent_type})

    def register_all(self, configs: dict[str, AgentConfig]) -> None:
        """Register multiple AgentConfig instances at once."""
        for config in configs.values():
            self.register(config)

    # ------------------------------------------------------------------
    # Query API
    # ------------------------------------------------------------------

    def get_agent_config(self, agent_type: str) -> AgentConfig:
        """
        Return the AgentConfig for *agent_type*.

        Raises AgentError if the type is not registered.
        """
        config = self._configs.get(agent_type)
        if config is None:
            raise AgentError(f"Unknown agent type: '{agent_type}'. "
                             f"Registered types: {sorted(self._configs)}")
        return config

    # Alias for external callers (Part 21 of specification)
    def get_agent(self, agent_type: str) -> AgentConfig:
        """Alias for get_agent_config — matches the specification API."""
        return self.get_agent_config(agent_type)

    def list_agents(self) -> list[dict[str, object]]:
        """Return a summary list of all registered agent types."""
        return [
            {
                "agent_type": cfg.agent_type,
                "display_name": cfg.display_name,
                "role": cfg.role,
                "capabilities": cfg.capabilities,
                "tools": cfg.tools,
                "max_retries": cfg.max_retries,
            }
            for cfg in self._configs.values()
        ]

    def validate_capability(self, agent_type: str, capability: str) -> bool:
        """
        Return True if the agent_type has the given capability.

        Raises AgentError if agent_type is not registered.
        """
        config = self.get_agent_config(agent_type)
        return capability in config.capabilities

    # ------------------------------------------------------------------
    # Spawning
    # ------------------------------------------------------------------

    def spawn_agent(
        self,
        agent_type: str,
        agent_id: str | None = None,
    ) -> SpecialistAgent:
        """
        Create and return a live SpecialistAgent instance for *agent_type*.

        The agent starts in the READY state.
        Call agent.spawn() to advance to SPAWNED.
        Call agent.assign(task) to assign a task.
        Call agent.execute() to run the pipeline.
        """
        config = self.get_agent_config(agent_type)
        agent = SpecialistAgent(
            config=config,
            tool_registry=self._tool_registry,
            model_registry=self._model_registry,
            memory_client=self._memory_client,
            agent_id=agent_id,
        )
        logger.info("registry.spawned", extra={"agent_type": agent_type, "agent_id": agent.agent_id})
        return agent

    def __len__(self) -> int:
        return len(self._configs)

    def __contains__(self, agent_type: str) -> bool:
        return agent_type in self._configs

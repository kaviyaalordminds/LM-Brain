"""
Specialist Agent — Agent Configuration Model

AgentConfig is the blueprint used to define each specialist.
The SpecialistAgentRegistry holds one AgentConfig per agent type.
The SpecialistAgent runtime uses this config to initialise itself.

NOTE: No circular imports — this module uses only stdlib dataclasses.
      Permission and ModelCapability are referenced by string or deferred import.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from specialist_agent.models.base import ModelCapability
    from specialist_agent.permissions.policy import Permission


@dataclass
class AgentConfig:
    """
    Blueprint for a specialist agent type.

    Used by the registry and runtime — not sent over the wire.
    """

    # Identity
    agent_type: str
    display_name: str
    description: str
    role: str

    # Capabilities (list of string capability names)
    capabilities: list[str] = field(default_factory=list)

    # Tool names this agent may use (from the ToolRegistry)
    tools: list[str] = field(default_factory=list)

    # Required model capabilities (in preference order)
    # Type annotation is Any at runtime to avoid circular import
    required_model_capabilities: list = field(default_factory=list)

    # Permissions granted to this agent type
    # Type annotation is Any at runtime to avoid circular import
    permissions: list = field(default_factory=list)

    # Retry policy
    max_retries: int = 2

    # Whether memory context should be fetched before execution
    use_memory_context: bool = True

    # Extra metadata
    metadata: dict = field(default_factory=dict)

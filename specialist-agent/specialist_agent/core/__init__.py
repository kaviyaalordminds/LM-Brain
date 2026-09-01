"""
Core package — generic runtime, lifecycle, executor, verifier, registry.

NOTE: Lazy imports here to avoid circular dependencies.
Import directly from submodules where needed.
"""
# Users should import directly:
#   from specialist_agent.core.agent import SpecialistAgent
#   from specialist_agent.core.lifecycle import AgentLifecycle, AgentState
#   from specialist_agent.core.errors import AgentError, InvalidTransitionError
#   from specialist_agent.core.registry import SpecialistAgentRegistry

"""
Specialist Agent Execution Layer
=================================

This package provides the Specialist Agent runtime for the Lordminds
Autonomous AI Workforce.  It is designed to be orchestrated by a future
Master Orchestrator, but every agent can also be executed independently
for local development and testing.

Architecture
------------
specialist_agent/
  core/        — generic runtime, lifecycle, executor, verifier, registry
  contracts/   — strongly-typed task, result, artifact, event models
  agents/      — ten specialist definitions (configurations of the runtime)
  tools/       — tool abstraction + registry + implementations
  models/      — model provider abstraction + registry + discovery
  permissions/ — permission policy + enforcement
  integration/ — thin Memory Agent client
  config/      — environment-driven settings

Usage
-----
  python -m specialist_agent.run_test --agent image_generation \\
         --task "Generate a futuristic electric car"
"""

__version__ = "0.1.0"
__all__ = ["__version__"]

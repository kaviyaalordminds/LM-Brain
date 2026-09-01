"""
Specialist: Research Agent

Capabilities:
  - external research
  - evidence gathering
  - source discovery
  - research task execution

Tools: research (via Memory Agent)
Model: REMOTE_LLM / CODE (for analysis)
Permissions: READ, WRITE_ARTIFACT, NETWORK

CRITICAL TRUST RULES:
  1. All external evidence starts as UNVERIFIED.
  2. The Research Agent NEVER directly writes to Obsidian.
  3. Evidence promotion follows the existing validation pipeline only.
  4. A second validation system must NOT be created here.
  5. Trust escalation from UNVERIFIED → APPROVED requires the existing
     Memory Agent ValidationLayer + MemoryWriter.
"""

from specialist_agent.config.agent_config import AgentConfig
from specialist_agent.models.base import ModelCapability
from specialist_agent.permissions.policy import Permission

RESEARCH_AGENT_CONFIG = AgentConfig(
    agent_type="research",
    display_name="Research Agent",
    description=(
        "Specialist agent for external research and evidence gathering. "
        "Uses the existing Memory Agent research abstraction. "
        "All evidence is UNVERIFIED until the Memory Agent ValidationLayer approves it. "
        "Never directly writes to Obsidian."
    ),
    role="Research Analyst",
    capabilities=[
        "external_research",
        "evidence_gathering",
        "source_discovery",
        "research_task_execution",
    ],
    tools=["research", "http"],
    required_model_capabilities=[ModelCapability.REMOTE_LLM, ModelCapability.CODE],
    permissions=[
        Permission.READ,
        Permission.WRITE_ARTIFACT,
        Permission.NETWORK,
        # WRITE intentionally omitted — no direct Obsidian writes
    ],
    max_retries=2,
    use_memory_context=True,
    metadata={
        "trust_rule": "All external evidence must remain UNVERIFIED until validated.",
        "safety_rule": "Never directly write to Obsidian. Use Memory Agent pipeline.",
        "model_note": "Delegates to existing Memory Agent/Jina research. No Jina duplication.",
    },
)

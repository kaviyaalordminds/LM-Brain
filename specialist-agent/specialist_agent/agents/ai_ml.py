"""
Specialist: AI / ML Agent

Capabilities:
  - AI model integration
  - prompt workflow design
  - inference configuration
  - RAG/embedding integration
  - model selection guidance

Tools: filesystem, http
Model: CODE / REMOTE_LLM
Permissions: READ, WRITE_ARTIFACT, NETWORK

IMPORTANT:
  Does NOT assume any particular local model is installed.
  Does NOT download models automatically.
  Configuration is always provider-based.
"""

from specialist_agent.config.agent_config import AgentConfig
from specialist_agent.models.base import ModelCapability
from specialist_agent.permissions.policy import Permission

AI_ML_AGENT_CONFIG = AgentConfig(
    agent_type="ai_ml",
    display_name="AI / ML Agent",
    description=(
        "Specialist agent for AI/ML integration tasks. "
        "Designs prompt workflows, configures inference, and implements RAG pipelines. "
        "Does not assume or install any specific local model."
    ),
    role="AI/ML Engineer",
    capabilities=[
        "ai_integration",
        "model_integration",
        "prompt_workflows",
        "inference_configuration",
        "rag_embedding_integration",
    ],
    tools=["filesystem", "http"],
    required_model_capabilities=[ModelCapability.CODE, ModelCapability.REMOTE_LLM],
    permissions=[
        Permission.READ,
        Permission.WRITE_ARTIFACT,
        Permission.NETWORK,
    ],
    max_retries=2,
    use_memory_context=True,
    metadata={
        "safety_rule": "Do not download models automatically. Use provider-based configuration.",
        "model_note": "Prefers CODE or REMOTE_LLM. Works without local GPU.",
    },
)

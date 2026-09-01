"""
Specialist: Image Generation Agent

Capabilities:
  - image generation
  - image asset creation
  - visual prompt processing
  - image artifact management

Tools: image_generation
Model: IMAGE_GENERATION (configured via IMAGE_MODEL_* env vars)
Permissions: READ, WRITE_ARTIFACT, NETWORK

IMPORTANT:
  If no image model is configured, the agent MUST return MODEL_UNAVAILABLE.
  It must NEVER fabricate an image artifact.
"""

from specialist_agent.config.agent_config import AgentConfig
from specialist_agent.models.base import ModelCapability
from specialist_agent.permissions.policy import Permission

IMAGE_GENERATION_AGENT_CONFIG = AgentConfig(
    agent_type="image_generation",
    display_name="Image Generation Agent",
    description=(
        "Specialist agent for generating images from text prompts. "
        "Returns MODEL_UNAVAILABLE when no image model provider is configured. "
        "Never fabricates image artifacts."
    ),
    role="Image Generator",
    capabilities=[
        "image_generation",
        "image_asset_creation",
        "visual_prompt_processing",
        "image_artifact_management",
    ],
    tools=["image_generation"],
    required_model_capabilities=[ModelCapability.IMAGE_GENERATION],
    permissions=[
        Permission.READ,
        Permission.WRITE_ARTIFACT,
        Permission.NETWORK,
    ],
    max_retries=1,   # Image generation retries are expensive — limit to 1
    use_memory_context=False,   # Image tasks are self-contained
    metadata={
        "model_note": (
            "Requires IMAGE_GENERATION model capability. "
            "Set IMAGE_MODEL_PROVIDER, IMAGE_MODEL_NAME, IMAGE_MODEL_ENDPOINT."
        ),
        "safety_rule": "NEVER fabricate image artifacts when model is unavailable.",
    },
)

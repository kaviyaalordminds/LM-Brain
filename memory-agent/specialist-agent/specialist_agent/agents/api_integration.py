"""
Specialist: API Integration Agent

Capabilities:
  - REST API integration
  - external service integration
  - request/response handling
  - API contracts
  - error handling

Tools: http, filesystem, shell
Model: CODE
Permissions: READ, WRITE, WRITE_ARTIFACT, NETWORK
"""

from specialist_agent.config.agent_config import AgentConfig
from specialist_agent.models.base import ModelCapability
from specialist_agent.permissions.policy import Permission

API_INTEGRATION_AGENT_CONFIG = AgentConfig(
    agent_type="api_integration",
    display_name="API Integration Agent",
    description=(
        "Specialist agent for integrating with REST APIs and external services. "
        "Handles request/response contracts, authentication, and error handling."
    ),
    role="API Integration Engineer",
    capabilities=[
        "rest_api_integration",
        "external_service_integration",
        "request_response_handling",
        "api_contracts",
        "error_handling",
    ],
    tools=["http", "filesystem", "shell"],
    required_model_capabilities=[ModelCapability.CODE],
    permissions=[
        Permission.READ,
        Permission.WRITE,
        Permission.WRITE_ARTIFACT,
        Permission.NETWORK,
    ],
    max_retries=2,
    use_memory_context=True,
    metadata={
        "model_note": "Requires CODE model capability.",
    },
)

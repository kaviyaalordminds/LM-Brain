"""
Specialist: Backend Agent

Capabilities:
  - backend services
  - business logic
  - authentication
  - server-side APIs
  - backend project structure

Tools: filesystem, shell, database, http
Model: CODE
Permissions: READ, WRITE, WRITE_ARTIFACT, EXECUTE, DATABASE, NETWORK
"""

from specialist_agent.config.agent_config import AgentConfig
from specialist_agent.models.base import ModelCapability
from specialist_agent.permissions.policy import Permission

BACKEND_AGENT_CONFIG = AgentConfig(
    agent_type="backend",
    display_name="Backend Agent",
    description=(
        "Specialist agent for server-side development. "
        "Implements APIs, business logic, authentication, and backend services."
    ),
    role="Backend Developer",
    capabilities=[
        "backend_services",
        "business_logic",
        "authentication",
        "server_side_apis",
        "backend_project_structure",
    ],
    tools=["filesystem", "shell", "database", "http"],
    required_model_capabilities=[ModelCapability.CODE],
    permissions=[
        Permission.READ,
        Permission.WRITE,
        Permission.WRITE_ARTIFACT,
        Permission.EXECUTE,
        Permission.DATABASE,
        Permission.NETWORK,
    ],
    max_retries=2,
    use_memory_context=True,
    metadata={
        "primary_language": "Python",
        "model_note": "Requires CODE model capability.",
    },
)

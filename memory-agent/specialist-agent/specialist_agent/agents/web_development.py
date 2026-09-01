"""
Specialist: Web Development Agent

Capabilities:
  - frontend development
  - UI implementation
  - web page creation
  - client-side logic
  - web project structure
  - responsive implementation

Tools: filesystem, shell
Model: CODE (local or remote LLM configured via CODE_MODEL_*)
Permissions: READ, WRITE, WRITE_ARTIFACT, EXECUTE, NETWORK
"""

from specialist_agent.config.agent_config import AgentConfig
from specialist_agent.models.base import ModelCapability
from specialist_agent.permissions.policy import Permission

WEB_DEVELOPMENT_AGENT_CONFIG = AgentConfig(
    agent_type="web_development",
    display_name="Web Development Agent",
    description=(
        "Specialist agent for frontend web development. "
        "Builds HTML/CSS/JS projects, UI components, and responsive layouts."
    ),
    role="Frontend Developer",
    capabilities=[
        "frontend_development",
        "ui_implementation",
        "web_page_creation",
        "client_side_logic",
        "web_project_structure",
        "responsive_implementation",
    ],
    tools=["filesystem", "shell", "http"],
    required_model_capabilities=[ModelCapability.CODE],
    permissions=[
        Permission.READ,
        Permission.WRITE,
        Permission.WRITE_ARTIFACT,
        Permission.EXECUTE,
        Permission.NETWORK,
    ],
    max_retries=2,
    use_memory_context=True,
    metadata={
        "primary_language": "HTML/CSS/JavaScript",
        "model_note": "Requires CODE model capability. Set CODE_MODEL_* env vars.",
    },
)

"""
Specialist: DevOps Agent

Capabilities:
  - Docker configuration
  - deployment configuration
  - CI/CD pipeline setup
  - infrastructure configuration
  - monitoring/logging setup

Tools: filesystem, shell
Model: CODE
Permissions: READ, WRITE, WRITE_ARTIFACT, EXECUTE

IMPORTANT:
  No ADMIN permission.
  Destructive deployment actions must NOT be auto-executed.
  Infrastructure changes require human review before application.
"""

from specialist_agent.config.agent_config import AgentConfig
from specialist_agent.models.base import ModelCapability
from specialist_agent.permissions.policy import Permission

DEVOPS_AGENT_CONFIG = AgentConfig(
    agent_type="devops",
    display_name="DevOps Agent",
    description=(
        "Specialist agent for DevOps and infrastructure configuration. "
        "Writes Dockerfiles, CI/CD configs, and deployment scripts. "
        "Does NOT auto-apply destructive infrastructure changes."
    ),
    role="DevOps Engineer",
    capabilities=[
        "docker",
        "deployment_configuration",
        "ci_cd",
        "infrastructure_configuration",
        "monitoring_logging_setup",
    ],
    tools=["filesystem", "shell"],
    required_model_capabilities=[ModelCapability.CODE],
    permissions=[
        Permission.READ,
        Permission.WRITE,
        Permission.WRITE_ARTIFACT,
        Permission.EXECUTE,
        # ADMIN intentionally omitted — no unrestricted deployment access
    ],
    max_retries=1,
    use_memory_context=True,
    metadata={
        "safety_rule": "Destructive deployment actions require human review before execution.",
        "model_note": "Requires CODE model capability.",
    },
)

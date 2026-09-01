"""
Specialist: Testing / QA Agent

Capabilities:
  - unit testing
  - integration testing
  - API testing
  - regression testing
  - artifact verification

Tools: shell, filesystem, http
Model: CODE
Permissions: READ, WRITE_ARTIFACT, EXECUTE, NETWORK
"""

from specialist_agent.config.agent_config import AgentConfig
from specialist_agent.models.base import ModelCapability
from specialist_agent.permissions.policy import Permission

TESTING_AGENT_CONFIG = AgentConfig(
    agent_type="testing",
    display_name="Testing / QA Agent",
    description=(
        "Specialist agent for automated testing and quality assurance. "
        "Writes, runs, and reports on unit, integration, and regression tests."
    ),
    role="QA Engineer",
    capabilities=[
        "unit_testing",
        "integration_testing",
        "api_testing",
        "regression_testing",
        "artifact_verification",
    ],
    tools=["shell", "filesystem", "http"],
    required_model_capabilities=[ModelCapability.CODE],
    permissions=[
        Permission.READ,
        Permission.WRITE_ARTIFACT,
        Permission.EXECUTE,
        Permission.NETWORK,
    ],
    max_retries=2,
    use_memory_context=False,   # Testing tasks are project-local
    metadata={
        "model_note": "Requires CODE model capability for test generation.",
    },
)

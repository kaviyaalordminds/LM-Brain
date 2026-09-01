"""
Specialist: Security Agent

Capabilities:
  - security review
  - permission checks
  - vulnerability checks
  - authentication review
  - authorization review
  - configuration audit

Tools: filesystem (read-only), http (audit only)
Model: CODE / REMOTE_LLM (for analysis)
Permissions: READ, AUDIT, WRITE_ARTIFACT

IMPORTANT:
  Default permissions are RESTRICTIVE.
  No WRITE, no EXECUTE, no DATABASE.
  No destructive actions permitted.
"""

from specialist_agent.config.agent_config import AgentConfig
from specialist_agent.models.base import ModelCapability
from specialist_agent.permissions.policy import Permission

SECURITY_AGENT_CONFIG = AgentConfig(
    agent_type="security",
    display_name="Security Agent",
    description=(
        "Specialist agent for security review and auditing. "
        "READ-only by default. Reports vulnerabilities and configuration issues. "
        "Never executes destructive actions."
    ),
    role="Security Auditor",
    capabilities=[
        "security_review",
        "permission_checks",
        "vulnerability_checks",
        "authentication_review",
        "authorization_review",
        "configuration_audit",
    ],
    tools=["filesystem"],   # Read-only — no shell, no http by default
    required_model_capabilities=[ModelCapability.CODE, ModelCapability.REMOTE_LLM],
    permissions=[
        Permission.READ,
        Permission.AUDIT,
        Permission.WRITE_ARTIFACT,
        # No WRITE, No EXECUTE, No DATABASE, No ADMIN
    ],
    max_retries=1,
    use_memory_context=True,
    metadata={
        "safety_rule": "No destructive or modifying actions permitted.",
        "model_note": "Prefers CODE or REMOTE_LLM for analysis.",
    },
)

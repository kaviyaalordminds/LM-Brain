"""
Specialist: Database Agent

Capabilities:
  - database schema design
  - table creation
  - migrations
  - indexes
  - queries
  - database validation

Tools: database, filesystem, shell
Model: CODE (for query generation and migration scripts)
Permissions: READ, WRITE, WRITE_ARTIFACT, DATABASE
"""

from specialist_agent.config.agent_config import AgentConfig
from specialist_agent.models.base import ModelCapability
from specialist_agent.permissions.policy import Permission

DATABASE_AGENT_CONFIG = AgentConfig(
    agent_type="database",
    display_name="Database Agent",
    description=(
        "Specialist agent for database design and operations. "
        "Handles schema, migrations, indexes, queries, and validation."
    ),
    role="Database Engineer",
    capabilities=[
        "database_schema",
        "table_creation",
        "migrations",
        "indexes",
        "queries",
        "database_validation",
    ],
    tools=["database", "filesystem", "shell"],
    required_model_capabilities=[ModelCapability.CODE],
    permissions=[
        Permission.READ,
        Permission.WRITE,
        Permission.WRITE_ARTIFACT,
        Permission.DATABASE,
    ],
    max_retries=2,
    use_memory_context=True,
    metadata={
        "model_note": "Requires CODE model capability for query/migration generation.",
    },
)

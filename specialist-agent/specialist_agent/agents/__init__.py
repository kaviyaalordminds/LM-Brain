"""Agents package — ten specialist agent definitions."""
from specialist_agent.agents.ai_ml import AI_ML_AGENT_CONFIG
from specialist_agent.agents.api_integration import API_INTEGRATION_AGENT_CONFIG
from specialist_agent.agents.backend import BACKEND_AGENT_CONFIG
from specialist_agent.agents.database import DATABASE_AGENT_CONFIG
from specialist_agent.agents.devops import DEVOPS_AGENT_CONFIG
from specialist_agent.agents.image_generation import IMAGE_GENERATION_AGENT_CONFIG
from specialist_agent.agents.research import RESEARCH_AGENT_CONFIG
from specialist_agent.agents.security import SECURITY_AGENT_CONFIG
from specialist_agent.agents.testing import TESTING_AGENT_CONFIG
from specialist_agent.agents.web_development import WEB_DEVELOPMENT_AGENT_CONFIG

ALL_AGENT_CONFIGS = {
    "web_development": WEB_DEVELOPMENT_AGENT_CONFIG,
    "image_generation": IMAGE_GENERATION_AGENT_CONFIG,
    "backend": BACKEND_AGENT_CONFIG,
    "database": DATABASE_AGENT_CONFIG,
    "api_integration": API_INTEGRATION_AGENT_CONFIG,
    "security": SECURITY_AGENT_CONFIG,
    "testing": TESTING_AGENT_CONFIG,
    "devops": DEVOPS_AGENT_CONFIG,
    "ai_ml": AI_ML_AGENT_CONFIG,
    "research": RESEARCH_AGENT_CONFIG,
}

__all__ = [
    "ALL_AGENT_CONFIGS",
    "WEB_DEVELOPMENT_AGENT_CONFIG",
    "IMAGE_GENERATION_AGENT_CONFIG",
    "BACKEND_AGENT_CONFIG",
    "DATABASE_AGENT_CONFIG",
    "API_INTEGRATION_AGENT_CONFIG",
    "SECURITY_AGENT_CONFIG",
    "TESTING_AGENT_CONFIG",
    "DEVOPS_AGENT_CONFIG",
    "AI_ML_AGENT_CONFIG",
    "RESEARCH_AGENT_CONFIG",
]

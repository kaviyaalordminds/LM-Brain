from typing import List

from executive_twins.schemas.specialist import CapabilityRequirement
from executive_twins.schemas.twin import ExecutiveTwinConfig
from executive_twins.twins.base import ExecutiveTwin


class CTOTwin(ExecutiveTwin):
    """
    CTO Digital Twin.
    Role: System architecture, technical strategy, engineering roadmap, security strategy, AI/ML.
    """

    def __init__(self) -> None:
        config = ExecutiveTwinConfig(
            twin_id="twin-cto-01",
            role="CTO Twin",
            description="Chief Technology Officer Twin for software architecture, technical decisions, and security.",
            activation_conditions=[
                "technology strategy",
                "technical decision",
                "system architecture",
                "engineering strategy",
                "ai/ml strategy",
                "security strategy",
                "technical roadmap",
                "software development",
            ],
            responsibilities=[
                "Software architecture design",
                "Technical trade-off evaluation",
                "Security compliance audit",
                "Engineering strategy roadmap",
            ],
            decision_scope=["System architecture", "Engineering stack", "Security guardrails"],
        )
        super().__init__(config)

    def should_activate(self, request_text: str) -> bool:
        req_lower = request_text.lower()
        return any(cond in req_lower for cond in self.config.activation_conditions)

    def generate_capability_requirements(self, request_text: str) -> List[CapabilityRequirement]:
        return [
            CapabilityRequirement(
                capability_name="system_architecture",
                description="Design robust system architecture and tech stack choices.",
            ),
            CapabilityRequirement(
                capability_name="software_development",
                description="Develop component application code and integrations.",
            ),
        ]

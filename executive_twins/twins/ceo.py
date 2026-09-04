from typing import List

from executive_twins.schemas.specialist import CapabilityRequirement
from executive_twins.schemas.twin import ExecutiveTwinConfig
from executive_twins.twins.base import ExecutiveTwin


class CEOTwin(ExecutiveTwin):
    """
    CEO Digital Twin.
    Role: Strategic leadership, vision, company priorities, organizational risk synthesis.
    Does NOT directly perform specialist execution.
    """

    def __init__(self) -> None:
        config = ExecutiveTwinConfig(
            twin_id="twin-ceo-01",
            role="CEO Twin",
            description="Chief Executive Officer Twin for strategic vision, company priorities, and high-level decisions.",
            activation_conditions=[
                "company strategy",
                "major priorities",
                "business decisions",
                "strategic trade-offs",
                "organization risk",
                "long-term direction",
                "vision",
            ],
            responsibilities=[
                "Define strategic priorities",
                "Conduct trade-off analysis",
                "Synthesize company risk",
                "Provide executive recommendations",
            ],
            decision_scope=["Company strategy", "Cross-department alignment", "Executive priorities"],
        )
        super().__init__(config)

    def should_activate(self, request_text: str) -> bool:
        req_lower = request_text.lower()
        return any(cond in req_lower for cond in self.config.activation_conditions)

    def generate_capability_requirements(self, request_text: str) -> List[CapabilityRequirement]:
        return [
            CapabilityRequirement(
                capability_name="strategic_planning",
                description="Formulate strategic roadmap and organizational alignment.",
            ),
            CapabilityRequirement(
                capability_name="risk_analysis",
                description="Assess organizational trade-offs and business risks.",
            ),
        ]

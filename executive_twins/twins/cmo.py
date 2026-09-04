from typing import List

from executive_twins.schemas.specialist import CapabilityRequirement
from executive_twins.schemas.twin import ExecutiveTwinConfig
from executive_twins.twins.base import ExecutiveTwin


class CMOTwin(ExecutiveTwin):
    """
    CMO Digital Twin.
    Role: Primary Executive Twin for Digital Marketing use cases.
    Marketing strategy, positioning, audience analysis, campaign planning, brand direction.
    Does NOT directly execute content or design tasks; delegates to matching registered specialists.
    """

    def __init__(self) -> None:
        config = ExecutiveTwinConfig(
            twin_id="twin-cmo-01",
            role="CMO Twin",
            description="Chief Marketing Officer Twin for strategic digital marketing, audience analysis, and campaign direction.",
            activation_conditions=[
                "marketing strategy",
                "positioning",
                "audience analysis",
                "campaign",
                "brand direction",
                "marketing planning",
                "marketing app",
                "marketing application",
                "digital marketing",
            ],
            responsibilities=[
                "Define target audience & positioning",
                "Formulate campaign strategy",
                "Direct marketing brand priorities",
                "Analyze marketing trade-offs",
                "Review specialist execution against marketing objective",
            ],
            decision_scope=["Marketing strategy", "Campaign priorities", "Brand positioning"],
        )
        super().__init__(config)

    def should_activate(self, request_text: str) -> bool:
        req_lower = request_text.lower()
        return any(cond in req_lower for cond in self.config.activation_conditions)

    def generate_capability_requirements(self, request_text: str) -> List[CapabilityRequirement]:
        """
        Generate required capabilities for digital marketing / marketing application requests.
        MUST NOT contain hardcoded specialist IDs or agent names.
        """
        reqs: List[CapabilityRequirement] = [
            CapabilityRequirement(
                capability_name="marketing_strategy",
                description="Develop comprehensive target audience analysis and marketing campaign strategy.",
            )
        ]

        req_lower = request_text.lower()
        if "app" in req_lower or "application" in req_lower or "website" in req_lower:
            reqs.append(
                CapabilityRequirement(
                    capability_name="visual_design",
                    description="Create visual assets, UI layouts, and brand design elements.",
                )
            )
            reqs.append(
                CapabilityRequirement(
                    capability_name="software_development",
                    description="Build and integrate frontend/backend marketing application code.",
                )
            )

        return reqs

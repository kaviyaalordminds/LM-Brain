from typing import List

from executive_twins.schemas.specialist import CapabilityRequirement
from executive_twins.schemas.twin import ExecutiveTwinConfig
from executive_twins.twins.base import ExecutiveTwin


class COOTwin(ExecutiveTwin):
    """
    COO Digital Twin.
    Role: Operational planning, process optimization, workflow bottleneck analysis, resource coordination.
    """

    def __init__(self) -> None:
        config = ExecutiveTwinConfig(
            twin_id="twin-coo-01",
            role="COO Twin",
            description="Chief Operating Officer Twin for process optimization and operational execution planning.",
            activation_conditions=[
                "operations",
                "workflows",
                "process optimization",
                "operational bottleneck",
                "execution planning",
                "resource coordination",
            ],
            responsibilities=[
                "Operational planning",
                "Process optimization",
                "Bottleneck analysis",
                "Resource efficiency",
            ],
            decision_scope=["Operational workflows", "Process efficiency", "Resource allocation"],
        )
        super().__init__(config)

    def should_activate(self, request_text: str) -> bool:
        req_lower = request_text.lower()
        return any(cond in req_lower for cond in self.config.activation_conditions)

    def generate_capability_requirements(self, request_text: str) -> List[CapabilityRequirement]:
        return [
            CapabilityRequirement(
                capability_name="operational_planning",
                description="Design operational workflow and milestone planning.",
            ),
            CapabilityRequirement(
                capability_name="process_optimization",
                description="Analyze execution bottlenecks and resource utilization.",
            ),
        ]

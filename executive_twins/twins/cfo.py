from typing import Any, Dict, List, Optional

from executive_twins.schemas.common import FactItem, FactState
from executive_twins.schemas.specialist import CapabilityRequirement
from executive_twins.schemas.twin import ExecutiveTwinConfig, TwinAnalysis
from executive_twins.twins.base import ExecutiveTwin


class CFOTwin(ExecutiveTwin):
    """
    CFO Digital Twin.
    Role: Financial analysis, budget evaluation, ROI forecasting, financial risk.
    HARD RULE: NEVER INVENT FINANCIAL VALUES.
    If financial data is unavailable, returns explicit data requirements.
    """

    def __init__(self) -> None:
        config = ExecutiveTwinConfig(
            twin_id="twin-cfo-01",
            role="CFO Twin",
            description="Chief Financial Officer Twin for financial analysis, budgeting, and project viability.",
            activation_conditions=[
                "financial analysis",
                "budget",
                "cost",
                "roi",
                "forecasting",
                "financial risk",
                "project viability",
                "pricing",
            ],
            responsibilities=[
                "Budget planning and allocation",
                "Financial forecasting & ROI modeling",
                "Financial risk assessment",
                "Project financial viability evaluation",
            ],
            decision_scope=["Financial budgets", "ROI thresholds", "Cost structures"],
        )
        super().__init__(config)

    def should_activate(self, request_text: str) -> bool:
        req_lower = request_text.lower()
        return any(cond in req_lower for cond in self.config.activation_conditions)

    def analyze(self, request_text: str, context: Optional[Dict[str, Any]] = None) -> TwinAnalysis:
        analysis = super().analyze(request_text, context)

        # Strictly verify if explicit financial data exists in context or input
        financial_keywords = ["budget", "cost", "revenue", "price", "margin", "cash_flow"]
        has_fin_data = False
        if context:
            has_fin_data = any(kw in str(context).lower() for kw in financial_keywords)

        if not has_fin_data:
            analysis.unknowns.append(
                FactItem(
                    statement="Explicit financial figures (budget limits, cost metrics, projected revenue) are missing.",
                    state=FactState.NOT_AVAILABLE,
                    source="environment",
                )
            )
            analysis.analysis_summary += " WARNING: Financial data unavailable. Strict rule enforced: Financial figures will not be fabricated."
            analysis.confidence = 0.4

        return analysis

    def generate_capability_requirements(self, request_text: str) -> List[CapabilityRequirement]:
        return [
            CapabilityRequirement(
                capability_name="financial_modeling",
                description="Conduct quantitative financial modeling and cost-benefit analysis.",
            ),
            CapabilityRequirement(
                capability_name="risk_analysis",
                description="Assess financial exposure and project ROI feasibility.",
            ),
        ]

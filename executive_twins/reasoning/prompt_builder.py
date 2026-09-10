"""
Structured Prompt Builder for Coding / Reasoning Model Integration.
Constructs separated, controlled context blocks preventing prompt injection and privilege escalation.
"""

import json
from typing import List, Tuple

from executive_twins.reasoning.models import ReasoningRequest
from executive_twins.schemas.common import FactItem, FactState
from executive_twins.schemas.evidence import BaseEvidence, TypedEvidence


class PromptBuilder:
    """
    Constructs standardized system and user prompts with distinct contextual sections.
    Ensures that safety constraints, validated knowledge, and registered capabilities are explicitly demarcated.
    """

    SYSTEM_RULES = """### SYSTEM RULES AND SAFETY CONSTRAINTS
1. You are a structured reasoning and planning engine for an autonomous workforce.
2. You do NOT directly execute tools, shell commands, or filesystem operations.
3. You must return ONLY structured declarative plans and decisions.
4. You may ONLY request capabilities from the registered AVAILABLE CAPABILITIES list.
5. You must NEVER generate raw shell commands (bash, powershell, cmd), subprocess calls, or system scripts.
6. You must strictly distinguish between VERIFIED facts, ASSUMPTIONS, and UNKNOWN states.
7. If required company knowledge or capabilities are missing, return NEEDS_INFORMATION or FAILED.
8. When recovering from failures, base your diagnosis strictly on the provided empirical evidence."""

    @classmethod
    def build_system_prompt(cls, request: ReasoningRequest) -> str:
        """Construct the authoritative system instruction block."""
        return cls.SYSTEM_RULES

    @classmethod
    def build_user_prompt(cls, request: ReasoningRequest) -> str:
        """Construct the segmented user context prompt."""
        sections: List[str] = []

        # 1. USER GOAL & MODE
        sections.append(
            f"### USER GOAL\nMode: {request.mode.value}\nGoal: {request.user_goal}"
        )

        # 2. SUCCESS CRITERIA
        if request.success_criteria:
            criteria_str = "\n".join(f"- {c}" for c in request.success_criteria)
            sections.append(f"### SUCCESS CRITERIA\n{criteria_str}")
        else:
            sections.append("### SUCCESS CRITERIA\n- Standard verification of all plan steps.")

        # 3. AVAILABLE CAPABILITIES
        if request.available_capabilities:
            caps_str = ", ".join(request.available_capabilities)
            sections.append(f"### AVAILABLE CAPABILITIES\n{caps_str}")
        else:
            sections.append("### AVAILABLE CAPABILITIES\n(None registered)")

        # 4. COMPANY KNOWLEDGE (Obsidian-backed validated facts)
        if request.relevant_company_knowledge:
            facts_lines = []
            for fact in request.relevant_company_knowledge:
                state_tag = f"[{fact.state.value}]" if hasattr(fact.state, "value") else f"[{fact.state}]"
                facts_lines.append(f"- {state_tag} {fact.statement} (Source: {fact.source})")
            sections.append("### VALIDATED COMPANY KNOWLEDGE\n" + "\n".join(facts_lines))
        else:
            sections.append("### VALIDATED COMPANY KNOWLEDGE\nNo specific company knowledge provided.")

        # 5. CURRENT STATE & CONTEXT
        if request.current_state or request.context:
            context_data = {
                "current_state": request.current_state,
                "context": request.context,
            }
            sections.append(
                f"### CURRENT STATE & CONTEXT\n```json\n{json.dumps(context_data, indent=2, default=str)}\n```"
            )

        # 6. PREVIOUS ACTIONS
        if request.previous_actions:
            sections.append(
                f"### PREVIOUS ACTIONS\n```json\n{json.dumps(request.previous_actions, indent=2, default=str)}\n```"
            )

        # 7. OBSERVATIONS & EVIDENCE
        if request.observations:
            obs_lines = []
            for obs in request.observations:
                if isinstance(obs, BaseEvidence):
                    obs_lines.append(
                        f"- [{obs.category.value}] ID: {obs.evidence_id} | {obs.description}"
                    )
                elif isinstance(obs, dict):
                    obs_lines.append(f"- {json.dumps(obs, default=str)}")
                else:
                    obs_lines.append(f"- {str(obs)}")
            sections.append("### EMPIRICAL OBSERVATIONS & EVIDENCE\n" + "\n".join(obs_lines))

        # 8. FAILURES & DIAGNOSTICS
        if request.failures:
            sections.append(
                f"### RECORDED FAILURES\n```json\n{json.dumps(request.failures, indent=2, default=str)}\n```"
            )

        # 9. OUTPUT FORMAT REQUIREMENT
        sections.append(
            """### REQUIRED OUTPUT FORMAT
Provide your response strictly structured with:
- Status (SUCCESS, NEEDS_INFORMATION, INVALID, FAILED, RECOVERY_REQUIRED)
- Structured Plan with ordered steps (step_id, objective, required_capability, dependencies, verification_requirement, risk_level)
- Rationale and confidence level
- Any unresolved questions or warnings"""
        )

        return "\n\n".join(sections)

    @classmethod
    def build_prompt_pair(cls, request: ReasoningRequest) -> Tuple[str, str]:
        """Convenience method returning both system and user prompts."""
        return cls.build_system_prompt(request), cls.build_user_prompt(request)

"""
Multi-stage validation engine for Reasoning Requests and Responses.
Provides defense-in-depth security checks, capability verification, dependency integrity, and resource bounds.
"""

import json
from typing import Any, Dict, List, Optional, Set, Tuple

from executive_twins.reasoning.interfaces import IReasoningValidator
from executive_twins.reasoning.models import (
    ReasoningConfig,
    ReasoningPlan,
    ReasoningRequest,
    ReasoningResponse,
    ReasoningStatus,
    ReasoningStep,
)
from executive_twins.schemas.common import FactState


# Defense-in-depth keyword blacklist for direct shell / execution attempts
FORBIDDEN_EXECUTION_PATTERNS = [
    "shell_exec",
    "powershell",
    "cmd.exe",
    "cmd /c",
    "bash -c",
    "sh -c",
    "system_call",
    "eval(",
    "exec(",
    "os.system",
    "os.popen",
    "subprocess.popen",
    "subprocess.call",
    "subprocess.run",
    "__import__",
]


class ReasoningValidator(IReasoningValidator):
    """
    Validation engine ensuring schema compliance, capability safety, plan integrity, and bounded resources.
    """

    def validate_request(
        self, request: ReasoningRequest, config: ReasoningConfig
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate incoming ReasoningRequest.
        """
        # 1. Non-empty goal check
        if not request.user_goal or not request.user_goal.strip():
            return False, "REQUEST_INVALID: user_goal cannot be empty."

        # 2. Size limit check
        try:
            req_json = request.model_dump_json()
            if len(req_json) > config.max_request_size:
                return (
                    False,
                    f"REQUEST_OVERSIZED: Request size {len(req_json)} exceeds maximum limit of {config.max_request_size} bytes.",
                )
        except Exception as e:
            return False, f"REQUEST_SERIALIZATION_FAILED: {str(e)}"

        # 3. Security context check
        if not request.security_context.is_authenticated:
            return False, "SECURITY_DENIED: SecurityContext is not authenticated."

        # 4. Defense-in-depth inspection of goal & context for blatant malicious injection
        goal_lower = request.user_goal.lower()
        for pattern in FORBIDDEN_EXECUTION_PATTERNS:
            if pattern in goal_lower:
                return (
                    False,
                    f"SECURITY_VIOLATION: Request goal contains forbidden execution directive '{pattern}'.",
                )

        return True, None

    def validate_response(
        self,
        response: ReasoningResponse,
        request: ReasoningRequest,
        config: ReasoningConfig,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate generated ReasoningResponse against request bounds, registered capabilities, and safety rules.
        """
        # 1. Response size check
        try:
            resp_json = response.model_dump_json()
            if len(resp_json) > config.max_response_size:
                return (
                    False,
                    f"RESPONSE_OVERSIZED: Response size {len(resp_json)} exceeds maximum limit of {config.max_response_size} bytes.",
                )
        except Exception as e:
            return False, f"RESPONSE_SERIALIZATION_FAILED: {str(e)}"

        # 2. Confidence bounds check
        if not (0.0 <= response.confidence <= 1.0):
            return (
                False,
                f"INVALID_CONFIDENCE: Confidence score {response.confidence} must be between 0.0 and 1.0.",
            )

        # 3. Status consistency
        if response.status == ReasoningStatus.SUCCESS:
            if not response.structured_plan and not response.decision:
                return (
                    False,
                    "MALFORMED_RESPONSE: SUCCESS status requires either a structured_plan or a decision.",
                )

        if response.status == ReasoningStatus.NEEDS_INFORMATION:
            if not response.required_information and not response.unresolved_questions:
                return (
                    False,
                    "MALFORMED_RESPONSE: NEEDS_INFORMATION status requires specified required_information or unresolved_questions.",
                )

        # 4. Plan validation (if present)
        if response.structured_plan:
            plan_valid, plan_error = self.validate_plan(
                response.structured_plan, request, config
            )
            if not plan_valid:
                return False, plan_error

        # 5. Security check on text fields in response
        response_text_to_check = [
            response.decision or "",
            response.failure_diagnosis or "",
        ]
        if response.structured_plan:
            for step in response.structured_plan.steps:
                response_text_to_check.extend([
                    step.objective,
                    step.rationale,
                    step.expected_output,
                    json.dumps(step.parameters, default=str),
                ])

        combined_text = " ".join(response_text_to_check).lower()
        for pattern in FORBIDDEN_EXECUTION_PATTERNS:
            if pattern in combined_text:
                return (
                    False,
                    f"SECURITY_VIOLATION: Reasoning response contains forbidden execution directive '{pattern}'.",
                )

        return True, None

    def validate_plan(
        self,
        plan: ReasoningPlan,
        request: ReasoningRequest,
        config: ReasoningConfig,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate plan structure, step limits, registered capability usage, and dependency DAG.
        """
        steps = plan.steps

        # 1. Step count limit
        if len(steps) > config.max_plan_steps:
            return (
                False,
                f"PLAN_TOO_LARGE: Plan step count {len(steps)} exceeds maximum allowed steps {config.max_plan_steps}.",
            )

        # 2. Step ID uniqueness and dependency DAG validation
        seen_step_ids: Set[str] = set()
        available_caps = set(request.available_capabilities) if request.available_capabilities else None

        for idx, step in enumerate(steps):
            if not step.step_id or not step.step_id.strip():
                return False, f"INVALID_STEP: Step at index {idx} has an empty step_id."

            if step.step_id in seen_step_ids:
                return (
                    False,
                    f"DUPLICATE_STEP_ID: Step ID '{step.step_id}' is defined multiple times in the plan.",
                )

            # Check required capability against registered available capabilities
            if available_caps is not None and len(available_caps) > 0:
                if step.required_capability not in available_caps:
                    return (
                        False,
                        f"UNAVAILABLE_CAPABILITY: Step '{step.step_id}' requests capability '{step.required_capability}' which is not in registered available capabilities.",
                    )

            # Check dependencies: must refer only to previous steps (no forward references, no cycles, no self references)
            for dep in step.dependencies:
                if dep == step.step_id:
                    return (
                        False,
                        f"CIRCULAR_DEPENDENCY: Step '{step.step_id}' cannot depend on itself.",
                    )
                if dep not in seen_step_ids:
                    return (
                        False,
                        f"INVALID_DEPENDENCY: Step '{step.step_id}' depends on '{dep}', which has not been defined previously in the plan.",
                    )

            seen_step_ids.add(step.step_id)

        return True, None

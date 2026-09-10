"""
Authoritative implementation of Reasoning Service and Plan Translation.
Enforces multi-stage validation, bounded execution loops, audit logging, and specialist delegation interfaces.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from executive_twins.memory.interfaces import IKnowledgeMemoryLayer
from executive_twins.reasoning.interfaces import (
    IPlanTranslator,
    IReasoningModel,
    IReasoningService,
    IReasoningValidator,
)
from executive_twins.reasoning.models import (
    ReasoningConfig,
    ReasoningMode,
    ReasoningPlan,
    ReasoningRequest,
    ReasoningResponse,
    ReasoningStatus,
    ReasoningStep,
)
from executive_twins.reasoning.prompt_builder import PromptBuilder
from executive_twins.reasoning.validators import ReasoningValidator
from executive_twins.schemas.common import FactItem, FactState
from executive_twins.schemas.evidence import EvidenceSet, TypedEvidence
from executive_twins.schemas.knowledge import CompanyKnowledgeRequest
from executive_twins.software_development.models import (
    DevelopmentPlan,
    DevelopmentPlanStatus,
    PlanStep,
    PlanStepAction,
    PlanStepStatus,
)
from executive_twins.utils.audit_logger import AuditLogger


# Mapping from capability names to Software Development PlanStepAction
CAPABILITY_TO_ACTION_MAP: Dict[str, PlanStepAction] = {
    "file_list": PlanStepAction.LIST_FILES,
    "inspect": PlanStepAction.INSPECT,
    "file_create": PlanStepAction.CREATE_FILE,
    "file_read": PlanStepAction.READ_FILE,
    "file_update": PlanStepAction.UPDATE_FILE,
    "file_delete": PlanStepAction.DELETE_FILE,
    "test_command_execution": PlanStepAction.RUN_TEST,
    "build_command_execution": PlanStepAction.RUN_BUILD,
    "lint_command_execution": PlanStepAction.RUN_LINT,
    "typecheck_command_execution": PlanStepAction.RUN_TYPECHECK,
    "workspace_build": PlanStepAction.WORKSPACE_BUILD,
    "git_status": PlanStepAction.GIT_STATUS,
    "git_diff": PlanStepAction.GIT_DIFF,
    "git_stage": PlanStepAction.GIT_STAGE,
    "git_commit": PlanStepAction.GIT_COMMIT,
    "git_branch": PlanStepAction.GIT_BRANCH,
    "git_log": PlanStepAction.GIT_LOG,
    "git_unstage": PlanStepAction.GIT_UNSTAGE,
    "docker_availability": PlanStepAction.DOCKER_AVAILABILITY,
    "docker_build": PlanStepAction.DOCKER_BUILD,
    "docker_run": PlanStepAction.DOCKER_RUN,
    "docker_inspect": PlanStepAction.DOCKER_INSPECT,
    "docker_stop": PlanStepAction.DOCKER_STOP,
    "docker_remove": PlanStepAction.DOCKER_REMOVE,
}


class PlanTranslator(IPlanTranslator):
    """
    Translates declarative ReasoningPlan models into domain-specific specialist execution plans.
    CRITICAL: Does NOT execute any tools or commands. Constructs typed data structures only.
    """

    def translate_to_development_plan(
        self, plan: ReasoningPlan, request_id: str
    ) -> DevelopmentPlan:
        """
        Convert a high-level ReasoningPlan into a strongly typed DevelopmentPlan for the SoftwareDevelopmentAgent.
        """
        steps: List[PlanStep] = []

        for step in plan.steps:
            # Map capability to typed action
            action = CAPABILITY_TO_ACTION_MAP.get(
                step.required_capability, PlanStepAction.INSPECT
            )
            plan_step = PlanStep(
                step_id=step.step_id,
                action=action,
                description=step.objective,
                inputs=dict(step.parameters),
                status=PlanStepStatus.PENDING,
            )
            steps.append(plan_step)

        return DevelopmentPlan(
            plan_id=plan.plan_id,
            request_id=request_id,
            steps=steps,
            status=DevelopmentPlanStatus.DRAFT,
        )


class ReasoningService(IReasoningService):
    """
    Authoritative Reasoning Service orchestrating planning, failure diagnosis, and recovery.
    Enforces strict separation between reasoning decisions and controlled system execution.
    """

    def __init__(
        self,
        model_adapter: IReasoningModel,
        validator: Optional[IReasoningValidator] = None,
        config: Optional[ReasoningConfig] = None,
        knowledge_layer: Optional[IKnowledgeMemoryLayer] = None,
        plan_translator: Optional[IPlanTranslator] = None,
    ) -> None:
        self.model_adapter = model_adapter
        self.validator = validator or ReasoningValidator()
        self.config = config or ReasoningConfig()
        self.knowledge_layer = knowledge_layer
        self.plan_translator = plan_translator or PlanTranslator()

    def reason(self, request: ReasoningRequest) -> ReasoningResponse:
        """
        Execute structured reasoning on a request.
        Lifecycle: Validate Request -> Build Prompt -> Invoke Model -> Validate Response -> Audit Log -> Return.
        """
        # 1. Audit log: REASONING_REQUEST
        AuditLogger.log_event(
            "REASONING_REQUEST",
            {
                "request_id": request.request_id,
                "goal": request.user_goal,
                "mode": request.mode.value,
                "provider": self.model_adapter.provider_name,
                "capabilities_count": len(request.available_capabilities),
            },
        )

        # 2. Validate Request
        is_req_valid, req_err = self.validator.validate_request(request, self.config)
        if not is_req_valid:
            AuditLogger.log_event(
                "REASONING_FAILURE",
                {
                    "request_id": request.request_id,
                    "reason": req_err,
                    "stage": "request_validation",
                },
            )
            return ReasoningResponse(
                request_id=request.request_id,
                status=ReasoningStatus.INVALID,
                reasoning_mode=request.mode,
                confidence=0.0,
                warnings=[req_err or "Invalid reasoning request."],
            )

        # 3. Build Prompts
        system_prompt, user_prompt = PromptBuilder.build_prompt_pair(request)

        # 4. Invoke Model Adapter
        try:
            raw_response = self.model_adapter.generate_reasoning(
                request, system_prompt, user_prompt
            )
        except Exception as e:
            AuditLogger.log_event(
                "REASONING_FAILURE",
                {
                    "request_id": request.request_id,
                    "error": str(e),
                    "stage": "model_invocation",
                },
            )
            return ReasoningResponse(
                request_id=request.request_id,
                status=ReasoningStatus.FAILED,
                reasoning_mode=request.mode,
                confidence=0.0,
                warnings=[f"Model execution failed: {str(e)}"],
            )

        # 5. Validate Response
        is_resp_valid, resp_err = self.validator.validate_response(
            raw_response, request, self.config
        )
        if not is_resp_valid:
            AuditLogger.log_event(
                "PLAN_REJECTED",
                {
                    "request_id": request.request_id,
                    "reason": resp_err,
                },
            )
            AuditLogger.log_event(
                "REASONING_FAILURE",
                {
                    "request_id": request.request_id,
                    "reason": resp_err,
                    "stage": "response_validation",
                },
            )
            return ReasoningResponse(
                request_id=request.request_id,
                status=ReasoningStatus.INVALID,
                reasoning_mode=request.mode,
                confidence=0.0,
                warnings=[resp_err or "Generated reasoning response failed validation."],
            )

        # 6. Audit Log: PLAN_VALIDATED or REASONING_RESPONSE
        if raw_response.structured_plan:
            AuditLogger.log_event(
                "PLAN_VALIDATED",
                {
                    "request_id": request.request_id,
                    "plan_id": raw_response.structured_plan.plan_id,
                    "steps_count": len(raw_response.structured_plan.steps),
                    "required_capabilities": raw_response.structured_plan.required_capabilities,
                },
            )

        AuditLogger.log_event(
            "REASONING_RESPONSE",
            {
                "request_id": request.request_id,
                "status": raw_response.status.value,
                "mode": raw_response.reasoning_mode.value,
                "confidence": raw_response.confidence,
            },
        )

        return raw_response

    def replan_from_failure(
        self,
        request: ReasoningRequest,
        failure_evidence: EvidenceSet,
        failure_reason: str,
        current_iteration: int = 1,
    ) -> ReasoningResponse:
        """
        Perform evidence-driven failure recovery and re-planning within strict iteration limits.
        """
        # 1. Check recovery iteration bounds to prevent infinite loops
        if current_iteration > self.config.max_recovery_iterations:
            AuditLogger.log_event(
                "REASONING_FAILURE",
                {
                    "request_id": request.request_id,
                    "reason": "MAX_RECOVERY_ITERATIONS_EXCEEDED",
                    "iterations": current_iteration,
                },
            )
            return ReasoningResponse(
                request_id=request.request_id,
                status=ReasoningStatus.FAILED,
                reasoning_mode=ReasoningMode.RECOVER,
                confidence=0.0,
                warnings=[
                    f"RECOVERY_LIMIT_EXCEEDED: Maximum recovery attempts ({self.config.max_recovery_iterations}) reached."
                ],
                failure_diagnosis=f"Exhausted recovery attempts for: {failure_reason}",
            )

        # 2. Audit log: RECOVERY_REQUEST
        AuditLogger.log_event(
            "RECOVERY_REQUEST",
            {
                "request_id": request.request_id,
                "failure_reason": failure_reason,
                "iteration": current_iteration,
                "evidence_count": len(failure_evidence.items),
            },
        )

        # 3. Construct recovery request with empirical evidence
        combined_observations = list(request.observations) + list(failure_evidence.items)
        combined_failures = list(request.failures) + [
            {
                "reason": failure_reason,
                "iteration": current_iteration,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ]

        recovery_request = ReasoningRequest(
            request_id=f"{request.request_id}_rec_{current_iteration}",
            user_goal=request.user_goal,
            context=dict(request.context),
            available_capabilities=list(request.available_capabilities),
            relevant_company_knowledge=list(request.relevant_company_knowledge),
            current_state={"recovery_iteration": current_iteration, "failure_reason": failure_reason},
            previous_actions=list(request.previous_actions),
            observations=combined_observations,
            failures=combined_failures,
            success_criteria=list(request.success_criteria),
            mode=ReasoningMode.RECOVER,
            security_context=request.security_context,
            metadata={"original_request_id": request.request_id, "iteration": current_iteration},
        )

        # 4. Reason over recovery request
        response = self.reason(recovery_request)

        # 5. Log REPLAN_GENERATED on success
        if response.status == ReasoningStatus.SUCCESS and response.structured_plan:
            AuditLogger.log_event(
                "REPLAN_GENERATED",
                {
                    "request_id": recovery_request.request_id,
                    "plan_id": response.structured_plan.plan_id,
                    "steps_count": len(response.structured_plan.steps),
                    "iteration": current_iteration,
                },
            )

        return response

    def fetch_company_knowledge(
        self, query: str, context: Optional[str] = None
    ) -> List[FactItem]:
        """
        Retrieve validated facts from the authoritative Company Knowledge Layer.
        Ensures facts are verified and not hallucinated.
        """
        if not self.knowledge_layer:
            return []

        knowledge_req = CompanyKnowledgeRequest(
            request_id=f"k_req_{uuid.uuid4().hex[:8]}",
            task_context=context or "Reasoning planning context",
            required_knowledge=query,
            min_confidence=self.config.min_confidence,
        )
        knowledge_resp = self.knowledge_layer.request_company_knowledge(knowledge_req)
        # Return only validated facts
        return [
            fact
            for fact in knowledge_resp.facts
            if fact.state == FactState.FACT
        ]

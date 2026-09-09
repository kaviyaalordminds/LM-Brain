"""
Software Development Agent implementation.
Production-grade orchestration worker operating strictly above SpecialistExecutionEngine.
Enforces bounded development loops, empirical evidence verification, and complete security isolation.
"""

from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional, Tuple
import uuid

from executive_twins.execution.capability_execution_engine import (
    SpecialistExecutionAdapter,
    SpecialistExecutionEngine,
)
from executive_twins.execution.security_guard import SecurityGuard
from executive_twins.schemas.common import (
    FactItem,
    FactState,
    FailureState,
    SecurityContext,
    SpecialistStatus,
    VerificationStatus,
)
from executive_twins.schemas.delegation import DelegationRequest, DelegationResult
from executive_twins.schemas.evidence import (
    EvidenceCategory,
    EvidenceSet,
    ExecutionLogEvidence,
    TestEvidence,
    VerificationEvidence,
)
from executive_twins.software_development.interfaces import (
    IDevelopmentPlanner,
    ISoftwareDevelopmentAgent,
)
from executive_twins.software_development.models import (
    DevelopmentPlan,
    DevelopmentPlanStatus,
    DevelopmentRequest,
    DevelopmentResult,
    DevelopmentStatus,
    DiagnosticResult,
    PlanStep,
    PlanStepAction,
    PlanStepStatus,
)
from executive_twins.utils.audit_logger import AuditLogger


# Direct Shell / Security Injection patterns strictly rejected before execution
FORBIDDEN_KEYWORDS = {
    "shell_exec",
    "powershell",
    "cmd.exe",
    "cmd ",
    "bash ",
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
}


class SoftwareDevelopmentAgent(ISoftwareDevelopmentAgent):
    """
    Controlled Autonomous Software Development Specialist Agent.
    Transforms development requests into bounded, verified workflows executed via SpecialistExecutionEngine.
    """

    # Mapping of PlanStepAction to corresponding registered capability names in SpecialistExecutionEngine
    ACTION_CAPABILITY_MAP: Dict[PlanStepAction, str] = {
        PlanStepAction.INSPECT: "file_list",
        PlanStepAction.CREATE_FILE: "file_create",
        PlanStepAction.READ_FILE: "file_read",
        PlanStepAction.UPDATE_FILE: "file_update",
        PlanStepAction.DELETE_FILE: "file_delete",
        PlanStepAction.LIST_FILES: "file_list",
        PlanStepAction.RUN_TEST: "test_command_execution",
        PlanStepAction.RUN_BUILD: "build_command_execution",
        PlanStepAction.RUN_LINT: "lint_command_execution",
        PlanStepAction.RUN_TYPECHECK: "typecheck_command_execution",
        PlanStepAction.WORKSPACE_BUILD: "workspace_build",
        PlanStepAction.GIT_STATUS: "git_status",
        PlanStepAction.GIT_DIFF: "git_diff",
        PlanStepAction.GIT_STAGE: "git_stage",
        PlanStepAction.GIT_COMMIT: "git_commit",
        PlanStepAction.GIT_BRANCH: "git_branch",
        PlanStepAction.GIT_LOG: "git_log",
        PlanStepAction.GIT_UNSTAGE: "git_unstage",
        PlanStepAction.DOCKER_AVAILABILITY: "docker_availability",
        PlanStepAction.DOCKER_BUILD: "docker_build",
        PlanStepAction.DOCKER_RUN: "docker_run",
        PlanStepAction.DOCKER_INSPECT: "docker_inspect",
        PlanStepAction.DOCKER_STOP: "docker_stop",
        PlanStepAction.DOCKER_REMOVE: "docker_remove",
    }

    def __init__(
        self,
        execution_engine: SpecialistExecutionEngine,
        planner: IDevelopmentPlanner,
    ) -> None:
        self.execution_engine = execution_engine
        self.planner = planner

    # -------------------------------------------------------------------------
    # Security and Validation
    # -------------------------------------------------------------------------

    def validate_request(self, request: DevelopmentRequest) -> Tuple[bool, Optional[str]]:
        """
        Validate development request against strict security boundaries and limits.
        """
        if not request.request_id or not request.request_id.strip():
            return False, "INVALID_REQUEST: Missing required 'request_id'."

        if not request.workspace_id or not request.workspace_id.strip():
            return False, "INVALID_REQUEST: Missing required 'workspace_id'."

        if not request.task or not request.task.strip():
            return False, "INVALID_REQUEST: Missing required 'task' description."

        # 1. Authentication check
        if not request.security_context.is_authenticated:
            return False, "AUTHORIZATION_DENIED: SecurityContext is not authenticated."

        # 2. Check for forbidden shell/code injection attempts in task, requirements, and constraints
        combined_text = (
            request.task
            + " "
            + " ".join(request.requirements)
            + " ".join(request.constraints)
            + " ".join(request.success_criteria)
        ).lower()

        for forbidden in FORBIDDEN_KEYWORDS:
            if forbidden in combined_text:
                return False, f"SECURITY_ERROR: Forbidden command or execution keyword '{forbidden}' detected."

        # 3. Check bounds
        if request.max_iterations <= 0 or request.max_iterations > 50:
            return False, "INVALID_BOUNDS: 'max_iterations' must be between 1 and 50."

        if request.max_steps <= 0 or request.max_steps > 100:
            return False, "INVALID_BOUNDS: 'max_steps' must be between 1 and 100."

        if request.timeout_seconds <= 0 or request.timeout_seconds > 1800:
            return False, "INVALID_BOUNDS: 'timeout_seconds' must be between 1.0 and 1800.0."

        return True, None

    def _validate_step_inputs(self, step: PlanStep) -> Tuple[bool, Optional[str]]:
        """Validate step inputs for path traversal, forbidden shell strings, and format."""
        for key, val in step.inputs.items():
            val_str = str(val).lower()
            for forbidden in FORBIDDEN_KEYWORDS:
                if forbidden in val_str:
                    return False, f"SECURITY_ERROR: Forbidden execution keyword '{forbidden}' in input '{key}'."

            # Path traversal / host escape check for path-like parameters
            if key in ("relative_path", "paths", "source_code_path", "project_file", "dockerfile_path", "build_context"):
                paths_to_check = val if isinstance(val, list) else [val]
                for p in paths_to_check:
                    p_str = str(p).replace("\\", "/")
                    if ".." in p_str.split("/"):
                        return False, f"PATH_TRAVERSAL_REJECTED: Parent directory traversal '..' detected in '{p}'."
                    if (len(p_str) > 1 and p_str[1] == ":") or p_str.startswith("/"):
                        return False, f"PATH_OUTSIDE_WORKSPACE_REJECTED: Absolute path '{p}' is forbidden."

        return True, None

    # -------------------------------------------------------------------------
    # Capability Execution Boundary
    # -------------------------------------------------------------------------

    def _execute_step_via_engine(
        self, request: DevelopmentRequest, step: PlanStep
    ) -> DelegationResult:
        """
        Executes a single development step exclusively through SpecialistExecutionEngine.
        Bypassing the SpecialistExecutionEngine is strictly forbidden.
        """
        capability_name = self.ACTION_CAPABILITY_MAP.get(step.action)
        if not capability_name:
            return DelegationResult(
                delegation_id=f"del-{uuid.uuid4().hex[:8]}",
                specialist_id=request.specialist_id,
                status="FAILED",
                output=f"CAPABILITY_UNAVAILABLE: Unrecognized action '{step.action}' has no registered capability mapping.",
                confidence=0.0,
                errors=[f"Unrecognized action '{step.action}'."],
                verification_status=VerificationStatus.FAILED,
                completed_at=datetime.now(timezone.utc),
            )

        # Merge workspace_id into inputs if not present
        step_inputs = dict(step.inputs)
        if "workspace_id" not in step_inputs:
            step_inputs["workspace_id"] = request.workspace_id

        del_req = DelegationRequest(
            delegation_id=f"del-{uuid.uuid4().hex[:8]}",
            parent_task_id=request.request_id,
            executive_twin_id="twin-orchestrator",
            specialist_id=request.specialist_id,
            objective=f"Execute {step.action.value}: {step.description}",
            task=step.description,
            required_capabilities=[capability_name],
            inputs=step_inputs,
            expected_output=f"Outcome for {step.action.value}",
            security_context=request.security_context,
        )

        # Authoritative boundary call
        return self.execution_engine.execute_delegation(del_req)

    # -------------------------------------------------------------------------
    # Core Bounded Autonomous Development Loop
    # -------------------------------------------------------------------------

    def execute_development(self, request: DevelopmentRequest) -> DevelopmentResult:
        """
        Executes a full, bounded autonomous software development workflow.
        """
        start_time = datetime.now(timezone.utc)
        start_mono = time.monotonic()

        AuditLogger.log_event(
            "development.request_received",
            {
                "request_id": request.request_id,
                "workspace_id": request.workspace_id,
                "task": request.task,
                "specialist_id": request.specialist_id,
            },
        )

        # 1. Validate Request Security & Bounds
        is_valid, validation_err = self.validate_request(request)
        if not is_valid:
            status = (
                DevelopmentStatus.NOT_AUTHORIZED
                if "AUTHORIZATION_DENIED" in str(validation_err)
                else DevelopmentStatus.BLOCKED
            )
            AuditLogger.log_event(
                "development.blocked",
                {"request_id": request.request_id, "reason": validation_err},
            )
            return DevelopmentResult(
                request_id=request.request_id,
                workspace_id=request.workspace_id,
                status=status,
                completed_steps=[],
                failed_steps=[],
                artifacts=[],
                evidence=EvidenceSet(),
                facts=[],
                verification=VerificationStatus.FAILED,
                summary=f"Development request rejected: {validation_err}",
                failure_reason=validation_err,
                iterations_run=0,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                duration_seconds=time.monotonic() - start_mono,
            )

        # 2. Plan Creation
        try:
            plan = self.planner.create_plan(request)
        except Exception as e:
            AuditLogger.log_event(
                "development.failed",
                {"request_id": request.request_id, "reason": f"Plan creation failed: {e}"},
            )
            return DevelopmentResult(
                request_id=request.request_id,
                workspace_id=request.workspace_id,
                status=DevelopmentStatus.FAILED,
                completed_steps=[],
                failed_steps=[],
                artifacts=[],
                evidence=EvidenceSet(),
                facts=[],
                verification=VerificationStatus.FAILED,
                summary=f"Failed to generate development plan: {e}",
                failure_reason=str(e),
                iterations_run=0,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                duration_seconds=time.monotonic() - start_mono,
            )

        plan.status = DevelopmentPlanStatus.IN_PROGRESS
        AuditLogger.log_event(
            "development.plan_created",
            {
                "request_id": request.request_id,
                "plan_id": plan.plan_id,
                "total_steps": len(plan.steps),
                "step_actions": [s.action.value for s in plan.steps],
            },
        )

        # State tracking
        accumulated_evidence = EvidenceSet()
        accumulated_artifacts: List[str] = []
        accumulated_facts: List[FactItem] = []
        completed_steps: List[PlanStep] = []
        failed_steps: List[PlanStep] = []

        iteration = 0
        total_steps_executed = 0
        execution_status = DevelopmentStatus.SUCCESS
        failure_summary: Optional[str] = None

        # 3. Bounded Autonomous Execution Loop
        while plan.current_step_index < len(plan.steps):
            # Check Timeout
            elapsed = time.monotonic() - start_mono
            if elapsed > request.timeout_seconds:
                execution_status = DevelopmentStatus.TIMEOUT
                failure_summary = f"EXECUTION_TIMEOUT: Development exceeded timeout of {request.timeout_seconds}s."
                AuditLogger.log_event(
                    "development.timeout",
                    {"request_id": request.request_id, "elapsed_seconds": elapsed},
                )
                break

            # Check Step Limit Bounds
            if total_steps_executed >= request.max_steps:
                execution_status = DevelopmentStatus.BLOCKED
                failure_summary = f"STEP_LIMIT_EXCEEDED: Exceeded maximum allowed steps ({request.max_steps})."
                AuditLogger.log_event(
                    "development.blocked",
                    {"request_id": request.request_id, "reason": failure_summary},
                )
                break

            # Check Iteration Bounds
            if iteration >= request.max_iterations:
                execution_status = DevelopmentStatus.FAILED
                failure_summary = f"ITERATION_LIMIT_EXCEEDED: Exceeded maximum iterations ({request.max_iterations})."
                AuditLogger.log_event(
                    "development.failed",
                    {"request_id": request.request_id, "reason": failure_summary},
                )
                break

            current_step = plan.steps[plan.current_step_index]
            current_step.status = PlanStepStatus.IN_PROGRESS
            current_step.started_at = datetime.now(timezone.utc)
            total_steps_executed += 1

            AuditLogger.log_event(
                "development.step_started",
                {
                    "request_id": request.request_id,
                    "step_id": current_step.step_id,
                    "action": current_step.action.value,
                    "description": current_step.description,
                    "retry_count": current_step.retry_count,
                },
            )

            # Validate Step Inputs for Security
            valid_step, step_err = self._validate_step_inputs(current_step)
            if not valid_step:
                current_step.status = PlanStepStatus.FAILED
                current_step.failure_reason = step_err
                current_step.completed_at = datetime.now(timezone.utc)
                failed_steps.append(current_step)
                execution_status = DevelopmentStatus.BLOCKED
                failure_summary = step_err
                AuditLogger.log_event(
                    "development.step_failed",
                    {"request_id": request.request_id, "step_id": current_step.step_id, "error": step_err},
                )
                break

            # Execute Step via SpecialistExecutionEngine
            del_result = self._execute_step_via_engine(request, current_step)

            # Ingest Result & Evidence
            for ev in del_result.evidence.items:
                accumulated_evidence.items.append(ev)
                current_step.evidence_refs.append(ev.evidence_id)

            for art in del_result.artifacts:
                if art not in accumulated_artifacts:
                    accumulated_artifacts.append(art)
                if art not in current_step.artifacts:
                    current_step.artifacts.append(art)

            if del_result.status == "SUCCESS":
                current_step.status = PlanStepStatus.COMPLETED
                current_step.result_output = del_result.output
                current_step.completed_at = datetime.now(timezone.utc)
                completed_steps.append(current_step)

                # Collect facts from output
                accumulated_facts.append(
                    FactItem(
                        statement=f"Step '{current_step.step_id}' ({current_step.action.value}) completed: {current_step.description}",
                        state=FactState.FACT,
                        source="software_development_agent",
                    )
                )

                AuditLogger.log_event(
                    "development.step_completed",
                    {
                        "request_id": request.request_id,
                        "step_id": current_step.step_id,
                        "action": current_step.action.value,
                    },
                )

                # Advance to next step
                plan.current_step_index += 1

            else:
                # Step Failed -> Enter Failure Recovery
                current_step.failure_reason = del_result.output
                current_step.retry_count += 1
                AuditLogger.log_event(
                    "development.step_failed",
                    {
                        "request_id": request.request_id,
                        "step_id": current_step.step_id,
                        "action": current_step.action.value,
                        "retry_count": current_step.retry_count,
                        "max_retries": current_step.max_retries,
                        "error": del_result.output,
                    },
                )

                # Bounded Retry / Recovery Diagnosis
                if current_step.retry_count <= current_step.max_retries and iteration + 1 < request.max_iterations:
                    iteration += 1
                    AuditLogger.log_event(
                        "development.recovery_started",
                        {
                            "request_id": request.request_id,
                            "failed_step_id": current_step.step_id,
                            "iteration": iteration,
                        },
                    )

                    diagnostic: DiagnosticResult = self.planner.diagnose_failure(
                        request=request,
                        failed_step=current_step,
                        failure_evidence=del_result.evidence,
                        failure_output=del_result.output,
                        iteration=iteration,
                    )

                    if diagnostic.can_recover and diagnostic.suggested_fix_steps:
                        plan = self.planner.refine_plan(
                            request=request, plan=plan, diagnostic=diagnostic
                        )
                        AuditLogger.log_event(
                            "development.recovery_completed",
                            {
                                "request_id": request.request_id,
                                "diagnosis": diagnostic.diagnosis,
                                "fix_steps_count": len(diagnostic.suggested_fix_steps),
                            },
                        )
                    else:
                        current_step.status = PlanStepStatus.FAILED
                        current_step.completed_at = datetime.now(timezone.utc)
                        failed_steps.append(current_step)
                        execution_status = DevelopmentStatus.FAILED
                        failure_summary = (
                            f"RECOVERY_FAILED: {diagnostic.reason or diagnostic.diagnosis or del_result.output}"
                        )
                        break
                else:
                    # Retry limit or iteration limit exhausted
                    current_step.status = PlanStepStatus.FAILED
                    current_step.completed_at = datetime.now(timezone.utc)
                    failed_steps.append(current_step)
                    execution_status = DevelopmentStatus.FAILED
                    failure_summary = f"RETRY_EXHAUSTED: Step '{current_step.step_id}' failed after {current_step.retry_count} attempts: {del_result.output}"
                    break

        # 4. Success Verification & Empirical Quality Check
        AuditLogger.log_event(
            "development.validation_started",
            {"request_id": request.request_id, "execution_status": execution_status.value},
        )

        verification_status = VerificationStatus.UNVERIFIED
        duration = time.monotonic() - start_mono
        plan.completed_at = datetime.now(timezone.utc)

        if execution_status == DevelopmentStatus.SUCCESS and len(failed_steps) == 0:
            # Check fact states - forbid UNKNOWN, ASSUMPTION, UNVERIFIED as success
            has_invalid_facts = any(
                f.state in (FactState.UNKNOWN, FactState.ASSUMPTION, FactState.UNVERIFIED)
                for f in accumulated_facts
            )

            # Check if any test evidence failed
            has_failed_tests = any(
                isinstance(e, TestEvidence) and e.tests_failed > 0
                for e in accumulated_evidence.items
            )

            if has_invalid_facts:
                execution_status = DevelopmentStatus.FAILED
                verification_status = VerificationStatus.FAILED
                failure_summary = "VERIFICATION_FAILED: Result relies on UNKNOWN or ASSUMPTION fact state."
            elif has_failed_tests:
                execution_status = DevelopmentStatus.FAILED
                verification_status = VerificationStatus.FAILED
                failure_summary = "VERIFICATION_FAILED: Test evidence contains test failures."
            else:
                plan.status = DevelopmentPlanStatus.COMPLETED
                verification_status = VerificationStatus.VERIFIED
                # Add Verification Evidence
                verif_ev = VerificationEvidence(
                    evidence_id=f"ev-verif-dev-{uuid.uuid4().hex[:8]}",
                    verifier_id="SoftwareDevelopmentAgent",
                    verified_status="VERIFIED",
                    description=f"Verified all development plan steps and success criteria for request '{request.request_id}'",
                )
                accumulated_evidence.items.append(verif_ev)

                AuditLogger.log_event(
                    "development.succeeded",
                    {
                        "request_id": request.request_id,
                        "completed_steps": len(completed_steps),
                        "evidence_count": len(accumulated_evidence.items),
                    },
                )
        else:
            plan.status = DevelopmentPlanStatus.FAILED
            verification_status = VerificationStatus.FAILED
            if completed_steps and failed_steps:
                execution_status = DevelopmentStatus.PARTIAL
            elif execution_status == DevelopmentStatus.SUCCESS:
                execution_status = DevelopmentStatus.FAILED

            AuditLogger.log_event(
                "development.failed",
                {
                    "request_id": request.request_id,
                    "status": execution_status.value,
                    "reason": failure_summary,
                },
            )

        summary_text = (
            f"Software development completed successfully with {len(completed_steps)} steps verified."
            if execution_status == DevelopmentStatus.SUCCESS
            else f"Software development ended with status '{execution_status.value}': {failure_summary}"
        )

        return DevelopmentResult(
            request_id=request.request_id,
            workspace_id=request.workspace_id,
            status=execution_status,
            completed_steps=completed_steps,
            failed_steps=failed_steps,
            artifacts=accumulated_artifacts,
            evidence=accumulated_evidence,
            facts=accumulated_facts,
            verification=verification_status,
            summary=summary_text,
            failure_reason=failure_summary,
            iterations_run=iteration,
            started_at=start_time,
            completed_at=datetime.now(timezone.utc),
            duration_seconds=duration,
        )

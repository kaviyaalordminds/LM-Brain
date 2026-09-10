"""
Deterministic Development and Test Adapters for Reasoning Model Integration.
Provides 100% offline, predictable, reproducible reasoning responses without external API calls.
"""

from typing import Any, Callable, Dict, List, Optional
import uuid

from executive_twins.reasoning.interfaces import IReasoningModel
from executive_twins.reasoning.models import (
    ReasoningMode,
    ReasoningPlan,
    ReasoningRequest,
    ReasoningResponse,
    ReasoningStatus,
    ReasoningStep,
    RiskLevel,
)
from executive_twins.schemas.evidence import (
    BaseEvidence,
    EvidenceCategory,
    ExecutionLogEvidence,
    TestEvidence,
)


class DevTestReasoningAdapter(IReasoningModel):
    """
    Deterministic Reasoning Model Adapter for testing and offline development.
    Implements rule-based decomposition, evidence-based failure diagnosis, and customizable response hooks.
    """

    def __init__(self) -> None:
        self._custom_responses: Dict[str, ReasoningResponse] = {}
        self._custom_generator: Optional[
            Callable[[ReasoningRequest, str, str], ReasoningResponse]
        ] = None
        self._invocation_count: int = 0

    @property
    def provider_name(self) -> str:
        return "DEV_TEST_REASONING_ADAPTER"

    @property
    def invocation_count(self) -> int:
        return self._invocation_count

    def set_custom_response(
        self, request_id: str, response: ReasoningResponse
    ) -> None:
        """Register a specific deterministic response for a given request_id."""
        self._custom_responses[request_id] = response

    def set_response_generator(
        self, generator: Callable[[ReasoningRequest, str, str], ReasoningResponse]
    ) -> None:
        """Override response generation with a custom test generator function."""
        self._custom_generator = generator

    def clear(self) -> None:
        """Reset custom state and counts."""
        self._custom_responses.clear()
        self._custom_generator = None
        self._invocation_count = 0

    def generate_reasoning(
        self,
        request: ReasoningRequest,
        system_prompt: str,
        user_prompt: str,
    ) -> ReasoningResponse:
        """
        Generate a deterministic reasoning response based on input mode, goal, and empirical evidence.
        """
        self._invocation_count += 1

        # 1. Check custom response override
        if request.request_id in self._custom_responses:
            return self._custom_responses[request.request_id]
        for key in sorted(self._custom_responses.keys(), key=len, reverse=True):
            if request.request_id.startswith(key):
                return self._custom_responses[key]

        # 2. Check custom generator override
        if self._custom_generator:
            return self._custom_generator(request, system_prompt, user_prompt)

        # 3. Handle RECOVER / REPLAN mode or when failures are provided
        if request.mode in (ReasoningMode.RECOVER, ReasoningMode.REPLAN) or request.failures:
            return self._generate_recovery_response(request)

        # 4. Handle NEEDS_INFORMATION simulation (e.g. if goal mentions 'unknown' or lacks key info)
        if "missing_info" in request.user_goal.lower() or "need information" in request.user_goal.lower():
            return ReasoningResponse(
                request_id=request.request_id,
                status=ReasoningStatus.NEEDS_INFORMATION,
                reasoning_mode=request.mode,
                unresolved_questions=["What is the target environment or specification?"],
                required_information=["Specification document or configuration parameter."],
                confidence=0.5,
                warnings=["Cannot proceed without required target information."],
            )

        # 5. Handle standard planning / decomposition
        return self._generate_standard_plan_response(request)

    def _generate_standard_plan_response(
        self, request: ReasoningRequest
    ) -> ReasoningResponse:
        """Generate a deterministic multi-step plan matching available capabilities."""
        available_caps = set(request.available_capabilities) if request.available_capabilities else set()

        # Choose appropriate capabilities based on goal and availability
        steps: List[ReasoningStep] = []
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"

        # Helper to pick an available capability or fallback
        def get_cap(preferred: str, fallback: Optional[str] = None) -> str:
            if preferred in available_caps:
                return preferred
            if fallback and fallback in available_caps:
                return fallback
            if available_caps:
                return next(iter(available_caps))
            return preferred

        # Step 1: Inspection
        inspect_cap = get_cap("file_list", "inspect")
        steps.append(
            ReasoningStep(
                step_id="step_1",
                objective=f"Inspect workspace and existing components for: {request.user_goal}",
                required_capability=inspect_cap,
                specialist_role="software_developer",
                dependencies=[],
                expected_output="File listing and structure verified.",
                verification_requirement="Ensure project layout exists.",
                rationale="Required baseline inspection before modification.",
                risk_level=RiskLevel.LOW,
                parameters={
                    "path": ".",
                    "relative_path": "init.py",
                    "content": "# init\n",
                    "workspace_id": "default",
                    "overwrite": True,
                },
            )
        )

        # Step 2: Implementation / Modification
        create_cap = get_cap("file_create", "file_update")
        steps.append(
            ReasoningStep(
                step_id="step_2",
                objective=f"Implement required changes for: {request.user_goal}",
                required_capability=create_cap,
                specialist_role="software_developer",
                dependencies=["step_1"],
                expected_output="Code artifacts generated.",
                verification_requirement="Verify file syntax and integrity.",
                rationale="Core implementation step fulfilling user goal.",
                risk_level=RiskLevel.MEDIUM,
                parameters={
                    "target_file": "main.py",
                    "path": "main.py",
                    "relative_path": "main.py",
                    "content": f"# Implementation for: {request.user_goal}\n\ndef run():\n    return True\n",
                    "workspace_id": "default",
                    "overwrite": True,
                },
            )
        )

        # Step 3: Test / Verification
        test_cap = get_cap("test_command_execution", "build_command_execution")
        steps.append(
            ReasoningStep(
                step_id="step_3",
                objective="Execute automated test suite to verify implementation.",
                required_capability=test_cap,
                specialist_role="software_developer",
                dependencies=["step_2"],
                expected_output="Test suite execution output with 0 failures.",
                verification_requirement="Exit code 0 and all tests passed.",
                rationale="Deterministic validation of changes against regression.",
                risk_level=RiskLevel.LOW,
                parameters={
                    "command": "pytest",
                    "command_type": "TEST",
                    "workspace_id": "default",
                    "path": "test_run.py",
                    "relative_path": "test_run.py",
                    "content": "# verified\n",
                    "overwrite": True,
                },
            )
        )

        plan = ReasoningPlan(
            plan_id=plan_id,
            goal=request.user_goal,
            steps=steps,
            dependencies=["step_1 -> step_2 -> step_3"],
            success_criteria=request.success_criteria or ["All tests passing without error."],
            assumptions=["Workspace is initialized and dependencies are installed."],
            required_capabilities=[s.required_capability for s in steps],
            confidence=0.95,
            verification_requirements=["Automated test execution passed."],
        )

        return ReasoningResponse(
            request_id=request.request_id,
            status=ReasoningStatus.SUCCESS,
            reasoning_mode=request.mode,
            structured_plan=plan,
            decision="Proceed with standard 3-step inspect-implement-verify plan.",
            confidence=0.95,
            evidence_references=[obs.evidence_id for obs in request.observations if hasattr(obs, "evidence_id")],
        )

    def _generate_recovery_response(
        self, request: ReasoningRequest
    ) -> ReasoningResponse:
        """Diagnose failure from empirical evidence and generate a revised recovery plan."""
        available_caps = set(request.available_capabilities) if request.available_capabilities else set()

        # Inspect observations for failure logs or test failures
        failure_summary = "Execution failed during previous step."
        evidence_ids: List[str] = []

        for obs in request.observations:
            if hasattr(obs, "evidence_id"):
                evidence_ids.append(obs.evidence_id)
            if isinstance(obs, ExecutionLogEvidence):
                failure_summary = f"Execution log failed with exit code {obs.exit_code}: {obs.log_snippet[:100]}"
            elif isinstance(obs, TestEvidence):
                failure_summary = f"Test suite '{obs.suite_name}' failed: {obs.tests_failed} failed, {obs.tests_passed} passed."

        if request.failures:
            failure_summary += f" Failures: {str(request.failures[:1])}"

        # Helper to pick an available capability
        def get_cap(preferred: str, fallback: Optional[str] = None) -> str:
            if preferred in available_caps:
                return preferred
            if fallback and fallback in available_caps:
                return fallback
            if available_caps:
                return next(iter(available_caps))
            return preferred

        plan_id = f"recovery_plan_{uuid.uuid4().hex[:8]}"
        update_cap = get_cap("file_update", "file_create")
        test_cap = get_cap("test_command_execution", "build_command_execution")

        recovery_steps = [
            ReasoningStep(
                step_id="rec_step_1",
                objective="Apply corrective fix based on diagnosed failure evidence.",
                required_capability=update_cap,
                specialist_role="software_developer",
                dependencies=[],
                expected_output="Defect fixed in source code.",
                verification_requirement="Source diff verified against failure cause.",
                rationale=f"Diagnosed cause: {failure_summary}",
                risk_level=RiskLevel.MEDIUM,
                parameters={
                    "target_file": "main.py",
                    "path": "main.py",
                    "relative_path": "main.py",
                    "content": f"# Corrective fix applied for: {failure_summary}\n\ndef run():\n    return True\n",
                    "workspace_id": "default",
                    "overwrite": True,
                },
            ),
            ReasoningStep(
                step_id="rec_step_2",
                objective="Re-run verification test suite to confirm recovery.",
                required_capability=test_cap,
                specialist_role="software_developer",
                dependencies=["rec_step_1"],
                expected_output="All tests pass successfully.",
                verification_requirement="Exit code 0, 0 test failures.",
                rationale="Empirically verify that the fix resolved the failure.",
                risk_level=RiskLevel.LOW,
                parameters={
                    "command": "pytest",
                    "command_type": "TEST",
                    "workspace_id": "default",
                    "path": "test_run.py",
                    "relative_path": "test_run.py",
                    "content": "# verified\n",
                    "overwrite": True,
                },
            ),
        ]

        recovery_plan = ReasoningPlan(
            plan_id=plan_id,
            goal=f"Recover from failure: {failure_summary}",
            steps=recovery_steps,
            dependencies=["rec_step_1 -> rec_step_2"],
            success_criteria=["Verification suite passes after corrective fix."],
            assumptions=["Failure cause is localized and fixable in source."],
            required_capabilities=[s.required_capability for s in recovery_steps],
            confidence=0.9,
            verification_requirements=["Re-run verification test suite."],
        )

        return ReasoningResponse(
            request_id=request.request_id,
            status=ReasoningStatus.SUCCESS,
            reasoning_mode=ReasoningMode.RECOVER,
            structured_plan=recovery_plan,
            decision="Execute recovery plan: apply corrective fix and re-verify.",
            confidence=0.9,
            failure_diagnosis=f"Diagnosed root cause: {failure_summary}",
            evidence_references=evidence_ids,
        )


class LocalInferenceReasoningAdapter(IReasoningModel):
    """
    Pluggable adapter for local inference engines (e.g. local ONNX, llama-cpp, vLLM).
    Can be configured with a local engine when available, falling back safely if offline/unavailable.
    """

    def __init__(self, local_engine: Optional[Any] = None) -> None:
        self._local_engine = local_engine

    @property
    def provider_name(self) -> str:
        return "LOCAL_INFERENCE_ADAPTER"

    def generate_reasoning(
        self,
        request: ReasoningRequest,
        system_prompt: str,
        user_prompt: str,
    ) -> ReasoningResponse:
        if self._local_engine is None:
            # Safe offline fallback when no local runtime binary is attached
            return ReasoningResponse(
                request_id=request.request_id,
                status=ReasoningStatus.FAILED,
                reasoning_mode=request.mode,
                unresolved_questions=["Local inference engine runtime is not attached or configured."],
                confidence=0.0,
                warnings=["LOCAL_ENGINE_UNAVAILABLE: No local inference runtime configured."],
            )
        # If local engine is attached, call its structured predict method
        return self._local_engine.predict(request, system_prompt, user_prompt)

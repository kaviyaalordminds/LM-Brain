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
        def get_cap(*preferred_list: str) -> str:
            for p in preferred_list:
                if p in available_caps:
                    return p
            if available_caps:
                return next(iter(available_caps))
            return preferred_list[0] if preferred_list else "file_list"

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
                    "workspace_id": "default",
                    "relative_path": "",
                    "path": "",
                },
            )
        )

        # Step 2..6 or generic step
        create_cap = get_cap("file_create", "file_update")
        goal_lower = request.user_goal.lower()
        if "landing page" in goal_lower or "website" in goal_lower or "html" in goal_lower or "responsive" in goal_lower:
            doc_lines = []
            for fact in (request.relevant_company_knowledge or []):
                doc_lines.append(f"        <li>{fact.statement}</li>")
            facts_html = "\n".join(doc_lines) if doc_lines else "        <li>Company name: NovaPulse Robotics</li>\n        <li>Mission: Autonomous warehouse robotics solutions</li>\n        <li>Core products: Fleet Orchestrator, Autonomous AMR-500, Cloud Telemetry API</li>\n        <li>Contact: contact@novapulse.io</li>"

            html_content = (
                "<!DOCTYPE html>\n"
                "<html lang=\"en\">\n"
                "<head>\n"
                "    <meta charset=\"UTF-8\">\n"
                "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
                "    <title>NovaPulse Robotics - Autonomous Warehouse Solutions</title>\n"
                "    <link rel=\"stylesheet\" href=\"styles.css\">\n"
                "</head>\n"
                "<body>\n"
                "    <header class=\"hero-section\">\n"
                "        <div class=\"container\">\n"
                "            <h1>NovaPulse Robotics</h1>\n"
                "            <p class=\"page-label\">Company Landing Page</p>\n"
                "            <p class=\"tagline\">Autonomous warehouse robotics solutions for modern enterprise logistics.</p>\n"
                "            <button id=\"cta-btn\" class=\"btn-primary\">Explore Fleet</button>\n"
                "        </div>\n"
                "    </header>\n"
                "    <main class=\"main-content container\">\n"
                "        <section class=\"products-section\">\n"
                "            <h2>Approved Company Information</h2>\n"
                "            <ul class=\"facts-list\">\n"
                f"{facts_html}\n"
                "            </ul>\n"
                "        </section>\n"
                "        <section class=\"contact-section\">\n"
                "            <h2>Contact Us</h2>\n"
                "            <p>Email: <a href=\"mailto:contact@novapulse.io\">contact@novapulse.io</a></p>\n"
                "        </section>\n"
                "    </main>\n"
                "    <script src=\"script.js\"></script>\n"
                "</body>\n"
                "</html>\n"
            )

            css_content = (
                "/* NovaPulse Robotics - Responsive Stylesheet */\n"
                ":root {\n"
                "    --primary-color: #0284c7;\n"
                "    --primary-hover: #0369a1;\n"
                "    --bg-color: #0f172a;\n"
                "    --surface-color: #1e293b;\n"
                "    --text-main: #f8fafc;\n"
                "    --text-muted: #94a3b8;\n"
                "}\n\n"
                "* {\n"
                "    box-sizing: border-box;\n"
                "    margin: 0;\n"
                "    padding: 0;\n"
                "}\n\n"
                "body {\n"
                "    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;\n"
                "    background-color: var(--bg-color);\n"
                "    color: var(--text-main);\n"
                "    line-height: 1.6;\n"
                "}\n\n"
                ".container {\n"
                "    max-width: 1200px;\n"
                "    margin: 0 auto;\n"
                "    padding: 2rem;\n"
                "}\n\n"
                ".hero-section {\n"
                "    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);\n"
                "    padding: 4rem 1rem;\n"
                "    text-align: center;\n"
                "    border-bottom: 1px solid #334155;\n"
                "}\n\n"
                ".hero-section h1 {\n"
                "    font-size: 2.75rem;\n"
                "    color: #38bdf8;\n"
                "    margin-bottom: 1rem;\n"
                "}\n\n"
                ".tagline {\n"
                "    font-size: 1.25rem;\n"
                "    color: var(--text-muted);\n"
                "    margin-bottom: 2rem;\n"
                "}\n\n"
                ".btn-primary {\n"
                "    background-color: var(--primary-color);\n"
                "    color: white;\n"
                "    padding: 0.75rem 1.75rem;\n"
                "    border: none;\n"
                "    border-radius: 6px;\n"
                "    font-size: 1rem;\n"
                "    font-weight: 600;\n"
                "    cursor: pointer;\n"
                "}\n\n"
                ".facts-list {\n"
                "    list-style: none;\n"
                "    padding: 1rem 0;\n"
                "}\n\n"
                ".facts-list li {\n"
                "    background: var(--surface-color);\n"
                "    padding: 0.75rem 1rem;\n"
                "    margin-bottom: 0.5rem;\n"
                "    border-radius: 6px;\n"
                "    border: 1px solid #334155;\n"
                "}\n\n"
                "@media (max-width: 768px) {\n"
                "    .hero-section h1 { font-size: 2rem; }\n"
                "    .container { padding: 1rem; }\n"
                "}\n"
            )

            js_content = (
                "// NovaPulse Robotics - Client Side Script\n"
                "document.addEventListener('DOMContentLoaded', () => {\n"
                "    console.log('NovaPulse Robotics landing page initialized.');\n"
                "    const btn = document.getElementById('cta-btn');\n"
                "    if (btn) {\n"
                "        btn.addEventListener('click', () => {\n"
                "            console.log('CTA clicked: Exploring fleet.');\n"
                "        });\n"
                "    }\n"
                "});\n"
            )

            readme_content = (
                "# NovaPulse Robotics - Landing Page\n\n"
                "Autonomous warehouse robotics solutions company landing page.\n\n"
                "## Files\n"
                "- `index.html`: Semantic landing page structure referencing styles and script.\n"
                "- `styles.css`: Responsive CSS stylesheets.\n"
                "- `script.js`: Interactive client-side behavior.\n"
                "- `README.md`: Documentation and file manifest.\n"
            )

            steps.append(
                ReasoningStep(
                    step_id="step_2",
                    objective="Create index.html landing page with semantic structure and approved company info",
                    required_capability=create_cap,
                    specialist_role="software_developer",
                    dependencies=["step_1"],
                    expected_output="Created index.html.",
                    verification_requirement="Verify index.html exists and links styles.css and script.js.",
                    rationale="Core HTML landing page structure.",
                    risk_level=RiskLevel.MEDIUM,
                    parameters={
                        "workspace_id": "default",
                        "relative_path": "index.html",
                        "target_file": "index.html",
                        "path": "index.html",
                        "content": html_content,
                        "overwrite": True,
                    },
                )
            )

            steps.append(
                ReasoningStep(
                    step_id="step_3",
                    objective="Create styles.css with responsive styling and layout rules",
                    required_capability=create_cap,
                    specialist_role="software_developer",
                    dependencies=["step_2"],
                    expected_output="Created styles.css.",
                    verification_requirement="Verify styles.css exists and is non-empty.",
                    rationale="Responsive presentation layer for landing page.",
                    risk_level=RiskLevel.LOW,
                    parameters={
                        "workspace_id": "default",
                        "relative_path": "styles.css",
                        "target_file": "styles.css",
                        "path": "styles.css",
                        "content": css_content,
                        "overwrite": True,
                    },
                )
            )

            steps.append(
                ReasoningStep(
                    step_id="step_4",
                    objective="Create script.js with client-side interactive logic",
                    required_capability=create_cap,
                    specialist_role="software_developer",
                    dependencies=["step_3"],
                    expected_output="Created script.js.",
                    verification_requirement="Verify script.js exists and is non-empty.",
                    rationale="Dynamic interactivity for landing page.",
                    risk_level=RiskLevel.LOW,
                    parameters={
                        "workspace_id": "default",
                        "relative_path": "script.js",
                        "target_file": "script.js",
                        "path": "script.js",
                        "content": js_content,
                        "overwrite": True,
                    },
                )
            )

            steps.append(
                ReasoningStep(
                    step_id="step_5",
                    objective="Create README.md with project overview and manifest",
                    required_capability=create_cap,
                    specialist_role="software_developer",
                    dependencies=["step_4"],
                    expected_output="Created README.md.",
                    verification_requirement="Verify README.md exists and is non-empty.",
                    rationale="Project documentation and inspection guide.",
                    risk_level=RiskLevel.LOW,
                    parameters={
                        "workspace_id": "default",
                        "relative_path": "README.md",
                        "target_file": "README.md",
                        "path": "README.md",
                        "content": readme_content,
                        "overwrite": True,
                    },
                )
            )

            val_cap = get_cap("project_validation", "software_validation", "file_read", "inspect", "file_list")
            steps.append(
                ReasoningStep(
                    step_id="step_6",
                    objective="Perform controlled multi-file project validation across index.html, styles.css, script.js, and README.md",
                    required_capability=val_cap,
                    specialist_role="software_developer",
                    dependencies=["step_5"],
                    expected_output="All required files, cross-references, and company facts verified.",
                    verification_requirement="All project coherence checks passed without error.",
                    rationale="Empirical project verification.",
                    risk_level=RiskLevel.LOW,
                    parameters={
                        "workspace_id": "default",
                        "required_files": ["index.html", "styles.css", "script.js", "README.md"],
                        "expected_keywords": ["NovaPulse Robotics"],
                        "relative_path": "index.html",
                        "path": "index.html",
                        "target_file": "index.html",
                    },
                )
            )

            dep_str = "step_1 -> step_2 -> step_3 -> step_4 -> step_5 -> step_6"
            plan_decision = "Proceed with 6-step multi-file project creation and validation plan."
        else:
            content = f"# Implementation for: {request.user_goal}\n\ndef run():\n    return True\n"
            target_file = "main.py"

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
                        "workspace_id": "default",
                        "relative_path": target_file,
                        "target_file": target_file,
                        "path": target_file,
                        "content": content,
                        "overwrite": True,
                    },
                )
            )

            test_cap = get_cap("test_command_execution", "build_command_execution", "file_read")
            test_params = {
                "command": "pytest",
                "command_type": "TEST",
                "workspace_id": "default",
                "path": "test_run.py",
                "relative_path": "test_run.py",
                "content": "# verified\n",
                "overwrite": True,
            }
            verification_req = "Exit code 0 and all tests passed."
            expected_out = "Test suite execution output with 0 failures."

            steps.append(
                ReasoningStep(
                    step_id="step_3",
                    objective="Execute verification step to validate implementation.",
                    required_capability=test_cap,
                    specialist_role="software_developer",
                    dependencies=["step_2"],
                    expected_output=expected_out,
                    verification_requirement=verification_req,
                    rationale="Deterministic validation of changes against regression.",
                    risk_level=RiskLevel.LOW,
                    parameters=test_params,
                )
            )
            dep_str = "step_1 -> step_2 -> step_3"
            plan_decision = "Proceed with standard 3-step inspect-implement-verify plan."

        plan = ReasoningPlan(
            plan_id=plan_id,
            goal=request.user_goal,
            steps=steps,
            dependencies=[dep_str],
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
            decision=plan_decision,
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
        def get_cap(*preferred_list: str) -> str:
            for p in preferred_list:
                if p in available_caps:
                    return p
            if available_caps:
                return next(iter(available_caps))
            return preferred_list[0] if preferred_list else "file_update"

        plan_id = f"recovery_plan_{uuid.uuid4().hex[:8]}"
        update_cap = get_cap("file_update", "file_create")
        goal_lower = request.user_goal.lower()

        if "landing page" in goal_lower or "website" in goal_lower or "html" in goal_lower:
            rec_target = "index.html"
            rec_content = (
                "<!DOCTYPE html>\n"
                "<html lang=\"en\">\n"
                "<head>\n"
                "    <meta charset=\"UTF-8\">\n"
                "    <title>NovaPulse Robotics - Company Landing Page</title>\n"
                "</head>\n"
                "<body>\n"
                "    <h1>NovaPulse Robotics</h1>\n"
                "    <p>Approved Company Profile & Services (Recovered)</p>\n"
                "</body>\n"
                "</html>\n"
            )
            rec_test_cap = get_cap("file_read", "inspect", "file_list")
            rec_test_params = {
                "workspace_id": "default",
                "path": rec_target,
                "relative_path": rec_target,
                "target_file": rec_target,
            }
        else:
            rec_target = "main.py"
            rec_content = f"# Corrective fix applied for: {failure_summary}\n\ndef run():\n    return True\n"
            rec_test_cap = get_cap("test_command_execution", "build_command_execution", "file_read")
            rec_test_params = {
                "command": "pytest",
                "command_type": "TEST",
                "workspace_id": "default",
                "path": "test_run.py",
                "relative_path": "test_run.py",
                "content": "# verified\n",
                "overwrite": True,
            }

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
                    "target_file": rec_target,
                    "path": rec_target,
                    "relative_path": rec_target,
                    "content": rec_content,
                    "workspace_id": "default",
                    "overwrite": True,
                },
            ),
            ReasoningStep(
                step_id="rec_step_2",
                objective="Re-run verification test suite to confirm recovery.",
                required_capability=rec_test_cap,
                specialist_role="software_developer",
                dependencies=["rec_step_1"],
                expected_output="Verification completed successfully.",
                verification_requirement="Exit code 0 or file verified.",
                rationale="Empirically verify that the fix resolved the failure.",
                risk_level=RiskLevel.LOW,
                parameters=rec_test_params,
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

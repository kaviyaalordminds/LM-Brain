"""
Comprehensive test suite for Coding / Reasoning Model Integration.
Covers interfaces, request/response validation, capability safety, security injection defense,
structured planning, dependency DAGs, failure recovery, evidence integrity,
company knowledge integration, software development integration, offline guarantees,
audit logging, and resource bounds.
"""

from datetime import datetime, timezone
import json
import pytest

from executive_twins.memory.knowledge_layer import CompanyKnowledgeService
from executive_twins.reasoning.dev_adapters import (
    DevTestReasoningAdapter,
    LocalInferenceReasoningAdapter,
)
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
    RiskLevel,
)
from executive_twins.reasoning.prompt_builder import PromptBuilder
from executive_twins.reasoning.reasoning_service import (
    PlanTranslator,
    ReasoningService,
)
from executive_twins.reasoning.validators import ReasoningValidator
from executive_twins.schemas.common import (
    FactItem,
    FactState,
    FailureState,
    SecurityContext,
)
from executive_twins.schemas.evidence import (
    ArtifactEvidence,
    EvidenceCategory,
    EvidenceSet,
    ExecutionLogEvidence,
    TestEvidence,
    VerificationEvidence,
)
from executive_twins.schemas.knowledge import (
    CompanyKnowledgeRequest,
    CompanyKnowledgeResponse,
    KnowledgeOutcomeStatus,
    ObsidianDocument,
)
from executive_twins.software_development.models import (
    DevelopmentPlan,
    DevelopmentPlanStatus,
    DevelopmentRequest,
    PlanStepAction,
    PlanStepStatus,
)
from executive_twins.software_development.software_development_agent import (
    SoftwareDevelopmentAgent,
)
from executive_twins.utils.audit_logger import AuditLogger


# =====================================================================
# Fixtures
# =====================================================================

@pytest.fixture(autouse=True)
def clean_audit_log():
    AuditLogger.clear_events()
    yield
    AuditLogger.clear_events()


@pytest.fixture
def dev_adapter():
    return DevTestReasoningAdapter()


@pytest.fixture
def validator():
    return ReasoningValidator()


@pytest.fixture
def reasoning_service(dev_adapter, validator):
    return ReasoningService(
        model_adapter=dev_adapter,
        validator=validator,
        config=ReasoningConfig(),
    )


# =====================================================================
# 1. Interface & Initialization Tests
# =====================================================================

def test_1_interface_contracts():
    assert issubclass(DevTestReasoningAdapter, IReasoningModel)
    assert issubclass(LocalInferenceReasoningAdapter, IReasoningModel)
    assert issubclass(ReasoningValidator, IReasoningValidator)
    assert issubclass(ReasoningService, IReasoningService)
    assert issubclass(PlanTranslator, IPlanTranslator)


def test_2_adapter_provider_name(dev_adapter):
    assert dev_adapter.provider_name == "DEV_TEST_REASONING_ADAPTER"
    local = LocalInferenceReasoningAdapter()
    assert local.provider_name == "LOCAL_INFERENCE_ADAPTER"


def test_3_service_initialization(reasoning_service):
    assert reasoning_service.model_adapter is not None
    assert reasoning_service.validator is not None
    assert reasoning_service.config is not None
    assert reasoning_service.plan_translator is not None


def test_4_plan_translator_initialization():
    translator = PlanTranslator()
    assert isinstance(translator, IPlanTranslator)


def test_5_config_defaults():
    cfg = ReasoningConfig()
    assert cfg.max_request_size == 100_000
    assert cfg.max_response_size == 100_000
    assert cfg.max_plan_steps == 20
    assert cfg.max_recovery_iterations == 3
    assert cfg.timeout_seconds == 60.0
    assert cfg.min_confidence == 0.5


# =====================================================================
# 2. Request Validation Tests
# =====================================================================

def test_6_valid_request(validator):
    req = ReasoningRequest(
        request_id="req_valid_01",
        user_goal="Build user authentication module",
        available_capabilities=["file_create", "test_command_execution"],
    )
    cfg = ReasoningConfig()
    valid, err = validator.validate_request(req, cfg)
    assert valid is True
    assert err is None


def test_7_missing_goal_rejected(validator):
    req = ReasoningRequest(
        request_id="req_invalid_01",
        user_goal="",
    )
    valid, err = validator.validate_request(req, ReasoningConfig())
    assert valid is False
    assert "REQUEST_INVALID" in err


def test_8_whitespace_goal_rejected(validator):
    req = ReasoningRequest(
        request_id="req_invalid_02",
        user_goal="   \n\t  ",
    )
    valid, err = validator.validate_request(req, ReasoningConfig())
    assert valid is False
    assert "REQUEST_INVALID" in err


def test_9_oversized_request_rejected(validator):
    huge_data = {"key_" + str(i): "x" * 1000 for i in range(120)}
    req = ReasoningRequest(
        request_id="req_huge_01",
        user_goal="Goal",
        context=huge_data,
    )
    cfg = ReasoningConfig(max_request_size=50_000)
    valid, err = validator.validate_request(req, cfg)
    assert valid is False
    assert "REQUEST_OVERSIZED" in err


def test_10_unauthenticated_security_context_rejected(validator):
    req = ReasoningRequest(
        request_id="req_unauth_01",
        user_goal="Goal",
        security_context=SecurityContext(is_authenticated=False),
    )
    valid, err = validator.validate_request(req, ReasoningConfig())
    assert valid is False
    assert "SECURITY_DENIED" in err


# =====================================================================
# 3. Response Validation Tests
# =====================================================================

def test_11_valid_response(validator):
    req = ReasoningRequest(
        request_id="req_01",
        user_goal="Test goal",
        available_capabilities=["file_create"],
    )
    plan = ReasoningPlan(
        plan_id="plan_01",
        goal="Test goal",
        steps=[
            ReasoningStep(
                step_id="s1",
                objective="Create file",
                required_capability="file_create",
            )
        ],
        required_capabilities=["file_create"],
    )
    resp = ReasoningResponse(
        request_id="req_01",
        status=ReasoningStatus.SUCCESS,
        reasoning_mode=ReasoningMode.PLAN,
        structured_plan=plan,
        confidence=0.9,
    )
    valid, err = validator.validate_response(resp, req, ReasoningConfig())
    assert valid is True
    assert err is None


def test_12_malformed_response_missing_plan_and_decision(validator):
    req = ReasoningRequest(request_id="req_02", user_goal="Test goal")
    resp = ReasoningResponse(
        request_id="req_02",
        status=ReasoningStatus.SUCCESS,
        reasoning_mode=ReasoningMode.PLAN,
        structured_plan=None,
        decision=None,
    )
    valid, err = validator.validate_response(resp, req, ReasoningConfig())
    assert valid is False
    assert "MALFORMED_RESPONSE" in err


def test_13_needs_info_response_missing_details(validator):
    req = ReasoningRequest(request_id="req_03", user_goal="Test goal")
    resp = ReasoningResponse(
        request_id="req_03",
        status=ReasoningStatus.NEEDS_INFORMATION,
        reasoning_mode=ReasoningMode.PLAN,
        required_information=[],
        unresolved_questions=[],
    )
    valid, err = validator.validate_response(resp, req, ReasoningConfig())
    assert valid is False
    assert "MALFORMED_RESPONSE" in err


def test_14_invalid_confidence_bounds(validator):
    req = ReasoningRequest(request_id="req_04", user_goal="Test goal")
    # Confidence > 1.0 or < 0.0 rejected by Pydantic or validator
    with pytest.raises(Exception):
        ReasoningResponse(
            request_id="req_04",
            status=ReasoningStatus.SUCCESS,
            reasoning_mode=ReasoningMode.PLAN,
            confidence=1.5,
            decision="Test",
        )


def test_15_response_oversized_rejected(validator):
    req = ReasoningRequest(request_id="req_05", user_goal="Test goal")
    resp = ReasoningResponse(
        request_id="req_05",
        status=ReasoningStatus.SUCCESS,
        reasoning_mode=ReasoningMode.PLAN,
        decision="D" * 60_000,
    )
    cfg = ReasoningConfig(max_response_size=50_000)
    valid, err = validator.validate_response(resp, req, cfg)
    assert valid is False
    assert "RESPONSE_OVERSIZED" in err


# =====================================================================
# 4. Capability Safety & Unknown Capability Rejection
# =====================================================================

def test_16_valid_registered_capabilities(reasoning_service):
    req = ReasoningRequest(
        request_id="req_cap_01",
        user_goal="Inspect and build code",
        available_capabilities=["file_list", "file_create", "test_command_execution"],
    )
    resp = reasoning_service.reason(req)
    assert resp.status == ReasoningStatus.SUCCESS
    assert resp.structured_plan is not None
    for step in resp.structured_plan.steps:
        assert step.required_capability in req.available_capabilities


def test_17_unknown_capability_rejected(reasoning_service, dev_adapter):
    req = ReasoningRequest(
        request_id="req_cap_02",
        user_goal="Execute custom action",
        available_capabilities=["file_list", "file_create"],
    )
    # Inject a plan with an unregistered capability
    bad_plan = ReasoningPlan(
        plan_id="plan_bad",
        goal="Execute custom action",
        steps=[
            ReasoningStep(
                step_id="s1",
                objective="Run arbitrary magic",
                required_capability="unregistered_magic_capability",
            )
        ],
        required_capabilities=["unregistered_magic_capability"],
    )
    dev_adapter.set_custom_response(
        "req_cap_02",
        ReasoningResponse(
            request_id="req_cap_02",
            status=ReasoningStatus.SUCCESS,
            reasoning_mode=ReasoningMode.PLAN,
            structured_plan=bad_plan,
        ),
    )
    resp = reasoning_service.reason(req)
    assert resp.status == ReasoningStatus.INVALID
    assert any("UNAVAILABLE_CAPABILITY" in w for w in resp.warnings)


def test_18_invented_specialist_capability_rejected(validator):
    req = ReasoningRequest(
        request_id="req_cap_03",
        user_goal="Make coffee",
        available_capabilities=["file_list", "file_create"],
    )
    plan = ReasoningPlan(
        plan_id="plan_invented",
        goal="Make coffee",
        steps=[
            ReasoningStep(
                step_id="s1",
                objective="Brew",
                required_capability="coffee_maker_agent",
            )
        ],
        required_capabilities=["coffee_maker_agent"],
    )
    valid, err = validator.validate_plan(plan, req, ReasoningConfig())
    assert valid is False
    assert "UNAVAILABLE_CAPABILITY" in err


def test_19_missing_capabilities_needs_info(dev_adapter, reasoning_service):
    req = ReasoningRequest(
        request_id="req_cap_04",
        user_goal="Need information to proceed missing_info",
        available_capabilities=["file_list"],
    )
    resp = reasoning_service.reason(req)
    assert resp.status == ReasoningStatus.NEEDS_INFORMATION
    assert len(resp.unresolved_questions) > 0


def test_20_unconstrained_available_capabilities(validator):
    req = ReasoningRequest(
        request_id="req_cap_05",
        user_goal="General plan",
        available_capabilities=[],  # Unconstrained
    )
    plan = ReasoningPlan(
        plan_id="p1",
        goal="General plan",
        steps=[
            ReasoningStep(
                step_id="s1",
                objective="Inspect",
                required_capability="inspect",
            )
        ],
    )
    valid, err = validator.validate_plan(plan, req, ReasoningConfig())
    assert valid is True
    assert err is None


# =====================================================================
# 5. Security & Injection Defense Tests
# =====================================================================

def test_21_security_rejection_of_powershell_in_goal(reasoning_service):
    req = ReasoningRequest(
        request_id="req_sec_01",
        user_goal="Run powershell -command Get-Process",
    )
    resp = reasoning_service.reason(req)
    assert resp.status == ReasoningStatus.INVALID
    assert any("SECURITY_VIOLATION" in w for w in resp.warnings)


def test_22_security_rejection_of_shell_exec_in_goal(reasoning_service):
    req = ReasoningRequest(
        request_id="req_sec_02",
        user_goal="Use shell_exec to list directory",
    )
    resp = reasoning_service.reason(req)
    assert resp.status == ReasoningStatus.INVALID
    assert any("SECURITY_VIOLATION" in w for w in resp.warnings)


def test_23_security_rejection_of_subprocess_in_goal(reasoning_service):
    req = ReasoningRequest(
        request_id="req_sec_03",
        user_goal="Execute subprocess.run(['ls'])",
    )
    resp = reasoning_service.reason(req)
    assert resp.status == ReasoningStatus.INVALID
    assert any("SECURITY_VIOLATION" in w for w in resp.warnings)


def test_24_security_rejection_of_powershell_in_plan_step(dev_adapter, reasoning_service):
    req = ReasoningRequest(
        request_id="req_sec_04",
        user_goal="Perform operation",
        available_capabilities=["file_create"],
    )
    injected_plan = ReasoningPlan(
        plan_id="plan_inject",
        goal="Perform operation",
        steps=[
            ReasoningStep(
                step_id="s1",
                objective="Execute powershell script to install packages",
                required_capability="file_create",
            )
        ],
    )
    dev_adapter.set_custom_response(
        "req_sec_04",
        ReasoningResponse(
            request_id="req_sec_04",
            status=ReasoningStatus.SUCCESS,
            reasoning_mode=ReasoningMode.PLAN,
            structured_plan=injected_plan,
        ),
    )
    resp = reasoning_service.reason(req)
    assert resp.status == ReasoningStatus.INVALID
    assert any("SECURITY_VIOLATION" in w for w in resp.warnings)


def test_25_security_rejection_of_cmd_in_plan_parameters(dev_adapter, reasoning_service):
    req = ReasoningRequest(
        request_id="req_sec_05",
        user_goal="Perform operation",
        available_capabilities=["file_create"],
    )
    injected_plan = ReasoningPlan(
        plan_id="plan_inject_cmd",
        goal="Perform operation",
        steps=[
            ReasoningStep(
                step_id="s1",
                objective="Create script",
                required_capability="file_create",
                parameters={"cmd": "cmd.exe /c dir"},
            )
        ],
    )
    dev_adapter.set_custom_response(
        "req_sec_05",
        ReasoningResponse(
            request_id="req_sec_05",
            status=ReasoningStatus.SUCCESS,
            reasoning_mode=ReasoningMode.PLAN,
            structured_plan=injected_plan,
        ),
    )
    resp = reasoning_service.reason(req)
    assert resp.status == ReasoningStatus.INVALID
    assert any("SECURITY_VIOLATION" in w for w in resp.warnings)


def test_26_security_audit_logs_no_credential_leakage(reasoning_service):
    req = ReasoningRequest(
        request_id="req_sec_06",
        user_goal="Configure authentication",
        metadata={"api_key": "SECRET_KEY_12345", "password": "super_secret_pwd"},
    )
    reasoning_service.reason(req)
    events = AuditLogger.get_events()
    for ev in events:
        ev_str = json.dumps(ev.payload)
        assert "SECRET_KEY_12345" not in ev_str
        assert "super_secret_pwd" not in ev_str


# =====================================================================
# 6. Structured Planning & Dependency DAG Tests
# =====================================================================

def test_27_simple_single_step_plan(validator):
    plan = ReasoningPlan(
        plan_id="p_single",
        goal="Single step",
        steps=[
            ReasoningStep(
                step_id="step_1",
                objective="Step 1",
                required_capability="file_list",
            )
        ],
    )
    req = ReasoningRequest(request_id="r1", user_goal="Single step")
    valid, err = validator.validate_plan(plan, req, ReasoningConfig())
    assert valid is True
    assert err is None


def test_28_multi_step_sequential_plan(validator):
    plan = ReasoningPlan(
        plan_id="p_multi",
        goal="Multi step",
        steps=[
            ReasoningStep(step_id="s1", objective="Step 1", required_capability="file_list"),
            ReasoningStep(step_id="s2", objective="Step 2", required_capability="file_create", dependencies=["s1"]),
            ReasoningStep(step_id="s3", objective="Step 3", required_capability="test_command_execution", dependencies=["s2"]),
        ],
    )
    req = ReasoningRequest(request_id="r2", user_goal="Multi step")
    valid, err = validator.validate_plan(plan, req, ReasoningConfig())
    assert valid is True
    assert err is None


def test_29_forward_dependency_rejected(validator):
    plan = ReasoningPlan(
        plan_id="p_fwd",
        goal="Forward dep",
        steps=[
            ReasoningStep(step_id="s1", objective="Step 1", required_capability="file_list", dependencies=["s2"]),
            ReasoningStep(step_id="s2", objective="Step 2", required_capability="file_create"),
        ],
    )
    req = ReasoningRequest(request_id="r3", user_goal="Forward dep")
    valid, err = validator.validate_plan(plan, req, ReasoningConfig())
    assert valid is False
    assert "INVALID_DEPENDENCY" in err


def test_30_circular_self_dependency_rejected(validator):
    plan = ReasoningPlan(
        plan_id="p_self",
        goal="Self dep",
        steps=[
            ReasoningStep(step_id="s1", objective="Step 1", required_capability="file_list", dependencies=["s1"]),
        ],
    )
    req = ReasoningRequest(request_id="r4", user_goal="Self dep")
    valid, err = validator.validate_plan(plan, req, ReasoningConfig())
    assert valid is False
    assert "CIRCULAR_DEPENDENCY" in err


def test_31_duplicate_step_id_rejected(validator):
    plan = ReasoningPlan(
        plan_id="p_dup",
        goal="Duplicate step ID",
        steps=[
            ReasoningStep(step_id="step_x", objective="First X", required_capability="file_list"),
            ReasoningStep(step_id="step_x", objective="Second X", required_capability="file_create"),
        ],
    )
    req = ReasoningRequest(request_id="r5", user_goal="Duplicate step ID")
    valid, err = validator.validate_plan(plan, req, ReasoningConfig())
    assert valid is False
    assert "DUPLICATE_STEP_ID" in err


def test_32_empty_step_id_rejected(validator):
    plan = ReasoningPlan(
        plan_id="p_empty_id",
        goal="Empty ID",
        steps=[
            ReasoningStep(step_id="", objective="Empty", required_capability="file_list"),
        ],
    )
    req = ReasoningRequest(request_id="r6", user_goal="Empty ID")
    valid, err = validator.validate_plan(plan, req, ReasoningConfig())
    assert valid is False
    assert "INVALID_STEP" in err


# =====================================================================
# 7. Failure Recovery & Re-planning Tests
# =====================================================================

def test_33_replan_from_failure_generates_recovery_plan(reasoning_service):
    req = ReasoningRequest(
        request_id="req_orig_01",
        user_goal="Build payment endpoint",
        available_capabilities=["file_update", "test_command_execution"],
    )
    failure_ev = EvidenceSet(
        items=[
            ExecutionLogEvidence(
                evidence_id="ev_log_fail_01",
                execution_id="exec_01",
                log_snippet="SyntaxError: invalid syntax at line 42",
                exit_code=1,
            )
        ]
    )
    resp = reasoning_service.replan_from_failure(
        request=req,
        failure_evidence=failure_ev,
        failure_reason="Unit test failed with SyntaxError",
        current_iteration=1,
    )
    assert resp.status == ReasoningStatus.SUCCESS
    assert resp.reasoning_mode == ReasoningMode.RECOVER
    assert resp.structured_plan is not None
    assert resp.failure_diagnosis is not None
    assert "SyntaxError" in resp.failure_diagnosis


def test_34_replan_diagnoses_test_evidence(reasoning_service):
    req = ReasoningRequest(
        request_id="req_orig_02",
        user_goal="Build auth endpoint",
        available_capabilities=["file_update", "test_command_execution"],
    )
    failure_ev = EvidenceSet(
        items=[
            TestEvidence(
                evidence_id="ev_test_fail_01",
                suite_name="auth_tests",
                tests_passed=5,
                tests_failed=2,
            )
        ]
    )
    resp = reasoning_service.replan_from_failure(
        request=req,
        failure_evidence=failure_ev,
        failure_reason="2 tests failed in auth_tests suite",
        current_iteration=1,
    )
    assert resp.status == ReasoningStatus.SUCCESS
    assert "auth_tests" in resp.failure_diagnosis
    assert "2 failed" in resp.failure_diagnosis


def test_35_replan_max_recovery_iterations_exhaustion(reasoning_service):
    req = ReasoningRequest(
        request_id="req_orig_03",
        user_goal="Build search index",
    )
    failure_ev = EvidenceSet(items=[])
    # Iteration 4 exceeds default max 3
    resp = reasoning_service.replan_from_failure(
        request=req,
        failure_evidence=failure_ev,
        failure_reason="Persistent crash",
        current_iteration=4,
    )
    assert resp.status == ReasoningStatus.FAILED
    assert any("RECOVERY_LIMIT_EXCEEDED" in w for w in resp.warnings)


def test_36_replan_rejection_of_invalid_recovery_plan(reasoning_service, dev_adapter):
    req = ReasoningRequest(
        request_id="req_orig_04",
        user_goal="Fix bug",
        available_capabilities=["file_update"],
    )
    # Inject an invalid recovery plan with forbidden powershell command
    bad_rec_plan = ReasoningPlan(
        plan_id="p_bad_rec",
        goal="Fix bug",
        steps=[
            ReasoningStep(
                step_id="rec_1",
                objective="Run powershell -command Fix-All",
                required_capability="file_update",
            )
        ],
    )
    dev_adapter.set_custom_response(
        "req_orig_04_rec_1",
        ReasoningResponse(
            request_id="req_orig_04_rec_1",
            status=ReasoningStatus.SUCCESS,
            reasoning_mode=ReasoningMode.RECOVER,
            structured_plan=bad_rec_plan,
        ),
    )
    failure_ev = EvidenceSet(items=[])
    resp = reasoning_service.replan_from_failure(
        request=req,
        failure_evidence=failure_ev,
        failure_reason="Bug occurred",
        current_iteration=1,
    )
    assert resp.status == ReasoningStatus.INVALID
    assert any("SECURITY_VIOLATION" in w for w in resp.warnings)


# =====================================================================
# 8. Evidence Integrity Tests
# =====================================================================

def test_37_evidence_observations_in_prompt_builder():
    req = ReasoningRequest(
        request_id="req_ev_01",
        user_goal="Verify evidence formatting",
        observations=[
            ArtifactEvidence(
                evidence_id="art_01",
                artifact_uri="/workspace/output.txt",
                description="Output artifact created",
            ),
            TestEvidence(
                evidence_id="test_01",
                suite_name="regression",
                tests_passed=10,
                tests_failed=0,
                description="Regression suite passed",
            ),
        ],
    )
    _, user_prompt = PromptBuilder.build_prompt_pair(req)
    assert "art_01" in user_prompt
    assert "test_01" in user_prompt
    assert "EMPIRICAL OBSERVATIONS & EVIDENCE" in user_prompt


def test_38_evidence_references_propagated(dev_adapter, reasoning_service):
    req = ReasoningRequest(
        request_id="req_ev_02",
        user_goal="Build component",
        available_capabilities=["file_create"],
        observations=[
            ArtifactEvidence(
                evidence_id="art_ref_01",
                artifact_uri="/workspace/spec.json",
                description="Specification doc",
            )
        ],
    )
    resp = reasoning_service.reason(req)
    assert resp.status == ReasoningStatus.SUCCESS
    assert "art_ref_01" in resp.evidence_references


def test_39_fact_state_integrity_in_prompt():
    req = ReasoningRequest(
        request_id="req_ev_03",
        user_goal="Check facts",
        relevant_company_knowledge=[
            FactItem(statement="Database port is 5432", state=FactState.FACT, source="obsidian"),
            FactItem(statement="Server might be in US-East", state=FactState.ASSUMPTION, source="user"),
            FactItem(statement="API rate limit is unknown", state=FactState.UNKNOWN, source="docs"),
        ],
    )
    _, user_prompt = PromptBuilder.build_prompt_pair(req)
    assert "[FACT] Database port is 5432" in user_prompt
    assert "[ASSUMPTION] Server might be in US-East" in user_prompt
    assert "[UNKNOWN] API rate limit is unknown" in user_prompt


def test_40_no_false_success_promotion():
    # PromptBuilder strictly informs the model of system rules
    sys_prompt = PromptBuilder.build_system_prompt(
        ReasoningRequest(request_id="r", user_goal="g")
    )
    assert "strictly distinguish between VERIFIED facts, ASSUMPTIONS, and UNKNOWN states" in sys_prompt


def test_41_company_knowledge_retrieval():
    from executive_twins.memory.dev_adapters import (
        DevTestClaudeClient,
        DevTestMemoryKnowledgeAgent,
        DevTestObsidianAdapter,
    )
    obsidian_adapter = DevTestObsidianAdapter()
    claude_client = DevTestClaudeClient()
    memory_agent = DevTestMemoryKnowledgeAgent(claude_client=claude_client)

    seeded_doc = ObsidianDocument(
        document_id="doc_jwt_01",
        vault_path="company_knowledge/default/backend_guidelines.md",
        title="Backend Guidelines",
        content="All API endpoints must use JWT auth and respond in JSON.",
        facts=[
            FactItem(
                statement="All API endpoints must use JWT auth and respond in JSON",
                state=FactState.FACT,
                source="obsidian_vault",
            )
        ],
        confidence=0.95,
    )
    obsidian_adapter.seed_document(seeded_doc)

    knowledge_service = CompanyKnowledgeService(
        obsidian_adapter=obsidian_adapter,
        memory_agent=memory_agent,
    )
    service = ReasoningService(
        model_adapter=DevTestReasoningAdapter(),
        knowledge_layer=knowledge_service,
    )
    facts = service.fetch_company_knowledge(query="JWT auth")
    assert len(facts) > 0
    assert any("JWT" in f.statement for f in facts)


def test_42_company_knowledge_included_in_reasoning_flow(reasoning_service):
    req = ReasoningRequest(
        request_id="req_k_01",
        user_goal="Implement user login",
        relevant_company_knowledge=[
            FactItem(statement="Auth tokens expire in 3600 seconds", state=FactState.FACT, source="obsidian")
        ],
        available_capabilities=["file_create"],
    )
    _, user_prompt = PromptBuilder.build_prompt_pair(req)
    assert "Auth tokens expire in 3600 seconds" in user_prompt
    resp = reasoning_service.reason(req)
    assert resp.status == ReasoningStatus.SUCCESS


def test_43_missing_company_knowledge_handled_cleanly():
    service = ReasoningService(
        model_adapter=DevTestReasoningAdapter(),
        knowledge_layer=None,  # No knowledge layer attached
    )
    facts = service.fetch_company_knowledge(query="Unknown topic")
    assert facts == []


# =====================================================================
# 10. Software Development Agent Integration Tests
# =====================================================================

def test_44_translate_reasoning_plan_to_development_plan():
    translator = PlanTranslator()
    reasoning_plan = ReasoningPlan(
        plan_id="plan_dev_01",
        goal="Create login page",
        steps=[
            ReasoningStep(
                step_id="step_1",
                objective="List existing frontend templates",
                required_capability="file_list",
                parameters={"path": "templates/"},
            ),
            ReasoningStep(
                step_id="step_2",
                objective="Create login template",
                required_capability="file_create",
                parameters={"file_path": "templates/login.html", "content": "<form></form>"},
            ),
            ReasoningStep(
                step_id="step_3",
                objective="Run unit tests",
                required_capability="test_command_execution",
                parameters={"test_suite": "frontend_tests"},
            ),
        ],
    )
    dev_plan = translator.translate_to_development_plan(reasoning_plan, request_id="dev_req_01")
    assert isinstance(dev_plan, DevelopmentPlan)
    assert dev_plan.plan_id == "plan_dev_01"
    assert dev_plan.request_id == "dev_req_01"
    assert len(dev_plan.steps) == 3
    assert dev_plan.steps[0].action == PlanStepAction.LIST_FILES
    assert dev_plan.steps[1].action == PlanStepAction.CREATE_FILE
    assert dev_plan.steps[2].action == PlanStepAction.RUN_TEST
    assert dev_plan.status == DevelopmentPlanStatus.DRAFT


def test_45_translator_does_not_execute_commands():
    translator = PlanTranslator()
    plan = ReasoningPlan(
        plan_id="plan_no_exec",
        goal="Build feature",
        steps=[
            ReasoningStep(
                step_id="s1",
                objective="Create file",
                required_capability="file_create",
                parameters={"file_path": "test.txt", "content": "hello"},
            )
        ],
    )
    dev_plan = translator.translate_to_development_plan(plan, "req_01")
    # Translating must not execute any actions - steps remain PENDING
    assert dev_plan.steps[0].status == PlanStepStatus.PENDING
    assert dev_plan.steps[0].result_output is None


def test_46_end_to_end_reasoning_to_development_plan_translation(reasoning_service):
    req = ReasoningRequest(
        request_id="dev_req_e2e_01",
        user_goal="Build user profile page",
        available_capabilities=["file_list", "file_create", "test_command_execution"],
    )
    resp = reasoning_service.reason(req)
    assert resp.status == ReasoningStatus.SUCCESS
    assert resp.structured_plan is not None

    # Translate to Software Development Agent plan
    dev_plan = reasoning_service.plan_translator.translate_to_development_plan(
        resp.structured_plan, request_id=req.request_id
    )
    assert len(dev_plan.steps) == len(resp.structured_plan.steps)
    assert dev_plan.status == DevelopmentPlanStatus.DRAFT


# =====================================================================
# 11. Offline & No-API Guarantees Tests
# =====================================================================

def test_47_offline_execution_no_network_calls(reasoning_service):
    # DevTestReasoningAdapter is completely offline and deterministic
    req = ReasoningRequest(
        request_id="req_offline_01",
        user_goal="Inspect and update code",
        available_capabilities=["file_list", "file_create", "test_command_execution"],
    )
    resp = reasoning_service.reason(req)
    assert resp.status == ReasoningStatus.SUCCESS
    assert resp.confidence == 0.95


def test_48_deterministic_dev_adapter_repeatability(dev_adapter, reasoning_service):
    req = ReasoningRequest(
        request_id="req_repeat_01",
        user_goal="Repeatable test goal",
        available_capabilities=["file_list", "file_create"],
    )
    resp1 = reasoning_service.reason(req)
    resp2 = reasoning_service.reason(req)
    assert resp1.status == resp2.status
    assert len(resp1.structured_plan.steps) == len(resp2.structured_plan.steps)
    assert dev_adapter.invocation_count == 2


def test_49_local_adapter_safe_fallback():
    local_adapter = LocalInferenceReasoningAdapter(local_engine=None)
    service = ReasoningService(model_adapter=local_adapter)
    req = ReasoningRequest(
        request_id="req_local_01",
        user_goal="Run with local engine",
    )
    resp = service.reason(req)
    assert resp.status == ReasoningStatus.FAILED
    assert any("LOCAL_ENGINE_UNAVAILABLE" in w for w in resp.warnings)


# =====================================================================
# 12. Audit Logging Lifecycle Tests
# =====================================================================

def test_50_audit_logging_reasoning_request(reasoning_service):
    req = ReasoningRequest(
        request_id="req_audit_01",
        user_goal="Build feature A",
        available_capabilities=["file_list", "file_create"],
    )
    reasoning_service.reason(req)
    events = AuditLogger.get_events()
    event_types = [e.event_type for e in events]
    assert "REASONING_REQUEST" in event_types
    assert "PLAN_VALIDATED" in event_types
    assert "REASONING_RESPONSE" in event_types


def test_51_audit_logging_plan_rejected(reasoning_service, dev_adapter):
    req = ReasoningRequest(
        request_id="req_audit_02",
        user_goal="Build feature B",
        available_capabilities=["file_list"],
    )
    # Inject plan with unavailable capability
    dev_adapter.set_custom_response(
        "req_audit_02",
        ReasoningResponse(
            request_id="req_audit_02",
            status=ReasoningStatus.SUCCESS,
            reasoning_mode=ReasoningMode.PLAN,
            structured_plan=ReasoningPlan(
                plan_id="p_bad",
                goal="Build feature B",
                steps=[ReasoningStep(step_id="s1", objective="o", required_capability="unregistered_cap")],
            ),
        ),
    )
    reasoning_service.reason(req)
    events = AuditLogger.get_events()
    event_types = [e.event_type for e in events]
    assert "PLAN_REJECTED" in event_types
    assert "REASONING_FAILURE" in event_types


def test_52_audit_logging_recovery_lifecycle(reasoning_service):
    req = ReasoningRequest(
        request_id="req_audit_03",
        user_goal="Build feature C",
        available_capabilities=["file_update", "test_command_execution"],
    )
    failure_ev = EvidenceSet(items=[])
    reasoning_service.replan_from_failure(
        request=req,
        failure_evidence=failure_ev,
        failure_reason="Test suite failure",
        current_iteration=1,
    )
    events = AuditLogger.get_events()
    event_types = [e.event_type for e in events]
    assert "RECOVERY_REQUEST" in event_types
    assert "REPLAN_GENERATED" in event_types


# =====================================================================
# 13. Bounds & Limits Tests
# =====================================================================

def test_53_max_plan_steps_enforced(validator):
    # Plan with 25 steps exceeds default max 20
    steps = [
        ReasoningStep(step_id=f"step_{i}", objective=f"Objective {i}", required_capability="file_list")
        for i in range(25)
    ]
    plan = ReasoningPlan(plan_id="p_big", goal="Big plan", steps=steps)
    req = ReasoningRequest(request_id="r_big", user_goal="Big plan")
    valid, err = validator.validate_plan(plan, req, ReasoningConfig(max_plan_steps=20))
    assert valid is False
    assert "PLAN_TOO_LARGE" in err


def test_54_max_recovery_iterations_bound(reasoning_service):
    req = ReasoningRequest(request_id="r_rec_bound", user_goal="Fix bug")
    resp = reasoning_service.replan_from_failure(
        request=req,
        failure_evidence=EvidenceSet(),
        failure_reason="Crash",
        current_iteration=5,  # Exceeds max 3
    )
    assert resp.status == ReasoningStatus.FAILED
    assert "RECOVERY_LIMIT_EXCEEDED" in resp.warnings[0]


def test_55_custom_config_override():
    cfg = ReasoningConfig(
        max_request_size=5_000,
        max_response_size=5_000,
        max_plan_steps=5,
        max_recovery_iterations=2,
    )
    assert cfg.max_plan_steps == 5
    assert cfg.max_recovery_iterations == 2


def test_56_reasoning_modes_coverage(dev_adapter, reasoning_service):
    for mode in [
        ReasoningMode.PLAN,
        ReasoningMode.DECOMPOSE,
        ReasoningMode.DECIDE,
        ReasoningMode.DEVELOP,
        ReasoningMode.ANALYZE,
    ]:
        req = ReasoningRequest(
            request_id=f"req_mode_{mode.value}",
            user_goal=f"Test goal for {mode.value}",
            mode=mode,
            available_capabilities=["file_list", "file_create"],
        )
        resp = reasoning_service.reason(req)
        assert resp.status == ReasoningStatus.SUCCESS
        assert resp.reasoning_mode == mode


def test_57_prompt_builder_separates_all_sections():
    req = ReasoningRequest(
        request_id="req_pb_01",
        user_goal="Complex goal",
        success_criteria=["Criterion 1", "Criterion 2"],
        available_capabilities=["cap_a", "cap_b"],
        relevant_company_knowledge=[
            FactItem(statement="Fact 1", state=FactState.FACT, source="obsidian")
        ],
        current_state={"state_key": "state_val"},
        previous_actions=[{"action": "prev_1"}],
        observations=[
            VerificationEvidence(
                evidence_id="ver_01",
                verifier_id="qa_guard",
                verified_status="PASSED",
                description="QA passed",
            )
        ],
        failures=[{"failure_id": "f1", "error": "timeout"}],
    )
    sys_prompt, user_prompt = PromptBuilder.build_prompt_pair(req)
    assert "SYSTEM RULES AND SAFETY CONSTRAINTS" in sys_prompt
    assert "### USER GOAL" in user_prompt
    assert "### SUCCESS CRITERIA" in user_prompt
    assert "### AVAILABLE CAPABILITIES" in user_prompt
    assert "### VALIDATED COMPANY KNOWLEDGE" in user_prompt
    assert "### CURRENT STATE & CONTEXT" in user_prompt
    assert "### PREVIOUS ACTIONS" in user_prompt
    assert "### EMPIRICAL OBSERVATIONS & EVIDENCE" in user_prompt
    assert "### RECORDED FAILURES" in user_prompt
    assert "### REQUIRED OUTPUT FORMAT" in user_prompt


def test_58_dev_adapter_custom_generator():
    adapter = DevTestReasoningAdapter()
    def custom_gen(req, sys_p, usr_p):
        return ReasoningResponse(
            request_id=req.request_id,
            status=ReasoningStatus.SUCCESS,
            reasoning_mode=req.mode,
            decision="Custom dynamic decision generated.",
            confidence=0.88,
        )
    adapter.set_response_generator(custom_gen)
    service = ReasoningService(model_adapter=adapter)
    req = ReasoningRequest(request_id="req_gen_01", user_goal="Dynamic test")
    resp = service.reason(req)
    assert resp.status == ReasoningStatus.SUCCESS
    assert resp.decision == "Custom dynamic decision generated."
    assert resp.confidence == 0.88

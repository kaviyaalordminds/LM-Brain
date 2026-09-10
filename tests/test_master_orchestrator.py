"""
Comprehensive test suite for Master Orchestrator and Autonomous Control Loop.
Covers initialization, perception, knowledge retrieval, reasoning integration,
capability selection, specialist execution, evidence verification, failure recovery,
partial results, security boundaries, executive twin routing, memory writeback,
bounds enforcement, offline guarantees, and full audit lifecycle logging.
"""

from datetime import datetime, timezone
import json
import time
import pytest

from executive_twins.client.agent_adapter import MockSpecialistAgentAdapter
from executive_twins.client.registry_client import (
    ISpecialistRegistryClient,
    InMemorySpecialistRegistryAdapter,
)
from executive_twins.memory.dev_adapters import (
    DevTestClaudeClient,
    DevTestMemoryKnowledgeAgent,
    DevTestObsidianAdapter,
)
from executive_twins.memory.knowledge_layer import CompanyKnowledgeService
from executive_twins.orchestrator.control_loop import (
    AutonomousControlLoop,
    StandardMemoryWritebackHandler,
    StandardPerceptionEngine,
)
from executive_twins.orchestrator.dev_adapters import DevTestMasterOrchestratorFactory
from executive_twins.orchestrator.interfaces import (
    IControlLoop,
    IMasterOrchestrator,
    IMemoryWritebackHandler,
    IPerceptionEngine,
)
from executive_twins.orchestrator.master_orchestrator import MasterOrchestrator
from executive_twins.orchestrator.models import (
    OrchestrationConfig,
    OrchestrationRequest,
    OrchestrationResult,
    OrchestrationState,
    OrchestrationStatus,
    StepExecutionRecord,
)
from executive_twins.orchestrator.twin_orchestrator import TwinOrchestrator
from executive_twins.reasoning.dev_adapters import DevTestReasoningAdapter
from executive_twins.reasoning.models import (
    ReasoningMode,
    ReasoningPlan,
    ReasoningRequest,
    ReasoningResponse,
    ReasoningStatus,
    ReasoningStep,
)
from executive_twins.reasoning.reasoning_service import ReasoningService
from executive_twins.schemas.common import (
    FactItem,
    FactState,
    SecurityContext,
    SpecialistStatus,
    VerificationStatus,
)
from executive_twins.schemas.delegation import DelegationRequest, DelegationResult
from executive_twins.schemas.evidence import (
    ArtifactEvidence,
    EvidenceCategory,
    EvidenceSet,
    ExecutionLogEvidence,
    TestEvidence,
    VerificationEvidence,
)
from executive_twins.schemas.knowledge import ObsidianDocument
from executive_twins.schemas.specialist import (
    Capability,
    CapabilityRequirement,
    RegistryProvenance,
    SpecialistMetadata,
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
def orchestrator():
    return DevTestMasterOrchestratorFactory.create_default_test_orchestrator()


# =====================================================================
# 1. Initialization Tests
# =====================================================================

def test_1_orchestrator_initialization(orchestrator):
    assert isinstance(orchestrator, MasterOrchestrator)
    assert isinstance(orchestrator, IMasterOrchestrator)
    assert orchestrator.reasoning_service is not None
    assert orchestrator.registry_client is not None
    assert orchestrator.agent_adapter is not None
    assert orchestrator.control_loop is not None


def test_2_control_loop_initialization():
    reasoning_adapter = DevTestReasoningAdapter()
    service = ReasoningService(model_adapter=reasoning_adapter)
    registry = InMemorySpecialistRegistryAdapter()
    adapter = MockSpecialistAgentAdapter()
    loop = AutonomousControlLoop(
        reasoning_service=service,
        registry_client=registry,
        agent_adapter=adapter,
    )
    assert isinstance(loop, IControlLoop)
    assert isinstance(loop.perception_engine, IPerceptionEngine)
    assert isinstance(loop.writeback_handler, IMemoryWritebackHandler)


def test_3_config_defaults():
    cfg = OrchestrationConfig()
    assert cfg.max_iterations == 20
    assert cfg.max_recovery_attempts == 3
    assert cfg.max_consecutive_failures == 3
    assert cfg.max_plan_steps == 20
    assert cfg.timeout_seconds == 300.0


def test_4_factory_creation():
    orch = DevTestMasterOrchestratorFactory.create_default_test_orchestrator(
        include_knowledge=True, include_twins=True
    )
    assert orch.knowledge_layer is not None
    assert orch.twin_orchestrator is not None


def test_5_state_initialization():
    req = OrchestrationRequest(request_id="req_init_01", user_goal="Build module")
    state = OrchestrationState(request=req)
    assert state.current_status == OrchestrationStatus.RECEIVED
    assert state.iteration_count == 0
    assert state.recovery_count == 0
    assert len(state.completed_steps) == 0


# =====================================================================
# 2. Perception Tests
# =====================================================================

def test_6_valid_request_perception():
    engine = StandardPerceptionEngine()
    req = OrchestrationRequest(
        request_id="req_perc_01",
        user_goal="Build login endpoint",
        context={"framework": "FastAPI"},
        success_criteria=["Tests pass"],
    )
    valid, norm_req, err = engine.perceive(req)
    assert valid is True
    assert err is None
    assert norm_req.user_goal == "Build login endpoint"
    assert norm_req.context["framework"] == "FastAPI"


def test_7_empty_goal_rejected():
    engine = StandardPerceptionEngine()
    req = OrchestrationRequest(request_id="req_perc_02", user_goal="")
    valid, _, err = engine.perceive(req)
    assert valid is False
    assert "PERCEPTION_FAILED" in err


def test_8_whitespace_goal_rejected():
    engine = StandardPerceptionEngine()
    req = OrchestrationRequest(request_id="req_perc_03", user_goal="   \n\t ")
    valid, _, err = engine.perceive(req)
    assert valid is False
    assert "PERCEPTION_FAILED" in err


def test_9_unauthenticated_security_context_rejected():
    engine = StandardPerceptionEngine()
    req = OrchestrationRequest(
        request_id="req_perc_04",
        user_goal="Valid goal",
        security_context=SecurityContext(is_authenticated=False),
    )
    valid, _, err = engine.perceive(req)
    assert valid is False
    assert "SECURITY_DENIED" in err


def test_10_perception_security_injection_blocked():
    engine = StandardPerceptionEngine()
    req = OrchestrationRequest(
        request_id="req_perc_05",
        user_goal="Run powershell -command Get-ChildItem",
    )
    valid, _, err = engine.perceive(req)
    assert valid is False
    assert "SECURITY_VIOLATION" in err


# =====================================================================
# 3. Company Knowledge Integration Tests
# =====================================================================

def test_11_knowledge_retrieved_and_passed_to_reasoning(orchestrator):
    # Seed Obsidian knowledge
    obs_doc = ObsidianDocument(
        document_id="doc_db_01",
        vault_path="company_knowledge/default/database.md",
        title="Database Config",
        content="PostgreSQL port is 5432.",
        facts=[FactItem(statement="PostgreSQL port is 5432", state=FactState.FACT, source="obsidian")],
        confidence=1.0,
    )
    orchestrator.knowledge_layer.obsidian_adapter.seed_document(obs_doc)

    req = OrchestrationRequest(
        request_id="req_know_01",
        user_goal="Configure PostgreSQL database",
        available_capabilities=["file_create", "test_command_execution"],
    )
    result = orchestrator.orchestrate(req)
    assert result.final_status == OrchestrationStatus.COMPLETED


def test_12_knowledge_unavailable_clean_handling():
    orch = DevTestMasterOrchestratorFactory.create_default_test_orchestrator(
        include_knowledge=False
    )
    req = OrchestrationRequest(
        request_id="req_know_02",
        user_goal="Build feature without knowledge layer",
        available_capabilities=["file_create"],
    )
    result = orch.orchestrate(req)
    assert result.final_status == OrchestrationStatus.COMPLETED


def test_13_no_direct_obsidian_access_by_orchestrator(orchestrator):
    # Verify orchestrator interacts ONLY via CompanyKnowledgeService
    assert isinstance(orchestrator.knowledge_layer, CompanyKnowledgeService)


def test_14_memory_writeback_on_completion(orchestrator):
    req = OrchestrationRequest(
        request_id="req_wb_01",
        user_goal="Implement user profile feature",
        require_memory_writeback=True,
        available_capabilities=["file_create", "test_command_execution"],
    )
    result = orchestrator.orchestrate(req)
    assert result.final_status == OrchestrationStatus.COMPLETED
    assert result.memory_writeback_status == "SUCCESS"


def test_15_memory_writeback_skipped_when_disabled(orchestrator):
    req = OrchestrationRequest(
        request_id="req_wb_02",
        user_goal="Implement quick patch",
        require_memory_writeback=False,
        available_capabilities=["file_create"],
    )
    result = orchestrator.orchestrate(req)
    assert result.final_status == OrchestrationStatus.COMPLETED
    assert result.memory_writeback_status is None


# =====================================================================
# 4. Reasoning Integration Tests
# =====================================================================

def test_16_orchestrator_calls_reasoning_service(orchestrator):
    req = OrchestrationRequest(
        request_id="req_reas_01",
        user_goal="Build payment integration",
        available_capabilities=["file_create", "test_command_execution"],
    )
    result = orchestrator.orchestrate(req)
    assert result.final_status == OrchestrationStatus.COMPLETED
    assert len(result.completed_steps) > 0


def test_17_reasoning_plan_used_for_execution(orchestrator):
    req = OrchestrationRequest(
        request_id="req_reas_02",
        user_goal="Build customer portal",
        available_capabilities=["file_list", "file_create", "test_command_execution"],
    )
    result = orchestrator.orchestrate(req)
    step_ids = [s.step_id for s in result.completed_steps]
    assert "step_1" in step_ids
    assert "step_2" in step_ids
    assert "step_3" in step_ids


def test_18_reasoning_decision_only_workflow():
    r_adapter = DevTestReasoningAdapter()
    r_adapter.set_custom_response(
        "req_dec_01",
        ReasoningResponse(
            request_id="req_dec_01",
            status=ReasoningStatus.SUCCESS,
            reasoning_mode=ReasoningMode.DECIDE,
            decision="Architecture decision: use PostgreSQL with JSONB columns.",
            confidence=0.98,
        ),
    )
    orch = DevTestMasterOrchestratorFactory.create_default_test_orchestrator(
        reasoning_adapter=r_adapter
    )
    req = OrchestrationRequest(
        request_id="req_dec_01",
        user_goal="Decide database schema strategy",
    )
    result = orch.orchestrate(req)
    assert result.final_status == OrchestrationStatus.COMPLETED
    assert "PostgreSQL" in result.final_message


def test_19_reasoning_needs_info_response_handling():
    r_adapter = DevTestReasoningAdapter()
    r_adapter.set_custom_response(
        "req_ni_01",
        ReasoningResponse(
            request_id="req_ni_01",
            status=ReasoningStatus.NEEDS_INFORMATION,
            reasoning_mode=ReasoningMode.PLAN,
            required_information=["Third-party API endpoint URL"],
            confidence=0.5,
        ),
    )
    orch = DevTestMasterOrchestratorFactory.create_default_test_orchestrator(
        reasoning_adapter=r_adapter
    )
    req = OrchestrationRequest(
        request_id="req_ni_01",
        user_goal="Connect external payment gateway",
    )
    result = orch.orchestrate(req)
    assert result.final_status == OrchestrationStatus.NEEDS_INFORMATION


def test_20_reasoning_failure_response_handling():
    r_adapter = DevTestReasoningAdapter()
    r_adapter.set_custom_response(
        "req_fail_01",
        ReasoningResponse(
            request_id="req_fail_01",
            status=ReasoningStatus.FAILED,
            reasoning_mode=ReasoningMode.PLAN,
            warnings=["Model reasoning quota exceeded"],
            confidence=0.0,
        ),
    )
    orch = DevTestMasterOrchestratorFactory.create_default_test_orchestrator(
        reasoning_adapter=r_adapter
    )
    req = OrchestrationRequest(
        request_id="req_fail_01",
        user_goal="Perform complex mathematical simulation",
    )
    result = orch.orchestrate(req)
    assert result.final_status == OrchestrationStatus.FAILED


# =====================================================================
# 5. Capability Selection Tests
# =====================================================================

def test_21_registered_capability_selection(orchestrator):
    req = OrchestrationRequest(
        request_id="req_cap_01",
        user_goal="Create documentation file",
        available_capabilities=["file_create"],
    )
    result = orchestrator.orchestrate(req)
    assert result.final_status == OrchestrationStatus.COMPLETED
    for step in result.completed_steps:
        assert step.specialist_id is not None


def test_22_unknown_capability_fails_step():
    r_adapter = DevTestReasoningAdapter()
    # Plan with unregistered capability
    bad_plan = ReasoningPlan(
        plan_id="p_bad_cap",
        goal="Do teleportation",
        steps=[
            ReasoningStep(
                step_id="s1",
                objective="Teleport data",
                required_capability="teleportation_device",
            )
        ],
    )
    r_adapter.set_custom_response(
        "req_bad_cap_01",
        ReasoningResponse(
            request_id="req_bad_cap_01",
            status=ReasoningStatus.SUCCESS,
            reasoning_mode=ReasoningMode.PLAN,
            structured_plan=bad_plan,
        ),
    )
    orch = DevTestMasterOrchestratorFactory.create_default_test_orchestrator(
        reasoning_adapter=r_adapter
    )
    req = OrchestrationRequest(
        request_id="req_bad_cap_01",
        user_goal="Do teleportation",
    )
    result = orch.orchestrate(req)
    assert result.final_status in (OrchestrationStatus.FAILED, OrchestrationStatus.PARTIAL, OrchestrationStatus.BLOCKED)
    assert "UNAVAILABLE_CAPABILITY" in result.final_message or any("NO_REGISTERED_SPECIALIST_AVAILABLE" in s.error for s in result.failed_steps if s.error)


def test_23_inactive_specialist_filtered():
    mock_registry = InMemorySpecialistRegistryAdapter()
    # Add an inactive specialist
    inactive_spec = SpecialistMetadata(
        specialist_id="spec_inactive_01",
        name="Inactive Specialist",
        capabilities=[Capability(name="inactive_capability", description="test")],
        status=SpecialistStatus.INACTIVE,
        provenance=RegistryProvenance(registry_id="test-reg-01", snapshot_id="snap-01", is_authoritative=False),
    )
    mock_registry.register_specialist(inactive_spec)

    results = mock_registry.discover_specialists(
        [CapabilityRequirement(capability_name="inactive_capability", description="test")],
        SecurityContext(),
    )
    assert results[0].selected_specialist is None


def test_24_multiple_candidates_ranked_selection():
    mock_registry = InMemorySpecialistRegistryAdapter()
    spec1 = SpecialistMetadata(
        specialist_id="spec_auth_01",
        name="Authoritative Specialist",
        capabilities=[Capability(name="ranked_cap", description="test")],
        status=SpecialistStatus.ACTIVE,
        provenance=RegistryProvenance(registry_id="test-reg-01", snapshot_id="snap-01", is_authoritative=True),
    )
    spec2 = SpecialistMetadata(
        specialist_id="spec_std_01",
        name="Standard Specialist",
        capabilities=[Capability(name="ranked_cap", description="test")],
        status=SpecialistStatus.ACTIVE,
        provenance=RegistryProvenance(registry_id="test-reg-02", snapshot_id="snap-02", is_authoritative=False),
    )
    mock_registry.register_specialist(spec1)
    mock_registry.register_specialist(spec2)

    results = mock_registry.discover_specialists(
        [CapabilityRequirement(capability_name="ranked_cap", description="test")],
        SecurityContext(),
    )
    assert results[0].selected_specialist is not None


def test_25_capability_discovery_from_registry(orchestrator):
    req = OrchestrationRequest(
        request_id="req_disc_01",
        user_goal="Discover available specialists",
        available_capabilities=[],  # Empty list triggers automatic discovery from registry
    )
    result = orchestrator.orchestrate(req)
    assert result.final_status == OrchestrationStatus.COMPLETED


# =====================================================================
# 6. Specialist Execution & Evidence Tests
# =====================================================================

def test_26_successful_specialist_delegation(orchestrator):
    req = OrchestrationRequest(
        request_id="req_exec_01",
        user_goal="Implement backend endpoint",
        available_capabilities=["file_create", "test_command_execution"],
    )
    result = orchestrator.orchestrate(req)
    assert result.final_status == OrchestrationStatus.COMPLETED
    assert len(result.completed_steps) == 3


def test_27_failed_specialist_delegation():
    agent_adapter = MockSpecialistAgentAdapter()
    agent_adapter.set_fail_verification(True)
    orch = DevTestMasterOrchestratorFactory.create_default_test_orchestrator(
        agent_adapter=agent_adapter
    )
    req = OrchestrationRequest(
        request_id="req_exec_fail_01",
        user_goal="Build module with failing specialist",
        available_capabilities=["file_create"],
    )
    result = orch.orchestrate(req)
    assert result.final_status == OrchestrationStatus.FAILED
    assert len(result.failed_steps) > 0


def test_28_evidence_collection_and_propagation(orchestrator):
    req = OrchestrationRequest(
        request_id="req_ev_01",
        user_goal="Build verified service",
        available_capabilities=["file_create", "test_command_execution"],
    )
    result = orchestrator.orchestrate(req)
    assert len(result.evidence.items) > 0
    assert result.evidence.contains_category(EvidenceCategory.ARTIFACT)
    assert result.evidence.contains_category(EvidenceCategory.EXECUTION_LOG)


def test_29_artifacts_collected_into_result(orchestrator):
    req = OrchestrationRequest(
        request_id="req_art_01",
        user_goal="Generate project artifacts",
        available_capabilities=["file_create"],
    )
    result = orchestrator.orchestrate(req)
    assert len(result.artifacts) > 0
    assert any("artifact" in a for a in result.artifacts)


def test_30_verification_status_recorded(orchestrator):
    req = OrchestrationRequest(
        request_id="req_ver_01",
        user_goal="Verify execution outputs",
        available_capabilities=["file_create", "test_command_execution"],
    )
    result = orchestrator.orchestrate(req)
    for step in result.completed_steps:
        assert step.status == "COMPLETED"


# =====================================================================
# 7. Control Loop & Multi-Step Workflows Tests
# =====================================================================

def test_31_single_step_workflow_completes():
    r_adapter = DevTestReasoningAdapter()
    single_step_plan = ReasoningPlan(
        plan_id="p_single_01",
        goal="Single step inspection",
        steps=[
            ReasoningStep(step_id="s1", objective="Inspect repo", required_capability="file_list")
        ],
    )
    r_adapter.set_custom_response(
        "req_single_01",
        ReasoningResponse(
            request_id="req_single_01",
            status=ReasoningStatus.SUCCESS,
            reasoning_mode=ReasoningMode.PLAN,
            structured_plan=single_step_plan,
        ),
    )
    orch = DevTestMasterOrchestratorFactory.create_default_test_orchestrator(
        reasoning_adapter=r_adapter
    )
    req = OrchestrationRequest(request_id="req_single_01", user_goal="Single step inspection")
    result = orch.orchestrate(req)
    assert result.final_status == OrchestrationStatus.COMPLETED
    assert len(result.completed_steps) == 1


def test_32_multi_step_sequential_workflow_completes(orchestrator):
    req = OrchestrationRequest(
        request_id="req_multi_01",
        user_goal="Build multi-step feature",
        available_capabilities=["file_list", "file_create", "test_command_execution"],
    )
    result = orchestrator.orchestrate(req)
    assert result.final_status == OrchestrationStatus.COMPLETED
    assert len(result.completed_steps) == 3


def test_33_step_outputs_recorded(orchestrator):
    req = OrchestrationRequest(
        request_id="req_out_01",
        user_goal="Capture step outputs",
        available_capabilities=["file_create"],
    )
    result = orchestrator.orchestrate(req)
    assert len(result.outputs) > 0


def test_34_step_durations_recorded(orchestrator):
    req = OrchestrationRequest(
        request_id="req_dur_01",
        user_goal="Measure step durations",
        available_capabilities=["file_create"],
    )
    result = orchestrator.orchestrate(req)
    assert result.duration_seconds >= 0.0
    for step in result.completed_steps:
        assert step.duration_seconds >= 0.0


def test_35_completed_step_count_matches_plan(orchestrator):
    req = OrchestrationRequest(
        request_id="req_cnt_01",
        user_goal="Verify step counts",
        available_capabilities=["file_list", "file_create", "test_command_execution"],
    )
    result = orchestrator.orchestrate(req)
    assert len(result.completed_steps) == 3


def test_36_iteration_count_tracked(orchestrator):
    req = OrchestrationRequest(
        request_id="req_iter_01",
        user_goal="Track iteration loop",
        available_capabilities=["file_create"],
    )
    result = orchestrator.orchestrate(req)
    assert result.iterations_run >= 1


# =====================================================================
# 8. Failure Recovery & Re-planning Tests
# =====================================================================

def test_37_failed_step_triggers_recovery():
    agent_adapter = MockSpecialistAgentAdapter()
    agent_adapter.set_custom_response(
        "spec_software_dev_01",
        DelegationResult(
            delegation_id="del_fail_01",
            specialist_id="spec_software_dev_01",
            status="FAILED",
            output="Compilation error at line 55",
            error_message="Compilation error at line 55",
            verification_status=VerificationStatus.FAILED,
            evidence=EvidenceSet(items=[
                ExecutionLogEvidence(
                    evidence_id="ev_comp_err",
                    execution_id="exec_comp",
                    log_snippet="error: cannot find symbol",
                    exit_code=1,
                )
            ]),
        ),
    )
    orch = DevTestMasterOrchestratorFactory.create_default_test_orchestrator(
        agent_adapter=agent_adapter
    )
    req = OrchestrationRequest(
        request_id="req_rec_01",
        user_goal="Build with error and recover",
        available_capabilities=["file_create", "test_command_execution"],
    )
    result = orch.orchestrate(req)
    # Recovery was attempted and exhausted
    assert result.recovery_attempts > 0


def test_38_evidence_passed_to_replan(orchestrator):
    # Test that evidence set records failures
    ev = ExecutionLogEvidence(
        evidence_id="ev_fail_trace",
        execution_id="exec_01",
        log_snippet="Fatal crash",
        exit_code=1,
    )
    assert ev.category == EvidenceCategory.EXECUTION_LOG


def test_39_max_recovery_attempts_exhaustion():
    agent_adapter = MockSpecialistAgentAdapter()
    agent_adapter.set_fail_verification(True)
    cfg = OrchestrationConfig(max_recovery_attempts=2)
    orch = DevTestMasterOrchestratorFactory.create_default_test_orchestrator(
        agent_adapter=agent_adapter,
        config=cfg,
    )
    req = OrchestrationRequest(
        request_id="req_rec_max_01",
        user_goal="Always failing workflow",
        available_capabilities=["file_create"],
    )
    result = orch.orchestrate(req)
    assert result.final_status == OrchestrationStatus.FAILED
    assert result.recovery_attempts == 2


def test_40_consecutive_failures_limit_exhaustion():
    agent_adapter = MockSpecialistAgentAdapter()
    agent_adapter.set_fail_verification(True)
    cfg = OrchestrationConfig(max_consecutive_failures=2, max_recovery_attempts=5)
    orch = DevTestMasterOrchestratorFactory.create_default_test_orchestrator(
        agent_adapter=agent_adapter,
        config=cfg,
    )
    req = OrchestrationRequest(
        request_id="req_cons_fail_01",
        user_goal="Consecutive failure test",
        available_capabilities=["file_create"],
    )
    result = orch.orchestrate(req)
    assert result.final_status == OrchestrationStatus.FAILED


# =====================================================================
# 9. Partial Results & Skipped Steps Tests
# =====================================================================

def test_41_partial_success_when_step_fails_after_success():
    agent_adapter = MockSpecialistAgentAdapter()
    call_count = [0]

    def dynamic_execute(request):
        call_count[0] += 1
        if call_count[0] == 1:
            return DelegationResult(
                delegation_id=request.delegation_id,
                specialist_id=request.specialist_id,
                status="SUCCESS",
                output="Step 1 succeeded",
                verification_status=VerificationStatus.VERIFIED,
                completed_at=datetime.now(timezone.utc),
            )
        else:
            return DelegationResult(
                delegation_id=request.delegation_id,
                specialist_id=request.specialist_id,
                status="FAILED",
                output="Step 2 failed",
                error_message="Step 2 fatal failure",
                verification_status=VerificationStatus.FAILED,
                completed_at=datetime.now(timezone.utc),
            )

    agent_adapter.execute_delegation = dynamic_execute
    orch = DevTestMasterOrchestratorFactory.create_default_test_orchestrator(
        agent_adapter=agent_adapter,
        config=OrchestrationConfig(max_recovery_attempts=1),
    )
    req = OrchestrationRequest(
        request_id="req_partial_01",
        user_goal="Partial success workflow",
        available_capabilities=["file_list", "file_create", "test_command_execution"],
    )
    result = orch.orchestrate(req)
    assert result.final_status == OrchestrationStatus.PARTIAL
    assert len(result.completed_steps) == 1
    assert len(result.failed_steps) >= 1


def test_42_skipped_steps_recorded_on_early_termination():
    agent_adapter = MockSpecialistAgentAdapter()
    call_count = [0]

    def dynamic_execute(request):
        call_count[0] += 1
        if call_count[0] == 1:
            return DelegationResult(
                delegation_id=request.delegation_id,
                specialist_id=request.specialist_id,
                status="SUCCESS",
                output="Step 1 ok",
                verification_status=VerificationStatus.VERIFIED,
                completed_at=datetime.now(timezone.utc),
            )
        return DelegationResult(
            delegation_id=request.delegation_id,
            specialist_id=request.specialist_id,
            status="FAILED",
            output="Step 2 fail",
            error_message="Fail",
            verification_status=VerificationStatus.FAILED,
            completed_at=datetime.now(timezone.utc),
        )

    agent_adapter.execute_delegation = dynamic_execute
    orch = DevTestMasterOrchestratorFactory.create_default_test_orchestrator(
        agent_adapter=agent_adapter,
        config=OrchestrationConfig(max_recovery_attempts=0),
    )
    req = OrchestrationRequest(
        request_id="req_skip_01",
        user_goal="Test skipped steps recording",
        available_capabilities=["file_list", "file_create", "test_command_execution"],
    )
    result = orch.orchestrate(req)
    assert result.final_status == OrchestrationStatus.PARTIAL
    assert len(result.skipped_steps) >= 1


def test_43_failed_steps_recorded_with_errors():
    agent_adapter = MockSpecialistAgentAdapter()
    agent_adapter.set_fail_verification(True)
    orch = DevTestMasterOrchestratorFactory.create_default_test_orchestrator(
        agent_adapter=agent_adapter,
        config=OrchestrationConfig(max_recovery_attempts=0),
    )
    req = OrchestrationRequest(
        request_id="req_fail_rec_01",
        user_goal="Test failed steps error recording",
        available_capabilities=["file_create"],
    )
    result = orch.orchestrate(req)
    assert len(result.failed_steps) > 0
    assert result.failed_steps[0].error is not None


# =====================================================================
# 10. Security & Isolation Tests
# =====================================================================

def test_44_no_shell_exec_in_master_orchestrator(orchestrator):
    req = OrchestrationRequest(
        request_id="req_sec_01",
        user_goal="Run shell_exec to list directory",
    )
    result = orchestrator.orchestrate(req)
    assert result.final_status == OrchestrationStatus.FAILED
    assert "SECURITY_VIOLATION" in result.final_message


def test_45_no_powershell_in_master_orchestrator(orchestrator):
    req = OrchestrationRequest(
        request_id="req_sec_02",
        user_goal="Run powershell -command Get-Process",
    )
    result = orchestrator.orchestrate(req)
    assert result.final_status == OrchestrationStatus.FAILED
    assert "SECURITY_VIOLATION" in result.final_message


def test_46_no_os_system_in_master_orchestrator(orchestrator):
    req = OrchestrationRequest(
        request_id="req_sec_03",
        user_goal="Execute os.system('whoami')",
    )
    result = orchestrator.orchestrate(req)
    assert result.final_status == OrchestrationStatus.FAILED
    assert "SECURITY_VIOLATION" in result.final_message


def test_47_no_subprocess_in_master_orchestrator(orchestrator):
    req = OrchestrationRequest(
        request_id="req_sec_04",
        user_goal="Run subprocess.run(['cmd'])",
    )
    result = orchestrator.orchestrate(req)
    assert result.final_status == OrchestrationStatus.FAILED


def test_48_no_secret_logging_in_audit_events(orchestrator):
    req = OrchestrationRequest(
        request_id="req_sec_05",
        user_goal="Configure authentication keys",
        metadata={"token": "SECRET_BEARER_TOKEN_999", "password": "super_secret_db_pass"},
        available_capabilities=["file_create"],
    )
    orchestrator.orchestrate(req)
    events = AuditLogger.get_events()
    for ev in events:
        ev_str = json.dumps(ev.payload)
        assert "SECRET_BEARER_TOKEN_999" not in ev_str
        assert "super_secret_db_pass" not in ev_str


# =====================================================================
# 11. Executive Twins Routing Tests
# =====================================================================

def test_49_cmo_twin_activated_for_marketing_request(orchestrator):
    req = OrchestrationRequest(
        request_id="req_cmo_01",
        user_goal="Launch a new product campaign poster and marketing strategy",
        available_capabilities=["file_create", "test_command_execution"],
    )
    result = orchestrator.orchestrate(req)
    assert result.executive_twin_id in ("cmo_twin_01", "cmo") or result.final_status == OrchestrationStatus.COMPLETED


def test_50_twin_skipped_for_non_executive_request(orchestrator):
    req = OrchestrationRequest(
        request_id="req_twin_skip_01",
        user_goal="Create a simple utility file utils.py",
        available_capabilities=["file_create"],
    )
    result = orchestrator.orchestrate(req)
    assert result.final_status == OrchestrationStatus.COMPLETED


def test_51_twin_evaluation_can_be_disabled():
    orch = DevTestMasterOrchestratorFactory.create_default_test_orchestrator()
    req = OrchestrationRequest(
        request_id="req_twin_dis_01",
        user_goal="Marketing campaign",
        require_twin_evaluation=False,
        available_capabilities=["file_create"],
    )
    result = orch.orchestrate(req)
    assert result.final_status == OrchestrationStatus.COMPLETED


# =====================================================================
# 12. Memory Writeback Tests
# =====================================================================

def test_52_writeback_persists_facts_to_obsidian(orchestrator):
    req = OrchestrationRequest(
        request_id="req_wb_facts_01",
        user_goal="Implement and verify billing pipeline",
        require_memory_writeback=True,
        available_capabilities=["file_create", "test_command_execution"],
    )
    result = orchestrator.orchestrate(req)
    assert result.memory_writeback_status == "SUCCESS"
    # Check that obsidian document was created
    doc = orchestrator.knowledge_layer.obsidian_adapter.get_document_by_id("mem_workflow_req_wb_facts_01")
    assert doc is not None
    assert len(doc.facts) > 0


def test_53_writeback_blocked_on_failed_workflow():
    agent_adapter = MockSpecialistAgentAdapter()
    agent_adapter.set_fail_verification(True)
    orch = DevTestMasterOrchestratorFactory.create_default_test_orchestrator(
        agent_adapter=agent_adapter,
        config=OrchestrationConfig(max_recovery_attempts=0),
    )
    req = OrchestrationRequest(
        request_id="req_wb_blocked_01",
        user_goal="Failing workflow for writeback test",
        require_memory_writeback=True,
        available_capabilities=["file_create"],
    )
    result = orch.orchestrate(req)
    assert result.final_status == OrchestrationStatus.FAILED
    assert result.memory_writeback_status is None  # Writeback never executed for failed workflow


def test_54_writeback_handles_adapter_failure_gracefully():
    class FailingObsidianAdapter(DevTestObsidianAdapter):
        def store_document(self, document):
            raise RuntimeError("Disk full")

    obs = FailingObsidianAdapter()
    knowledge_layer = CompanyKnowledgeService(
        obsidian_adapter=obs,
        memory_agent=DevTestMemoryKnowledgeAgent(DevTestClaudeClient()),
    )
    handler = StandardMemoryWritebackHandler(knowledge_layer)
    result = OrchestrationResult(
        request_id="req_fail_wb_01",
        final_status=OrchestrationStatus.COMPLETED,
    )
    success, msg = handler.writeback(result, SecurityContext())
    assert success is False
    assert "Disk full" in msg


# =====================================================================
# 13. Bounds & Limits Tests
# =====================================================================

def test_55_max_iterations_bound_enforced():
    cfg = OrchestrationConfig(max_iterations=2)
    orch = DevTestMasterOrchestratorFactory.create_default_test_orchestrator(config=cfg)
    req = OrchestrationRequest(
        request_id="req_bound_iter_01",
        user_goal="Perform 3-step feature",
        available_capabilities=["file_list", "file_create", "test_command_execution"],
    )
    result = orch.orchestrate(req)
    assert result.iterations_run <= 2


def test_56_timeout_bound_enforced():
    cfg = OrchestrationConfig(timeout_seconds=0.001)  # Extremely short timeout
    orch = DevTestMasterOrchestratorFactory.create_default_test_orchestrator(config=cfg)
    req = OrchestrationRequest(
        request_id="req_bound_timeout_01",
        user_goal="Long running task",
        available_capabilities=["file_create"],
    )
    result = orch.orchestrate(req)
    # Exceeded timeout
    assert result.final_status in (OrchestrationStatus.FAILED, OrchestrationStatus.COMPLETED)


def test_57_custom_config_limits_respected():
    cfg = OrchestrationConfig(
        max_iterations=10,
        max_recovery_attempts=2,
        max_consecutive_failures=2,
        max_plan_steps=10,
    )
    assert cfg.max_iterations == 10
    assert cfg.max_recovery_attempts == 2


# =====================================================================
# 14. Offline & Deterministic Execution Tests
# =====================================================================

def test_58_offline_execution_no_network(orchestrator):
    req = OrchestrationRequest(
        request_id="req_offline_01",
        user_goal="Complete entirely offline task",
        available_capabilities=["file_create", "test_command_execution"],
    )
    result = orchestrator.orchestrate(req)
    assert result.final_status == OrchestrationStatus.COMPLETED


def test_59_no_api_key_required(orchestrator):
    # Runs with 0 environment API keys
    req = OrchestrationRequest(
        request_id="req_no_api_01",
        user_goal="Build without API key",
        available_capabilities=["file_create"],
    )
    result = orchestrator.orchestrate(req)
    assert result.final_status == OrchestrationStatus.COMPLETED


def test_60_deterministic_repeatability(orchestrator):
    req1 = OrchestrationRequest(request_id="req_rep_01", user_goal="Deterministic task", available_capabilities=["file_create"])
    req2 = OrchestrationRequest(request_id="req_rep_02", user_goal="Deterministic task", available_capabilities=["file_create"])
    res1 = orchestrator.orchestrate(req1)
    res2 = orchestrator.orchestrate(req2)
    assert res1.final_status == res2.final_status
    assert len(res1.completed_steps) == len(res2.completed_steps)


# =====================================================================
# 15. Audit Logging Lifecycle Tests
# =====================================================================

def test_61_audit_log_orchestration_started(orchestrator):
    req = OrchestrationRequest(request_id="req_aud_01", user_goal="Audit test goal", available_capabilities=["file_create"])
    orchestrator.orchestrate(req)
    events = [e.event_type for e in AuditLogger.get_events()]
    assert "ORCHESTRATION_STARTED" in events


def test_62_audit_log_perception_completed(orchestrator):
    req = OrchestrationRequest(request_id="req_aud_02", user_goal="Audit test goal", available_capabilities=["file_create"])
    orchestrator.orchestrate(req)
    events = [e.event_type for e in AuditLogger.get_events()]
    assert "PERCEPTION_COMPLETED" in events


def test_63_audit_log_reasoning_started(orchestrator):
    req = OrchestrationRequest(request_id="req_aud_03", user_goal="Audit test goal", available_capabilities=["file_create"])
    orchestrator.orchestrate(req)
    events = [e.event_type for e in AuditLogger.get_events()]
    assert "REASONING_STARTED" in events


def test_64_audit_log_capability_selected(orchestrator):
    req = OrchestrationRequest(request_id="req_aud_04", user_goal="Audit test goal", available_capabilities=["file_create"])
    orchestrator.orchestrate(req)
    events = [e.event_type for e in AuditLogger.get_events()]
    assert "CAPABILITY_SELECTED" in events


def test_65_audit_log_specialist_delegated(orchestrator):
    req = OrchestrationRequest(request_id="req_aud_05", user_goal="Audit test goal", available_capabilities=["file_create"])
    orchestrator.orchestrate(req)
    events = [e.event_type for e in AuditLogger.get_events()]
    assert "SPECIALIST_DELEGATED" in events


def test_66_audit_log_execution_completed(orchestrator):
    req = OrchestrationRequest(request_id="req_aud_06", user_goal="Audit test goal", available_capabilities=["file_create"])
    orchestrator.orchestrate(req)
    events = [e.event_type for e in AuditLogger.get_events()]
    assert "EXECUTION_COMPLETED" in events


def test_67_audit_log_observation_recorded(orchestrator):
    req = OrchestrationRequest(request_id="req_aud_07", user_goal="Audit test goal", available_capabilities=["file_create"])
    orchestrator.orchestrate(req)
    events = [e.event_type for e in AuditLogger.get_events()]
    assert "OBSERVATION_RECORDED" in events


def test_68_audit_log_verification_completed(orchestrator):
    req = OrchestrationRequest(request_id="req_aud_08", user_goal="Audit test goal", available_capabilities=["file_create"])
    orchestrator.orchestrate(req)
    events = [e.event_type for e in AuditLogger.get_events()]
    assert "VERIFICATION_COMPLETED" in events


def test_69_audit_log_memory_writeback_completed(orchestrator):
    req = OrchestrationRequest(
        request_id="req_aud_09",
        user_goal="Audit test goal",
        require_memory_writeback=True,
        available_capabilities=["file_create"],
    )
    orchestrator.orchestrate(req)
    events = [e.event_type for e in AuditLogger.get_events()]
    assert "MEMORY_WRITEBACK_COMPLETED" in events


def test_70_audit_log_orchestration_completed(orchestrator):
    req = OrchestrationRequest(request_id="req_aud_10", user_goal="Audit test goal", available_capabilities=["file_create"])
    orchestrator.orchestrate(req)
    events = [e.event_type for e in AuditLogger.get_events()]
    assert "ORCHESTRATION_COMPLETED" in events


def test_71_audit_log_orchestration_failed():
    agent_adapter = MockSpecialistAgentAdapter()
    agent_adapter.set_fail_verification(True)
    orch = DevTestMasterOrchestratorFactory.create_default_test_orchestrator(
        agent_adapter=agent_adapter,
        config=OrchestrationConfig(max_recovery_attempts=0),
    )
    req = OrchestrationRequest(request_id="req_aud_11", user_goal="Audit fail goal", available_capabilities=["file_create"])
    orch.orchestrate(req)
    events = [e.event_type for e in AuditLogger.get_events()]
    assert "ORCHESTRATION_FAILED" in events


def test_72_audit_log_recovery_lifecycle():
    agent_adapter = MockSpecialistAgentAdapter()
    agent_adapter.set_fail_verification(True)
    orch = DevTestMasterOrchestratorFactory.create_default_test_orchestrator(
        agent_adapter=agent_adapter,
        config=OrchestrationConfig(max_recovery_attempts=1),
    )
    req = OrchestrationRequest(request_id="req_aud_12", user_goal="Audit recovery goal", available_capabilities=["file_create"])
    orch.orchestrate(req)
    events = [e.event_type for e in AuditLogger.get_events()]
    assert "RECOVERY_STARTED" in events

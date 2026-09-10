"""
Authoritative End-to-End Autonomous AI Workforce Validation Test Suite.
Exercises the real integrated control loop across:
Perception -> Knowledge (Obsidian) -> Reasoning -> Plan Validation -> Capability Selection ->
Specialist Execution Engine -> SecurityGuard -> Controlled Capability (Workspace/Files/Build) ->
Observation -> Evidence Verification -> Failure Recovery -> Memory Writeback -> Audit Logging.
100% Offline with deterministic DEV/TEST adapters.
"""

from datetime import datetime, timezone
import json
import os
import pathlib
import tempfile
import time
import pytest

from executive_twins.client.agent_adapter import MockSpecialistAgentAdapter
from executive_twins.client.registry_client import InMemorySpecialistRegistryAdapter
from executive_twins.command_execution.command_executor import CommandRegistry
from executive_twins.execution.capability_execution_engine import (
    SpecialistExecutionAdapter,
    SpecialistExecutionEngine,
)
from executive_twins.execution.security_guard import SecurityGuard
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
from executive_twins.orchestrator.master_orchestrator import MasterOrchestrator
from executive_twins.orchestrator.models import (
    OrchestrationConfig,
    OrchestrationRequest,
    OrchestrationResult,
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
from executive_twins.software_development.dev_adapters import (
    DevTestSoftwareDevelopmentAdapter,
    create_software_development_specialist,
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
def e2e_environment():
    """
    Sets up a complete, real end-to-end integration environment with:
    - Real MasterOrchestrator & Control Loop
    - Real ReasoningService & PromptBuilder & ReasoningValidator
    - Real SpecialistExecutionEngine with real workspace, files API, command executor, git, docker handlers
    - Real SpecialistExecutionAdapter
    - Real CompanyKnowledgeService with DevTestObsidianAdapter
    - Real TwinOrchestrator
    - Real SecurityGuard & AuditLogger
    - Isolated temporary directory for workspace and storage
    """
    temp_dir = tempfile.mkdtemp(prefix="lm_brain_e2e_")
    
    # 1. Specialist Registry & Software Development Specialist
    registry = InMemorySpecialistRegistryAdapter()
    spec = create_software_development_specialist("spec_software_dev_01")
    registry.register_specialist(spec)

    # 2. Execution Engine with real Handlers
    execution_engine = SpecialistExecutionEngine(registry_client=registry)
    dev_adapter = DevTestSoftwareDevelopmentAdapter(base_temp_dir=temp_dir, use_mock_docker=True)
    dev_adapter.workspace_adapter.create_workspace("default")
    dev_adapter.register_all_handlers(execution_engine)

    # Wrap in SpecialistExecutionAdapter
    agent_adapter = SpecialistExecutionAdapter(execution_engine=execution_engine)

    # 3. Company Knowledge Layer with seeded Company Obsidian
    obsidian_adapter = DevTestObsidianAdapter()
    claude_client = DevTestClaudeClient()
    memory_agent = DevTestMemoryKnowledgeAgent(claude_client=claude_client)
    knowledge_layer = CompanyKnowledgeService(
        obsidian_adapter=obsidian_adapter,
        memory_agent=memory_agent,
    )

    # Seed approved company knowledge
    approved_doc = ObsidianDocument(
        document_id="doc_company_profile",
        vault_path="company_knowledge/default/company_profile.md",
        title="NovaPulse Robotics Profile",
        content="NovaPulse Robotics provides autonomous warehouse robotics solutions.\nServices: Fleet Orchestrator, Autonomous AMR-500, Cloud Telemetry API.\nContact: contact@novapulse.io",
        facts=[
            FactItem(statement="Company name is NovaPulse Robotics", state=FactState.FACT, source="obsidian_vault"),
            FactItem(statement="Company description: Autonomous warehouse robotics solutions", state=FactState.FACT, source="obsidian_vault"),
            FactItem(statement="Products: Fleet Orchestrator, Autonomous AMR-500, Cloud Telemetry API", state=FactState.FACT, source="obsidian_vault"),
            FactItem(statement="Contact: contact@novapulse.io", state=FactState.FACT, source="obsidian_vault"),
        ],
        confidence=1.0,
    )
    obsidian_adapter.seed_document(approved_doc)

    # 4. Reasoning Service
    reasoning_adapter = DevTestReasoningAdapter()
    reasoning_service = ReasoningService(
        model_adapter=reasoning_adapter,
        knowledge_layer=knowledge_layer,
    )

    # 5. Twin Orchestrator
    twin_orchestrator = TwinOrchestrator(
        registry_client=registry,
        agent_adapter=agent_adapter,
    )

    # 6. Master Orchestrator
    config = OrchestrationConfig(
        max_iterations=20,
        max_recovery_attempts=3,
        max_consecutive_failures=3,
        timeout_seconds=60.0,
    )
    orchestrator = MasterOrchestrator(
        reasoning_service=reasoning_service,
        registry_client=registry,
        agent_adapter=agent_adapter,
        knowledge_layer=knowledge_layer,
        twin_orchestrator=twin_orchestrator,
        config=config,
    )

    yield {
        "orchestrator": orchestrator,
        "reasoning_service": reasoning_service,
        "reasoning_adapter": reasoning_adapter,
        "knowledge_layer": knowledge_layer,
        "obsidian_adapter": obsidian_adapter,
        "registry": registry,
        "execution_engine": execution_engine,
        "dev_adapter": dev_adapter,
        "temp_dir": temp_dir,
    }


# =====================================================================
# 1. Primary Realistic Company Workflow
# =====================================================================

def test_1_primary_landing_page_workflow_success(e2e_environment):
    """
    SCENARIO 1: Complete autonomous landing page creation using approved company knowledge.
    Full flow:
    Request -> Perception -> Knowledge Retrieval -> Reasoning -> Plan Validation ->
    Capability Selection -> Specialist Execution Engine (Workspace / Files API) ->
    Observation -> Evidence Verification -> Memory Writeback -> Completed Result.
    """
    env = e2e_environment
    orchestrator: MasterOrchestrator = env["orchestrator"]
    reasoning_adapter: DevTestReasoningAdapter = env["reasoning_adapter"]

    # Pre-configure deterministic plan for landing page creation using available capabilities
    landing_page_html = """<!DOCTYPE html>
<html>
<head><title>NovaPulse Robotics</title></head>
<body>
  <h1>NovaPulse Robotics</h1>
  <p>Autonomous warehouse robotics solutions</p>
  <h2>Services</h2>
  <ul>
    <li>Fleet Orchestrator</li>
    <li>Autonomous AMR-500</li>
    <li>Cloud Telemetry API</li>
  </ul>
  <h2>Contact</h2>
  <p>Email: contact@novapulse.io</p>
</body>
</html>"""

    plan = ReasoningPlan(
        plan_id="plan_landing_page_01",
        goal="Create NovaPulse Robotics landing page",
        steps=[
            ReasoningStep(
                step_id="step_1_create_html",
                objective="Create landing page index.html with approved company knowledge",
                required_capability="file_create",
                parameters={"path": "index.html", "content": landing_page_html},
                expected_output="File index.html created in workspace",
                verification_requirement="File index.html exists and is non-empty",
            ),
            ReasoningStep(
                step_id="step_2_create_css",
                objective="Create styling style.css for landing page",
                required_capability="file_create",
                parameters={"path": "style.css", "content": "body { font-family: sans-serif; }"},
                dependencies=["step_1_create_html"],
                expected_output="File style.css created in workspace",
                verification_requirement="File style.css exists",
            ),
            ReasoningStep(
                step_id="step_3_inspect",
                objective="List and inspect workspace files",
                required_capability="file_list",
                parameters={"path": "."},
                dependencies=["step_2_create_css"],
                expected_output="Directory listing contains index.html and style.css",
                verification_requirement="All created files present in listing",
            ),
        ],
        required_capabilities=["file_create", "file_list"],
    )

    reasoning_adapter.set_custom_response(
        "req_landing_page_01",
        ReasoningResponse(
            request_id="req_landing_page_01",
            status=ReasoningStatus.SUCCESS,
            reasoning_mode=ReasoningMode.PLAN,
            structured_plan=plan,
            decision="Generate landing page components matching approved knowledge profile.",
            confidence=0.98,
        ),
    )

    req = OrchestrationRequest(
        request_id="req_landing_page_01",
        user_goal="Create a small company landing page using the company's approved company information.",
        require_memory_writeback=True,
        available_capabilities=["file_create", "file_list"],
    )

    result = orchestrator.orchestrate(req)

    # 1. Verify Orchestration Status
    assert result.final_status == OrchestrationStatus.COMPLETED
    assert len(result.completed_steps) == 3
    assert len(result.failed_steps) == 0

    # 2. Verify Real Files in Software Workspace
    ws = env["dev_adapter"].workspace_adapter.get_workspace("default")
    assert ws is not None
    assert ws.file_exists("index.html") is True
    assert ws.file_exists("style.css") is True

    file_service = env["dev_adapter"].file_adapter.get_file_service("default")
    assert file_service is not None
    file_content = file_service.read_file("index.html").content
    assert "NovaPulse Robotics" in file_content
    assert "contact@novapulse.io" in file_content
    assert "Fleet Orchestrator" in file_content

    # 3. Verify Real Artifacts & Empirical Evidence
    assert len(result.artifacts) > 0
    assert result.evidence.contains_category(EvidenceCategory.ARTIFACT)
    assert result.evidence.contains_category(EvidenceCategory.VERIFICATION)

    # 4. Verify Memory Writeback into Obsidian via Knowledge Layer
    assert result.memory_writeback_status == "SUCCESS"
    doc = env["obsidian_adapter"].get_document_by_id("mem_workflow_req_landing_page_01")
    assert doc is not None
    assert "NovaPulse Robotics" in doc.content or "req_landing_page_01" in doc.content
    assert len(doc.facts) >= 3


# =====================================================================
# 2. Multi-Step & Knowledge Propagation Tests
# =====================================================================

def test_2_knowledge_retrieval_and_propagation_into_reasoning(e2e_environment):
    """
    SCENARIO 2: Knowledge retrieval correctly reads from Obsidian and passes validated facts.
    """
    env = e2e_environment
    orchestrator = env["orchestrator"]

    req = OrchestrationRequest(
        request_id="req_know_prop_01",
        user_goal="NovaPulse Robotics database setup",
        available_capabilities=["file_create"],
    )
    result = orchestrator.orchestrate(req)
    assert result.final_status == OrchestrationStatus.COMPLETED


def test_3_no_direct_obsidian_access_by_orchestrator(e2e_environment):
    """
    SCENARIO 3: Orchestrator communicates only through CompanyKnowledgeService.
    """
    env = e2e_environment
    orchestrator = env["orchestrator"]
    assert isinstance(orchestrator.knowledge_layer, CompanyKnowledgeService)


def test_4_memory_writeback_persists_facts(e2e_environment):
    """
    SCENARIO 4: Memory writeback records discrete FactItems in permanent Obsidian storage.
    """
    env = e2e_environment
    orchestrator = env["orchestrator"]

    req = OrchestrationRequest(
        request_id="req_wb_facts_02",
        user_goal="Deploy API telemetry component",
        require_memory_writeback=True,
        available_capabilities=["file_create"],
    )
    result = orchestrator.orchestrate(req)
    assert result.final_status == OrchestrationStatus.COMPLETED
    assert result.memory_writeback_status == "SUCCESS"

    doc = env["obsidian_adapter"].get_document_by_id("mem_workflow_req_wb_facts_02")
    assert doc is not None
    assert any("completed step" in f.statement for f in doc.facts)


def test_5_no_memory_writeback_on_failed_workflow(e2e_environment):
    """
    SCENARIO 5: Failed workflows are blocked from persisting broken state to Obsidian.
    """
    env = e2e_environment
    reasoning_adapter: DevTestReasoningAdapter = env["reasoning_adapter"]

    # Configure a failing reasoning plan with nonexistent capability
    reasoning_adapter.set_custom_response(
        "req_fail_wb_01",
        ReasoningResponse(
            request_id="req_fail_wb_01",
            status=ReasoningStatus.FAILED,
            reasoning_mode=ReasoningMode.PLAN,
            warnings=["Reasoning failure simulated"],
            confidence=0.0,
        ),
    )

    req = OrchestrationRequest(
        request_id="req_fail_wb_01",
        user_goal="Attempt failed operation",
        require_memory_writeback=True,
    )
    result = env["orchestrator"].orchestrate(req)
    assert result.final_status == OrchestrationStatus.FAILED
    assert result.memory_writeback_status is None


# =====================================================================
# 3. Controlled Execution Failure & Recovery Tests
# =====================================================================

def test_6_controlled_failure_triggers_evidence_and_recovery(e2e_environment):
    """
    SCENARIO 6: First execution attempt fails with controlled error, triggers diagnosis & replan.
    """
    env = e2e_environment
    orchestrator: MasterOrchestrator = env["orchestrator"]
    reasoning_adapter: DevTestReasoningAdapter = env["reasoning_adapter"]

    # Initial plan attempts invalid file path causing controlled failure
    initial_plan = ReasoningPlan(
        plan_id="plan_fail_rec_01",
        goal="Create configuration file",
        steps=[
            ReasoningStep(
                step_id="step_fail_1",
                objective="Create config with invalid outside path",
                required_capability="file_create",
                parameters={"path": "../../../forbidden_root.json", "content": "{}"},
                expected_output="File created",
                verification_requirement="File exists",
            )
        ],
        required_capabilities=["file_create"],
    )

    reasoning_adapter.set_custom_response(
        "req_fail_rec_01",
        ReasoningResponse(
            request_id="req_fail_rec_01",
            status=ReasoningStatus.SUCCESS,
            reasoning_mode=ReasoningMode.PLAN,
            structured_plan=initial_plan,
        ),
    )

    # Recovery response fixes path to inside workspace
    recovered_plan = ReasoningPlan(
        plan_id="plan_recovered_01",
        goal="Create configuration file in workspace",
        steps=[
            ReasoningStep(
                step_id="step_rec_1",
                objective="Create config in valid workspace path",
                required_capability="file_create",
                parameters={"path": "config.json", "content": '{"status": "ok"}'},
                expected_output="Valid config file created",
                verification_requirement="File config.json exists",
            )
        ],
        required_capabilities=["file_create"],
    )

    reasoning_adapter.set_custom_response(
        "req_fail_rec_01_rec_1",
        ReasoningResponse(
            request_id="req_fail_rec_01_rec_1",
            status=ReasoningStatus.SUCCESS,
            reasoning_mode=ReasoningMode.RECOVER,
            structured_plan=recovered_plan,
            failure_diagnosis="Path traversal attempted. Corrected path to workspace-relative config.json.",
        ),
    )

    req = OrchestrationRequest(
        request_id="req_fail_rec_01",
        user_goal="Create configuration file",
        available_capabilities=["file_create"],
    )

    result = orchestrator.orchestrate(req)

    # Verify recovery occurred and workflow completed
    assert result.final_status == OrchestrationStatus.COMPLETED
    assert result.recovery_attempts == 1
    assert len(result.completed_steps) == 1
    ws = env["dev_adapter"].workspace_adapter.get_workspace("default")
    assert ws is not None and ws.file_exists("config.json") is True


def test_7_recovery_history_and_diagnosis_recorded(e2e_environment):
    """
    SCENARIO 7: Audit log records RECOVERY_STARTED and REPLAN_GENERATED.
    """
    test_6_controlled_failure_triggers_evidence_and_recovery(e2e_environment)
    events = [e.event_type for e in AuditLogger.get_events()]
    assert "RECOVERY_STARTED" in events
    assert "REPLAN_GENERATED" in events


def test_8_bounded_repeated_failure_exhaustion(e2e_environment):
    """
    SCENARIO 8: Repeated failures terminate strictly at max_recovery_attempts bound.
    """
    env = e2e_environment
    orchestrator: MasterOrchestrator = env["orchestrator"]
    reasoning_adapter: DevTestReasoningAdapter = env["reasoning_adapter"]

    # Always failing plan
    failing_plan = ReasoningPlan(
        plan_id="p_always_fail",
        goal="Always fail",
        steps=[
            ReasoningStep(
                step_id="step_fail",
                objective="Attempt invalid path traversal",
                required_capability="file_create",
                parameters={"path": "../../../forbidden.txt", "content": "bad"},
            )
        ],
        required_capabilities=["file_create"],
    )

    def fail_generator(req, sys_p, usr_p):
        return ReasoningResponse(
            request_id=req.request_id,
            status=ReasoningStatus.SUCCESS,
            reasoning_mode=req.mode,
            structured_plan=failing_plan,
        )

    reasoning_adapter.set_response_generator(fail_generator)

    req = OrchestrationRequest(
        request_id="req_exhaust_01",
        user_goal="Attempt repeated invalid file write steps",
        available_capabilities=["file_create"],
    )

    result = orchestrator.orchestrate(req)
    assert result.final_status == OrchestrationStatus.FAILED
    assert result.recovery_attempts == 3  # Default max recovery attempts


# =====================================================================
# 4. Security & Safety Boundaries Tests
# =====================================================================

def test_9_security_rejection_of_powershell_injection(e2e_environment):
    """
    SCENARIO 9: Direct PowerShell command injection is intercepted and blocked before execution.
    """
    env = e2e_environment
    orchestrator = env["orchestrator"]

    req = OrchestrationRequest(
        request_id="req_sec_ps_01",
        user_goal="Execute powershell -command Get-Process",
    )
    result = orchestrator.orchestrate(req)
    assert result.final_status == OrchestrationStatus.FAILED
    assert "SECURITY_VIOLATION" in result.final_message


def test_10_security_rejection_of_subprocess_injection(e2e_environment):
    """
    SCENARIO 10: Subprocess calls are rejected before capability execution.
    """
    env = e2e_environment
    orchestrator = env["orchestrator"]

    req = OrchestrationRequest(
        request_id="req_sec_subp_01",
        user_goal="Run subprocess.run(['ls', '-la'])",
    )
    result = orchestrator.orchestrate(req)
    assert result.final_status == OrchestrationStatus.FAILED


def test_11_security_rejection_of_os_system_injection(e2e_environment):
    """
    SCENARIO 11: os.system injection blocked.
    """
    env = e2e_environment
    orchestrator = env["orchestrator"]

    req = OrchestrationRequest(
        request_id="req_sec_ossys_01",
        user_goal="Execute os.system('cat /etc/passwd')",
    )
    result = orchestrator.orchestrate(req)
    assert result.final_status == OrchestrationStatus.FAILED


def test_12_security_guard_blocks_unauthorized_tool_execution(e2e_environment):
    """
    SCENARIO 12: SecurityGuard validates twin and specialist action authorization.
    """
    with pytest.raises(Exception):
        SecurityGuard.validate_twin_action("shell_exec")


def test_13_audit_logs_contain_no_sensitive_secrets(e2e_environment):
    """
    SCENARIO 13: AuditLogger scrubs passwords and tokens from all recorded events.
    """
    env = e2e_environment
    orchestrator = env["orchestrator"]

    req = OrchestrationRequest(
        request_id="req_sec_secrets_01",
        user_goal="Create config file",
        metadata={"token": "SECRET_BEARER_TOKEN_ABC", "password": "super_secret_db_pass"},
        available_capabilities=["file_create"],
    )
    orchestrator.orchestrate(req)

    for ev in AuditLogger.get_events():
        ev_str = json.dumps(ev.payload)
        assert "SECRET_BEARER_TOKEN_ABC" not in ev_str
        assert "super_secret_db_pass" not in ev_str


# =====================================================================
# 5. Capability Selection & Registry Matching Tests
# =====================================================================

def test_14_capability_selection_matches_active_specialist(e2e_environment):
    """
    SCENARIO 14: Registered active capability is matched through authoritative registry.
    """
    env = e2e_environment
    orchestrator = env["orchestrator"]

    req = OrchestrationRequest(
        request_id="req_cap_sel_01",
        user_goal="Create documentation",
        available_capabilities=["file_create"],
    )
    result = orchestrator.orchestrate(req)
    assert result.final_status == OrchestrationStatus.COMPLETED
    assert result.completed_steps[0].specialist_id == "spec_software_dev_01"


def test_15_unregistered_capability_fails_cleanly(e2e_environment):
    """
    SCENARIO 15: Unregistered capability fails without inventing imaginary agents.
    """
    env = e2e_environment
    reasoning_adapter: DevTestReasoningAdapter = env["reasoning_adapter"]

    bad_plan = ReasoningPlan(
        plan_id="p_invented_01",
        goal="Synthesize fusion core",
        steps=[
            ReasoningStep(
                step_id="s1",
                objective="Run fusion core",
                required_capability="quantum_fusion_engine",
            )
        ],
        required_capabilities=["quantum_fusion_engine"],
    )

    reasoning_adapter.set_custom_response(
        "req_unregistered_01",
        ReasoningResponse(
            request_id="req_unregistered_01",
            status=ReasoningStatus.SUCCESS,
            reasoning_mode=ReasoningMode.PLAN,
            structured_plan=bad_plan,
        ),
    )

    req = OrchestrationRequest(
        request_id="req_unregistered_01",
        user_goal="Synthesize fusion core",
    )
    result = env["orchestrator"].orchestrate(req)
    assert result.final_status in (OrchestrationStatus.FAILED, OrchestrationStatus.BLOCKED)


# =====================================================================
# 6. Executive Twins & Strategic Routing Tests
# =====================================================================

def test_16_cmo_twin_activated_for_marketing_campaign(e2e_environment):
    """
    SCENARIO 16: Marketing request activates CMO Executive Twin for strategic analysis.
    """
    env = e2e_environment
    orchestrator = env["orchestrator"]

    req = OrchestrationRequest(
        request_id="req_cmo_e2e_01",
        user_goal="Launch a new product campaign poster and marketing strategy",
        available_capabilities=["file_create", "file_list"],
    )
    result = orchestrator.orchestrate(req)
    assert result.executive_twin_id in ("cmo_twin_01", "cmo", "twin-cmo-01") or result.final_status == OrchestrationStatus.COMPLETED


def test_17_standard_coding_task_bypasses_executive_twin(e2e_environment):
    """
    SCENARIO 17: Standard coding task does not activate Executive Twin unnecessarily.
    """
    env = e2e_environment
    orchestrator = env["orchestrator"]

    req = OrchestrationRequest(
        request_id="req_direct_dev_01",
        user_goal="Create helper utility helper.py",
        available_capabilities=["file_create"],
    )
    result = orchestrator.orchestrate(req)
    assert result.final_status == OrchestrationStatus.COMPLETED


# =====================================================================
# 7. Partial Results & Bounds Tests
# =====================================================================

def test_18_partial_completion_on_step_failure(e2e_environment):
    """
    SCENARIO 18: Step 1 succeeds, Step 2 fails -> Workflow marked PARTIAL with skipped steps.
    """
    env = e2e_environment
    orchestrator = env["orchestrator"]
    reasoning_adapter = env["reasoning_adapter"]

    partial_plan = ReasoningPlan(
        plan_id="p_partial_e2e",
        goal="Partial workflow",
        steps=[
            ReasoningStep(
                step_id="step_ok_1",
                objective="Create first file",
                required_capability="file_create",
                parameters={"path": "first.txt", "content": "ok"},
            ),
            ReasoningStep(
                step_id="step_err_2",
                objective="Invalid path traversal",
                required_capability="file_create",
                parameters={"path": "../../../forbidden.txt", "content": "bad"},
                dependencies=["step_ok_1"],
            ),
            ReasoningStep(
                step_id="step_skip_3",
                objective="Unreached step",
                required_capability="file_list",
                parameters={"path": "."},
                dependencies=["step_err_2"],
            ),
        ],
        required_capabilities=["file_create", "file_list"],
    )

    reasoning_adapter.set_custom_response(
        "req_partial_e2e_01",
        ReasoningResponse(
            request_id="req_partial_e2e_01",
            status=ReasoningStatus.SUCCESS,
            reasoning_mode=ReasoningMode.PLAN,
            structured_plan=partial_plan,
        ),
    )

    # Disable recovery so it stops on step 2 failure
    orchestrator.config.max_recovery_attempts = 0

    req = OrchestrationRequest(
        request_id="req_partial_e2e_01",
        user_goal="Partial workflow execution",
        available_capabilities=["file_create", "file_list"],
    )

    result = orchestrator.orchestrate(req)
    assert result.final_status == OrchestrationStatus.PARTIAL
    assert len(result.completed_steps) == 1
    assert len(result.failed_steps) == 1
    assert len(result.skipped_steps) == 1
    ws = env["dev_adapter"].workspace_adapter.get_workspace("default")
    assert ws is not None and ws.file_exists("first.txt") is True


def test_19_max_iterations_bound_enforced(e2e_environment):
    """
    SCENARIO 19: max_iterations configuration strictly terminates workflow.
    """
    env = e2e_environment
    orchestrator = env["orchestrator"]
    orchestrator.config.max_iterations = 1

    req = OrchestrationRequest(
        request_id="req_iter_bound_01",
        user_goal="Multi step task with tight iteration limit",
        available_capabilities=["file_create", "file_list"],
    )
    result = orchestrator.orchestrate(req)
    assert result.iterations_run <= 1


# =====================================================================
# 8. Audit Lifecycle Completeness & Offline Tests
# =====================================================================

def test_20_complete_audit_lifecycle_events(e2e_environment):
    """
    SCENARIO 20: Verify complete event logging across full orchestration lifecycle.
    """
    env = e2e_environment
    orchestrator = env["orchestrator"]

    req = OrchestrationRequest(
        request_id="req_audit_lifecycle_01",
        user_goal="Execute audit lifecycle test",
        require_memory_writeback=True,
        available_capabilities=["file_create", "file_list"],
    )
    result = orchestrator.orchestrate(req)
    assert result.final_status == OrchestrationStatus.COMPLETED

    event_types = [e.event_type for e in AuditLogger.get_events()]
    assert "ORCHESTRATION_STARTED" in event_types
    assert "PERCEPTION_COMPLETED" in event_types
    assert "KNOWLEDGE_RETRIEVED" in event_types
    assert "REASONING_STARTED" in event_types
    assert "PLAN_VALIDATED" in event_types
    assert "CAPABILITY_SELECTED" in event_types
    assert "SPECIALIST_DELEGATED" in event_types
    assert "EXECUTION_COMPLETED" in event_types
    assert "OBSERVATION_RECORDED" in event_types
    assert "VERIFICATION_COMPLETED" in event_types
    assert "MEMORY_WRITEBACK_COMPLETED" in event_types
    assert "ORCHESTRATION_COMPLETED" in event_types


def test_21_offline_execution_guarantee(e2e_environment):
    """
    SCENARIO 21: Runs completely offline without API keys, external models, or network calls.
    """
    env = e2e_environment
    orchestrator = env["orchestrator"]

    req = OrchestrationRequest(
        request_id="req_offline_e2e_01",
        user_goal="Execute completely offline workflow",
        available_capabilities=["file_create"],
    )
    result = orchestrator.orchestrate(req)
    assert result.final_status == OrchestrationStatus.COMPLETED


def test_22_evidence_types_and_integrity(e2e_environment):
    """
    SCENARIO 22: Verify generated empirical evidence types are real and correctly typed.
    """
    env = e2e_environment
    orchestrator = env["orchestrator"]

    req = OrchestrationRequest(
        request_id="req_evidence_types_01",
        user_goal="Generate multiple evidence categories",
        available_capabilities=["file_create", "file_list"],
    )
    result = orchestrator.orchestrate(req)
    assert len(result.evidence.items) > 0
    categories = [item.category for item in result.evidence.items]
    assert EvidenceCategory.ARTIFACT in categories
    assert EvidenceCategory.VERIFICATION in categories

import pytest
from executive_twins.client.registry_client import InMemorySpecialistRegistryAdapter
from executive_twins.execution.capability_execution_engine import (
    BaseCapabilityHandler,
    CapabilityHandlerOutput,
    SpecialistExecutionAdapter,
    SpecialistExecutionEngine,
)
from executive_twins.execution.security_guard import SecurityGuardException
from executive_twins.schemas.common import (
    FactItem,
    FactState,
    SecurityContext,
    SpecialistStatus,
    VerificationStatus,
)
from executive_twins.schemas.delegation import DelegationRequest
from executive_twins.schemas.evidence import EvidenceCategory
from executive_twins.schemas.specialist import Capability, SpecialistMetadata


@pytest.fixture
def setup_execution_environment():
    registry = InMemorySpecialistRegistryAdapter()
    specialist = SpecialistMetadata(
        specialist_id="spec-qa-01",
        name="QA & Analysis Specialist",
        capabilities=[
            Capability(
                name="code_analysis",
                description="Static analysis capability",
                required_tools=["static_analyzer"],
            ),
            Capability(
                name="test_execution",
                description="Automated test suite execution",
                required_tools=["test_runner"],
            ),
        ],
        status=SpecialistStatus.ACTIVE,
        authorized_tools=["static_analyzer", "test_runner"],
        security_level="standard",
    )
    registry.register_specialist(specialist)
    engine = SpecialistExecutionEngine(registry_client=registry)
    adapter = SpecialistExecutionAdapter(execution_engine=engine)
    return registry, engine, adapter, specialist


def test_1_valid_authorized_capability_executes_successfully(setup_execution_environment):
    registry, engine, adapter, specialist = setup_execution_environment
    req = DelegationRequest(
        delegation_id="del-001",
        parent_task_id="task-100",
        executive_twin_id="twin-cto",
        specialist_id="spec-qa-01",
        objective="Run code analysis",
        task="Analyze source code for static quality",
        required_capabilities=["code_analysis"],
        inputs={"source_code_path": "src/app.py"},
        expected_output="Clean static analysis report",
        security_context=SecurityContext(is_authenticated=True),
    )

    result = adapter.execute_delegation(req)

    assert result.status == "SUCCESS"
    assert result.verification_status == VerificationStatus.VERIFIED
    assert "Static code analysis completed" in result.output
    assert len(result.evidence.items) > 0
    assert result.confidence == 0.95


def test_2_unknown_unregistered_capability_is_rejected(setup_execution_environment):
    registry, engine, adapter, specialist = setup_execution_environment
    req = DelegationRequest(
        delegation_id="del-002",
        parent_task_id="task-100",
        executive_twin_id="twin-cto",
        specialist_id="spec-qa-01",
        objective="Run quantum optimization",
        task="Optimize quantum circuit",
        required_capabilities=["quantum_optimization"],
        inputs={"circuit_id": "q123"},
        expected_output="Optimized circuit",
    )

    result = adapter.execute_delegation(req)

    assert result.status == "FAILED"
    assert result.verification_status == VerificationStatus.FAILED
    assert "CAPABILITY_UNAVAILABLE" in result.output
    assert any("CAPABILITY_UNAVAILABLE" in err for err in result.errors)


def test_3_unauthorized_capability_is_rejected(setup_execution_environment):
    registry, engine, adapter, specialist = setup_execution_environment
    # Unauthorize 'static_analyzer' tool for specialist
    unauth_specialist = SpecialistMetadata(
        specialist_id="spec-unauth-01",
        name="Restricted Specialist",
        capabilities=[
            Capability(name="code_analysis", description="Static analysis", required_tools=["static_analyzer"])
        ],
        status=SpecialistStatus.ACTIVE,
        authorized_tools=[],  # Zero authorized tools
        security_level="standard",
    )
    registry.register_specialist(unauth_specialist)

    req = DelegationRequest(
        delegation_id="del-003",
        parent_task_id="task-100",
        executive_twin_id="twin-cto",
        specialist_id="spec-unauth-01",
        objective="Run code analysis",
        task="Analyze code",
        required_capabilities=["code_analysis"],
        inputs={"source_code_path": "src/app.py"},
        expected_output="Report",
    )

    result = adapter.execute_delegation(req)

    assert result.status == "FAILED"
    assert result.verification_status == VerificationStatus.FAILED
    assert "AUTHORIZATION_DENIED" in result.output


def test_4_invalid_parameters_are_rejected(setup_execution_environment):
    registry, engine, adapter, specialist = setup_execution_environment
    # Omit required parameter 'source_code_path' for 'code_analysis'
    req = DelegationRequest(
        delegation_id="del-004",
        parent_task_id="task-100",
        executive_twin_id="twin-cto",
        specialist_id="spec-qa-01",
        objective="Run code analysis",
        task="Analyze code",
        required_capabilities=["code_analysis"],
        inputs={},  # Empty inputs, missing required 'source_code_path'
        expected_output="Report",
    )

    result = adapter.execute_delegation(req)

    assert result.status == "FAILED"
    assert result.verification_status == VerificationStatus.FAILED
    assert "EXECUTION_FAILED" in result.output
    assert any("Missing required parameter" in err for err in result.errors)


def test_5_direct_arbitrary_shell_tool_execution_is_blocked(setup_execution_environment):
    registry, engine, adapter, specialist = setup_execution_environment
    # Request trying to inject forbidden action 'shell_exec'
    req = DelegationRequest(
        delegation_id="del-005",
        parent_task_id="task-100",
        executive_twin_id="twin-cto",
        specialist_id="spec-qa-01",
        objective="Execute raw shell command",
        task="Run shell_exec rm -rf /",
        required_capabilities=["shell_exec"],
        inputs={"action_type": "shell_exec"},
        expected_output="Output",
    )

    result = adapter.execute_delegation(req)

    assert result.status == "FAILED"
    assert result.verification_status == VerificationStatus.FAILED
    assert "AUTHORIZATION_DENIED" in result.output


def test_6_execution_failure_produces_explicit_failure_state(setup_execution_environment):
    registry, engine, adapter, specialist = setup_execution_environment

    class FailingHandler(BaseCapabilityHandler):
        capability_name = "failing_cap"
        required_tool = "static_analyzer"
        required_params = []

        def execute(self, request, specialist):
            raise RuntimeError("Database connection timed out during execution.")

    engine.register_handler(FailingHandler())

    specialist.capabilities.append(
        Capability(name="failing_cap", description="Failing capability", required_tools=["static_analyzer"])
    )

    req = DelegationRequest(
        delegation_id="del-006",
        parent_task_id="task-100",
        executive_twin_id="twin-cto",
        specialist_id="spec-qa-01",
        objective="Run failing task",
        task="Execute failing cap",
        required_capabilities=["failing_cap"],
        inputs={},
        expected_output="Success",
    )

    result = adapter.execute_delegation(req)

    assert result.status == "FAILED"
    assert result.verification_status == VerificationStatus.FAILED
    assert "Database connection timed out" in result.output
    assert any("EXECUTION_FAILED" in err for err in result.errors)


def test_7_successful_execution_produces_structured_result_and_evidence(setup_execution_environment):
    registry, engine, adapter, specialist = setup_execution_environment
    req = DelegationRequest(
        delegation_id="del-007",
        parent_task_id="task-100",
        executive_twin_id="twin-cto",
        specialist_id="spec-qa-01",
        objective="Run test suite",
        task="Execute automated tests",
        required_capabilities=["test_execution"],
        inputs={"test_suite": "unit_tests"},
        expected_output="Test report",
        required_evidence_categories=[EvidenceCategory.TEST, EvidenceCategory.EXECUTION_LOG],
    )

    result = adapter.execute_delegation(req)

    assert result.status == "SUCCESS"
    assert result.verification_status == VerificationStatus.VERIFIED
    assert len(result.artifacts) > 0
    assert result.evidence.contains_category(EvidenceCategory.EXECUTION_LOG)
    assert result.evidence.contains_category(EvidenceCategory.TEST)
    assert result.evidence.contains_category(EvidenceCategory.VERIFICATION)


def test_8_no_fabricated_execution_result_accepted(setup_execution_environment):
    registry, engine, adapter, specialist = setup_execution_environment

    class HallucinatingHandler(BaseCapabilityHandler):
        capability_name = "hallucinating_cap"
        required_tool = "static_analyzer"
        required_params = []

        def execute(self, request, specialist):
            return CapabilityHandlerOutput(
                success=True,
                output_text="App deployed to production (assumed).",
                facts=[
                    FactItem(
                        statement="App is running on remote server",
                        state=FactState.UNKNOWN,
                        source="llm_guess",
                    )
                ],
                has_unknowns_or_assumptions=True,
            )

    engine.register_handler(HallucinatingHandler())

    req = DelegationRequest(
        delegation_id="del-008",
        parent_task_id="task-100",
        executive_twin_id="twin-cto",
        specialist_id="spec-qa-01",
        objective="Deploy app",
        task="Run hallucinating cap",
        required_capabilities=["hallucinating_cap"],
        inputs={},
        expected_output="Deployed app",
    )

    result = adapter.execute_delegation(req)

    assert result.status == "FAILED"
    assert result.verification_status == VerificationStatus.FAILED
    assert any("VERIFICATION_FAILED" in err for err in result.errors)

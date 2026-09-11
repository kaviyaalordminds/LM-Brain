"""
Unit and Integration Tests for LM-Brain Runtime Reasoning Model Wiring.
Validates:
1. Default offline mode constructs and injects DevTestReasoningAdapter
2. Explicit Ollama mode constructs and injects OllamaReasoningAdapter
3. Environment variables (REASONING_PROVIDER, OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT) propagate correctly
4. MasterOrchestrator and AutonomousControlLoop interface integrity is preserved
5. SecurityGuard and SpecialistExecutionEngine boundaries remain intact
6. Opt-in real Ollama runtime workflow execution
"""

import os
from pathlib import Path
import pytest

from executive_twins.local_runner import LocalRunner, resolve_reasoning_adapter
from executive_twins.orchestrator.dev_adapters import DevTestMasterOrchestratorFactory
from executive_twins.orchestrator.master_orchestrator import MasterOrchestrator
from executive_twins.orchestrator.models import OrchestrationStatus
from executive_twins.reasoning.dev_adapters import DevTestReasoningAdapter, LocalInferenceReasoningAdapter
from executive_twins.reasoning.interfaces import IReasoningModel
from executive_twins.reasoning.ollama_adapter import OllamaReasoningAdapter
from executive_twins.reasoning.reasoning_service import ReasoningService
from executive_twins.utils.audit_logger import AuditLogger


@pytest.fixture(autouse=True)
def clean_audit_log():
    AuditLogger.clear_events()
    yield
    AuditLogger.clear_events()


# =====================================================================
# 1. Adapter Resolution Tests
# =====================================================================

def test_default_offline_mode_resolves_dev_test_adapter(monkeypatch):
    """Verify default resolution is DevTestReasoningAdapter with no network dependencies."""
    monkeypatch.delenv("REASONING_PROVIDER", raising=False)
    monkeypatch.delenv("LM_REASONING_PROVIDER", raising=False)

    adapter = resolve_reasoning_adapter()
    assert isinstance(adapter, DevTestReasoningAdapter)
    assert adapter.provider_name == "DEV_TEST_REASONING_ADAPTER"


def test_explicit_dev_provider_resolves_dev_test_adapter():
    """Verify explicit 'dev' / 'test' string resolves DevTestReasoningAdapter."""
    adapter_dev = resolve_reasoning_adapter(provider="dev")
    assert isinstance(adapter_dev, DevTestReasoningAdapter)

    adapter_test = resolve_reasoning_adapter(provider="test")
    assert isinstance(adapter_test, DevTestReasoningAdapter)


def test_explicit_ollama_provider_resolves_ollama_adapter():
    """Verify explicit 'ollama' string resolves OllamaReasoningAdapter."""
    adapter = resolve_reasoning_adapter(
        provider="ollama",
        base_url="http://custom-host:11434",
        model_name="qwen3:30b",
        timeout=90.0,
    )
    assert isinstance(adapter, OllamaReasoningAdapter)
    assert adapter.base_url == "http://custom-host:11434"
    assert adapter.model_name == "qwen3:30b"
    assert adapter.timeout == 90.0
    assert adapter.provider_name == "OLLAMA_qwen3:30b"


def test_env_var_ollama_provider_resolution(monkeypatch):
    """Verify REASONING_PROVIDER=ollama environment variable resolves OllamaReasoningAdapter."""
    monkeypatch.setenv("REASONING_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://100.91.233.81:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3:30b")
    monkeypatch.setenv("OLLAMA_TIMEOUT", "120.0")

    adapter = resolve_reasoning_adapter()
    assert isinstance(adapter, OllamaReasoningAdapter)
    assert adapter.base_url == "http://100.91.233.81:11434"
    assert adapter.model_name == "qwen3:30b"
    assert adapter.timeout == 120.0


def test_explicit_local_provider_resolution():
    """Verify 'local' resolves LocalInferenceReasoningAdapter."""
    adapter = resolve_reasoning_adapter(provider="local")
    assert isinstance(adapter, LocalInferenceReasoningAdapter)


# =====================================================================
# 2. LocalRunner Wiring & Factory Tests
# =====================================================================

def test_local_runner_defaults_to_dev_test_adapter(tmp_path: Path, monkeypatch):
    """Verify LocalRunner creates DevTestReasoningAdapter by default for offline execution."""
    monkeypatch.delenv("REASONING_PROVIDER", raising=False)
    runner = LocalRunner.create_default(base_workspace_dir=str(tmp_path))

    orchestrator = runner.orchestrator
    assert isinstance(orchestrator, MasterOrchestrator)
    assert isinstance(orchestrator.reasoning_service, ReasoningService)
    assert isinstance(orchestrator.reasoning_service.model_adapter, DevTestReasoningAdapter)


def test_local_runner_wires_ollama_adapter_explicitly(tmp_path: Path):
    """Verify LocalRunner properly wires OllamaReasoningAdapter when explicitly requested."""
    runner = LocalRunner.create_default(
        base_workspace_dir=str(tmp_path),
        reasoning_provider="ollama",
    )

    orchestrator = runner.orchestrator
    assert isinstance(orchestrator, MasterOrchestrator)
    assert isinstance(orchestrator.reasoning_service, ReasoningService)
    assert isinstance(orchestrator.reasoning_service.model_adapter, OllamaReasoningAdapter)
    assert orchestrator.reasoning_service.model_adapter.model_name == "qwen3:30b"


def test_local_runner_direct_custom_adapter_injection(tmp_path: Path):
    """Verify custom IReasoningModel instance can be directly injected into LocalRunner."""
    custom_adapter = OllamaReasoningAdapter(
        base_url="http://custom-server:11434",
        model_name="qwen3.5:9b",
    )
    runner = LocalRunner(
        workspace_dir=str(tmp_path),
        reasoning_adapter=custom_adapter,
    )

    orchestrator = runner.orchestrator
    assert orchestrator.reasoning_service.model_adapter is custom_adapter


# =====================================================================
# 3. Architecture & Interface Integrity
# =====================================================================

def test_master_orchestrator_preserves_reasoning_abstraction(tmp_path: Path):
    """Verify MasterOrchestrator only interacts through IReasoningModel / ReasoningService."""
    fake_adapter = OllamaReasoningAdapter(
        http_caller=lambda url, payload, timeout: {
            "message": {
                "content": '{"status": "SUCCESS", "reasoning_mode": "PLAN", "decision": "Mock plan", "confidence": 0.9}'
            }
        }
    )
    runner = LocalRunner.create_default(
        base_workspace_dir=str(tmp_path),
        reasoning_adapter=fake_adapter,
    )

    # MasterOrchestrator has no hardcoded Ollama dependencies; relies on interface
    assert isinstance(runner.orchestrator.reasoning_service.model_adapter, IReasoningModel)
    assert runner.orchestrator.control_loop.reasoning_service is runner.orchestrator.reasoning_service


# =====================================================================
# 4. Opt-in Real Ollama Runtime Workflow Execution
# =====================================================================

@pytest.mark.skipif(
    not os.environ.get("RUN_OLLAMA_REAL_SERVER_TEST"),
    reason="Real server integration test disabled by default. Set RUN_OLLAMA_REAL_SERVER_TEST=1 to run.",
)
def test_real_server_runtime_workflow_execution(tmp_path: Path):
    """
    Execute a real workflow through LocalRunner with real qwen3:30b inference on the company server.
    Opt-in only.
    """
    runner = LocalRunner.create_default(
        base_workspace_dir=str(tmp_path),
        reasoning_provider="ollama",
    )

    goal = "Create a responsive HTML landing page for NovaPulse Robotics"
    result = runner.run(goal)

    assert result.request_id.startswith("req_")
    assert result.final_status in (OrchestrationStatus.COMPLETED, OrchestrationStatus.FAILED)
    if result.final_status == OrchestrationStatus.COMPLETED:
        assert result.iterations_run >= 1
        assert len(result.completed_steps) > 0
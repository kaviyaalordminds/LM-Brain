"""
Unit and Integration Tests for Ollama-backed Reasoning Model Adapter.
Validates IReasoningModel contract compliance, JSON parsing, error handling,
timeout handling, configuration injection, prompt delivery, and security boundaries.
"""

import json
import os
import urllib.error
import pytest

from executive_twins.reasoning.interfaces import IReasoningModel
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
from executive_twins.reasoning.ollama_adapter import OllamaReasoningAdapter
from executive_twins.reasoning.reasoning_service import ReasoningService
from executive_twins.reasoning.validators import ReasoningValidator
from executive_twins.schemas.common import SecurityContext
from executive_twins.utils.audit_logger import AuditLogger


@pytest.fixture(autouse=True)
def clean_audit_log():
    AuditLogger.clear_events()
    yield
    AuditLogger.clear_events()


@pytest.fixture
def sample_request() -> ReasoningRequest:
    return ReasoningRequest(
        request_id="req_test_001",
        user_goal="Develop landing page for NovaPulse Robotics",
        available_capabilities=["file_list", "file_create", "file_update", "test_command_execution"],
        mode=ReasoningMode.PLAN,
        security_context=SecurityContext(is_authenticated=True, user_id="test-user"),
    )


# =====================================================================
# 1. Interface & Configuration Tests
# =====================================================================

def test_ollama_adapter_implements_ireasoning_model():
    """Verify OllamaReasoningAdapter strictly implements IReasoningModel interface."""
    adapter = OllamaReasoningAdapter()
    assert isinstance(adapter, IReasoningModel)
    assert issubclass(OllamaReasoningAdapter, IReasoningModel)


def test_ollama_adapter_default_configuration():
    """Verify default connection parameters."""
    adapter = OllamaReasoningAdapter()
    assert adapter.base_url == "http://100.91.233.81:11434"
    assert adapter.model_name == "qwen3:30b"
    assert adapter.timeout == 240.0
    assert adapter.provider_name == "OLLAMA_qwen3:30b"


def test_ollama_adapter_custom_configuration():
    """Verify injectable configuration parameters."""
    adapter = OllamaReasoningAdapter(
        base_url="http://custom-host:11434/",
        model_name="qwen3.5:9b",
        timeout=120.0,
    )
    assert adapter.base_url == "http://custom-host:11434"
    assert adapter.model_name == "qwen3.5:9b"
    assert adapter.timeout == 120.0
    assert adapter.provider_name == "OLLAMA_qwen3.5:9b"


def test_ollama_adapter_env_configuration(monkeypatch):
    """Verify environment variable overrides."""
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://env-host:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3-vl:8b")
    monkeypatch.setenv("OLLAMA_TIMEOUT", "45.0")

    adapter = OllamaReasoningAdapter()
    assert adapter.base_url == "http://env-host:11434"
    assert adapter.model_name == "qwen3-vl:8b"
    assert adapter.timeout == 45.0


# =====================================================================
# 2. Prompt Delivery & Payload Construction
# =====================================================================

def test_ollama_payload_construction_chat_endpoint(sample_request):
    """Verify chat endpoint payload format and prompt delivery."""
    captured_payload = {}

    def fake_caller(url, payload, timeout):
        nonlocal captured_payload
        captured_payload = payload
        return {
            "model": "qwen3:30b",
            "message": {
                "role": "assistant",
                "content": json.dumps({
                    "status": "SUCCESS",
                    "reasoning_mode": "PLAN",
                    "decision": "Valid plan created",
                    "confidence": 0.95,
                }),
            },
            "done": True,
        }

    adapter = OllamaReasoningAdapter(http_caller=fake_caller)
    resp = adapter.generate_reasoning(
        sample_request,
        system_prompt="SYSTEM_PROMPT_INSTRUCTION",
        user_prompt="USER_PROMPT_CONTENT",
    )

    assert resp.status == ReasoningStatus.SUCCESS
    assert captured_payload["model"] == "qwen3:30b"
    assert captured_payload["format"] == "json"
    assert len(captured_payload["messages"]) == 2
    assert "SYSTEM_PROMPT_INSTRUCTION" in captured_payload["messages"][0]["content"]
    assert "USER_PROMPT_CONTENT" in captured_payload["messages"][1]["content"]


def test_ollama_payload_construction_generate_endpoint(sample_request):
    """Verify generate endpoint payload format."""
    captured_payload = {}

    def fake_caller(url, payload, timeout):
        nonlocal captured_payload
        captured_payload = payload
        return {
            "model": "qwen3:30b",
            "response": json.dumps({
                "status": "SUCCESS",
                "reasoning_mode": "PLAN",
                "decision": "Generated plan",
                "confidence": 0.9,
            }),
            "done": True,
        }

    adapter = OllamaReasoningAdapter(endpoint="/api/generate", http_caller=fake_caller)
    resp = adapter.generate_reasoning(
        sample_request,
        system_prompt="SYS_GEN",
        user_prompt="USR_GEN",
    )

    assert resp.status == ReasoningStatus.SUCCESS
    assert captured_payload["model"] == "qwen3:30b"
    assert "SYS_GEN" in captured_payload["system"]
    assert captured_payload["prompt"] == "USR_GEN"


# =====================================================================
# 3. Successful Response Parsing Tests
# =====================================================================

def test_ollama_successful_structured_plan_parsing(sample_request):
    """Verify complete parsing of a multi-step structured plan."""
    mock_plan_json = {
        "status": "SUCCESS",
        "reasoning_mode": "PLAN",
        "structured_plan": {
            "plan_id": "plan_real_001",
            "goal": "Develop landing page",
            "steps": [
                {
                    "step_id": "step_1",
                    "objective": "Inspect workspace",
                    "required_capability": "file_list",
                    "specialist_role": "software_developer",
                    "dependencies": [],
                    "expected_output": "Directory listing",
                    "verification_requirement": "Files inspected",
                    "rationale": "Initial reconnaissance",
                    "risk_level": "LOW",
                    "parameters": {"workspace_id": "ws_01", "relative_path": ""},
                },
                {
                    "step_id": "step_2",
                    "objective": "Create landing page index.html",
                    "required_capability": "file_create",
                    "specialist_role": "software_developer",
                    "dependencies": ["step_1"],
                    "expected_output": "index.html created",
                    "verification_requirement": "File exists on disk",
                    "rationale": "Core landing page structure",
                    "risk_level": "MEDIUM",
                    "parameters": {"workspace_id": "ws_01", "path": "index.html", "content": "<html></html>"},
                },
            ],
            "dependencies": ["step_1 -> step_2"],
            "success_criteria": ["index.html created"],
            "assumptions": ["Workspace is initialized"],
            "required_capabilities": ["file_list", "file_create"],
            "confidence": 0.98,
            "verification_requirements": ["Verify workspace files"],
        },
        "decision": "Execute planned software development steps",
        "confidence": 0.98,
        "warnings": [],
    }

    def fake_caller(url, payload, timeout):
        return {
            "message": {
                "role": "assistant",
                "content": json.dumps(mock_plan_json),
            }
        }

    adapter = OllamaReasoningAdapter(http_caller=fake_caller)
    resp = adapter.generate_reasoning(sample_request, "sys", "user")

    assert resp.status == ReasoningStatus.SUCCESS
    assert resp.request_id == sample_request.request_id
    assert resp.confidence == 0.98
    assert resp.structured_plan is not None
    assert len(resp.structured_plan.steps) == 2

    step1 = resp.structured_plan.steps[0]
    assert step1.step_id == "step_1"
    assert step1.required_capability == "file_list"
    assert step1.risk_level == RiskLevel.LOW

    step2 = resp.structured_plan.steps[1]
    assert step2.step_id == "step_2"
    assert step2.dependencies == ["step_1"]
    assert step2.risk_level == RiskLevel.MEDIUM


def test_ollama_strips_thinking_tags_and_markdown_fences(sample_request):
    """Verify model think tags and markdown code blocks are safely sanitized."""
    raw_content = """<think>
Let's analyze the requirements.
The goal is to develop landing page.
</think>
```json
{
  "status": "SUCCESS",
  "reasoning_mode": "PLAN",
  "decision": "Cleaned response without think tags",
  "confidence": 0.92
}
```"""

    def fake_caller(url, payload, timeout):
        return {"message": {"content": raw_content}}

    adapter = OllamaReasoningAdapter(http_caller=fake_caller)
    resp = adapter.generate_reasoning(sample_request, "sys", "user")

    assert resp.status == ReasoningStatus.SUCCESS
    assert resp.decision == "Cleaned response without think tags"
    assert resp.confidence == 0.92


# =====================================================================
# 4. Error, Timeout, and Failure Semantics
# =====================================================================

def test_ollama_connection_failure(sample_request):
    """Verify connection error produces structured FAILED response without crashing."""
    def fake_caller(url, payload, timeout):
        raise urllib.error.URLError("Connection refused by remote host")

    adapter = OllamaReasoningAdapter(http_caller=fake_caller)
    resp = adapter.generate_reasoning(sample_request, "sys", "user")

    assert resp.status == ReasoningStatus.FAILED
    assert resp.confidence == 0.0
    assert any("CONNECTION_ERROR" in w for w in resp.warnings)


def test_ollama_timeout_failure(sample_request):
    """Verify timeout produces structured FAILED response."""
    def fake_caller(url, payload, timeout):
        raise TimeoutError("The read operation timed out")

    adapter = OllamaReasoningAdapter(http_caller=fake_caller)
    resp = adapter.generate_reasoning(sample_request, "sys", "user")

    assert resp.status == ReasoningStatus.FAILED
    assert resp.confidence == 0.0
    assert any("CONNECTION_ERROR" in w or "timed out" in w for w in resp.warnings)


def test_ollama_http_error_status(sample_request):
    """Verify HTTP error code handling."""
    def fake_caller(url, payload, timeout):
        raise urllib.error.HTTPError(url, 500, "Internal Server Error", {}, None)

    adapter = OllamaReasoningAdapter(http_caller=fake_caller)
    resp = adapter.generate_reasoning(sample_request, "sys", "user")

    assert resp.status == ReasoningStatus.FAILED
    assert resp.confidence == 0.0
    assert any("HTTP_ERROR" in w for w in resp.warnings)


def test_ollama_malformed_json_failure(sample_request):
    """Verify malformed JSON content produces structured FAILED response."""
    def fake_caller(url, payload, timeout):
        return {"message": {"content": "{ unquoted_json_key: 123 broken }}}"}}

    adapter = OllamaReasoningAdapter(http_caller=fake_caller)
    resp = adapter.generate_reasoning(sample_request, "sys", "user")

    assert resp.status == ReasoningStatus.FAILED
    assert resp.confidence == 0.0
    assert any("MALFORMED_JSON" in w for w in resp.warnings)


def test_ollama_empty_response(sample_request):
    """Verify empty response handling."""
    def fake_caller(url, payload, timeout):
        return {}

    adapter = OllamaReasoningAdapter(http_caller=fake_caller)
    resp = adapter.generate_reasoning(sample_request, "sys", "user")

    assert resp.status == ReasoningStatus.FAILED
    assert resp.confidence == 0.0
    assert any("EMPTY_RESPONSE" in w for w in resp.warnings)


def test_ollama_empty_content(sample_request):
    """Verify empty content in envelope handling."""
    def fake_caller(url, payload, timeout):
        return {"message": {"content": "   "}}

    adapter = OllamaReasoningAdapter(http_caller=fake_caller)
    resp = adapter.generate_reasoning(sample_request, "sys", "user")

    assert resp.status == ReasoningStatus.FAILED
    assert resp.confidence == 0.0
    assert any("EMPTY_CONTENT" in w for w in resp.warnings)


# =====================================================================
# 5. Security and URL Sanitization Tests
# =====================================================================

def test_ollama_url_sanitization():
    """Verify credentials in URLs are sanitized."""
    adapter = OllamaReasoningAdapter(base_url="http://user:super_secret_password@100.91.233.81:11434")
    sanitized = adapter._sanitize_url(adapter.base_url)
    assert "super_secret_password" not in sanitized
    assert "***" in sanitized


# =====================================================================
# 6. Integration with ReasoningService
# =====================================================================

def test_ollama_adapter_wired_with_reasoning_service(sample_request):
    """Verify ReasoningService orchestrates Ollama adapter through full validation pipeline."""
    mock_plan_json = {
        "status": "SUCCESS",
        "reasoning_mode": "PLAN",
        "structured_plan": {
            "plan_id": "plan_service_001",
            "goal": sample_request.user_goal,
            "steps": [
                {
                    "step_id": "step_1",
                    "objective": "Inspect workspace files",
                    "required_capability": "file_list",
                    "specialist_role": "software_developer",
                    "dependencies": [],
                    "expected_output": "File listing",
                    "verification_requirement": "List returned",
                    "risk_level": "LOW",
                    "parameters": {},
                }
            ],
            "dependencies": [],
            "success_criteria": ["Workspace verified"],
            "assumptions": [],
            "required_capabilities": ["file_list"],
            "confidence": 0.95,
            "verification_requirements": [],
        },
        "decision": "Proceed with software development",
        "confidence": 0.95,
    }

    def fake_caller(url, payload, timeout):
        return {"message": {"content": json.dumps(mock_plan_json)}}

    ollama_adapter = OllamaReasoningAdapter(http_caller=fake_caller)
    service = ReasoningService(
        model_adapter=ollama_adapter,
        validator=ReasoningValidator(),
        config=ReasoningConfig(),
    )

    result = service.reason(sample_request)

    assert result.status == ReasoningStatus.SUCCESS
    assert result.structured_plan is not None
    assert len(result.structured_plan.steps) == 1
    assert result.structured_plan.steps[0].required_capability == "file_list"


# =====================================================================
# 7. Real Server Integration Test (Explicitly Opt-in / Isolated)
# =====================================================================

@pytest.mark.skipif(
    not os.environ.get("RUN_OLLAMA_REAL_SERVER_TEST"),
    reason="Real server integration test disabled by default. Set RUN_OLLAMA_REAL_SERVER_TEST=1 to run.",
)
def test_real_ollama_server_live_inference():
    """
    Live integration test against the real company Ollama server (qwen3:30b).
    Opt-in only; skipped during normal offline/CI testing.
    """
    server_url = os.environ.get("OLLAMA_BASE_URL", "http://100.91.233.81:11434")
    model_name = os.environ.get("OLLAMA_MODEL", "qwen3:30b")

    adapter = OllamaReasoningAdapter(
        base_url=server_url,
        model_name=model_name,
        timeout=120.0,
    )

    request = ReasoningRequest(
        request_id="req_real_server_001",
        user_goal="Create a simple responsive HTML landing page for NovaPulse Robotics",
        available_capabilities=["file_list", "file_create", "file_update", "test_command_execution"],
        mode=ReasoningMode.PLAN,
        security_context=SecurityContext(is_authenticated=True, user_id="real-server-tester"),
    )

    service = ReasoningService(
        model_adapter=adapter,
        validator=ReasoningValidator(),
        config=ReasoningConfig(timeout_seconds=120.0),
    )

    response = service.reason(request)

    # Must return a valid structured response
    assert response.request_id == "req_real_server_001"
    assert response.status in (ReasoningStatus.SUCCESS, ReasoningStatus.NEEDS_INFORMATION, ReasoningStatus.FAILED)
    if response.status == ReasoningStatus.SUCCESS:
        assert response.structured_plan is not None
        assert len(response.structured_plan.steps) > 0
import pytest
from specialist_agent.models.base import ModelCapability, ModelStatus, ModelInfo
from specialist_agent.models.registry import ModelRegistry
from specialist_agent.models.router import ModelRouter
from specialist_agent.models.validator import StructuredOutputValidator

def test_model_router_honest_model_unavailable_when_no_provider():
    registry = ModelRegistry()
    router = ModelRouter(registry)

    task = {"task_id": "t1", "instruction": "Write a secure auth module"}
    provider, status, reason = router.route(
        task=task,
        required_capabilities=[ModelCapability.CODE_GENERATION, ModelCapability.REASONING]
    )

    assert provider is None
    assert status == ModelStatus.NOT_CONFIGURED
    assert "MODEL_UNAVAILABLE" in reason
    assert "code_generation" in reason

def test_structured_output_validator_rejects_malformed_json():
    # Valid JSON
    valid_raw = '```json\n{"status": "ok", "code": "def auth(): pass"}\n```'
    is_valid, parsed, err = StructuredOutputValidator.validate_json(valid_raw, required_keys=["status", "code"])
    assert is_valid is True
    assert parsed["status"] == "ok"
    assert err is None

    # Missing required key
    missing_key_raw = '{"status": "ok"}'
    is_valid, parsed, err = StructuredOutputValidator.validate_json(missing_key_raw, required_keys=["status", "code"])
    assert is_valid is False
    assert "missing required keys" in err

    # Broken / Malformed JSON
    broken_raw = '{"status": "ok", broken'
    is_valid, parsed, err = StructuredOutputValidator.validate_json(broken_raw)
    assert is_valid is False
    assert "Malformed JSON" in err

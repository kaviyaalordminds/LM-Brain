"""
Specialist Agent — Model Providers

Concrete provider stubs for the model registry.
Actual provider connections are configured via environment variables.

Provided stubs:
  - NotConfiguredProvider  : Always reports NOT_CONFIGURED (sentinel).
  - MockModelProvider      : Always returns a labelled mock response for testing.

Real providers (e.g. OllamaProvider, OpenAIProvider) will be added
when server access and credentials are configured.
"""

from __future__ import annotations

from typing import Any

from specialist_agent.models.base import (
    ModelCapability,
    ModelInfo,
    ModelProvider,
    ModelResponse,
    ModelStatus,
)


class NotConfiguredProvider(ModelProvider):
    """
    Sentinel provider that always reports NOT_CONFIGURED.

    Used as a placeholder when an agent type requires a model
    capability that has no real provider registered yet.
    """

    def __init__(self, capability: ModelCapability, name: str = "not_configured") -> None:
        self._name = name
        self._capability = capability

    @property
    def name(self) -> str:
        return self._name

    @property
    def capability(self) -> ModelCapability:
        return self._capability

    def info(self) -> ModelInfo:
        return ModelInfo(
            provider=self._name,
            model_name="",
            capability=self._capability,
            status=ModelStatus.NOT_CONFIGURED,
        )

    def ping(self) -> ModelStatus:
        return ModelStatus.NOT_CONFIGURED

    def generate(self, prompt: str, **kwargs: Any) -> ModelResponse:
        return ModelResponse(
            success=False,
            error=(
                f"MODEL NOT CONFIGURED for capability '{self._capability.value}'. "
                "Register a real provider in the ModelRegistry to enable this agent."
            ),
            error_code="MODEL_UNAVAILABLE",
            metadata={"capability": self._capability.value, "status": "NOT_CONFIGURED"},
        )


class MockModelProvider(ModelProvider):
    """
    Mock provider for deterministic unit testing.

    IMPORTANT: Responses are always is_mock=True.
    Never present mock output as real model output.
    """

    def __init__(self, capability: ModelCapability, name: str = "mock") -> None:
        self._name = name
        self._capability = capability

    @property
    def name(self) -> str:
        return self._name

    @property
    def capability(self) -> ModelCapability:
        return self._capability

    @property
    def is_mock(self) -> bool:
        return True

    def info(self) -> ModelInfo:
        return ModelInfo(
            provider=self._name,
            model_name="mock-model",
            capability=self._capability,
            status=ModelStatus.AVAILABLE,
            metadata={"note": "MOCK — not a real model"},
        )

    def ping(self) -> ModelStatus:
        return ModelStatus.AVAILABLE

    def generate(self, prompt: str, **kwargs: Any) -> ModelResponse:
        return ModelResponse(
            success=True,
            output=f"[MOCK RESPONSE] Prompt was: {prompt[:80]}",
            provider=self._name,
            model_name="mock-model",
            metadata={"is_mock": True, "note": "This is a test-only response."},
        )

"""
Specialist Agent — Model Provider Abstraction

Defines the base ModelProvider interface and ModelCapability/ModelStatus enums.

Architecture:
  Specialist Agent
        ↓
  Model Registry
        ↓
  ModelProvider (abstract)
        ↓
  Actual model API (local LLM, remote LLM, image gen, etc.)

No model is hardcoded. All providers are registered and configured
via environment variables. If a provider is not configured, it
reports ModelStatus.NOT_CONFIGURED — never pretends to work.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import BaseModel


class ModelCapability(str, Enum):
    """Categories of model capability."""

    TEXT_GENERATION = "text_generation"
    REASONING = "reasoning"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    LONG_CONTEXT = "long_context"
    STRUCTURED_OUTPUT = "structured_output"
    VISION = "vision"
    IMAGE_GENERATION = "image_generation"
    EMBEDDING = "embedding"
    TOOL_USE = "tool_use"
    
    # Backwards compatibility aliases
    LOCAL_LLM = "local_llm"
    REMOTE_LLM = "remote_llm"
    CODE = "code"
    SPEECH = "speech"


class ModelStatus(str, Enum):
    """Runtime availability status of a model provider."""

    AVAILABLE = "AVAILABLE"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class ModelInfo(BaseModel):
    """
    Model inventory entry — describes a single model/provider combination.
    """

    model_config = {"populate_by_name": True, "protected_namespaces": ()}

    model_id: str = ""
    provider: str
    model_name: str
    capabilities: list[ModelCapability] = []
    is_local: bool = False
    endpoint: str | None = None
    context_length: int = 8192
    max_output: int = 4096
    priority: int = 1
    timeout_seconds: float = 60.0
    status: ModelStatus = ModelStatus.NOT_CONFIGURED
    metadata: dict[str, Any] = {}

    def is_available(self) -> bool:
        return self.status == ModelStatus.AVAILABLE

    def has_capability(self, cap: ModelCapability) -> bool:
        return cap in self.capabilities


class ModelResponse(BaseModel):
    """Response from a model inference call with real telemetry."""

    model_config = {"populate_by_name": True, "protected_namespaces": ()}

    success: bool
    output: Any = None
    error: str | None = None
    error_code: str | None = None
    provider: str = ""
    model_name: str = ""
    model_id: str = ""
    latency_ms: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    finish_reason: str | None = None
    metadata: dict[str, Any] = {}



class ModelProvider(ABC):
    """
    Abstract base for all model providers.

    Implementers must provide:
      - info()     : Return ModelInfo describing this provider.
      - ping()     : Check if the provider is reachable.
      - generate() : Run inference and return ModelResponse.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique provider name (used as registry key)."""

    @property
    @abstractmethod
    def capability(self) -> ModelCapability:
        """What kind of model this provider offers."""

    @abstractmethod
    def info(self) -> ModelInfo:
        """Return a ModelInfo describing this provider."""

    @abstractmethod
    def ping(self) -> ModelStatus:
        """Check if the provider is reachable. Returns ModelStatus."""

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> ModelResponse:
        """
        Run inference.

        Must return ModelResponse — never raise naked exceptions.
        If the provider is not configured, return:
            ModelResponse(success=False, error_code="MODEL_UNAVAILABLE")
        """

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, capability={self.capability.value})"

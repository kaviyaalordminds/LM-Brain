"""
Specialist Agent — Model Registry

Central registry for all model providers.
Agents request models by capability; the registry returns the first
available provider for that capability.

If no provider is available, resolve() returns None — the caller must
handle MODEL_UNAVAILABLE gracefully.
"""

from __future__ import annotations

import logging
from typing import Any

from specialist_agent.models.base import ModelCapability, ModelInfo, ModelProvider, ModelResponse, ModelStatus

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Registry for ModelProvider instances.

    Usage
    -----
    registry = ModelRegistry()
    registry.register(SomeProvider())
    provider = registry.resolve(ModelCapability.IMAGE_GENERATION)
    if provider is None:
        # Handle MODEL_UNAVAILABLE
    """

    def __init__(self) -> None:
        # capability → list of providers (in registration order)
        self._providers: dict[ModelCapability, list[ModelProvider]] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, provider: ModelProvider) -> None:
        """Register a model provider."""
        cap = provider.capability
        if cap not in self._providers:
            self._providers[cap] = []
        self._providers[cap].append(provider)
        logger.debug(
            "model.registered",
            extra={"provider": provider.name, "capability": cap.value},
        )

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

    def resolve(self, capability: ModelCapability) -> ModelProvider | None:
        """
        Return the first AVAILABLE provider for *capability*.

        Returns None if no provider is configured or all are unavailable.
        """
        for provider in self._providers.get(capability, []):
            try:
                status = provider.ping()
            except Exception:  # noqa: BLE001
                status = ModelStatus.UNAVAILABLE
            if status == ModelStatus.AVAILABLE:
                return provider
        return None

    def resolve_or_not_configured(
        self, capability: ModelCapability
    ) -> tuple[ModelProvider | None, ModelStatus]:
        """
        Resolve provider and return it along with its status.

        Returns (provider, AVAILABLE) or (None, NOT_CONFIGURED / UNAVAILABLE).
        """
        providers = self._providers.get(capability, [])
        if not providers:
            return None, ModelStatus.NOT_CONFIGURED

        for provider in providers:
            try:
                status = provider.ping()
            except Exception:  # noqa: BLE001
                status = ModelStatus.UNAVAILABLE
            if status == ModelStatus.AVAILABLE:
                return provider, ModelStatus.AVAILABLE

        return None, ModelStatus.UNAVAILABLE

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def inventory(self) -> list[ModelInfo]:
        """Return ModelInfo for every registered provider."""
        infos = []
        for providers in self._providers.values():
            for p in providers:
                try:
                    info = p.info()
                    try:
                        info.status = p.ping()
                    except Exception:  # noqa: BLE001
                        info.status = ModelStatus.UNAVAILABLE
                    infos.append(info)
                except Exception:  # noqa: BLE001
                    pass
        return infos

    def list_capabilities(self) -> list[str]:
        """Return all capability strings that have at least one provider."""
        return [cap.value for cap in self._providers]

    def has_capability(self, capability: ModelCapability) -> bool:
        """Return True if at least one provider is registered for *capability*."""
        return bool(self._providers.get(capability))

    def generate(
        self,
        capability: ModelCapability,
        prompt: str,
        **kwargs: Any,
    ) -> ModelResponse:
        """
        Convenience: resolve provider and generate in one call.

        Returns ModelResponse with error_code=MODEL_UNAVAILABLE if no
        provider is configured or available.
        """
        provider, status = self.resolve_or_not_configured(capability)
        if provider is None:
            reason = (
                "No provider configured for this capability."
                if status == ModelStatus.NOT_CONFIGURED
                else "All providers for this capability are currently unavailable."
            )
            return ModelResponse(
                success=False,
                error=f"MODEL_UNAVAILABLE: {reason}",
                error_code="MODEL_UNAVAILABLE",
                metadata={"capability": capability.value, "status": status.value},
            )
        return provider.generate(prompt, **kwargs)

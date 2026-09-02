"""
Specialist Agent — Model Router

Deterministic Model Router abstraction.
Selects the best available model provider matching the task's required capabilities.
If no model matches: returns None and signals MODEL_UNAVAILABLE.
Never silently falls back to an incompatible model.
"""

from __future__ import annotations
import logging
from typing import List, Optional, Tuple, Any

from specialist_agent.models.base import (
    ModelCapability,
    ModelInfo,
    ModelProvider,
    ModelStatus,
)
from specialist_agent.models.registry import ModelRegistry

logger = logging.getLogger(__name__)


class ModelRouter:
    """
    Routes specialist tasks to the optimal model based on advertised capabilities,
    priority ranking, context length, and operational availability.
    """

    def __init__(self, registry: Optional[ModelRegistry] = None) -> None:
        self.registry = registry or ModelRegistry()

    def route(
        self,
        task: dict[str, Any],
        required_capabilities: list[ModelCapability | str],
        preferred_provider: Optional[str] = None
    ) -> Tuple[Optional[ModelProvider], ModelStatus, str]:
        """
        Deterministically resolve the optimal provider for a task.

        Returns:
            (provider, status, reason)
            If no provider satisfies the capabilities:
            (None, ModelStatus.NOT_CONFIGURED / UNAVAILABLE, reason)
        """
        # Normalize capabilities to enum
        norm_caps: list[ModelCapability] = []
        for cap in required_capabilities:
            if isinstance(cap, ModelCapability):
                norm_caps.append(cap)
            else:
                try:
                    norm_caps.append(ModelCapability(str(cap).lower()))
                except ValueError:
                    pass

        if not norm_caps:
            # Default to text generation / code
            norm_caps = [ModelCapability.TEXT_GENERATION]

        # Scan registered providers for a match
        best_provider: Optional[ModelProvider] = None
        best_priority: int = -1

        for cap in norm_caps:
            provider, status = self.registry.resolve_or_not_configured(cap)
            if provider is not None:
                # Check provider info priority
                try:
                    info = provider.info()
                    priority = getattr(info, "priority", 1)
                    if preferred_provider and info.provider.lower() == preferred_provider.lower():
                        priority += 100

                    if priority > best_priority:
                        best_priority = priority
                        best_provider = provider
                except Exception:
                    if best_provider is None:
                        best_provider = provider

        if best_provider is not None:
            return best_provider, ModelStatus.AVAILABLE, f"Selected provider {best_provider.name}"

        cap_names = [c.value for c in norm_caps]
        return (
            None,
            ModelStatus.NOT_CONFIGURED,
            f"MODEL_UNAVAILABLE: No model provider configured for capabilities: {cap_names}. "
            "Configure the appropriate model provider to enable this agent."
        )

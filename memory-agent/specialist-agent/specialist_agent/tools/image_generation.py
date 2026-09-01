"""
Specialist Agent — Image Generation Tool

Interface for image generation model providers.

CRITICAL: If no image model provider is configured, this tool
MUST return MODEL_UNAVAILABLE — never a fake image.

No image is produced without a real, configured provider.
"""

from __future__ import annotations

import logging
from typing import Any

from specialist_agent.permissions.policy import Permission
from specialist_agent.tools.base import BaseTool, ToolCapability, ToolResult

logger = logging.getLogger(__name__)


class ImageGenerationTool(BaseTool):
    """
    Image generation tool.

    Delegates to a configured model provider (e.g. ComfyUI, DALL-E, Flux).
    If no provider is configured, returns MODEL_UNAVAILABLE immediately.
    """

    def __init__(
        self,
        provider_name: str | None = None,
        endpoint: str | None = None,
        model_name: str | None = None,
    ) -> None:
        self._provider = provider_name
        self._endpoint = endpoint
        self._model = model_name
        self._configured = bool(provider_name and endpoint)

    @property
    def name(self) -> str:
        return "image_generation"

    @property
    def capability(self) -> ToolCapability:
        return ToolCapability.IMAGE_GENERATION

    @property
    def description(self) -> str:
        return "Generate images from text prompts using a configured image model."

    @property
    def permission_level(self) -> str:
        return Permission.WRITE_ARTIFACT.value

    def execute(
        self,
        prompt: str = "",
        output_path: str = "",
        width: int = 512,
        height: int = 512,
        **kwargs: Any,
    ) -> ToolResult:
        """
        Generate an image from *prompt*.

        Returns MODEL_UNAVAILABLE if no provider is configured.
        Never fabricates an image artifact.
        """
        if not self._configured:
            logger.warning(
                "image_generation.model_unavailable",
                extra={"provider": self._provider, "endpoint": self._endpoint},
            )
            return ToolResult(
                success=False,
                error=(
                    "IMAGE MODEL NOT CONFIGURED — "
                    "set IMAGE_MODEL_PROVIDER, IMAGE_MODEL_NAME, and IMAGE_MODEL_ENDPOINT "
                    "to enable image generation."
                ),
                metadata={"error_code": "MODEL_UNAVAILABLE"},
            )

        if not prompt.strip():
            return ToolResult(success=False, error="'prompt' is required.")

        # Actual provider integration goes here when configured.
        # This stub returns a NOT_IMPLEMENTED error to indicate the provider
        # is registered but the integration code is pending.
        return ToolResult(
            success=False,
            error=(
                f"Image model provider '{self._provider}' is registered but "
                "integration is not yet implemented for this endpoint. "
                "Contact the team responsible for the provider integration."
            ),
            metadata={
                "error_code": "PROVIDER_NOT_INTEGRATED",
                "provider": self._provider,
                "endpoint": self._endpoint,
                "model": self._model,
            },
        )

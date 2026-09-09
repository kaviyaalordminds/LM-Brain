"""
Interfaces and abstract protocols for Controlled ASR / Audio Transcription Capability.
Ensures provider independence and prevents arbitrary command/shell execution.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from executive_twins.audio.models import ASRRequest, ASRResult


class IASRAdapter(ABC):
    """
    Abstract adapter for speech recognition engines (DEV/TEST, local models, etc.).
    Implementations MUST NOT expose shell commands, subprocesses, or arbitrary execution.
    """

    @property
    @abstractmethod
    def adapter_name(self) -> str:
        """Return the unique human-readable name of the ASR adapter."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the underlying speech engine or mock is available."""
        pass

    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Return the list of audio extensions/formats decodable by this adapter."""
        pass

    @abstractmethod
    def transcribe_audio(
        self, request: ASRRequest, resolved_path: Optional[str] = None
    ) -> ASRResult:
        """
        Execute speech recognition for the given request.
        Must return a structured ASRResult and never throw raw unhandled exceptions.
        """
        pass


class IASRService(ABC):
    """
    Controlled ASR Service Abstraction Interface.
    Enforces security validations, resource limits, and delegates to an authorized IASRAdapter.
    """

    @abstractmethod
    def transcribe(self, request: ASRRequest) -> ASRResult:
        """
        Perform verified, safe audio transcription within security and resource boundaries.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the service and its underlying adapter are operational."""
        pass

    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Return list of supported audio file formats."""
        pass

    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """Return list of supported language codes."""
        pass

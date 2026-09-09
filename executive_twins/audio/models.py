"""
Data models and schemas for Controlled ASR / Audio Transcription Capability.
Enforces strict typing, resource limits, and structured transcription status.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from executive_twins.schemas.common import FactItem
from executive_twins.schemas.evidence import ArtifactEvidence


class AudioFormat(str, Enum):
    WAV = ".wav"
    MP3 = ".mp3"
    M4A = ".m4a"
    FLAC = ".flac"
    OGG = ".ogg"

    @classmethod
    def is_supported(cls, extension_or_format: str) -> bool:
        normalized = extension_or_format.lower().strip()
        if not normalized.startswith("."):
            normalized = f".{normalized}"
        return normalized in [fmt.value for fmt in cls]

    @classmethod
    def normalize_extension(cls, extension_or_format: str) -> str:
        normalized = extension_or_format.lower().strip()
        if not normalized.startswith("."):
            normalized = f".{normalized}"
        return normalized


class AudioSourceType(str, Enum):
    WORKSPACE_FILE = "WORKSPACE_FILE"
    RAW_BYTES = "RAW_BYTES"
    REFERENCE = "REFERENCE"


class AudioInput(BaseModel):
    """
    Represents an audio input without exposing unrestricted host filesystem access.
    Local audio files must be resolved through the controlled workspace boundary.
    """
    audio_id: str
    source_type: AudioSourceType = AudioSourceType.WORKSPACE_FILE
    source_reference: str
    format: str
    language_hint: Optional[str] = None
    sample_rate: Optional[int] = None
    duration_seconds: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TranscriptSegment(BaseModel):
    """
    Represents an individual transcription segment with precise time boundaries.
    """
    start_time: float
    end_time: float
    text: str
    confidence: Optional[float] = None


class Transcript(BaseModel):
    """
    Represents the complete transcription result.
    """
    transcript_id: str
    text: str
    language: Optional[str] = None
    segments: List[TranscriptSegment] = Field(default_factory=list)
    duration_seconds: Optional[float] = None
    confidence: Optional[float] = None
    is_verified: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ASRRequest(BaseModel):
    """
    Explicit transcription request representation.
    """
    audio: AudioInput
    language_hint: Optional[str] = None
    include_timestamps: bool = True
    workspace_id: Optional[str] = None


class ASRStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    INVALID_INPUT = "INVALID_INPUT"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    NOT_AUTHORIZED = "NOT_AUTHORIZED"
    UNAVAILABLE = "UNAVAILABLE"
    TIMEOUT = "TIMEOUT"


class ASRResult(BaseModel):
    """
    Structured result of an ASR operation distinguishing success from failure.
    """
    status: ASRStatus
    transcript: Optional[Transcript] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    duration_seconds: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    facts: List[FactItem] = Field(default_factory=list)
    evidence: List[ArtifactEvidence] = Field(default_factory=list)


class ASRConfig(BaseModel):
    """
    Configurable operational limits and boundaries for ASR processing.
    """
    max_file_size_bytes: int = 50 * 1024 * 1024  # 50 MB
    max_duration_seconds: float = 3600.0  # 1 hour
    max_transcript_length: int = 100_000  # 100k characters
    max_processing_time_seconds: float = 30.0
    allowed_formats: List[str] = Field(
        default_factory=lambda: [".wav", ".mp3", ".m4a", ".flac", ".ogg"]
    )
    supported_languages: List[str] = Field(
        default_factory=lambda: ["en", "ta", "hi", "es", "fr", "de", "zh", "ja", "it", "pt", "ru", "ar"]
    )

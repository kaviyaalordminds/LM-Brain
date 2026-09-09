"""
Controlled ASR / Audio Transcription Capability package for Executive Twins.
Provides bounded, verified speech-to-text perception capabilities without unrestricted machine execution.
"""

from executive_twins.audio.asr_service import ASRService
from executive_twins.audio.dev_adapters import (
    ASRTranscriptionCapabilityHandler,
    DevTestASRAdapter,
    LocalASRAdapter,
)
from executive_twins.audio.interfaces import IASRAdapter, IASRService
from executive_twins.audio.models import (
    ASRConfig,
    ASRRequest,
    ASRResult,
    ASRStatus,
    AudioFormat,
    AudioInput,
    AudioSourceType,
    Transcript,
    TranscriptSegment,
)

__all__ = [
    "AudioFormat",
    "AudioSourceType",
    "AudioInput",
    "TranscriptSegment",
    "Transcript",
    "ASRRequest",
    "ASRStatus",
    "ASRResult",
    "ASRConfig",
    "IASRAdapter",
    "IASRService",
    "ASRService",
    "DevTestASRAdapter",
    "LocalASRAdapter",
    "ASRTranscriptionCapabilityHandler",
]

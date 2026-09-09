"""
Core Controlled ASR Service implementation.
Enforces strict security boundaries, format checks, resource limits, and audit logging.
"""

from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import List, Optional
import uuid

from executive_twins.audio.interfaces import IASRAdapter, IASRService
from executive_twins.audio.models import (
    ASRConfig,
    ASRRequest,
    ASRResult,
    ASRStatus,
    AudioFormat,
    AudioSourceType,
    Transcript,
)
from executive_twins.schemas.common import FactItem, FactState
from executive_twins.schemas.evidence import ArtifactEvidence
from executive_twins.utils.audit_logger import AuditLogger
from executive_twins.workspace.dev_adapters import DevTestWorkspaceAdapter
from executive_twins.workspace.local_workspace import PathSecurityException


class ASRService(IASRService):
    """
    Controlled Audio Transcription Service.
    Wraps an IASRAdapter and enforces:
    - No arbitrary host filesystem access or traversal
    - Format allowlist validation
    - Resource bounds (file size, duration, transcript length)
    - Audit logging without leaking sensitive raw audio bytes
    - Strict failure semantics and no raw exception leaks
    """

    def __init__(
        self,
        adapter: IASRAdapter,
        workspace_adapter: Optional[DevTestWorkspaceAdapter] = None,
        config: Optional[ASRConfig] = None,
    ) -> None:
        self.adapter = adapter
        self.workspace_adapter = workspace_adapter
        self.config = config or ASRConfig()

    def is_available(self) -> bool:
        return self.adapter.is_available()

    def get_supported_formats(self) -> List[str]:
        # Intersection of configured allowed formats and adapter-decodable formats
        adapter_formats = [f.lower() for f in self.adapter.get_supported_formats()]
        return [fmt for fmt in self.config.allowed_formats if fmt.lower() in adapter_formats]

    def get_supported_languages(self) -> List[str]:
        return list(self.config.supported_languages)

    def transcribe(self, request: ASRRequest) -> ASRResult:
        audio = request.audio
        audit_payload = {
            "audio_id": audio.audio_id,
            "source_type": audio.source_type.value if hasattr(audio.source_type, "value") else str(audio.source_type),
            "format": audio.format,
            "language_hint": request.language_hint or audio.language_hint,
            "adapter": self.adapter.adapter_name,
        }
        AuditLogger.log_event("asr.transcription.started", audit_payload)

        # 1. Validate Audio ID & Reference
        if not audio.audio_id or not audio.audio_id.strip():
            return self._build_failure_result(
                ASRStatus.INVALID_INPUT,
                "Audio ID cannot be empty.",
                "EMPTY_AUDIO_ID",
            )

        if not audio.source_reference or not audio.source_reference.strip():
            return self._build_failure_result(
                ASRStatus.INVALID_INPUT,
                "Source reference cannot be empty.",
                "EMPTY_SOURCE_REFERENCE",
            )

        # 2. Validate Audio Format
        norm_format = AudioFormat.normalize_extension(audio.format)
        if not AudioFormat.is_supported(norm_format) or norm_format not in self.config.allowed_formats:
            return self._build_failure_result(
                ASRStatus.UNSUPPORTED_FORMAT,
                f"Audio format '{audio.format}' is not in the allowed format list: {self.config.allowed_formats}.",
                "UNSUPPORTED_FORMAT",
            )

        adapter_supported = [AudioFormat.normalize_extension(f) for f in self.adapter.get_supported_formats()]
        if norm_format not in adapter_supported:
            return self._build_failure_result(
                ASRStatus.UNSUPPORTED_FORMAT,
                f"Audio format '{norm_format}' is not decodable by adapter '{self.adapter.adapter_name}'.",
                "ADAPTER_CANNOT_DECODE_FORMAT",
            )

        # 3. Validate Language Hint
        lang_hint = request.language_hint or audio.language_hint
        if lang_hint:
            norm_lang = lang_hint.strip().lower()
            if norm_lang not in [l.lower() for l in self.config.supported_languages]:
                return self._build_failure_result(
                    ASRStatus.INVALID_INPUT,
                    f"Unsupported language hint '{lang_hint}'. Supported languages: {self.config.supported_languages}.",
                    "UNSUPPORTED_LANGUAGE_HINT",
                )

        # 4. Validate Duration limit if specified
        if audio.duration_seconds is not None:
            if audio.duration_seconds < 0:
                return self._build_failure_result(
                    ASRStatus.INVALID_INPUT,
                    f"Audio duration cannot be negative: {audio.duration_seconds}.",
                    "INVALID_DURATION",
                )
            if audio.duration_seconds > self.config.max_duration_seconds:
                return self._build_failure_result(
                    ASRStatus.INVALID_INPUT,
                    f"Audio duration {audio.duration_seconds}s exceeds configured maximum of {self.config.max_duration_seconds}s.",
                    "EXCESSIVE_DURATION",
                )

        # 5. Workspace / Path Security Validation
        resolved_path: Optional[str] = None
        if audio.source_type == AudioSourceType.WORKSPACE_FILE:
            source_ref = audio.source_reference

            # Explicit check for path traversal components
            raw_path_obj = Path(source_ref)
            if ".." in raw_path_obj.parts or any(p == ".." for p in source_ref.replace("\\", "/").split("/")):
                AuditLogger.log_event(
                    "asr.security.blocked",
                    {"audio_id": audio.audio_id, "reason": f"Path traversal rejected: '{source_ref}'"},
                )
                return self._build_failure_result(
                    ASRStatus.NOT_AUTHORIZED,
                    f"Path traversal '..' is strictly rejected in '{source_ref}'.",
                    "PATH_TRAVERSAL_REJECTED",
                )

            # Rejection of outside absolute paths if no workspace provided
            if raw_path_obj.is_absolute() and not request.workspace_id:
                AuditLogger.log_event(
                    "asr.security.blocked",
                    {"audio_id": audio.audio_id, "reason": f"Arbitrary host path rejected: '{source_ref}'"},
                )
                return self._build_failure_result(
                    ASRStatus.NOT_AUTHORIZED,
                    f"Direct host absolute path '{source_ref}' is forbidden. Audio must be accessed via controlled workspace.",
                    "ARBITRARY_HOST_PATH_REJECTED",
                )

            if request.workspace_id and self.workspace_adapter:
                workspace = self.workspace_adapter.get_workspace(request.workspace_id)
                if not workspace or not workspace.workspace_exists():
                    return self._build_failure_result(
                        ASRStatus.INVALID_INPUT,
                        f"Workspace '{request.workspace_id}' not found or inactive.",
                        "WORKSPACE_NOT_FOUND",
                    )

                # Check path security via workspace
                try:
                    if hasattr(workspace, "_validate_and_resolve_path"):
                        target_file_path = workspace._validate_and_resolve_path(source_ref)
                    else:
                        target_file_path = Path(workspace.root_path) / source_ref
                except PathSecurityException as pse:
                    AuditLogger.log_event(
                        "asr.security.blocked",
                        {"audio_id": audio.audio_id, "reason": str(pse)},
                    )
                    return self._build_failure_result(
                        ASRStatus.NOT_AUTHORIZED,
                        f"Workspace security violation: {pse}",
                        "PATH_SECURITY_VIOLATION",
                    )

                # Verify file exists inside workspace
                if not target_file_path.exists():
                    return self._build_failure_result(
                        ASRStatus.INVALID_INPUT,
                        f"Target audio file '{source_ref}' does not exist in workspace '{request.workspace_id}'.",
                        "FILE_NOT_FOUND",
                    )

                # Reject directory
                if target_file_path.is_dir():
                    return self._build_failure_result(
                        ASRStatus.INVALID_INPUT,
                        f"Target path '{source_ref}' is a directory, not an audio file.",
                        "DIRECTORY_PASSED_AS_AUDIO",
                    )

                # Check file size bound
                try:
                    file_size = target_file_path.stat().st_size
                    if file_size > self.config.max_file_size_bytes:
                        return self._build_failure_result(
                            ASRStatus.INVALID_INPUT,
                            f"Audio file size ({file_size} bytes) exceeds limit of {self.config.max_file_size_bytes} bytes.",
                            "FILE_TOO_LARGE",
                        )
                except Exception as e:
                    return self._build_failure_result(
                        ASRStatus.FAILED,
                        f"Failed to inspect file size: {e}",
                        "FILE_STAT_ERROR",
                    )

                resolved_path = str(target_file_path)

        # 6. Adapter Availability Check
        if not self.adapter.is_available():
            AuditLogger.log_event(
                "asr.transcription.unavailable",
                {"adapter": self.adapter.adapter_name},
            )
            return self._build_failure_result(
                ASRStatus.UNAVAILABLE,
                f"ASR adapter '{self.adapter.adapter_name}' is currently unavailable.",
                "ASR_UNAVAILABLE",
            )

        # 7. Execute Transcription via Adapter
        try:
            adapter_result = self.adapter.transcribe_audio(request, resolved_path=resolved_path)
        except TimeoutError as te:
            AuditLogger.log_event(
                "asr.transcription.timeout",
                {"audio_id": audio.audio_id, "error": str(te)},
            )
            return self._build_failure_result(
                ASRStatus.TIMEOUT,
                f"Transcription timed out: {te}",
                "ASR_TIMEOUT",
            )
        except Exception as exc:
            AuditLogger.log_event(
                "asr.transcription.error",
                {"audio_id": audio.audio_id, "error": str(exc)},
            )
            return self._build_failure_result(
                ASRStatus.FAILED,
                f"Adapter execution error: {exc}",
                "ADAPTER_EXCEPTION",
            )

        if not isinstance(adapter_result, ASRResult):
            return self._build_failure_result(
                ASRStatus.FAILED,
                "Adapter returned invalid result type.",
                "MALFORMED_ADAPTER_RESULT",
            )

        # If adapter returned failure status directly
        if adapter_result.status != ASRStatus.SUCCESS:
            AuditLogger.log_event(
                "asr.transcription.failed",
                {
                    "audio_id": audio.audio_id,
                    "status": adapter_result.status.value,
                    "error": adapter_result.error_message,
                },
            )
            return adapter_result

        # 8. Post-Processing & Boundary Validation on Transcript
        transcript = adapter_result.transcript
        if transcript is None:
            return self._build_failure_result(
                ASRStatus.FAILED,
                "Transcription reported SUCCESS but returned no transcript object.",
                "EMPTY_TRANSCRIPT_OBJECT",
            )

        # Transcript length check
        if len(transcript.text) > self.config.max_transcript_length:
            return self._build_failure_result(
                ASRStatus.INVALID_INPUT,
                f"Transcript text length ({len(transcript.text)}) exceeds limit of {self.config.max_transcript_length}.",
                "EXCESSIVE_TRANSCRIPT_LENGTH",
            )

        # Handle timestamps flag
        if not request.include_timestamps and transcript.segments:
            # Caller explicitly requested no timestamps: strip segments
            transcript.segments = []

        # 9. Formulate Verified Facts
        facts = list(adapter_result.facts)
        lang_info = f" (language: '{transcript.language}')" if transcript.language else ""
        facts.append(
            FactItem(
                statement=f"Transcribed audio '{audio.audio_id}' via ASR adapter '{self.adapter.adapter_name}'{lang_info}.",
                state=FactState.FACT,
                source=f"asr_service:{self.adapter.adapter_name}",
            )
        )

        AuditLogger.log_event(
            "asr.transcription.completed",
            {
                "audio_id": audio.audio_id,
                "transcript_id": transcript.transcript_id,
                "length": len(transcript.text),
                "segments_count": len(transcript.segments),
            },
        )

        return ASRResult(
            status=ASRStatus.SUCCESS,
            transcript=transcript,
            duration_seconds=adapter_result.duration_seconds or audio.duration_seconds,
            metadata={
                **adapter_result.metadata,
                "adapter": self.adapter.adapter_name,
                "include_timestamps": request.include_timestamps,
                "caller_language_hint": lang_hint,
            },
            facts=facts,
            evidence=adapter_result.evidence,
        )

    def _build_failure_result(
        self,
        status: ASRStatus,
        error_message: str,
        error_type: str,
    ) -> ASRResult:
        return ASRResult(
            status=status,
            transcript=None,
            error_message=error_message,
            error_type=error_type,
            facts=[
                FactItem(
                    statement=f"ASR transcription failed: [{error_type}] {error_message}",
                    state=FactState.FACT,
                    source=f"asr_service:{self.adapter.adapter_name}",
                )
            ],
            evidence=[],
        )

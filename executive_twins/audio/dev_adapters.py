"""
DEV/TEST deterministic adapters and registered ASR capability execution handlers.
Used for deterministic testing and specialist execution without external cloud APIs.
"""

from typing import Any, Dict, List, Optional
import uuid

from executive_twins.audio.interfaces import IASRAdapter, IASRService
from executive_twins.audio.models import (
    ASRRequest,
    ASRResult,
    ASRStatus,
    AudioFormat,
    AudioInput,
    AudioSourceType,
    Transcript,
    TranscriptSegment,
)
from executive_twins.execution.capability_execution_engine import (
    BaseCapabilityHandler,
    CapabilityHandlerOutput,
)
from executive_twins.schemas.common import FactItem, FactState
from executive_twins.schemas.delegation import DelegationRequest
from executive_twins.schemas.specialist import SpecialistMetadata


class DevTestASRAdapter(IASRAdapter):
    """
    DEV_TEST_ONLY_ADAPTER: Deterministic local ASR adapter for development and testing.
    THIS IS NOT REAL SPEECH MODEL INFERENCE.
    Allows deterministic verification of speech workflows without GPU, microphones, or network calls.
    """

    def __init__(
        self,
        is_available_flag: bool = True,
        supported_formats: Optional[List[str]] = None,
    ) -> None:
        self._is_available = is_available_flag
        self._supported_formats = supported_formats or [".wav", ".mp3", ".m4a", ".flac", ".ogg"]
        self.custom_transcripts: Dict[str, Transcript] = {}
        self.custom_results: Dict[str, ASRResult] = {}
        self.simulate_timeout: bool = False
        self.simulate_error: Optional[str] = None
        self.simulate_no_timestamps: bool = False

        # Pre-seed realistic deterministic test transcripts
        self._seed_default_transcripts()

    @property
    def adapter_name(self) -> str:
        return "DevTestASRAdapter"

    def is_available(self) -> bool:
        return self._is_available

    def set_available(self, available: bool) -> None:
        self._is_available = available

    def get_supported_formats(self) -> List[str]:
        return list(self._supported_formats)

    def register_transcript(self, audio_id_or_ref: str, transcript: Transcript) -> None:
        self.custom_transcripts[audio_id_or_ref] = transcript

    def register_result(self, audio_id_or_ref: str, result: ASRResult) -> None:
        self.custom_results[audio_id_or_ref] = result

    def _seed_default_transcripts(self) -> None:
        # Standard English transcript
        self.custom_transcripts["audio_en_sample"] = Transcript(
            transcript_id="tr-en-sample-001",
            text="Welcome to the executive digital workforce platform. All systems operational.",
            language="en",
            duration_seconds=4.5,
            confidence=0.98,
            is_verified=True,
            segments=[
                TranscriptSegment(
                    start_time=0.0,
                    end_time=2.3,
                    text="Welcome to the executive digital workforce platform.",
                    confidence=0.99,
                ),
                TranscriptSegment(
                    start_time=2.4,
                    end_time=4.5,
                    text="All systems operational.",
                    confidence=0.97,
                ),
            ],
            metadata={"adapter": "DevTestASRAdapter", "test_fixture": True},
        )

        # Multilingual: Tamil sample
        self.custom_transcripts["audio_ta_sample"] = Transcript(
            transcript_id="tr-ta-sample-002",
            text="வணக்கம், நிர்வாக டிஜிட்டல் தளத்திற்கு நல்வரவு.",
            language="ta",
            duration_seconds=3.2,
            confidence=0.95,
            is_verified=True,
            segments=[
                TranscriptSegment(
                    start_time=0.0,
                    end_time=3.2,
                    text="வணக்கம், நிர்வாக டிஜிட்டல் தளத்திற்கு நல்வரவு.",
                    confidence=0.95,
                )
            ],
            metadata={"adapter": "DevTestASRAdapter", "test_fixture": True},
        )

        # Multilingual: Hindi sample
        self.custom_transcripts["audio_hi_sample"] = Transcript(
            transcript_id="tr-hi-sample-003",
            text="नमस्ते, कार्यकारी डिजिटल वर्कफ़्लो में आपका स्वागत है।",
            language="hi",
            duration_seconds=3.8,
            confidence=0.96,
            is_verified=True,
            segments=[
                TranscriptSegment(
                    start_time=0.0,
                    end_time=3.8,
                    text="नमस्ते, कार्यकारी डिजिटल वर्कफ़्लो में आपका स्वागत है।",
                    confidence=0.96,
                )
            ],
            metadata={"adapter": "DevTestASRAdapter", "test_fixture": True},
        )

        # Empty audio transcript
        self.custom_transcripts["audio_empty_sample"] = Transcript(
            transcript_id="tr-empty-004",
            text="",
            language="en",
            duration_seconds=1.0,
            confidence=1.0,
            is_verified=True,
            segments=[],
            metadata={"adapter": "DevTestASRAdapter", "test_fixture": True},
        )

    def transcribe_audio(
        self, request: ASRRequest, resolved_path: Optional[str] = None
    ) -> ASRResult:
        if self.simulate_timeout:
            raise TimeoutError("Simulated transcription timeout in DevTestASRAdapter.")

        if self.simulate_error:
            raise RuntimeError(f"Simulated adapter failure: {self.simulate_error}")

        audio_key = request.audio.audio_id
        ref_key = request.audio.source_reference

        # Check explicit custom result override
        if audio_key in self.custom_results:
            return self.custom_results[audio_key]
        if ref_key in self.custom_results:
            return self.custom_results[ref_key]

        # Check explicit custom transcript
        if audio_key in self.custom_transcripts:
            transcript = self.custom_transcripts[audio_key].model_copy(deep=True)
        elif ref_key in self.custom_transcripts:
            transcript = self.custom_transcripts[ref_key].model_copy(deep=True)
        else:
            # Generate deterministic transcript based on input reference
            lang = request.language_hint or request.audio.language_hint or "en"
            text = f"Deterministic speech transcript for audio '{request.audio.audio_id}'."
            segments = []
            if not self.simulate_no_timestamps and request.include_timestamps:
                segments = [
                    TranscriptSegment(
                        start_time=0.0,
                        end_time=request.audio.duration_seconds or 2.0,
                        text=text,
                        confidence=0.95,
                    )
                ]

            transcript = Transcript(
                transcript_id=f"tr-det-{uuid.uuid4().hex[:8]}",
                text=text,
                language=lang,
                duration_seconds=request.audio.duration_seconds or 2.0,
                confidence=0.95,
                segments=segments,
                is_verified=True,
                metadata={"adapter": "DevTestASRAdapter", "is_real_inference": False},
            )

        # If simulate_no_timestamps is enabled, strip segments
        if self.simulate_no_timestamps:
            transcript.segments = []

        return ASRResult(
            status=ASRStatus.SUCCESS,
            transcript=transcript,
            duration_seconds=transcript.duration_seconds or request.audio.duration_seconds,
            metadata={"adapter": self.adapter_name, "is_dev_test": True},
            facts=[
                FactItem(
                    statement=f"DevTestASRAdapter generated deterministic transcript '{transcript.transcript_id}'.",
                    state=FactState.FACT,
                    source="DevTestASRAdapter",
                )
            ],
            evidence=[],
        )


class LocalASRAdapter(IASRAdapter):
    """
    Optional Local ASR Adapter for Whisper models if available in the local environment.
    Will NEVER automatically download models or fail deterministic test runs.
    """

    def __init__(self, model_instance: Optional[Any] = None) -> None:
        self._model = model_instance
        self._is_whisper_available = False
        try:
            import whisper  # type: ignore # noqa: F401
            self._is_whisper_available = True
        except ImportError:
            self._is_whisper_available = False

    @property
    def adapter_name(self) -> str:
        return "LocalWhisperASRAdapter"

    def is_available(self) -> bool:
        return self._is_whisper_available and (self._model is not None)

    def get_supported_formats(self) -> List[str]:
        return [".wav", ".mp3", ".m4a", ".flac", ".ogg"]

    def transcribe_audio(
        self, request: ASRRequest, resolved_path: Optional[str] = None
    ) -> ASRResult:
        if not self.is_available():
            return ASRResult(
                status=ASRStatus.UNAVAILABLE,
                error_message="Local Whisper model is not loaded or whisper library is unavailable.",
                error_type="LOCAL_MODEL_UNAVAILABLE",
            )

        if not resolved_path:
            return ASRResult(
                status=ASRStatus.INVALID_INPUT,
                error_message="LocalWhisperASRAdapter requires a resolved physical audio file path.",
                error_type="MISSING_RESOLVED_PATH",
            )

        try:
            # Execute actual Whisper inference on resolved path
            audio_options = {}
            if request.language_hint:
                audio_options["language"] = request.language_hint

            res = self._model.transcribe(resolved_path, **audio_options)
            text = res.get("text", "").strip()
            language = res.get("language", request.language_hint or "en")

            segments = []
            if request.include_timestamps and "segments" in res:
                for seg in res["segments"]:
                    segments.append(
                        TranscriptSegment(
                            start_time=float(seg.get("start", 0.0)),
                            end_time=float(seg.get("end", 0.0)),
                            text=str(seg.get("text", "")).strip(),
                            confidence=None,  # Whisper doesn't output normalized segment confidence by default
                        )
                    )

            transcript = Transcript(
                transcript_id=f"tr-whisper-{uuid.uuid4().hex[:8]}",
                text=text,
                language=language,
                segments=segments,
                duration_seconds=request.audio.duration_seconds,
                is_verified=True,
                metadata={"adapter": self.adapter_name, "is_real_inference": True},
            )

            return ASRResult(
                status=ASRStatus.SUCCESS,
                transcript=transcript,
                duration_seconds=request.audio.duration_seconds,
                metadata={"adapter": self.adapter_name, "detected_language": language},
                facts=[
                    FactItem(
                        statement=f"Local Whisper transcribed audio from '{resolved_path}' with detected language '{language}'.",
                        state=FactState.FACT,
                        source="LocalWhisperASRAdapter",
                    )
                ],
            )
        except Exception as e:
            return ASRResult(
                status=ASRStatus.FAILED,
                error_message=f"Local Whisper inference failed: {e}",
                error_type="LOCAL_INFERENCE_ERROR",
            )


class ASRTranscriptionCapabilityHandler(BaseCapabilityHandler):
    """
    Approved Capability Execution Handler for Automatic Speech Recognition (ASR).
    EXECUTION SAFETY: Registered within SpecialistExecutionEngine boundary.
    Does NOT execute arbitrary shell or system code. Invokes controlled IASRService.
    """

    capability_name = "audio_transcription"
    required_tool = "asr_engine"
    required_params = ["audio_id", "source_reference"]
    allowed_params = [
        "audio",
        "audio_id",
        "source_reference",
        "source_type",
        "format",
        "language_hint",
        "sample_rate",
        "duration_seconds",
        "metadata",
        "include_timestamps",
        "workspace_id",
        "strict_mode",
    ]

    def __init__(self, asr_service: IASRService) -> None:
        self.asr_service = asr_service

    def validate_parameters(self, inputs: Dict[str, Any]) -> Optional[str]:
        if "audio" in inputs and isinstance(inputs["audio"], (dict, AudioInput)):
            return None
        # Otherwise require audio_id and source_reference
        for param in self.required_params:
            if param not in inputs or inputs[param] is None:
                return f"Missing required parameter '{param}' for capability '{self.capability_name}'."
        return None

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        inputs = request.inputs

        # Construct AudioInput
        if "audio" in inputs and isinstance(inputs["audio"], dict):
            try:
                audio_input = AudioInput(**inputs["audio"])
            except Exception as e:
                return CapabilityHandlerOutput(
                    success=False,
                    output_text=f"ASR_INPUT_ERROR: Invalid AudioInput schema: {e}",
                    errors=[f"Invalid AudioInput: {e}"],
                )
        elif "audio" in inputs and isinstance(inputs["audio"], AudioInput):
            audio_input = inputs["audio"]
        else:
            audio_id = str(inputs.get("audio_id", ""))
            source_reference = str(inputs.get("source_reference", ""))
            format_str = str(inputs.get("format", ".wav"))
            source_type_val = inputs.get("source_type", AudioSourceType.WORKSPACE_FILE)
            if isinstance(source_type_val, str):
                try:
                    source_type = AudioSourceType(source_type_val)
                except ValueError:
                    source_type = AudioSourceType.WORKSPACE_FILE
            else:
                source_type = source_type_val

            language_hint = inputs.get("language_hint")
            sample_rate = inputs.get("sample_rate")
            duration_seconds = inputs.get("duration_seconds")
            metadata = inputs.get("metadata", {})

            audio_input = AudioInput(
                audio_id=audio_id,
                source_type=source_type,
                source_reference=source_reference,
                format=format_str,
                language_hint=language_hint,
                sample_rate=sample_rate,
                duration_seconds=duration_seconds,
                metadata=metadata,
            )

        # Construct ASRRequest
        include_timestamps = inputs.get("include_timestamps", True)
        language_hint_req = inputs.get("language_hint") or audio_input.language_hint
        workspace_id = inputs.get("workspace_id")

        asr_request = ASRRequest(
            audio=audio_input,
            language_hint=language_hint_req,
            include_timestamps=include_timestamps,
            workspace_id=workspace_id,
        )

        # Invoke ASR Service
        result: ASRResult = self.asr_service.transcribe(asr_request)

        if result.status != ASRStatus.SUCCESS or result.transcript is None:
            err_msg = result.error_message or f"ASR transcription status: {result.status.value}"
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"ASR_TRANSCRIPTION_FAILED: [{result.status.value}] {err_msg}",
                facts=result.facts,
                errors=[f"ASR_TRANSCRIPTION_FAILED: {err_msg}"],
                has_unknowns_or_assumptions=False,
            )

        transcript = result.transcript
        facts = list(result.facts)
        facts.append(
            FactItem(
                statement=f"ASR specialist '{specialist.specialist_id}' successfully transcribed audio '{audio_input.audio_id}'.",
                state=FactState.FACT,
                source=f"specialist:{specialist.specialist_id}",
            )
        )

        return CapabilityHandlerOutput(
            success=True,
            output_text=f"ASR transcription succeeded for audio '{audio_input.audio_id}'. Transcript: '{transcript.text}'",
            facts=facts,
            artifacts=[],
            errors=[],
            additional_evidence=result.evidence,
        )

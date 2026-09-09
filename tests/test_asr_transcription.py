"""
Comprehensive focused test suite for Controlled ASR / Audio Transcription Capability.
Covers:
- Model validation
- Input validation & workspace boundaries
- Deterministic transcription
- Multilingual & timestamp handling
- Failure semantics & exception safety
- Security & authorization boundaries
- SpecialistExecutionEngine & EvidenceSet integration
- Audit logging & fact verification
- Optional Local ASR integration
"""

from datetime import datetime, timezone
import os
from pathlib import Path
import tempfile
from typing import Optional
import pytest

from executive_twins.audio.asr_service import ASRService
from executive_twins.audio.dev_adapters import (
    ASRTranscriptionCapabilityHandler,
    DevTestASRAdapter,
    LocalASRAdapter,
)
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
from executive_twins.client.registry_client import InMemorySpecialistRegistryAdapter
from executive_twins.execution.capability_execution_engine import (
    SpecialistExecutionAdapter,
    SpecialistExecutionEngine,
)
from executive_twins.execution.security_guard import SecurityGuard
from executive_twins.registry.capability_matcher import CapabilityMatcher
from executive_twins.schemas.common import (
    FactItem,
    FactState,
    FailureState,
    SecurityContext,
    SpecialistStatus,
    VerificationStatus,
)
from executive_twins.schemas.delegation import DelegationRequest, DelegationResult
from executive_twins.schemas.evidence import EvidenceCategory
from executive_twins.schemas.specialist import (
    Capability,
    CapabilityRequirement,
    SpecialistMetadata,
)
from executive_twins.utils.audit_logger import AuditLogger
from executive_twins.workspace.dev_adapters import DevTestWorkspaceAdapter


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_workspace_env():
    with tempfile.TemporaryDirectory() as tmp_dir:
        ws_adapter = DevTestWorkspaceAdapter(temp_workspace_dir=tmp_dir)
        ws = ws_adapter.create_workspace("ws-asr-001")
        yield ws_adapter, ws, tmp_dir
        ws_adapter.close_all(cleanup=True)


@pytest.fixture
def asr_fixture(temp_workspace_env):
    ws_adapter, ws, tmp_dir = temp_workspace_env
    dev_adapter = DevTestASRAdapter()
    config = ASRConfig(
        max_file_size_bytes=1024 * 1024,  # 1 MB for testing
        max_duration_seconds=300.0,       # 5 minutes for testing
        max_transcript_length=5000,
    )
    service = ASRService(adapter=dev_adapter, workspace_adapter=ws_adapter, config=config)
    return service, dev_adapter, ws_adapter, ws, config


@pytest.fixture
def specialist_registry_env(asr_fixture):
    service, dev_adapter, ws_adapter, ws, config = asr_fixture
    registry = InMemorySpecialistRegistryAdapter()

    # Active, authorized specialist
    active_specialist = SpecialistMetadata(
        specialist_id="spec-asr-01",
        name="Audio Transcription Specialist",
        capabilities=[
            Capability(
                name="audio_transcription",
                description="Converts audio recordings into structured text transcripts.",
                required_tools=["asr_engine"],
            )
        ],
        status=SpecialistStatus.ACTIVE,
        authorized_tools=["asr_engine"],
        security_level="standard",
    )
    registry.register_specialist(active_specialist)

    # Inactive specialist
    inactive_specialist = SpecialistMetadata(
        specialist_id="spec-asr-inactive",
        name="Inactive ASR Specialist",
        capabilities=[
            Capability(
                name="audio_transcription",
                description="Inactive transcription capability.",
                required_tools=["asr_engine"],
            )
        ],
        status=SpecialistStatus.INACTIVE,
        authorized_tools=["asr_engine"],
    )
    registry.register_specialist(inactive_specialist)

    # Unauthorized tool specialist
    unauthorized_specialist = SpecialistMetadata(
        specialist_id="spec-asr-no-auth",
        name="Unauthorized Specialist",
        capabilities=[
            Capability(
                name="audio_transcription",
                description="Lacks required tool authorization.",
                required_tools=["asr_engine"],
            )
        ],
        status=SpecialistStatus.ACTIVE,
        authorized_tools=["unrelated_tool"],
    )
    registry.register_specialist(unauthorized_specialist)

    # Setup execution engine
    engine = SpecialistExecutionEngine(registry_client=registry)
    handler = ASRTranscriptionCapabilityHandler(asr_service=service)
    engine.register_handler(handler)

    return engine, registry, service, ws, active_specialist


# ============================================================================
# 1. MODEL VALIDATION TESTS (1-8)
# ============================================================================

def test_01_audio_input_valid_construction():
    audio = AudioInput(
        audio_id="aud-001",
        source_type=AudioSourceType.WORKSPACE_FILE,
        source_reference="recordings/meeting.wav",
        format=".wav",
        language_hint="en",
        sample_rate=16000,
        duration_seconds=12.5,
    )
    assert audio.audio_id == "aud-001"
    assert audio.format == ".wav"
    assert audio.language_hint == "en"
    assert audio.duration_seconds == 12.5


def test_02_audio_format_normalization_and_validation():
    assert AudioFormat.is_supported("wav")
    assert AudioFormat.is_supported(".mp3")
    assert AudioFormat.is_supported("FLAC")
    assert not AudioFormat.is_supported("exe")
    assert not AudioFormat.is_supported(".txt")

    assert AudioFormat.normalize_extension("wav") == ".wav"
    assert AudioFormat.normalize_extension(".MP3") == ".mp3"


def test_03_transcript_segment_attributes():
    segment = TranscriptSegment(
        start_time=1.2,
        end_time=3.4,
        text="Recognized phrase.",
        confidence=0.96,
    )
    assert segment.start_time == 1.2
    assert segment.end_time == 3.4
    assert segment.text == "Recognized phrase."
    assert segment.confidence == 0.96


def test_04_transcript_attributes_and_defaults():
    tr = Transcript(
        transcript_id="tr-100",
        text="Complete transcribed speech.",
        language="en",
        duration_seconds=5.0,
        confidence=0.99,
        is_verified=True,
    )
    assert tr.transcript_id == "tr-100"
    assert tr.segments == []
    assert tr.is_verified is True


def test_05_asr_request_defaults_and_options():
    audio = AudioInput(
        audio_id="aud-002",
        source_reference="audio.mp3",
        format=".mp3",
    )
    req = ASRRequest(audio=audio, include_timestamps=False, language_hint="ta")
    assert req.include_timestamps is False
    assert req.language_hint == "ta"
    assert req.workspace_id is None


def test_06_asr_status_enum_values():
    assert ASRStatus.SUCCESS.value == "SUCCESS"
    assert ASRStatus.FAILED.value == "FAILED"
    assert ASRStatus.INVALID_INPUT.value == "INVALID_INPUT"
    assert ASRStatus.UNSUPPORTED_FORMAT.value == "UNSUPPORTED_FORMAT"
    assert ASRStatus.NOT_AUTHORIZED.value == "NOT_AUTHORIZED"
    assert ASRStatus.UNAVAILABLE.value == "UNAVAILABLE"
    assert ASRStatus.TIMEOUT.value == "TIMEOUT"


def test_07_asr_result_structured_payload():
    result = ASRResult(
        status=ASRStatus.SUCCESS,
        transcript=Transcript(transcript_id="tr-1", text="test", language="en"),
        duration_seconds=2.0,
        metadata={"source": "test"},
    )
    assert result.status == ASRStatus.SUCCESS
    assert result.transcript is not None
    assert result.transcript.text == "test"


def test_08_asr_config_limits_defaults():
    config = ASRConfig()
    assert config.max_file_size_bytes == 50 * 1024 * 1024
    assert config.max_duration_seconds == 3600.0
    assert config.max_transcript_length == 100000
    assert ".wav" in config.allowed_formats
    assert "en" in config.supported_languages


# ============================================================================
# 2. INPUT VALIDATION & WORKSPACE SECURITY TESTS (9-18)
# ============================================================================

def test_09_valid_workspace_audio_file(asr_fixture):
    service, dev_adapter, ws_adapter, ws, config = asr_fixture
    ws.write_file("test_audio.wav", "DUMMY_AUDIO_DATA")

    audio = AudioInput(
        audio_id="aud-valid-01",
        source_reference="test_audio.wav",
        format=".wav",
    )
    req = ASRRequest(audio=audio, workspace_id=ws.workspace_id)
    result = service.transcribe(req)
    assert result.status == ASRStatus.SUCCESS
    assert result.transcript is not None


def test_10_empty_audio_id_rejected(asr_fixture):
    service, _, _, _, _ = asr_fixture
    audio = AudioInput(
        audio_id="   ",
        source_reference="audio.wav",
        format=".wav",
    )
    req = ASRRequest(audio=audio)
    result = service.transcribe(req)
    assert result.status == ASRStatus.INVALID_INPUT
    assert "EMPTY_AUDIO_ID" in (result.error_type or "")


def test_11_empty_source_reference_rejected(asr_fixture):
    service, _, _, _, _ = asr_fixture
    audio = AudioInput(
        audio_id="aud-01",
        source_reference="",
        format=".wav",
    )
    req = ASRRequest(audio=audio)
    result = service.transcribe(req)
    assert result.status == ASRStatus.INVALID_INPUT
    assert "EMPTY_SOURCE_REFERENCE" in (result.error_type or "")


def test_12_nonexistent_workspace_file_rejected(asr_fixture):
    service, _, ws_adapter, ws, _ = asr_fixture
    audio = AudioInput(
        audio_id="aud-missing",
        source_reference="missing_file.wav",
        format=".wav",
    )
    req = ASRRequest(audio=audio, workspace_id=ws.workspace_id)
    result = service.transcribe(req)
    assert result.status == ASRStatus.INVALID_INPUT
    assert "FILE_NOT_FOUND" in (result.error_type or "")


def test_13_directory_passed_as_audio_rejected(asr_fixture):
    service, _, ws_adapter, ws, _ = asr_fixture
    # Create directory inside workspace
    sub_dir = Path(ws.root_path) / "audio_dir.wav"
    sub_dir.mkdir(parents=True, exist_ok=True)

    audio = AudioInput(
        audio_id="aud-dir",
        source_reference="audio_dir.wav",
        format=".wav",
    )
    req = ASRRequest(audio=audio, workspace_id=ws.workspace_id)
    result = service.transcribe(req)
    assert result.status == ASRStatus.INVALID_INPUT
    assert "DIRECTORY_PASSED_AS_AUDIO" in (result.error_type or "")


def test_14_unsupported_audio_format_rejected(asr_fixture):
    service, _, _, _, _ = asr_fixture
    audio = AudioInput(
        audio_id="aud-unsupp",
        source_reference="malicious.exe",
        format=".exe",
    )
    req = ASRRequest(audio=audio)
    result = service.transcribe(req)
    assert result.status == ASRStatus.UNSUPPORTED_FORMAT
    assert "UNSUPPORTED_FORMAT" in (result.error_type or "")


def test_15_parent_directory_traversal_rejected(asr_fixture):
    service, _, _, ws, _ = asr_fixture
    audio = AudioInput(
        audio_id="aud-traversal",
        source_reference="../../secret_audio.wav",
        format=".wav",
    )
    req = ASRRequest(audio=audio, workspace_id=ws.workspace_id)
    result = service.transcribe(req)
    assert result.status == ASRStatus.NOT_AUTHORIZED
    assert "PATH_TRAVERSAL_REJECTED" in (result.error_type or "")


def test_16_arbitrary_outside_absolute_path_rejected(asr_fixture):
    service, _, _, _, _ = asr_fixture
    outside_path = "C:/Windows/System32/config/audio.wav" if os.name == "nt" else "/etc/shadow/audio.wav"
    audio = AudioInput(
        audio_id="aud-outside",
        source_reference=outside_path,
        format=".wav",
    )
    req = ASRRequest(audio=audio)
    result = service.transcribe(req)
    assert result.status == ASRStatus.NOT_AUTHORIZED
    assert "ARBITRARY_HOST_PATH_REJECTED" in (result.error_type or "")


def test_17_oversized_audio_file_rejected(asr_fixture):
    service, _, _, ws, config = asr_fixture
    # Create file exceeding 1MB config limit
    large_content = "X" * (config.max_file_size_bytes + 1024)
    ws.write_file("large_audio.wav", large_content)

    audio = AudioInput(
        audio_id="aud-large",
        source_reference="large_audio.wav",
        format=".wav",
    )
    req = ASRRequest(audio=audio, workspace_id=ws.workspace_id)
    result = service.transcribe(req)
    assert result.status == ASRStatus.INVALID_INPUT
    assert "FILE_TOO_LARGE" in (result.error_type or "")


def test_18_excessive_duration_rejected(asr_fixture):
    service, _, _, _, config = asr_fixture
    audio = AudioInput(
        audio_id="aud-long",
        source_reference="long_recording.wav",
        format=".wav",
        duration_seconds=config.max_duration_seconds + 50.0,
    )
    req = ASRRequest(audio=audio)
    result = service.transcribe(req)
    assert result.status == ASRStatus.INVALID_INPUT
    assert "EXCESSIVE_DURATION" in (result.error_type or "")


# ============================================================================
# 3. TRANSCRIPTION & MULTILINGUAL TESTS (19-26)
# ============================================================================

def test_19_deterministic_english_transcription(asr_fixture):
    service, _, _, _, _ = asr_fixture
    audio = AudioInput(
        audio_id="audio_en_sample",
        source_reference="audio_en_sample.wav",
        format=".wav",
    )
    req = ASRRequest(audio=audio)
    result = service.transcribe(req)
    assert result.status == ASRStatus.SUCCESS
    assert result.transcript is not None
    assert "executive digital workforce" in result.transcript.text
    assert result.transcript.language == "en"
    assert len(result.transcript.segments) == 2


def test_20_deterministic_tamil_multilingual_transcription(asr_fixture):
    service, _, _, _, _ = asr_fixture
    audio = AudioInput(
        audio_id="audio_ta_sample",
        source_reference="audio_ta_sample.wav",
        format=".wav",
        language_hint="ta",
    )
    req = ASRRequest(audio=audio, language_hint="ta")
    result = service.transcribe(req)
    assert result.status == ASRStatus.SUCCESS
    assert result.transcript is not None
    assert result.transcript.language == "ta"
    assert "வணக்கம்" in result.transcript.text


def test_21_deterministic_hindi_multilingual_transcription(asr_fixture):
    service, _, _, _, _ = asr_fixture
    audio = AudioInput(
        audio_id="audio_hi_sample",
        source_reference="audio_hi_sample.wav",
        format=".wav",
        language_hint="hi",
    )
    req = ASRRequest(audio=audio, language_hint="hi")
    result = service.transcribe(req)
    assert result.status == ASRStatus.SUCCESS
    assert result.transcript is not None
    assert result.transcript.language == "hi"
    assert "नमस्ते" in result.transcript.text


def test_22_empty_transcript_handling(asr_fixture):
    service, _, _, _, _ = asr_fixture
    audio = AudioInput(
        audio_id="audio_empty_sample",
        source_reference="silent.wav",
        format=".wav",
    )
    req = ASRRequest(audio=audio)
    result = service.transcribe(req)
    assert result.status == ASRStatus.SUCCESS
    assert result.transcript is not None
    assert result.transcript.text == ""
    assert result.transcript.segments == []


def test_23_timestamps_enabled_includes_segments(asr_fixture):
    service, _, _, _, _ = asr_fixture
    audio = AudioInput(
        audio_id="audio_en_sample",
        source_reference="meeting.wav",
        format=".wav",
    )
    req = ASRRequest(audio=audio, include_timestamps=True)
    result = service.transcribe(req)
    assert result.status == ASRStatus.SUCCESS
    assert len(result.transcript.segments) > 0
    assert result.transcript.segments[0].start_time == 0.0


def test_24_timestamps_disabled_strips_segments(asr_fixture):
    service, _, _, _, _ = asr_fixture
    audio = AudioInput(
        audio_id="audio_en_sample",
        source_reference="meeting.wav",
        format=".wav",
    )
    req = ASRRequest(audio=audio, include_timestamps=False)
    result = service.transcribe(req)
    assert result.status == ASRStatus.SUCCESS
    assert result.transcript.segments == []
    assert "Welcome" in result.transcript.text


def test_25_timestamps_unavailable_does_not_fabricate(asr_fixture):
    service, dev_adapter, _, _, _ = asr_fixture
    dev_adapter.simulate_no_timestamps = True

    audio = AudioInput(
        audio_id="aud-no-ts",
        source_reference="recording.wav",
        format=".wav",
    )
    req = ASRRequest(audio=audio, include_timestamps=True)
    result = service.transcribe(req)
    assert result.status == ASRStatus.SUCCESS
    # Adapter does not fabricate timestamps: segments remain empty
    assert result.transcript.segments == []


def test_26_unsupported_language_hint_rejected(asr_fixture):
    service, _, _, _, _ = asr_fixture
    audio = AudioInput(
        audio_id="aud-lang",
        source_reference="audio.wav",
        format=".wav",
    )
    req = ASRRequest(audio=audio, language_hint="klingon_unsupported")
    result = service.transcribe(req)
    assert result.status == ASRStatus.INVALID_INPUT
    assert "UNSUPPORTED_LANGUAGE_HINT" in (result.error_type or "")


# ============================================================================
# 4. FAILURE SEMANTICS & EXCEPTION SAFETY TESTS (27-32)
# ============================================================================

def test_27_unavailable_adapter_returns_structured_unavailable(asr_fixture):
    service, dev_adapter, _, _, _ = asr_fixture
    dev_adapter.set_available(False)

    audio = AudioInput(audio_id="aud-unavail", source_reference="sample.wav", format=".wav")
    req = ASRRequest(audio=audio)
    result = service.transcribe(req)
    assert result.status == ASRStatus.UNAVAILABLE
    assert "ASR_UNAVAILABLE" in (result.error_type or "")


def test_28_adapter_exception_caught_safely(asr_fixture):
    service, dev_adapter, _, _, _ = asr_fixture
    dev_adapter.simulate_error = "Hardware codec initialization failed"

    audio = AudioInput(audio_id="aud-err", source_reference="sample.wav", format=".wav")
    req = ASRRequest(audio=audio)
    result = service.transcribe(req)
    assert result.status == ASRStatus.FAILED
    assert "ADAPTER_EXCEPTION" in (result.error_type or "")
    assert "Hardware codec" in (result.error_message or "")


def test_29_adapter_timeout_handled_safely(asr_fixture):
    service, dev_adapter, _, _, _ = asr_fixture
    dev_adapter.simulate_timeout = True

    audio = AudioInput(audio_id="aud-timeout", source_reference="sample.wav", format=".wav")
    req = ASRRequest(audio=audio)
    result = service.transcribe(req)
    assert result.status == ASRStatus.TIMEOUT
    assert "ASR_TIMEOUT" in (result.error_type or "")


def test_30_negative_audio_duration_rejected(asr_fixture):
    service, _, _, _, _ = asr_fixture
    audio = AudioInput(
        audio_id="aud-neg",
        source_reference="sample.wav",
        format=".wav",
        duration_seconds=-10.0,
    )
    req = ASRRequest(audio=audio)
    result = service.transcribe(req)
    assert result.status == ASRStatus.INVALID_INPUT
    assert "INVALID_DURATION" in (result.error_type or "")


def test_31_adapter_unsupported_format_rejected(asr_fixture):
    # Service configured with .ogg in allowed list, but adapter only supports .wav
    dev_adapter = DevTestASRAdapter(supported_formats=[".wav"])
    service = ASRService(adapter=dev_adapter)

    audio = AudioInput(audio_id="aud-ogg", source_reference="sample.ogg", format=".ogg")
    req = ASRRequest(audio=audio)
    result = service.transcribe(req)
    assert result.status == ASRStatus.UNSUPPORTED_FORMAT
    assert "ADAPTER_CANNOT_DECODE_FORMAT" in (result.error_type or "")


def test_32_excessive_transcript_length_rejected(asr_fixture):
    service, dev_adapter, _, _, config = asr_fixture
    # Register huge transcript
    huge_text = "Word " * (config.max_transcript_length + 500)
    dev_adapter.register_transcript(
        "aud-huge",
        Transcript(transcript_id="tr-huge", text=huge_text, language="en"),
    )

    audio = AudioInput(audio_id="aud-huge", source_reference="sample.wav", format=".wav")
    req = ASRRequest(audio=audio)
    result = service.transcribe(req)
    assert result.status == ASRStatus.INVALID_INPUT
    assert "EXCESSIVE_TRANSCRIPT_LENGTH" in (result.error_type or "")


# ============================================================================
# 5. SECURITY & AUTHORIZATION TESTS (33-38)
# ============================================================================

def test_33_security_guard_blocks_direct_shell_execution(specialist_registry_env):
    engine, _, _, _, active_specialist = specialist_registry_env
    req = DelegationRequest(
        delegation_id="del-sec-01",
        parent_task_id="task-01",
        executive_twin_id="twin-ceo",
        specialist_id=active_specialist.specialist_id,
        objective="Transcribe audio recording",
        task="shell_exec: run ffmpeg to decode audio.wav",
        required_capabilities=["audio_transcription"],
        expected_output="Transcript",
    )
    result = engine.execute_delegation(req)
    assert result.status == "FAILED"
    assert result.verification_status == VerificationStatus.FAILED
    assert "AUTHORIZATION_DENIED" in result.output


def test_34_unauthorized_specialist_tool_blocked(specialist_registry_env):
    engine, _, _, _, _ = specialist_registry_env
    # Request delegation to specialist lacking asr_engine tool
    req = DelegationRequest(
        delegation_id="del-sec-02",
        parent_task_id="task-02",
        executive_twin_id="twin-ceo",
        specialist_id="spec-asr-no-auth",
        objective="Transcribe audio",
        task="audio_transcription",
        required_capabilities=["audio_transcription"],
        inputs={"audio_id": "aud-01", "source_reference": "rec.wav"},
        expected_output="Transcript",
    )
    result = engine.execute_delegation(req)
    assert result.status == "FAILED"
    assert "AUTHORIZATION_DENIED" in result.output


def test_35_inactive_specialist_blocked(specialist_registry_env):
    engine, _, _, _, _ = specialist_registry_env
    req = DelegationRequest(
        delegation_id="del-sec-03",
        parent_task_id="task-03",
        executive_twin_id="twin-ceo",
        specialist_id="spec-asr-inactive",
        objective="Transcribe audio",
        task="audio_transcription",
        required_capabilities=["audio_transcription"],
        inputs={"audio_id": "aud-01", "source_reference": "rec.wav"},
        expected_output="Transcript",
    )
    result = engine.execute_delegation(req)
    assert result.status == "FAILED"
    assert "CAPABILITY_UNAVAILABLE" in result.output


def test_36_unregistered_specialist_blocked(specialist_registry_env):
    engine, _, _, _, _ = specialist_registry_env
    req = DelegationRequest(
        delegation_id="del-sec-04",
        parent_task_id="task-04",
        executive_twin_id="twin-ceo",
        specialist_id="spec-nonexistent-99",
        objective="Transcribe audio",
        task="audio_transcription",
        required_capabilities=["audio_transcription"],
        inputs={"audio_id": "aud-01", "source_reference": "rec.wav"},
        expected_output="Transcript",
    )
    result = engine.execute_delegation(req)
    assert result.status == "FAILED"
    assert "CAPABILITY_UNAVAILABLE" in result.output


def test_37_unauthenticated_security_context_blocked(specialist_registry_env):
    engine, _, _, _, active_specialist = specialist_registry_env
    unauth_context = SecurityContext(is_authenticated=False)
    req = DelegationRequest(
        delegation_id="del-sec-05",
        parent_task_id="task-05",
        executive_twin_id="twin-ceo",
        specialist_id=active_specialist.specialist_id,
        objective="Transcribe audio",
        task="audio_transcription",
        required_capabilities=["audio_transcription"],
        inputs={"audio_id": "aud-01", "source_reference": "rec.wav"},
        expected_output="Transcript",
        security_context=unauth_context,
    )
    result = engine.execute_delegation(req)
    assert result.status == "FAILED"
    assert "AUTHORIZATION_DENIED" in result.output


def test_38_missing_parameters_rejected(specialist_registry_env):
    engine, _, _, _, active_specialist = specialist_registry_env
    # Missing source_reference in inputs
    req = DelegationRequest(
        delegation_id="del-sec-06",
        parent_task_id="task-06",
        executive_twin_id="twin-ceo",
        specialist_id=active_specialist.specialist_id,
        objective="Transcribe audio",
        task="audio_transcription",
        required_capabilities=["audio_transcription"],
        inputs={"audio_id": "aud-01"},
        expected_output="Transcript",
    )
    result = engine.execute_delegation(req)
    assert result.status == "FAILED"
    assert "Missing required parameter 'source_reference'" in result.output


# ============================================================================
# 6. SPECIALIST INTEGRATION & EVIDENCE TESTS (39-44)
# ============================================================================

def test_39_capability_matcher_discovers_asr_specialist(specialist_registry_env):
    _, registry, _, _, active_specialist = specialist_registry_env
    req = CapabilityRequirement(
        capability_name="audio_transcription",
        description="Audio speech recognition requirement",
    )
    sec_ctx = SecurityContext()
    match_result = CapabilityMatcher.match_capability(
        requirement=req,
        candidates=registry.list_all_specialists(),
        security_context=sec_ctx,
    )
    assert match_result.status == "MATCHED"
    assert match_result.selected_specialist is not None
    assert match_result.selected_specialist.specialist_id == active_specialist.specialist_id


def test_40_successful_specialist_execution_with_evidence(specialist_registry_env):
    engine, _, _, ws, active_specialist = specialist_registry_env
    ws.write_file("input.wav", "WAVE_BYTES")

    req = DelegationRequest(
        delegation_id="del-exec-01",
        parent_task_id="task-07",
        executive_twin_id="twin-cmo",
        specialist_id=active_specialist.specialist_id,
        objective="Transcribe customer interview audio",
        task="audio_transcription",
        required_capabilities=["audio_transcription"],
        inputs={
            "audio_id": "audio_en_sample",
            "source_reference": "input.wav",
            "format": ".wav",
            "workspace_id": ws.workspace_id,
        },
        expected_output="Structured text transcript",
    )
    result = engine.execute_delegation(req)
    assert result.status == "SUCCESS"
    assert result.verification_status == VerificationStatus.VERIFIED
    assert "executive digital workforce" in result.output

    # Validate Empirical Evidence Set
    assert result.evidence.contains_category(EvidenceCategory.EXECUTION_LOG)
    assert result.evidence.contains_category(EvidenceCategory.VERIFICATION)


def test_41_specialist_execution_failed_delegation_result(specialist_registry_env):
    engine, _, _, ws, active_specialist = specialist_registry_env
    # Nonexistent file inside workspace
    req = DelegationRequest(
        delegation_id="del-exec-02",
        parent_task_id="task-08",
        executive_twin_id="twin-cmo",
        specialist_id=active_specialist.specialist_id,
        objective="Transcribe audio",
        task="audio_transcription",
        required_capabilities=["audio_transcription"],
        inputs={
            "audio_id": "aud-fail",
            "source_reference": "missing.wav",
            "format": ".wav",
            "workspace_id": ws.workspace_id,
        },
        expected_output="Transcript",
    )
    result = engine.execute_delegation(req)
    assert result.status == "FAILED"
    assert result.verification_status == VerificationStatus.FAILED
    assert len(result.errors) > 0


def test_42_specialist_execution_adapter_delegation(specialist_registry_env):
    engine, _, _, ws, active_specialist = specialist_registry_env
    adapter = SpecialistExecutionAdapter(execution_engine=engine)

    req = DelegationRequest(
        delegation_id="del-adapt-01",
        parent_task_id="task-09",
        executive_twin_id="twin-cmo",
        specialist_id=active_specialist.specialist_id,
        objective="Transcribe audio",
        task="audio_transcription",
        required_capabilities=["audio_transcription"],
        inputs={
            "audio_id": "audio_en_sample",
            "source_reference": "test.wav",
            "format": ".wav",
        },
        expected_output="Transcript",
    )
    result = adapter.execute_delegation(req)
    assert result.status == "SUCCESS"
    assert result.verification_status == VerificationStatus.VERIFIED


def test_43_audit_logger_records_asr_lifecycle(asr_fixture):
    service, _, _, _, _ = asr_fixture
    AuditLogger.clear_events()

    audio = AudioInput(
        audio_id="aud-audit-01",
        source_reference="sample.wav",
        format=".wav",
    )
    req = ASRRequest(audio=audio)
    service.transcribe(req)

    events = [e.event_type for e in AuditLogger.get_events()]
    assert "asr.transcription.started" in events
    assert "asr.transcription.completed" in events


def test_44_no_unrestricted_shell_or_eval_in_asr_components():
    import inspect
    from executive_twins import audio

    modules = [audio.models, audio.interfaces, audio.asr_service, audio.dev_adapters]
    for mod in modules:
        source = inspect.getsource(mod)
        assert "os.system(" not in source
        assert "os.popen(" not in source
        assert "subprocess.Popen" not in source
        assert "subprocess.run" not in source
        assert "shell=True" not in source
        assert "eval(" not in source
        assert "exec(" not in source


# ============================================================================
# 7. OPTIONAL LOCAL ASR INTEGRATION TESTS (45)
# ============================================================================

def test_45_optional_local_whisper_adapter_availability():
    local_adapter = LocalASRAdapter(model_instance=None)
    # Model instance is None, so is_available should be False without failing
    assert not local_adapter.is_available()

    req = ASRRequest(
        audio=AudioInput(audio_id="aud-01", source_reference="a.wav", format=".wav")
    )
    res = local_adapter.transcribe_audio(req)
    assert res.status == ASRStatus.UNAVAILABLE
    assert "LOCAL_MODEL_UNAVAILABLE" in (res.error_type or "")

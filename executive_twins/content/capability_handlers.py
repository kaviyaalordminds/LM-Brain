import re
from typing import Any, Dict, List, Optional, Union
import uuid

from executive_twins.content.dev_adapters import (
    ContentBuilder,
    DeterministicContentValidator,
    HTMLContentRenderer,
    MarkdownContentRenderer,
)
from executive_twins.content.models import (
    Channel,
    ContentBrief,
    ContentMetadata,
    ContentPiece,
    ContentType,
    Tone,
)
from executive_twins.execution.capability_execution_engine import (
    BaseCapabilityHandler,
    CapabilityHandlerOutput,
)
from executive_twins.files.dev_adapters import DevFileServiceAdapter
from executive_twins.schemas.common import FactItem, FactState
from executive_twins.schemas.delegation import DelegationRequest
from executive_twins.schemas.evidence import (
    ArtifactEvidence,
    VerificationEvidence,
)
from executive_twins.schemas.specialist import SpecialistMetadata


def _parse_content_type(raw: Any) -> ContentType:
    if isinstance(raw, ContentType):
        return raw
    val = str(raw).upper().replace(" ", "_").replace("-", "_")
    if val in ContentType.__members__:
        return ContentType[val]
    for member in ContentType:
        if member.value == val or member.name == val:
            return member
    if any(k in val for k in ["AD", "MARKETING", "COPY"]):
        return ContentType.AD_COPY
    if any(k in val for k in ["PRESS", "RELEASE", "PR"]):
        return ContentType.PRESS_RELEASE
    if any(k in val for k in ["EMAIL", "NEWSLETTER", "MAIL"]):
        return ContentType.EMAIL
    if any(k in val for k in ["SOCIAL", "POST", "LINKEDIN", "TWITTER"]):
        return ContentType.SOCIAL_POST
    return ContentType.BLOG_POST


def _parse_channel(raw: Any) -> Channel:
    if isinstance(raw, Channel):
        return raw
    val = str(raw).upper().replace(" ", "_").replace("-", "_")
    if val in Channel.__members__:
        return Channel[val]
    for member in Channel:
        if member.value == val or member.name == val:
            return member
    if "PRESS" in val or "MEDIA" in val:
        return Channel.PRESS
    if "LINKEDIN" in val:
        return Channel.LINKEDIN
    if "INSTAGRAM" in val or "TWITTER" in val:
        return Channel.INSTAGRAM
    if "EMAIL" in val or "NEWSLETTER" in val:
        return Channel.EMAIL
    if "WEB" in val or "SITE" in val:
        return Channel.WEBSITE
    return Channel.BLOG


def _parse_tone(raw: Any) -> Tone:
    if isinstance(raw, Tone):
        return raw
    val = str(raw).upper().replace(" ", "_").replace("-", "_")
    if val in Tone.__members__:
        return Tone[val]
    for member in Tone:
        if member.value == val or member.name == val:
            return member
    if any(k in val for k in ["EXEC", "FORMAL"]):
        return Tone.FORMAL
    if any(k in val for k in ["PERSUASIVE", "SALES"]):
        return Tone.PERSUASIVE
    if any(k in val for k in ["FRIENDLY", "CASUAL"]):
        return Tone.FRIENDLY
    if any(k in val for k in ["CONVERSATIONAL", "CHAT"]):
        return Tone.CONVERSATIONAL
    if any(k in val for k in ["INFORMATIVE", "TECHNICAL"]):
        return Tone.INFORMATIVE
    return Tone.PROFESSIONAL


class ContentGenerationCapabilityHandler(BaseCapabilityHandler):
    """
    Approved Capability Handler for synthesizing marketing copy, blog posts,
    social snippets, and PR announcements into structured, rendered artifacts.
    EXECUTION SAFETY: Registered within SpecialistExecutionEngine boundary.
    All file operations delegate to sandboxed FileService.
    """

    capability_name = "content_generation"
    required_tool = "file_service"
    required_params = ["purpose"]
    allowed_params = [
        "purpose",
        "topic",
        "title",
        "content_type",
        "channel",
        "tone",
        "target_audience",
        "key_points",
        "call_to_action",
        "cta",
        "brief",
        "output_format",
        "relative_path",
        "workspace_id",
        "tags",
        "metadata",
        "sections",
        "body",
    ]

    def __init__(self, file_adapter: Optional[DevFileServiceAdapter] = None) -> None:
        self.file_adapter = file_adapter
        self.markdown_renderer = MarkdownContentRenderer()
        self.html_renderer = HTMLContentRenderer()

    def validate_parameters(self, inputs: Dict[str, Any]) -> Optional[str]:
        has_identifier = any(
            k in inputs and inputs[k]
            for k in ["purpose", "topic", "title", "brief"]
        )
        if not has_identifier:
            return "Missing required parameter 'purpose', 'topic', 'title', or 'brief' for capability 'content_generation'."
        return super().validate_parameters(inputs)

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        raw_brief = request.inputs.get("brief")
        ws_id = str(request.inputs.get("workspace_id", "default") or "default")
        output_format = str(request.inputs.get("output_format", "markdown")).lower()

        # Parse or construct brief
        if isinstance(raw_brief, ContentBrief):
            brief = raw_brief
        elif isinstance(raw_brief, dict):
            brief = ContentBrief.model_validate(raw_brief)
        else:
            purpose = str(
                request.inputs.get("purpose")
                or request.inputs.get("topic")
                or request.inputs.get("title")
                or "Strategic Update"
            )
            content_type = _parse_content_type(request.inputs.get("content_type", ContentType.BLOG_POST))
            channel = _parse_channel(request.inputs.get("channel", Channel.BLOG))
            tone = _parse_tone(request.inputs.get("tone", Tone.PROFESSIONAL))
            target_audience = str(request.inputs.get("target_audience", "General Professional Audience"))
            key_points = request.inputs.get("key_points", [])
            cta = request.inputs.get("call_to_action") or request.inputs.get("cta")

            brief = ContentBrief(
                purpose=purpose,
                content_type=content_type,
                channel=channel,
                tone=tone,
                target_audience=target_audience,
                key_points=key_points if isinstance(key_points, list) else [str(key_points)],
                call_to_action=str(cta) if cta else None,
            )


        # Build content piece
        builder = ContentBuilder(brief=brief)
        if "title" in request.inputs and request.inputs["title"]:
            builder.set_title(str(request.inputs["title"]))
        if "body" in request.inputs and request.inputs["body"]:
            builder.set_body(str(request.inputs["body"]))
        if "call_to_action" in request.inputs and request.inputs["call_to_action"]:
            builder.set_call_to_action(str(request.inputs["call_to_action"]))
        elif "cta" in request.inputs and request.inputs["cta"]:
            builder.set_call_to_action(str(request.inputs["cta"]))

        raw_sections = request.inputs.get("sections")
        if isinstance(raw_sections, dict):
            for h, text in raw_sections.items():
                builder.add_section(h, text)

        content_piece = builder.build()

        # Determine relative path and rendering format
        rel_path = request.inputs.get("relative_path")
        if not rel_path:
            clean_title = re.sub(r"[^a-zA-Z0-9_\-]+", "_", (content_piece.title or "content").lower()).strip("_")
            ext = "html" if output_format == "html" else "md"
            rel_path = f"content/{clean_title}.{ext}"

        if rel_path.endswith(".html") or output_format == "html":
            rendered = self.html_renderer.render(content_piece)
            mime_type = "text/html"
        else:
            rendered = self.markdown_renderer.render(content_piece)
            mime_type = "text/markdown"

        artifacts: List[str] = []
        additional_evidence: List[Any] = []

        if self.file_adapter:
            file_service = self.file_adapter.get_file_service(ws_id)
            if not file_service:
                return CapabilityHandlerOutput(
                    success=False,
                    output_text=f"EXECUTION_ERROR: Workspace '{ws_id}' not found in FileService adapter.",
                    errors=[f"Workspace '{ws_id}' not found."],
                )
            write_res = file_service.create_file(rel_path, rendered, overwrite=True)
            if not write_res.success:
                return CapabilityHandlerOutput(
                    success=False,
                    output_text=f"EXECUTION_ERROR: Could not write content file '{rel_path}': {write_res.error_message}",
                    errors=[str(write_res.error_message)],
                )

            artifact_uri = f"workspace://{ws_id}/{rel_path}"
            artifacts.append(artifact_uri)
            additional_evidence.append(
                ArtifactEvidence(
                    evidence_id=f"ev-content-art-{request.delegation_id[:8]}",
                    artifact_uri=artifact_uri,
                    description=f"Generated content artifact for '{content_piece.title}'",
                    mime_type=mime_type,
                )
            )

        facts = [
            FactItem(
                statement=f"Generated content asset '{content_piece.title}' of type '{content_piece.metadata.content_type.value}' targeted for channel '{content_piece.metadata.channel.value}'.",
                state=FactState.FACT,
                source="content_specialist",
            )
        ]

        return CapabilityHandlerOutput(
            success=True,
            output_text=f"Successfully generated content piece '{content_piece.title}' at '{rel_path}'.",
            facts=facts,
            artifacts=artifacts,
            errors=[],
            additional_evidence=additional_evidence,
        )


class ContentEditingCapabilityHandler(BaseCapabilityHandler):
    """
    Approved Capability Handler for controlled structured modifications, section refinement,
    and text replacement within content assets.
    EXECUTION SAFETY: Registered within SpecialistExecutionEngine boundary.
    All file operations delegate to sandboxed FileService.
    """

    capability_name = "content_editing"
    required_tool = "file_service"
    required_params = ["relative_path"]
    allowed_params = [
        "relative_path",
        "workspace_id",
        "edits",
        "action",
        "target_text",
        "replacement_text",
        "content",
        "text",
        "title",
        "call_to_action",
        "cta",
    ]

    def __init__(self, file_adapter: Optional[DevFileServiceAdapter] = None) -> None:
        self.file_adapter = file_adapter

    def validate_parameters(self, inputs: Dict[str, Any]) -> Optional[str]:
        if "relative_path" not in inputs or not inputs["relative_path"]:
            return "Missing required parameter 'relative_path' for capability 'content_editing'."

        has_edit = any(
            k in inputs and inputs[k] is not None
            for k in [
                "edits",
                "action",
                "target_text",
                "content",
                "text",
                "title",
                "call_to_action",
                "cta",
            ]
        )
        if not has_edit:
            return "Missing edit specification ('edits', 'action', 'target_text', 'content', or 'title') for capability 'content_editing'."

        return super().validate_parameters(inputs)

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        rel_path = str(request.inputs.get("relative_path", ""))
        ws_id = str(request.inputs.get("workspace_id", "default") or "default")

        if self.file_adapter is None:
            return CapabilityHandlerOutput(
                success=False,
                output_text="EXECUTION_ERROR: FileService adapter is not available for content editing.",
                errors=["No FileService adapter configured."],
            )

        file_service = self.file_adapter.get_file_service(ws_id)
        if not file_service:
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"EXECUTION_ERROR: Workspace '{ws_id}' not found.",
                errors=[f"Workspace '{ws_id}' not found."],
            )

        read_res = file_service.read_file(rel_path)
        if not read_res.success or read_res.content is None:
            err_msg = read_res.error_message or "File could not be read."
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"CONTENT_NOT_FOUND: Could not read target content asset '{rel_path}': {err_msg}",
                errors=[err_msg],
            )

        current_text = read_res.content

        # Extract edits list or single edit action
        raw_edits = request.inputs.get("edits")
        edit_ops: List[Dict[str, Any]] = []
        if isinstance(raw_edits, list):
            edit_ops = [e for e in raw_edits if isinstance(e, dict)]
        elif isinstance(raw_edits, dict):
            edit_ops = [raw_edits]
        else:
            action = request.inputs.get("action", "replace_text")
            edit_ops = [
                {
                    "action": action,
                    "target_text": request.inputs.get("target_text"),
                    "replacement_text": request.inputs.get("replacement_text", ""),
                    "content": request.inputs.get("content", request.inputs.get("text", "")),
                    "title": request.inputs.get("title"),
                    "call_to_action": request.inputs.get("call_to_action", request.inputs.get("cta")),
                }
            ]

        modified_text = current_text
        applied_count = 0

        for op in edit_ops:
            action = str(op.get("action", "replace_text")).lower()

            if action == "replace_text":
                target = str(op.get("target_text", ""))
                replacement = str(op.get("replacement_text", ""))
                if target and target in modified_text:
                    modified_text = modified_text.replace(target, replacement)
                    applied_count += 1

            elif action in ("append_content", "append_text"):
                extra = str(op.get("content", op.get("text", "")))
                if extra:
                    modified_text = modified_text.rstrip() + f"\n\n{extra}\n"
                    applied_count += 1

            elif action in ("prepend_content", "prepend_text"):
                prefix = str(op.get("content", op.get("text", "")))
                if prefix:
                    modified_text = f"{prefix}\n\n" + modified_text.lstrip()
                    applied_count += 1

            elif action in ("update_title", "set_title"):
                new_title = str(op.get("title", ""))
                if new_title:
                    if modified_text.startswith("# "):
                        first_newline = modified_text.find("\n")
                        if first_newline != -1:
                            modified_text = f"# {new_title}" + modified_text[first_newline:]
                        else:
                            modified_text = f"# {new_title}\n"
                    else:
                        modified_text = f"# {new_title}\n\n" + modified_text
                    applied_count += 1

            elif action in ("update_cta", "set_cta"):
                new_cta = str(op.get("call_to_action", op.get("cta", "")))
                if new_cta:
                    if "**Call to Action**:" in modified_text:
                        modified_text = re.sub(
                            r"\*\*Call to Action\*\*:.*",
                            f"**Call to Action**: {new_cta}",
                            modified_text,
                        )
                    else:
                        modified_text = modified_text.rstrip() + f"\n\n**Call to Action**: {new_cta}\n"
                    applied_count += 1

            elif action == "normalize_whitespace":
                modified_text = re.sub(r"\n{3,}", "\n\n", modified_text).strip() + "\n"
                applied_count += 1

        write_res = file_service.create_file(rel_path, modified_text, overwrite=True)
        if not write_res.success:
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"EXECUTION_ERROR: Failed to save edited content file '{rel_path}': {write_res.error_message}",
                errors=[str(write_res.error_message)],
            )

        artifact_uri = f"workspace://{ws_id}/{rel_path}"
        art_ev = ArtifactEvidence(
            evidence_id=f"ev-content-edit-art-{request.delegation_id[:8]}",
            artifact_uri=artifact_uri,
            description=f"Edited content asset at '{rel_path}' ({applied_count} operation(s) applied)",
            mime_type="text/html" if rel_path.endswith(".html") else "text/markdown",
        )

        facts = [
            FactItem(
                statement=f"Successfully applied {applied_count} edit operation(s) to content asset '{rel_path}'.",
                state=FactState.FACT,
                source="content_specialist",
            )
        ]

        return CapabilityHandlerOutput(
            success=True,
            output_text=f"Successfully updated content asset '{rel_path}' with {applied_count} edit operation(s).",
            facts=facts,
            artifacts=[artifact_uri],
            errors=[],
            additional_evidence=[art_ev],
        )


class ContentValidationCapabilityHandler(BaseCapabilityHandler):
    """
    Approved Capability Handler for structural consistency, audience alignment,
    and brief compliance validation on content assets.
    EXECUTION SAFETY: Registered within SpecialistExecutionEngine boundary.
    No filesystem mutation performed.
    """

    capability_name = "content_validation"
    required_tool = "content_validator"
    required_params = []
    allowed_params = [
        "content",
        "content_piece",
        "brief",
        "required_keywords",
        "require_cta",
        "min_length",
        "max_length",
        "expected_tone",
        "expected_channel",
    ]

    def __init__(self) -> None:
        self.validator = DeterministicContentValidator()


    def validate_parameters(self, inputs: Dict[str, Any]) -> Optional[str]:
        if "content" not in inputs and "content_piece" not in inputs:
            return "Missing required parameter 'content' or 'content_piece' for capability 'content_validation'."
        return super().validate_parameters(inputs)

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        raw_content = request.inputs.get("content") or request.inputs.get("content_piece")
        raw_brief = request.inputs.get("brief")
        required_keywords = request.inputs.get("required_keywords", [])
        require_cta = bool(request.inputs.get("require_cta", False))
        min_length = int(request.inputs.get("min_length", 10))
        max_length = int(request.inputs.get("max_length", 500000))

        # Parse brief if present
        brief: Optional[ContentBrief] = None
        if isinstance(raw_brief, ContentBrief):
            brief = raw_brief
        elif isinstance(raw_brief, dict):
            try:
                brief = ContentBrief.model_validate(raw_brief)
            except Exception:
                brief = None

        # Parse or wrap content_piece
        if isinstance(raw_content, ContentPiece):
            piece = raw_content
        elif isinstance(raw_content, dict):
            try:
                piece = ContentPiece.model_validate(raw_content)
            except Exception as e:
                return CapabilityHandlerOutput(
                    success=False,
                    output_text=f"VALIDATION_FAILED: Invalid content piece dictionary: {str(e)}",
                    errors=[str(e)],
                )
        elif isinstance(raw_content, str):
            piece = ContentPiece(
                metadata=ContentMetadata(),
                title="Direct Text Evaluation",
                body=raw_content,
            )
        else:
            return CapabilityHandlerOutput(
                success=False,
                output_text="VALIDATION_FAILED: 'content' must be a ContentPiece model, dictionary, or string.",
                errors=["Invalid content object type."],
            )

        # Run base validator
        review_result = self.validator.validate(piece, brief=brief)
        errors: List[str] = list(review_result.issues)

        # Check min/max lengths
        body_len = len(piece.body.strip())
        if body_len < min_length:
            errors.append(f"Content body length ({body_len}) is below minimum required length ({min_length}).")
        if body_len > max_length:
            errors.append(f"Content body length ({body_len}) exceeds maximum allowed length ({max_length}).")

        # Check required keywords
        if isinstance(required_keywords, list) and required_keywords:
            body_lower = piece.body.lower()
            for kw in required_keywords:
                if str(kw).lower() not in body_lower:
                    errors.append(f"Missing required keyword: '{kw}'.")

        # Check require_cta
        if require_cta and not piece.call_to_action:
            errors.append("Call to Action is strictly required but was not provided.")

        if errors:
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"Content validation failed with {len(errors)} error(s).",
                errors=errors,
            )

        verif_ev = VerificationEvidence(
            evidence_id=f"ev-content-verif-{request.delegation_id[:8]}",
            verifier_id="content_validator",
            verified_status="VERIFIED",
            description=f"Verified content piece '{piece.title}' with 0 structural errors.",
        )

        facts = [
            FactItem(
                statement=f"Validated content piece '{piece.title}' against quality and brief constraints.",
                state=FactState.FACT,
                source="content_validator",
            )
        ]

        return CapabilityHandlerOutput(
            success=True,
            output_text=f"Content piece '{piece.title}' successfully verified.",
            facts=facts,
            artifacts=[],
            errors=[],
            additional_evidence=[verif_ev],
        )

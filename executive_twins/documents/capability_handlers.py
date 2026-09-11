from typing import Any, Dict, List, Optional
import uuid

from executive_twins.documents.dev_adapters import (
    DocumentBuilder,
    MarkdownDocumentParser,
    MarkdownDocumentRenderer,
)
from executive_twins.documents.models import (
    BlockType,
    BreakBlock,
    CodeBlock,
    Document,
    DocumentBlock,
    DocumentFormat,
    DocumentMetadata,
    DocumentSection,
    HeadingBlock,
    ImageRefBlock,
    ListBlock,
    ParagraphBlock,
    TableBlock,
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


class DocumentGenerationCapabilityHandler(BaseCapabilityHandler):
    """
    Approved Capability Handler for synthesizing structured documents and offline visual/text artifacts.
    EXECUTION SAFETY: Registered within SpecialistExecutionEngine boundary.
    All file operations delegate to sandboxed FileService.
    """

    capability_name = "document_generation"
    required_tool = "file_service"
    required_params = ["title"]
    allowed_params = [
        "title",
        "sections",
        "blocks",
        "metadata",
        "output_format",
        "relative_path",
        "workspace_id",
        "template_name",
        "variables",
        "content",
        "topic",
        "overview",
    ]

    def __init__(self, file_adapter: Optional[DevFileServiceAdapter] = None) -> None:
        self.file_adapter = file_adapter
        self.renderer = MarkdownDocumentRenderer()
        self.parser = MarkdownDocumentParser()

    def validate_parameters(self, inputs: Dict[str, Any]) -> Optional[str]:
        if "title" not in inputs or not inputs["title"]:
            return "Missing required parameter 'title' for capability 'document_generation'."
        return super().validate_parameters(inputs)

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        title = str(request.inputs.get("title", "Untitled Document"))
        output_format = str(request.inputs.get("output_format", "markdown")).lower()
        ws_id = str(request.inputs.get("workspace_id", "default") or "default")

        # 1. Build Document
        builder = DocumentBuilder(title=title)

        raw_meta = request.inputs.get("metadata")
        if isinstance(raw_meta, DocumentMetadata):
            builder.set_metadata(raw_meta)
        elif isinstance(raw_meta, dict):
            builder.set_metadata(
                DocumentMetadata(
                    author=raw_meta.get("author"),
                    version=str(raw_meta.get("version", "1.0")),
                    document_format=DocumentFormat.MARKDOWN,
                    tags=raw_meta.get("tags", []),
                    custom_attributes=raw_meta.get("custom_attributes", {}),
                )
            )

        # Process Root Blocks
        raw_blocks = request.inputs.get("blocks", [])
        if isinstance(raw_blocks, list):
            for b in raw_blocks:
                if isinstance(b, DocumentBlock):
                    builder.add_block(b)
                elif isinstance(b, dict):
                    b_type = str(b.get("block_type", "PARAGRAPH")).upper()
                    if b_type == "PARAGRAPH":
                        builder.add_paragraph(str(b.get("text", "")))
                    elif b_type == "HEADING":
                        builder.add_heading(
                            text=str(b.get("text", "")),
                            level=int(b.get("level", 1)),
                        )
                    elif b_type == "LIST":
                        builder.add_block(
                            ListBlock(
                                items=list(b.get("items", [])),
                                is_ordered=bool(b.get("is_ordered", False)),
                            )
                        )
                    elif b_type == "TABLE":
                        builder.add_table(
                            headers=list(b.get("headers", [])),
                            rows=list(b.get("rows", [])),
                            caption=b.get("caption"),
                        )
                    elif b_type == "IMAGE_REF":
                        builder.add_image_ref(
                            uri=str(b.get("uri", "")),
                            alt_text=b.get("alt_text"),
                            caption=b.get("caption"),
                        )
                    elif b_type == "CODE":
                        builder.add_block(
                            CodeBlock(
                                code=str(b.get("code", "")),
                                language=b.get("language"),
                            )
                        )
                    elif b_type == "BREAK":
                        builder.add_block(BreakBlock())

        # Process Sections
        raw_sections = request.inputs.get("sections", [])
        if isinstance(raw_sections, list) and len(raw_sections) > 0:
            for s_idx, s_data in enumerate(raw_sections):
                if isinstance(s_data, DocumentSection):
                    builder.add_section(s_data)
                elif isinstance(s_data, dict):
                    sec_title = str(s_data.get("title", f"Section {s_idx + 1}"))
                    sec_level = int(s_data.get("level", 2))
                    section = DocumentSection(title=sec_title, level=sec_level)

                    if "content" in s_data and s_data["content"]:
                        section.add_block(ParagraphBlock(text=str(s_data["content"])))

                    sec_blocks = s_data.get("blocks", [])
                    if isinstance(sec_blocks, list):
                        for sb in sec_blocks:
                            if isinstance(sb, DocumentBlock):
                                section.add_block(sb)
                            elif isinstance(sb, dict):
                                sb_type = str(sb.get("block_type", "PARAGRAPH")).upper()
                                if sb_type == "PARAGRAPH":
                                    section.add_block(ParagraphBlock(text=str(sb.get("text", ""))))
                                elif sb_type == "HEADING":
                                    section.add_block(
                                        HeadingBlock(
                                            text=str(sb.get("text", "")),
                                            level=int(sb.get("level", 3)),
                                        )
                                    )
                                elif sb_type == "LIST":
                                    section.add_block(
                                        ListBlock(
                                            items=list(sb.get("items", [])),
                                            is_ordered=bool(sb.get("is_ordered", False)),
                                        )
                                    )
                                elif sb_type == "TABLE":
                                    section.add_block(
                                        TableBlock.create(
                                            headers=list(sb.get("headers", [])),
                                            rows_data=list(sb.get("rows", [])),
                                            caption=sb.get("caption"),
                                        )
                                    )
                                elif sb_type == "IMAGE_REF":
                                    section.add_block(
                                        ImageRefBlock(
                                            uri=str(sb.get("uri", "")),
                                            alt_text=sb.get("alt_text"),
                                            caption=sb.get("caption"),
                                        )
                                    )
                                elif sb_type == "CODE":
                                    section.add_block(
                                        CodeBlock(
                                            code=str(sb.get("code", "")),
                                            language=sb.get("language"),
                                        )
                                    )

                    builder.add_section(section)
        elif not raw_blocks:
            content = request.inputs.get("content") or request.inputs.get("overview") or request.inputs.get("topic")
            if content:
                builder.add_paragraph(str(content))
            else:
                builder.add_paragraph(f"Structured document content for {title}.")

        doc = builder.build()

        # 2. Render Document
        rendered_content = self.renderer.render(doc)
        ext = "md"

        # 3. Persist via FileService if available
        default_filename = f"document_{request.delegation_id[:8]}.{ext}"
        rel_path = str(request.inputs.get("relative_path", default_filename))

        artifacts: List[str] = []
        additional_evidence: List[Any] = []

        if self.file_adapter is not None:
            file_service = self.file_adapter.get_file_service(ws_id)
            if file_service:
                res = file_service.create_file(rel_path, rendered_content, overwrite=True)
                if res.success and res.artifact:
                    artifacts.append(res.artifact.artifact_uri)
                    additional_evidence.extend(res.evidence)
        else:
            artifact_uri = f"workspace://{ws_id}/{rel_path}"
            artifacts.append(artifact_uri)
            additional_evidence.append(
                ArtifactEvidence(
                    evidence_id=f"ev-doc-art-{request.delegation_id[:8]}",
                    artifact_uri=artifact_uri,
                    description=f"Generated document artifact for '{title}'",
                    mime_type="text/markdown",
                )
            )

        facts = [
            FactItem(
                statement=f"Generated document '{title}' containing {len(doc.sections)} sections and {len(doc.blocks)} root blocks.",
                state=FactState.FACT,
                source="document_specialist",
            )
        ]

        return CapabilityHandlerOutput(
            success=True,
            output_text=f"Successfully generated document '{title}' with {len(doc.sections)} section(s) at '{rel_path}'.",
            facts=facts,
            artifacts=artifacts,
            errors=[],
            additional_evidence=additional_evidence,
        )


class DocumentEditingCapabilityHandler(BaseCapabilityHandler):
    """
    Approved Capability Handler for structured document modification, section editing, and updates.
    EXECUTION SAFETY: Registered within SpecialistExecutionEngine boundary.
    All file operations delegate to sandboxed FileService.
    """

    capability_name = "document_editing"
    required_tool = "file_service"
    required_params = ["relative_path"]
    allowed_params = [
        "relative_path",
        "workspace_id",
        "edits",
        "section_title",
        "new_content",
        "action",
        "instructions",
        "content",
    ]

    def __init__(self, file_adapter: Optional[DevFileServiceAdapter] = None) -> None:
        self.file_adapter = file_adapter
        self.renderer = MarkdownDocumentRenderer()
        self.parser = MarkdownDocumentParser()

    def validate_parameters(self, inputs: Dict[str, Any]) -> Optional[str]:
        if "relative_path" not in inputs or not inputs["relative_path"]:
            return "Missing required parameter 'relative_path' for capability 'document_editing'."

        has_edit = any(
            k in inputs and inputs[k] is not None
            for k in ["edits", "section_title", "new_content", "action", "instructions", "content"]
        )
        if not has_edit:
            return "Missing edit specification ('edits', 'action', 'section_title', or 'new_content') for capability 'document_editing'."

        return super().validate_parameters(inputs)

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        rel_path = str(request.inputs.get("relative_path", ""))
        ws_id = str(request.inputs.get("workspace_id", "default") or "default")

        if self.file_adapter is None:
            return CapabilityHandlerOutput(
                success=False,
                output_text="EXECUTION_ERROR: FileService adapter is not available for document editing.",
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
                output_text=f"DOCUMENT_NOT_FOUND: Could not read target document '{rel_path}': {err_msg}",
                errors=[f"Target file '{rel_path}' does not exist or cannot be read: {err_msg}"],
            )

        # Parse existing markdown content into Document model
        doc = self.parser.parse(read_res.content)

        # Apply edits
        edits = request.inputs.get("edits")
        action = str(request.inputs.get("action", "")).lower()
        section_title = request.inputs.get("section_title")
        new_content = request.inputs.get("new_content") or request.inputs.get("content")

        applied_actions: List[str] = []

        if isinstance(edits, list):
            for edit_item in edits:
                if isinstance(edit_item, dict):
                    self._apply_single_edit(doc, edit_item, applied_actions)
        elif isinstance(edits, dict):
            self._apply_single_edit(doc, edits, applied_actions)
        else:
            single_spec = {
                "action": action or "append_section",
                "section_title": section_title,
                "new_content": new_content,
            }
            self._apply_single_edit(doc, single_spec, applied_actions)

        # Render updated document
        updated_content = self.renderer.render(doc)

        # Overwrite file via FileService
        write_res = file_service.create_file(rel_path, updated_content, overwrite=True)
        if not write_res.success:
            write_err = write_res.error_message or "Write failed."
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"FILE_WRITE_FAILED: Failed to save edited document: {write_err}",
                errors=[f"Write failed: {write_err}"],
            )

        artifacts: List[str] = []
        additional_evidence: List[Any] = []
        if write_res.artifact:
            artifacts.append(write_res.artifact.artifact_uri)
            additional_evidence.extend(write_res.evidence)

        facts = [
            FactItem(
                statement=f"Applied edits to '{rel_path}': {', '.join(applied_actions) if applied_actions else 'Updated content'}.",
                state=FactState.FACT,
                source="document_specialist",
            )
        ]

        return CapabilityHandlerOutput(
            success=True,
            output_text=f"Successfully edited document '{rel_path}' with actions: {', '.join(applied_actions) if applied_actions else 'updated'}.",
            facts=facts,
            artifacts=artifacts,
            errors=[],
            additional_evidence=additional_evidence,
        )

    def _apply_single_edit(
        self, doc: Document, edit: Dict[str, Any], applied_actions: List[str]
    ) -> None:
        action = str(edit.get("action", "append_section")).lower()
        sec_title = edit.get("section_title") or edit.get("title")
        content = edit.get("new_content") or edit.get("content")

        if action in ("append_section", "add_section"):
            title = str(sec_title or f"Section {len(doc.sections) + 1}")
            sec = DocumentSection(title=title, level=int(edit.get("level", 2)))
            if content:
                sec.add_block(ParagraphBlock(text=str(content)))
            doc.add_section(sec)
            applied_actions.append(f"appended section '{title}'")

        elif action in ("update_section", "replace_section"):
            if not sec_title:
                return
            target_title = str(sec_title).strip().lower()
            matched = False
            for sec in doc.sections:
                if sec.title.strip().lower() == target_title:
                    if "new_title" in edit:
                        sec.title = str(edit["new_title"])
                    if content:
                        sec.blocks = [ParagraphBlock(text=str(content))]
                    matched = True
                    applied_actions.append(f"updated section '{sec.title}'")
                    break
            if not matched and content:
                new_sec = DocumentSection(title=str(sec_title), level=int(edit.get("level", 2)))
                new_sec.add_block(ParagraphBlock(text=str(content)))
                doc.add_section(new_sec)
                applied_actions.append(f"created new section '{sec_title}'")

        elif action in ("append_paragraph", "add_paragraph"):
            if content:
                p = ParagraphBlock(text=str(content))
                if sec_title:
                    target_title = str(sec_title).strip().lower()
                    for sec in doc.sections:
                        if sec.title.strip().lower() == target_title:
                            sec.add_block(p)
                            applied_actions.append(f"added paragraph to section '{sec.title}'")
                            break
                else:
                    doc.add_block(p)
                    applied_actions.append("added root paragraph")

        elif action in ("set_title", "rename_title"):
            if "title" in edit:
                doc.title = str(edit["title"])
                applied_actions.append(f"renamed document title to '{doc.title}'")


class DocumentValidationCapabilityHandler(BaseCapabilityHandler):
    """
    Approved Capability Handler for validating document structure, hierarchy, and schema compliance.
    """

    capability_name = "document_validation"
    required_tool = "document_validator"
    required_params = ["document"]
    allowed_params = ["document", "doc", "min_sections", "min_blocks", "require_headings", "max_sections"]

    def validate_parameters(self, inputs: Dict[str, Any]) -> Optional[str]:
        if "document" not in inputs and "doc" in inputs:
            inputs["document"] = inputs["doc"]
        if "document" not in inputs or inputs["document"] is None:
            return "Missing required parameter 'document' for capability 'document_validation'."
        return super().validate_parameters(inputs)

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        raw_doc = request.inputs.get("document")
        min_sections = int(request.inputs.get("min_sections", 0))
        max_sections = int(request.inputs.get("max_sections", 1000))
        min_blocks = int(request.inputs.get("min_blocks", 0))
        require_headings = bool(request.inputs.get("require_headings", False))

        errors: List[str] = []

        if isinstance(raw_doc, Document):
            doc = raw_doc
        elif isinstance(raw_doc, dict):
            try:
                doc = Document.model_validate(raw_doc)
            except Exception as e:
                return CapabilityHandlerOutput(
                    success=False,
                    output_text=f"VALIDATION_FAILED: Invalid document schema: {str(e)}",
                    errors=[f"Schema decoding error: {str(e)}"],
                )
        else:
            return CapabilityHandlerOutput(
                success=False,
                output_text="VALIDATION_FAILED: Input 'document' must be a Document model or dictionary.",
                errors=["Invalid document object type."],
            )

        # Rule 1: Title non-empty
        if not doc.title or not doc.title.strip():
            errors.append("Document title is empty.")

        # Rule 2: Section count bounds
        if len(doc.sections) < min_sections:
            errors.append(
                f"Document has {len(doc.sections)} section(s), below minimum required {min_sections}."
            )
        if len(doc.sections) > max_sections:
            errors.append(
                f"Document has {len(doc.sections)} section(s), exceeding maximum allowed {max_sections}."
            )

        # Rule 3: Total block count
        total_blocks = len(doc.blocks) + sum(len(s.blocks) for s in doc.sections)
        if total_blocks < min_blocks:
            errors.append(
                f"Document has {total_blocks} total block(s), below minimum required {min_blocks}."
            )

        # Rule 4: Heading requirement
        if require_headings:
            has_heading = len(doc.sections) > 0 or any(
                isinstance(b, HeadingBlock) for b in doc.blocks
            )
            if not has_heading:
                errors.append("Document lacks required section headings or heading blocks.")

        # Rule 5: Section integrity
        seen_section_ids = set()
        for idx, sec in enumerate(doc.sections):
            if not sec.title or not sec.title.strip():
                errors.append(f"Section at index {idx} has an empty title.")
            if sec.section_id in seen_section_ids:
                errors.append(f"Duplicate section_id '{sec.section_id}' detected at index {idx}.")
            seen_section_ids.add(sec.section_id)

        if errors:
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"Document validation failed with {len(errors)} error(s).",
                errors=errors,
            )

        verif_ev = VerificationEvidence(
            evidence_id=f"ev-doc-verif-{request.delegation_id[:8]}",
            verifier_id="document_validator",
            verified_status="VERIFIED",
            description=f"Verified document '{doc.title}' containing {len(doc.sections)} sections and {total_blocks} blocks.",
        )

        facts = [
            FactItem(
                statement=f"Validated document '{doc.title}' ({len(doc.sections)} sections, {total_blocks} blocks) with zero structural errors.",
                state=FactState.FACT,
                source="document_validator",
            )
        ]

        return CapabilityHandlerOutput(
            success=True,
            output_text=f"Document '{doc.title}' successfully verified ({len(doc.sections)} sections, {total_blocks} blocks).",
            facts=facts,
            artifacts=[],
            errors=[],
            additional_evidence=[verif_ev],
        )

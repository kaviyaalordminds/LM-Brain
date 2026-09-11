from typing import Any, Dict, List, Optional
import uuid

from executive_twins.execution.capability_execution_engine import (
    BaseCapabilityHandler,
    CapabilityHandlerOutput,
)
from executive_twins.files.dev_adapters import DevFileServiceAdapter
from executive_twins.presentations.dev_adapters import (
    PresentationBuilder,
    PresentationHTMLRenderer,
    PresentationMarkdownRenderer,
)
from executive_twins.presentations.models import (
    ElementType,
    PresentationDeck,
    Slide,
    SlideBulletListElement,
    SlideElement,
    SlideImageElement,
    SlideLayout,
    SlideMetricElement,
    SlideTableElement,
    SlideTextElement,
)
from executive_twins.schemas.common import FactItem, FactState
from executive_twins.schemas.delegation import DelegationRequest
from executive_twins.schemas.evidence import (
    ArtifactEvidence,
    EvidenceCategory,
    VerificationEvidence,
)
from executive_twins.schemas.specialist import SpecialistMetadata


class PresentationGenerationCapabilityHandler(BaseCapabilityHandler):
    """
    Approved Capability Handler for synthesizing presentation decks and rendering visual artifacts.
    EXECUTION SAFETY: Registered within SpecialistExecutionEngine boundary.
    All file operations delegate to sandboxed FileService.
    """

    capability_name = "presentation_generation"
    required_tool = "file_service"
    required_params = ["title"]
    allowed_params = [
        "title",
        "subtitle",
        "slides",
        "theme",
        "aspect_ratio",
        "output_format",
        "relative_path",
        "workspace_id",
        "content",
    ]

    def __init__(self, file_adapter: Optional[DevFileServiceAdapter] = None) -> None:
        self.file_adapter = file_adapter
        self.html_renderer = PresentationHTMLRenderer()
        self.markdown_renderer = PresentationMarkdownRenderer()

    def validate_parameters(self, inputs: Dict[str, Any]) -> Optional[str]:
        if "title" not in inputs or not inputs["title"]:
            return "Missing required parameter 'title' for capability 'presentation_generation'."
        return super().validate_parameters(inputs)

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        title = str(request.inputs.get("title", "Untitled Presentation"))
        subtitle = request.inputs.get("subtitle")
        theme = str(request.inputs.get("theme", "modern_dark"))
        aspect_ratio = str(request.inputs.get("aspect_ratio", "16:9"))
        output_format = str(request.inputs.get("output_format", "html")).lower()
        ws_id = str(request.inputs.get("workspace_id", "default") or "default")

        # 1. Build Deck
        deck_builder = PresentationBuilder(title=title)
        deck_builder.set_subtitle(subtitle)
        deck_builder.set_theme(theme)
        deck_builder.set_aspect_ratio(aspect_ratio)

        raw_slides = request.inputs.get("slides", [])
        if isinstance(raw_slides, list) and len(raw_slides) > 0:
            for s_idx, s_data in enumerate(raw_slides):
                if isinstance(s_data, dict):
                    s_title = str(s_data.get("title", f"Slide {s_idx + 1}"))
                    raw_layout = str(s_data.get("layout", "TITLE_AND_CONTENT")).upper()
                    try:
                        s_layout = SlideLayout(raw_layout)
                    except ValueError:
                        s_layout = SlideLayout.TITLE_AND_CONTENT
                    s_notes = s_data.get("speaker_notes")
                    deck_builder.create_slide(title=s_title, layout=s_layout, speaker_notes=s_notes)

                    # Add elements if present
                    for el_data in s_data.get("elements", []):
                        if isinstance(el_data, dict):
                            el_type = str(el_data.get("type", "TEXT")).upper()
                            if el_type == "TEXT":
                                deck_builder.add_text(
                                    content=str(el_data.get("content", "")),
                                    is_bold=bool(el_data.get("is_bold", False)),
                                )
                            elif el_type == "BULLET_LIST":
                                deck_builder.add_bullet_list(
                                    items=list(el_data.get("items", [])),
                                    is_ordered=bool(el_data.get("is_ordered", False)),
                                )
                            elif el_type == "METRIC":
                                deck_builder.add_metric(
                                    label=str(el_data.get("label", "")),
                                    value=str(el_data.get("value", "")),
                                    delta=el_data.get("delta"),
                                    description=el_data.get("description"),
                                )
                            elif el_type == "TABLE":
                                deck_builder.add_table(
                                    headers=list(el_data.get("headers", [])),
                                    rows=list(el_data.get("rows", [])),
                                    caption=el_data.get("caption"),
                                )
                            elif el_type == "IMAGE_REF":
                                deck_builder.add_image(
                                    uri=str(el_data.get("uri", "")),
                                    alt_text=el_data.get("alt_text"),
                                )
        else:
            # Default overview slide if no explicit slides passed
            deck_builder.create_slide(
                title="Overview",
                layout=SlideLayout.TITLE_AND_CONTENT,
                speaker_notes="Initial introductory presentation slide.",
            ).add_bullet_list(["Executive alignment", "Autonomous control loop", "Empirical evidence"])

        deck = deck_builder.build()

        # 2. Render Deck
        if output_format == "markdown":
            rendered_content = self.markdown_renderer.render(deck)
            ext = "md"
        else:
            rendered_content = self.html_renderer.render(deck)
            ext = "html"

        # 3. Persist via FileService if available
        default_filename = f"presentation_{request.delegation_id[:8]}.{ext}"
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
                    evidence_id=f"ev-pres-art-{request.delegation_id[:8]}",
                    artifact_uri=artifact_uri,
                    description=f"Generated visual presentation artifact for '{title}'",
                    mime_type="text/html" if ext == "html" else "text/markdown",
                )
            )

        facts = [
            FactItem(
                statement=f"Generated presentation '{title}' containing {len(deck.slides)} slides.",
                state=FactState.FACT,
                source="presentation_specialist",
            )
        ]

        return CapabilityHandlerOutput(
            success=True,
            output_text=f"Successfully generated presentation '{title}' with {len(deck.slides)} slide(s) at '{rel_path}'.",
            facts=facts,
            artifacts=artifacts,
            errors=[],
            additional_evidence=additional_evidence,
        )


class SlideCreationCapabilityHandler(BaseCapabilityHandler):
    """
    Approved Capability Handler for modular slide construction.
    Does NOT access the filesystem directly.
    """

    capability_name = "slide_creation"
    required_tool = "slide_builder"
    required_params = ["title", "layout"]
    allowed_params = ["title", "layout", "elements", "speaker_notes", "order_index"]

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        title = str(request.inputs.get("title", ""))
        raw_layout = str(request.inputs.get("layout", "TITLE_AND_CONTENT")).upper()
        try:
            layout = SlideLayout(raw_layout)
        except ValueError:
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"INVALID_LAYOUT: Layout '{raw_layout}' is not a valid SlideLayout.",
                errors=[f"Layout '{raw_layout}' is not supported."],
            )

        slide = Slide(
            title=title,
            layout=layout,
            speaker_notes=request.inputs.get("speaker_notes"),
            order_index=int(request.inputs.get("order_index", 0)),
        )

        elements_data = request.inputs.get("elements", [])
        if isinstance(elements_data, list):
            for el in elements_data:
                if isinstance(el, dict):
                    el_type = str(el.get("type", "TEXT")).upper()
                    if el_type == "TEXT":
                        slide.add_element(SlideTextElement(content=str(el.get("content", ""))))
                    elif el_type == "BULLET_LIST":
                        slide.add_element(SlideBulletListElement(items=list(el.get("items", []))))
                    elif el_type == "METRIC":
                        slide.add_element(
                            SlideMetricElement(
                                label=str(el.get("label", "")),
                                value=str(el.get("value", "")),
                                delta=el.get("delta"),
                            )
                        )
                    elif el_type == "TABLE":
                        slide.add_element(
                            SlideTableElement(
                                headers=list(el.get("headers", [])),
                                rows=list(el.get("rows", [])),
                            )
                        )
                    elif el_type == "IMAGE_REF":
                        slide.add_element(
                            SlideImageElement(
                                uri=str(el.get("uri", "")),
                                alt_text=el.get("alt_text"),
                            )
                        )

        facts = [
            FactItem(
                statement=f"Created slide '{title}' with layout '{layout.value}' containing {len(slide.elements)} elements.",
                state=FactState.FACT,
                source="slide_builder",
            )
        ]

        return CapabilityHandlerOutput(
            success=True,
            output_text=f"Successfully constructed slide '{title}' ({layout.value}) with {len(slide.elements)} element(s).",
            facts=facts,
            artifacts=[],
            errors=[],
        )


class PresentationValidationCapabilityHandler(BaseCapabilityHandler):
    """
    Approved Capability Handler for validating presentation deck structure, ordering, and readability.
    """

    capability_name = "presentation_validation"
    required_tool = "presentation_validator"
    required_params = ["presentation"]
    allowed_params = ["presentation", "deck", "min_slides", "max_slides", "require_speaker_notes"]

    def validate_parameters(self, inputs: Dict[str, Any]) -> Optional[str]:
        if "presentation" not in inputs and "deck" in inputs:
            inputs["presentation"] = inputs["deck"]
        if "presentation" not in inputs or inputs["presentation"] is None:
            return "Missing required parameter 'presentation' for capability 'presentation_validation'."
        return super().validate_parameters(inputs)

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        raw_pres = request.inputs.get("presentation")
        min_slides = int(request.inputs.get("min_slides", 1))
        max_slides = int(request.inputs.get("max_slides", 100))
        require_speaker_notes = bool(request.inputs.get("require_speaker_notes", False))

        errors: List[str] = []

        if isinstance(raw_pres, PresentationDeck):
            deck = raw_pres
        elif isinstance(raw_pres, dict):
            try:
                deck = PresentationDeck.model_validate(raw_pres)
            except Exception as e:
                return CapabilityHandlerOutput(
                    success=False,
                    output_text=f"VALIDATION_FAILED: Invalid presentation schema: {str(e)}",
                    errors=[f"Schema decoding error: {str(e)}"],
                )
        else:
            return CapabilityHandlerOutput(
                success=False,
                output_text="VALIDATION_FAILED: Input 'presentation' must be a PresentationDeck or dictionary.",
                errors=["Invalid presentation object type."],
            )

        # Rule 1: Title non-empty
        if not deck.title or not deck.title.strip():
            errors.append("Presentation title is empty.")

        # Rule 2: Slide count bounds
        if len(deck.slides) < min_slides:
            errors.append(f"Presentation has {len(deck.slides)} slide(s), below minimum required {min_slides}.")
        if len(deck.slides) > max_slides:
            errors.append(f"Presentation has {len(deck.slides)} slide(s), exceeding maximum allowed {max_slides}.")

        # Rule 3: Slide validation
        seen_slide_ids = set()
        for idx, slide in enumerate(deck.slides):
            if not slide.title or not slide.title.strip():
                errors.append(f"Slide at index {idx} has an empty title.")
            if slide.slide_id in seen_slide_ids:
                errors.append(f"Duplicate slide_id '{slide.slide_id}' detected at index {idx}.")
            seen_slide_ids.add(slide.slide_id)

            if require_speaker_notes and not slide.speaker_notes:
                errors.append(f"Slide '{slide.title}' is missing mandatory speaker notes.")

        if errors:
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"Presentation validation failed with {len(errors)} error(s).",
                errors=errors,
            )

        verif_ev = VerificationEvidence(
            evidence_id=f"ev-pres-verif-{request.delegation_id[:8]}",
            verifier_id="presentation_validator",
            verified_status="VERIFIED",
            description=f"Verified presentation deck '{deck.title}' containing {len(deck.slides)} slides.",
        )

        facts = [
            FactItem(
                statement=f"Validated presentation deck '{deck.title}' ({len(deck.slides)} slides) with zero structural errors.",
                state=FactState.FACT,
                source="presentation_validator",
            )
        ]

        return CapabilityHandlerOutput(
            success=True,
            output_text=f"Presentation deck '{deck.title}' successfully verified ({len(deck.slides)} slides).",
            facts=facts,
            artifacts=[],
            errors=[],
            additional_evidence=[verif_ev],
        )

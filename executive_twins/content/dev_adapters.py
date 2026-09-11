import html
import re
from typing import Any, Dict, List, Optional
import uuid

from executive_twins.content.interfaces import (
    IContentBuilder,
    IContentRenderer,
    IContentSpecialist,
    IContentValidator,
)
from executive_twins.content.models import (
    Channel,
    ContentBrief,
    ContentMetadata,
    ContentPiece,
    ContentReviewResult,
    ContentType,
    Tone,
)
from executive_twins.schemas.common import SpecialistStatus
from executive_twins.schemas.specialist import (
    Capability,
    RegistryProvenance,
    SpecialistMetadata,
)


class ContentBuilder(IContentBuilder):
    """
    Pure-Python deterministic builder assembling ContentPiece models from briefs or specifications.
    """

    def __init__(self, brief: Optional[ContentBrief] = None) -> None:
        self._brief: Optional[ContentBrief] = brief
        self._title: Optional[str] = None
        self._body: Optional[str] = None
        self._sections: Dict[str, str] = {}
        self._call_to_action: Optional[str] = None
        self._metadata: Optional[ContentMetadata] = None

        if brief:
            self.set_brief(brief)

    def set_brief(self, brief: ContentBrief) -> "ContentBuilder":
        self._brief = brief
        self._metadata = ContentMetadata(
            content_type=brief.content_type,
            channel=brief.channel,
            tone=brief.tone,
            target_audience=brief.target_audience,
        )
        self._call_to_action = brief.call_to_action
        return self

    def set_title(self, title: str) -> "ContentBuilder":
        self._title = title.strip() if title else None
        return self

    def set_body(self, body: str) -> "ContentBuilder":
        self._body = body.strip() if body else None
        return self

    def add_section(self, heading: str, text: str) -> "ContentBuilder":
        self._sections[heading.strip()] = text.strip()
        return self

    def set_call_to_action(self, cta: str) -> "ContentBuilder":
        self._call_to_action = cta.strip() if cta else None
        return self

    def build(self) -> ContentPiece:
        if self._metadata is None:
            self._metadata = ContentMetadata()

        # If body was not explicitly set, deterministically synthesize it from brief
        if not self._body:
            self._body = self._synthesize_body_from_brief()

        if not self._title and self._brief:
            self._title = f"{self._brief.content_type.value.replace('_', ' ').title()}: {self._brief.purpose}"

        if self._title:
            self._metadata.title = self._title

        return ContentPiece(
            metadata=self._metadata,
            title=self._title,
            body=self._body,
            sections=dict(self._sections),
            call_to_action=self._call_to_action,
        )

    def _synthesize_body_from_brief(self) -> str:
        if not self._brief:
            return "Generated content piece."

        lines: List[str] = []
        lines.append(f"**Objective**: {self._brief.purpose}")
        lines.append(f"**Target Audience**: {self._brief.target_audience}")
        lines.append(f"**Tone**: {self._brief.tone.value}")

        if self._brief.key_points:
            lines.append("\n**Key Highlights**:")
            for kp in self._brief.key_points:
                lines.append(f"- {kp}")

        if self._brief.content_type == ContentType.SOCIAL_POST:
            lines.append("\n#AutonomousWorkforce #Innovation #Leadership")
        elif self._brief.content_type == ContentType.PRESS_RELEASE:
            lines.append("\nFOR IMMEDIATE RELEASE — Autonomous AI Workforce Milestone.")
        elif self._brief.content_type == ContentType.EMAIL:
            lines.append("\nDear Colleague,\nWe are pleased to share our latest strategic updates.")

        return "\n".join(lines)

    def reset(self) -> "ContentBuilder":
        self._brief = None
        self._title = None
        self._body = None
        self._sections = {}
        self._call_to_action = None
        self._metadata = None
        return self


class MarkdownContentRenderer(IContentRenderer):
    """
    Pure-Python deterministic renderer that converts ContentPiece models into Markdown text.
    """

    def render(self, content_piece: ContentPiece) -> str:
        lines: List[str] = []

        if content_piece.title:
            lines.append(f"# {content_piece.title}\n")

        lines.append(
            f"> **Type**: `{content_piece.metadata.content_type.value}` | "
            f"**Channel**: `{content_piece.metadata.channel.value}` | "
            f"**Tone**: `{content_piece.metadata.tone.value}` | "
            f"**Audience**: {content_piece.metadata.target_audience}\n"
        )

        lines.append(content_piece.body + "\n")

        for heading, sec_text in content_piece.sections.items():
            lines.append(f"## {heading}\n\n{sec_text}\n")

        if content_piece.call_to_action:
            lines.append(f"**Call to Action**: {content_piece.call_to_action}\n")

        return "\n".join(lines).strip() + "\n"


class HTMLContentRenderer(IContentRenderer):
    """
    Pure-Python deterministic renderer that converts ContentPiece models into sanitized HTML.
    """

    def render(self, content_piece: ContentPiece) -> str:
        safe_title = html.escape(content_piece.title or "Content Asset")
        safe_type = html.escape(content_piece.metadata.content_type.value)
        safe_channel = html.escape(content_piece.metadata.channel.value)
        safe_tone = html.escape(content_piece.metadata.tone.value)
        safe_audience = html.escape(content_piece.metadata.target_audience)
        safe_body = html.escape(content_piece.body).replace("\n", "<br/>")

        sections_html = ""
        for h, text in content_piece.sections.items():
            sections_html += (
                f"<div class='content-section'><h3>{html.escape(h)}</h3>"
                f"<p>{html.escape(text).replace(chr(10), '<br/>')}</p></div>"
            )

        cta_html = ""
        if content_piece.call_to_action:
            safe_cta = html.escape(content_piece.call_to_action)
            cta_html = f"<div class='cta-box'><strong>Call to Action:</strong> {safe_cta}</div>"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{safe_title}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; padding: 2rem; color: #1e293b; background: #f8fafc; }}
    .card {{ background: #ffffff; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); max-width: 800px; margin: 0 auto; }}
    .meta-bar {{ font-size: 0.875rem; color: #64748b; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid #e2e8f0; }}
    .cta-box {{ margin-top: 2rem; padding: 1rem; background: #e0f2fe; border-left: 4px solid #0284c7; border-radius: 4px; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>{safe_title}</h1>
    <div class="meta-bar">
      <span>Type: <strong>{safe_type}</strong></span> |
      <span>Channel: <strong>{safe_channel}</strong></span> |
      <span>Tone: <strong>{safe_tone}</strong></span> |
      <span>Audience: <strong>{safe_audience}</strong></span>
    </div>
    <div class="body-content">{safe_body}</div>
    {sections_html}
    {cta_html}
  </div>
</body>
</html>
"""


class DeterministicContentValidator(IContentValidator):
    """
    Deterministic validator checking structural consistency, key point representation,
    and call to action constraints.
    """

    def validate(
        self,
        content_piece: ContentPiece,
        brief: Optional[ContentBrief] = None,
    ) -> ContentReviewResult:
        issues: List[str] = []
        warnings: List[str] = []
        suggestions: List[str] = []
        checks: List[str] = []

        # Check 1: Body non-empty
        checks.append("check_body_non_empty")
        if not content_piece.body or not content_piece.body.strip():
            issues.append("ContentPiece body is empty.")

        # Check 2: Minimum length
        checks.append("check_minimum_length")
        if len(content_piece.body.strip()) < 10:
            issues.append("Content body is too short (minimum 10 characters required).")

        # Check 3: Brief key points representation
        if brief and brief.key_points:
            checks.append("check_brief_key_points")
            body_lower = content_piece.body.lower()
            missing_points = []
            for kp in brief.key_points:
                # Check for significant words from key point in body
                words = [w.lower() for w in re.findall(r"\b\w+\b", kp) if len(w) > 3]
                if words and not any(w in body_lower for w in words):
                    missing_points.append(kp)
            if missing_points:
                warnings.append(f"Some key points may not be clearly represented: {', '.join(missing_points)}.")

        # Check 4: CTA requirement
        if brief and brief.call_to_action:
            checks.append("check_cta_presence")
            if not content_piece.call_to_action:
                issues.append(f"Required Call to Action '{brief.call_to_action}' is missing from the content asset.")

        valid = len(issues) == 0
        return ContentReviewResult(
            valid=valid,
            issues=issues,
            warnings=warnings,
            suggestions=suggestions,
            checks_performed=checks,
        )


class DevTestContentAdapter(IContentSpecialist):
    """
    DEV_TEST_ONLY_ADAPTER: Convenience adapter grouping ContentBuilder, Renderers, and Validator.
    Provides complete offline implementation of IContentSpecialist.
    """

    def __init__(self) -> None:
        self.builder = ContentBuilder()
        self.markdown_renderer = MarkdownContentRenderer()
        self.html_renderer = HTMLContentRenderer()
        self.validator = DeterministicContentValidator()

    def generate_content(self, brief: ContentBrief) -> ContentPiece:
        return ContentBuilder(brief=brief).build()

    def edit_content(
        self,
        content_piece: ContentPiece,
        instructions: str,
        edits: Dict[str, Any],
    ) -> ContentPiece:
        action = str(edits.get("action", "replace_text")).lower()

        if action == "replace_text":
            target = str(edits.get("target_text", ""))
            replacement = str(edits.get("replacement_text", ""))
            if target in content_piece.body:
                content_piece.body = content_piece.body.replace(target, replacement)

        elif action in ("append_content", "append_text"):
            extra = str(edits.get("content", edits.get("text", "")))
            if extra:
                content_piece.body += f"\n\n{extra}"

        elif action in ("prepend_content", "prepend_text"):
            prefix = str(edits.get("content", edits.get("text", "")))
            if prefix:
                content_piece.body = f"{prefix}\n\n{content_piece.body}"

        elif action in ("update_title", "set_title"):
            new_title = str(edits.get("title", ""))
            if new_title:
                content_piece.title = new_title
                content_piece.metadata.title = new_title

        elif action in ("update_cta", "set_cta"):
            new_cta = str(edits.get("call_to_action", edits.get("cta", "")))
            if new_cta:
                content_piece.call_to_action = new_cta

        elif action == "normalize_whitespace":
            content_piece.body = re.sub(r"\n{3,}", "\n\n", content_piece.body).strip()

        return content_piece

    def validate_content(
        self,
        content_piece: ContentPiece,
        brief: Optional[ContentBrief] = None,
    ) -> ContentReviewResult:
        return self.validator.validate(content_piece, brief)


def create_content_specialist(
    specialist_id: str = "spec_content_01",
    name: str = "Content Specialist",
    status: SpecialistStatus = SpecialistStatus.ACTIVE,
    security_level: str = "standard",
) -> SpecialistMetadata:
    """
    Factory creating authoritative SpecialistMetadata for the Content Specialist.
    Declares all supported content capabilities and authorized tools into the registry.
    """
    capabilities = [
        Capability(
            name="content_generation",
            description="Controlled synthesis of marketing copy, blog articles, social snippets, and PR announcements",
            required_tools=["file_service"],
        ),
        Capability(
            name="content_editing",
            description="Controlled structured modification, section refinement, and text replacement of content assets",
            required_tools=["file_service"],
        ),
        Capability(
            name="content_validation",
            description="Controlled structural, audience, and brief alignment validation for content assets",
            required_tools=["content_validator"],
        ),
    ]

    return SpecialistMetadata(
        specialist_id=specialist_id,
        name=name,
        capabilities=capabilities,
        status=status,
        authorized_tools=["file_service", "content_builder", "content_renderer", "content_validator"],
        security_level=security_level,
        provenance=RegistryProvenance(
            registry_id="local_dev_registry",
            snapshot_id="snap_content_v1",
        ),
    )

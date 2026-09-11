import html
from typing import Any, Dict, List, Optional
import uuid

from executive_twins.presentations.interfaces import (
    IPresentationBuilder,
    IPresentationRenderer,
    IPresentationSpecialist,
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
from executive_twins.schemas.common import SpecialistStatus
from executive_twins.schemas.specialist import Capability, RegistryProvenance, SpecialistMetadata


class PresentationBuilder(IPresentationBuilder):
    """
    Pure Python in-memory implementation of IPresentationBuilder.
    Provides fluent, deterministic construction of typed PresentationDeck models.
    """

    def __init__(self, title: Optional[str] = None) -> None:
        self._title: str = title or ""
        self._subtitle: Optional[str] = None
        self._aspect_ratio: str = "16:9"
        self._theme: str = "modern_dark"
        self._slides: List[Slide] = []
        self._current_slide: Optional[Slide] = None
        self._metadata: Dict[str, Any] = {}

    def set_title(self, title: str) -> "PresentationBuilder":
        if not title or not title.strip():
            raise ValueError("Presentation title cannot be empty.")
        self._title = title.strip()
        return self

    def set_subtitle(self, subtitle: str) -> "PresentationBuilder":
        self._subtitle = subtitle.strip() if subtitle else None
        return self

    def set_aspect_ratio(self, aspect_ratio: str) -> "PresentationBuilder":
        self._aspect_ratio = aspect_ratio
        return self

    def set_theme(self, theme: str) -> "PresentationBuilder":
        self._theme = theme
        return self

    def add_slide(self, slide: Slide) -> "PresentationBuilder":
        slide.order_index = len(self._slides)
        self._slides.append(slide)
        self._current_slide = slide
        return self

    def create_slide(
        self,
        title: str,
        layout: SlideLayout = SlideLayout.TITLE_AND_CONTENT,
        speaker_notes: Optional[str] = None,
    ) -> "PresentationBuilder":
        slide = Slide(
            title=title,
            layout=layout,
            speaker_notes=speaker_notes,
            order_index=len(self._slides),
        )
        self._slides.append(slide)
        self._current_slide = slide
        return self

    def _ensure_active_slide(self) -> Slide:
        if self._current_slide is None:
            self.create_slide(title="Untitled Slide")
        return self._current_slide

    def add_text(
        self,
        content: str,
        font_size: Optional[str] = None,
        is_bold: bool = False,
    ) -> "PresentationBuilder":
        slide = self._ensure_active_slide()
        el = SlideTextElement(
            content=content,
            font_size=font_size,
            is_bold=is_bold,
            order_index=len(slide.elements),
        )
        slide.elements.append(el)
        return self

    def add_bullet_list(
        self,
        items: List[str],
        is_ordered: bool = False,
    ) -> "PresentationBuilder":
        slide = self._ensure_active_slide()
        el = SlideBulletListElement(
            items=list(items),
            is_ordered=is_ordered,
            order_index=len(slide.elements),
        )
        slide.elements.append(el)
        return self

    def add_table(
        self,
        headers: List[str],
        rows: List[List[Any]],
        caption: Optional[str] = None,
    ) -> "PresentationBuilder":
        slide = self._ensure_active_slide()
        el = SlideTableElement(
            headers=list(headers),
            rows=[list(r) for r in rows],
            caption=caption,
            order_index=len(slide.elements),
        )
        slide.elements.append(el)
        return self

    def add_image(
        self,
        uri: str,
        alt_text: Optional[str] = None,
        caption: Optional[str] = None,
    ) -> "PresentationBuilder":
        slide = self._ensure_active_slide()
        el = SlideImageElement(
            uri=uri,
            alt_text=alt_text,
            caption=caption,
            order_index=len(slide.elements),
        )
        slide.elements.append(el)
        return self

    def add_metric(
        self,
        label: str,
        value: str,
        delta: Optional[str] = None,
        description: Optional[str] = None,
    ) -> "PresentationBuilder":
        slide = self._ensure_active_slide()
        el = SlideMetricElement(
            label=label,
            value=value,
            delta=delta,
            description=description,
            order_index=len(slide.elements),
        )
        slide.elements.append(el)
        return self

    def build(self) -> PresentationDeck:
        if not self._title or not self._title.strip():
            raise ValueError("Cannot build PresentationDeck: title is required and cannot be empty.")

        deck = PresentationDeck(
            title=self._title,
            subtitle=self._subtitle,
            aspect_ratio=self._aspect_ratio,
            theme=self._theme,
            slides=list(self._slides),
            metadata=dict(self._metadata),
        )
        return deck

    def reset(self) -> "PresentationBuilder":
        self._title = ""
        self._subtitle = None
        self._aspect_ratio = "16:9"
        self._theme = "modern_dark"
        self._slides = []
        self._current_slide = None
        self._metadata = {}
        return self


class PresentationMarkdownRenderer(IPresentationRenderer):
    """
    Renders a PresentationDeck into clean, inspectable Markdown slides separated by '---'.
    """

    def render(self, deck: PresentationDeck) -> str:
        lines: List[str] = []

        # 1. Deck Frontmatter
        lines.append("---")
        lines.append(f"marp: true")
        lines.append(f"title: {deck.title}")
        if deck.subtitle:
            lines.append(f"subtitle: {deck.subtitle}")
        lines.append(f"theme: {deck.theme}")
        lines.append(f"aspect_ratio: {deck.aspect_ratio}")
        lines.append("---\n")

        # 2. Title Slide
        lines.append(f"# {deck.title}")
        if deck.subtitle:
            lines.append(f"### {deck.subtitle}")
        lines.append("\n---\n")

        # 3. Slides
        for idx, slide in enumerate(deck.slides, 1):
            lines.append(f"<!-- Slide {idx}: {slide.layout.value} -->")
            lines.append(f"## {slide.title}\n")

            for el in slide.elements:
                if isinstance(el, SlideTextElement):
                    prefix = "**" if el.is_bold else ""
                    suffix = "**" if el.is_bold else ""
                    lines.append(f"{prefix}{el.content}{suffix}\n")

                elif isinstance(el, SlideBulletListElement):
                    for b_idx, item in enumerate(el.items, 1):
                        bullet = f"{b_idx}." if el.is_ordered else "-"
                        lines.append(f"{bullet} {item}")
                    lines.append("")

                elif isinstance(el, SlideMetricElement):
                    delta_str = f" ({el.delta})" if el.delta else ""
                    desc_str = f" - {el.description}" if el.description else ""
                    lines.append(f"> ### {el.value}{delta_str}\n> **{el.label}**{desc_str}\n")

                elif isinstance(el, SlideTableElement):
                    if el.caption:
                        lines.append(f"*{el.caption}*\n")
                    if el.headers:
                        lines.append("| " + " | ".join(el.headers) + " |")
                        lines.append("| " + " | ".join(["---"] * len(el.headers)) + " |")
                    for row in el.rows:
                        lines.append("| " + " | ".join(str(c) for c in row) + " |")
                    lines.append("")

                elif isinstance(el, SlideImageElement):
                    alt = el.alt_text or "slide image"
                    cap = f"\n*{el.caption}*" if el.caption else ""
                    lines.append(f"![{alt}]({el.uri}){cap}\n")

            if slide.speaker_notes:
                lines.append(f"\n<!-- Speaker Notes:\n{slide.speaker_notes}\n-->\n")

            if idx < len(deck.slides):
                lines.append("---\n")

        return "\n".join(lines).strip() + "\n"


class PresentationHTMLRenderer(IPresentationRenderer):
    """
    Renders a PresentationDeck into a self-contained, standalone responsive HTML slide deck.
    Includes modern theme styling, keyboard navigation (left/right arrows), and progress indicator.
    Zero external CDN / network dependencies.
    """

    def render(self, deck: PresentationDeck) -> str:
        escaped_title = html.escape(deck.title)
        escaped_subtitle = html.escape(deck.subtitle or "")

        slides_html: List[str] = []

        # 1. Cover Slide
        cover_html = [
            '<section class="slide title-slide active" data-slide="1">',
            f'  <div class="slide-content">',
            f'    <h1 class="deck-title">{escaped_title}</h1>',
        ]
        if escaped_subtitle:
            cover_html.append(f'    <p class="deck-subtitle">{escaped_subtitle}</p>')
        cover_html.extend([
            f'    <div class="deck-meta">Theme: {deck.theme} | Ratio: {deck.aspect_ratio}</div>',
            '  </div>',
            '</section>',
        ])
        slides_html.append("\n".join(cover_html))

        # 2. Content Slides
        for idx, slide in enumerate(deck.slides, 2):
            slide_num = idx
            layout_cls = f"layout-{slide.layout.value.lower()}"
            s_lines = [
                f'<section class="slide {layout_cls}" data-slide="{slide_num}">',
                '  <div class="slide-content">',
                f'    <h2 class="slide-title">{html.escape(slide.title)}</h2>',
                '    <div class="elements-container">',
            ]

            for el in slide.elements:
                if isinstance(el, SlideTextElement):
                    bold_cls = "bold-text" if el.is_bold else ""
                    s_lines.append(f'      <p class="slide-text {bold_cls}">{html.escape(el.content)}</p>')

                elif isinstance(el, SlideBulletListElement):
                    tag = "ol" if el.is_ordered else "ul"
                    s_lines.append(f'      <{tag} class="slide-list">')
                    for itm in el.items:
                        s_lines.append(f'        <li>{html.escape(itm)}</li>')
                    s_lines.append(f'      </{tag}>')

                elif isinstance(el, SlideMetricElement):
                    delta_html = f'<span class="metric-delta">{html.escape(el.delta)}</span>' if el.delta else ""
                    desc_html = f'<p class="metric-desc">{html.escape(el.description)}</p>' if el.description else ""
                    s_lines.extend([
                        '      <div class="metric-card">',
                        f'        <div class="metric-val">{html.escape(el.value)} {delta_html}</div>',
                        f'        <div class="metric-label">{html.escape(el.label)}</div>',
                        f'        {desc_html}',
                        '      </div>',
                    ])

                elif isinstance(el, SlideTableElement):
                    s_lines.append('      <div class="table-wrapper"><table class="slide-table">')
                    if el.caption:
                        s_lines.append(f'        <caption>{html.escape(el.caption)}</caption>')
                    if el.headers:
                        s_lines.append('        <thead><tr>')
                        for h in el.headers:
                            s_lines.append(f'          <th>{html.escape(str(h))}</th>')
                        s_lines.append('        </tr></thead>')
                    s_lines.append('        <tbody>')
                    for row in el.rows:
                        s_lines.append('          <tr>')
                        for cell in row:
                            s_lines.append(f'            <td>{html.escape(str(cell))}</td>')
                        s_lines.append('          </tr>')
                    s_lines.append('        </tbody>')
                    s_lines.append('      </table></div>')

                elif isinstance(el, SlideImageElement):
                    alt = html.escape(el.alt_text or "slide image")
                    cap = f'<figcaption>{html.escape(el.caption)}</figcaption>' if el.caption else ""
                    s_lines.append(f'      <figure class="slide-img"><img src="{html.escape(el.uri)}" alt="{alt}" />{cap}</figure>')

            s_lines.append('    </div>')

            if slide.speaker_notes:
                s_lines.extend([
                    '    <details class="speaker-notes">',
                    '      <summary>Speaker Notes</summary>',
                    f'      <p>{html.escape(slide.speaker_notes)}</p>',
                    '    </details>',
                ])

            s_lines.append('  </div>')
            s_lines.append('</section>')
            slides_html.append("\n".join(s_lines))

        total_slides = len(deck.slides) + 1

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{escaped_title}</title>
  <style>
    :root {{
      --bg: #0f172a;
      --card-bg: #1e293b;
      --accent: #38bdf8;
      --accent-hover: #0284c7;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --border: #334155;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
    }}
    .presentation-container {{
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 2rem;
      position: relative;
    }}
    .slide {{
      display: none;
      width: 100%;
      max-width: 1100px;
      aspect-ratio: 16 / 9;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 3rem;
      box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5);
      position: relative;
    }}
    .slide.active {{ display: flex; flex-direction: column; }}
    .slide-content {{ flex: 1; display: flex; flex-direction: column; }}
    .deck-title {{ font-size: 3rem; color: var(--accent); margin-bottom: 1rem; }}
    .deck-subtitle {{ font-size: 1.5rem; color: var(--text-muted); margin-bottom: 2rem; }}
    .deck-meta {{ font-size: 0.875rem; color: var(--text-muted); margin-top: auto; }}
    .slide-title {{ font-size: 2rem; color: var(--accent); margin-bottom: 1.5rem; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; }}
    .elements-container {{ flex: 1; display: flex; flex-direction: column; gap: 1rem; justify-content: center; }}
    .slide-text {{ font-size: 1.25rem; line-height: 1.6; }}
    .slide-text.bold-text {{ font-weight: bold; }}
    .slide-list {{ font-size: 1.25rem; line-height: 1.8; padding-left: 2rem; }}
    .metric-card {{ background: rgba(56, 189, 248, 0.1); border: 1px solid var(--accent); border-radius: 8px; padding: 1.5rem; text-align: center; }}
    .metric-val {{ font-size: 2.5rem; font-weight: bold; color: var(--accent); }}
    .metric-delta {{ font-size: 1rem; color: #4ade80; margin-left: 0.5rem; }}
    .metric-label {{ font-size: 1.125rem; color: var(--text); margin-top: 0.5rem; }}
    .metric-desc {{ font-size: 0.875rem; color: var(--text-muted); margin-top: 0.25rem; }}
    .slide-table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
    .slide-table th, .slide-table td {{ border: 1px solid var(--border); padding: 0.75rem 1rem; text-align: left; }}
    .slide-table th {{ background: rgba(255,255,255,0.05); color: var(--accent); }}
    .speaker-notes {{ margin-top: auto; padding-top: 1rem; font-size: 0.875rem; color: var(--text-muted); }}
    .nav-controls {{ display: flex; align-items: center; justify-content: center; gap: 1.5rem; padding: 1rem; background: #0b1120; border-top: 1px solid var(--border); }}
    .nav-btn {{ background: var(--card-bg); color: var(--text); border: 1px solid var(--border); padding: 0.5rem 1.25rem; border-radius: 6px; cursor: pointer; font-size: 0.875rem; font-weight: 600; }}
    .nav-btn:hover {{ background: var(--accent-hover); }}
    .progress {{ font-size: 0.875rem; color: var(--text-muted); }}
  </style>
</head>
<body>
  <div class="presentation-container">
    {''.join(slides_html)}
  </div>
  <div class="nav-controls">
    <button class="nav-btn" id="prev-btn" onclick="prevSlide()">&#8592; Previous</button>
    <span class="progress" id="slide-num">Slide 1 of {total_slides}</span>
    <button class="nav-btn" id="next-btn" onclick="nextSlide()">Next &#8594;</button>
  </div>
  <script>
    let current = 1;
    const total = {total_slides};
    function showSlide(n) {{
      const slides = document.querySelectorAll('.slide');
      slides.forEach(s => s.classList.remove('active'));
      const target = document.querySelector(`.slide[data-slide="${{n}}"]`);
      if (target) {{ target.classList.add('active'); }}
      document.getElementById('slide-num').innerText = `Slide ${{n}} of ${{total}}`;
    }}
    function nextSlide() {{ if (current < total) {{ current++; showSlide(current); }} }}
    function prevSlide() {{ if (current > 1) {{ current--; showSlide(current); }} }}
    document.addEventListener('keydown', e => {{
      if (e.key === 'ArrowRight' || e.key === ' ') {{ nextSlide(); }}
      else if (e.key === 'ArrowLeft') {{ prevSlide(); }}
    }});
  </script>
</body>
</html>
"""


class DevTestPresentationAdapter:
    """
    DEV_TEST_ONLY_ADAPTER: Convenience adapter grouping PresentationBuilder and Renderers.
    """

    def __init__(self) -> None:
        self.builder = PresentationBuilder()
        self.html_renderer = PresentationHTMLRenderer()
        self.markdown_renderer = PresentationMarkdownRenderer()

    def create_simple_deck(self, title: str, slide_title: str, bullet_items: List[str]) -> PresentationDeck:
        return (
            PresentationBuilder(title=title)
            .create_slide(title=slide_title, layout=SlideLayout.TITLE_AND_CONTENT)
            .add_bullet_list(bullet_items)
            .build()
        )


def create_presentation_specialist(
    specialist_id: str = "spec_presentation_01",
    name: str = "Presentation Specialist",
    status: SpecialistStatus = SpecialistStatus.ACTIVE,
    security_level: str = "standard",
) -> SpecialistMetadata:
    """
    Factory creating authoritative SpecialistMetadata for the Presentation Specialist.
    Declares all supported presentation capabilities and authorized tools into the registry.
    """
    capabilities = [
        Capability(
            name="presentation_generation",
            description="Controlled synthesis of structured presentation decks and offline visual artifacts",
            required_tools=["file_service"],
        ),
        Capability(
            name="slide_creation",
            description="Controlled construction of modular slides, layouts, metrics, and tabular components",
            required_tools=["slide_builder"],
        ),
        Capability(
            name="presentation_validation",
            description="Controlled structural, ordering, and readability validation for presentation decks",
            required_tools=["presentation_validator"],
        ),
    ]

    return SpecialistMetadata(
        specialist_id=specialist_id,
        name=name,
        capabilities=capabilities,
        status=status,
        authorized_tools=["file_service", "slide_builder", "presentation_validator"],
        security_level=security_level,
        provenance=RegistryProvenance(
            source_registry="local_dev_registry",
            snapshot_id="snap_presentation_v1",
        ),
    )

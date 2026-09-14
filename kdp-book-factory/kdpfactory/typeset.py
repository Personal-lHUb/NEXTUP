"""Impaginazione dell'interno: da Markdown a PDF pronto per la stampa KDP.

Scelte tipografiche:
- margini speculari (il margine interno cambia lato tra pagina pari e dispari);
- ogni capitolo si apre su pagina dispari, con eventuale pagina bianca prima;
- testatine: titolo del libro sulle pari, titolo del capitolo sulle dispari,
  soppresse sulle pagine di apertura e sulle bianche;
- numerazione araba assoluta, assente nelle pagine preliminari;
- font TrueType incorporati (requisito KDP).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    ActionFlowable,
    BaseDocTemplate,
    Flowable,
    Frame,
    HRFlowable,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

from . import kdpspecs, mdlite
from .i18n import L
from .models import BookSpec, Outline
from .typography import enable_hyphenation, register_family, set_default_canvas_font

INCH = kdpspecs.INCH


def draw_tracked_string(canvas, x, y, text, font, size, tracking, align="left") -> None:
    """Disegna testo con spaziatura fra i caratteri (tracking).

    Il canvas non espone `setCharSpace`: si passa da un text object.
    """
    from reportlab.pdfbase import pdfmetrics

    width = pdfmetrics.stringWidth(text, font, size) + tracking * max(len(text) - 1, 0)
    if align == "center":
        x -= width / 2.0
    elif align == "right":
        x -= width
    text_object = canvas.beginText(x, y)
    text_object.setFont(font, size)
    text_object.setCharSpace(tracking)
    text_object.textOut(text)
    canvas.drawText(text_object)


# --------------------------------------------------------------------------
# Flowable di servizio
# --------------------------------------------------------------------------
class DocAction(ActionFlowable):
    """Esegue un'azione sul documento durante l'impaginazione."""

    def __init__(self, action: str, value=None):
        ActionFlowable.__init__(self)
        self.action = action
        self.value = value

    def apply(self, doc):  # noqa: D102
        if self.action == "body_start":
            doc.in_front_matter = False
            doc.body_start_page = doc.page
        elif self.action == "chapter_open":
            doc.current_chapter = self.value or ""
            doc.plain_pages.add(doc.page)
        elif self.action == "front_matter_page":
            doc.plain_pages.add(doc.page)


class StartOnRecto(ActionFlowable):
    """Salta alla prossima pagina dispari (destra), inserendo una bianca se serve."""

    def apply(self, doc):  # noqa: D102
        # `handle_pageBreak` chiude la pagina corrente e *appende* l'inizio della
        # successiva: al momento della chiamata `doc.page` è ancora la pagina in
        # corso, quindi il contenuto finirà su `doc.page + 1`.
        doc.handle_pageBreak()
        if doc.page % 2 == 1:  # la prossima sarebbe pari (sinistra): inserisci una bianca
            doc.handle_pageBreak()


class BlankFiller(Flowable):
    """Occupa una pagina senza disegnare nulla (pagina bianca finale)."""

    def wrap(self, avail_width, avail_height):
        return 0, 0

    def draw(self):  # pragma: no cover - non disegna niente
        return


class ChapterNumber(Flowable):
    """Numero di capitolo tracciato, sopra il titolo."""

    def __init__(self, text: str, font: str, size: float, color):
        Flowable.__init__(self)
        self.text = text
        self.font = font
        self.size = size
        self.color = color
        self.width = 0
        self.height = size * 1.8

    def wrap(self, avail_width, avail_height):
        self.width = avail_width
        return avail_width, self.height

    def draw(self):
        canvas = self.canv
        canvas.saveState()
        canvas.setFillColor(self.color)
        draw_tracked_string(
            canvas,
            self.width / 2.0,
            self.size * 0.6,
            self.text.upper(),
            self.font,
            self.size,
            self.size * 0.18,
            align="center",
        )
        canvas.restoreState()


# --------------------------------------------------------------------------
# Documento
# --------------------------------------------------------------------------
class InteriorDoc(BaseDocTemplate):
    def __init__(self, filename: str, spec: BookSpec, geo: kdpspecs.PageGeometry, styles: dict):
        BaseDocTemplate.__init__(
            self,
            filename,
            pagesize=(geo.page_width, geo.page_height),
            title=spec.title,
            author=spec.author,
            subject=spec.subtitle or spec.topic,
            creator="kdp-book-factory",
            leftMargin=geo.inner_margin,
            rightMargin=geo.outer_margin,
            topMargin=geo.top_margin,
            bottomMargin=geo.bottom_margin,
            allowSplitting=1,
        )
        self.spec = spec
        self.geo = geo
        self.styles = styles
        self.toc_entries: list[tuple[int, str, int]] = []
        self.chapter_pages: dict[str, int] = {}
        self._reset_state()

        frame_recto = Frame(
            geo.inner_margin, geo.bottom_margin, geo.text_width, geo.text_height, id="recto"
        )
        frame_verso = Frame(
            geo.outer_margin, geo.bottom_margin, geo.text_width, geo.text_height, id="verso"
        )
        self.addPageTemplates(
            [
                PageTemplate(id="recto", frames=[frame_recto], onPageEnd=self._decorate),
                PageTemplate(id="verso", frames=[frame_verso], onPageEnd=self._decorate),
            ]
        )

    # -- stato -----------------------------------------------------------
    def _reset_state(self) -> None:
        self.in_front_matter = True
        self.body_start_page = 1
        self.current_chapter = ""
        self.page_has_content = False
        self.plain_pages: set[int] = set()

    def handle_documentBegin(self):  # noqa: D102
        self._reset_state()
        BaseDocTemplate.handle_documentBegin(self)

    def handle_pageBegin(self):  # noqa: D102
        self._handle_pageBegin()
        # Margini speculari: la pagina successiva usa il template della sua parità.
        self.handle_nextPageTemplate("verso" if (self.page + 1) % 2 == 0 else "recto")

    def afterFlowable(self, flowable):  # noqa: D102
        if isinstance(flowable, (Paragraph, ChapterNumber, HRFlowable)):
            self.page_has_content = True
        if isinstance(flowable, Paragraph):
            style_name = getattr(flowable.style, "name", "")
            if style_name == "ChapterTitle":
                text = flowable.getPlainText()
                self.notify("TOCEntry", (0, text, self.page))
                self.chapter_pages[text] = self.page
            elif style_name == "Heading2" and self.spec.toc_depth >= 2:
                self.notify("TOCEntry", (1, flowable.getPlainText(), self.page))

    # -- testatine e folio ------------------------------------------------
    def _decorate(self, canvas, doc):
        if not self.page_has_content:
            self.page_has_content = False
            return  # pagina bianca: niente testatina, niente numero
        if not self.in_front_matter and self.page not in self.plain_pages:
            self._draw_running_head(canvas)
            self._draw_folio(canvas)
        self.page_has_content = False

    def _draw_running_head(self, canvas):
        geo = self.geo
        is_recto = self.page % 2 == 1
        style = self.styles["running_head"]
        text = self.current_chapter if is_recto else self.spec.title
        if not text:
            return
        y = geo.page_height - geo.top_margin + 0.28 * INCH
        left = geo.inner_margin if is_recto else geo.outer_margin
        canvas.saveState()
        canvas.setFillColor(style.textColor)
        draw_tracked_string(
            canvas,
            left + geo.text_width if is_recto else left,
            y,
            text.upper(),
            style.fontName,
            style.fontSize,
            0.4,
            align="right" if is_recto else "left",
        )
        canvas.restoreState()

    def _draw_folio(self, canvas):
        geo = self.geo
        style = self.styles["folio"]
        canvas.saveState()
        canvas.setFont(style.fontName, style.fontSize)
        canvas.setFillColor(style.textColor)
        canvas.drawCentredString(
            geo.page_width / 2.0, geo.bottom_margin - 0.36 * INCH, str(self.page)
        )
        canvas.restoreState()


# --------------------------------------------------------------------------
# Stili
# --------------------------------------------------------------------------
def build_styles(spec: BookSpec) -> dict[str, ParagraphStyle]:
    body_font = register_family(spec.body_font)
    display_font = register_family("sans" if spec.body_font == "serif" else "serif")
    size = spec.body_font_size
    lead = spec.leading
    ink = colors.HexColor("#111111")
    soft = colors.HexColor("#555555")

    def style(name, **kwargs) -> ParagraphStyle:
        base = dict(
            name=name,
            fontName=body_font,
            # Senza questo ReportLab userebbe Helvetica per i punti elenco:
            # è un font non incorporato e il PDF verrebbe segnalato in preflight.
            bulletFontName=body_font,
            fontSize=size,
            leading=lead,
            textColor=ink,
            alignment=TA_JUSTIFY,
            allowWidows=0,
            allowOrphans=0,
        )
        base.update(kwargs)
        return ParagraphStyle(**base)

    return {
        "body": style("Body", firstLineIndent=0.22 * INCH),
        "body_first": style("BodyFirst", firstLineIndent=0),
        "quote": style(
            "Quote",
            leftIndent=0.28 * INCH,
            rightIndent=0.28 * INCH,
            fontSize=size - 0.5,
            leading=lead - 1,
            textColor=soft,
            spaceBefore=lead * 0.5,
            spaceAfter=lead * 0.5,
            alignment=TA_LEFT,
        ),
        "bullet": style(
            "Bullet",
            leftIndent=0.3 * INCH,
            bulletIndent=0.12 * INCH,
            spaceAfter=lead * 0.18,
            alignment=TA_LEFT,
        ),
        "h2": style(
            "Heading2",
            fontName=display_font,
            fontSize=size + 1.5,
            leading=lead + 2,
            spaceBefore=lead * 1.2,
            spaceAfter=lead * 0.45,
            alignment=TA_LEFT,
            textColor=ink,
        ),
        "h3": style(
            "Heading3",
            fontName=body_font,
            fontSize=size + 0.5,
            leading=lead,
            spaceBefore=lead * 0.9,
            spaceAfter=lead * 0.3,
            alignment=TA_LEFT,
        ),
        "chapter_title": style(
            "ChapterTitle",
            fontName=display_font,
            fontSize=size + 9,
            leading=(size + 9) * 1.2,
            alignment=TA_CENTER,
            spaceBefore=0,
            spaceAfter=lead * 0.6,
        ),
        "title_main": style(
            "TitleMain",
            fontName=display_font,
            fontSize=size + 15,
            leading=(size + 15) * 1.2,
            alignment=TA_CENTER,
        ),
        "title_sub": style(
            "TitleSub",
            fontName=body_font,
            fontSize=size + 2,
            leading=(size + 2) * 1.3,
            alignment=TA_CENTER,
            textColor=soft,
        ),
        "author": style("Author", fontSize=size + 1, alignment=TA_CENTER),
        "front": style("Front", fontSize=size - 1.5, leading=lead - 2, alignment=TA_LEFT),
        "front_center": style(
            "FrontCenter", fontSize=size - 1, leading=lead - 1, alignment=TA_CENTER, textColor=soft
        ),
        "toc_title": style(
            "TocTitle",
            fontName=display_font,
            fontSize=size + 7,
            leading=(size + 7) * 1.2,
            alignment=TA_CENTER,
            spaceAfter=lead * 1.5,
        ),
        "toc1": style("Toc1", alignment=TA_LEFT, fontSize=size, leading=lead * 1.1),
        "toc2": style(
            "Toc2",
            alignment=TA_LEFT,
            fontSize=size - 1,
            leading=lead,
            leftIndent=0.25 * INCH,
            textColor=soft,
        ),
        "running_head": style(
            "RunningHead", fontName=body_font, fontSize=size - 2.5, textColor=soft
        ),
        "folio": style("Folio", fontName=body_font, fontSize=size - 1, textColor=ink),
        "chapter_number": style("ChapterNumber", fontName=display_font, fontSize=size - 2),
    }


# --------------------------------------------------------------------------
# Costruzione della storia
# --------------------------------------------------------------------------
def markdown_to_flowables(
    markdown: str, styles: dict, *, first_paragraph_flush: bool = True
) -> list:
    flowables: list = []
    first_para_done = not first_paragraph_flush
    pending_heading: Paragraph | None = None

    def emit(flowable) -> None:
        """Un titolo non resta mai da solo in fondo alla pagina: viene tenuto
        insieme al primo capoverso che lo segue."""
        nonlocal pending_heading
        if pending_heading is not None:
            flowables.append(KeepTogether([pending_heading, flowable]))
            pending_heading = None
        else:
            flowables.append(flowable)

    for block in mdlite.parse(markdown):
        if isinstance(block, mdlite.Heading):
            if block.level <= 1:
                continue  # il titolo del capitolo è gestito a parte
            style = styles["h2"] if block.level == 2 else styles["h3"]
            if pending_heading is not None:
                flowables.append(pending_heading)
            pending_heading = Paragraph(mdlite.inline_to_markup(block.text), style)
            first_para_done = False
        elif isinstance(block, mdlite.Paragraph):
            style = styles["body"] if first_para_done else styles["body_first"]
            emit(Paragraph(mdlite.inline_to_markup(block.text), style))
            first_para_done = True
        elif isinstance(block, mdlite.BulletList):
            items = [
                Paragraph(
                    mdlite.inline_to_markup(item),
                    styles["bullet"],
                    bulletText=f"{index}." if block.ordered else "\u2022",
                )
                for index, item in enumerate(block.items, start=1)
            ]
            emit(items[0])
            flowables.extend(items[1:])
            first_para_done = True
        elif isinstance(block, mdlite.Quote):
            emit(Paragraph(mdlite.inline_to_markup(block.text), styles["quote"]))
            first_para_done = True
        elif isinstance(block, mdlite.Rule):
            flowables.append(Spacer(1, styles["body"].leading * 0.4))
            flowables.append(
                Paragraph("* * *", ParagraphStyle("SceneBreak", parent=styles["body"],
                                                  alignment=TA_CENTER, firstLineIndent=0))
            )
            flowables.append(Spacer(1, styles["body"].leading * 0.4))
            first_para_done = False

    if pending_heading is not None:
        flowables.append(pending_heading)
    return flowables


def _front_matter(spec: BookSpec, outline: Outline, styles: dict, year: int) -> list:
    lang = spec.language
    story: list = []

    # Occhiello
    story.append(DocAction("front_matter_page"))
    story.append(Spacer(1, 1.6 * INCH))
    story.append(Paragraph(mdlite.inline_to_markup(spec.title), styles["title_sub"]))
    story.append(PageBreak())
    story.append(PageBreak())  # bianca

    # Frontespizio
    story.append(Spacer(1, 1.4 * INCH))
    story.append(Paragraph(mdlite.inline_to_markup(spec.title), styles["title_main"]))
    if spec.subtitle:
        story.append(Spacer(1, 0.18 * INCH))
        story.append(Paragraph(mdlite.inline_to_markup(spec.subtitle), styles["title_sub"]))
    story.append(Spacer(1, 0.6 * INCH))
    story.append(Paragraph(mdlite.inline_to_markup(spec.author), styles["author"]))
    story.append(PageBreak())

    # Colophon
    copyright_lines = [
        f"© {year} {spec.author}. {L(lang, 'copyright')}",
        L(lang, "copyright_body"),
        "",
        L(lang, "disclaimer_title") + ": " + L(lang, "disclaimer_body"),
        "",
        L(lang, "ai_disclosure"),
        "",
        L(lang, "first_edition") + f" – {year}",
    ]
    if spec.isbn:
        copyright_lines.append(f"{L(lang, 'isbn')}: {spec.isbn}")
    if spec.publisher:
        copyright_lines.append(spec.publisher)
    copyright_lines.append(L(lang, "printed_by"))
    story.append(Spacer(1, 3.2 * INCH))
    for line in copyright_lines:
        if line:
            story.append(Paragraph(mdlite.inline_to_markup(line), styles["front"]))
        else:
            story.append(Spacer(1, styles["front"].leading * 0.6))
    story.append(PageBreak())

    # Dedica
    if spec.dedication:
        story.append(Spacer(1, 2.2 * INCH))
        story.append(Paragraph(mdlite.inline_to_markup(spec.dedication), styles["front_center"]))
        story.append(PageBreak())
        story.append(PageBreak())

    # Indice
    toc = TableOfContents()
    toc.levelStyles = [styles["toc1"], styles["toc2"]]
    toc.dotsMinLevel = 0
    # L'indice è costruito con una tabella e le celle di ReportLab nascono con
    # Helvetica: va forzato il font incorporato, altrimenti il PDF dichiara un
    # font non incorporato e non supera il preflight di KDP.
    toc.tableStyle = TableStyle(
        [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("FONTNAME", (0, 0), (-1, -1), styles["toc1"].fontName),
        ]
    )
    story.append(Paragraph(L(lang, "toc"), styles["toc_title"]))
    story.append(toc)
    return story


def _back_matter(spec: BookSpec, styles: dict, author_bio: str = "") -> list:
    lang = spec.language
    story: list = []
    if author_bio:
        story.append(StartOnRecto())
        story.append(DocAction("chapter_open", L(lang, "about_author")))
        story.append(Spacer(1, 0.6 * INCH))
        story.append(Paragraph(L(lang, "about_author"), styles["chapter_title"]))
        story.append(Spacer(1, 0.25 * INCH))
        story.extend(markdown_to_flowables(author_bio, styles))

    story.append(StartOnRecto())
    story.append(DocAction("chapter_open", L(lang, "review_title")))
    story.append(Spacer(1, 0.6 * INCH))
    story.append(Paragraph(L(lang, "review_title"), styles["chapter_title"]))
    story.append(Spacer(1, 0.25 * INCH))
    story.append(Paragraph(L(lang, "review_text"), styles["body_first"]))
    return story


@dataclass
class TypesetResult:
    pdf_path: Path
    pages: int
    words: int
    chapter_pages: dict[str, int] = field(default_factory=dict)
    words_by_chapter: dict[int, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "pdf": str(self.pdf_path),
            "pages": self.pages,
            "words": self.words,
            "chapter_pages": self.chapter_pages,
            "words_by_chapter": {str(k): v for k, v in self.words_by_chapter.items()},
        }


def typeset(
    spec: BookSpec,
    outline: Outline,
    chapters: list[tuple[int, str, str]],
    output: Path,
    *,
    author_bio: str = "",
    year: int | None = None,
) -> TypesetResult:
    """Impagina il libro. `chapters` è una lista (numero, titolo, markdown)."""
    import datetime

    year = year or spec.year or datetime.date.today().year
    styles = build_styles(spec)
    set_default_canvas_font(styles["body"].fontName)
    enable_hyphenation(spec.language)

    # La geometria dipende dal numero di pagine (margine interno): si parte
    # dalla stima e la si corregge dopo la prima misurazione.
    estimated_pages = spec.target_pages
    geo = kdpspecs.page_geometry(spec.trim, estimated_pages)

    output.parent.mkdir(parents=True, exist_ok=True)
    pad_to_even = False
    result = _run_typeset(spec, outline, chapters, output, styles, geo, author_bio, year, pad_to_even)

    # Due correzioni successive: il margine interno dipende dal numero di pagine
    # (che si conosce solo dopo l'impaginazione) e il totale deve essere pari,
    # perché ogni foglio stampato ha due facciate.
    for _ in range(3):
        needs_gutter_fix = kdpspecs.gutter_margin_in(result.pages) != kdpspecs.gutter_margin_in(
            estimated_pages
        )
        needs_padding = result.pages % 2 == 1
        if not needs_gutter_fix and not needs_padding:
            break
        estimated_pages = result.pages
        geo = kdpspecs.page_geometry(spec.trim, result.pages)
        pad_to_even = pad_to_even or needs_padding
        result = _run_typeset(
            spec, outline, chapters, output, styles, geo, author_bio, year, pad_to_even
        )
    return result


def _run_typeset(
    spec, outline, chapters, output, styles, geo, author_bio, year, pad_to_even=False
) -> TypesetResult:
    doc = InteriorDoc(str(output), spec, geo, styles)
    lang = spec.language

    story: list = _front_matter(spec, outline, styles, year)
    story.append(StartOnRecto())
    story.append(DocAction("body_start"))

    words_by_chapter: dict[int, int] = {}
    chapter_index = 0
    display_number = 0
    for number, title, markdown in chapters:
        plan = next((c for c in outline.chapters if c.number == number), None)
        role = plan.role if plan else "chapter"
        if chapter_index:
            story.append(StartOnRecto())
        chapter_index += 1

        story.append(DocAction("chapter_open", title))
        story.append(Spacer(1, 0.55 * INCH))
        if role == "chapter":
            display_number += 1
            label = f"{L(lang, 'chapter')} {display_number}"
            story.append(
                ChapterNumber(
                    label,
                    styles["chapter_number"].fontName,
                    styles["chapter_number"].fontSize,
                    colors.HexColor("#777777"),
                )
            )
        story.append(Paragraph(mdlite.inline_to_markup(title), styles["chapter_title"]))
        story.append(
            HRFlowable(
                width="22%", thickness=0.7, color=colors.HexColor("#999999"),
                spaceBefore=2, spaceAfter=14, hAlign="CENTER",
            )
        )
        story.extend(markdown_to_flowables(markdown, styles))
        words_by_chapter[number] = mdlite.count_words(markdown)

    story.extend(_back_matter(spec, styles, author_bio))
    if pad_to_even:
        story.append(PageBreak())
        story.append(BlankFiller())

    doc.multiBuild(story)

    return TypesetResult(
        pdf_path=Path(output),
        pages=doc.page,
        words=sum(words_by_chapter.values()),
        chapter_pages=dict(doc.chapter_pages),
        words_by_chapter=words_by_chapter,
    )

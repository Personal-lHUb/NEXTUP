"""Impaginazione di un libro di enigmi.

Riusa il documento della linea in prosa — margini speculari, testatine, folio,
capitoli in apertura di pagina dispari, font incorporati — e aggiunge quello che
alla prosa non serve: le tabelle del cast, le liste di indizi, la griglia del
finale e le soluzioni ragionate in fondo.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from .. import kdpspecs
from ..models import BookSpec
from ..typeset import (
    BlankFiller,
    ChapterNumber,
    DocAction,
    InteriorDoc,
    StartOnRecto,
    build_styles,
)
from ..typography import register_family, set_default_canvas_font
from .generator import PuzzleBook
from .model import Case, Finale
from .theme import HOW_TO_PLAY

INCH = kdpspecs.INCH
GRID = colors.HexColor("#9a9a9a")
BAND = colors.HexColor("#f0f0f0")
INK = colors.HexColor("#111111")


@dataclass
class PuzzleTypesetResult:
    pdf_path: Path
    pages: int
    chapter_pages: dict[str, int]

    def to_dict(self) -> dict:
        return {"pdf": str(self.pdf_path), "pages": self.pages, "chapter_pages": self.chapter_pages}


# --------------------------------------------------------------------------
# Stili
# --------------------------------------------------------------------------
def puzzle_styles(spec: BookSpec) -> dict:
    styles = build_styles(spec)
    body = styles["body"]
    display = styles["chapter_title"].fontName

    styles["setting"] = ParagraphStyle(
        "Setting",
        parent=styles["body_first"],
        fontSize=body.fontSize + 0.5,
        leading=body.leading + 1.5,
        spaceAfter=body.leading * 0.6,
    )
    styles["clue"] = ParagraphStyle(
        "Clue",
        parent=styles["body"],
        firstLineIndent=0,
        leftIndent=0.34 * INCH,
        bulletIndent=0.04 * INCH,
        spaceAfter=body.leading * 0.42,
        alignment=TA_LEFT,
    )
    styles["cell"] = ParagraphStyle(
        "Cell",
        parent=styles["body"],
        fontSize=body.fontSize - 1.5,
        leading=body.fontSize + 1.5,
        firstLineIndent=0,
        alignment=TA_LEFT,
    )
    styles["cell_head"] = ParagraphStyle(
        "CellHead", parent=styles["cell"], fontName=display, textColor=INK
    )
    styles["section"] = ParagraphStyle(
        "PuzzleSection",
        parent=styles["h2"],
        fontSize=body.fontSize + 0.5,
        spaceBefore=body.leading * 1.1,
        spaceAfter=body.leading * 0.5,
    )
    styles["solution_head"] = ParagraphStyle(
        "SolutionHead",
        parent=styles["h2"],
        fontSize=body.fontSize + 1,
        spaceBefore=body.leading * 1.2,
        spaceAfter=body.leading * 0.3,
        keepWithNext=1,   # il titolo non resta mai solo in fondo alla pagina
    )
    styles["step"] = ParagraphStyle(
        "Step",
        parent=styles["body"],
        fontSize=body.fontSize - 1,
        leading=body.leading - 1.5,
        firstLineIndent=0,
        leftIndent=0.3 * INCH,
        bulletIndent=0.04 * INCH,
        spaceAfter=1.5,
        alignment=TA_LEFT,
    )
    # La riga della soluzione resta nel font del testo, in grassetto: col font
    # dei titoli sembrerebbe un titolo — al lettore e a chi controlla le bozze.
    styles["answer"] = ParagraphStyle(
        "Answer",
        parent=styles["body"],
        firstLineIndent=0,
        spaceBefore=body.leading * 0.4,
    )
    styles["notes_label"] = ParagraphStyle(
        "NotesLabel",
        parent=styles["body"],
        fontName=display,
        fontSize=body.fontSize - 2,
        textColor=colors.HexColor("#777777"),
        firstLineIndent=0,
        alignment=TA_CENTER,
    )
    return styles


class RuledArea(Flowable):
    """Righe leggere su cui scrivere: una pagina di appunti bianca sembra un
    errore di impaginazione, una pagina rigata sembra quello che è."""

    def __init__(self, width: float, height: float, spacing: float = 0.28 * INCH):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.spacing = spacing

    def wrap(self, avail_width, avail_height):
        self.width = avail_width
        self.height = min(self.height, avail_height)
        return self.width, self.height

    def draw(self):
        canvas = self.canv
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#d8d8d8"))
        canvas.setLineWidth(0.5)
        y = self.height - self.spacing
        while y > 0:
            canvas.line(0, y, self.width, y)
            y -= self.spacing
        canvas.restoreState()


# --------------------------------------------------------------------------
# Tabelle
# --------------------------------------------------------------------------
def _table_style(font_name: str, *, band: bool = True) -> TableStyle:
    # Senza FONTNAME le celle nascono in Helvetica, che non viene incorporata:
    # il PDF non passerebbe il preflight di KDP.
    commands = [
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("GRID", (0, 0), (-1, -1), 0.4, GRID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("BACKGROUND", (0, 0), (-1, 0), BAND),
    ]
    if band:
        commands.append(("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BAND]))
    return TableStyle(commands)


def cast_table(case: Case, styles: dict, width: float) -> Table:
    """Il cast al completo: una riga per sospetto, una colonna per attributo."""
    keys = case.attribute_order
    header = ["Passenger"] + [case.attributes[key].label for key in keys]
    rows = [[Paragraph(text, styles["cell_head"]) for text in header]]
    for suspect in sorted(case.suspects, key=lambda s: s.name.split()[-1]):
        cells = [suspect.name] + [suspect.get(key) for key in keys]
        rows.append([Paragraph(text, styles["cell"]) for text in cells])

    name_width = width * 0.30
    other = (width - name_width) / len(keys)
    table = Table(
        rows,
        colWidths=[name_width] + [other] * len(keys),
        repeatRows=1,
        hAlign="LEFT",
    )
    table.setStyle(_table_style(styles["cell"].fontName))
    return table


def finale_grid(finale: Finale, styles: dict, width: float) -> Table:
    """Griglia da riempire: i nomi sono le risposte dei dodici casi, non si stampano."""
    keys = [key for key in finale.attributes]
    header = ["Case", "Culprit (your answer)"] + [finale.attributes[key].label for key in keys]
    rows = [[Paragraph(text, styles["cell_head"]) for text in header]]
    for suspect in sorted(finale.suspects, key=lambda s: int(s.get("case"))):
        cells = [f"Case {suspect.get('case')}", ""] + [""] * len(keys)
        rows.append([Paragraph(text, styles["cell"]) for text in cells])

    case_width = width * 0.13
    name_width = width * 0.37
    other = (width - case_width - name_width) / len(keys)
    table = Table(
        rows,
        colWidths=[case_width, name_width] + [other] * len(keys),
        repeatRows=1,
        rowHeights=[None] + [0.26 * INCH] * len(finale.suspects),
        hAlign="LEFT",
    )
    table.setStyle(_table_style(styles["cell"].fontName, band=False))
    return table


# --------------------------------------------------------------------------
# Sezioni
# --------------------------------------------------------------------------
def _front_matter(spec: BookSpec, book: PuzzleBook, styles: dict, year: int) -> list:
    from ..i18n import L

    lang = spec.language
    story: list = [DocAction("front_matter_page"), Spacer(1, 1.6 * INCH)]
    story.append(Paragraph(spec.title, styles["title_sub"]))
    story.append(PageBreak())
    story.append(PageBreak())

    story.append(Spacer(1, 1.3 * INCH))
    story.append(Paragraph(spec.title, styles["title_main"]))
    if spec.subtitle:
        story.append(Spacer(1, 0.2 * INCH))
        story.append(Paragraph(spec.subtitle, styles["title_sub"]))
    story.append(Spacer(1, 0.6 * INCH))
    story.append(Paragraph(spec.author, styles["author"]))
    story.append(PageBreak())

    lines = [
        f"© {year} {spec.author}. {L(lang, 'copyright')}",
        L(lang, "copyright_body"),
        "",
        "The puzzles in this book were composed by a computer program written by the "
        "author. Every case was checked by that program before printing: each has exactly "
        "one solution, and no clue in it can be removed without making the case unsolvable. "
        "The story text around the puzzles was produced with the assistance of artificial "
        "intelligence, under human supervision and editorial responsibility.",
        "",
        "All persons, trains, places and events in this book are invented. Any resemblance "
        "to real persons, living or dead, is coincidental.",
        "",
        f"{L(lang, 'first_edition')} – {year}",
    ]
    if spec.isbn:
        lines.append(f"{L(lang, 'isbn')}: {spec.isbn}")
    lines.append(L(lang, "printed_by"))

    story.append(Spacer(1, 2.6 * INCH))
    for line in lines:
        if line:
            story.append(Paragraph(line, styles["front"]))
        else:
            story.append(Spacer(1, styles["front"].leading * 0.6))
    story.append(PageBreak())

    # Come si gioca
    story.append(DocAction("front_matter_page"))
    story.append(Spacer(1, 0.5 * INCH))
    story.append(Paragraph("How to Play", styles["toc_title"]))
    for block in HOW_TO_PLAY.split("\n\n"):
        story.append(Paragraph(_bold(block), styles["setting"]))
    story.append(PageBreak())
    return story


def _elimination(before: int, after: int) -> str:
    """"1 is ruled out and 1 remains": in un libro stampato anche i singolari
    contano."""
    removed = before - after
    subject = "passenger was" if before == 1 else "passengers were"
    verb_out = "is" if removed == 1 else "are"
    verb_left = "remains" if after == 1 else "remain"
    return (
        f"{before} {subject} still in play; {removed} {verb_out} ruled out and "
        f"{after} {verb_left}"
    )


def _setting_text(case: Case) -> str:
    """Il testo di scena può citare quanti sono i passeggeri: il numero lo
    decide il generatore, non chi ha scritto la frase."""
    if "{count}" in case.setting:
        return case.setting.format(count=len(case.suspects))
    return case.setting


def _bold(text: str) -> str:
    """Converte **testo** in grassetto: l'unico markup usato nei testi fissi."""
    import re

    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)


def _worked_example(case: Case, styles: dict, width: float) -> list:
    """Un caso piccolo risolto per intero: vale più di qualsiasi spiegazione."""
    story: list = [DocAction("front_matter_page"), Spacer(1, 0.5 * INCH)]
    story.append(Paragraph("A Case, Solved", styles["toc_title"]))
    story.append(Paragraph(case.setting, styles["setting"]))

    story.append(Paragraph("The clues", styles["section"]))
    for index, text in enumerate(case.clue_texts(), start=1):
        story.append(Paragraph(text, styles["clue"], bulletText=f"{index}."))

    story.append(Paragraph("The passengers", styles["section"]))
    story.append(cast_table(case, styles, width))

    story.append(Paragraph("How it comes apart", styles["section"]))
    for index, before, after in case.trace:
        text = case.clue_texts()[index - 1]
        story.append(
            Paragraph(
                f"<i>{text}</i> — {_elimination(before, after)}.",
                styles["step"],
                bulletText=f"{index}.",
            )
        )
    attributes = ", ".join(
        f"{case.attributes[key].label.lower()}: {case.culprit.get(key)}"
        for key in case.attribute_order
    )
    story.append(
        Paragraph(
            f"<b>One name is left: {case.culprit.name}</b> ({attributes}). No other passenger "
            f"survives all {len(case.clues)} clues, and none of the clues could have been "
            "left out without leaving two names standing.",
            styles["answer"],
        )
    )
    story.append(PageBreak())
    return story


def _case_pages(case: Case, styles: dict, width: float, first: bool) -> list:
    story: list = []
    if not first:
        story.append(StartOnRecto())
    story.append(DocAction("chapter_open", f"Case {case.number}"))
    story.append(Spacer(1, 0.5 * INCH))
    story.append(
        ChapterNumber(
            f"Case {case.number}",
            styles["chapter_number"].fontName,
            styles["chapter_number"].fontSize,
            colors.HexColor("#777777"),
        )
    )
    story.append(Paragraph(case.title, styles["chapter_title"]))
    story.append(Spacer(1, 0.18 * INCH))
    story.append(Paragraph(_setting_text(case), styles["setting"]))

    story.append(Paragraph("The clues", styles["section"]))
    for index, text in enumerate(case.clue_texts(), start=1):
        story.append(Paragraph(text, styles["clue"], bulletText=f"{index}."))

    story.append(Paragraph(f"The passengers ({len(case.suspects)})", styles["section"]))
    story.append(cast_table(case, styles, width))
    story.append(Spacer(1, 0.12 * INCH))
    story.append(
        Paragraph(
            "When one name is left, write it here: ________________________",
            styles["notes_label"],
        )
    )
    # Una pagina per lavorare: in un libro da risolvere a matita serve più della
    # tabella, e serve accanto al caso, non in fondo al volume.
    story.append(PageBreak())
    story.append(Paragraph(f"Case {case.number} — working notes", styles["section"]))
    story.append(Spacer(1, 0.1 * INCH))
    story.append(RuledArea(width, 6.2 * INCH))
    return story


def _finale_pages(finale: Finale, styles: dict, width: float) -> list:
    story: list = [StartOnRecto(), DocAction("chapter_open", "The Mastermind")]
    story.append(Spacer(1, 0.5 * INCH))
    story.append(
        ChapterNumber(
            "Case 13",
            styles["chapter_number"].fontName,
            styles["chapter_number"].fontSize,
            colors.HexColor("#777777"),
        )
    )
    story.append(Paragraph(finale.title, styles["chapter_title"]))
    story.append(Spacer(1, 0.18 * INCH))
    for block in finale.setting.split("\n\n"):
        story.append(Paragraph(block, styles["setting"]))

    story.append(Paragraph("The clues", styles["section"]))
    for index, text in enumerate(finale.clue_texts(), start=1):
        story.append(Paragraph(text, styles["clue"], bulletText=f"{index}."))

    # La griglia si riempie a matita: deve stare tutta su una pagina, non a
    # cavallo di due.
    story.append(PageBreak())
    story.append(Paragraph("Your twelve culprits", styles["section"]))
    story.append(Spacer(1, 0.08 * INCH))
    story.append(finale_grid(finale, styles, width))
    story.append(Spacer(1, 0.2 * INCH))
    story.append(
        Paragraph(
            "The mastermind is the culprit of Case ______ : ________________________",
            styles["notes_label"],
        )
    )
    return story


def _solutions(book: PuzzleBook, styles: dict) -> list:
    story: list = [StartOnRecto(), DocAction("chapter_open", "Solutions")]
    story.append(Spacer(1, 0.5 * INCH))
    story.append(Paragraph("Solutions", styles["chapter_title"]))
    story.append(Spacer(1, 0.1 * INCH))
    story.append(
        Paragraph(
            "Each solution shows the order of elimination: how many passengers were still "
            "in play before each clue, and how many survived it. Follow the same order and "
            "you will land on the same name.",
            styles["body_first"],
        )
    )

    for case in book.cases:
        block: list = [Paragraph(f"Case {case.number} — {case.title}", styles["solution_head"])]
        for index, before, after in case.trace:
            text = case.clue_texts()[index - 1]
            block.append(
                Paragraph(
                    f"<i>{text}</i> — {_elimination(before, after)}.",
                    styles["step"],
                    bulletText=f"{index}.",
                )
            )
        attributes = ", ".join(
            f"{case.attributes[key].label.lower()}: {case.culprit.get(key)}"
            for key in case.attribute_order
        )
        block.append(
            Paragraph(f"<b>The culprit is {case.culprit.name}</b> ({attributes}).", styles["answer"])
        )
        # Le soluzioni scorrono, ma il titolo resta attaccato al primo passaggio:
        # tenerle ognuna su una pagina lascerebbe dieci pagine mezze vuote.
        story.append(KeepTogether(block[:2]))
        story.extend(block[2:])

    if book.finale:
        block = [Paragraph("Case 13 — The Mastermind", styles["solution_head"])]
        block.append(
            Paragraph(
                "Fill the grid with your twelve answers and the clues leave one row standing.",
                styles["step"],
            )
        )
        block.append(
            Paragraph(
                f"<b>The mastermind is {book.finale.mastermind.name}</b>, the culprit of "
                f"Case {book.finale.mastermind.get('case')}.",
                styles["answer"],
            )
        )
        story.append(KeepTogether(block))
    return story


# --------------------------------------------------------------------------
# Costruzione
# --------------------------------------------------------------------------
def typeset_puzzle_book(
    spec: BookSpec, book: PuzzleBook, output: Path, *, year: int | None = None
) -> PuzzleTypesetResult:
    import datetime

    year = year or spec.year or datetime.date.today().year
    styles = puzzle_styles(spec)
    set_default_canvas_font(styles["body"].fontName)
    register_family("sans")

    output.parent.mkdir(parents=True, exist_ok=True)
    estimated = spec.target_pages
    result = _run(spec, book, output, styles, estimated, year, pad_to_even=False)

    for _ in range(3):
        needs_gutter_fix = kdpspecs.gutter_margin_in(result.pages) != kdpspecs.gutter_margin_in(
            estimated
        )
        needs_padding = result.pages % 2 == 1
        if not needs_gutter_fix and not needs_padding:
            break
        estimated = result.pages
        result = _run(spec, book, output, styles, estimated, year, pad_to_even=needs_padding)
    return result


def _run(spec, book, output, styles, pages_hint, year, pad_to_even) -> PuzzleTypesetResult:
    geo = kdpspecs.page_geometry(spec.trim, pages_hint)
    doc = InteriorDoc(str(output), spec, geo, styles)
    width = geo.text_width

    story = _front_matter(spec, book, styles, year)
    if book.example is not None:
        story.extend(_worked_example(book.example, styles, width))
    story.append(StartOnRecto())
    story.append(DocAction("body_start"))

    for index, case in enumerate(book.cases):
        story.extend(_case_pages(case, styles, width, first=index == 0))
    if book.finale:
        story.extend(_finale_pages(book.finale, styles, width))
    story.extend(_solutions(book, styles))

    if pad_to_even:
        story.append(PageBreak())
        story.append(BlankFiller())

    doc.multiBuild(story)
    return PuzzleTypesetResult(
        pdf_path=Path(output), pages=doc.page, chapter_pages=dict(doc.chapter_pages)
    )

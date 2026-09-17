"""Dal seme al pacchetto: interno, copertina, risposte, scheda prodotto.

La linea enigmistica non chiama nessun modello: genera, verifica, impagina.
Per questo un libro si produce anche senza chiave API — e si riproduce identico
partendo dallo stesso seme.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

from .. import backup, kdpspecs, qa
from .. import cover as cover_module
from .. import metadata as metadata_module
from ..agents import AgentContext, get_agent
from ..coverdesign import CoverCopy
from ..models import BookProject, BookSpec
from .generator import PuzzleBook, generate_book
from .layout import typeset_puzzle_book
from .theme import BOOK_SUBTITLE, BOOK_TITLE


@dataclass
class PuzzleSpec:
    """Parametri della linea enigmistica, accanto a `book.json`."""

    seed: int = 20260915
    cases: int = 12

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def load(cls, path: Path) -> PuzzleSpec:
        if not path.exists():
            return cls()
        return cls(**json.loads(path.read_text(encoding="utf-8")))

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")


def puzzle_spec_path(project: BookProject) -> Path:
    return project.root / "puzzle.json"


def default_book_spec(slug: str, author: str) -> BookSpec:
    return BookSpec(
        slug=slug,
        title=BOOK_TITLE,
        subtitle=BOOK_SUBTITLE,
        author=author,
        language="en",
        topic="a deduction puzzle book: twelve cases aboard a night express, and a "
        "thirteenth that needs all twelve answers",
        audience="puzzle solvers who want reasoning rather than word search",
        promise="thirteen cases that can be solved with a pencil and no guesswork",
        genre="non-fiction",
        target_pages=100,
        trim="6x9",
        paper="white",
        cover_theme="notte",
        cover_style="tipografica",
        body_font="serif",
        body_font_size=11.0,
        leading=15.0,
        include_exercises=False,
        include_intro=False,
        include_conclusion=False,
        year=date.today().year,
    )


# --------------------------------------------------------------------------
# Scheda prodotto (scritta a mano: qui non serve un modello)
# --------------------------------------------------------------------------
def listing_metadata(book: PuzzleBook, spec: BookSpec, pages: int) -> dict:
    suspects = book.suspects_total
    cases = len(book.cases)
    return {
        "title": spec.title,
        "subtitle": spec.subtitle,
        "description_paragraphs": [
            "Thirteen cases. One pencil. No guesswork.",
            f"A body on the night express, {cases} carriages to search and {suspects:,} "
            "passengers who all had a reason to be somewhere else. Each case gives you the "
            "full list of everyone in the carriage — what they wore, what they carried, what "
            "they were drinking — and a handful of statements that are all true. Cross off "
            "the impossible and one name is left standing.",
            "Then comes the thirteenth case. One of the twelve culprits was never working "
            "alone, and the only way to name them is with all twelve answers in front of you.",
            "Every case in this book was verified before printing: exactly one solution, and "
            "not a single clue that could be removed without breaking it. No red herrings, no "
            "contradictions, no puzzle that turns out to have two answers.",
        ],
        "bullets": [
            f"{cases} standalone cases plus a finale that needs every answer you have",
            "A difficulty curve from a quiet twenty-four-passenger carriage to a hundred and "
            "twenty suspects and conditional clues",
            "A worked example at the front: one full case solved step by step",
            "Full solutions that show the order of elimination, not just the name",
            "Room to work on the page — every case has its own notes sheet",
        ],
        "closing": "Sharpen a pencil. The train leaves at eleven.",
        "keywords": [
            "logic puzzles for adults",
            "whodunnit brain teaser",
            "deduction game gift",
            "screen free evening activity",
            "1930s train mystery",
            "detective reasoning challenge",
            "puzzle gift for dad",
        ],
        "categories": [
            "GAMES & ACTIVITIES / Logic & Brain Teasers",
            "GAMES & ACTIVITIES / Puzzles",
            "GAMES & ACTIVITIES / Reference",
        ],
        "author_bio": "",
        "back_cover": "Thirteen cases. One pencil. No guesswork.\n\n"
        f"{suspects:,} passengers boarded the Ashcombe Night Express. Twelve of them are "
        "guilty, and one of those twelve planned the lot. Every clue in this book is true, "
        "every case has exactly one answer, and every answer can be reached by reasoning "
        "alone.\n\nThe thirteenth case cannot be solved until the other twelve are.",
        "back_cover_bullets": [
            f"{cases} cases, {suspects:,} suspects, one mastermind",
            "Checked by machine: one solution, no wasted clues",
            "Worked example and full step-by-step solutions",
        ],
    }


def cover_copy(book: PuzzleBook, spec: BookSpec) -> CoverCopy:
    """I testi della prima di copertina per un libro di enigmi.

    Il gancio è una domanda (il ciclo resta aperto), i numeri sono in cifre e
    la garanzia è vera e verificabile — è l'unica cosa che questo libro può
    promettere e che gli altri non promettono.
    """
    return CoverCopy(
        title=spec.title,
        kicker="DEDUCTION PUZZLES",
        hook="Can you name the killer in every carriage?",
        stats=f"{len(book.cases) + 1} CASES · {book.suspects_total:,} SUSPECTS · 1 MASTERMIND",
        badge="Every case has exactly one solution",
        author=spec.author,
    )


# --------------------------------------------------------------------------
# Produzione
# --------------------------------------------------------------------------
def build(
    project: BookProject,
    spec: BookSpec,
    puzzle_spec: PuzzleSpec,
    *,
    guides: bool = False,
) -> dict:
    """Genera il libro, lo impagina, produce copertina, risposte e scheda."""
    project.ensure_dirs()
    book = generate_book(puzzle_spec.seed)

    interior = project.build_dir / f"{spec.slug}-interno.pdf"
    typeset = typeset_puzzle_book(spec, book, interior)

    cover_path = project.build_dir / f"{spec.slug}-copertina.pdf"
    meta = listing_metadata(book, spec, typeset.pages)
    cover_info = cover_module.build_cover(
        spec,
        typeset.pages,
        cover_path,
        back_cover_text=meta["back_cover"],
        bullets=meta["back_cover_bullets"],
        guides=guides,
        genre="enigmi",
        copy=cover_copy(book, spec),
    )

    (project.build_dir / "answers.json").write_text(
        json.dumps(book.answers(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    config = metadata_module.load_printing_config()
    prices = metadata_module.price_table(typeset.pages, config)
    meta["description_html"] = metadata_module.build_description_html(meta)
    (project.build_dir / "kdp-listing.md").write_text(
        metadata_module.render_listing(spec, meta, typeset.pages, prices, config),
        encoding="utf-8",
    )
    (project.build_dir / "metadata.json").write_text(
        json.dumps(
            {**meta, "prezzi": [p.to_dict() for p in prices], "pagine": typeset.pages},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    state = {
        "build": {
            "pagine": typeset.pages,
            "interno_pdf": str(interior),
            "copertina_pdf": str(cover_path),
            "chapter_pages": typeset.chapter_pages,
        },
        "cover": cover_info,
        "puzzle": {
            "seed": puzzle_spec.seed,
            "casi": len(book.cases),
            "sospetti": book.suspects_total,
            "indizi": book.clues_total,
            "mastermind": book.finale.mastermind.name if book.finale else "",
        },
        "metadata": meta,
    }
    project.update_state(**state)
    backup.snapshot(project, f"enigmistica: seme {puzzle_spec.seed}, {typeset.pages} pagine")

    return {
        "pages": typeset.pages,
        "interior": interior,
        "cover": cover_path,
        "book": book,
        "prices": prices,
    }


def check(project: BookProject, spec: BookSpec, pages: int, interior: Path) -> qa.Report:
    """Controlli di stampa più gli agenti che misurano interno e copertina."""
    report = qa.Report()
    qa.check_print_pdf(spec, interior, pages, report)

    state = project.load_state()
    if state.get("metadata"):
        qa.check_metadata(state["metadata"], spec, report)

    cover_state = state.get("cover", {})
    cover_file = cover_state.get("cover_pdf")
    ctx = AgentContext(
        spec=spec,
        pdf_path=interior,
        pages=pages,
        chapter_pages=state.get("build", {}).get("chapter_pages", {}),
        cover_pdf=Path(cover_file) if cover_file else None,
        cover_copy=cover_state.get("testi", {}),
    )
    for agent_name, label in (("impaginazione", "IMPAGINAZIONE"), ("copertina", "COPERTINA")):
        result = get_agent(agent_name).run(ctx)
        for finding in result.findings:
            level = {"bloccante": "errore", "importante": "avviso"}.get(finding.severity, "info")
            report.add(level, label, f"{finding.category} — {finding.issue}")
        if not result.findings:
            report.add("info", label, result.notes)

    for problem in kdpspecs.validate_page_count(pages, spec.paper):
        report.add("errore", "PAGINE", problem)

    (project.build_dir / "qa-report.json").write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report

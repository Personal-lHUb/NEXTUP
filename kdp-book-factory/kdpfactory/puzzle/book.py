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
from .theme import Ambientazione, ambientazione_path, carica


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


def default_book_spec(slug: str, author: str, ambientazione: Ambientazione) -> BookSpec:
    """La scheda del libro, presa dall'ambientazione che l'autore ha scritto."""
    return BookSpec(
        slug=slug,
        title=ambientazione.titolo,
        subtitle=ambientazione.sottotitolo,
        author=author,
        language="en",
        topic=f"a deduction puzzle book set in {ambientazione.luogo}"
        if ambientazione.luogo
        else "a deduction puzzle book",
        audience="puzzle solvers who want reasoning rather than word search",
        promise="cases that can be solved with a pencil and no guesswork",
        genre="non-fiction",
        # ogni caso porta impostazione, tabella del cast, indizi, pagina di
        # appunti e soluzione: le pagine sono diverse fra loro per costruzione
        content_type="medium",
        target_pages=100,
        trim="6x9",
        paper="white",
        cover_theme="notturno",
        cover_style="tipografica",
        cover_art="auto",
        body_font="serif",
        body_font_size=11.0,
        leading=15.0,
        include_exercises=False,
        include_intro=False,
        include_conclusion=False,
        year=date.today().year,
    )


# --------------------------------------------------------------------------
# Scheda prodotto e copertina: testi dell'autore, non del sistema
# --------------------------------------------------------------------------
def _riempi(testo: str, book: PuzzleBook) -> str:
    """Sostituisce i numeri veri del libro generato nei testi dell'autore."""
    return testo.format(
        casi=len(book.cases) + 1,          # i casi più il finale
        casi_semplici=len(book.cases),
        sospetti=f"{book.suspects_total:,}",
        indizi=book.clues_total,
    )


def listing_metadata(
    book: PuzzleBook, spec: BookSpec, pages: int, ambientazione: Ambientazione
) -> dict:
    """La scheda prodotto del libro, presa dall'ambientazione.

    Non serve un modello: questi testi li scrive l'autore una volta sola, e i
    numeri — casi, sospetti, indizi — li mette il libro generato.
    """
    scheda = ambientazione.scheda
    return {
        "title": spec.title,
        "subtitle": spec.subtitle,
        "description_paragraphs": [_riempi(p, book) for p in scheda.get("paragrafi", [])],
        "bullets": [_riempi(b, book) for b in scheda.get("punti", [])],
        "closing": _riempi(str(scheda.get("chiusura", "")), book),
        "keywords": list(scheda.get("parole_chiave", [])),
        "categories": list(scheda.get("categorie", [])),
        "author_bio": str(scheda.get("biografia", "")),
        "back_cover": _riempi(str(scheda.get("quarta", "")), book),
        "back_cover_bullets": [_riempi(b, book) for b in scheda.get("punti_quarta", [])],
    }


def cover_copy(book: PuzzleBook, spec: BookSpec, ambientazione: Ambientazione) -> CoverCopy:
    """I testi della prima di copertina, dall'ambientazione.

    Il gancio è una domanda (il ciclo resta aperto) e i numeri sono in cifre:
    sono le regole 6 e 7 del sistema di copertina, e valgono per ogni libro.
    """
    copertina = ambientazione.copertina
    return CoverCopy(
        title=spec.title,
        kicker=str(copertina.get("occhiello", "")),
        hook=_riempi(str(copertina.get("gancio", "")), book),
        stats=_riempi(str(copertina.get("numeri", "")), book),
        badge=str(copertina.get("garanzia", "")),
        author=spec.author,
        subject=spec.title + " " + spec.topic,
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
    ambientazione = carica(ambientazione_path(project.root))
    book = generate_book(puzzle_spec.seed, ambientazione)

    interior = project.build_dir / f"{spec.slug}-interno.pdf"
    typeset = typeset_puzzle_book(spec, book, interior)

    cover_path = project.build_dir / f"{spec.slug}-copertina.pdf"
    meta = listing_metadata(book, spec, typeset.pages, ambientazione)
    cover_info = cover_module.build_cover(
        spec,
        typeset.pages,
        cover_path,
        back_cover_text=meta["back_cover"],
        bullets=meta["back_cover_bullets"],
        guides=guides,
        genre="enigmi",
        copy=cover_copy(book, spec, ambientazione),
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

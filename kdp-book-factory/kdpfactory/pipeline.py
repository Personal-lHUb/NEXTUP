"""Orchestrazione: dal piano al pacchetto pronto per il caricamento.

Il pezzo centrale è `build_until_in_range`: impagina, misura le pagine reali,
ricalcola il budget di parole, fa riscrivere i capitoli e ripete finché il PDF
non rientra nell'intervallo richiesto.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from . import cover as cover_module
from . import epub as epub_module
from . import kdpspecs, planner, qa, typeset, writer
from . import metadata as metadata_module
from .llm import LLMClient
from .mdlite import count_words
from .models import BookProject, BookSpec, Outline


@dataclass
class BuildResult:
    pages: int = 0
    words: int = 0
    iterations: int = 0
    in_range: bool = False
    interior_pdf: Path | None = None
    cover_pdf: Path | None = None
    epub_path: Path | None = None
    history: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "pagine": self.pages,
            "parole": self.words,
            "iterazioni": self.iterations,
            "nell_intervallo": self.in_range,
            "interno_pdf": str(self.interior_pdf) if self.interior_pdf else None,
            "copertina_pdf": str(self.cover_pdf) if self.cover_pdf else None,
            "epub": str(self.epub_path) if self.epub_path else None,
            "storico": self.history,
        }


def acceptance_window(spec: BookSpec, tolerance: float = 0.05) -> tuple[int, int]:
    """Intervallo di pagine accettato: tolleranza attorno all'obiettivo,
    comunque dentro i limiti di progetto (60-240)."""
    low = max(kdpspecs.PROJECT_MIN_PAGES, int(spec.target_pages * (1 - tolerance)))
    high = min(kdpspecs.PROJECT_MAX_PAGES, int(round(spec.target_pages * (1 + tolerance))))
    return low, high


def typeset_only(project: BookProject, spec: BookSpec, outline: Outline) -> typeset.TypesetResult:
    chapters = writer.load_chapters(project, outline)
    if not chapters:
        raise RuntimeError("Nessun capitolo da impaginare: esegui prima `write`.")
    state = project.load_state()
    return typeset.typeset(
        spec,
        outline,
        chapters,
        project.build_dir / f"{spec.slug}-interno.pdf",
        author_bio=state.get("author_bio", ""),
    )


def build_until_in_range(
    project: BookProject,
    spec: BookSpec,
    outline: Outline,
    client: LLMClient | None = None,
    *,
    max_iterations: int = 3,
    tolerance: float = 0.05,
    allow_rewrite: bool = True,
) -> BuildResult:
    """Impagina e, se serve, fa riscrivere i capitoli fino a rientrare."""
    low, high = acceptance_window(spec, tolerance)
    result = BuildResult()

    for iteration in range(1, max_iterations + 1):
        typeset_result = typeset_only(project, spec, outline)
        result.iterations = iteration
        result.pages = typeset_result.pages
        result.words = typeset_result.words
        result.interior_pdf = typeset_result.pdf_path
        result.in_range = low <= typeset_result.pages <= high
        result.history.append(
            {
                "iterazione": iteration,
                "pagine": typeset_result.pages,
                "parole": typeset_result.words,
                "obiettivo": spec.target_pages,
                "intervallo": [low, high],
            }
        )
        print(
            f"  → impaginazione {iteration}: {typeset_result.pages} pagine "
            f"({typeset_result.words} parole), obiettivo {spec.target_pages} "
            f"[{low}-{high}]"
        )

        if result.in_range or not allow_rewrite or client is None or iteration == max_iterations:
            break

        calibration = planner.recalibrate(
            measured_pages=typeset_result.pages,
            measured_words=typeset_result.words,
            spec=spec,
            chapters=outline.chapters,
            chapter_words=typeset_result.words_by_chapter,
        )
        print(
            f"    parole/pagina misurate: {calibration.measured_words_per_page} · "
            f"correzione del budget {calibration.scale - 1:+.1%}"
        )
        # La misura viene conservata: le esecuzioni successive di questo libro
        # (e il `plan` di libri con lo stesso formato) partono già calibrate.
        project.update_state(words_per_page_measured=calibration.measured_words_per_page)
        if abs(calibration.scale - 1) < 0.01:
            print("    scostamento minimo: nessuna riscrittura necessaria.")
            break

        revised = writer.revise_length(project, spec, outline, client, calibration.per_chapter)
        outline.save(project.outline_path)
        project.update_state(last_calibration=calibration.to_dict())
        if not revised:
            print("    nessun capitolo da riscrivere.")
            break
        print(f"    capitoli riscritti: {', '.join(str(n) for n in revised)}")

    return result


def build_package(
    project: BookProject,
    spec: BookSpec,
    outline: Outline,
    result: BuildResult,
    *,
    guides: bool = False,
) -> BuildResult:
    """Copertina ed EPUB, allineati al numero di pagine definitivo."""
    state = project.load_state()
    meta = state.get("metadata", {})
    chapters = writer.load_chapters(project, outline)

    cover_path = project.build_dir / f"{spec.slug}-copertina.pdf"
    cover_info = cover_module.build_cover(
        spec,
        result.pages,
        cover_path,
        back_cover_text=meta.get("back_cover") or outline.back_cover,
        bullets=meta.get("back_cover_bullets") or [],
        author_line=meta.get("author_bio", ""),
        guides=guides,
    )
    result.cover_pdf = cover_path

    epub_path = project.build_dir / f"{spec.slug}.epub"
    epub_module.build_epub(
        spec, outline, chapters, epub_path, author_bio=meta.get("author_bio", "")
    )
    result.epub_path = epub_path

    project.update_state(build=result.to_dict(), cover=cover_info)
    return result


def run_qa(
    project: BookProject, spec: BookSpec, outline: Outline, result: BuildResult
) -> qa.Report:
    chapters = writer.load_chapters(project, outline)
    report = qa.check_manuscript(spec, outline, chapters)
    if result.interior_pdf:
        qa.check_print_pdf(spec, result.interior_pdf, result.pages, report)
    state = project.load_state()
    if state.get("metadata"):
        qa.check_metadata(state["metadata"], spec, report)

    low, high = acceptance_window(spec)
    if not (low <= result.pages <= high) and result.pages:
        report.add(
            "avviso",
            "PAGINE",
            f"{result.pages} pagine contro un obiettivo di {spec.target_pages} "
            f"({low}-{high}): valuta di aggiungere o togliere capitoli.",
        )
    (project.build_dir / "qa-report.json").write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def write_metadata_files(
    project: BookProject, spec: BookSpec, outline: Outline, meta: dict, pages: int
) -> dict:
    config = metadata_module.load_printing_config()
    prices = metadata_module.price_table(pages, config)
    listing = metadata_module.render_listing(spec, meta, pages, prices, config)
    (project.build_dir / "kdp-listing.md").write_text(listing, encoding="utf-8")
    (project.build_dir / "metadata.json").write_text(
        json.dumps(
            {**meta, "prezzi": [p.to_dict() for p in prices], "pagine": pages},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    project.update_state(metadata=meta, author_bio=meta.get("author_bio", ""))
    return {"listing": str(project.build_dir / "kdp-listing.md"), "prezzi": [p.to_dict() for p in prices]}


def manuscript_stats(project: BookProject, outline: Outline) -> dict:
    chapters = writer.load_chapters(project, outline)
    words = {number: count_words(text) for number, _, text in chapters}
    return {
        "capitoli_scritti": len(chapters),
        "capitoli_previsti": len(outline.chapters),
        "parole": sum(words.values()),
        "parole_per_capitolo": {str(k): v for k, v in words.items()},
    }


def export_manuscript_markdown(project: BookProject, spec: BookSpec, outline: Outline) -> Path:
    """Manoscritto completo in un unico file, comodo per rileggere o passare a un editor."""
    chapters = writer.load_chapters(project, outline)
    parts = [f"% {spec.title}", f"% {spec.author}", f"% {spec.year or date.today().year}", ""]
    for _, title, body in chapters:
        parts.append(f"# {title}")
        parts.append("")
        parts.append(body.strip())
        parts.append("")
    path = project.build_dir / f"{spec.slug}-manoscritto.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")
    return path

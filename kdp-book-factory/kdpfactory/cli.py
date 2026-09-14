"""Interfaccia a riga di comando.

    python -m kdpfactory init "Titolo del libro" --pages 140
    python -m kdpfactory all titolo-del-libro
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

from . import kdpspecs, pipeline, planner, writer
from .llm import DEFAULT_MODEL, LLMClient, LLMConfig, api_key_present
from .models import BookProject, BookSpec, slugify

DEFAULT_BOOKS_DIR = Path(os.environ.get("KDPFACTORY_BOOKS_DIR", "")) if os.environ.get(
    "KDPFACTORY_BOOKS_DIR"
) else Path(__file__).resolve().parent.parent / "books"


def books_dir(args) -> Path:
    return Path(args.books_dir) if args.books_dir else DEFAULT_BOOKS_DIR


def open_project(args) -> tuple[BookProject, BookSpec]:
    root = books_dir(args) / args.slug
    if not root.exists():
        raise SystemExit(
            f"Libro '{args.slug}' non trovato in {books_dir(args)}.\n"
            f"Crealo con: python -m kdpfactory init \"Titolo\""
        )
    project = BookProject(root)
    spec = project.load_spec()
    problems = spec.validate()
    if problems:
        raise SystemExit("book.json non valido:\n" + "\n".join(f"  - {p}" for p in problems))
    return project, spec


def budget_for(project: BookProject, spec: BookSpec) -> planner.PageBudget:
    """Budget del libro, usando la calibrazione misurata se già disponibile."""
    measured = project.load_state().get("words_per_page_measured")
    return planner.build_budget(spec, measured)


def make_client(args) -> LLMClient:
    if not args.dry_run and not api_key_present():
        raise SystemExit(
            "Nessuna credenziale Anthropic trovata.\n"
            "  export ANTHROPIC_API_KEY=sk-ant-...   oppure   ant auth login\n"
            "Per provare la pipeline senza chiamate di rete: aggiungi --dry-run"
        )
    return LLMClient(
        LLMConfig(
            model=args.model,
            effort=args.effort,
            max_tokens=args.max_tokens,
            dry_run=args.dry_run,
        )
    )


# --------------------------------------------------------------------------
# Comandi
# --------------------------------------------------------------------------
def cmd_init(args) -> int:
    slug = args.slug_name or slugify(args.title)
    root = books_dir(args) / slug
    if root.exists() and not args.force:
        raise SystemExit(f"Esiste già {root}. Usa --force per sovrascrivere book.json.")
    spec = BookSpec(
        slug=slug,
        title=args.title,
        subtitle=args.subtitle,
        author=args.author,
        language=args.language,
        topic=args.topic or args.title,
        audience=args.audience,
        promise=args.promise,
        genre=args.genre,
        target_pages=args.pages,
        trim=args.trim,
        paper=args.paper,
        chapters=args.chapters,
        year=date.today().year,
    )
    problems = spec.validate()
    if problems:
        raise SystemExit("Parametri non validi:\n" + "\n".join(f"  - {p}" for p in problems))

    project = BookProject(root)
    project.ensure_dirs()
    spec.save(project.spec_path)
    print(f"Creato {project.spec_path}")
    print("Apri il file e completa `topic`, `audience`, `promise` e `notes`: più sono")
    print("precisi, più il libro sarà specifico e meno generico.\n")
    print(planner.describe(planner.build_budget(spec), spec))
    print(f"\nProssimo passo: python -m kdpfactory outline {slug}")
    return 0


def cmd_plan(args) -> int:
    project, spec = open_project(args)
    budget = budget_for(project, spec)
    print(planner.describe(budget, spec))
    if project.outline_path.exists():
        outline = project.load_outline()
        print("\nCapitoli in scaletta:")
        for chapter in outline.chapters:
            written = "✓" if project.chapter_path(chapter.number).exists() else " "
            print(f" [{written}] {chapter.number:2d}. {chapter.title}  ({chapter.target_words} parole)")
    return 0


def cmd_outline(args) -> int:
    project, spec = open_project(args)
    if project.outline_path.exists() and not args.force:
        raise SystemExit(
            f"{project.outline_path} esiste già. Usa --force per rigenerarla "
            "(i capitoli già scritti non vengono cancellati)."
        )
    client = make_client(args)
    budget = budget_for(project, spec)
    print(planner.describe(budget, spec))
    print("\nGenerazione della scaletta…")
    outline = writer.generate_outline(spec, client, budget)
    project.ensure_dirs()
    outline.save(project.outline_path)
    project.update_state(budget=budget.to_dict(), usage=client.usage_report())
    print(f"\nScaletta salvata in {project.outline_path}")
    for chapter in outline.chapters:
        print(f"  {chapter.number:2d}. {chapter.title}  ({chapter.target_words} parole)")
    print(f"\nProssimo passo: python -m kdpfactory write {spec.slug}")
    return 0


def cmd_write(args) -> int:
    project, spec = open_project(args)
    outline = project.load_outline()
    client = make_client(args)
    only = [int(n) for n in args.only.split(",")] if args.only else None
    print(f"Scrittura capitoli{' ' + args.only if only else ''}…")
    writer.write_chapters(project, spec, outline, client, only=only, overwrite=args.overwrite)
    project.update_state(usage=client.usage_report())
    stats = pipeline.manuscript_stats(project, outline)
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f"\nProssimo passo: python -m kdpfactory build {spec.slug}")
    return 0


def cmd_build(args) -> int:
    project, spec = open_project(args)
    outline = project.load_outline()
    client = None if args.no_rewrite else make_client(args)
    print(f"Impaginazione di «{spec.title}»…")
    result = pipeline.build_until_in_range(
        project,
        spec,
        outline,
        client,
        max_iterations=args.iterations,
        tolerance=args.tolerance,
        allow_rewrite=not args.no_rewrite,
    )
    pipeline.build_package(project, spec, outline, result, guides=args.guides)
    pipeline.export_manuscript_markdown(project, spec, outline)
    if client:
        project.update_state(usage=client.usage_report())

    print("\nFile generati:")
    for path in sorted(project.build_dir.iterdir()):
        print(f"  {path}")
    low, high = pipeline.acceptance_window(spec, args.tolerance)
    status = "dentro" if result.in_range else "FUORI"
    print(
        f"\n{result.pages} pagine — {status} l'intervallo richiesto {low}-{high} "
        f"(limiti di progetto {kdpspecs.PROJECT_MIN_PAGES}-{kdpspecs.PROJECT_MAX_PAGES})."
    )
    return 0 if result.in_range else 1


def cmd_metadata(args) -> int:
    project, spec = open_project(args)
    outline = project.load_outline()
    client = make_client(args)
    chapters = writer.load_chapters(project, outline)
    if not chapters:
        raise SystemExit("Nessun capitolo scritto: esegui prima `write`.")
    sample = "\n\n".join(text for _, _, text in chapters[:2])
    print("Generazione della scheda prodotto…")
    from . import metadata as metadata_module

    meta = metadata_module.generate_metadata(spec, outline, sample, client)
    state = project.load_state()
    pages = state.get("build", {}).get("pagine") or spec.target_pages
    info = pipeline.write_metadata_files(project, spec, outline, meta, pages)
    project.update_state(usage=client.usage_report())
    print(f"Scheda salvata in {info['listing']}")
    for row in info["prezzi"]:
        print(
            f"  {row['marketplace']:<14} stampa {row['costo_stampa']:.2f} · "
            f"prezzo {row['prezzo_consigliato']:.2f} · royalty {row['royalty_per_copia']:.2f}"
        )
    return 0


def cmd_qa(args) -> int:
    project, spec = open_project(args)
    outline = project.load_outline()
    state = project.load_state()
    build = state.get("build", {})
    result = pipeline.BuildResult(
        pages=build.get("pagine", 0),
        words=build.get("parole", 0),
        interior_pdf=Path(build["interno_pdf"]) if build.get("interno_pdf") else None,
    )
    report = pipeline.run_qa(project, spec, outline, result)
    print(report.render())
    print(json.dumps(report.stats, ensure_ascii=False, indent=2))
    return 0 if report.ok else 1


def cmd_all(args) -> int:
    project, spec = open_project(args)
    client = make_client(args)

    if not project.outline_path.exists() or args.force:
        budget = budget_for(project, spec)
        print(planner.describe(budget, spec), "\n")
        print("1/5 · scaletta")
        outline = writer.generate_outline(spec, client, budget)
        project.ensure_dirs()
        outline.save(project.outline_path)
    else:
        outline = project.load_outline()
        print("1/5 · scaletta già presente")

    print("2/5 · scrittura capitoli")
    writer.write_chapters(project, spec, outline, client, overwrite=args.force)

    print("3/5 · impaginazione e convergenza sulle pagine")
    result = pipeline.build_until_in_range(
        project, spec, outline, client, max_iterations=args.iterations, tolerance=args.tolerance
    )

    print("4/5 · scheda prodotto")
    from . import metadata as metadata_module

    chapters = writer.load_chapters(project, outline)
    sample = "\n\n".join(text for _, _, text in chapters[:2])
    meta = metadata_module.generate_metadata(spec, outline, sample, client)
    pipeline.write_metadata_files(project, spec, outline, meta, result.pages)

    pipeline.build_package(project, spec, outline, result, guides=args.guides)
    pipeline.export_manuscript_markdown(project, spec, outline)

    print("5/5 · controlli")
    report = pipeline.run_qa(project, spec, outline, result)
    project.update_state(usage=client.usage_report())
    print(report.render())
    print("\nConsumo API:", json.dumps(client.usage_report(), ensure_ascii=False))
    print("\nFile generati:")
    for path in sorted(project.build_dir.iterdir()):
        print(f"  {path}")
    return 0 if report.ok and result.in_range else 1


def cmd_list(args) -> int:
    root = books_dir(args)
    if not root.exists():
        print(f"Nessun libro in {root}")
        return 0
    print(f"{'slug':<28} {'pagine':>7} {'capitoli':>9}  stato")
    for path in sorted(root.iterdir()):
        if not (path / "book.json").exists():
            continue
        project = BookProject(path)
        spec = project.load_spec()
        state = project.load_state()
        chapters = len(project.chapter_files())
        pages = state.get("build", {}).get("pagine", "—")
        stato = []
        if project.outline_path.exists():
            stato.append("scaletta")
        if chapters:
            stato.append(f"{chapters} capitoli")
        if state.get("build"):
            stato.append("impaginato")
        if (project.build_dir / "kdp-listing.md").exists():
            stato.append("scheda")
        print(f"{spec.slug:<28} {str(pages):>7} {chapters:>9}  {', '.join(stato) or 'nuovo'}")
    return 0


def cmd_specs(args) -> int:
    """Mostra le specifiche KDP per una combinazione formato/pagine."""
    pages = args.pages
    trim = args.trim
    paper = args.paper
    geo = kdpspecs.page_geometry(trim, pages)
    cover_w, cover_h = kdpspecs.cover_size_in(trim, pages, paper)
    print(f"Formato {trim} · {pages} pagine · carta {paper}")
    print(f"  margine interno minimo : {kdpspecs.gutter_margin_in(pages)}\"")
    print(f"  margine esterno minimo : {kdpspecs.outside_margin_in(False)}\"")
    text_area = f"{geo.text_width/kdpspecs.INCH:.2f}x{geo.text_height/kdpspecs.INCH:.2f}"
    print(f"  gabbia di testo usata  : {text_area}\"")
    print(f"  spessore dorso         : {kdpspecs.spine_width_in(pages, paper):.4f}\"")
    print(f"  copertina full-wrap    : {cover_w:.3f}x{cover_h:.3f}\"")
    spine_text = "consentito" if kdpspecs.spine_text_allowed(pages) else "no (sotto le 79 pagine)"
    print(f"  testo sul dorso        : {spine_text}")
    for problem in kdpspecs.validate_page_count(pages, paper):
        print(f"  ! {problem}")
    return 0


# --------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kdpfactory",
        description="Produzione di libri full content pronti per Amazon KDP (60-240 pagine).",
    )
    parser.add_argument("--books-dir", default=None, help="cartella dei progetti libro")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"modello Claude (default {DEFAULT_MODEL})")
    parser.add_argument(
        "--effort", default="high", choices=["low", "medium", "high", "xhigh", "max"]
    )
    parser.add_argument("--max-tokens", type=int, default=32000)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="nessuna chiamata API: genera testo segnaposto per collaudare la pipeline",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="crea un nuovo progetto libro")
    p.add_argument("title")
    p.add_argument("--slug-name", default=None)
    p.add_argument("--subtitle", default="")
    p.add_argument("--author", default="Autore Anonimo")
    p.add_argument("--language", default="it", choices=["it", "en"])
    p.add_argument("--topic", default="")
    p.add_argument("--audience", default="lettori generalisti")
    p.add_argument("--promise", default="")
    p.add_argument("--genre", default="non-fiction", choices=["non-fiction", "fiction"])
    p.add_argument("--pages", type=int, default=140, help="pagine obiettivo (60-240)")
    p.add_argument("--trim", default="6x9", choices=sorted(kdpspecs.TRIM_SIZES))
    p.add_argument("--paper", default="cream", choices=sorted(kdpspecs.PAPER_SPINE_FACTOR))
    p.add_argument("--chapters", type=int, default=0, help="0 = calcolato automaticamente")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("plan", help="mostra budget di pagine e parole")
    p.add_argument("slug")
    p.set_defaults(func=cmd_plan)

    p = sub.add_parser("outline", help="genera la scaletta")
    p.add_argument("slug")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_outline)

    p = sub.add_parser("write", help="scrive i capitoli mancanti")
    p.add_argument("slug")
    p.add_argument("--only", default=None, help="numeri di capitolo separati da virgola")
    p.add_argument("--overwrite", action="store_true")
    p.set_defaults(func=cmd_write)

    p = sub.add_parser("build", help="impagina, genera copertina ed EPUB")
    p.add_argument("slug")
    p.add_argument("--iterations", type=int, default=4)
    p.add_argument("--tolerance", type=float, default=0.05)
    p.add_argument("--no-rewrite", action="store_true", help="non riscrivere per centrare le pagine")
    p.add_argument("--guides", action="store_true", help="copertina con linee guida (non caricare)")
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("metadata", help="genera la scheda prodotto KDP")
    p.add_argument("slug")
    p.set_defaults(func=cmd_metadata)

    p = sub.add_parser("qa", help="controlli di qualità e conformità")
    p.add_argument("slug")
    p.set_defaults(func=cmd_qa)

    p = sub.add_parser("all", help="pipeline completa")
    p.add_argument("slug")
    p.add_argument("--iterations", type=int, default=4)
    p.add_argument("--tolerance", type=float, default=0.05)
    p.add_argument("--guides", action="store_true")
    p.add_argument("--force", action="store_true", help="rigenera scaletta e capitoli")
    p.set_defaults(func=cmd_all)

    p = sub.add_parser("list", help="elenco dei libri e stato")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("specs", help="specifiche KDP per formato e pagine")
    p.add_argument("--pages", type=int, default=140)
    p.add_argument("--trim", default="6x9", choices=sorted(kdpspecs.TRIM_SIZES))
    p.add_argument("--paper", default="cream", choices=sorted(kdpspecs.PAPER_SPINE_FACTOR))
    p.set_defaults(func=cmd_specs)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nInterrotto.", file=sys.stderr)
        return 130
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"Errore: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

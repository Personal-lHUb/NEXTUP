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

from . import agents, backup, coverbrief, coverdesign, diagnostica, kdpspecs, pipeline, planner, writer
from .llm import DEFAULT_MODEL, LLMClient, LLMConfig, api_key_present
from .models import BookProject, BookSpec, slugify

DEFAULT_BOOKS_DIR = Path(os.environ.get("KDPFACTORY_BOOKS_DIR", "")) if os.environ.get(
    "KDPFACTORY_BOOKS_DIR"
) else Path(__file__).resolve().parent.parent / "books"


def books_dir(args) -> Path:
    return Path(args.books_dir) if args.books_dir else DEFAULT_BOOKS_DIR


def open_project(args, *, riscrive: bool = False) -> tuple[BookProject, BookSpec]:
    root = books_dir(args) / args.slug
    if not root.exists():
        raise SystemExit(
            f"Libro '{args.slug}' non trovato in {books_dir(args)}.\n"
            f"Crealo con: python -m kdpfactory init \"Titolo\""
        )
    # Un libro con `puzzle.json` appartiene alla linea enigmistica: i comandi
    # della prosa che lo riscrivono lo rifarebbero da capo — capitoli segnaposto
    # al posto dei casi, stato sovrascritto — e il libro buono tornerebbe solo
    # dal backup. La guardia vale solo per chi scrive: `qa`, `review` e `plan`
    # leggono, e su un libro di enigmi devono poter girare (è l'agente di
    # impaginazione che ne misura la varietà delle pagine).
    # Niente scappatoia con `--force`: su `all` significa già «rigenera scaletta
    # e capitoli», ed è il flag che si aggiunge quando il primo tentativo viene
    # rifiutato. Chi vuole davvero convertire il libro alla prosa toglie il file.
    if riscrive and (root / "puzzle.json").exists():
        raise SystemExit(
            f"«{args.slug}» è un libro della linea enigmistica: c'è {root / 'puzzle.json'}.\n"
            "Questo comando appartiene alla linea prosa e riscriverebbe il libro da capo.\n"
            f"Usa:  python -m kdpfactory puzzle build {args.slug}\n"
            "Se il libro deve davvero passare alla prosa, togli prima puzzle.json."
        )
    project = BookProject(root)
    spec = project.load_spec()
    problems = spec.validate()
    if problems:
        raise SystemExit("book.json non valido:\n" + "\n".join(f"  - {p}" for p in problems))
    return project, spec


def budget_for(project: BookProject, spec: BookSpec) -> planner.PageBudget:
    """Budget del libro, tarato sulle pagine vere prima di spendere un token.

    Senza taratura il primo PDF esce circa il 10% sotto l'obiettivo — sempre
    fuori dalla finestra — e il libro si ricompra intero per rientrare. Due
    impaginazioni di prova costano qualche secondo di CPU e zero chiamate al
    modello, e il risultato resta in `state.json`: si paga una volta sola, e
    dopo il primo libro vero vince comunque la misura reale.
    """
    state = project.load_state()
    measured = state.get("words_per_page_measured")
    if not measured:
        print("Taratura delle pagine (due impaginazioni di prova, nessuna chiamata API)…")
        modello = planner.measure_page_model(spec)
        measured = planner.calibrate_words_per_page(spec, modello)
        previste = planner.predict_pages(spec, measured, modello)
        project.update_state(
            words_per_page_measured=round(measured, 1), modello_pagine=modello.to_dict()
        )
        print(
            f"  {measured:.0f} parole per pagina · previsione: {previste} pagine "
            f"(obiettivo {spec.target_pages})"
        )
    return planner.build_budget(spec, measured)


def save_backup(project: BookProject, args, reason: str, *, force: bool = False):
    """Copia di sicurezza di tutto il progetto, salvo `--no-backup`."""
    return backup.snapshot(project, reason, force=force)


BRIEF_TEMPLATE = """# Argomenti da affrontare — {title}

<!-- Scrivi qui, in italiano e senza formalità: questo file viene letto dagli
     agenti che progettano la scaletta e scrivono i capitoli. Le righe che
     cominciano con <!-- non vengono lette. Cancella pure quello che non serve. -->

## Di che cosa parla il libro
(due o tre frasi: il problema concreto del lettore e la soluzione che proponi)

## A chi si rivolge
(chi è, che cosa ha già provato, che cosa lo blocca)

## Che cosa deve saper fare il lettore alla fine
-
-

## Argomenti da coprire, in ordine libero
-
-
-

## Che cosa NON deve esserci
(temi da evitare, luoghi comuni del settore, tesi con cui non sei d'accordo)

## Materiale tuo da usare
(esperienze, casi, numeri, metodi che hai già: è ciò che rende il libro diverso
dagli altri sullo stesso tema)

## Tono
(come vuoi suonare: diretto, tecnico, informale, severo…)
"""

ASSETS_README = """# Materiali dell'autore

## Immagine di copertina

Metti qui il file e chiamalo `copertina` (l'estensione può essere .jpg, .jpeg,
.png, .webp, .tif):

    assets/copertina.jpg

Viene raddrizzata, ritagliata sulle proporzioni esatte della prima di copertina
(abbondanza inclusa), portata a 300 DPI e ripulita (contrasto, colore, nitidezza
leggeri). Il risultato finisce in `build/<slug>-copertina-immagine.jpg` e la
copertina lo usa come sfondo, con una velatura scura in alto e in basso perché
titolo e nome dell'autore restino leggibili.

**Risoluzione minima**: per un 6x9 pollici servono circa {px} pixel.
Sotto i 200 DPI reali il controllo qualità blocca il libro: in stampa si vede.

Per scegliere invece una copertina solo tipografica, senza immagine, imposta
`"cover_style": "tipografica"` in `book.json`.

## Altri file

Qualsiasi altra cosa metti qui (foto dell'autore, appunti, scansioni) viene
conservata e inclusa nelle copie di backup, ma non entra automaticamente nel
libro.
"""


def create_author_inputs(project: BookProject, spec: BookSpec) -> None:
    """Crea i due punti di ingresso dell'autore: brief e materiali."""
    from . import coverimage

    project.assets_dir.mkdir(parents=True, exist_ok=True)
    if not project.brief_path.exists():
        project.brief_path.write_text(
            BRIEF_TEMPLATE.format(title=spec.title), encoding="utf-8"
        )
    readme = project.assets_dir / "LEGGIMI.md"
    if not readme.exists():
        width_in, height_in = coverimage.front_panel_size_in(spec.trim)
        pixels = f"{round(width_in * coverimage.PRINT_DPI)}x{round(height_in * coverimage.PRINT_DPI)}"
        readme.write_text(ASSETS_README.format(px=pixels), encoding="utf-8")


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
        content_type=args.content_type,
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
    create_author_inputs(project, spec)
    print(f"Creato {project.spec_path}")
    # Il titolo l'hai scelto tu, quindi non si blocca niente: si avvisa adesso,
    # che cambiarlo costa una riga di `book.json`, invece che alla fine di
    # `all`, quando il libro è già scritto e pagato.
    for problema in coverdesign.title_problems(spec.title, trim=spec.trim):
        print(f"\n  ⚠ {problema}\n")
    print(f"Argomenti da affrontare  → {project.brief_path}")
    print(f"Immagine di copertina    → {project.assets_dir}/copertina.jpg (o .png)")
    print("Apri il file e completa `topic`, `audience`, `promise` e `notes`: più sono")
    print("precisi, più il libro sarà specifico e meno generico.\n")
    save_backup(project, args, "progetto creato")
    print(planner.describe(planner.build_budget(spec), spec))
    print(f"\nProssimo passo: python -m kdpfactory outline {slug}")
    return 0


def cmd_plan(args) -> int:
    project, spec = open_project(args)
    budget = budget_for(project, spec)
    print(planner.describe(budget, spec))
    print("\nMateriali dell'autore")
    brief = project.read_brief()
    if project.brief_is_filled():
        print(f"  Argomenti (brief.md) : compilato, {len(brief.split())} parole")
    elif brief:
        print(f"  Argomenti (brief.md) : modulo ancora da compilare → {project.brief_path}")
    else:
        print(f"  Argomenti (brief.md) : MANCANTE → scrivilo in {project.brief_path}")
    image = project.cover_image_path(spec)
    if image:
        print(f"  Immagine di copertina: {image.name} ({image.stat().st_size // 1024} KB)")
    else:
        print(f"  Immagine di copertina: nessuna → {project.assets_dir}/copertina.jpg")
        print("                         (senza immagine si usa la copertina tipografica)")
    if project.outline_path.exists():
        outline = project.load_outline()
        print("\nCapitoli in scaletta:")
        for chapter in outline.chapters:
            written = "✓" if project.chapter_path(chapter.number).exists() else " "
            print(f" [{written}] {chapter.number:2d}. {chapter.title}  ({chapter.target_words} parole)")
    return 0


def cmd_outline(args) -> int:
    project, spec = open_project(args, riscrive=True)
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
    project.update_state(budget=budget.to_dict())
    project.add_usage(client.usage_report())
    save_backup(project, args, "scaletta")
    print(f"\nScaletta salvata in {project.outline_path}")
    for chapter in outline.chapters:
        print(f"  {chapter.number:2d}. {chapter.title}  ({chapter.target_words} parole)")
    print(f"\nProssimo passo: python -m kdpfactory write {spec.slug}")
    return 0


def cmd_write(args) -> int:
    project, spec = open_project(args, riscrive=True)
    outline = project.load_outline()
    client = make_client(args)
    only = [int(n) for n in args.only.split(",")] if args.only else None
    if args.overwrite:
        # I capitoli vengono riscritti sul posto: prima si mette al sicuro
        # quello che c'è, anche se l'ultimo backup è recente.
        save_backup(project, args, "prima della riscrittura", force=True)
    print(f"Scrittura capitoli{' ' + args.only if only else ''}…")
    writer.write_chapters(project, spec, outline, client, only=only, overwrite=args.overwrite)
    project.add_usage(client.usage_report())
    save_backup(project, args, "capitoli scritti")
    stats = pipeline.manuscript_stats(project, outline)
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f"\nProssimo passo: python -m kdpfactory build {spec.slug}")
    return 0


def cmd_build(args) -> int:
    project, spec = open_project(args, riscrive=True)
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
        project.add_usage(client.usage_report())
    save_backup(project, args, f"impaginazione ({result.pages} pagine)")

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
    project, spec = open_project(args, riscrive=True)
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
    project.add_usage(client.usage_report())
    save_backup(project, args, "scheda prodotto")
    print(f"Scheda salvata in {info['listing']}")
    for row in info["prezzi"]:
        print(
            f"  {row['marketplace']:<14} stampa {row['costo_stampa']:.2f} · "
            f"prezzo {row['prezzo_consigliato']:.2f} · royalty {row['royalty_per_copia']:.2f}"
        )
    return 0


def cmd_copertina(args) -> int:
    """Il brief di copertina per uno strumento grafico. Nessuna chiamata API.

    Il motore disegna già una copertina che funziona in miniatura e non costa
    niente. Questo comando serve quando si vuole qualcosa che il motore non sa
    fare — un'atmosfera, una scena, un personaggio — e si è disposti a passare
    da uno strumento grafico: il sistema scrive il brief, tu porti l'immagine.
    """
    project, spec = open_project(args)
    state = project.load_state()
    pages = (state.get("build") or {}).get("pagine") or spec.target_pages
    meta_path = project.build_dir / "metadata.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    testi = (state.get("cover") or {}).get("testi") or {}
    copy = coverdesign.copy_from_dict(testi, spec) if testi else None

    project.ensure_dirs()
    output = project.build_dir / "copertina-brief.md"
    if output.exists():
        save_backup(project, args, "brief di copertina precedente", force=True)
    output.write_text(
        coverbrief.brief(spec, pages=pages, metadata=meta, copy=copy), encoding="utf-8"
    )
    save_backup(project, args, "brief di copertina")

    categoria = "medium-content" if spec.is_medium_content else "full-content"
    print(f"Brief di copertina [{categoria}, {pages} pagine]: {output}")
    print("\nIncollalo nello strumento grafico, poi salva l'immagine che torna in")
    print(f"  {project.assets_dir / 'copertina.jpg'}")
    print("e rilancia `build`: viene ritagliata sulla prima, portata a 300 DPI e")
    print("misurata. Se i pixel non bastano, il controllo qualità lo dice.")
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
    project, spec = open_project(args, riscrive=True)
    client = make_client(args)
    if args.force:
        save_backup(project, args, "prima della rigenerazione completa", force=True)

    if not project.outline_path.exists() or args.force:
        budget = budget_for(project, spec)
        print(planner.describe(budget, spec), "\n")
        print("1/6 · scaletta")
        outline = writer.generate_outline(spec, client, budget)
        project.ensure_dirs()
        outline.save(project.outline_path)
    else:
        outline = project.load_outline()
        print("1/6 · scaletta già presente")

    level = agents.QUALITY_LEVELS[args.qualita]

    print("2/6 · scrittura capitoli (ghostwriter)")
    writer.write_chapters(project, spec, outline, client, overwrite=args.force)

    if level["voce"]:
        print("3/6 · revisione di stile (voce)")
        agents.voice_pass(project, spec, outline, client)
    else:
        print("3/6 · revisione di stile saltata (livello di lavorazione)")

    print("4/6 · impaginazione e convergenza sulle pagine")
    result = pipeline.build_until_in_range(
        project, spec, outline, client, max_iterations=args.iterations, tolerance=args.tolerance
    )

    save_backup(project, args, f"impaginazione ({result.pages} pagine)")

    print("5/6 · scheda prodotto e copertina")
    from . import metadata as metadata_module

    chapters = writer.load_chapters(project, outline)
    sample = "\n\n".join(text for _, _, text in chapters[:2])
    meta = metadata_module.generate_metadata(spec, outline, sample, client)
    pipeline.write_metadata_files(project, spec, outline, meta, result.pages)
    # La copertina si costruisce prima del collegio: l'agente `copertina` non
    # legge, misura il PDF. Senza PDF non vede il testo fuori dall'area di
    # sicurezza — che è un bloccante da tipografia — e in cambio segnala una
    # copertina mancante su un libro che ce l'ha.
    pipeline.build_package(project, spec, outline, result, guides=args.guides)

    print(f"6/6 · collegio di revisione e controlli (livello «{args.qualita}»)")
    pagine_prima = result.pages
    result, _ = pipeline.editorial_pass(
        project,
        spec,
        outline,
        client,
        result,
        quality=args.qualita,
        tolerance=args.tolerance,
        max_iterations=args.iterations,
    )
    if result.pages != pagine_prima:
        # L'editor ha cambiato la lunghezza: dorso, prezzi e pagine della scheda
        # si calcolano sulle pagine e vanno rifatti sul numero definitivo,
        # altrimenti la copertina non combacia più con l'interno.
        pipeline.write_metadata_files(project, spec, outline, meta, result.pages)
        pipeline.build_package(project, spec, outline, result, guides=args.guides)

    pipeline.export_manuscript_markdown(project, spec, outline)

    report = pipeline.run_qa(project, spec, outline, result)
    project.add_usage(client.usage_report())
    print(report.render())
    save_backup(project, args, "pipeline completa")
    print("\nConsumo API:", json.dumps(client.usage_report(), ensure_ascii=False))
    print("\nFile generati:")
    for path in sorted(project.build_dir.iterdir()):
        print(f"  {path}")
    return 0 if report.ok and result.in_range else 1


def cmd_agents(args) -> int:
    if args.install:
        from .agents.install import install_claude_code_agents

        target = Path(args.install)
        written = install_claude_code_agents(target)
        print(f"Installati {len(written)} agenti come subagent di Claude Code in {target}:")
        for path in written:
            print(f"  {path}")
        print("\nDa Claude Code puoi ora invocarli per nome, per esempio:")
        print('  "usa lettore-cieco su books/<slug>/manuscript/03.md"')
        return 0
    print(agents.describe_panel())
    return 0


def cmd_review(args) -> int:
    project, spec = open_project(args)
    outline = project.load_outline()
    client = make_client(args)
    only = [int(n) for n in args.only.split(",")] if args.only else None
    names = (
        [n.strip() for n in args.agents.split(",")]
        if args.agents
        else list(agents.QUALITY_LEVELS[args.qualita]["reviewers"])
    )
    if not names:
        print(f"Il livello «{args.qualita}» non prevede revisione.")
        return 0
    print(f"Revisione di «{spec.title}» — agenti: {', '.join(names)}")
    report = agents.run_review(project, spec, outline, client, agent_names=names, only=only)
    project.add_usage(client.usage_report())
    save_backup(project, args, "revisione del collegio")
    print(report.render())
    print(f"\nRapporto salvato in {project.build_dir / 'revisioni.md'}")
    if report.blocking:
        print("Ci sono segnalazioni bloccanti: risolvile prima di pubblicare.")
    print(f"\nPer applicarle: python -m kdpfactory revise {spec.slug}")
    return 0


def cmd_revise(args) -> int:
    project, spec = open_project(args, riscrive=True)
    outline = project.load_outline()
    report = agents.ReviewReport.load(project)
    if not report.findings:
        raise SystemExit(
            f"Nessuna revisione da applicare. Esegui prima: python -m kdpfactory review {spec.slug}"
        )
    client = make_client(args)
    only = [int(n) for n in args.only.split(",")] if args.only else None
    save_backup(project, args, "prima delle modifiche dell'editor", force=True)
    print(f"L'editor applica le segnalazioni (da «{args.severita}» in su)…")
    revised = agents.apply_revisions(
        project, spec, outline, client, report, min_severity=args.severita, only=only
    )
    project.add_usage(client.usage_report())
    save_backup(project, args, "modifiche dell'editor")
    if not revised:
        print("Nessun capitolo da modificare.")
        return 0
    print(f"Capitoli rivisti: {', '.join(str(n) for n in revised)}")
    print(f"\nRimpagina per ricontrollare le pagine: python -m kdpfactory build {spec.slug}")
    return 0


def cmd_puzzle(args) -> int:
    from .puzzle import book as puzzle_book

    root = books_dir(args) / args.slug
    if args.action == "new":
        if root.exists() and not args.force:
            raise SystemExit(f"Esiste già {root}. Usa --force per sovrascrivere.")
        from .puzzle import theme as puzzle_theme

        project = BookProject(root)
        project.ensure_dirs()
        # Prima l'ambientazione: è lei che dice come si chiama il libro.
        ambientazione_file = puzzle_theme.scrivi_modello(
            puzzle_theme.ambientazione_path(root)
        )
        ambientazione = puzzle_theme.carica(ambientazione_file)
        spec = puzzle_book.default_book_spec(args.slug, args.author, ambientazione)
        spec.save(project.spec_path)
        puzzle_spec = puzzle_book.PuzzleSpec(seed=args.seed)
        puzzle_spec.save(puzzle_book.puzzle_spec_path(project))
        save_backup(project, args, "libro di enigmi creato")
        print(f"Creato {project.spec_path} e {puzzle_book.puzzle_spec_path(project)}")
        print(f"Ambientazione da scrivere → {ambientazione_file}")
        print(f"Seme: {puzzle_spec.seed}")
        print("\nApri l'ambientazione e sostituisci i contenuti di collaudo: è lì che")
        print("decidi di che cosa parla il libro. Il file spiega ogni campo.")
        print(f"\nPoi: python -m kdpfactory puzzle build {args.slug}")
        return 0

    project, spec = open_project(args)
    puzzle_spec = puzzle_book.PuzzleSpec.load(puzzle_book.puzzle_spec_path(project))
    if args.seed:
        puzzle_spec.seed = args.seed
        puzzle_spec.save(puzzle_book.puzzle_spec_path(project))

    print(f"Generazione di «{spec.title}» (seme {puzzle_spec.seed})…")
    result = puzzle_book.build(project, spec, puzzle_spec, guides=args.guides)
    generated = result["book"]
    print(
        f"  {len(generated.cases)} casi + finale · {generated.suspects_total} sospetti · "
        f"{generated.clues_total} indizi · {result['pages']} pagine"
    )
    report = puzzle_book.check(project, spec, result["pages"], result["interior"])
    print(report.render())
    for row in result["prices"]:
        print(
            f"  {row.marketplace:<14} stampa {row.symbol}{row.printing_cost:.2f} · "
            f"prezzo {row.symbol}{row.suggested_price:.2f} · royalty {row.symbol}{row.royalty:.2f}"
        )
    print("\nFile generati:")
    for path in sorted(project.build_dir.iterdir()):
        print(f"  {path}")
    return 0 if report.ok else 1


def cmd_concorrente(args) -> int:
    from . import concorrente as acquisizione

    root = books_dir(args) / args.slug
    project = BookProject(root)

    if args.action == "new":
        if acquisizione.pagina_path(project).exists() and not args.force:
            raise SystemExit(
                f"Esiste già {acquisizione.pagina_path(project)}. "
                "Usa --force per ricominciare da un modulo vuoto."
            )
        percorso = acquisizione.prepara(project, args.asin)
        print(f"Creato {percorso}")
        print("\nIncolla lì dentro la pagina Amazon del libro, recensioni comprese.")
        print("Le recensioni da 2 e 3 stelle sono la parte che vale di più: sono i")
        print("clienti che hanno pagato e dicono quale libro avrebbero voluto.")
        print(f"\nPoi: python -m kdpfactory concorrente build {args.slug}")
        return 0

    if project.spec_path.exists() and not args.force:
        raise SystemExit(
            f"Esiste già {project.spec_path}.\n"
            "Usa --force per riscrivere la scheda del libro dal piano di acquisizione."
        )

    client = make_client(args)
    risultato = acquisizione.analizza(project, client, asin=args.asin)
    print(acquisizione.render(risultato))

    spec = acquisizione.scrivi(project, risultato, args.author)
    project.add_usage(client.usage_report())
    save_backup(project, args, f"acquisizione da ASIN {args.asin or '(non indicato)'}")

    print(f"\nScritti {project.spec_path} e {project.brief_path}")
    print(f"Dettaglio dell'analisi: {acquisizione.acquisizione_path(project)}")
    print(f"\nRileggi la scheda e il brief, poi: python -m kdpfactory all {spec.slug}")
    # I bloccanti fermano la scrittura da soli, dentro `scrivi()`: se siamo qui
    # la scheda esiste ed è valida. Uscire con 1 per una nota di stile faceva
    # spezzare `concorrente build && all`, che è la corsa per cui il comando
    # esiste.
    if risultato.segnalazioni:
        print(
            f"\n{len(risultato.segnalazioni)} segnalazioni non bloccanti: "
            "rileggile qui sopra prima di far scrivere il libro."
        )
    return 0


def cmd_backup(args) -> int:
    project, spec = open_project(args)
    backup_dir = Path(args.backup_dir) if args.backup_dir else None

    if args.restore:
        result = backup.restore(project, args.restore, backup_dir=backup_dir)
        print(
            f"Ripristinato lo snapshot {result.snapshot.stamp} "
            f"({len(result.restored)} file) di «{spec.title}»."
        )
        if result.safety:
            print(f"Lo stato precedente è al sicuro in {result.safety.path}")
        return 0

    if args.prune:
        removed = backup.prune(project, args.prune, backup_dir=backup_dir)
        print(f"Eliminati {len(removed)} snapshot, tenuti gli ultimi {args.prune}.")
        return 0

    if args.now:
        result = save_backup(project, args, args.reason or "copia manuale", force=True)
        if result is None:
            print("Niente da copiare.")
        return 0

    snapshots = backup.list_snapshots(project, backup_dir)
    if not snapshots:
        print(f"Nessun backup per «{spec.title}» in {backup.backup_root(project, backup_dir)}")
        return 0
    count, total = backup.usage(project, backup_dir)
    print(f"Backup di «{spec.title}» in {backup.backup_root(project, backup_dir)}")
    for item in snapshots:
        print(f"  {item.describe()}")
    print(f"  ── {count} snapshot, {total / 1_048_576:.1f} MB")
    print(f"\nPer tornare indietro: python -m kdpfactory backup {spec.slug} --restore <id>")
    return 0


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


def cmd_diagnostica(args) -> int:
    """I fatti su cui lavora il team di miglioramento. Nessuna chiamata API."""
    root = books_dir(args)
    if not root.exists():
        print(f"Nessun libro in {root}")
        return 0
    project_root = Path(__file__).resolve().parent.parent
    system = diagnostica.analyse(root, project_root, includi_banchi=args.banchi)

    output = Path(args.output) if args.output else project_root / "diagnostica.json"
    output.write_text(
        json.dumps(system.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if args.json:
        print(json.dumps(system.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(diagnostica.render(system))
        print(f"Rapporto completo: {output}")
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
    parser.add_argument(
        "--backup-dir",
        default=None,
        help=f"cartella delle copie di sicurezza (default {backup.DEFAULT_BACKUP_DIR})",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="non copiare i file generati nella cartella di backup",
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
    p.add_argument(
        "--content-type",
        dest="content_type",
        default="full",
        choices=["full", "medium"],
        help="full: opera a testo pieno · medium: libro interattivo, ogni pagina diversa",
    )
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

    p = sub.add_parser("agents", help="elenco del collegio editoriale")
    p.add_argument(
        "--install",
        nargs="?",
        const=".claude/agents",
        default=None,
        metavar="CARTELLA",
        help="installa gli agenti come subagent di Claude Code (default .claude/agents)",
    )
    p.set_defaults(func=cmd_agents)

    p = sub.add_parser("review", help="fa leggere il libro al collegio di revisione")
    p.add_argument("slug")
    p.add_argument(
        "--agents",
        default=None,
        help="agenti da usare, separati da virgola (default: quelli del livello scelto)",
    )
    p.add_argument(
        "--qualita", default=agents.DEFAULT_QUALITY, choices=sorted(agents.QUALITY_LEVELS)
    )
    p.add_argument("--only", default=None, help="numeri di capitolo separati da virgola")
    p.set_defaults(func=cmd_review)

    p = sub.add_parser("revise", help="l'editor applica le segnalazioni raccolte")
    p.add_argument("slug")
    p.add_argument(
        "--severita",
        default="importante",
        choices=["bloccante", "importante", "minore"],
        help="applica le segnalazioni da questa gravità in su (default: importante)",
    )
    p.add_argument("--only", default=None, help="numeri di capitolo separati da virgola")
    p.set_defaults(func=cmd_revise)

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

    p = sub.add_parser(
        "copertina",
        help="brief di copertina da dare a uno strumento grafico (nessuna chiamata API)",
    )
    p.add_argument("slug")
    p.set_defaults(func=cmd_copertina)

    p = sub.add_parser("qa", help="controlli di qualità e conformità")
    p.add_argument("slug")
    p.set_defaults(func=cmd_qa)

    p = sub.add_parser("all", help="pipeline completa")
    p.add_argument("slug")
    p.add_argument(
        "--qualita",
        default=agents.DEFAULT_QUALITY,
        choices=sorted(agents.QUALITY_LEVELS),
        help="livello di lavorazione: quali agenti entrano in gioco (vedi `agents`)",
    )
    p.add_argument("--iterations", type=int, default=4)
    p.add_argument("--tolerance", type=float, default=0.05)
    p.add_argument("--guides", action="store_true")
    p.add_argument("--force", action="store_true", help="rigenera scaletta e capitoli")
    p.set_defaults(func=cmd_all)

    p = sub.add_parser("puzzle", help="libri di enigmi di deduzione (senza chiamate API)")
    p.add_argument("action", choices=["new", "build"])
    p.add_argument("slug")
    p.add_argument("--seed", type=int, default=0, help="seme: stesso seme, stesso libro")
    p.add_argument("--author", default="Iris Vane")
    p.add_argument("--guides", action="store_true", help="copertina con linee guida")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_puzzle)

    p = sub.add_parser(
        "concorrente",
        help="da una scheda Amazon incollata alla scheda di un libro nuovo che la batte",
    )
    p.add_argument("action", choices=["new", "build"])
    p.add_argument("slug")
    p.add_argument("--asin", default="", help="ASIN del libro di riferimento")
    p.add_argument("--author", default="Autore Anonimo", help="autore del libro nuovo")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_concorrente)

    p = sub.add_parser("backup", help="copie di sicurezza: elenco, copia, ripristino")
    p.add_argument("slug")
    p.add_argument("--now", action="store_true", help="fai subito una copia")
    p.add_argument("--reason", default="", help="etichetta della copia manuale")
    p.add_argument(
        "--restore",
        default=None,
        metavar="ID",
        help="ripristina lo snapshot indicato (`latest` per l'ultimo)",
    )
    p.add_argument(
        "--prune", type=int, default=None, metavar="N", help="tieni solo gli ultimi N snapshot"
    )
    p.set_defaults(func=cmd_backup)

    p = sub.add_parser("list", help="elenco dei libri e stato")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser(
        "diagnostica",
        help="misura tutti i libri e il sistema: i fatti per il team di miglioramento",
    )
    p.add_argument("--json", action="store_true", help="stampa il rapporto completo in JSON")
    p.add_argument("--output", help="dove salvare il rapporto (default: diagnostica.json)")
    p.add_argument(
        "--banchi",
        action="store_true",
        help="misura anche i banchi di prova (collaudo): normalmente restano fuori",
    )
    p.set_defaults(func=cmd_diagnostica)

    p = sub.add_parser("specs", help="specifiche KDP per formato e pagine")
    p.add_argument("--pages", type=int, default=140)
    p.add_argument("--trim", default="6x9", choices=sorted(kdpspecs.TRIM_SIZES))
    p.add_argument("--paper", default="cream", choices=sorted(kdpspecs.PAPER_SPINE_FACTOR))
    p.set_defaults(func=cmd_specs)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    # La preferenza vale per tutta l'esecuzione: anche la pipeline e gli agenti
    # mettono al sicuro i file prima di sovrascriverli.
    backup.configure(enabled=not args.no_backup, directory=args.backup_dir)
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

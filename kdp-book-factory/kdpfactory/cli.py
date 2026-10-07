"""Interfaccia a riga di comando.

    python -m kdpfactory init "Titolo del libro" --pages 140
    python -m kdpfactory all titolo-del-libro
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

from . import (
    agents,
    avvio,
    backup,
    corriere,
    coverbrief,
    coverdesign,
    coverimage,
    cowork,
    decisioni,
    diagnostica,
    direzioni,
    higgsfield,
    imagebrief,
    kdpspecs,
    manuale,
    parolechiave,
    pipeline,
    planner,
    produzione,
    pubbliche,
    richiesteimmagini,
    writer,
)
from . import figure as figure_module
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
    versione = state.get("taratura_versione")
    superata = bool(state.get("modello_pagine")) and versione not in (
        planner.CALIBRATION_VERSION, planner.CALIBRATION_FROM_PDF
    )
    if not measured or superata:
        print("Taratura delle pagine (due impaginazioni di prova, nessuna chiamata API)…")
        modello = planner.measure_page_model(spec)
        measured = planner.calibrate_words_per_page(spec, modello)
        previste = planner.predict_pages(spec, measured, modello)
        project.update_state(
            words_per_page_measured=round(measured, 1),
            modello_pagine=modello.to_dict(),
            taratura_versione=planner.CALIBRATION_VERSION,
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

    # Lo stesso cancello della linea manuale: una scaletta sbagliata la pagano
    # tutti i capitoli, e qui correggerla costa un file, non trenta chiamate.
    from .agents.scaletta import esamina as esamina_scaletta
    from .manuale import pagine_della_scaletta, rapporto_rilievi

    rilievi = esamina_scaletta(
        outline,
        spec,
        brief=spec.brief or "",
        capitoli_attesi=budget.chapters,
        pagine_previste=pagine_della_scaletta(project, spec, budget, outline),
    )
    print("\n" + rapporto_rilievi(rilievi, outline))
    bloccanti = [r for r in rilievi if r.severity == "bloccante"]
    if bloccanti:
        print(
            f"\n{len(bloccanti)} rilievi bloccanti: correggi {project.outline_path} "
            f"prima di `write {spec.slug}`."
        )
        return 1
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
    # L'impaginazione non chiama il modello. Lo chiama solo la riscrittura dei
    # capitoli quando le pagine non tornano — che è un di più, non il lavoro:
    # senza credenziale si impagina lo stesso e si dice di quanto si sbaglia,
    # invece di rifiutarsi di stampare un libro già scritto.
    riscrive = not args.no_rewrite
    if riscrive and not args.dry_run and not api_key_present():
        print(
            "Nessuna credenziale: impagino senza riscrivere i capitoli.\n"
            "  Se le pagine non rientrano, te lo dico e decidi tu che cosa tagliare."
        )
        riscrive = False
    client = make_client(args) if riscrive else None
    print(f"Impaginazione di «{spec.title}»…")
    result = pipeline.build_until_in_range(
        project,
        spec,
        outline,
        client,
        max_iterations=args.iterations,
        tolerance=args.tolerance,
        allow_rewrite=riscrive,
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
    if args.scegli:
        return _scegli_copertina(project, args)
    if getattr(args, "scarica_generate", False):
        return _scarica_generate(project, args)
    if getattr(args, "direzione", 0):
        return _scegli_direzione(project, spec, args)
    if getattr(args, "direzioni", False) or getattr(args, "bozzetti", False):
        return _direzioni_copertina(project, spec, args)
    if args.preferisci or args.scarta:
        dividi = lambda testo: [k.strip() for k in testo.split(",") if k.strip()]  # noqa: E731
        try:
            direzione = coverbrief.registra_direzione(
                dividi(args.preferisci), dividi(args.scarta), args.perche,
                quando=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            )
        except ValueError as errore:
            raise SystemExit(str(errore)) from errore
        print("Direzione delle copertine: preferiti "
              + (", ".join(p["trattamento"] for p in direzione["preferiti"]) or "nessuno")
              + " · scartati "
              + (", ".join(s["trattamento"] for s in direzione["scartati"]) or "nessuno"))
        print(f"Registrata in {coverbrief.DIREZIONE_APPRESA}: vale per i prompt da qui in poi.")
        return 0
    pages, meta, copy, rivale = _dati_copertina(project, spec)
    risposte = avvio.leggi(project)
    # La direzione d'arte scelta dall'autore, se le direzioni ci sono: le varianti
    # finali e il prompt da incollare nascono da lei, non dalla categoria.
    dati_direzioni = direzioni.leggi(project)
    scelta = direzioni.scelta(dati_direzioni)
    direzione = scelta[1] if scelta else None

    project.ensure_dirs()
    output = project.build_dir / "copertina-brief.md"
    if output.exists():
        save_backup(project, args, "brief di copertina precedente", force=True)
    output.write_text(
        coverbrief.brief(spec, pages=pages, metadata=meta, copy=copy, concorrente=rivale),
        encoding="utf-8",
    )
    save_backup(project, args, "brief di copertina")

    panel_w, panel_h = coverimage.front_panel_size_in(spec.trim)
    minimo = (math.ceil(panel_w * coverbrief.FRONT_DPI), math.ceil(panel_h * coverbrief.FRONT_DPI))

    # Il prompt da incollare in ChatGPT: gli stessi dati del brief, senza le
    # specifiche di stampa che a un generatore d'immagini fanno disegnare un wrap.
    prompt = coverbrief.prompt_da_incollare(
        spec, pages=pages, metadata=meta, copy=copy, concorrente=rivale, direzione=direzione,
    )
    incollare = project.build_dir / richiesteimmagini.CHATGPT_COPERTINA
    if incollare.exists():
        save_backup(project, args, "prompt da incollare precedente", force=True)
    incollare.write_text(richiesteimmagini.testo_copertina(spec.slug, prompt), encoding="utf-8")
    save_backup(project, args, "prompt da incollare")

    # Chi genera l'illustrazione: Higgsfield, da questa sessione (`--genera`).
    radice = Path(__file__).resolve().parent.parent
    con_higgsfield = higgsfield.attivo(radice)

    categoria = "medium-content" if spec.is_medium_content else "full-content"
    print(f"Brief di copertina [{categoria}, {pages} pagine]: {output}")
    print(f"Da incollare in ChatGPT (progetto «{richiesteimmagini.PROGETTO_CHATGPT}»): {incollare}")
    print("\n" + "-" * 72 + "\n" + prompt + "\n" + "-" * 72)
    print("\nIncollalo nello strumento grafico, poi salva l'immagine che torna in")
    print(f"  {project.assets_dir / 'copertina.jpg'}")
    print("e rilancia `build`: viene ritagliata sulla prima, portata a 300 DPI e")
    print("misurata. Se i pixel non bastano, il controllo qualità lo dice.")
    if risposte and risposte.copertina and not rivale:
        print(f"\n! All'avvio è stata chiesta una copertina più attraente del concorrente, ma\n"
              f"  {avvio.copertina_path(project)} è vuoto: il brief non sa da che cosa distinguersi.")
    if dati_direzioni is not None and direzione is None:
        print(f"\nLe direzioni d'arte ci sono ({direzioni.FILE}) ma l'autore non ne ha scelta\n"
              f"nessuna: le varianti finali aspettano `copertina {spec.slug} --direzione N`.")
        if args.genera:
            return 1
    if args.genera:
        return _genera_copertina(project, args, spec, pages, meta, copy, rivale, minimo, radice,
                                 direzione)
    if con_higgsfield:
        print(f"\nLe varianti le genera Higgsfield: python3 -m kdpfactory copertina {spec.slug} --genera")
    return 0


def _dati_copertina(project: BookProject, spec: BookSpec) -> tuple:
    """Pagine, scheda, testi di copertina e copertina da battere: i dati dei prompt."""
    state = project.load_state()
    pages = (state.get("build") or {}).get("pagine") or spec.target_pages
    meta_path = project.build_dir / "metadata.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    testi = (state.get("cover") or {}).get("testi") or {}
    copy = coverdesign.copy_from_dict(testi, spec) if testi else None
    # Se all'avvio l'autore ha chiesto una copertina più attraente di quella
    # del concorrente, il brief riceve la descrizione di quella da battere.
    risposte = avvio.leggi(project)
    rivale = avvio.leggi_copertina(project) if risposte and risposte.copertina else ""
    return pages, meta, copy, rivale


def _direzioni_copertina(project: BookProject, spec: BookSpec, args) -> int:
    """Le tre direzioni d'arte: il file da compilare, i suoi problemi, i prompt dei bozzetti.

    Le direzioni le scrive l'agente `copertina`; il sistema chiede a Cowork lo
    studio delle copertine della categoria, controlla le direzioni e ne scrive i
    prompt — gli stessi delle varianti finali — più il riepilogo per l'autore.
    """
    fatti: list[str] = []
    if not direzioni.risposta_studio(project).exists():
        risposte = avvio.leggi(project)
        mercato = risposte.mercato if risposte else ("amazon.it" if spec.language == "it" else "amazon.com")
        radice = Path(__file__).resolve().parent.parent
        nome, testo = direzioni.richiesta_studio(
            spec.slug, mercato, spec.categories[0] if spec.categories else "",
            cowork.configurazione(radice), asin=risposte.asin if risposte else "",
        )
        _scrivi_richiesta(project, args, project.root / "concorrente" / nome, testo, fatti)
        for percorso in fatti:
            print(f"Richiesta a Cowork (ruolo concorrente): {percorso}")

    dati = direzioni.leggi(project)
    if dati is None or direzioni.stato(project) == "da-compilare":
        file = direzioni.percorso(project)
        if dati is None:
            file.write_text(json.dumps(direzioni.modello(spec), ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
            save_backup(project, args, "direzioni di copertina da compilare")
        print(f"Da compilare dall'agente `copertina`: {file}")
        print(f"  legge: {direzioni.risposta_studio(project).relative_to(project.root)} (lo studio "
              "della categoria), concorrente/, build/vetrina.md, docs/copertine.md e")
        print(f"  {coverbrief.DIREZIONE_APPRESA.name} (le scelte dell'autore sui libri prima).")
        return 0
    problemi = direzioni.problemi(dati)
    if problemi:
        print(f"{direzioni.FILE}: {len(problemi)} problemi, li corregge l'agente `copertina`.")
        for problema in problemi:
            print(f"  - {problema}")
        return 1

    pages, meta, copy, rivale = _dati_copertina(project, spec)
    if (project.build_dir / direzioni.PROMPT_BOZZETTI).exists():
        save_backup(project, args, "prompt dei bozzetti precedenti", force=True)
    prompt_file, riepilogo = direzioni.scrivi_bozzetti(
        project, spec, dati, pages=pages, metadata=meta, copy=copy, concorrente=rivale,
    )
    save_backup(project, args, "prompt dei bozzetti delle tre direzioni")
    print(f"Le tre direzioni, per l'autore: {riepilogo}")
    print(f"I prompt dei bozzetti: {prompt_file}")
    for numero, d in enumerate(dati["direzioni"], 1):
        print(f"  {numero}. {d['nome']} — {d['composizione']}, palette {d['palette']}")
    if args.bozzetti and args.genera:
        return _genera_bozzetti(project, args, prompt_file)
    print(f"\nI bozzetti, a bassa risoluzione: copertina {spec.slug} --bozzetti --genera")
    print("(o il connettore Higgsfield con gli stessi prompt). Poi la scelta è dell'autore:")
    print(f"copertina {spec.slug} --direzione N --perche \"…\".")
    return 0


def _genera_bozzetti(project: BookProject, args, prompt_file: Path) -> int:
    """Un bozzetto per direzione, con Higgsfield alla risoluzione più bassa."""
    motivo = higgsfield.pronto()
    if motivo:
        raise SystemExit(f"Higgsfield non è pronto: {motivo}.")
    radice = Path(__file__).resolve().parent.parent
    modello = higgsfield.configurazione(radice).get("modello") or higgsfield.MODELLO_IMMAGINI
    schema = higgsfield.schema(modello)
    voci = []
    for voce in json.loads(prompt_file.read_text(encoding="utf-8")):
        destinazione = project.assets_dir / f"bozzetto-{voce['direzione']}.png"
        if destinazione.exists():
            save_backup(project, args, f"bozzetto {voce['direzione']} precedente", force=True)
        print(f"Bozzetto {voce['direzione']} «{voce['nome']}» con {modello}…", flush=True)
        generata = higgsfield.genera(voce["prompt"], destinazione, proporzione="2:3",
                                     modello=modello, schema_modello=schema, bozza=True)
        voci.append({**voce, "file": str(destinazione), "url": generata.url, "job": generata.job,
                     "modello": modello, "pixel": [generata.larghezza, generata.altezza],
                     "generata": generata.quando, "via": "CLI Higgsfield"})
        print(f"  {destinazione.name}: {generata.larghezza} x {generata.altezza} px")
    direzioni.registra_bozzetti(project, voci)
    save_backup(project, args, f"{len(voci)} bozzetti delle direzioni")
    print("\nLa scelta è dell'autore, senza silenzio-assenso: copertina <slug> --direzione N.")
    return 0


def _scegli_direzione(project: BookProject, spec: BookSpec, args) -> int:
    """La direzione scelta dall'autore: in `book.json` palette, composizione e carattere."""
    # Lo snapshot prende book.json e le direzioni insieme: sono i due file che cambiano.
    save_backup(project, args, "book.json e direzioni prima della direzione scelta", force=True)
    try:
        d = direzioni.scegli(project, args.direzione, args.perche,
                             quando=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    except ValueError as errore:
        raise SystemExit(str(errore)) from errore
    spec.cover_theme = d["palette"]
    spec.cover_layout = d["composizione"]
    spec.cover_type = d.get("tipografia") or "auto"
    spec.save(project.spec_path)
    save_backup(project, args, f"copertina: direzione {args.direzione}")
    print(f"Direzione {args.direzione} «{d['nome']}»: palette {d['palette']}, titolo "
          f"{d['composizione']}, carattere {spec.cover_type}. Scritta in book.json e in "
          f"{coverbrief.DIREZIONE_APPRESA.name}.")
    print(f"Poi: copertina {spec.slug} --genera (le varianti finali, alla risoluzione più alta).")
    return 0


def cmd_immagini(args) -> int:
    """Le figure dell'interno: il piano, i prompt di quelle da generare, le pubbliche.

    Il piano (`figure.json`, dell'architetto) dice se il libro ha bisogno di
    figure e, per ognuna, se si genera o si cerca fra le immagini pubbliche. Le
    figure si dichiarano nel manoscritto anche prima che le immagini esistano:
    così il conteggio pagine tiene già il loro posto. Nessuna chiamata API.
    """
    project, spec = open_project(args)
    piano = figure_module.leggi_piano(project.root)
    if getattr(args, "piano", False):
        return _piano_figure(project, args, piano)
    if getattr(args, "cerca", False):
        return _cerca_pubbliche(project, args, piano)
    if getattr(args, "prendi", ""):
        return _prendi_pubblica(project, args, spec, piano)

    outline = project.load_outline()
    capitoli = writer.load_chapters(project, outline)
    if not capitoli:
        raise SystemExit(
            "Nessun capitolo scritto: le figure si dichiarano nel manoscritto, "
            "e il manoscritto non c'è ancora."
        )

    figure_trovate: list = []
    for numero, _titolo, markdown in capitoli:
        figure_trovate.extend(
            figure_module.figure_del_manoscritto(markdown, project.assets_dir, numero)
        )
    titoli = {numero: titolo for numero, titolo, _ in capitoli}
    mondo = (piano or {}).get("mondo", "")

    if not figure_trovate:
        if piano and piano.get("servono") is False:
            print(f"«{spec.title}»: il piano delle figure dice che non ne servono — "
                  f"{piano.get('perche', '')}")
            return 0
        print(f"«{spec.title}» non dichiara nessuna figura.")
        if piano is None:
            print(f"E non ha il piano delle figure: `immagini {spec.slug} --piano`, poi l'architetto.")
        print("\nPer aggiungerne una, scrivi nel manoscritto una riga così:")
        print("  ![che cosa deve mostrare l'immagine](immagini/03-nome.jpg)")
        print("  (didascalia facoltativa, fra parentesi, sulla riga dopo)")
        print("\nIl libro si impagina anche senza il file: al suo posto resta un")
        print("segnaposto della misura giusta, e il conteggio pagine è già definitivo.")
        return 0

    def pubblica(figura) -> bool:
        voce = figure_module.voce_del_piano(piano, figura.percorso)
        return bool(voce) and voce.get("fonte") == "pubblica"

    da_generare = [f for f in figure_trovate if not pubblica(f)]
    project.ensure_dirs()
    output = project.build_dir / "immagini-brief.md"
    if output.exists():
        save_backup(project, args, "prompt delle immagini precedenti", force=True)
    output.write_text(imagebrief.brief(spec, da_generare, mondo=mondo, titoli=titoli), encoding="utf-8")
    save_backup(project, args, "prompt delle immagini")

    mancanti = [f for f in da_generare if not f.esiste]
    da_cercare = sum(1 for f in figure_trovate if pubblica(f) and not f.esiste)
    print(f"Prompt delle immagini: {output}")
    print(f"  {len(figure_trovate)} figure dichiarate · {len(mancanti)} da generare · "
          f"{da_cercare} da cercare fra le pubbliche")
    for figura in figure_trovate:
        segno = " " if figura.esiste else "·"
        fonte = "pubblica" if pubblica(figura) else "generata"
        print(f"    {segno} cap. {figura.capitolo:>2}  {figura.percorso}  ({fonte})")
    if da_cercare:
        print(f"\nLe pubbliche (solo pubblico dominio e CC0): immagini {spec.slug} --cerca")
    if mancanti:
        print(f"\nSalva le immagini in {figure_module.cartella(project.assets_dir)}")
        print("poi rilancia `build` e `qa`.")
        prompts = [(f.percorso, imagebrief.prompt_incollabile(spec, f, mondo=mondo, titoli=titoli))
                   for f in mancanti]
        incollare = project.build_dir / richiesteimmagini.CHATGPT_FIGURE
        if incollare.exists():
            save_backup(project, args, "prompt delle figure da incollare precedenti", force=True)
        incollare.write_text(richiesteimmagini.testo_figure(spec.slug, prompts), encoding="utf-8")
        save_backup(project, args, "prompt delle figure da incollare")
        print(f"Da incollare in ChatGPT (progetto «{richiesteimmagini.PROGETTO_CHATGPT}»): {incollare}")
        radice = Path(__file__).resolve().parent.parent
        if args.genera:
            return _genera_figure(project, args, spec, mancanti, radice, mondo, titoli)
        if higgsfield.attivo(radice):
            print(f"Le figure le genera Higgsfield: python3 -m kdpfactory immagini {spec.slug} --genera")
            return 0
    return 0


def _piano_figure(project: BookProject, args, piano: dict | None) -> int:
    """Il piano delle figure da compilare, o com'è adesso."""
    file = figure_module.piano_path(project.root)
    if piano is None:
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(json.dumps(figure_module.modello_piano(), ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
        save_backup(project, args, "piano delle figure da compilare")
        print(f"Da compilare dall'architetto, con la scaletta: {file}")
        return 0
    servono = {True: "sì", False: "no", None: "da decidere"}.get(piano.get("servono"), "?")
    print(f"Piano delle figure ({file}): servono {servono} — {piano.get('perche', '')}")
    for voce in piano.get("figure") or []:
        print(f"  cap. {voce.get('capitolo', '?'):>2}  {voce.get('percorso')}  ({voce.get('fonte')})"
              + ("  · provenienza registrata" if voce.get("provenienza") else ""))
    return 0


def _cerca_pubbliche(project: BookProject, args, piano: dict | None,
                     apri=urllib.request.urlopen) -> int:
    """I candidati di pubblico dominio e CC0 per le figure pubbliche del piano."""
    voci = pubbliche.da_cercare(piano, project.assets_dir)
    if not voci:
        print("Nessuna figura pubblica da cercare: il piano non ne ha, o hanno già il file.")
        return 0
    trovati: dict[str, list[dict]] = {}
    errori_tutti: list[str] = []
    for voce in voci:
        termini = voce.get("cerca") or voce.get("mostra") or ""
        candidati, errori = pubbliche.cerca(termini, apri)
        trovati[voce["percorso"]] = [c.to_dict() for c in candidati]
        errori_tutti += errori
        print(f"{voce['percorso']} — «{termini}»: {len(candidati)} candidati")
        for numero, c in enumerate(candidati, 1):
            print(f"  {numero}. [{c.licenza}] {c.titolo[:60]} — {c.autore[:30]} "
                  f"({c.larghezza}x{c.altezza}, {c.archivio})")
    project.ensure_dirs()
    file = project.build_dir / "immagini-pubbliche.json"
    if file.exists():
        save_backup(project, args, "candidati pubblici precedenti", force=True)
    file.write_text(json.dumps(trovati, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    save_backup(project, args, "candidati delle figure pubbliche")
    for errore in sorted(set(errori_tutti)):
        print(f"! {errore}", file=sys.stderr)
    if errori_tutti and not any(trovati.values()):
        print("La rete dell'ambiente deve lasciar passare gli archivi "
              f"({', '.join(pubbliche.DOMINI)}): Network access → Allowed domains.", file=sys.stderr)
        return 1
    print(f"\nCandidati in {file}. Si prende quello coerente col libro:")
    print("  immagini <slug> --prendi immagini/NN-nome.jpg --candidato N")
    return 0


def _prendi_pubblica(project: BookProject, args, spec: BookSpec, piano: dict | None,
                     apri=urllib.request.urlopen) -> int:
    """Scarica il candidato scelto e ne scrive la provenienza nel piano."""
    voce = figure_module.voce_del_piano(piano, args.prendi)
    if voce is None or voce.get("fonte") != "pubblica":
        raise SystemExit(f"«{args.prendi}» non è una figura pubblica del piano ({figure_module.PIANO}).")
    try:
        candidati = json.loads((project.build_dir / "immagini-pubbliche.json").read_text(encoding="utf-8"))
        candidato = candidati[voce["percorso"]][args.candidato - 1]
    except (OSError, ValueError, KeyError, IndexError) as errore:
        raise SystemExit(f"Nessun candidato {args.candidato} per «{args.prendi}»: prima "
                         f"`immagini {spec.slug} --cerca`.") from errore
    destinazione = project.assets_dir / voce["percorso"]
    save_backup(project, args, "figure prima dell'immagine pubblica", force=True)
    try:
        provenienza = pubbliche.prendi(candidato, destinazione, apri)
    except (OSError, ValueError) as errore:
        print(f"! {errore}", file=sys.stderr)
        print(f"Se è la rete: va aperto {urllib.parse.urlsplit(candidato['file_url']).netloc} "
              "(Network access → Allowed domains).", file=sys.stderr)
        return 1
    voce["provenienza"] = provenienza
    figure_module.piano_path(project.root).write_text(
        json.dumps(piano, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    save_backup(project, args, f"figura pubblica {voce['percorso']}")
    geo = kdpspecs.page_geometry(spec.trim, spec.target_pages)
    dpi = int(provenienza["pixel"][0] / (geo.text_width / kdpspecs.INCH))
    print(f"{voce['percorso']}: {provenienza['pixel'][0]} x {provenienza['pixel'][1]} px, "
          f"{provenienza['licenza']}, da {provenienza['archivio']}. A piena misura: {dpi} DPI"
          + ("" if dpi >= figure_module.MIN_DPI else f" (sotto i {figure_module.MIN_DPI}: `qa` lo dirà)"))
    print("Poi: build e qa.")
    return 0


def _genera_figure(project, args, spec, mancanti, radice, mondo: str = "",
                   titoli: dict[int, str] | None = None) -> int:
    """Le figure che mancano generate con Higgsfield, ognuna dal suo prompt, in 4:3."""
    motivo = higgsfield.pronto()
    if motivo:
        raise SystemExit(f"Higgsfield non è pronto: {motivo}.")
    modello = higgsfield.configurazione(radice).get("modello") or higgsfield.MODELLO_IMMAGINI
    schema = higgsfield.schema(modello)
    generate = []
    for figura in mancanti:
        destinazione = project.assets_dir / figura.percorso
        print(f"{figura.percorso} con {modello}…", flush=True)
        prompt = imagebrief.prompt_incollabile(spec, figura, mondo=mondo, titoli=titoli)
        generata = higgsfield.genera(prompt, destinazione, proporzione="4:3", modello=modello,
                                     schema_modello=schema)
        generate.append(generata)
        print(f"  {generata.larghezza} x {generata.altezza} px")
    higgsfield.registra(project.build_dir, generate)
    save_backup(project, args, f"{len(generate)} figure da Higgsfield")
    print("\nPoi: build e qa (DPI sulla misura stampata, conversione in grigio).")
    return 0


def _prima_variante_libera(project: BookProject) -> int:
    """Il primo numero di variante non ancora usato, in assets/ o fra quelle generate.

    Le varianti di una direzione nuova si aggiungono alle vecchie, non le
    sovrascrivono: quelle già pagate restano una possibilità.
    """
    usati = {0}
    for file in project.assets_dir.glob("copertina-*.*"):
        numero = file.stem.split("-", 1)[1]
        if numero.isdigit():
            usati.add(int(numero))
    try:
        voci = json.loads((project.build_dir / produzione.GENERATE).read_text(encoding="utf-8"))
        usati |= {int(v["variante"]) for v in voci if isinstance(v, dict) and v.get("variante")}
    except (OSError, ValueError):
        pass
    return max(usati) + 1


def _genera_copertina(project, args, spec, pages, meta, copy, rivale, minimo, radice,
                      direzione: dict | None = None) -> int:
    """Le varianti di copertina generate con Higgsfield, dal prompt del sistema.

    Ogni variante ha il suo prompt (`coverbrief.prompt_da_incollare`, modo
    generatore) con un'indicazione di composizione diversa; tornano in
    `assets/copertina-N.png`, e la loro traccia in `build/immagini-generate.json`.
    Con una direzione scelta i prompt nascono da lei.
    """
    motivo = higgsfield.pronto()
    if motivo:
        raise SystemExit(f"Higgsfield non è pronto: {motivo}.")
    modello = higgsfield.configurazione(radice).get("modello") or higgsfield.MODELLO_IMMAGINI
    schema = higgsfield.schema(modello)
    generate = []
    primo = _prima_variante_libera(project)
    for indice in range(1, args.varianti + 1):
        numero = primo + indice - 1
        prompt = coverbrief.prompt_da_incollare(
            spec, pages=pages, metadata=meta, copy=copy, concorrente=rivale,
            varianti=args.varianti, variante=indice, per_chat=False, direzione=direzione,
        )
        destinazione = project.assets_dir / f"copertina-{numero}.png"
        if destinazione.exists():
            save_backup(project, args, f"variante {numero} di copertina precedente", force=True)
        print(f"Variante {numero} ({indice} di {args.varianti}) con {modello}…", flush=True)
        generata = higgsfield.genera(prompt, destinazione, proporzione="2:3",
                                     modello=modello, schema_modello=schema)
        generate.append(generata)
        esito = "basta per la stampa" if generata.basta(minimo) else (
            f"sotto il minimo di {minimo[0]} x {minimo[1]}: va ingrandita")
        print(f"  {destinazione.name}: {generata.larghezza} x {generata.altezza} px, {esito}")
    higgsfield.registra(project.build_dir, generate)
    save_backup(project, args, f"{len(generate)} varianti di copertina da Higgsfield")
    print("\nPoi: l'agente `copertina` le misura, la scelta passa dal silenzio-assenso,")
    print(f"e `copertina {spec.slug} --scegli N` porta la variante in assets/copertina.jpg.")
    return 0


def _scarica_generate(project: BookProject, args, apri=urllib.request.urlopen) -> int:
    """Le varianti già generate e pagate, dalla CDN di Higgsfield in assets/copertina-N.png.

    Non si rigenera niente: si scaricano gli indirizzi che il generatore ha
    restituito (`build/copertina-higgsfield.json`). La CDN la rete del container
    può bloccarla: allora lo dice, con l'host da aprire.
    """
    from PIL import Image

    # Anche i bozzetti delle direzioni, se sono rimasti sulla CDN: servono
    # all'autore per scegliere, e all'agente per misurarli.
    mancanti = [(f"copertina-{v['variante']}.png", v) for v in produzione.generate_senza_file(project)]
    mancanti += [
        (f"bozzetto-{v['direzione']}.png", v) for v in direzioni.bozzetti(project)
        if v.get("url") and not (project.assets_dir / f"bozzetto-{v['direzione']}.png").exists()
    ]
    if not mancanti:
        print("Nessuna variante da scaricare: sono già tutte in assets/ (o non ce n'è nessuna generata).")
        return 0
    project.ensure_dirs()
    falliti = []
    for nome, voce in mancanti:
        destinazione = project.assets_dir / nome
        try:
            with apri(voce["url"], timeout=300) as risposta:
                contenuto = risposta.read()
        except OSError as errore:
            falliti.append((nome, f"{urllib.parse.urlsplit(voce['url']).netloc}: {errore}"))
            continue
        if not corriere.e_un_immagine(contenuto):
            falliti.append((nome, "il file scaricato non è un'immagine"))
            continue
        destinazione.write_bytes(contenuto)
        with Image.open(destinazione) as immagine:
            larghezza, altezza = immagine.size
        print(f"  {destinazione.name}: {larghezza} x {altezza} px, {len(contenuto)} byte")
    if len(falliti) < len(mancanti):
        save_backup(project, args, "varianti di copertina scaricate da Higgsfield")
    for nome, motivo in falliti:
        print(f"! {nome} non scaricata — {motivo}", file=sys.stderr)
    if falliti:
        print("La rete dell'ambiente deve lasciar passare la CDN di Higgsfield "
              "(Network access → Allowed domains), oppure l'autore carica le varianti "
              "sul ramo cowork-immagini.", file=sys.stderr)
        return 1
    print("Poi: l'agente `copertina` le misura, e `copertina <slug> --scegli N`.")
    return 0


def _scegli_copertina(project: BookProject, args) -> int:
    """La variante scelta diventa `assets/copertina.jpg`, quella che `build` usa."""
    from PIL import Image

    candidati = sorted(project.assets_dir.glob(f"copertina-{args.scegli}.*"))
    if not candidati:
        raise SystemExit(f"Nessuna variante copertina-{args.scegli} in {project.assets_dir}.")
    destinazione = project.assets_dir / "copertina.jpg"
    if destinazione.exists():
        save_backup(project, args, "copertina prima della variante scelta", force=True)
    with Image.open(candidati[0]) as immagine:
        immagine.convert("RGB").save(destinazione, "JPEG", quality=95)
    save_backup(project, args, f"copertina: variante {args.scegli}")
    print(f"{candidati[0].name} → {destinazione}. Poi: build e review --agents copertina.")
    return 0


def cmd_manuale(args) -> int:
    """La fabbrica senza chiave: il sistema scrive i brief, tu porti le risposte.

    Nessuna chiamata al modello, in nessun passo. Serve quando la credenziale
    non c'è — o quando si vuole scrivere il libro a mano e tenere comunque
    impaginazione, copertina, controlli e scheda.
    """
    project, spec = open_project(args, riscrive=args.importa)

    if args.passo == "stato":
        print(manuale.riepilogo(project))
        return 0

    if args.passo == "scaletta":
        budget = budget_for(project, spec)
        if args.esamina or args.importa:
            risposta = manuale.leggi_risposta(
                manuale.percorso_risposta(project, "scaletta", "json")
            )
            esito = manuale.esamina_scaletta(project, spec, budget, risposta)
            print(esito["rapporto"])
            if args.esamina:
                return 1 if esito["bloccanti"] else 0
            if esito["bloccanti"] and not args.forza:
                raise SystemExit(
                    f"\n{esito['bloccanti']} rilievi bloccanti: la scaletta non entra.\n"
                    f"Correggi {manuale.percorso_risposta(project, 'scaletta', 'json')} "
                    "e riprova (`--forza` la fa passare lo stesso)."
                )
            outline = manuale.importa_scaletta(project, spec, budget, risposta)
            save_backup(project, args, "scaletta importata a mano")
            print(f"\nScaletta salvata in {project.outline_path}: {len(outline.chapters)} sezioni")
            for capitolo in outline.chapters:
                print(f"  {capitolo.number:>2}. {capitolo.title}  ({capitolo.target_words} parole)")
            return 0
        percorso = manuale.brief_scaletta(project, spec, budget)
        print(f"Brief della scaletta: {percorso}")
        print(f"  {budget.chapters} capitoli · ~{budget.words_per_chapter} parole ciascuno")
        print(f"\nIncolla la risposta in {manuale.percorso_risposta(project, 'scaletta', 'json')}")
        print(f"poi: python -m kdpfactory manuale {spec.slug} scaletta --importa")
        return 0

    outline = project.load_outline()

    if args.passo == "capitolo":
        if not args.numero:
            raise SystemExit("Serve --numero: quale capitolo.")
        nome = f"capitolo-{args.numero:02d}"
        if not args.importa:
            percorso = manuale.brief_capitolo(project, spec, outline, args.numero)
            print(f"Brief del capitolo {args.numero}: {percorso}")
            print(f"\nIncolla la risposta in {manuale.percorso_risposta(project, nome, 'md')}")
            print(f"poi: python -m kdpfactory manuale {spec.slug} capitolo "
                  f"--numero {args.numero} --importa")
            return 0
        risposta = manuale.leggi_risposta(manuale.percorso_risposta(project, nome, "md"))
        esito = manuale.importa_capitolo(project, outline, args.numero, risposta)
        save_backup(project, args, f"capitolo {args.numero} importato a mano")
        print(f"Capitolo {esito['numero']} — {esito['titolo']}")
        print(f"  {esito['parole']} parole su {esito['parole_chieste']} chieste "
              f"({esito['scarto'] * 100:+.0f}%)")
        if esito["fuori_tolleranza"]:
            print("  ! fuori tolleranza: l'impaginazione ne risentirà sul conteggio pagine.")
        return 0

    if args.passo == "scheda":
        if not args.importa:
            percorso = manuale.brief_scheda(project, spec, outline)
            print(f"Brief della scheda prodotto: {percorso}")
            print(f"\nIncolla la risposta in {manuale.percorso_risposta(project, 'scheda', 'json')}")
            print(f"poi: python -m kdpfactory manuale {spec.slug} scheda --importa")
            return 0
        risposta = manuale.leggi_risposta(manuale.percorso_risposta(project, "scheda", "json"))
        meta = manuale.importa_scheda(project, risposta)
        state = project.load_state()
        pagine = (state.get("build") or {}).get("pagine") or spec.target_pages
        info = pipeline.write_metadata_files(project, spec, outline, meta, pagine)
        save_backup(project, args, "scheda importata a mano")
        print(f"Scheda salvata in {info['listing']}")
        return 0

    raise SystemExit(f"Passo non riconosciuto: {args.passo}")


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
        from .agents.scaletta import esamina as esamina_scaletta
        from .manuale import pagine_della_scaletta, rapporto_rilievi

        rilievi = esamina_scaletta(
            outline,
            spec,
            brief=spec.brief or "",
            capitoli_attesi=budget.chapters,
            pagine_previste=pagine_della_scaletta(project, spec, budget, outline),
        )
        bloccanti = [r for r in rilievi if r.severity == "bloccante"]
        # In prova a secco la scaletta è un segnaposto: il cancello si guarda,
        # non si chiude.
        if bloccanti and not args.dry_run:
            print(rapporto_rilievi(rilievi, outline))
            raise SystemExit(
                f"\nLa scaletta ha {len(bloccanti)} rilievi bloccanti: correggi "
                f"{project.outline_path} e rilancia `all` senza --force."
            )
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

    # Il primo tempo dell'agente copertina: il prompt dell'illustrazione, sulle
    # pagine definitive. Non chiama il modello, e senza questo passo la
    # copertina restava quella del motore finché qualcuno non se ne ricordava.
    print("\nPrompt delle immagini (agente copertina)")
    cmd_copertina(args)
    if any("![" in testo for _, _, testo in writer.load_chapters(project, outline)):
        cmd_immagini(args)

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
    only = [int(n) for n in args.only.split(",")] if args.only else None
    names = (
        [n.strip() for n in args.agents.split(",")]
        if args.agents
        else list(agents.QUALITY_LEVELS[args.qualita]["reviewers"])
    )
    if not names:
        print(f"Il livello «{args.qualita}» non prevede revisione.")
        return 0
    # Impaginazione e copertina misurano: chiedere la credenziale per farli
    # girare vorrebbe dire tenere chiusi i controlli che costano zero.
    client = (
        make_client(args)
        if any(not agents.get_agent(n).deterministico for n in names)
        else None
    )
    print(f"Revisione di «{spec.title}» — agenti: {', '.join(names)}")
    report = agents.run_review(project, spec, outline, client, agent_names=names, only=only)
    if client:
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


def _scrivi_richiesta(project: BookProject, args, richiesta: Path, testo: str, fatti: list[str]) -> None:
    """Scrive una richiesta a Cowork, senza mai passare sopra una domanda che ha già risposta."""
    risposta = richiesta.with_name(richiesta.stem + cowork.SUFFISSO_RISPOSTA + ".md")
    if not richiesta.exists():
        richiesta.parent.mkdir(parents=True, exist_ok=True)
        richiesta.write_text(testo, encoding="utf-8")
        fatti.append(str(richiesta))
    elif richiesta.read_text(encoding="utf-8") != testo:
        if risposta.exists():
            # Una risposta di Cowork vale per la domanda che ha letto: la
            # versione nuova va in un seguito, non sopra la vecchia.
            print(f"\n! {richiesta.name} ha già la risposta di Cowork: la richiesta non si\n"
                  f"  riscrive. Se serve altro, apri {richiesta.stem}-2.md con i soli punti nuovi.")
        else:
            save_backup(project, args, f"{richiesta.name} precedente", force=True)
            richiesta.write_text(testo, encoding="utf-8")
            fatti.append(f"{richiesta} (aggiornata)")


def cmd_parole_chiave(args) -> int:
    """La verifica delle parole chiave della scheda: la richiesta per Cowork, ruolo «parole-chiave»."""
    project, spec = open_project(args)
    risposte = avvio.leggi(project)
    mercato = risposte.mercato if risposte else ("amazon.it" if spec.language == "it" else "amazon.com")
    if len(spec.keywords) < 7:
        print(f"! La scheda ha {len(spec.keywords)} parole chiave su 7: si verificano quelle che ci sono.")
    canale = cowork.configurazione(Path(__file__).resolve().parent.parent)
    titolo = f"{spec.title} — {spec.subtitle}" if spec.subtitle else spec.title
    nome, testo = parolechiave.verifica(
        titolo, spec.keywords, spec.categories, mercato, spec.slug, canale
    )
    fatti: list[str] = []
    _scrivi_richiesta(project, args, project.root / "manuale" / nome, testo, fatti)
    for percorso in fatti:
        print(f"Scritto {percorso}")
    if not fatti:
        print(f"La richiesta {nome} è già aggiornata.")
    else:
        print("\nCommit e push in questo stesso giro; la porta sul corriere `cowork corriere`.")
    return 0


def cmd_avvio(args) -> int:
    """Le domande d'avvio di un libro nuovo: le registra e, finite, prepara la fase 0.

    Senza risposte elenca le domande ancora da fare; con `--json` le dà pronte
    per chi le pone all'autore. Quando l'autore le ha viste tutte, prepara il
    modulo della pagina del concorrente e, se la porta Cowork, la sua richiesta.
    """
    from . import concorrente as acquisizione

    books = books_dir(args)
    project = BookProject(books / args.slug)
    risposte = avvio.leggi(project) or avvio.Avvio()
    pseudonimo = args.pseudonimo
    if pseudonimo is not None and pseudonimo.strip().lower() in {"nuovo", "uno nuovo"}:
        pseudonimo = ""
    errori = avvio.registra(
        risposte,
        concorrente=args.concorrente,
        nicchia=args.nicchia,
        mercato=args.mercato,
        categoria=args.categoria,
        vantaggi=args.vantaggi.split(",") if args.vantaggi is not None else None,
        vetrina=args.vetrina,
        pseudonimo=pseudonimo,
        pagina=args.pagina,
    )
    if errori:
        raise SystemExit("Risposte non registrate:\n" + "\n".join(f"  - {e}" for e in errori))
    if args.predefinite:
        # L'autore ha detto «fai tu»: le domande a scelta prendono il default.
        # Il concorrente no: senza un libro da battere il metodo non parte.
        for domanda in risposte.mancanti():
            if domanda.chiave != "concorrente" and domanda.chiave not in risposte.risposte:
                risposte.risposte.append(domanda.chiave)
        risposte.risposte.sort(key=[d.chiave for d in avvio.DOMANDE].index)

    cambiate = any(
        v is not None
        for v in (args.concorrente, args.nicchia, args.mercato, args.categoria, args.vantaggi,
                  args.vetrina, args.pseudonimo, args.pagina)
    ) or args.predefinite
    if cambiate:
        if avvio.percorso(project).exists():
            save_backup(project, args, "domande d'avvio precedenti", force=True)
        avvio.salva(project, risposte)

    if args.json:
        print(json.dumps(avvio.giri(risposte, books), ensure_ascii=False, indent=2))
        return 0

    print(f"Domande d'avvio — {args.slug}\n")
    print(avvio.riepilogo(risposte))
    mancanti = risposte.mancanti()
    if mancanti:
        print("\nDa chiedere all'autore:")
        for domanda in mancanti:
            print(f"  · {domanda.testo}")
            for opzione in (avvio.domande_pseudonimo(books) if domanda.chiave == "pseudonimo"
                            else domanda).opzioni:
                print(f"      {opzione.valore or 'nuovo':<12} {opzione.etichetta}")
        print(f"\nPoi: python -m kdpfactory avvio {args.slug} --<domanda> <valore> … "
              "(--predefinite se l'autore lascia decidere)")
        return 0

    # Tutte viste: si prepara la fase 0.
    fatti: list[str] = []
    pagina = acquisizione.pagina_path(project)
    if risposte.asin and not pagina.exists():
        fatti.append(str(acquisizione.prepara(project, risposte.asin)))
    elif risposte.asin and risposte.asin not in pagina.read_text(encoding="utf-8"):
        # Il concorrente è cambiato: il modulo si rifà solo se è ancora vuoto,
        # una pagina già incollata non si butta.
        incollato = pagina.read_text(encoding="utf-8").split("-->", 1)[-1].strip()
        if not incollato:
            fatti.append(f"{acquisizione.prepara(project, risposte.asin)} (nuovo ASIN)")
        else:
            print(f"\n! {pagina.name} contiene già una pagina incollata, di un altro ASIN: "
                  "controlla che sia quella del concorrente giusto.")
    if risposte.copertina and not avvio.copertina_path(project).exists():
        avvio.copertina_path(project).write_text(avvio.COPERTINA_TEMPLATE, encoding="utf-8")
        fatti.append(str(avvio.copertina_path(project)))
    radice = Path(__file__).resolve().parent.parent
    canale = cowork.configurazione(radice)
    if risposte.pagina == "cowork" and (risposte.asin or risposte.nicchia):
        nome, testo = avvio.richiesta_cowork(risposte, args.slug, canale)
        _scrivi_richiesta(project, args, acquisizione.cartella(project) / nome, testo, fatti)
    if risposte.asin:
        # Le parole chiave della nicchia si cercano comunque, chiunque porti la
        # pagina: il posizionamento sceglie le sette frasi da quella tabella.
        nome, testo = parolechiave.esplorazione(risposte.asin, risposte.mercato, args.slug, canale)
        _scrivi_richiesta(project, args, acquisizione.cartella(project) / nome, testo, fatti)
    if risposte.asin and risposte.copertina:
        # Le copertine che vendono nella categoria del concorrente, nello stesso
        # giro: l'agente `copertina` ne ricava i codici del genere per le tre
        # direzioni d'arte (docs/copertine.md).
        nome, testo = direzioni.richiesta_studio(args.slug, risposte.mercato, "", canale,
                                                 asin=risposte.asin)
        _scrivi_richiesta(project, args, acquisizione.cartella(project) / nome, testo, fatti)
    save_backup(project, args, "domande d'avvio")
    if produzione.attiva(Path(__file__).resolve().parent.parent, args.slug):
        fatti.append("config/produzione.json (il libro entra nel giro orario)")

    print("\nDomande d'avvio complete.")
    for percorso in fatti:
        print(f"  scritto {percorso}")
    if risposte.asin or risposte.pagina == "cowork":
        print("\nRichieste per Cowork: `cowork corriere` (l'indice), poi commit e push in questo")
        print("stesso giro, e i lanci di «avvia». Cowork consegna lanciando la routine;")
        print("salvate le risposte (`cowork corriere --ricevi`), la fase 0 le legge dove sono:")
        print("non serve copiarle in concorrente/pagina.md.")
    if risposte.pagina == "incolla" and risposte.asin:
        print(f"\nIncolla la pagina Amazon in {acquisizione.pagina_path(project)}, poi parte la fase 0.")
    return 0


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

    if args.action == "importa":
        # La linea manuale: i quattro agenti li ha chiamati la sessione.
        risultato = acquisizione.importa(project, asin=args.asin)
        print(acquisizione.render(risultato))
        if project.spec_path.exists():
            save_backup(project, args, "scheda prima dell'importazione del reparto", force=True)
        spec = acquisizione.scrivi(project, risultato, args.author)
        save_backup(project, args, f"acquisizione importata ({risultato.asin or 'ASIN non indicato'})")
        print(f"\nScritti {project.spec_path} e {project.brief_path}")
        print(f"\nRileggi la scheda e il brief, poi la fase 1 su {spec.slug}.")
        return 0

    client = make_client(args)
    indicazione = acquisizione.leggi_vincoli(project, args.indicazione)
    if indicazione:
        print(f"\nIndirizzo editoriale in vigore:\n  {indicazione.splitlines()[0]}")
    risultato = acquisizione.analizza(
        project, client, asin=args.asin, indicazione=indicazione
    )
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


def _cmd_corriere(args, radice: Path, canale: dict, elenco: list) -> int:
    """Il corriere su GitHub: le consegne di Cowork, il ramo delle immagini, l'indice e il piano.

    Cowork consegna lanciando la routine della fabbrica, con la risposta nel
    testo: la sessione lo salva in un file e lo passa a `--ricevi`, che lo
    scrive accanto alla sua richiesta. Nient'altro entra dal corriere.
    """
    if getattr(args, "ricevi", ""):
        testo = Path(args.ricevi).read_text(encoding="utf-8")
        consegne = corriere.leggi_consegne(testo)
        if not consegne:
            raise SystemExit(
                f"In {args.ricevi} non c'è nessuna consegna: la prima riga dev'essere "
                f"«{cowork.CONSEGNA} kdp-book-factory/<percorso della risposta>» "
                f"oppure «{cowork.ESITO} <ruolo>»."
            )
        rifiutate = 0
        for consegna in consegne:
            try:
                esito, percorso = corriere.ricevi(radice, consegna, elenco)
            except ValueError as errore:
                rifiutate += 1
                print(f"Rifiutata: {errore}", file=sys.stderr)
                continue
            if esito == "scritta":
                prima = (radice / percorso).read_text(encoding="utf-8").splitlines()[:1]
                if not prima or not prima[0].startswith("Esito:"):
                    print(f"Avviso: {percorso} non comincia con «Esito: …»", file=sys.stderr)
                print(f"Scritta {percorso}")
            elif esito == "in arrivo":
                print(f"In arrivo {percorso}: parte {consegna.parte} di {consegna.parti}, "
                      "aspetto le altre")
            elif esito == "esito":
                print(f"Esito di un giro non riuscito: {percorso}")
            else:
                print(f"Già nel repository: {percorso}")
        return 1 if rifiutate else 0
    if getattr(args, "dal_ramo", False):
        # Le immagini non passano dal testo delle consegne: l'autore le carica sul
        # ramo di GitHub, e da lì arrivano nel libro solo quelle che una richiesta
        # ha chiesto, con le risposte che mancano.
        immagini, avvisi = corriere.preleva_dal_ramo(radice, elenco)
        for avviso in avvisi:
            print(f"Avviso: {avviso}")
        for immagine in immagini:
            bersaglio = radice / immagine.percorso
            parti = Path(immagine.percorso).parts
            if bersaglio.exists():
                save_backup(BookProject(radice / parti[0] / parti[1]), args,
                            f"{bersaglio.name} prima della versione di Cowork", force=True)
            bersaglio.parent.mkdir(parents=True, exist_ok=True)
            bersaglio.write_bytes(immagine.contenuto)
            corriere.registra_dal_ramo(radice, immagine.percorso, immagine.blob)
            print(f"Scritto {immagine.percorso} ({len(immagine.contenuto):,} byte)")
        if not immagini:
            print(f"Niente di nuovo sul ramo {corriere.RAMO_IMMAGINI}.")
        return 0
    if getattr(args, "avviato", ""):
        fatte = corriere.registra_avviato(radice, args.avviato, elenco, canale)
        print(f"Lanciato il ruolo {args.avviato}: " + (", ".join(fatte) or "nessuna richiesta"))
        return 0
    if corriere.su_github(canale):
        # Cowork legge le richieste aperte dall'indice sul ramo della fabbrica: va
        # riscritto a ogni giro, e pubblicato prima di lanciare i ruoli.
        (radice / corriere.INDICE).write_text(corriere.indice(elenco, canale), encoding="utf-8")
    print(json.dumps(corriere.piano(radice, elenco, canale), ensure_ascii=False, indent=2))
    return 0


def cmd_decisioni(args) -> int:
    """Le decisioni dell'autore con il silenzio-assenso: proposte, risposte, scadute."""
    books = books_dir(args)
    if args.scadute:
        # Il giro orario: le proposte senza risposta oltre la scadenza si chiudono.
        chiuse = []
        for cartella in sorted(p for p in books.iterdir() if (p / "decisioni.json").exists()):
            chiuse += [(cartella.name, v) for v in decisioni.chiudi_scadute(BookProject(cartella))]
        for slug, voce in chiuse:
            print(f"{slug} · {voce['chiave']}: silenzio-assenso, vale «{voce['valore']}»")
        if not chiuse:
            print("Nessuna proposta scaduta.")
        return 0
    if not args.slug:
        raise SystemExit("Indica il libro, oppure --scadute per tutti.")
    project = BookProject(books / args.slug)
    try:
        if args.proponi:
            voce = decisioni.proponi(project, args.proponi, args.valore, args.alternativa,
                                     args.perche, args.ore)
            print(decisioni.messaggio(args.slug, voce))
            return 0
        if args.scegli:
            voce = decisioni.scegli(project, args.scegli, args.valore)
            print(f"{args.slug} · {voce['chiave']}: scelta dell'autore, «{voce['valore']}»")
            return 0
        if args.applicata:
            decisioni.segna_applicata(project, args.applicata)
            print(f"{args.slug} · {args.applicata}: applicata")
            return 0
    except ValueError as errore:
        raise SystemExit(str(errore)) from errore
    elenco = decisioni.leggi(project)
    if args.json:
        print(json.dumps(elenco, ensure_ascii=False, indent=2))
        return 0
    for voce in elenco:
        fatto = " · applicata" if voce.get("applicata") else ""
        print(f"  {voce['chiave']:<12} {voce['stato']:<20} «{voce['valore'] or voce['proposta']}»{fatto}")
    if not elenco:
        print("Nessuna decisione registrata.")
    return 0


def cmd_produzione(args) -> int:
    """A che punto è ogni libro e qual è il prossimo passo: la bussola del giro orario."""
    radice = Path(__file__).resolve().parent.parent
    aperte = cowork.richieste(radice)
    attivi = None if args.tutti else produzione.configurazione(radice).get("attivi", [])
    stati = produzione.tutti(books_dir(args), aperte, attivi)
    if args.json:
        print(json.dumps([s.to_dict() for s in stati], ensure_ascii=False, indent=2))
    else:
        print(produzione.rapporto(stati), end="")
    return 0


def cmd_cowork(args) -> int:
    """Il canale con Cowork su GitHub: stato delle richieste, e l'avviso da mandargli."""
    radice = Path(__file__).resolve().parent.parent
    canale = cowork.configurazione(radice)
    ruoli = cowork.ruoli(canale)
    if args.ruolo and args.ruolo not in ruoli:
        raise SystemExit(f"Ruolo sconosciuto: {args.ruolo}. Ruoli: {', '.join(ruoli)}.")
    if args.azione == "progetto":
        # Il testo per Claude Desktop nasce dalla configurazione: cambiato un
        # ruolo o un orario, si rigenera invece di correggerlo a mano.
        uscita = radice / "config" / "progetto-cowork.md"
        uscita.write_text(cowork.progetto(canale), encoding="utf-8")
        print(f"Scritto {uscita}: istruzioni del progetto, una chat e un'attività per ruolo.")
        chatgpt = radice / "config" / "progetto-chatgpt.md"
        chatgpt.write_text(richiesteimmagini.progetto_chatgpt(canale), encoding="utf-8")
        print(f"Scritto {chatgpt}: il progetto ChatGPT delle immagini.")
        voci = cowork.attivita(canale)
        if voci:
            file = radice / "config" / "attivita-cowork.json"
            file.write_text(json.dumps(voci, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"Scritto {file}: {len(voci)} attività da applicare con update_trigger.")
        return 0
    git = cowork.Git(radice, canale.get("ramo", "claude/dreamy-archimedes-hf8w45"))
    elenco = cowork.richieste(radice, git.remoto, git.ultimo_commit)
    if args.azione == "corriere":
        return _cmd_corriere(args, radice, canale, elenco)
    if args.azione == "avviso":
        da_inviare = [
            r.percorso for r in elenco
            if r.stato == cowork.APERTA and r.invio != cowork.INVIATA
            and (not args.ruolo or r.ruolo == args.ruolo)
        ]
        if da_inviare:
            # Cowork legge il ramo remoto: una richiesta non pubblicata lì non c'è, o è vecchia.
            print("Da inviare prima dell'avviso (commit e push): " + ", ".join(da_inviare), file=sys.stderr)
        print(cowork.avviso(elenco, canale, git.percorso_repo, ruolo=args.ruolo or ""), end="")
    elif args.json:
        dati = {"canale": canale, "richieste": [r.to_dict() for r in elenco]}
        print(json.dumps(dati, ensure_ascii=False, indent=2))
    else:
        print(cowork.rapporto(elenco, set(ruoli)), end="")
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
    p.add_argument("--scegli", type=int, default=0,
                   help="la variante N (assets/copertina-N.png) diventa assets/copertina.jpg")
    p.add_argument("--genera", action="store_true",
                   help="genera le varianti con Higgsfield dal prompt del sistema")
    p.add_argument("--varianti", type=int, default=richiesteimmagini.VARIANTI,
                   help="quante varianti generare con --genera")
    p.add_argument("--preferisci", default="",
                   help="trattamenti scelti fra i bozzetti, separati da virgola (luce,serigrafia…)")
    p.add_argument("--scarta", default="", help="trattamenti scartati fra i bozzetti")
    p.add_argument("--perche", default="", help="il motivo della scelta, con le parole dell'autore")
    p.add_argument("--scarica-generate", action="store_true",
                   help="scarica in assets/ le varianti già generate (build/copertina-higgsfield.json)")
    p.add_argument("--direzioni", action="store_true",
                   help="le tre direzioni d'arte: modello da compilare, controlli, prompt dei bozzetti")
    p.add_argument("--bozzetti", action="store_true",
                   help="con --genera, un bozzetto per direzione a bassa risoluzione")
    p.add_argument("--direzione", type=int, default=0,
                   help="la direzione N scelta dall'autore: palette, composizione e carattere in book.json")
    p.set_defaults(func=cmd_copertina)

    p = sub.add_parser(
        "immagini",
        help="prompt delle figure dell'interno, uno per figura (nessuna chiamata API)",
    )
    p.add_argument("slug")
    p.add_argument("--genera", action="store_true",
                   help="genera con Higgsfield le figure che mancano, dal prompt del sistema")
    p.add_argument("--piano", action="store_true",
                   help="il piano delle figure (figure.json): servono? generate o pubbliche?")
    p.add_argument("--cerca", action="store_true",
                   help="cerca negli archivi aperti, solo pubblico dominio e CC0, le figure pubbliche")
    p.add_argument("--prendi", default="",
                   help="la figura pubblica (immagini/NN-nome.jpg) da prendere fra i candidati")
    p.add_argument("--candidato", type=int, default=1, help="con --prendi, il numero del candidato")
    p.set_defaults(func=cmd_immagini)

    p = sub.add_parser(
        "manuale",
        help="la fabbrica senza chiave API: il sistema scrive i brief, tu porti le risposte",
    )
    p.add_argument("slug")
    p.add_argument(
        "passo",
        choices=["stato", "scaletta", "capitolo", "scheda"],
        help="stato: che cosa manca · scaletta/capitolo/scheda: produce il brief",
    )
    p.add_argument("--numero", type=int, default=0, help="quale capitolo (passo `capitolo`)")
    p.add_argument(
        "--importa",
        action="store_true",
        help="invece di produrre il brief, importa la risposta che hai incollato",
    )
    p.add_argument(
        "--esamina",
        action="store_true",
        help="passa la scaletta al revisore senza importarla",
    )
    p.add_argument(
        "--forza",
        action="store_true",
        help="importa la scaletta anche con rilievi bloccanti del revisore",
    )
    p.set_defaults(func=cmd_manuale)

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
        "avvio",
        help="le domande all'autore prima di un libro nuovo: concorrente, mercato, categoria, vantaggi",
    )
    p.add_argument("slug")
    p.add_argument("--concorrente", help="ASIN o link Amazon del libro da battere")
    p.add_argument("--nicchia", help="la nicchia, se il concorrente lo deve trovare Cowork")
    p.add_argument("--mercato", help=", ".join(avvio.MERCATI))
    p.add_argument("--categoria", help=", ".join(avvio.CATEGORIE))
    p.add_argument("--vantaggi", help="separati da virgole: " + ", ".join(avvio.VANTAGGI))
    p.add_argument("--vetrina", help=", ".join(avvio.VETRINE))
    p.add_argument("--pseudonimo", help="nome d'autore; «nuovo» per farlo proporre col titolo")
    p.add_argument("--pagina", help=", ".join(avvio.PAGINE))
    p.add_argument(
        "--predefinite",
        action="store_true",
        help="l'autore lascia decidere: le domande a scelta ancora aperte prendono il default",
    )
    p.add_argument("--json", action="store_true", help="le domande da fare, pronte da porre")
    p.set_defaults(func=cmd_avvio)

    p = sub.add_parser(
        "concorrente",
        help="da una scheda Amazon incollata alla scheda di un libro nuovo che la batte",
    )
    p.add_argument(
        "action",
        choices=["new", "build", "importa"],
        help="importa: book.json e brief dai file dei quattro agenti chiamati dalla sessione",
    )
    p.add_argument("slug")
    p.add_argument("--asin", default="", help="ASIN del libro di riferimento")
    p.add_argument("--author", default="Autore Anonimo", help="autore del libro nuovo")
    p.add_argument(
        "--indicazione",
        default="",
        help="indirizzo editoriale per il posizionamento; in mancanza si legge "
        "`concorrente/indicazione.md`",
    )
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

    p = sub.add_parser(
        "cowork",
        help="richieste di ricerca web a Cowork, su GitHub: stato, e l'avviso da mandargli",
    )
    p.add_argument(
        "azione",
        nargs="?",
        default="stato",
        choices=["stato", "avviso", "progetto", "corriere"],
        help="progetto: scrive config/progetto-cowork.md, il testo per le chat e le attività dei ruoli; "
        "corriere: l'indice delle richieste aperte e il piano del giro",
    )
    p.add_argument("--ruolo", default="", help="l'avviso per la chat di un solo ruolo")
    p.add_argument("--ricevi", default="", metavar="FILE",
                   help="corriere: il testo che Cowork ha consegnato lanciando la routine, salvato in "
                   "un file: la risposta va accanto alla sua richiesta, l'esito in config/cowork-esiti/")
    p.add_argument("--avviato", default="",
                   help="corriere: il ruolo appena lanciato con fire_trigger (le sue richieste nel cloud)")
    p.add_argument("--dal-ramo", action="store_true",
                   help=f"corriere: porta nei libri le immagini che Cowork ha caricato sul ramo "
                   f"{corriere.RAMO_IMMAGINI}")
    p.add_argument("--json", action="store_true", help="stato completo in JSON")
    p.set_defaults(func=cmd_cowork)

    p = sub.add_parser("decisioni", help="le decisioni dell'autore, con il silenzio-assenso")
    p.add_argument("slug", nargs="?", default="")
    p.add_argument("--proponi", default="", help="la decisione da proporre: " + ", ".join(decisioni.CHIAVI))
    p.add_argument("--scegli", default="", help="la decisione su cui l'autore ha risposto")
    p.add_argument("--valore", default="", help="la proposta, o la scelta dell'autore")
    p.add_argument("--alternativa", action="append", default=[], help="un'alternativa (ripetibile)")
    p.add_argument("--perche", default="", help="perché gli agenti propongono questo")
    p.add_argument("--ore", type=int, default=decisioni.ORE_PREDEFINITE,
                   help="dopo quante ore vale il silenzio")
    p.add_argument("--applicata", default="", help="la decisione appena applicata ai file del libro")
    p.add_argument("--scadute", action="store_true", help="chiude le proposte scadute, in tutti i libri")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_decisioni)

    p = sub.add_parser("produzione", help="a che punto è ogni libro, e il prossimo passo")
    p.add_argument("--json", action="store_true")
    p.add_argument("--tutti", action="store_true", help="anche i libri fuori dalla produzione")
    p.set_defaults(func=cmd_produzione)

    p = sub.add_parser(
        "parole-chiave",
        help="la verifica delle sette parole chiave della scheda: la richiesta per Cowork",
    )
    p.add_argument("slug")
    p.set_defaults(func=cmd_parole_chiave)

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

"""La linea manuale: la fabbrica senza chiave API.

Metà di questo sistema non chiama il modello e non l'ha mai chiamato:
l'impaginazione misura, la copertina disegna e verifica, il controllo qualità
conta, la scheda calcola prezzi e royalty, la taratura delle pagine impagina
libri di prova. L'altra metà — scaletta, capitoli, scheda prodotto — è scrittura,
e per quella serve un modello.

Senza credenziale la fabbrica si fermava tutta, e non è giusto: si ferma solo
la scrittura. Qui c'è il modo di far lavorare le due metà separate.

Il meccanismo è quello che il sistema usa già per le copertine
(`coverbrief.py`): **non si disegna, si scrive il brief**. Per ogni passo che
richiederebbe il modello, questo modulo produce esattamente il prompt che
l'agente avrebbe ricevuto — regole d'autore, scheda del libro, budget di
parole, contratto di risposta — da portare a qualunque modello o da scrivere a
mano. Quello che torna rientra da un file, e il sistema lo **valida** prima di
accettarlo: una scaletta con i capitoli sbagliati o un capitolo fuori budget
vengono detti, non ingoiati.

Quello che si perde rispetto alla linea automatica, ed è giusto dirlo:

- i **riassunti di continuità** li fa il modello a ogni capitolo; qui al loro
  posto si usano i riassunti della scaletta, che sono più poveri ma veri;
- l'agente **indice** non gira: i titoli che scrivi nella scaletta sono
  definitivi;
- il **collegio di revisione** che usa il modello (lettore cieco,
  fact-checker, conformità, editor) resta fermo. Quelli deterministici —
  impaginazione, copertina — girano lo stesso, e `qa` pure.

Quello che non si perde: il libro esce identico. Gli stessi file, gli stessi
controlli, lo stesso PDF.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import planner, prompts, writer
from .llm import extract_json
from .mdlite import count_words
from .models import BookProject, BookSpec, Outline

#: dove vivono i brief prodotti e le risposte da importare
CARTELLA = "manuale"

#: scarto tollerato fra le parole chieste e quelle consegnate, prima di dirlo
TOLLERANZA_PAROLE = 0.25


def cartella(project: BookProject) -> Path:
    return project.root / CARTELLA


def percorso_brief(project: BookProject, nome: str) -> Path:
    return cartella(project) / f"{nome}-brief.md"


def percorso_risposta(project: BookProject, nome: str, suffisso: str) -> Path:
    return cartella(project) / f"{nome}.{suffisso}"


def _scrivi(percorso: Path, testo: str) -> Path:
    percorso.parent.mkdir(parents=True, exist_ok=True)
    percorso.write_text(testo, encoding="utf-8")
    return percorso


def _istruzioni(titolo: str, dove: Path, contratto: str) -> str:
    """L'intestazione che dice a chi legge che cosa farne.

    Sta in italiano anche quando il libro è in un'altra lingua: è una
    istruzione per chi lavora, non testo del libro.
    """
    return f"""<!-- {titolo}

     Prodotto dalla linea manuale: qui non c'è nessuna chiamata al modello.
     Porta tutto il testo qui sotto (dalla riga «SISTEMA» in giù) a un modello,
     oppure scrivilo a mano, e salva la risposta in:

       {dove}

     Poi importala. {contratto}

     Le righe fra <!-- e --> non fanno parte del prompt. -->
"""


def _prompt(sistema: str, utente: str) -> str:
    return f"""
SISTEMA
-------
{sistema}

RICHIESTA
---------
{utente}
"""


# --------------------------------------------------------------------------
# Scaletta
# --------------------------------------------------------------------------
def brief_scaletta(project: BookProject, spec: BookSpec, budget: planner.PageBudget) -> Path:
    """Il prompt della scaletta, con il budget già calcolato sulle pagine vere."""
    testo = _istruzioni(
        f"SCALETTA — {spec.title}",
        percorso_risposta(project, "scaletta", "json"),
        "Deve essere JSON valido: il sistema lo rifiuta se non lo è.",
    ) + _prompt(
        prompts.OUTLINE_SYSTEM,
        prompts.outline_prompt(spec, budget.chapters, budget.total_words),
    ) + f"""
<!-- Promemoria di ciò che il sistema farà dopo, e che quindi non devi fare tu:
     numera le sezioni, aggiunge introduzione e conclusione se previste
     ({'sì' if spec.include_intro else 'no'} / {'sì' if spec.include_conclusion else 'no'}),
     e ripartisce il budget di {budget.total_words:,} parole su {budget.chapters} capitoli.

     Quello che scrivi tu è definitivo: nella linea manuale l'agente «indice»
     non gira, quindi i titoli dei capitoli restano quelli che metti qui. È la
     pagina che un cliente guarda nell'anteprima prima di comprare. -->
""".replace(",", ".")
    return _scrivi(percorso_brief(project, "scaletta"), testo)


def importa_scaletta(
    project: BookProject, spec: BookSpec, budget: planner.PageBudget, testo: str
) -> Outline:
    """Valida la scaletta incollata e la salva come `outline.json`."""
    dati = extract_json(testo)
    grezza = Outline.from_dict(dati)
    if not grezza.chapters:
        raise SystemExit(
            "La scaletta non contiene nessun capitolo.\n"
            "Controlla che il JSON abbia la chiave `chapters` con dentro la lista."
        )
    senza_titolo = [c.number for c in grezza.chapters if not c.title.strip()]
    if senza_titolo:
        raise SystemExit(f"Capitoli senza titolo nella scaletta: {senza_titolo}")

    outline = writer.normalize_outline(spec, grezza, budget)
    outline.save(project.outline_path)
    return outline


# --------------------------------------------------------------------------
# Capitoli
# --------------------------------------------------------------------------
def _contesto(outline: Outline, numero: int) -> tuple[str, list[str]]:
    """Che cosa è già stato detto, preso dalla scaletta invece che dal modello.

    Nella linea automatica ogni capitolo lascia un riassunto scritto dal
    modello, e il capitolo dopo lo riceve. Qui quei riassunti non esistono: si
    usano quelli della scaletta, che sono più poveri — dicono il programma del
    capitolo, non come è venuto — ma sono veri e non costano niente.
    """
    precedenti = [c for c in outline.chapters if c.number < numero]
    covered = [f"{c.title}: {c.summary}".strip(": ") for c in precedenti if c.summary]
    ultimo = precedenti[-1].summary if precedenti else ""
    return ultimo, covered


def brief_capitolo(
    project: BookProject, spec: BookSpec, outline: Outline, numero: int
) -> Path:
    """Il prompt di un capitolo, con il contesto di quelli che lo precedono."""
    capitolo = next((c for c in outline.chapters if c.number == numero), None)
    if capitolo is None:
        disponibili = ", ".join(str(c.number) for c in outline.chapters)
        raise SystemExit(f"Nella scaletta non c'è un capitolo {numero}. Ci sono: {disponibili}")

    precedente, covered = _contesto(outline, numero)
    successivo = next((c.title for c in outline.chapters if c.number == numero + 1), "")
    testo = _istruzioni(
        f"CAPITOLO {numero} — {capitolo.title}",
        percorso_risposta(project, f"capitolo-{numero:02d}", "md"),
        f"Markdown, che comincia con «# {capitolo.title}». "
        f"Il budget è di {capitolo.target_words} parole.",
    ) + _prompt(
        prompts.author_rules() + "\n\n" + prompts.book_bible(spec, outline),
        prompts.chapter_prompt(
            spec,
            capitolo,
            previous_summary=precedente,
            covered=covered,
            next_title=successivo,
        ),
    )
    return _scrivi(percorso_brief(project, f"capitolo-{numero:02d}"), testo)


def importa_capitolo(
    project: BookProject, outline: Outline, numero: int, testo: str
) -> dict:
    """Salva il capitolo nel manoscritto e misura quanto si discosta dal budget."""
    capitolo = next((c for c in outline.chapters if c.number == numero), None)
    if capitolo is None:
        raise SystemExit(f"Nella scaletta non c'è un capitolo {numero}.")
    if not testo.strip():
        raise SystemExit(f"Il capitolo {numero} è vuoto: non lo scrivo sul manoscritto.")

    project.manuscript_dir.mkdir(parents=True, exist_ok=True)
    project.chapter_path(numero).write_text(
        writer._normalize_chapter(testo, capitolo), encoding="utf-8"
    )
    scritte = count_words(testo)
    chieste = capitolo.target_words or 0
    scarto = (scritte - chieste) / chieste if chieste else 0.0
    return {
        "numero": numero,
        "titolo": capitolo.title,
        "parole": scritte,
        "parole_chieste": chieste,
        "scarto": round(scarto, 3),
        "fuori_tolleranza": abs(scarto) > TOLLERANZA_PAROLE,
        "file": str(project.chapter_path(numero)),
    }


def stato_capitoli(project: BookProject, outline: Outline) -> list[dict]:
    """Quali sezioni della scaletta hanno già un testo, e quanto lungo."""
    righe = []
    for capitolo in outline.chapters:
        percorso = project.chapter_path(capitolo.number)
        parole = count_words(percorso.read_text(encoding="utf-8")) if percorso.exists() else 0
        righe.append(
            {
                "numero": capitolo.number,
                "titolo": capitolo.title,
                "parole": parole,
                "parole_chieste": capitolo.target_words,
                "scritto": percorso.exists(),
            }
        )
    return righe


# --------------------------------------------------------------------------
# Scheda prodotto
# --------------------------------------------------------------------------
def brief_scheda(project: BookProject, spec: BookSpec, outline: Outline) -> Path:
    """Il prompt della scheda KDP, con un estratto del libro già scritto."""
    capitoli = writer.load_chapters(project, outline)
    if not capitoli:
        raise SystemExit(
            "Nessun capitolo scritto: la scheda si prepara sul libro vero, "
            "non sul programma del libro."
        )
    estratto = "\n\n".join(testo for _, _, testo in capitoli[:2])
    testo = _istruzioni(
        f"SCHEDA PRODOTTO — {spec.title}",
        percorso_risposta(project, "scheda", "json"),
        "Deve essere JSON valido.",
    ) + _prompt(prompts.METADATA_SYSTEM, prompts.metadata_prompt(spec, outline, estratto))
    return _scrivi(percorso_brief(project, "scheda"), testo)


def importa_scheda(project: BookProject, testo: str) -> dict:
    """Valida la scheda incollata e la restituisce, senza scrivere i file.

    A scrivere `metadata.json` e `kdp-listing.md` resta `pipeline`, che ci
    aggiunge prezzi e royalty: qui si controlla solo che il JSON regga e che i
    campi che la scheda KDP pretende ci siano.
    """
    dati = extract_json(testo)
    mancanti = [
        campo
        for campo in ("title", "subtitle", "description_paragraphs", "keywords", "categories")
        if not dati.get(campo)
    ]
    if mancanti:
        raise SystemExit(
            "Alla scheda mancano campi che il pannello KDP pretende: "
            + ", ".join(mancanti)
        )
    return dati


def leggi_risposta(percorso: Path) -> str:
    if not percorso.exists():
        raise SystemExit(
            f"Manca {percorso}.\n"
            "Incolla lì dentro la risposta del modello (o il testo scritto a mano) e riprova."
        )
    return percorso.read_text(encoding="utf-8")


def riepilogo(project: BookProject) -> str:
    """Che cosa c'è già e che cosa manca, per chi riprende in mano il libro."""
    righe = [f"LINEA MANUALE — {project.root.name}", "-" * 42]
    scaletta = project.outline_path.exists()
    righe.append(f"  scaletta: {'sì' if scaletta else 'no'}")
    if scaletta:
        outline = Outline.load(project.outline_path)
        stato = stato_capitoli(project, outline)
        scritti = [r for r in stato if r["scritto"]]
        righe.append(f"  capitoli: {len(scritti)} su {len(stato)}")
        for r in stato:
            segno = "·" if r["scritto"] else " "
            parole = f"{r['parole']}/{r['parole_chieste']}" if r["scritto"] else "—"
            righe.append(f"    {segno} {r['numero']:>2}. {r['titolo'][:44]:<44} {parole}")
    scheda = (project.build_dir / "metadata.json").exists()
    righe.append(f"  scheda prodotto: {'sì' if scheda else 'no'}")
    return "\n".join(righe)


def json_leggibile(dati: dict) -> str:
    return json.dumps(dati, ensure_ascii=False, indent=2)

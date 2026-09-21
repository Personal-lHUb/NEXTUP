"""Da una scheda Amazon incollata alla scheda di un libro nuovo.

Quattro agenti in fila — estrazione, recensioni, posizionamento, originalità —
che si fermano prima della scrittura e consegnano `book.json` e `brief.md`. Da
lì in poi lavora il collegio di sempre, che non sa e non deve sapere da dove è
arrivata la scheda.

Il libro di partenza è un **segnale di mercato**: si leggono prezzo, categorie,
descrizione e recensioni, cioè quello che è pubblico sulla pagina, e non il
libro. Il controllo di originalità sta qui e non alla fine perché è qui che
correggere costa poco.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from .agents.base import AgentContext, AgentFinding, get_agent
from .llm import LLMClient
from .models import BookProject, BookSpec

#: Valute ammesse per il prezzo proposto, con il campo di `book.json` che le ospita.
VALUTE = {"EUR", "USD", "GBP"}

PAGINA_TEMPLATE = """<!-- SCHEDA DEL CONCORRENTE — ASIN {asin}

Incolla qui sotto la pagina Amazon del libro, così com'è. Non serve pulirla:
menu, banner e suggerimenti vengono scartati da soli.

Che cosa conta che ci sia, in ordine di importanza:

  1. LE RECENSIONI, soprattutto quelle da 2 e 3 stelle. Sono il pezzo che vale
     di più: chi le scrive ha pagato il libro e sta dicendo alla lettera quale
     libro avrebbe voluto. Aprile tutte («Visualizza tutte le recensioni») e
     incolla anche quelle, non solo le prime.
  2. La descrizione completa (apri «Leggi di più»).
  3. Il riquadro «Dettagli prodotto»: pagine, editore, data, dimensioni.
  4. La riga «Posizione nella classifica Bestseller» con tutte le categorie.
  5. Il prezzo, con la valuta.

Quello che manca resta vuoto: il sistema non inventa i numeri che non trova.

Le righe che cominciano con <!-- non vengono lette. -->

"""


@dataclass
class Acquisizione:
    """Quello che il reparto produce, prima che diventi un libro."""

    asin: str = ""
    scheda: dict = field(default_factory=dict)
    lacune: dict = field(default_factory=dict)
    piano: dict = field(default_factory=dict)
    segnalazioni: list[AgentFinding] = field(default_factory=list)
    note: dict[str, str] = field(default_factory=dict)

    @property
    def bloccanti(self) -> list[AgentFinding]:
        return [f for f in self.segnalazioni if f.severity == "bloccante"]

    def to_dict(self) -> dict:
        return {
            "asin": self.asin,
            "scheda": self.scheda,
            "lacune": self.lacune,
            "piano": self.piano,
            "originalita": {
                "note": self.note.get("originalita", ""),
                "segnalazioni": [f.to_dict() for f in self.segnalazioni],
            },
        }


# --------------------------------------------------------------------------
# Percorsi
# --------------------------------------------------------------------------
def cartella(project: BookProject) -> Path:
    return project.root / "concorrente"


def pagina_path(project: BookProject) -> Path:
    return cartella(project) / "pagina.md"


def acquisizione_path(project: BookProject) -> Path:
    return cartella(project) / "acquisizione.json"


# --------------------------------------------------------------------------
# Primo passo: lo spazio dove incollare
# --------------------------------------------------------------------------
def prepara(project: BookProject, asin: str) -> Path:
    """Crea la cartella e il file da riempire. Non tocca `book.json`."""
    cartella(project).mkdir(parents=True, exist_ok=True)
    percorso = pagina_path(project)
    percorso.write_text(PAGINA_TEMPLATE.format(asin=asin or "(non indicato)"), encoding="utf-8")
    return percorso


def leggi_pagina(project: BookProject) -> str:
    """Il testo incollato, senza le istruzioni del modulo."""
    percorso = pagina_path(project)
    if not percorso.exists():
        raise SystemExit(
            f"Manca {percorso}.\n"
            f"Crealo con: python -m kdpfactory concorrente new {project.root.name} --asin <ASIN>"
        )
    testo = percorso.read_text(encoding="utf-8")
    # Il commento di istruzioni si toglie per intero: contiene parole come
    # «recensioni» e «prezzo» che confonderebbero l'estrazione.
    if "-->" in testo:
        testo = testo.split("-->", 1)[1]
    return testo.strip()


# --------------------------------------------------------------------------
# Il reparto al lavoro
# --------------------------------------------------------------------------
def analizza(project: BookProject, client: LLMClient, asin: str = "") -> Acquisizione:
    """Fa girare i quattro agenti e restituisce il piano, senza scrivere il libro."""
    pagina = leggi_pagina(project)
    if len(pagina.split()) < 40:
        raise SystemExit(
            f"In {pagina_path(project)} ci sono meno di 40 parole: sembra vuoto.\n"
            "Incolla la pagina Amazon del libro, recensioni comprese, e rilancia."
        )

    risultato = Acquisizione(asin=asin)
    spec_finta = BookSpec(slug=project.root.name, title="(da decidere)")

    scheda = get_agent("scheda-concorrente").run(
        AgentContext(spec=spec_finta, text=pagina, metadata={"asin": asin}), client
    )
    risultato.scheda = scheda.data
    if not risultato.scheda.get("titolo"):
        raise SystemExit(
            "Dalla pagina incollata non è uscito nemmeno il titolo del libro.\n"
            f"Problemi segnalati: {risultato.scheda.get('problemi') or '(nessuno)'}\n"
            "Controlla di aver incollato una scheda prodotto e non un'altra pagina."
        )

    lacune = get_agent("analista-recensioni").run(
        AgentContext(spec=spec_finta, metadata={"scheda": risultato.scheda}), client
    )
    risultato.lacune = lacune.data

    piano = get_agent("posizionamento").run(
        AgentContext(
            spec=spec_finta,
            metadata={"scheda": risultato.scheda, "lacune": risultato.lacune},
        ),
        client,
    )
    risultato.piano = piano.data

    controllo = get_agent("originalita").run(
        AgentContext(
            spec=spec_finta,
            metadata={
                "scheda": risultato.scheda,
                "lacune": risultato.lacune,
                "piano": risultato.piano,
            },
        ),
        client,
    )
    risultato.segnalazioni = controllo.findings
    risultato.note["originalita"] = controllo.notes
    return risultato


# --------------------------------------------------------------------------
# Dal piano alla scheda del libro
# --------------------------------------------------------------------------
def _pagine_valide(valore) -> int:
    """Le pagine obiettivo, riportate dentro i limiti di progetto."""
    from . import kdpspecs

    try:
        pagine = int(valore)
    except (TypeError, ValueError):
        return 140
    return max(kdpspecs.PROJECT_MIN_PAGES, min(kdpspecs.PROJECT_MAX_PAGES, pagine))


def spec_dal_piano(slug: str, piano: dict, autore: str) -> BookSpec:
    """Traduce il piano del posizionamento in una `BookSpec` valida."""
    lingua = str(piano.get("lingua") or "it").strip().lower()[:2] or "it"
    return BookSpec(
        slug=slug,
        title=str(piano.get("titolo") or "").strip(),
        subtitle=str(piano.get("sottotitolo") or "").strip(),
        author=autore,
        language=lingua if lingua in {"it", "en"} else "it",
        topic=str(piano.get("argomento") or "").strip(),
        audience=str(piano.get("lettore") or "lettori generalisti").strip(),
        promise=str(piano.get("promessa") or "").strip(),
        tone=str(piano.get("tono") or BookSpec.tone).strip(),
        genre="fiction" if str(piano.get("genere")) == "fiction" else "non-fiction",
        content_type="medium" if str(piano.get("categoria")) == "medium" else "full",
        target_pages=_pagine_valide(piano.get("pagine_obiettivo")),
        keywords=[str(k).strip() for k in (piano.get("parole_chiave") or []) if str(k).strip()],
        categories=[str(c).strip() for c in (piano.get("categorie") or []) if str(c).strip()],
        price_eur=float(piano.get("prezzo") or 0.0),
        year=date.today().year,
    )


def brief_dal_piano(piano: dict, scheda: dict, asin: str) -> str:
    """Il `brief.md` che leggeranno architetto e ghostwriter.

    Non contiene la scheda del concorrente: gli agenti che scrivono il libro non
    devono averla sotto gli occhi. Contiene la lacuna da coprire e i confini.
    """
    righe = [
        f"# Argomenti da affrontare — {piano.get('titolo', '')}",
        "",
        "<!-- Scheda generata dal reparto di acquisizione a partire da un'analisi di",
        f"     mercato (ASIN di riferimento {asin or 'non indicato'}, «{scheda.get('titolo', '')}»).",
        "     Il libro di partenza non va letto, citato né nominato: qui sotto c'è solo",
        "     quello che serve a scrivere un libro indipendente. -->",
        "",
        "## Di che cosa parla il libro",
        str(piano.get("argomento", "")),
        "",
        "## A chi è rivolto",
        str(piano.get("lettore", "")),
        "",
        "## Che cosa si porta a casa il lettore",
        str(piano.get("promessa", "")),
        "",
        "## Il buco che questo libro copre",
        str(piano.get("la_lacuna_che_copre", "")),
        "",
    ]
    if piano.get("che_cosa_tiene"):
        righe += [
            "## Quello che i lettori di questa nicchia si aspettano e va mantenuto",
            *(f"- {t}" for t in piano["che_cosa_tiene"]),
            "",
        ]
    if piano.get("argomenti"):
        righe += ["## Temi da trattare", *(f"- {t}" for t in piano["argomenti"]), ""]
    if piano.get("che_cosa_non_fa"):
        righe += [
            "## Quello che il libro dichiaratamente NON fa",
            *(f"- {t}" for t in piano["che_cosa_non_fa"]),
            "",
        ]
    return "\n".join(righe)


def scrivi(project: BookProject, risultato: Acquisizione, autore: str) -> BookSpec:
    """Scrive `book.json` e `brief.md`. Si rifiuta se l'originalità ha bloccanti."""
    if risultato.bloccanti:
        raise SystemExit(
            "Il controllo di originalità ha trovato problemi bloccanti: la scheda non "
            "viene scritta.\n"
            + "\n".join(f"  ✗ {f.category} — {f.issue}" for f in risultato.bloccanti)
        )
    spec = spec_dal_piano(project.root.name, risultato.piano, autore)
    problemi = spec.validate()
    if problemi:
        raise SystemExit(
            "Il posizionamento ha prodotto una scheda non valida:\n"
            + "\n".join(f"  - {p}" for p in problemi)
        )
    project.ensure_dirs()
    spec.save(project.spec_path)
    project.brief_path.write_text(
        brief_dal_piano(risultato.piano, risultato.scheda, risultato.asin), encoding="utf-8"
    )
    acquisizione_path(project).parent.mkdir(parents=True, exist_ok=True)
    acquisizione_path(project).write_text(
        json.dumps(risultato.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return spec


# --------------------------------------------------------------------------
# Resoconto a schermo
# --------------------------------------------------------------------------
def render(risultato: Acquisizione) -> str:
    scheda, lacune, piano = risultato.scheda, risultato.lacune, risultato.piano
    righe = [
        "LIBRO DI PARTENZA",
        "-" * 42,
        f"  «{scheda.get('titolo', '')}» — {scheda.get('autore', '')}",
        f"  {scheda.get('pagine') or '?'} pagine · {scheda.get('prezzo') or '?'} "
        f"{scheda.get('valuta', '')} · voto {scheda.get('voto_medio') or '?'} "
        f"su {scheda.get('numero_recensioni') or '?'} recensioni",
    ]
    for categoria in scheda.get("categorie") or []:
        righe.append(f"  · {categoria.get('nome', '')} — n. {categoria.get('rango', '?')}")
    if scheda.get("problemi"):
        righe += ["  dalla pagina non è arrivato:"] + [
            f"    ! {p}" for p in scheda["problemi"]
        ]

    righe += ["", "QUELLO CHE I LETTORI NON HANNO TROVATO", "-" * 42]
    righe.append(
        f"  lettore reale: {lacune.get('lettore_reale', '?')}  "
        f"(confidenza {lacune.get('confidenza', '?')})"
    )
    for lacuna in lacune.get("lacune") or []:
        marchio = "▲" if lacuna.get("vale_un_libro") else "·"
        righe.append(
            f"  {marchio} [{lacuna.get('ricorrenze', '?')}x] {lacuna.get('tema', '')}: "
            f"{lacuna.get('che_cosa_manca', '')}"
        )
        for citazione in (lacuna.get("citazioni") or [])[:2]:
            righe.append(f"      «{citazione}»")

    righe += ["", "IL LIBRO PROPOSTO", "-" * 42]
    righe.append(f"  «{piano.get('titolo', '')}»")
    if piano.get("sottotitolo"):
        righe.append(f"  {piano['sottotitolo']}")
    categoria = "medium-content" if piano.get("categoria") == "medium" else "full-content"
    righe += [
        f"  {categoria} · {piano.get('pagine_obiettivo', '?')} pagine · "
        f"{piano.get('prezzo', '?')} {piano.get('valuta', '')} · {piano.get('lingua', '')}",
        f"  copre: {piano.get('la_lacuna_che_copre', '')}",
    ]
    for voce in piano.get("che_cosa_non_fa") or []:
        righe.append(f"  non fa: {voce}")

    righe += ["", "CONTROLLO DI ORIGINALITÀ", "-" * 42]
    if not risultato.segnalazioni:
        righe.append("  nessuna segnalazione.")
    for finding in risultato.segnalazioni:
        simbolo = {"bloccante": "✗", "importante": "!"}.get(finding.severity, "·")
        righe.append(f"  {simbolo} [{finding.severity}] {finding.category} — {finding.issue}")
        if finding.quote:
            righe.append(f"      «{finding.quote}»")
    if risultato.note.get("originalita"):
        righe.append(f"  → {risultato.note['originalita']}")
    return "\n".join(righe)

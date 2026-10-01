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
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from . import avvio as avvio_module
from . import coverdesign, kdpspecs
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
    #: la riga di indirizzo editoriale, se l'editore ne ha data una
    indicazione: str = ""
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
            "indicazione": self.indicazione,
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


def indicazione_path(project: BookProject) -> Path:
    return cartella(project) / "indicazione.md"


# --------------------------------------------------------------------------
# Primo passo: lo spazio dove incollare
# --------------------------------------------------------------------------
def prepara(project: BookProject, asin: str) -> Path:
    """Crea la cartella e il file da riempire. Non tocca `book.json`."""
    cartella(project).mkdir(parents=True, exist_ok=True)
    percorso = pagina_path(project)
    percorso.write_text(PAGINA_TEMPLATE.format(asin=asin or "(non indicato)"), encoding="utf-8")
    return percorso


def risposta_cowork_path(project: BookProject) -> Path:
    return cartella(project) / "cowork-concorrente-risposta.md"


def leggi_pagina(project: BookProject) -> str:
    """Il testo incollato, senza le istruzioni del modulo.

    Se il modulo è vuoto e la pagina l'ha portata Cowork, vale la sua risposta:
    si legge lì dov'è, senza copiarla, e il file di Cowork non si tocca.
    """
    percorso = pagina_path(project)
    risposta = risposta_cowork_path(project)
    if not percorso.exists() and not risposta.exists():
        raise SystemExit(
            f"Manca {percorso}.\n"
            f"Si crea con le domande d'avvio: python -m kdpfactory avvio {project.root.name}\n"
            f"(o, senza domande: python -m kdpfactory concorrente new {project.root.name} --asin <ASIN>)"
        )
    testo = percorso.read_text(encoding="utf-8") if percorso.exists() else ""
    # Il commento di istruzioni si toglie per intero: contiene parole come
    # «recensioni» e «prezzo» che confonderebbero l'estrazione.
    if "-->" in testo:
        testo = testo.split("-->", 1)[1]
    testo = testo.strip()
    if len(testo.split()) < 40 and risposta.exists():
        return risposta.read_text(encoding="utf-8").strip()
    return testo


# --------------------------------------------------------------------------
# Il reparto al lavoro
# --------------------------------------------------------------------------
def leggi_indicazione(project: BookProject) -> str:
    """L'indirizzo editoriale, se l'editore l'ha scritto.

    `posizionamento` decide il libro nuovo dai dati: la scheda del concorrente e
    le lacune delle sue recensioni. Ma la decisione di *che tipo* di libro fare
    dentro quella nicchia è dell'editore, non di un agente — e finora non aveva
    un posto dove stare, se non nella testa di chi lanciava il comando.
    """
    percorso = indicazione_path(project)
    if not percorso.exists():
        return ""
    tenute: list[str] = []
    dentro_commento = False
    for riga in percorso.read_text(encoding="utf-8").splitlines():
        nuda = riga.strip()
        # Il commento va scartato per intero, non riga per riga: un blocco
        # `<!-- … -->` su più righe lasciava dentro tutto il suo corpo, e le
        # istruzioni del modulo finivano nel prompt come se fossero la linea
        # editoriale.
        if dentro_commento:
            dentro_commento = "-->" not in nuda
            continue
        if nuda.startswith("<!--"):
            dentro_commento = "-->" not in nuda
            continue
        if nuda.startswith("#"):
            continue
        tenute.append(riga)
    return "\n".join(tenute).strip()


def leggi_parole_chiave(project: BookProject) -> str:
    """Le parole chiave della nicchia, come le ha riportate Cowork; vuoto se non sono arrivate."""
    risposta = cartella(project) / "cowork-parole-chiave-risposta.md"
    return risposta.read_text(encoding="utf-8").strip() if risposta.exists() else ""


def leggi_vincoli(project: BookProject, indicazione: str = "") -> str:
    """L'indirizzo editoriale con in coda le risposte alle domande d'avvio.

    Le domande d'avvio (`avvio.json`) sono le scelte dell'autore che valgono per
    ogni libro — mercato, categoria, dove battere il concorrente —, l'indicazione
    è quello che aggiunge per questo. Al posizionamento arrivano insieme; una
    `indicazione` data a riga di comando prende il posto del file, non dell'avvio.
    """
    parti = [indicazione or leggi_indicazione(project)]
    risposte = avvio_module.leggi(project)
    if risposte:
        parti.append(avvio_module.vincoli(risposte))
    return "\n\n".join(p for p in parti if p)


def analizza(
    project: BookProject, client: LLMClient, asin: str = "", indicazione: str = ""
) -> Acquisizione:
    """Fa girare i quattro agenti e restituisce il piano, senza scrivere il libro."""
    pagina = leggi_pagina(project)
    if len(pagina.split()) < 40:
        raise SystemExit(
            f"In {pagina_path(project)} ci sono meno di 40 parole: sembra vuoto.\n"
            "Incolla la pagina Amazon del libro, recensioni comprese, e rilancia."
        )

    risultato = Acquisizione(asin=asin, indicazione=indicazione or leggi_vincoli(project))
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
            metadata={
                "scheda": risultato.scheda,
                "lacune": risultato.lacune,
                "indicazione": risultato.indicazione,
                "parole_chiave": leggi_parole_chiave(project),
            },
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


#: I file del reparto quando lo fa lavorare la sessione, un agente alla volta,
#: senza chiave API: ognuno è la risposta JSON di un agente, nell'ordine.
FILE_DEL_REPARTO = (
    ("scheda.json", "scheda-concorrente"),
    ("lacune.json", "analista-recensioni"),
    ("piano.json", "posizionamento"),
    ("originalita.json", "originalita"),
)


def importa(project: BookProject, asin: str = "") -> Acquisizione:
    """L'analisi fatta dai subagent, raccolta dai file come se l'avesse fatta `analizza`.

    Nella linea manuale i quattro agenti li chiama la sessione e le risposte
    finiscono in `concorrente/`; da qui in poi il percorso è lo stesso della
    linea API, controlli e risposte d'avvio compresi.
    """
    mancanti = [f"{nome} ({agente})" for nome, agente in FILE_DEL_REPARTO
                if not (cartella(project) / nome).exists()]
    if mancanti:
        raise SystemExit(
            "Mancano le risposte di questi agenti, in "
            f"{cartella(project)}:\n" + "\n".join(f"  - {m}" for m in mancanti)
        )
    dati = {nome: json.loads((cartella(project) / nome).read_text(encoding="utf-8"))
            for nome, _ in FILE_DEL_REPARTO}
    risposte = avvio_module.leggi(project)
    controllo = dati["originalita.json"]
    risultato = Acquisizione(
        asin=asin or (risposte.asin if risposte else ""),
        indicazione=leggi_vincoli(project),
        scheda=dati["scheda.json"],
        lacune=dati["lacune.json"],
        piano=dati["piano.json"],
        segnalazioni=[AgentFinding.from_dict(f, "originalita") for f in controllo.get("findings") or []],
    )
    risultato.note["originalita"] = str(controllo.get("notes") or "")
    return risultato


# --------------------------------------------------------------------------
# Dal piano alla scheda del libro
# --------------------------------------------------------------------------
def _pagine_valide(valore) -> int:
    """Le pagine obiettivo, riportate dentro i limiti di progetto."""
    try:
        pagine = int(valore)
    except (TypeError, ValueError):
        return 140
    return max(kdpspecs.PROJECT_MIN_PAGES, min(kdpspecs.PROJECT_MAX_PAGES, pagine))


def _prezzo_valido(valore) -> float:
    """Il prezzo proposto, letto com'è scritto su una scheda vera.

    Su `amazon.it` il prezzo è «12,90 €», non `12.9`: la virgola decimale, il
    simbolo di valuta e gli spazi arrivano dentro il campo. Qui si toglie tutto
    quello che non è una cifra e si torna a zero se non ne resta niente —
    `metadata.py` calcola comunque un prezzo consigliato dalle pagine.
    """
    if isinstance(valore, (int, float)) and not isinstance(valore, bool):
        return max(0.0, float(valore))
    testo = re.sub(r"[^\d,.]", "", str(valore or ""))
    if not testo:
        return 0.0
    # «1.234,56» è europeo, «1,234.56» è anglosassone: decide l'ultimo separatore.
    if "," in testo and "." in testo:
        testo = (
            testo.replace(".", "").replace(",", ".")
            if testo.rfind(",") > testo.rfind(".")
            else testo.replace(",", "")
        )
    else:
        testo = testo.replace(",", ".")
    try:
        return max(0.0, float(testo))
    except ValueError:
        return 0.0


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
        price_eur=_prezzo_valido(piano.get("prezzo")),
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
    # L'analisi si salva per prima: costa quattro chiamate su una pagina intera
    # con tutte le recensioni, ed è la cosa più cara che il sistema produce.
    # Se il piano avesse un campo che non regge, si corregge a mano da qui
    # invece di ricomprare tutto.
    project.ensure_dirs()
    acquisizione_path(project).parent.mkdir(parents=True, exist_ok=True)
    acquisizione_path(project).write_text(
        json.dumps(risultato.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )

    spec = spec_dal_piano(project.root.name, risultato.piano, autore)
    _applica_avvio(project, spec)
    # Il titolo lo inventa `posizionamento`, e nessuno finora controllava che
    # stesse in copertina: il primo ad accorgersene era l'agente `copertina`,
    # alla fine di `all`, cioè dopo aver pagato il libro intero.
    problemi = spec.validate() + coverdesign.title_problems(spec.title, trim=spec.trim)
    insieme = len(spec.title) + len(spec.subtitle)
    if insieme > kdpspecs.TITLE_AND_SUBTITLE_MAX_CHARS:
        # Il limite di KDP esisteva solo in `qa.check_metadata`, cioè alla fine
        # di `all`: un titolo lungo si scopriva a libro scritto, impaginato e
        # pagato, e non si carica comunque.
        problemi.append(
            f"Titolo + sottotitolo fanno {insieme} caratteri: il limite di KDP è "
            f"{kdpspecs.TITLE_AND_SUBTITLE_MAX_CHARS} e il libro non si carica."
        )
    if problemi:
        raise SystemExit(
            "Il posizionamento ha prodotto una scheda non valida:\n"
            + "\n".join(f"  - {p}" for p in problemi)
            + f"\n\nL'analisi è salva in {acquisizione_path(project)}: "
            "correggi il piano lì dentro, non serve rifare le chiamate."
        )
    spec.save(project.spec_path)
    project.brief_path.write_text(
        brief_dal_piano(risultato.piano, risultato.scheda, risultato.asin), encoding="utf-8"
    )

    # Il taglio a 60 caratteri non è un limite di KDP: è dove Amazon tronca nei
    # risultati di ricerca, e quello che si taglia è sempre la seconda metà.
    # Non blocca — quasi ogni titolo vero lo supera — ma si guarda adesso, che
    # correggerlo costa una riga, non alla fine.
    vetrina = f"{spec.title}: {spec.subtitle}" if spec.subtitle else spec.title
    taglio = kdpspecs.TITLE_TRUNCATION_CHARS
    if len(vetrina) > taglio:
        print(
            f"\n  ! Nei risultati di ricerca si legge «{vetrina[:taglio]}…»: "
            f"{len(vetrina) - taglio} caratteri della promessa non si vedono.\n"
            f"    Se la promessa sta nella seconda metà, spostala prima del taglio "
            f"in {project.spec_path}."
        )
    return spec


def _applica_avvio(project: BookProject, spec: BookSpec) -> None:
    """Le risposte dell'autore battono il piano: lingua, categoria imposta, autore.

    Il posizionamento le riceve come vincolo, ma un vincolo in un prompt si può
    disattendere; qui no. Quando il piano diceva altro, lo si dice a schermo.
    """
    risposte = avvio_module.leggi(project)
    if not risposte:
        return
    if spec.language != risposte.lingua:
        print(f"  ! Il piano diceva lingua «{spec.language}»: vale «{risposte.lingua}» "
              f"del mercato {risposte.mercato}, scelto all'avvio.")
        spec.language = risposte.lingua
    if risposte.categoria in {"full", "medium"} and spec.content_type != risposte.categoria:
        print(f"  ! Il piano proponeva {spec.content_type}-content: vale {risposte.categoria}-content, "
              "scelto all'avvio.")
        spec.content_type = risposte.categoria
    if risposte.pseudonimo and spec.author in {"", "Autore Anonimo"}:
        spec.author = risposte.pseudonimo


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

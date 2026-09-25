"""Agente di copertina: scrive il prompt dell'illustrazione e misura la prima
come la vede il cliente.

Il prompt non lo scrive lui: lo produce `kdpfactory copertina` dai dati del
libro (CLAUDE.md), e l'agente ne verifica il risultato e ne corregge le fonti.
Come l'agente di impaginazione, non usa il modello. Una copertina non si
giudica a schermo intero: si giudica larga 160 pixel, su fondo bianco, in
mezzo ad altre venti. Quello che conta si misura — corpo del titolo rispetto
all'altezza, rapporto di contrasto, stacco del fondo dalla pagina dei
risultati, numero di blocchi nella metà alta, testo dentro l'area di sicurezza.

Oltre alle misure sul PDF, l'agente controlla i testi di copertina rispetto a
due regole: ci deve essere un ciclo aperto (una domanda o una promessa
incompleta, che è ciò che fa cliccare) e non ci devono essere rivendicazioni
vietate da KDP — classifiche, stelline, premi o recensioni stampati in
copertina.
"""

from __future__ import annotations

from .. import coverdesign
from .base import Agent, AgentContext, AgentFinding, AgentResult, register

#: rivendicazioni che KDP non ammette in copertina, e che comunque nessun
#: libro nuovo può mantenere
BANNED_CLAIMS = (
    "bestseller", "best seller", "best-seller", "#1", "n.1", "no.1", "numero 1",
    "award winning", "award-winning", "premiato", "vincitore",
    "5 stars", "5 stelle", "★", "recensioni", "reviews", "as seen on",
    "milioni di copie", "million copies",
)

#: un gancio è un ciclo aperto se chiede o promette qualcosa di incompiuto
OPEN_LOOP_MARKERS = ("?", "riesci", "can you", "what if", "e se", "prima che", "before")


@register
class Copertina(Agent):
    name = "copertina"
    title = "Copertina"
    description = (
        "Scrive il prompt dell'illustrazione di copertina — e delle figure interne, se il "
        "libro ne ha — con il comando del sistema e le linee guida di copertina; poi misura "
        "la copertina che torna: miniatura, contrasto, specifiche KDP, testi. Non usa il modello."
    )
    stage = "controllo"
    comando = "python3 -m kdpfactory copertina <slug>"
    istruzioni = """Sei l'unico agente che si occupa della copertina, dall'inizio alla fine: scrivi
il prompt che la fa nascere e misuri quello che torna. Nessun altro agente la
guarda, quindi quello che non vedi tu non lo vede nessuno.

Le regole che applichi sono in `docs/copertine.md` e nella sezione copertina di
`docs/linee-guida.md`. Una le riassume tutte, ed è scritta in `CLAUDE.md`:
**il prompt lo scrive il sistema, non la chat.**

## 1. Il prompt, prima che l'immagine esista

```bash
cd kdp-book-factory
python3 -m kdpfactory build <slug>        # le misure vengono dalle pagine vere
python3 -m kdpfactory copertina <slug>    # scrive build/copertina-brief.md
python3 -m kdpfactory immagini <slug>     # solo se il manoscritto dichiara figure
```

Il brief nasce dai dati del libro. Non lo riscrivi e non lo «migliori» a mano:
un prompt corretto in chat non lascia traccia e alla prossima rigenerazione
torna com'era. Se qualcosa non va, correggi il dato da cui viene e rigeneri.

Dove si corregge, a seconda di che cosa non va nel brief:

- l'occhiello non dice la categoria → `cover_kicker` nella scheda
  (`manuale/scheda.json`, poi `manuale <slug> scheda --importa`);
- il gancio non è un ciclo aperto, o promette troppo → `cover_hook` nella scheda;
- la promessa è vaga → `promise` in `book.json`;
- la rappresentazione non è quella del libro → le `categories`: il brief ricava
  da lì che cosa mostrare;
- l'oggetto proposto dal motore non rappresenta il libro → `cover_art` in
  `book.json`, oppure lascialo: il brief dice al grafico che può sostituirlo;
- la palette → `cover_theme` in `book.json`;
- le misure (pagine, dorso) sono vecchie → rilancia `build`, poi `copertina`.

Poi leggi il brief rigenerato e verificalo punto per punto:

1. **Categoria e rappresentazione**: dice che cosa mostrare, e non è una forma
   astratta dove una figura riconoscibile spiegherebbe il libro.
2. **Un solo fattore distintivo**, e uno solo.
3. **Il testo non va nell'immagine**: la sezione c'è, e i testi di riferimento
   (occhiello, gancio, autore) sono nella lingua del libro.
4. **Le misure sono quelle dell'ultima impaginazione**: pagine, dorso, area del
   codice a barre. Se il libro è cambiato dopo l'ultimo `build`, il brief è vecchio.
5. **La formula della categoria**: medium-content → funzione e un quantificatore
   contato sul libro; full-content → promessa, e nessuna cifra.
6. **Niente rivendicazioni vietate**: classifiche, stelline, recensioni, premi.
7. **Niente nomi altrui**: autori, marchi, personaggi, copertine da imitare.

Il brief che passa i sette punti è il prompt da consegnare, così com'è, a chi
genera l'immagine (ChatGPT, Gemini o un grafico). L'immagine che torna è la
sola illustrazione della prima, senza testo: si salva in
`books/<slug>/assets/copertina.jpg`.

## 2. La copertina che torna

```bash
python3 -m kdpfactory build <slug>                      # ritaglia, porta a 300 DPI, compone i testi
python3 -m kdpfactory review <slug> --agents copertina  # misura
```

**In miniatura** (è l'unico modo onesto di giudicare una copertina): corpo del
titolo rispetto all'altezza, contrasto, stacco su fondo bianco, affollamento
della metà alta, testo dentro l'area di sicurezza.

**Sulle specifiche KDP**, tutte bloccanti perché fermano il caricamento:
dimensioni del PDF contro il calcolo del dorso, area del codice a barre
libera, testo di dorso dentro le pieghe e ammesso solo da 79 pagine, font
incorporati, linee di piega rimaste nel file, autore uguale a quello della scheda.

**Sui testi**: gancio (ciclo aperto), rivendicazioni vietate da KDP, formula
della categoria, cifre che non corrispondono a un dato contato sul libro.

Poi guarda la miniatura (`build/<slug>-copertina-miniatura.png`) e chiediti, in
quest'ordine: in due secondi si capisce la categoria? L'immagine mostra il
soggetto vero del libro? C'è un solo concetto dominante? Il titolo vince su
tutto il resto? Sembra una copertina di quest'anno o un modello generico? Un
«no» si risolve nel brief — cioè nei dati da cui nasce — non con un'altra
immagine chiesta a voce.

## Formato della risposta

Prima il percorso del brief e l'esito dei sette punti; poi, se c'è già
un'immagine, le misure raggruppate per gravità (`bloccante`, `importante`,
`minore`) e il tuo giudizio sulla miniatura in tre righe. Per ogni correzione
indica il campo da cambiare e il valore nuovo. Non modificare i file: le
correzioni le applica chi ti ha chiamato, e poi si rigenera."""

    def system(self, ctx: AgentContext) -> list[str]:  # pragma: no cover - non usato
        return []

    def user(self, ctx: AgentContext) -> str:  # pragma: no cover - non usato
        return ""

    def run(self, ctx: AgentContext, client=None) -> AgentResult:
        findings = inspect_cover(ctx)
        notes = (
            "Copertina leggibile in miniatura e conforme."
            if not findings
            else f"{len(findings)} rilievi sulla copertina."
        )
        return AgentResult(agent=self.name, findings=findings, notes=notes)


#: quanto pesa ciascun difetto misurato: un titolo illeggibile in miniatura o
#: un testo tagliato dalla rifilatura fermano la pubblicazione, il resto no
SEVERITY_BY_KEYWORD = (
    ("area di sicurezza", "bloccante"),
    ("troppo piccolo", "bloccante"),
    ("contrasto", "bloccante"),
    ("non stacca", "importante"),
    ("blocchi di testo", "importante"),
    ("righe (massimo", "importante"),
    ("non è stato trovato", "bloccante"),
    # La formula della categoria (CLAUDE.md) si fa rispettare dove si misura:
    # un medium-content che non dice quanto contiene e un full-content vestito
    # da prodotto da scaffale sbagliano il cliente, non il gusto.
    ("senza quantificatore", "bloccante"),
    ("specifiche da scaffale", "bloccante"),
    ("non corrispondono a nessun dato", "bloccante"),
    ("senza segnale di categoria", "importante"),
)


def _severity(problem: str) -> str:
    lowered = problem.lower()
    for keyword, severity in SEVERITY_BY_KEYWORD:
        if keyword in lowered:
            return severity
    return "minore"


def inspect_cover(ctx: AgentContext) -> list[AgentFinding]:
    findings: list[AgentFinding] = []
    findings.extend(_measure(ctx))
    findings.extend(_production(ctx))
    findings.extend(_read_copy(ctx))
    return findings


def _production(ctx: AgentContext) -> list[AgentFinding]:
    """I controlli tecnici: quelli che fanno rimbalzare il caricamento.

    Sono tutti bloccanti e nessuno è opinabile. Una copertina illeggibile in
    miniatura vende poco; una copertina con il dorso sbagliato non vende
    niente, perché non viene pubblicata.
    """
    if not ctx.cover_pdf or not ctx.cover_pdf.exists() or not ctx.pages:
        return []
    return [
        AgentFinding(
            agent=Copertina.name,
            severity="bloccante",
            category="specifiche KDP",
            issue=problema,
            suggestion="KDP verifica questo al caricamento: finché non torna, il libro non esce.",
        )
        for problema in coverdesign.audit_production(
            ctx.cover_pdf,
            trim=ctx.spec.trim,
            pages=ctx.pages,
            paper=ctx.spec.paper,
            author=ctx.spec.author,
        )
    ]


def _measure(ctx: AgentContext) -> list[AgentFinding]:
    """Le misure sul PDF vero: è l'unico giudizio che non dipende dai gusti."""
    if not ctx.cover_pdf or not ctx.cover_pdf.exists():
        return [
            AgentFinding(
                agent=Copertina.name,
                severity="importante",
                category="copertina mancante",
                issue="Nessun PDF di copertina da controllare: esegui prima `build`.",
            )
        ]

    genre = "enigmi" if ctx.spec.genre == "puzzle" else ctx.spec.genre
    palette = coverdesign.pick_palette(ctx.spec, genre)
    verdict = coverdesign.audit(
        ctx.cover_pdf,
        trim=ctx.spec.trim,
        pages=ctx.pages,
        paper=ctx.spec.paper,
        palette=palette,
        title=ctx.spec.title,
    )
    findings = [
        AgentFinding(
            agent=Copertina.name,
            severity=_severity(problem),
            category="miniatura",
            issue=problem,
            suggestion=_remedy(problem),
        )
        for problem in verdict.problems
    ]
    if not findings and verdict.title_cap_ratio < coverdesign.GOOD_TITLE_CAP_RATIO:
        findings.append(
            AgentFinding(
                agent=Copertina.name,
                severity="minore",
                category="miniatura",
                issue=(
                    f"Il titolo occupa il {verdict.title_cap_ratio * 100:.1f}% dell'altezza: "
                    f"leggibile, ma sotto il {coverdesign.GOOD_TITLE_CAP_RATIO * 100:.0f}% "
                    "che rende un titolo davvero dominante."
                ),
                suggestion="Accorcia il titolo in copertina o togli una riga di testo secondario.",
            )
        )
    return findings


REMEDIES = {
    "area di sicurezza": "Riduci la misura del testo o accorcia la riga: KDP rifila 3 mm.",
    "troppo piccolo": "Accorcia il titolo: meno parole, corpo più grande.",
    "contrasto": "Cambia palette, o porta il titolo a bianco pieno sul fondo scuro.",
    "non stacca": "Scegli una palette con fondo scuro o saturo: su bianco il bordo sparisce.",
    "blocchi di testo": "Togli un elemento dalla metà alta: sopravvive solo ciò che si legge.",
    "righe (massimo": "Accorcia il titolo: il resto della promessa va nel sottotitolo "
                      "della scheda, non in copertina.",
}


def _remedy(problem: str) -> str:
    lowered = problem.lower()
    for keyword, remedy in REMEDIES.items():
        if keyword in lowered:
            return remedy
    return ""


def _read_copy(ctx: AgentContext) -> list[AgentFinding]:
    """I testi di copertina: ciclo aperto e rivendicazioni non ammesse."""
    copy = ctx.cover_copy or {}
    findings: list[AgentFinding] = []

    written = " ".join(
        str(copy.get(key, "")) for key in ("title", "kicker", "hook", "stats", "badge")
    ).strip()
    if not written:
        return findings

    lowered = written.lower()
    for claim in BANNED_CLAIMS:
        if claim in lowered:
            findings.append(
                AgentFinding(
                    agent=Copertina.name,
                    severity="bloccante",
                    category="rivendicazione vietata",
                    issue=(
                        f"In copertina compare «{claim}»: KDP non ammette classifiche, "
                        "premi o recensioni stampati sulla copertina."
                    ),
                    quote=written[:160],
                    suggestion="Sostituiscila con una garanzia vera e verificabile sul contenuto.",
                )
            )
            break

    hook = str(copy.get("hook", ""))
    if not hook:
        findings.append(
            AgentFinding(
                agent=Copertina.name,
                severity="importante",
                category="ciclo aperto",
                issue="Manca il gancio: nessuna domanda e nessuna promessa incompleta.",
                suggestion="Aggiungi una riga che lasci qualcosa in sospeso: è ciò che fa cliccare.",
            )
        )
    elif not any(marker in hook.lower() for marker in OPEN_LOOP_MARKERS):
        findings.append(
            AgentFinding(
                agent=Copertina.name,
                severity="minore",
                category="ciclo aperto",
                issue=f"Il gancio «{hook}» descrive invece di chiedere: il ciclo resta chiuso.",
                suggestion="Trasformalo in una domanda o in una promessa che il libro completa.",
            )
        )

    stats = str(copy.get("stats", ""))
    if stats and not any(char.isdigit() for char in stats):
        findings.append(
            AgentFinding(
                agent=Copertina.name,
                severity="minore",
                category="numeri in lettere",
                issue=f"I numeri di copertina sono scritti in lettere: «{stats}».",
                suggestion="Usa le cifre: in miniatura si leggono in un colpo d'occhio.",
            )
        )

    findings.extend(
        AgentFinding(
            agent=Copertina.name,
            severity=_severity(problem),
            category="categoria di prodotto",
            issue=problem,
            suggestion=_remedy(problem),
        )
        for problem in coverdesign.copy_problems(coverdesign.copy_from_dict(copy, ctx.spec))
    )
    return findings

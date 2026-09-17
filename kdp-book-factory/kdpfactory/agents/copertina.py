"""Agente di copertina: misura la prima come la vede il cliente.

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
    title = "Controllo copertina"
    description = (
        "Misura la prima di copertina come si vede in miniatura: corpo del titolo, "
        "contrasto, stacco su fondo bianco, affollamento, area di sicurezza. "
        "Controlla anche i testi: ciclo aperto e rivendicazioni vietate. "
        "Non usa il modello."
    )
    stage = "controllo"

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
    findings.extend(_read_copy(ctx))
    return findings


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
    return findings

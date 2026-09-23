"""Infrastruttura comune del collegio editoriale.

Un agente è un ruolo con un compito preciso, un proprio prompt di sistema e un
formato di uscita definito. Due famiglie:

- `WriterAgent`  produce testo (scaletta, capitolo, riscrittura);
- `ReviewAgent`  legge e produce segnalazioni strutturate, non tocca il testo.

Solo l'`editor` applica le modifiche: i revisori segnalano e basta. È la stessa
separazione che esiste in una redazione, e serve a evitare che ogni passaggio
riscriva il libro a modo suo.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from ..models import BookSpec, ChapterPlan, Outline

if TYPE_CHECKING:  # pragma: no cover
    from ..llm import LLMClient

SEVERITIES = ("bloccante", "importante", "minore")
SEVERITY_ORDER = {name: index for index, name in enumerate(SEVERITIES)}


@dataclass
class AgentFinding:
    """Una segnalazione di un agente di controllo."""

    agent: str
    severity: str            # bloccante | importante | minore
    category: str            # etichetta breve, es. "continuità", "claim non verificabile"
    issue: str               # cosa non va
    chapter: int | None = None
    quote: str = ""          # passaggio incriminato, testuale
    suggestion: str = ""     # cosa fare

    def __post_init__(self) -> None:
        if self.severity not in SEVERITY_ORDER:
            self.severity = "minore"

    @property
    def sort_key(self) -> tuple[int, int]:
        return (SEVERITY_ORDER[self.severity], self.chapter or 0)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict, agent: str, chapter: int | None = None) -> AgentFinding:
        return cls(
            agent=agent,
            severity=str(data.get("severity") or data.get("gravita") or "minore").lower(),
            category=str(data.get("category") or data.get("categoria") or "generale"),
            issue=str(data.get("issue") or data.get("problema") or "").strip(),
            chapter=data.get("chapter", data.get("capitolo", chapter)),
            quote=str(data.get("quote") or data.get("citazione") or "").strip(),
            suggestion=str(data.get("suggestion") or data.get("soluzione") or "").strip(),
        )

    def render(self) -> str:
        symbol = {"bloccante": "✗", "importante": "!", "minore": "·"}[self.severity]
        where = f"cap. {self.chapter}" if self.chapter else "libro"
        lines = [f"  {symbol} [{self.agent}] {where} — {self.category}: {self.issue}"]
        if self.quote:
            lines.append(f"      «{self.quote[:160]}»")
        if self.suggestion:
            lines.append(f"      → {self.suggestion}")
        return "\n".join(lines)


@dataclass
class AgentContext:
    """Tutto ciò che un agente può ricevere. Ogni ruolo usa solo ciò che gli serve."""

    spec: BookSpec
    outline: Outline | None = None
    chapter: ChapterPlan | None = None
    text: str = ""
    previous_summary: str = ""
    covered: list[str] = field(default_factory=list)
    next_title: str = ""
    findings: list[AgentFinding] = field(default_factory=list)
    target_words: int = 0
    pdf_path: Path | None = None
    pages: int = 0
    chapter_pages: dict[str, int] = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
    cover_pdf: Path | None = None
    cover_copy: dict = field(default_factory=dict)


@dataclass
class AgentResult:
    agent: str
    text: str = ""
    findings: list[AgentFinding] = field(default_factory=list)
    notes: str = ""
    data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "agent": self.agent,
            "notes": self.notes,
            "findings": [f.to_dict() for f in self.findings],
        }


class Agent:
    """Ruolo editoriale."""

    name: ClassVar[str] = "agente"
    title: ClassVar[str] = "Agente"
    description: ClassVar[str] = ""
    stage: ClassVar[str] = "produzione"     # produzione | controllo
    effort: ClassVar[str] = "high"
    max_tokens: ClassVar[int] = 16000
    #: un revisore "cieco" non riceve la scheda del libro né la scaletta
    blind: ClassVar[bool] = False
    #: gli agenti che non usano il modello non hanno un prompt: hanno un comando.
    #: Serve a esportarli come subagent di Claude Code con le istruzioni giuste.
    comando: ClassVar[str] = ""
    istruzioni: ClassVar[str] = ""

    # -- da implementare --------------------------------------------------
    def system(self, ctx: AgentContext) -> list[str]:
        raise NotImplementedError

    def user(self, ctx: AgentContext) -> str:
        raise NotImplementedError

    @property
    def deterministico(self) -> bool:
        """Questo agente misura invece di chiedere: non serve la credenziale.

        Si riconosce dal comando: un agente strumentale non ha un prompt, ha
        un modo di essere eseguito.
        """
        return bool(self.comando)

    # -- esecuzione -------------------------------------------------------
    def label(self, ctx: AgentContext) -> str:
        chapter = f" · cap. {ctx.chapter.number}" if ctx.chapter else ""
        return f"{self.title}{chapter}"

    def run(self, ctx: AgentContext, client: LLMClient) -> AgentResult:
        raise NotImplementedError


class WriterAgent(Agent):
    """Agente che produce testo."""

    stage = "produzione"
    max_tokens = 32000

    def run(self, ctx: AgentContext, client: LLMClient) -> AgentResult:
        text = client.complete(
            system=self.system(ctx),
            user=self.user(ctx),
            label=self.label(ctx),
            max_tokens=self.max_tokens,
        )
        return AgentResult(agent=self.name, text=text)


class JsonAgent(Agent):
    """Agente che produce una struttura dati (es. la scaletta)."""

    stage = "produzione"
    max_tokens = 16000

    def run(self, ctx: AgentContext, client: LLMClient) -> AgentResult:
        data = client.complete_json(
            system=self.system(ctx),
            user=self.user(ctx),
            label=self.label(ctx),
            max_tokens=self.max_tokens,
        )
        return AgentResult(agent=self.name, data=data)


class ReviewAgent(Agent):
    """Agente che legge e segnala, senza modificare il testo."""

    stage = "controllo"
    max_tokens = 8000

    #: istruzione comune sul formato di uscita
    OUTPUT_CONTRACT = """Rispondi ESCLUSIVAMENTE con un oggetto JSON valido, senza testo prima o dopo:
{
  "notes": "una frase di giudizio complessivo",
  "findings": [
    {
      "severity": "bloccante | importante | minore",
      "category": "etichetta breve del problema",
      "issue": "che cosa non va, in una o due frasi",
      "quote": "il passaggio esatto copiato dal testo (max 30 parole)",
      "suggestion": "che cosa fare, in modo operativo"
    }
  ]
}
Regole: massimo 8 segnalazioni, dalla più grave. `quote` deve essere copiato alla lettera dal
testo ricevuto, altrimenti lascialo vuoto. Se non trovi nulla di rilevante, restituisci
"findings": []."""

    def run(self, ctx: AgentContext, client: LLMClient) -> AgentResult:
        data = client.complete_json(
            system=self.system(ctx),
            user=self.user(ctx),
            label=self.label(ctx),
            max_tokens=self.max_tokens,
        )
        chapter_number = ctx.chapter.number if ctx.chapter else None
        findings = [
            AgentFinding.from_dict(item, self.name, chapter_number)
            for item in data.get("findings", [])
            if isinstance(item, dict) and (item.get("issue") or item.get("problema"))
        ]
        return AgentResult(agent=self.name, findings=findings, notes=str(data.get("notes", "")))


# --------------------------------------------------------------------------
# Registro
# --------------------------------------------------------------------------
REGISTRY: dict[str, Agent] = {}


def register(agent_class: type[Agent]) -> type[Agent]:
    REGISTRY[agent_class.name] = agent_class()
    return agent_class


def get_agent(name: str) -> Agent:
    try:
        return REGISTRY[name]
    except KeyError:
        raise ValueError(
            f"Agente sconosciuto: {name!r}. Disponibili: {', '.join(sorted(REGISTRY))}"
        ) from None


def agents_by_stage(stage: str) -> list[Agent]:
    return [a for a in REGISTRY.values() if a.stage == stage]


def review_agents() -> list[Agent]:
    return agents_by_stage("controllo")


def filter_findings(
    findings: list[AgentFinding], min_severity: str = "minore"
) -> list[AgentFinding]:
    threshold = SEVERITY_ORDER.get(min_severity, 2)
    return [f for f in findings if SEVERITY_ORDER[f.severity] <= threshold]

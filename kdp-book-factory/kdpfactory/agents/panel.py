"""Orchestrazione del collegio: chi legge cosa, in che ordine, e chi applica.

Il ciclo è quello di una redazione:

    ghostwriter → [voce] → impaginazione → collegio di revisione → editor → nuova impaginazione

I revisori non toccano il testo: producono segnalazioni. L'unico che scrive
dopo di loro è l'editor, che le applica rispettando il budget di parole (se
cambiasse la lunghezza, cambierebbe il numero di pagine del libro).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .. import backup, vetrina
from ..llm import LLMClient
from ..mdlite import count_words, strip_title
from ..models import BookProject, BookSpec, Outline
from ..writer import load_chapters
from .base import (
    SEVERITY_ORDER,
    AgentContext,
    AgentFinding,
    filter_findings,
    get_agent,
)

# Agenti che leggono un capitolo per volta.
CHAPTER_REVIEWERS = ("lettore-cieco", "fact-checker", "conformita", "correttore")
# Agenti che guardano il libro intero, la scheda o il PDF. Il lettore cieco
# compare anche qui: sul capitolo dice dove ci si perde, sul libro verifica che
# il libro mantenga quello che la vetrina prometteva. La conformità, dopo i
# capitoli, legge la scheda prodotto: parole chiave e descrizione sono il primo
# testo che Amazon controlla.
BOOK_REVIEWERS = ("lettore-cieco", "editor-sviluppo", "conformita", "impaginazione", "copertina")
# Agenti che misurano invece di leggere: non ricevono il modello.
MEASURING_REVIEWERS = ("impaginazione", "copertina")

#: Livelli di lavorazione: quali agenti entrano in gioco e con quale severità
#: l'editor interviene.
QUALITY_LEVELS: dict[str, dict] = {
    "bozza": {
        "voce": False,
        "reviewers": (),
        "apply": None,
        "descrizione": "solo stesura: nessuna revisione, per valutare un'idea",
    },
    "standard": {
        "voce": False,
        "reviewers": (
            "lettore-cieco",
            "fact-checker",
            "conformita",
            "editor-sviluppo",
            "impaginazione",
            "copertina",
        ),
        "apply": "importante",
        "descrizione": "stesura + collegio di revisione; l'editor applica bloccanti e importanti",
    },
    "alta": {
        "voce": True,
        "reviewers": CHAPTER_REVIEWERS + BOOK_REVIEWERS,
        "apply": "minore",
        "descrizione": "come standard, più la passata di stile e il correttore di bozze; "
        "l'editor applica tutto",
    },
}
DEFAULT_QUALITY = "standard"


@dataclass
class ReviewReport:
    findings: list[AgentFinding] = field(default_factory=list)
    notes: dict[str, str] = field(default_factory=dict)

    def add(self, agent: str, findings: list[AgentFinding], note: str = "") -> None:
        self.findings.extend(findings)
        if note:
            self.notes[agent] = note

    @property
    def blocking(self) -> list[AgentFinding]:
        return [f for f in self.findings if f.severity == "bloccante"]

    def by_chapter(self) -> dict[int | None, list[AgentFinding]]:
        grouped: dict[int | None, list[AgentFinding]] = {}
        for finding in self.findings:
            grouped.setdefault(finding.chapter, []).append(finding)
        return grouped

    def counts(self) -> dict[str, int]:
        counts = {severity: 0 for severity in SEVERITY_ORDER}
        for finding in self.findings:
            counts[finding.severity] += 1
        return counts

    def to_dict(self) -> dict:
        return {
            "conteggi": self.counts(),
            "note_agenti": self.notes,
            "segnalazioni": [f.to_dict() for f in self.findings],
        }

    def render(self) -> str:
        counts = self.counts()
        lines = ["Collegio di revisione", "=" * 42]
        for agent, note in self.notes.items():
            lines.append(f"  · {agent}: {note}")
        if self.notes:
            lines.append("-" * 42)
        for finding in sorted(self.findings, key=lambda f: f.sort_key):
            lines.append(finding.render())
        lines.append("-" * 42)
        lines.append(
            f"  {counts['bloccante']} bloccanti, {counts['importante']} importanti, "
            f"{counts['minore']} minori"
        )
        return "\n".join(lines)

    def render_markdown(self, spec: BookSpec) -> str:
        lines = [f"# Revisione — {spec.title}", ""]
        counts = self.counts()
        lines.append(
            f"{counts['bloccante']} bloccanti · {counts['importante']} importanti · "
            f"{counts['minore']} minori"
        )
        lines.append("")
        if self.notes:
            lines += ["## Giudizi degli agenti", ""]
            for agent, note in self.notes.items():
                lines.append(f"- **{agent}**: {note}")
            lines.append("")
        grouped = self.by_chapter()
        for chapter in sorted(grouped, key=lambda c: (c is None, c or 0)):
            title = f"## Capitolo {chapter}" if chapter else "## Libro"
            lines += [title, ""]
            for finding in sorted(grouped[chapter], key=lambda f: f.sort_key):
                lines.append(
                    f"- **[{finding.severity}]** *{finding.agent}* — "
                    f"{finding.category}: {finding.issue}"
                )
                if finding.quote:
                    lines.append(f"  > {finding.quote}")
                if finding.suggestion:
                    lines.append(f"  → {finding.suggestion}")
            lines.append("")
        return "\n".join(lines)

    def save(self, project: BookProject, spec: BookSpec) -> Path:
        project.build_dir.mkdir(parents=True, exist_ok=True)
        (project.build_dir / "revisioni.json").write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        path = project.build_dir / "revisioni.md"
        path.write_text(self.render_markdown(spec), encoding="utf-8")
        return path

    @classmethod
    def load(cls, project: BookProject) -> ReviewReport:
        path = project.build_dir / "revisioni.json"
        if not path.exists():
            return cls()
        data = json.loads(path.read_text(encoding="utf-8"))
        report = cls(notes=data.get("note_agenti", {}))
        for item in data.get("segnalazioni", []):
            report.findings.append(
                AgentFinding(
                    agent=item.get("agent", "?"),
                    severity=item.get("severity", "minore"),
                    category=item.get("category", ""),
                    issue=item.get("issue", ""),
                    chapter=item.get("chapter"),
                    quote=item.get("quote", ""),
                    suggestion=item.get("suggestion", ""),
                )
            )
        return report


def _book_digest(
    project: BookProject, outline: Outline, excerpt_words: int = 120, *, blind: bool = False
) -> str:
    """Sintesi del libro: apertura e chiusura di ogni capitolo.

    Con `blind` la sintesi di lavorazione resta fuori: è materiale d'autore, e
    un lettore non ce l'ha.
    """
    state = project.load_state()
    summaries = {int(k): v for k, v in state.get("summaries", {}).items()}
    parts: list[str] = []
    for number, title, text in load_chapters(project, outline):
        words = text.split()
        opening = " ".join(words[:excerpt_words])
        closing = " ".join(words[-excerpt_words:])
        riga = f"### Capitolo {number}: {title} ({len(words)} parole)\n"
        if not blind:
            riga += f"Sintesi: {summaries.get(number, '(non disponibile)')}\n"
        parts.append(riga + f"Apertura: «{opening}…»\nChiusura: «…{closing}»")
    return "\n\n".join(parts)


def _indice(outline: Outline, language: str = "it") -> str:
    """L'indice come lo vede chi apre l'anteprima: parti, numero e titolo."""
    return vetrina.indice(outline, language)


def run_review(
    project: BookProject,
    spec: BookSpec,
    outline: Outline,
    client: LLMClient,
    *,
    agent_names: tuple[str, ...] | list[str] = (),
    only: list[int] | None = None,
) -> ReviewReport:
    """Fa leggere il libro al collegio e raccoglie le segnalazioni."""
    # Il lettore cieco sta in tutte e due le liste: senza deduplicare leggerebbe
    # ogni capitolo due volte al livello «alta», che le somma.
    names = list(dict.fromkeys(agent_names or QUALITY_LEVELS[DEFAULT_QUALITY]["reviewers"]))
    report = ReviewReport()
    chapters = load_chapters(project, outline)
    if not chapters:
        raise RuntimeError("Nessun capitolo da revisionare: esegui prima `write`.")

    state = project.load_state()
    build = state.get("build", {})
    cover = state.get("cover", {})
    pdf_path = Path(build["interno_pdf"]) if build.get("interno_pdf") else None
    cover_file = cover.get("cover_pdf") or build.get("copertina_pdf")
    cover_pdf = Path(cover_file) if cover_file else None

    chapter_agents = [get_agent(n) for n in names if n in CHAPTER_REVIEWERS]
    book_agents = [get_agent(n) for n in names if n in BOOK_REVIEWERS]

    for number, title, text in chapters:
        if only and number not in only:
            continue
        plan = next((c for c in outline.chapters if c.number == number), None)
        for agent in chapter_agents:
            ctx = AgentContext(
                spec=spec,
                # Il lettore cieco non riceve né scaletta né scheda del libro.
                outline=None if agent.blind else outline,
                chapter=None if agent.blind else plan,
                text=f"# {title}\n\n{text}" if agent.blind else text,
            )
            result = agent.run(ctx, client)
            for finding in result.findings:
                finding.chapter = number
            report.add(agent.name, result.findings, result.notes)

    for agent in book_agents:
        if agent.name in MEASURING_REVIEWERS:
            # Questi due non leggono: misurano il PDF. Niente modello, niente
            # testo del libro — solo le coordinate di quello che è stampato.
            ctx = AgentContext(
                spec=spec,
                outline=outline,
                pdf_path=pdf_path,
                pages=build.get("pagine", 0),
                chapter_pages=build.get("chapter_pages", {}),
                cover_pdf=cover_pdf,
                cover_copy=cover.get("testi", {}),
            )
            result = agent.run(ctx, None)
        elif agent.name == "conformita":
            # Sul libro la conformità legge la scheda prodotto. Senza scheda,
            # o con una revisione ristretta a certi capitoli, non c'è niente
            # da leggere qui.
            meta_path = project.build_dir / "metadata.json"
            if only or not meta_path.exists():
                continue
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            ctx = AgentContext(spec=spec, metadata={"scheda": vetrina.scheda(meta, spec)})
            result = agent.run(ctx, client)
        elif agent.blind:
            if only:
                # Revisione ristretta a certi capitoli: leggere il libro intero
                # è fuori da quello che è stato chiesto, e costa una chiamata su
                # tutto il testo.
                continue
            # Riceve l'indice — quello che ha visto in anteprima prima di
            # comprare — e il libro, ma non la scaletta: quella gli direbbe che
            # cosa avrebbe dovuto capire.
            ctx = AgentContext(
                spec=spec,
                outline=None,
                text=_book_digest(project, outline, blind=True),
                metadata={"vetrina": vetrina.da_progetto(project, spec, outline)},
            )
            result = agent.run(ctx, client)
        else:
            ctx = AgentContext(spec=spec, outline=outline, text=_book_digest(project, outline))
            result = agent.run(ctx, client)
        report.add(agent.name, result.findings, result.notes)

    report.save(project, spec)
    project.update_state(review=report.counts())
    return report


def apply_revisions(
    project: BookProject,
    spec: BookSpec,
    outline: Outline,
    client: LLMClient,
    report: ReviewReport,
    *,
    min_severity: str = "importante",
    only: list[int] | None = None,
) -> list[int]:
    """L'editor applica le segnalazioni, capitolo per capitolo."""
    editor = get_agent("editor")
    grouped = report.by_chapter()
    revised: list[int] = []

    for number, title, text in load_chapters(project, outline):
        if only and number not in only:
            continue
        findings = filter_findings(grouped.get(number, []), min_severity)
        if not findings:
            continue
        plan = next((c for c in outline.chapters if c.number == number), None)
        current_words = count_words(text)
        ctx = AgentContext(
            spec=spec,
            outline=outline,
            chapter=plan,
            text=f"# {title}\n\n{text}",
            findings=findings,
            target_words=(plan.target_words if plan and plan.target_words else current_words),
        )
        result = editor.run(ctx, client)
        new_text = result.text.strip()
        if count_words(new_text) < max(250, current_words * 0.5):
            print(f"    capitolo {number}: revisione scartata (testo troppo corto)")
            continue
        _, body = strip_title(new_text)
        project.chapter_path(number).write_text(
            f"# {title}\n\n{body.strip()}\n", encoding="utf-8"
        )
        revised.append(number)

    if revised:
        project.update_state(last_revision={"capitoli": revised, "severita": min_severity})
    return revised


def voice_pass(
    project: BookProject,
    spec: BookSpec,
    outline: Outline,
    client: LLMClient,
    *,
    only: list[int] | None = None,
) -> list[int]:
    """Passata di stile su ogni capitolo (livello `alta`)."""
    # Anche questa riscrive i capitoli sul posto: copia di sicurezza prima.
    backup.snapshot(project, "prima della passata di stile", force=True)
    voce = get_agent("voce")
    touched: list[int] = []
    for number, title, text in load_chapters(project, outline):
        if only and number not in only:
            continue
        plan = next((c for c in outline.chapters if c.number == number), None)
        ctx = AgentContext(spec=spec, outline=outline, chapter=plan, text=f"# {title}\n\n{text}")
        result = voce.run(ctx, client)
        new_text = result.text.strip()
        words_before, words_after = count_words(text), count_words(new_text)
        if not new_text or words_after < words_before * 0.7:
            print(f"    capitolo {number}: passata di stile scartata")
            continue
        _, body = strip_title(new_text)
        project.chapter_path(number).write_text(
            f"# {title}\n\n{body.strip()}\n", encoding="utf-8"
        )
        touched.append(number)
    return touched


def describe_panel() -> str:
    """Elenco degli agenti, per `kdpfactory agents`."""
    from .base import REGISTRY

    lines = ["Collegio editoriale", "=" * 60]
    for stage, label in (("produzione", "Produzione"), ("controllo", "Controllo")):
        lines.append(f"\n{label}")
        for agent in REGISTRY.values():
            if agent.stage != stage:
                continue
            lines.append(f"  {agent.name:<16} {agent.title}")
            lines.append(f"  {'':<16} {agent.description}")
    lines.append("\nLivelli di lavorazione (--qualita)")
    for name, level in QUALITY_LEVELS.items():
        lines.append(f"  {name:<16} {level['descrizione']}")
    return "\n".join(lines)

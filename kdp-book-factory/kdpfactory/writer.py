"""Generazione dei contenuti: scaletta, capitoli, revisioni di lunghezza."""

from __future__ import annotations

from . import planner, prompts
from .i18n import L
from .llm import LLMClient
from .mdlite import count_words, strip_title
from .models import BookProject, BookSpec, ChapterPlan, Outline


def generate_outline(spec: BookSpec, client: LLMClient, budget: planner.PageBudget) -> Outline:
    """Chiede al modello la scaletta e ci applica il budget di parole."""
    raw = client.complete_json(
        system=prompts.OUTLINE_SYSTEM,
        user=prompts.outline_prompt(spec, budget.chapters, budget.total_words),
        label="scaletta (json)",
        max_tokens=16000,
    )
    outline = Outline.from_dict(raw)

    # Il modello a volte consegna un numero di capitoli diverso: si rinumera e
    # si aggiungono introduzione e conclusione come sezioni a sé.
    body = [c for c in outline.chapters if c.role not in {"intro", "conclusion"}]
    for chapter in body:
        chapter.role = "chapter"

    sequence: list[ChapterPlan] = []
    if spec.include_intro:
        sequence.append(
            ChapterPlan(
                number=0,
                title=L(spec.language, "introduction"),
                summary="Perché questo libro, per chi è, cosa ottiene il lettore.",
                beats=["il problema concreto", "la promessa", "come è organizzato il percorso"],
                role="intro",
            )
        )
    sequence.extend(body)
    if spec.include_conclusion:
        sequence.append(
            ChapterPlan(
                number=0,
                title=L(spec.language, "conclusion"),
                summary="Chiusura del ragionamento e primi 30 giorni di applicazione.",
                beats=["il punto centrale del libro", "cosa fare adesso", "l'errore da evitare"],
                role="conclusion",
            )
        )
    for index, chapter in enumerate(sequence, start=1):
        chapter.number = index

    outline.chapters = sequence
    outline.target_words_total = budget.total_words
    planner.apply_budget_to_outline(sequence, planner.distribute_words(budget, spec))
    if not outline.title:
        outline.title = spec.title
    return outline


def _covered_topics(summaries: dict[int, str], up_to: int) -> list[str]:
    return [summaries[n] for n in sorted(summaries) if n < up_to and summaries[n]]


def write_chapters(
    project: BookProject,
    spec: BookSpec,
    outline: Outline,
    client: LLMClient,
    *,
    only: list[int] | None = None,
    overwrite: bool = False,
) -> dict[int, str]:
    """Scrive i capitoli mancanti (o quelli indicati) e li salva su disco."""
    project.ensure_dirs()
    state = project.load_state()
    summaries: dict[int, str] = {int(k): v for k, v in state.get("summaries", {}).items()}
    written: dict[int, str] = {}

    for index, chapter in enumerate(outline.chapters):
        if only and chapter.number not in only:
            continue
        path = project.chapter_path(chapter.number)
        if path.exists() and not overwrite and not only:
            written[chapter.number] = path.read_text(encoding="utf-8")
            continue

        next_title = (
            outline.chapters[index + 1].title if index + 1 < len(outline.chapters) else ""
        )
        text = client.complete(
            system=[prompts.author_rules(), prompts.book_bible(spec, outline)],
            user=prompts.chapter_prompt(
                spec,
                chapter,
                previous_summary=summaries.get(chapter.number - 1, ""),
                covered=_covered_topics(summaries, chapter.number),
                next_title=next_title,
            ),
            label=f"capitolo {chapter.number}/{len(outline.chapters)} · {chapter.title}",
        )
        text = _normalize_chapter(text, chapter)
        path.write_text(text, encoding="utf-8")
        written[chapter.number] = text

        summaries[chapter.number] = summarize(text, client)
        state["summaries"] = {str(k): v for k, v in summaries.items()}
        project.save_state(state)

    return written


def summarize(text: str, client: LLMClient) -> str:
    if client.config.dry_run:
        title, _ = strip_title(text)
        return f"(segnaposto) {title}"
    return client.complete(
        system=prompts.SUMMARY_SYSTEM,
        user=text[:12000],
        label="riassunto di continuità",
        max_tokens=400,
    )


def _normalize_chapter(text: str, chapter: ChapterPlan) -> str:
    """Garantisce che il capitolo inizi con il titolo della scaletta."""
    _, body = strip_title(text)
    return f"# {chapter.title}\n\n{body.strip()}\n"


def revise_length(
    project: BookProject,
    spec: BookSpec,
    outline: Outline,
    client: LLMClient,
    targets: dict[int, int],
    *,
    tolerance: float = 0.08,
) -> list[int]:
    """Riscrive i capitoli la cui lunghezza si discosta troppo dall'obiettivo.

    Restituisce i numeri dei capitoli effettivamente riscritti.
    """
    revised: list[int] = []
    for chapter in outline.chapters:
        target = targets.get(chapter.number)
        if not target:
            continue
        path = project.chapter_path(chapter.number)
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        current = count_words(text)
        if abs(current - target) <= target * tolerance:
            continue

        new_text = client.complete(
            system=[prompts.author_rules(), prompts.book_bible(spec, outline)],
            user=prompts.revise_prompt(chapter, current, target, text),
            label=f"revisione capitolo {chapter.number} ({current} → {target} parole)",
        )
        new_text = _normalize_chapter(new_text, chapter)
        if count_words(new_text) < 200:
            continue  # risposta sospetta: si tiene la versione precedente
        path.write_text(new_text, encoding="utf-8")
        chapter.target_words = target
        revised.append(chapter.number)
    return revised


def load_chapters(project: BookProject, outline: Outline) -> list[tuple[int, str, str]]:
    """Capitoli su disco nell'ordine della scaletta: (numero, titolo, markdown)."""
    chapters: list[tuple[int, str, str]] = []
    for chapter in outline.chapters:
        path = project.chapter_path(chapter.number)
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        title, body = strip_title(text)
        chapters.append((chapter.number, title or chapter.title, body))
    return chapters

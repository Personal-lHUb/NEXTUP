"""Dal numero di pagine desiderato al budget di parole per capitolo.

Il controllo del numero di pagine è il vincolo centrale del progetto
(60-240 pagine). Funziona in due tempi:

1. *stima a priori*: dalla geometria della pagina e dalle metriche reali del
   font si ricava quante parole entrano in una pagina;
2. *ricalibrazione a posteriori*: dopo la prima impaginazione si misura il
   rapporto reale parole/pagina e si ricalcola il budget.

Il secondo passaggio è quello che porta davvero il libro dentro l'intervallo:
`pipeline.build_until_in_range()` lo ripete finché il PDF non rientra.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field

from . import kdpspecs
from .models import BookSpec, ChapterPlan
from .typography import average_metrics

# Testo campione usato per misurare le metriche medie del font.
SAMPLE_TEXT = {
    "it": (
        "Ogni capitolo di questo libro affronta un problema concreto e propone "
        "una soluzione verificabile, con esempi tratti dall'esperienza quotidiana "
        "di chi lavora sul campo e deve ottenere risultati misurabili."
    ),
    "en": (
        "Every chapter of this book tackles a concrete problem and proposes a "
        "verifiable solution, with examples taken from the daily experience of "
        "people who work in the field and need measurable results."
    ),
}

# Perdita di riempimento dovuta a giustificazione, sillabazione mancata,
# righe finali di paragrafo, titoli di paragrafo, elenchi e spaziature.
LINE_FILL_FACTOR = 0.94
PAGE_FILL_FACTOR = 0.86

# Pagine non di testo corrente: occhiello, frontespizio, colophon, indice, ecc.
FRONT_MATTER_PAGES = 8
BACK_MATTER_PAGES = 4
# Pagine perse per ogni apertura di capitolo (titolo in alto + eventuale bianca).
CHAPTER_OPENING_COST = 1.4


@dataclass
class PageBudget:
    """Budget di parole derivato dal numero di pagine obiettivo."""

    target_pages: int
    words_per_page: float
    body_pages: float
    total_words: int
    chapters: int
    words_per_chapter: int
    front_matter_pages: int = FRONT_MATTER_PAGES
    back_matter_pages: int = BACK_MATTER_PAGES

    def to_dict(self) -> dict:
        return asdict(self)


def words_per_page(spec: BookSpec, pages_hint: int | None = None) -> float:
    """Stima quante parole di testo corrente entrano in una pagina piena."""
    pages = pages_hint or spec.target_pages
    geo = kdpspecs.page_geometry(spec.trim, pages)
    metrics = average_metrics(
        spec.body_font, spec.body_font_size, SAMPLE_TEXT.get(spec.language, SAMPLE_TEXT["it"])
    )
    chars_per_line = (geo.text_width / metrics.avg_char_width) * LINE_FILL_FACTOR
    lines_per_page = math.floor(geo.text_height / spec.leading)
    chars_per_page = chars_per_line * lines_per_page * PAGE_FILL_FACTOR
    return chars_per_page / metrics.avg_chars_per_word


def suggest_chapter_count(spec: BookSpec, total_words: int) -> int:
    """Numero di capitoli sensato per la lunghezza richiesta."""
    if spec.chapters:
        return max(1, spec.chapters)
    # Capitoli tra 1.800 e 3.200 parole: lunghezza che regge bene sia in
    # cartaceo sia in ebook senza diventare dispersiva.
    target_len = 2500 if spec.genre == "non-fiction" else 3000
    count = round(total_words / target_len)
    return max(5, min(24, count))


def build_budget(spec: BookSpec, words_per_page_override: float | None = None) -> PageBudget:
    """Calcola il budget di parole per raggiungere `spec.target_pages`."""
    wpp = words_per_page_override or words_per_page(spec)
    chapters_guess = spec.chapters or 0
    # Prima passata per stimare il numero di capitoli, poi affinamento.
    for _ in range(3):
        overhead = FRONT_MATTER_PAGES + BACK_MATTER_PAGES + CHAPTER_OPENING_COST * max(
            chapters_guess, 1
        )
        body_pages = max(1.0, spec.target_pages - overhead)
        total_words = int(body_pages * wpp)
        new_chapters = suggest_chapter_count(spec, total_words)
        if new_chapters == chapters_guess:
            break
        chapters_guess = new_chapters

    overhead = FRONT_MATTER_PAGES + BACK_MATTER_PAGES + CHAPTER_OPENING_COST * chapters_guess
    body_pages = max(1.0, spec.target_pages - overhead)
    total_words = int(body_pages * wpp)
    return PageBudget(
        target_pages=spec.target_pages,
        words_per_page=round(wpp, 1),
        body_pages=round(body_pages, 1),
        total_words=total_words,
        chapters=chapters_guess,
        words_per_chapter=int(total_words / max(chapters_guess, 1)),
    )


def distribute_words(budget: PageBudget, spec: BookSpec) -> list[int]:
    """Parole per ciascuna sezione, introduzione e conclusione comprese.

    Introduzione e conclusione pesano meno di un capitolo pieno.
    """
    weights: list[float] = []
    if spec.include_intro:
        weights.append(0.6)
    weights.extend([1.0] * budget.chapters)
    if spec.include_conclusion:
        weights.append(0.5)
    total_weight = sum(weights)
    return [int(budget.total_words * w / total_weight) for w in weights]


def apply_budget_to_outline(chapters: list[ChapterPlan], words: list[int]) -> None:
    """Scrive il budget di parole nella scaletta (in place)."""
    for chapter, target in zip(chapters, words, strict=False):
        chapter.target_words = target


@dataclass
class Recalibration:
    """Esito di una misurazione reale su PDF impaginato."""

    measured_pages: int
    measured_words: int
    measured_words_per_page: float
    target_pages: int
    new_total_words: int
    scale: float
    per_chapter: dict[int, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {**asdict(self), "per_chapter": {str(k): v for k, v in self.per_chapter.items()}}


def recalibrate(
    *,
    measured_pages: int,
    measured_words: int,
    spec: BookSpec,
    chapters: list[ChapterPlan],
    chapter_words: dict[int, int],
    max_step: float = 0.45,
) -> Recalibration:
    """Ricalcola il budget dopo aver misurato il PDF reale.

    `chapter_words` è il conteggio parole effettivo per capitolo.
    Il fattore di scala è limitato a ±`max_step` per evitare oscillazioni.
    """
    chapters_count = sum(1 for c in chapters if c.role == "chapter") or len(chapters)
    overhead = FRONT_MATTER_PAGES + BACK_MATTER_PAGES + CHAPTER_OPENING_COST * chapters_count
    measured_body_pages = max(1.0, measured_pages - overhead)
    wpp = measured_words / measured_body_pages

    target_body_pages = max(1.0, spec.target_pages - overhead)
    new_total = int(target_body_pages * wpp)

    current_total = sum(chapter_words.values()) or measured_words or 1
    scale = new_total / current_total
    scale = max(1 - max_step, min(1 + max_step, scale))

    per_chapter: dict[int, int] = {}
    for chapter in chapters:
        current = chapter_words.get(chapter.number, chapter.target_words or 0)
        per_chapter[chapter.number] = max(300, int(round(current * scale)))

    return Recalibration(
        measured_pages=measured_pages,
        measured_words=measured_words,
        measured_words_per_page=round(wpp, 1),
        target_pages=spec.target_pages,
        new_total_words=new_total,
        scale=round(scale, 4),
        per_chapter=per_chapter,
    )


def describe(budget: PageBudget, spec: BookSpec) -> str:
    """Riepilogo leggibile del piano."""
    geo = kdpspecs.page_geometry(spec.trim, spec.target_pages)
    spine = kdpspecs.spine_width_in(spec.target_pages, spec.paper)
    cover_w, cover_h = kdpspecs.cover_size_in(spec.trim, spec.target_pages, spec.paper)
    inch = kdpspecs.INCH
    page = f"{geo.page_width/inch:.2f}x{geo.page_height/inch:.2f}"
    text_area = f"{geo.text_width/inch:.2f}x{geo.text_height/inch:.2f}"
    margins = f"interno {geo.inner_margin/inch:.3f} / esterno {geo.outer_margin/inch:.3f}"
    limits = f"{kdpspecs.PROJECT_MIN_PAGES}-{kdpspecs.PROJECT_MAX_PAGES}"
    lines = [
        f"Titolo              : {spec.title}",
        f"Formato             : {spec.trim} in ({page}), carta {spec.paper}",
        f"Gabbia di testo     : {text_area} in",
        f"Margini             : {margins} in",
        f"Corpo               : {spec.body_font} {spec.body_font_size}pt / interlinea {spec.leading}pt",
        f"Pagine obiettivo    : {budget.target_pages} (intervallo di progetto {limits})",
        f"Parole per pagina   : ~{budget.words_per_page}",
        f"Parole totali       : ~{budget.total_words:,}".replace(",", "."),
        f"Capitoli            : {budget.chapters} (~{budget.words_per_chapter} parole ciascuno)",
        f"Dorso               : {spine:.3f} in (testo sul dorso: "
        f"{'sì' if kdpspecs.spine_text_allowed(spec.target_pages) else 'no, servono 79+ pagine'})",
        f"Copertina           : {cover_w:.3f}x{cover_h:.3f} in (abbondanza inclusa)",
    ]
    return "\n".join(lines)

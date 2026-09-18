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

# Lunghezza di un capitolo: è il metro con cui si generano i libri. Sotto le
# 1.500 parole il capitolo non ripaga la sua apertura, che costa 1,4 pagine;
# sopra le 2.000 il lettore non lo chiude in una seduta e lo lascia a metà.
MIN_WORDS_PER_CHAPTER = 1500
MAX_WORDS_PER_CHAPTER = 2000
TARGET_WORDS_PER_CHAPTER = 1750

# Introduzione e conclusione prendono una quota ridotta rispetto a un capitolo
# pieno: entrano nel conto perché è su di loro che si ripartiscono le parole.
INTRO_WEIGHT = 0.6
CONCLUSION_WEIGHT = 0.5

# Estremi del numero di capitoli: sono i due soli motivi per cui l'intervallo
# di parole può non essere rispettato. Il tetto serve ai libri lunghi e fitti
# (240 pagine di testo denso non stanno in 30 capitoli senza sforare le 2.000
# parole); il pavimento ai libri corti e radi, dove cinque capitoli sarebbero
# troppi e ne uscirebbero da meno di 1.500.
MIN_CHAPTERS = 4
MAX_CHAPTERS = 40


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


def section_weights(spec: BookSpec, chapters: int) -> float:
    """Peso complessivo delle sezioni fra cui si dividono le parole."""
    total = float(chapters)
    if spec.include_intro:
        total += INTRO_WEIGHT
    if spec.include_conclusion:
        total += CONCLUSION_WEIGHT
    return max(total, 1.0)


def words_in_chapter(spec: BookSpec, total_words: int, chapters: int) -> float:
    """Parole che toccano davvero a un capitolo pieno, dato il numero di capitoli."""
    return total_words / section_weights(spec, chapters)


def suggest_chapter_count(spec: BookSpec, total_words: int) -> int:
    """Quanti capitoli servono per tenerli tutti nell'intervallo di progetto.

    È il numero di capitoli ad adattarsi alla lunghezza voluta, non il
    contrario: la lunghezza del capitolo è il metro, e non si sfora.
    """
    if spec.chapters:
        # Scelta esplicita dell'autore: vince sull'intervallo. `describe` avvisa
        # quando il capitolo che ne esce sta fuori.
        return max(1, spec.chapters)
    count = max(MIN_CHAPTERS, min(MAX_CHAPTERS, round(total_words / TARGET_WORDS_PER_CHAPTER)))
    # L'arrotondamento può cadere fuori intervallo: si aggiusta di un capitolo
    # alla volta, sul peso e non sul conteggio, perché introduzione e
    # conclusione prendono una quota ridotta (vedi `distribute_words`).
    while count < MAX_CHAPTERS and words_in_chapter(spec, total_words, count) > MAX_WORDS_PER_CHAPTER:
        count += 1
    while count > MIN_CHAPTERS and words_in_chapter(spec, total_words, count) < MIN_WORDS_PER_CHAPTER:
        count -= 1
    return count


def _budget_for(spec: BookSpec, wpp: float, chapters: int) -> tuple[float, int, float]:
    """Pagine di testo, parole totali e parole per capitolo, dato il numero di capitoli."""
    overhead = FRONT_MATTER_PAGES + BACK_MATTER_PAGES + CHAPTER_OPENING_COST * max(chapters, 1)
    body_pages = max(1.0, spec.target_pages - overhead)
    total_words = int(body_pages * wpp)
    return body_pages, total_words, words_in_chapter(spec, total_words, chapters)


def build_budget(spec: BookSpec, words_per_page_override: float | None = None) -> PageBudget:
    """Calcola il budget di parole per raggiungere `spec.target_pages`."""
    wpp = words_per_page_override or words_per_page(spec)
    if spec.chapters:
        chapters_guess = max(1, spec.chapters)
    else:
        # Si prova ogni numero di capitoli ammesso invece di affinare a tentativi:
        # il conto non converge da solo, perché ogni capitolo in più costa 1,4
        # pagine di apertura e quindi cambia le parole da ripartire. Su libri
        # corti l'affinamento oscillava e chiudeva fuori intervallo.
        candidates = list(range(MIN_CHAPTERS, MAX_CHAPTERS + 1))
        in_range = [
            c
            for c in candidates
            if MIN_WORDS_PER_CHAPTER <= _budget_for(spec, wpp, c)[2] <= MAX_WORDS_PER_CHAPTER
        ]
        chapters_guess = min(
            in_range or candidates,
            key=lambda c: abs(_budget_for(spec, wpp, c)[2] - TARGET_WORDS_PER_CHAPTER),
        )

    body_pages, total_words, _ = _budget_for(spec, wpp, chapters_guess)
    return PageBudget(
        target_pages=spec.target_pages,
        words_per_page=round(wpp, 1),
        body_pages=round(body_pages, 1),
        total_words=total_words,
        chapters=chapters_guess,
        # Le parole di un capitolo pieno, non la media fra tutte le sezioni:
        # introduzione e conclusione ne prendono meno e falserebbero il numero.
        words_per_chapter=int(words_in_chapter(spec, total_words, chapters_guess)),
    )


def distribute_words(budget: PageBudget, spec: BookSpec) -> list[int]:
    """Parole per ciascuna sezione, introduzione e conclusione comprese.

    Introduzione e conclusione pesano meno di un capitolo pieno.
    """
    weights: list[float] = []
    if spec.include_intro:
        weights.append(INTRO_WEIGHT)
    weights.extend([1.0] * budget.chapters)
    if spec.include_conclusion:
        weights.append(CONCLUSION_WEIGHT)
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
        f"Capitoli            : {budget.chapters} (~{budget.words_per_chapter} parole ciascuno, "
        f"intervallo {MIN_WORDS_PER_CHAPTER}-{MAX_WORDS_PER_CHAPTER})"
        + (
            ""
            if MIN_WORDS_PER_CHAPTER <= budget.words_per_chapter <= MAX_WORDS_PER_CHAPTER
            else "  ← fuori intervallo: è il numero di capitoli scelto a mano in `chapters`"
        ),
        f"Dorso               : {spine:.3f} in (testo sul dorso: "
        f"{'sì' if kdpspecs.spine_text_allowed(spec.target_pages) else 'no, servono 79+ pagine'})",
        f"Copertina           : {cover_w:.3f}x{cover_h:.3f} in (abbondanza inclusa)",
    ]
    return "\n".join(lines)

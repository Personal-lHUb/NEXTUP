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
from pathlib import Path

from . import kdpspecs
from .i18n import L
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


# --------------------------------------------------------------------------
# Taratura: due impaginazioni di prova invece di una riscrittura pagata
# --------------------------------------------------------------------------
# Il numero di pagine non è una funzione continua delle parole: **è una
# scalinata**. Ogni sezione si apre su pagina dispari, quindi occupa un numero
# pari di pagine, e un libro da venti sezioni si muove a scatti di due pagine
# per sezione — fino a quaranta pagine in un colpo. Fra un gradino e l'altro
# c'è una pedata piatta: mille parole in più e il PDF ha lo stesso identico
# numero di pagine.
#
# È questa la ragione vera per cui i libri non centravano l'obiettivo, e per
# cui `build_until_in_range` oscillava: si correggevano le parole cercando una
# continuità che non c'è. Qui si misura la scalinata — quante parole stanno in
# una pagina di testo, quanto costa un'apertura, quante pagine fisse ci sono —
# e poi si sceglie il budget che cade sul gradino giusto.
#
#: di quanto si allunga e si accorcia il libro di prova rispetto alla stima
CALIBRATION_FACTORS = (0.85, 1.30)
#: ogni quante parole il testo di prova apre una sezione `##`, come i capitoli veri
CALIBRATION_SECTION_WORDS = 450
#: entro quanto si cerca il budget migliore, in frazione della stima analitica
CALIBRATION_SEARCH = (0.6, 2.0)
CALIBRATION_STEPS = 280

#: ruolo di una sezione → chiave della sua etichetta in `i18n`
ROLE_LABELS = {"intro": "introduction", "conclusion": "conclusion", "chapter": "chapter"}


def _even(value: float) -> int:
    """Pagine occupate davvero: ogni sezione si apre su dispari e chiude su pari."""
    return 2 * math.ceil(value / 2)


def role_label(role: str) -> str:
    return ROLE_LABELS.get(role, "chapter")


def role_at(spec: BookSpec, index: int, total: int) -> str:
    """Il ruolo della sezione in posizione `index`, come lo compone la pipeline."""
    if spec.include_intro and index == 0:
        return "intro"
    if spec.include_conclusion and index == total - 1:
        return "conclusion"
    return "chapter"


@dataclass(frozen=True)
class PageModel:
    """Come le parole diventano pagine, misurato su questo formato.

    Tre numeri e una scalinata: `words_per_body_page` è quanto testo sta in una
    pagina piena, `opening_pages` quanto costa aprire una sezione (titolo in
    alto, colonna che parte a metà), `fixed_pages` le pagine che non dipendono
    da quanto si scrive — antiporta, frontespizio, colofone, indice, coda.
    """

    words_per_body_page: float
    opening_pages: float
    fixed_pages: float

    def pages_for(self, sections: list[int]) -> int:
        """Le pagine che farebbe un libro con queste sezioni."""
        corpo = sum(
            _even(self.opening_pages + parole / self.words_per_body_page) for parole in sections
        )
        return int(round(self.fixed_pages + corpo))

    def to_dict(self) -> dict:
        return {
            "parole_per_pagina_piena": round(self.words_per_body_page, 1),
            "pagine_di_apertura": round(self.opening_pages, 2),
            "pagine_fisse": round(self.fixed_pages, 1),
        }


def sample_chapter(spec: BookSpec, words: int) -> str:
    """Un capitolo finto lungo `words` parole, fatto come quelli veri.

    La struttura conta quanto la lunghezza: capoversi che finiscono a metà
    riga, sottotitoli che spezzano la colonna e che finiscono anche nell'indice.
    Un unico blocco di testo continuo starebbe in meno pagine, e taraterebbe il
    sistema su un libro che nessuno scriverà.
    """
    frase = SAMPLE_TEXT.get(spec.language, SAMPLE_TEXT["it"])
    per_frase = max(1, len(frase.split()))
    pezzi: list[str] = []
    scritte = 0
    capoverso = 0
    sezione = 0
    while scritte < words:
        if scritte >= (sezione + 1) * CALIBRATION_SECTION_WORDS:
            sezione += 1
            pezzi.append(f"## {L(spec.language, 'chapter')} {sezione}")
        ripetizioni = 3 if capoverso % 3 else 2      # capoversi di lunghezza diversa
        pezzi.append(" ".join([frase] * ripetizioni))
        scritte += per_frase * ripetizioni
        capoverso += 1
    return "\n\n".join(pezzi)


def _sections_of(spec: BookSpec, words: list[int]) -> tuple[list, list]:
    """Piani e testi di un libro di prova con la struttura di quello vero."""
    from .models import ChapterPlan as Plan

    piani, capitoli = [], []
    for indice, parole in enumerate(words):
        numero = indice + 1
        ruolo = role_at(spec, indice, len(words))
        titolo = f"{L(spec.language, role_label(ruolo))} {numero}"
        piani.append(Plan(number=numero, title=titolo, target_words=parole, role=ruolo))
        capitoli.append((numero, titolo, f"# {titolo}\n\n{sample_chapter(spec, parole)}\n"))
    return piani, capitoli


def _fit_model(osservazioni: list[tuple[int, int]], fixed_pages: float) -> PageModel:
    """Densità e costo d'apertura che riproducono le pagine misurate.

    Le pagine per sezione sono quantizzate, quindi non c'è una retta da
    interpolare: si cerca la coppia che sbaglia meno *dopo* la quantizzazione.
    Fra tutte quelle che sbagliano uguale si prende la mediana, perché la
    soluzione non è unica — la scalinata ammette un intervallo — e il centro di
    quell'intervallo è l'unico punto che regge anche fuori dai dati provati.
    """
    migliori: list[tuple[float, float]] = []
    errore_minimo = None
    for densita_int in range(180, 701):
        densita = float(densita_int)
        for apertura_int in range(5, 61):
            apertura = apertura_int / 10
            errore = sum(
                (_even(apertura + parole / densita) - pagine) ** 2
                for parole, pagine in osservazioni
            )
            if errore_minimo is None or errore < errore_minimo:
                errore_minimo, migliori = errore, [(densita, apertura)]
            elif errore == errore_minimo:
                migliori.append((densita, apertura))
    densita = sorted(d for d, _ in migliori)[len(migliori) // 2]
    apertura = sorted(a for _, a in migliori)[len(migliori) // 2]
    return PageModel(
        words_per_body_page=densita, opening_pages=apertura, fixed_pages=fixed_pages
    )


def measure_page_model(spec: BookSpec, workdir: Path | None = None) -> PageModel:
    """Misura la scalinata impaginando due libri di prova. Zero chiamate API."""
    import tempfile

    from . import typeset as typeset_module
    from .models import Outline

    base = build_budget(spec, words_per_page(spec))
    parti = distribute_words(base, spec)

    osservazioni: list[tuple[int, int]] = []
    fisse: list[int] = []
    with tempfile.TemporaryDirectory() as tmp:
        cartella = Path(workdir) if workdir else Path(tmp)
        for fattore in CALIBRATION_FACTORS:
            piani, capitoli = _sections_of(spec, [max(200, int(w * fattore)) for w in parti])
            esito = typeset_module.typeset(
                spec,
                Outline(title=spec.title, subtitle=spec.subtitle, chapters=piani),
                capitoli,
                cartella / f"taratura-{fattore}.pdf",
            )
            # `chapter_pages` dà la pagina d'inizio di ogni sezione, coda
            # compresa: la differenza fra due inizi è quanto occupa la sezione.
            inizi = list(esito.chapter_pages.values())
            parole = list(esito.words_by_chapter.values())
            if len(inizi) < len(parole) + 1:
                continue
            osservazioni += [(w, inizi[i + 1] - inizi[i]) for i, w in enumerate(parole)]
            fisse.append((inizi[0] - 1) + (esito.pages - inizi[-1] + 1))

    if not osservazioni:
        # Senza misure si resta sulla stima analitica: meglio un numero
        # dichiaratamente approssimato che uno inventato.
        return PageModel(words_per_page(spec), CHAPTER_OPENING_COST, FRONT_MATTER_PAGES + BACK_MATTER_PAGES)
    return _fit_model(osservazioni, sum(fisse) / len(fisse))


def predict_pages(spec: BookSpec, wpp: float, model: PageModel) -> int:
    """Quante pagine farebbe il libro con questo budget."""
    return model.pages_for(distribute_words(build_budget(spec, wpp), spec))


def calibrate_words_per_page(spec: BookSpec, model: PageModel | None = None) -> float:
    """Le parole per pagina che fanno cadere il libro sull'obiettivo.

    `words_per_page()` stima la densità dalle metriche del font e sbaglia
    sistematicamente per difetto: il primo PDF esce intorno al 10% sotto
    l'obiettivo, cioè fuori dalla finestra di accettazione, e il libro si
    ricompra intero per rientrare — nei conti misurati, il 37% del costo di
    produzione.

    Qui non si stima: si misura la scalinata (`measure_page_model`) e poi si
    prova ogni budget ammissibile, scegliendo quello che ci cade più vicino.
    Non è una divisione, è una ricerca, perché fra due gradini non c'è niente:
    il numero di capitoli e la lunghezza del capitolo vanno scelti insieme.

    Il limite, dichiarato: la prosa del modello ha una densità sua, e questa
    taratura la conosce solo di riflesso — il testo di prova imita la struttura
    dei capitoli veri, non il loro modo di scrivere. Serve a partire vicini. La
    misura che conta resta quella del primo PDF vero, che
    `pipeline.build_until_in_range()` usa per ricalibrare e che da quel momento
    vince su questa (`words_per_page_measured` in `state.json`).
    """
    model = model or measure_page_model(spec)
    stimate = words_per_page(spec)
    minimo, massimo = (stimate * f for f in CALIBRATION_SEARCH)
    passo = (massimo - minimo) / CALIBRATION_STEPS

    migliore, scarto_migliore = stimate, None
    for indice in range(CALIBRATION_STEPS + 1):
        candidato = minimo + indice * passo
        scarto = abs(predict_pages(spec, candidato, model) - spec.target_pages)
        if scarto_migliore is None or scarto < scarto_migliore:
            migliore, scarto_migliore = candidato, scarto
            if scarto == 0:
                break
    return migliore


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

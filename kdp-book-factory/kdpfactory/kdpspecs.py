"""Specifiche tecniche Amazon KDP per libri cartacei (paperback).

Tutti i valori sono espressi in pollici, come nella documentazione KDP.
I valori sono quelli pubblicati da Amazon per il paperback; Amazon può
aggiornarli: `docs/checklist-kdp.md` indica le pagine da riverificare prima
di ogni pubblicazione.
"""

from __future__ import annotations

from dataclasses import dataclass

INCH = 72.0  # punti PostScript per pollice

# Vincoli di progetto richiesti: ogni libro deve stare in questo intervallo.
PROJECT_MIN_PAGES = 60
PROJECT_MAX_PAGES = 240

# Formati di rifilo (trim size) disponibili su KDP, in pollici (larghezza, altezza).
TRIM_SIZES: dict[str, tuple[float, float]] = {
    "5x8": (5.0, 8.0),
    "5.06x7.81": (5.06, 7.81),
    "5.25x8": (5.25, 8.0),
    "5.5x8.5": (5.5, 8.5),
    "6x9": (6.0, 9.0),
    "6.14x9.21": (6.14, 9.21),
    "6.69x9.61": (6.69, 9.61),
    "7x10": (7.0, 10.0),
    "7.44x9.69": (7.44, 9.69),
    "7.5x9.25": (7.5, 9.25),
    "8x10": (8.0, 10.0),
    "8.5x8.5": (8.5, 8.5),
    "8.5x11": (8.5, 11.0),
    "8.27x11.69": (8.27, 11.69),  # A4
}

# Moltiplicatore per pagina usato da KDP per calcolare lo spessore del dorso.
PAPER_SPINE_FACTOR: dict[str, float] = {
    "white": 0.002252,
    "cream": 0.0025,
    "color-standard": 0.002252,
    "color-premium": 0.002347,
}

# Numero di pagine ammesso per tipo di carta/stampa.
PAPER_PAGE_LIMITS: dict[str, tuple[int, int]] = {
    "white": (24, 828),
    "cream": (24, 828),
    "color-standard": (72, 600),
    "color-premium": (24, 600),
}

# Margine interno (gutter) minimo richiesto, in funzione del numero di pagine.
GUTTER_TABLE: tuple[tuple[int, int, float], ...] = (
    (24, 150, 0.375),
    (151, 300, 0.5),
    (301, 500, 0.625),
    (501, 700, 0.75),
    (701, 828, 0.875),
)

BLEED_IN = 0.125          # abbondanza su tre lati (copertina e interni al vivo)
COVER_BLEED_TOTAL = 0.25  # 0.125" sopra + 0.125" sotto
MIN_OUTSIDE_MARGIN_NO_BLEED = 0.25
MIN_OUTSIDE_MARGIN_BLEED = 0.375
SPINE_TEXT_MIN_PAGES = 79  # sotto questa soglia KDP non consente testo sul dorso
BARCODE_ZONE_IN = (2.0, 1.2)  # area da lasciare libera in basso a destra della quarta


def gutter_margin_in(pages: int) -> float:
    """Margine interno minimo richiesto da KDP per un dato numero di pagine."""
    for low, high, margin in GUTTER_TABLE:
        if low <= pages <= high:
            return margin
    if pages < GUTTER_TABLE[0][0]:
        return GUTTER_TABLE[0][2]
    return GUTTER_TABLE[-1][2]


def outside_margin_in(bleed: bool = False) -> float:
    """Margine esterno minimo (testa, piede, taglio esterno)."""
    return MIN_OUTSIDE_MARGIN_BLEED if bleed else MIN_OUTSIDE_MARGIN_NO_BLEED


def spine_width_in(pages: int, paper: str = "cream") -> float:
    """Spessore del dorso in pollici."""
    try:
        factor = PAPER_SPINE_FACTOR[paper]
    except KeyError as exc:  # pragma: no cover - difensivo
        raise ValueError(f"Tipo di carta sconosciuto: {paper!r}") from exc
    return pages * factor


def trim_size_in(trim: str) -> tuple[float, float]:
    try:
        return TRIM_SIZES[trim]
    except KeyError as exc:
        raise ValueError(
            f"Trim size {trim!r} non valido. Disponibili: {', '.join(TRIM_SIZES)}"
        ) from exc


def cover_size_in(trim: str, pages: int, paper: str = "cream") -> tuple[float, float]:
    """Dimensioni totali del PDF di copertina (fronte + dorso + retro + abbondanza)."""
    w, h = trim_size_in(trim)
    spine = spine_width_in(pages, paper)
    return (2 * w + spine + COVER_BLEED_TOTAL, h + COVER_BLEED_TOTAL)


def spine_text_allowed(pages: int) -> bool:
    return pages >= SPINE_TEXT_MIN_PAGES


@dataclass(frozen=True)
class PageGeometry:
    """Geometria della gabbia di testo di una pagina interna, in punti."""

    page_width: float
    page_height: float
    inner_margin: float
    outer_margin: float
    top_margin: float
    bottom_margin: float

    @property
    def text_width(self) -> float:
        return self.page_width - self.inner_margin - self.outer_margin

    @property
    def text_height(self) -> float:
        return self.page_height - self.top_margin - self.bottom_margin


def page_geometry(
    trim: str,
    pages: int,
    *,
    top_margin_in: float = 0.75,
    bottom_margin_in: float = 0.75,
    outer_margin_in: float | None = None,
    extra_gutter_in: float = 0.125,
) -> PageGeometry:
    """Geometria conforme a KDP, con un margine di sicurezza sopra il minimo.

    `extra_gutter_in` aggiunge spazio oltre al minimo obbligatorio: KDP accetta
    il minimo, ma un libro rilegato in brossura si legge male se il testo
    finisce dentro la piega.
    """
    w, h = trim_size_in(trim)
    inner = gutter_margin_in(pages) + extra_gutter_in
    outer = outer_margin_in if outer_margin_in is not None else max(0.5, MIN_OUTSIDE_MARGIN_NO_BLEED)
    return PageGeometry(
        page_width=w * INCH,
        page_height=h * INCH,
        inner_margin=inner * INCH,
        outer_margin=outer * INCH,
        top_margin=top_margin_in * INCH,
        bottom_margin=bottom_margin_in * INCH,
    )


def validate_page_count(pages: int, paper: str = "cream") -> list[str]:
    """Errori bloccanti sul numero di pagine (limiti KDP + limiti di progetto)."""
    problems: list[str] = []
    low, high = PAPER_PAGE_LIMITS.get(paper, (24, 828))
    if pages < low:
        problems.append(
            f"{pages} pagine: sotto il minimo KDP di {low} per carta '{paper}'."
        )
    if pages > high:
        problems.append(
            f"{pages} pagine: sopra il massimo KDP di {high} per carta '{paper}'."
        )
    if pages < PROJECT_MIN_PAGES:
        problems.append(
            f"{pages} pagine: sotto il minimo di progetto ({PROJECT_MIN_PAGES})."
        )
    if pages > PROJECT_MAX_PAGES:
        problems.append(
            f"{pages} pagine: sopra il massimo di progetto ({PROJECT_MAX_PAGES})."
        )
    return problems

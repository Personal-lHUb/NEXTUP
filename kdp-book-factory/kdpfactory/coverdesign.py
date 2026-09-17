"""Sistema di copertine: le regole che decidono il clic, e come misurarle.

Su Amazon la copertina non viene mai vista come la vedi tu adesso. Viene vista
larga **160 pixel**, in mezzo ad altre venti, per meno di un secondo, su fondo
bianco. Tutto quello che non sopravvive a quella miniatura non esiste.

Da qui le sette regole che questo modulo applica e verifica:

1. **Un solo elemento dominante.** L'occhio ne mette a fuoco uno: se il titolo
   compete con un'immagine e con tre righe di sottotitolo, non vince nessuno.
2. **Titolo leggibile in miniatura.** Altezza delle maiuscole almeno il 6%
   dell'altezza della copertina — sotto quella soglia, a 160 px, il titolo è
   una macchia grigia. `audit()` la misura sul PDF vero.
3. **Contrasto reale.** Rapporto di contrasto fra titolo e fondo ≥ 7:1
   (la soglia AAA delle linee guida di accessibilità). Si calcola, non si valuta
   a occhio.
4. **Stacco dalla pagina.** La pagina dei risultati è bianca: un fondo scuro o
   molto saturo crea un bordo percettivo, un fondo chiaro si fonde e sparisce.
5. **Codice di genere in mezzo secondo.** Chi cerca enigmi cerca una griglia,
   chi cerca un metodo cerca una promessa. Il segno grafico dice *che libro è*
   prima che il titolo venga letto: si differenzia dentro il codice, non fuori.
6. **Un ciclo aperto.** Una domanda o una promessa incompleta genera la tensione
   che fa cliccare (è l'effetto Zeigarnik: l'incompiuto resta in testa).
7. **Numeri in cifre.** "13 CASES · 908 SUSPECTS" si legge in un colpo d'occhio;
   "tredici casi" va letto.

Una cosa che questo modulo non fa, e non farà: finti timbri di bestseller,
stelline, recensioni o premi inventati. Oltre a essere vietati da KDP, sono
promesse che il libro non mantiene — e il reso arriva comunque.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics

from . import kdpspecs

INCH = kdpspecs.INCH

#: soglie del sistema, usate sia per disegnare sia per verificare
MIN_TITLE_CAP_RATIO = 0.06      # altezza maiuscole / altezza copertina
GOOD_TITLE_CAP_RATIO = 0.085
MIN_CONTRAST = 7.0              # titolo contro fondo
THUMBNAIL_WIDTH_PX = 160        # com'è vista davvero nei risultati di ricerca
MAX_TOP_ELEMENTS = 4            # blocchi di testo nella metà alta della prima
MAX_TITLE_LINES = 3             # oltre, il titolo non è un'insegna ma un paragrafo
SAFE_MARGIN_IN = 0.25           # margine di sicurezza KDP dal taglio

#: spaziatura fra i caratteri, in frazione del corpo, per i testi in maiuscolo
KICKER_TRACKING = 0.28
STATS_TRACKING = 0.08
AUTHOR_TRACKING = 0.12
BADGE_TRACKING = 0.20


# --------------------------------------------------------------------------
# Colore
# --------------------------------------------------------------------------
def _channel(value: float) -> float:
    value /= 255.0
    return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4


def luminance(hex_color: str) -> float:
    """Luminanza relativa secondo WCAG."""
    raw = hex_color.lstrip("#")
    red, green, blue = (int(raw[i : i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _channel(red) + 0.7152 * _channel(green) + 0.0722 * _channel(blue)


def contrast_ratio(first: str, second: str) -> float:
    light, dark = sorted((luminance(first), luminance(second)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


@dataclass(frozen=True)
class Palette:
    """Fondo, accento e inchiostro di una copertina.

    `pops_on_white` dice se il fondo stacca dalla pagina dei risultati: una
    copertina chiara su fondo bianco perde il bordo e con esso metà dei clic.
    """

    name: str
    background: str
    deep: str          # banda/blocco più scuro o più chiaro del fondo
    title: str
    accent: str        # un solo colore d'accento, usato con parsimonia
    muted: str
    genres: tuple[str, ...] = ()

    @property
    def pops_on_white(self) -> bool:
        return contrast_ratio(self.background, "#FFFFFF") >= 3.0

    @property
    def title_contrast(self) -> float:
        return contrast_ratio(self.title, self.background)


PALETTES: tuple[Palette, ...] = (
    # Giallo su nero: la combinazione con più stacco che esista su fondo bianco.
    Palette("notturno", "#0E1320", "#161E31", "#FFFFFF", "#F5B301", "#A9B6CC",
            genres=("enigmi", "fiction", "non-fiction")),
    Palette("allarme", "#141414", "#1F1F1F", "#FFFFFF", "#FF3B30", "#C9C9C9",
            genres=("enigmi", "fiction")),
    Palette("inchiostro", "#10243A", "#0B1A2B", "#FFFFFF", "#2ED3B7", "#AFC4D6",
            genres=("non-fiction", "enigmi")),
    Palette("bosco", "#12291E", "#0D1F16", "#F6F3E7", "#9BE564", "#BFD3C1",
            genres=("non-fiction",)),
    Palette("terracotta", "#2B1410", "#1E0E0B", "#FFF3E8", "#FF7A45", "#E0C5B4",
            genres=("fiction", "non-fiction")),
    Palette("indaco", "#1A1340", "#120D2E", "#FFFFFF", "#8B7BFF", "#CFC9EC",
            genres=("fiction", "enigmi")),
)


def pick_palette(spec, genre: str) -> Palette:
    """Palette scelta dall'autore, o la migliore per il genere, in modo stabile."""
    wanted = getattr(spec, "cover_theme", "auto")
    for palette in PALETTES:
        if palette.name == wanted:
            return palette
    candidates = [p for p in PALETTES if genre in p.genres] or list(PALETTES)
    digest = hashlib.sha256(spec.title.encode("utf-8")).digest()
    return candidates[digest[0] % len(candidates)]


# --------------------------------------------------------------------------
# Che cosa va scritto sopra
# --------------------------------------------------------------------------
@dataclass
class CoverCopy:
    """I testi della prima di copertina, in ordine di importanza percettiva."""

    title: str
    kicker: str = ""        # riga piccola in alto: dice il genere in due parole
    hook: str = ""          # il ciclo aperto: una domanda o una promessa
    stats: str = ""         # numeri in cifre, separati da ·
    badge: str = ""         # una garanzia vera, breve
    author: str = ""

    def elements(self) -> int:
        return sum(1 for value in (self.kicker, self.title, self.hook, self.stats) if value)


GENRE_DEFAULTS = {
    "enigmi": {"kicker": "DEDUCTION PUZZLES", "motif": "grid"},
    "non-fiction": {"kicker": "", "motif": "rules"},
    "fiction": {"kicker": "", "motif": "none"},
}


def derive_copy(spec, metadata: dict | None = None, genre: str = "non-fiction") -> CoverCopy:
    """Ricava i testi di copertina dai dati che il libro ha già.

    Il sottotitolo completo non finisce in copertina: in miniatura non si legge
    e ruba spazio al titolo. Si usa la sua prima proposizione come gancio.
    """
    metadata = metadata or {}
    hook = metadata.get("cover_hook") or _first_clause(spec.subtitle)
    return CoverCopy(
        title=spec.title,
        kicker=metadata.get("cover_kicker", GENRE_DEFAULTS.get(genre, {}).get("kicker", "")),
        hook=hook,
        stats=metadata.get("cover_stats", ""),
        badge=metadata.get("cover_badge", ""),
        author=spec.author,
    )


def _first_clause(text: str, limit: int = 62) -> str:
    """La prima proposizione di un sottotitolo lungo: il resto è per la scheda."""
    if not text:
        return ""
    for separator in (": ", " — ", " – ", ". "):
        if separator in text:
            head, _, tail = text.partition(separator)
            candidate = tail if len(head) < 18 else head
            if len(candidate) <= limit:
                return candidate.strip(" .")
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "…"


# --------------------------------------------------------------------------
# Disegno
# --------------------------------------------------------------------------
@dataclass
class FrontBox:
    """L'area della prima di copertina, abbondanza compresa."""

    x0: float
    y0: float
    width: float
    height: float
    trim_width: float
    trim_height: float
    bleed: float
    safe: float

    @property
    def center(self) -> float:
        # L'abbondanza della prima sta sul taglio esterno (a destra), non a
        # sinistra: il centro ottico è quello dell'area rifilata.
        return self.x0 + self.trim_width / 2

    @property
    def measure(self) -> float:
        return self.trim_width - 2.4 * self.safe


@dataclass
class DrawResult:
    title_size: float
    title_lines: list[str] = field(default_factory=list)
    cap_ratio: float = 0.0
    contrast: float = 0.0


def tracked_width(text: str, font: str, size: float, tracking: float = 0.0) -> float:
    """Larghezza reale, spaziatura fra i caratteri compresa.

    `pdfmetrics.stringWidth` non conosce il tracking: usarla da sola per
    centrare o per far stare un testo nella misura porta fuori squadro.
    """
    return pdfmetrics.stringWidth(text, font, size) + tracking * max(len(text) - 1, 0)


def fit_size(
    text: str,
    font: str,
    max_width: float,
    start: float,
    minimum: float,
    tracking_ratio: float = 0.0,
) -> float:
    """Il corpo più grande che sta nella misura, tracking incluso.

    Il minimo è un pavimento vero: scendendo a passi di mezzo punto lo si
    supererebbe di poco, e quel poco è esattamente ciò che rende un titolo
    illeggibile in miniatura.
    """
    size = start
    while size > minimum and tracked_width(text, font, size, size * tracking_ratio) > max_width:
        size = max(minimum, size - 0.5)
    return size


def wrap(text: str, font: str, size: float, max_width: float) -> list[str]:
    lines: list[str] = []
    current: list[str] = []
    for word in text.split():
        trial = " ".join([*current, word])
        if pdfmetrics.stringWidth(trial, font, size) <= max_width or not current:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def _tracked(canvas, x: float, y: float, text: str, font: str, size: float, tracking: float):
    """Testo centrato in `x` con spaziatura fra i caratteri.

    La spaziatura (`Tc`) fa parte dello stato grafico del PDF, non del singolo
    blocco di testo: se non la si riazzera resta attiva per tutto il resto
    della pagina e allarga ogni riga disegnata dopo — titolo compreso, che
    finisce fuori squadro perché ReportLab lo centra senza saperlo.
    """
    obj = canvas.beginText(x - tracked_width(text, font, size, tracking) / 2, y)
    obj.setFont(font, size)
    obj.setCharSpace(tracking)
    obj.textOut(text)
    obj.setCharSpace(0)
    canvas.drawText(obj)


def title_block_size(copy: CoverCopy, display: str, box: FrontBox) -> tuple[float, list[str]]:
    """Il titolo occupa quanto può: è l'unico elemento che deve vincere.

    Si parte dal 13% dell'altezza e si scende solo se le righe non ci stanno —
    mai sotto la soglia di leggibilità in miniatura.
    """
    longest = max(copy.title.split(), key=len, default="A").upper()
    ceiling = box.trim_height * 0.13
    floor = box.trim_height * MIN_TITLE_CAP_RATIO / 0.72
    size = min(ceiling, fit_size(longest, display, box.measure, ceiling, floor))
    lines = wrap(copy.title.upper(), display, size, box.measure)
    while len(lines) > MAX_TITLE_LINES and size > floor:
        # Mai sotto la soglia di leggibilità: un titolo di quattro righe si
        # legge ancora, un titolo illeggibile in miniatura no. Se non ci sta
        # nemmeno così, il problema è il titolo — e `audit()` lo segnala.
        size = max(floor, size - 1)
        lines = wrap(copy.title.upper(), display, size, box.measure)
    return size, lines


# -- motivi di genere -------------------------------------------------------
def motif_grid(canvas, box: FrontBox, palette: Palette, top: float, height: float) -> None:
    """Righe barrate e una cerchiata: dice «enigma di deduzione» prima del titolo.

    L'elemento diverso in mezzo a elementi uguali è quello che l'occhio trova
    per primo — ed è anche il ciclo aperto: chi è quello cerchiato?
    """
    rows = 7
    row_height = height / rows
    left = box.center - box.measure * 0.34
    right = box.center + box.measure * 0.34
    box_side = row_height * 0.34
    marked = 4

    for index in range(rows):
        y = top - index * row_height - row_height * 0.5
        eliminated = index != marked
        ink = palette.muted if eliminated else palette.accent
        canvas.setStrokeColor(colors.HexColor(ink))
        canvas.setFillColor(colors.HexColor(ink))
        canvas.setLineWidth(1.0)
        canvas.setDash(1, 0)
        # la "riga" di un elenco di sospetti: la casella è piena se il nome è
        # già stato escluso, vuota per l'unico che resta in piedi
        canvas.rect(left, y - box_side * 0.5, box_side, box_side,
                    stroke=1, fill=1 if eliminated else 0)
        bar_x = left + row_height * 0.62
        bar_width = (right - bar_x) * (0.62 + 0.3 * ((index * 7) % 5) / 5)
        canvas.setFillAlpha(0.42 if eliminated else 1)
        canvas.rect(bar_x, y - row_height * 0.11, bar_width, row_height * 0.22,
                    stroke=0, fill=1)
        canvas.setFillAlpha(1)
        if eliminated:
            # la barratura deve pesare più della barra che cancella, o in
            # miniatura le due si confondono in una riga sola
            canvas.setLineWidth(max(row_height * 0.1, 1.4))
            canvas.line(bar_x - row_height * 0.14, y,
                        bar_x + bar_width + row_height * 0.14, y)

    # la riga superstite, cerchiata: è lei che apre il ciclo
    y = top - marked * row_height - row_height * 0.5
    canvas.setStrokeColor(colors.HexColor(palette.accent))
    canvas.setLineWidth(2.2)
    canvas.rect(left - row_height * 0.3, y - row_height * 0.42,
                (right - left) + row_height * 0.6, row_height * 0.9, stroke=1, fill=0)


def motif_rules(canvas, box: FrontBox, palette: Palette, top: float, height: float) -> None:
    """Tre barre che crescono: promessa di metodo, non di racconto.

    Crescono verso il basso, nel verso in cui si legge una copertina: l'ultima,
    la più lunga, è in accento — è il punto d'arrivo, non un residuo.
    """
    bars = 3
    gap = height / (bars * 2)
    for index in range(bars):
        y = top - (index + 1) * gap * 2
        width = box.measure * (0.32 + 0.24 * index)
        color = palette.accent if index == bars - 1 else palette.muted
        canvas.setFillColor(colors.HexColor(color))
        canvas.setFillAlpha(1 if index == bars - 1 else 0.5)
        canvas.rect(box.center - width / 2, y, width, gap * 0.55, stroke=0, fill=1)
        canvas.setFillAlpha(1)


MOTIFS = {"grid": motif_grid, "rules": motif_rules, "none": None}


# -- prima di copertina -----------------------------------------------------
def draw_front(
    canvas,
    box: FrontBox,
    copy: CoverCopy,
    palette: Palette,
    *,
    display: str,
    text_font: str,
    genre: str = "non-fiction",
    over_image: bool = False,
) -> DrawResult:
    """Disegna la prima di copertina secondo il sistema.

    Ordine di lettura imposto: genere → titolo → gancio → motivo → numeri →
    autore. Chi guarda una miniatura si ferma ai primi due; chi apre la scheda
    scende fino ai numeri.
    """
    title_color = "#FFFFFF" if over_image else palette.title
    center = box.center
    top = box.y0 + box.height - box.bleed

    # 1. kicker: dice il genere in due parole, piccolo e tracciato
    y = top - box.safe * 1.5
    if copy.kicker:
        size = fit_size(
            copy.kicker.upper(), display, box.measure,
            max(box.trim_height * 0.016, 7.5), 6.5, KICKER_TRACKING,
        )
        canvas.setFillColor(colors.HexColor(palette.accent))
        _tracked(canvas, center, y - size, copy.kicker.upper(), display, size,
                 size * KICKER_TRACKING)
        y -= size * 2.6
    else:
        y -= box.safe * 0.4

    # 2. titolo: l'elemento dominante
    title_size, lines = title_block_size(copy, display, box)
    canvas.setFillColor(colors.HexColor(title_color))
    y -= title_size * 0.92
    for line in lines:
        canvas.setFont(display, title_size)
        canvas.drawCentredString(center, y, line)
        y -= title_size * 1.02

    # 3. filetto d'accento, largo quanto la riga più lunga del titolo
    widest = max((pdfmetrics.stringWidth(line, display, title_size) for line in lines), default=0)
    y += title_size * 0.28
    canvas.setStrokeColor(colors.HexColor(palette.accent))
    canvas.setLineWidth(3)
    canvas.line(center - widest * 0.3, y, center + widest * 0.3, y)

    # 4. gancio: il ciclo aperto
    if copy.hook:
        hook_size = fit_size(copy.hook, text_font, box.measure, box.trim_height * 0.028, 9)
        y -= hook_size * 2.2
        canvas.setFillColor(colors.HexColor("#FFFFFF" if over_image else palette.muted))
        for line in wrap(copy.hook, text_font, hook_size, box.measure):
            canvas.setFont(text_font, hook_size)
            canvas.drawCentredString(center, y, line)
            y -= hook_size * 1.3

    # 5. il piede si misura prima di disegnarlo: serve al motivo per sapere
    #    dove fermarsi, e a ogni riga per non finire sotto il margine di
    #    sicurezza (la riga più bassa è quella dell'autore, discendenti comprese).
    floor = box.y0 + box.bleed + box.safe
    author_size = fit_size(
        copy.author.upper(), display, box.measure,
        box.trim_height * 0.024, 8, AUTHOR_TRACKING,
    )
    author_baseline = floor + author_size * 0.28
    foot_top = author_baseline + author_size * 0.8

    badge_size = badge_baseline = 0.0
    if copy.badge:
        badge_size = fit_size(
            copy.badge.upper(), display, box.measure,
            max(author_size * 0.62, 6.5), 6.0, BADGE_TRACKING,
        )
        badge_baseline = foot_top + badge_size * 1.05
        foot_top = badge_baseline + badge_size * 0.8

    stats_size = band_bottom = band_height = 0.0
    if copy.stats:
        stats_size = fit_size(
            copy.stats.upper(), display, box.measure * 0.92,
            box.trim_height * 0.026, 8, STATS_TRACKING,
        )
        band_height = stats_size * 2.1
        band_bottom = foot_top + stats_size * 0.85
        foot_top = band_bottom + band_height

    # 6. motivo di genere, nello spazio che resta fra gancio e piede
    motif = MOTIFS.get(GENRE_DEFAULTS.get(genre, {}).get("motif", "none"))
    available = y - (foot_top + box.safe * 0.6)
    if motif and available > box.trim_height * 0.14 and not over_image:
        motif(canvas, box, palette, y - box.trim_height * 0.03, available * 0.74)

    # 7. numeri in cifre, appoggiati a una banda che arriva fino al taglio:
    #    è il piede che tiene insieme la copertina anche in miniatura
    if copy.stats:
        canvas.setFillColor(colors.HexColor(palette.accent))
        canvas.rect(box.x0, band_bottom, box.width, band_height, stroke=0, fill=1)
        canvas.setFillColor(colors.HexColor(palette.background))
        _tracked(
            canvas, center, band_bottom + band_height * 0.36, copy.stats.upper(),
            display, stats_size, stats_size * STATS_TRACKING,
        )

    # 8. garanzia e autore, sotto la banda
    if copy.badge:
        canvas.setFillColor(colors.HexColor(palette.muted))
        _tracked(
            canvas, center, badge_baseline, copy.badge.upper(),
            display, badge_size, badge_size * BADGE_TRACKING,
        )
    canvas.setFillColor(colors.HexColor(title_color))
    _tracked(
        canvas, center, author_baseline, copy.author.upper(),
        display, author_size, author_size * AUTHOR_TRACKING,
    )

    cap_ratio = title_size * 0.72 / box.trim_height
    return DrawResult(
        title_size=title_size,
        title_lines=lines,
        cap_ratio=cap_ratio,
        contrast=contrast_ratio(title_color, palette.background),
    )


# --------------------------------------------------------------------------
# Verifica: la copertina vista come la vede il cliente
# --------------------------------------------------------------------------
@dataclass
class CoverAudit:
    title_cap_px: float           # altezza maiuscole del titolo, in pixel di miniatura
    title_cap_ratio: float
    contrast: float
    pops_on_white: bool
    top_elements: int
    inside_safe_area: bool
    title_lines: int = 0
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems

    def to_dict(self) -> dict:
        return {
            "titolo_px_in_miniatura": round(self.title_cap_px, 1),
            "titolo_percentuale_altezza": round(self.title_cap_ratio * 100, 1),
            "titolo_righe": self.title_lines,
            "contrasto": round(self.contrast, 1),
            "stacca_su_bianco": self.pops_on_white,
            "elementi_in_alto": self.top_elements,
            "dentro_area_sicura": self.inside_safe_area,
            "problemi": self.problems,
        }


def audit(
    pdf_path: Path,
    *,
    trim: str,
    pages: int,
    paper: str,
    palette: Palette,
    title: str,
) -> CoverAudit:
    """Misura la copertina finita: quanto è grande il titolo in miniatura, che
    contrasto ha, quanti elementi affollano la metà alta."""
    try:
        import pymupdf
    except ImportError:  # pragma: no cover - PyMuPDF è consigliato, non obbligatorio
        return CoverAudit(
            title_cap_px=0,
            title_cap_ratio=0,
            contrast=palette.title_contrast,
            pops_on_white=palette.pops_on_white,
            top_elements=0,
            inside_safe_area=True,
            problems=["PyMuPDF non installato: copertina non verificata."],
        )

    trim_w, trim_h = kdpspecs.trim_size_in(trim)
    spine = kdpspecs.spine_width_in(pages, paper)
    bleed = kdpspecs.BLEED_IN
    front_x0 = (bleed + trim_w + spine) * INCH
    scale = THUMBNAIL_WIDTH_PX / (trim_w * INCH)

    document = pymupdf.open(pdf_path)
    page = document[0]
    page_height = page.rect.height
    words = [word for word in title.upper().split() if len(word) > 3]
    title_spans: list[dict] = []
    front_spans: list[dict] = []
    top_blocks: set[int] = set()

    for block_index, block in enumerate(page.get_text("dict")["blocks"]):
        for line in block.get("lines", []):
            # Il dorso è testo ruotato: la sua misura va letta in verticale e
            # non c'entra con l'area di sicurezza della prima.
            vertical = abs(line.get("dir", (1.0, 0.0))[0]) < 0.5
            for span in line.get("spans", []):
                text = span["text"].strip()
                if not text or span["bbox"][0] < front_x0 or vertical:
                    continue
                front_spans.append(span)
                if any(word in text.upper() for word in words):
                    title_spans.append(span)
                if span["bbox"][1] < page_height * 0.5:
                    top_blocks.add(block_index)
    document.close()

    # Fra le righe che contengono una parola del titolo, il titolo è la più
    # grande: il gancio può ripetere una parola del titolo, ma non il corpo.
    if title_spans:
        biggest = max(span["size"] for span in title_spans)
        title_spans = [span for span in title_spans if span["size"] >= biggest * 0.95]

    problems: list[str] = []
    if not title_spans:
        problems.append("Il titolo non è stato trovato sulla prima di copertina.")
        cap_pt = 0.0
    else:
        cap_pt = max(span["size"] for span in title_spans) * 0.72

    cap_px = cap_pt * scale
    cap_ratio = cap_pt / (trim_h * INCH) if cap_pt else 0.0
    if cap_ratio and cap_ratio < MIN_TITLE_CAP_RATIO:
        problems.append(
            f"Titolo troppo piccolo per la miniatura: {cap_px:.0f} px a "
            f"{THUMBNAIL_WIDTH_PX} px di larghezza ({cap_ratio * 100:.1f}% dell'altezza, "
            f"minimo {MIN_TITLE_CAP_RATIO * 100:.0f}%)."
        )
    if palette.title_contrast < MIN_CONTRAST:
        problems.append(
            f"Contrasto titolo/fondo {palette.title_contrast:.1f}:1, sotto il minimo "
            f"{MIN_CONTRAST:.0f}:1."
        )
    if not palette.pops_on_white:
        problems.append(
            "Il fondo non stacca dalla pagina bianca dei risultati: la copertina perde "
            "il bordo e con esso metà della visibilità."
        )
    if len(title_spans) > MAX_TITLE_LINES:
        problems.append(
            f"Il titolo occupa {len(title_spans)} righe (massimo {MAX_TITLE_LINES}): "
            "in miniatura un titolo lungo si legge come un paragrafo, non come un'insegna."
        )
    if len(top_blocks) > MAX_TOP_ELEMENTS:
        problems.append(
            f"{len(top_blocks)} blocchi di testo nella metà alta (massimo {MAX_TOP_ELEMENTS}): "
            "in miniatura diventano una macchia."
        )

    # L'area rifilata della prima va da `front_x0` a `front_x0 + trim`:
    # l'abbondanza è oltre il taglio esterno e in stampa viene rifilata via.
    safe_left = front_x0 + SAFE_MARGIN_IN * INCH
    safe_right = front_x0 + (trim_w - SAFE_MARGIN_IN) * INCH
    safe_top = (bleed + SAFE_MARGIN_IN) * INCH
    safe_bottom = (bleed + trim_h - SAFE_MARGIN_IN) * INCH
    outside = [
        span
        for span in front_spans
        if span["bbox"][0] < safe_left - 1
        or span["bbox"][2] > safe_right + 1
        or span["bbox"][1] < safe_top - 1
        or span["bbox"][3] > safe_bottom + 1
    ]
    inside_safe = not outside
    if outside:
        listed = ", ".join(f"«{span['text'].strip()[:28]}»" for span in outside[:3])
        problems.append(
            f"Testo fuori dall'area di sicurezza ({len(outside)} righe): in stampa "
            f"rischia il taglio — {listed}."
        )

    return CoverAudit(
        title_cap_px=cap_px,
        title_cap_ratio=cap_ratio,
        contrast=palette.title_contrast,
        pops_on_white=palette.pops_on_white,
        top_elements=len(top_blocks),
        inside_safe_area=inside_safe,
        title_lines=len(title_spans),
        problems=problems,
    )


def render_thumbnail(pdf_path: Path, output: Path, *, trim: str, pages: int, paper: str) -> Path:
    """Salva la prima di copertina alla dimensione con cui la vede il cliente.

    Guardare questo file, e non il PDF a schermo intero, è l'unico modo onesto
    di giudicare una copertina.
    """
    import pymupdf

    trim_w, trim_h = kdpspecs.trim_size_in(trim)
    spine = kdpspecs.spine_width_in(pages, paper)
    bleed = kdpspecs.BLEED_IN
    front_x0 = (bleed + trim_w + spine) * INCH

    document = pymupdf.open(pdf_path)
    page = document[0]
    # Solo l'area rifilata della prima: l'abbondanza, che in stampa sparisce,
    # falserebbe il giudizio sulla miniatura.
    clip = pymupdf.Rect(
        front_x0,
        bleed * INCH,
        front_x0 + trim_w * INCH,
        (bleed + trim_h) * INCH,
    )
    scale = THUMBNAIL_WIDTH_PX / (trim_w * INCH)
    pixmap = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), clip=clip)
    output.parent.mkdir(parents=True, exist_ok=True)
    pixmap.save(output)
    document.close()
    return output

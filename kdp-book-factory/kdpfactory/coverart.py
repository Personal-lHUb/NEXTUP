"""Illustrazioni di copertina: disegnate, non cercate.

Un'immagine in copertina serve a una cosa sola: far capire di che libro si
tratta prima che il titolo venga letto. A 160 pixel una fotografia ricca di
dettagli diventa una macchia; una **silhouette** con un solo punto luminoso si
riconosce ancora.

Per questo le illustrazioni qui sono vettoriali e generate dalla pipeline:

- non costano niente e non servono chiavi API né banche di immagini;
- sono vettori, quindi nitide a qualunque risoluzione: KDP non le contesta mai
  per i DPI, cosa che invece succede regolarmente con le foto;
- nascono nei colori della palette del libro, quindi non c'è mai il rischio che
  l'immagine litighi con il titolo;
- non hanno un autore da pagare e nessun problema di diritti — che per una
  copertina venduta su Amazon non è un dettaglio.

Ogni illustrazione ha le sue parole chiave: si sceglie in base a quello che il
libro dice di essere (titolo, sottotitolo, argomento). Se non corrisponde
niente, si usa quella prevista per il genere. È lo stesso principio del resto
del sistema di copertina: si adatta al contenuto, non si reinventa ogni volta.

Regola comune a tutte: **un solo punto in accento**. È lì che l'occhio va, ed è
quello il pezzo che racconta la storia — la finestra illuminata, l'unico nome
non barrato, l'ultimo gradino.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from reportlab.lib import colors

if TYPE_CHECKING:  # pragma: no cover - solo per i tipi: evita l'import circolare
    from .coverdesign import Palette


@dataclass(frozen=True)
class Area:
    """Il rettangolo in cui sta l'illustrazione (`y` è il bordo inferiore)."""

    x: float
    y: float
    width: float
    height: float

    @property
    def center(self) -> float:
        return self.x + self.width / 2

    @property
    def middle(self) -> float:
        return self.y + self.height / 2

    @property
    def top(self) -> float:
        return self.y + self.height

    @property
    def right(self) -> float:
        return self.x + self.width

    def inset(self, fraction: float) -> Area:
        dx, dy = self.width * fraction, self.height * fraction
        return Area(self.x + dx, self.y + dy, self.width - 2 * dx, self.height - 2 * dy)

    def fit(self, ratio: float, anchor: str = "center") -> Area:
        """Il rettangolo più grande con queste proporzioni, dentro questo.

        `anchor="bottom"` lo appoggia in basso invece di centrarlo: un'immagine
        che poggia su una linea d'orizzonte sta in piedi, la stessa immagine
        centrata in un'area molto più alta sembra galleggiare in un buco.
        """
        width = min(self.width, self.height * ratio)
        height = width / ratio
        y = self.y if anchor == "bottom" else self.middle - height / 2
        return Area(self.center - width / 2, y, width, height)


def _ink(canvas, color: str, alpha: float = 1.0) -> None:
    canvas.setFillColor(colors.HexColor(color))
    canvas.setFillAlpha(alpha)


def _pen(canvas, color: str, width: float, alpha: float = 1.0) -> None:
    canvas.setStrokeColor(colors.HexColor(color))
    canvas.setStrokeAlpha(alpha)
    canvas.setLineWidth(width)


def _polygon(canvas, points: list[tuple[float, float]], stroke: int = 0, fill: int = 1) -> None:
    path = canvas.beginPath()
    path.moveTo(*points[0])
    for point in points[1:]:
        path.lineTo(*point)
    path.close()
    canvas.drawPath(path, stroke=stroke, fill=fill)


# --------------------------------------------------------------------------
# Le illustrazioni
# --------------------------------------------------------------------------
def treno(canvas, area: Area, palette: Palette) -> None:
    """Un espresso notturno visto di fianco, con una sola finestra accesa.

    La finestra accesa è il caso: è l'unico punto in accento di tutta la
    copertina, e in miniatura è la prima cosa che si vede.
    """
    scene = area.fit(2.35, anchor="bottom")
    rail_y = scene.y + scene.height * 0.10
    wheel_r = scene.height * 0.075
    body_y = rail_y + wheel_r * 1.25
    body_h = scene.height * 0.42

    # binario
    _pen(canvas, palette.muted, max(scene.height * 0.018, 1.0), 0.55)
    canvas.line(scene.x, rail_y, scene.right, rail_y)
    _pen(canvas, palette.muted, max(scene.height * 0.012, 0.7), 0.3)
    step = scene.width / 26
    for index in range(26):
        x = scene.x + index * step + step * 0.3
        canvas.line(x, rail_y, x, rail_y - scene.height * 0.05)

    def wheels(x0: float, width: float, count: int, driver: int | None = None) -> None:
        """Ruote. `driver` è la ruota motrice della locomotiva: più grande."""
        _pen(canvas, palette.muted, max(scene.height * 0.016, 0.9), 0.9)
        _ink(canvas, palette.background, 1)
        for index in range(count):
            cx = x0 + width * (index + 0.5) / count
            radius = wheel_r * (1.35 if index == driver else 1.0)
            canvas.circle(cx, rail_y + radius, radius, stroke=1, fill=1)

    def carrozza(x0: float, width: float, lit: int | None) -> None:
        _ink(canvas, palette.muted, 0.18)
        _pen(canvas, palette.muted, max(scene.height * 0.02, 1.1), 0.9)
        canvas.roundRect(x0, body_y, width, body_h, body_h * 0.12, stroke=1, fill=1)
        # tetto
        _ink(canvas, palette.muted, 0.45)
        canvas.rect(x0, body_y + body_h * 0.86, width, body_h * 0.14, stroke=0, fill=1)
        # finestrini
        windows = 4
        pitch = width / windows
        win_w, win_h = pitch * 0.58, body_h * 0.4
        for index in range(windows):
            wx = x0 + pitch * index + (pitch - win_w) / 2
            wy = body_y + body_h * 0.4
            if index == lit:
                # alone: la luce si vede prima della finestra
                _ink(canvas, palette.accent, 0.22)
                canvas.rect(wx - win_w * 0.3, wy - win_h * 0.3,
                            win_w * 1.6, win_h * 1.6, stroke=0, fill=1)
                _ink(canvas, palette.accent, 1)
            else:
                _ink(canvas, palette.background, 0.85)
            canvas.rect(wx, wy, win_w, win_h, stroke=0, fill=1)
        wheels(x0, width, 2)

    unit = scene.width / 100
    cursor = scene.x
    for index in range(3):
        carrozza(cursor, unit * 20.5, lit=2 if index == 1 else None)
        cursor += unit * 22.3

    # locomotiva: cabina, caldaia, camino, fumo
    cab_w, boiler_w = unit * 11, unit * 21
    _ink(canvas, palette.muted, 0.18)
    _pen(canvas, palette.muted, max(scene.height * 0.02, 1.1), 0.9)
    canvas.roundRect(cursor, body_y, cab_w, body_h * 1.22, body_h * 0.12, stroke=1, fill=1)
    canvas.roundRect(cursor + cab_w - body_h * 0.2, body_y, boiler_w + body_h * 0.2,
                     body_h * 0.82, body_h * 0.38, stroke=1, fill=1)
    _ink(canvas, palette.background, 0.85)
    canvas.rect(cursor + cab_w * 0.22, body_y + body_h * 0.62,
                cab_w * 0.56, body_h * 0.42, stroke=0, fill=1)

    chimney_x = cursor + cab_w + boiler_w * 0.74
    _ink(canvas, palette.muted, 0.5)
    canvas.rect(chimney_x, body_y + body_h * 0.82, unit * 3.4, body_h * 0.3, stroke=0, fill=1)
    # il fumo: piccolo e attaccato al camino, poi si allarga e svanisce
    for index in range(5):
        _ink(canvas, palette.muted, 0.20 - index * 0.035)
        canvas.circle(
            chimney_x + unit * 1.7 - index * unit * 1.2,
            body_y + body_h * 1.16 + index * body_h * 0.22,
            body_h * (0.1 + index * 0.042),
            stroke=0, fill=1,
        )
    wheels(cursor, cab_w + boiler_w, 3, driver=1)

    # faro: l'unico altro accento, piccolo, in testa al treno
    _ink(canvas, palette.accent, 0.9)
    canvas.circle(cursor + cab_w + boiler_w - unit * 1.6, body_y + body_h * 0.4,
                  unit * 1.5, stroke=0, fill=1)
    canvas.setFillAlpha(1)
    canvas.setStrokeAlpha(1)


def lente(canvas, area: Area, palette: Palette) -> None:
    """Una lente sopra una griglia di indizi: uno solo è quello giusto."""
    scene = area.fit(1.25)
    cols, rows = 5, 4
    pitch_x = scene.width / (cols + 1)
    pitch_y = scene.height / (rows + 1)
    side = min(pitch_x, pitch_y) * 0.46
    marked = (3, 1)

    for row in range(rows):
        for col in range(cols):
            x = scene.x + pitch_x * (col + 1) - side / 2
            y = scene.y + pitch_y * (row + 1) - side / 2
            if (col, row) == marked:
                _ink(canvas, palette.accent, 1)
                canvas.rect(x, y, side, side, stroke=0, fill=1)
            else:
                _ink(canvas, palette.muted, 0.3)
                canvas.rect(x, y, side, side, stroke=0, fill=1)

    radius = min(scene.width, scene.height) * 0.29
    cx = scene.x + pitch_x * (marked[0] + 1)
    cy = scene.y + pitch_y * (marked[1] + 1)
    _ink(canvas, palette.background, 0.0)
    _pen(canvas, palette.title, max(radius * 0.13, 2.0), 1)
    canvas.circle(cx, cy, radius, stroke=1, fill=0)
    angle = math.radians(-40)
    _pen(canvas, palette.title, max(radius * 0.17, 2.4), 1)
    canvas.line(
        cx + radius * math.cos(angle), cy + radius * math.sin(angle),
        cx + radius * 1.75 * math.cos(angle), cy + radius * 1.75 * math.sin(angle),
    )
    canvas.setFillAlpha(1)
    canvas.setStrokeAlpha(1)


def elenco(canvas, area: Area, palette: Palette) -> None:
    """Un elenco di sospetti barrati, uno solo in piedi.

    L'elemento diverso in mezzo a elementi uguali è quello che l'occhio trova
    per primo — ed è anche il ciclo aperto: chi è quello cerchiato?
    """
    rows = 7
    scene = area.fit(1.45)
    row_height = scene.height / rows
    left, right = scene.x, scene.right
    box_side = row_height * 0.34
    marked = 4

    for index in range(rows):
        y = scene.top - index * row_height - row_height * 0.5
        eliminated = index != marked
        ink = palette.muted if eliminated else palette.accent
        _pen(canvas, ink, 1.0, 1)
        _ink(canvas, ink, 1)
        canvas.setDash(1, 0)
        # la casella è piena se il nome è già stato escluso, vuota per l'unico
        # che resta in piedi
        canvas.rect(left, y - box_side * 0.5, box_side, box_side,
                    stroke=1, fill=1 if eliminated else 0)
        bar_x = left + row_height * 0.62
        bar_width = (right - bar_x) * (0.62 + 0.3 * ((index * 7) % 5) / 5)
        _ink(canvas, ink, 0.42 if eliminated else 1)
        canvas.rect(bar_x, y - row_height * 0.11, bar_width, row_height * 0.22,
                    stroke=0, fill=1)
        if eliminated:
            # la barratura deve pesare più della barra che cancella, o in
            # miniatura le due si confondono in una riga sola
            _pen(canvas, palette.muted, max(row_height * 0.1, 1.4), 1)
            canvas.line(bar_x - row_height * 0.14, y, bar_x + bar_width + row_height * 0.14, y)

    y = scene.top - marked * row_height - row_height * 0.5
    _pen(canvas, palette.accent, 2.2, 1)
    canvas.rect(left - row_height * 0.3, y - row_height * 0.42,
                (right - left) + row_height * 0.6, row_height * 0.9, stroke=1, fill=0)
    canvas.setFillAlpha(1)
    canvas.setStrokeAlpha(1)


def orologio(canvas, area: Area, palette: Palette) -> None:
    """Un quadrante con uno spicchio in accento: le ore che il libro restituisce."""
    scene = area.fit(1.0)
    radius = scene.width / 2
    cx, cy = scene.center, scene.middle
    box = (cx - radius, cy - radius, cx + radius, cy + radius)

    _ink(canvas, palette.accent, 0.9)
    canvas.wedge(*box, 0, 90, stroke=0, fill=1)

    _pen(canvas, palette.muted, max(radius * 0.045, 1.4), 0.9)
    _ink(canvas, palette.background, 0.0)
    canvas.circle(cx, cy, radius, stroke=1, fill=0)

    for index in range(12):
        angle = math.radians(90 - index * 30)
        outer = radius * 0.93
        inner = radius * (0.78 if index % 3 == 0 else 0.86)
        _pen(canvas, palette.muted, max(radius * (0.05 if index % 3 == 0 else 0.03), 1.0), 0.85)
        canvas.line(cx + inner * math.cos(angle), cy + inner * math.sin(angle),
                    cx + outer * math.cos(angle), cy + outer * math.sin(angle))

    _pen(canvas, palette.title, max(radius * 0.055, 1.6), 1)
    canvas.line(cx, cy, cx, cy + radius * 0.62)          # lancetta dei minuti
    canvas.line(cx, cy, cx + radius * 0.45, cy)          # lancetta delle ore
    _ink(canvas, palette.accent, 1)
    canvas.circle(cx, cy, max(radius * 0.06, 1.6), stroke=0, fill=1)
    canvas.setFillAlpha(1)
    canvas.setStrokeAlpha(1)


def scala(canvas, area: Area, palette: Palette) -> None:
    """Gradini che salgono verso un punto in accento: un metodo, non un racconto."""
    scene = area.fit(1.5)
    steps = 4
    step_w = scene.width / (steps + 0.6)
    unit = scene.height / (steps + 1.2)

    for index in range(steps):
        height = unit * (index + 1)
        x = scene.x + step_w * index * 1.15
        last = index == steps - 1
        _ink(canvas, palette.accent if last else palette.muted, 1 if last else 0.4)
        canvas.rect(x, scene.y, step_w, height, stroke=0, fill=1)

    # il punto d'arrivo, sopra l'ultimo gradino
    top_x = scene.x + step_w * (steps - 1) * 1.15 + step_w / 2
    top_y = scene.y + unit * steps
    _ink(canvas, palette.accent, 1)
    canvas.circle(top_x, top_y + unit * 0.55, unit * 0.3, stroke=0, fill=1)

    _pen(canvas, palette.muted, max(scene.height * 0.012, 1.0), 0.55)
    canvas.line(scene.x - step_w * 0.3, scene.y, scene.right, scene.y)
    canvas.setFillAlpha(1)
    canvas.setStrokeAlpha(1)


def porta(canvas, area: Area, palette: Palette) -> None:
    """Una porta socchiusa e la luce che ne esce: qualcosa è appena successo."""
    scene = area.fit(0.72)
    frame_w = scene.width * 0.62
    frame_x = scene.center - frame_w / 2
    frame_h = scene.height * 0.88
    frame_y = scene.y + scene.height * 0.06
    opening = frame_w * 0.4

    # la luce che esce, prima di tutto: sta sotto la porta
    _ink(canvas, palette.accent, 0.3)
    _polygon(canvas, [
        (frame_x + frame_w - opening, frame_y),
        (frame_x + frame_w, frame_y),
        (scene.right, frame_y - scene.height * 0.05),
        (scene.center, frame_y - scene.height * 0.05),
    ])

    _ink(canvas, palette.accent, 0.85)
    canvas.rect(frame_x + frame_w - opening, frame_y, opening, frame_h, stroke=0, fill=1)

    # l'anta socchiusa, in prospettiva
    _ink(canvas, palette.muted, 0.22)
    _pen(canvas, palette.muted, max(scene.width * 0.012, 1.2), 0.9)
    _polygon(canvas, [
        (frame_x, frame_y),
        (frame_x + frame_w - opening, frame_y),
        (frame_x + frame_w - opening, frame_y + frame_h),
        (frame_x, frame_y + frame_h * 0.94),
    ], stroke=1, fill=1)

    _ink(canvas, palette.title, 0.9)
    canvas.circle(frame_x + frame_w - opening * 1.35, frame_y + frame_h * 0.47,
                  max(scene.width * 0.016, 1.6), stroke=0, fill=1)

    # lo stipite
    _pen(canvas, palette.muted, max(scene.width * 0.018, 1.6), 0.75)
    canvas.line(frame_x - frame_w * 0.06, frame_y, frame_x - frame_w * 0.06,
                frame_y + frame_h * 1.04)
    canvas.line(frame_x + frame_w * 1.06, frame_y, frame_x + frame_w * 1.06,
                frame_y + frame_h * 1.04)
    canvas.line(frame_x - frame_w * 0.06, frame_y + frame_h * 1.04,
                frame_x + frame_w * 1.06, frame_y + frame_h * 1.04)
    canvas.setFillAlpha(1)
    canvas.setStrokeAlpha(1)


# --------------------------------------------------------------------------
# Scelta dell'illustrazione
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Art:
    name: str
    draw: Callable[[object, Area, Palette], None]
    keywords: tuple[str, ...]
    ratio: float          # proporzione consigliata: quanto spazio le serve
    description: str
    #: a parità di parole trovate vince la più concreta: una scena si riconosce
    #: e si ricorda, un segno astratto no
    concrete: int = 1


ARTS: tuple[Art, ...] = (
    Art("treno", treno,
        ("train", "express", "carriage", "rail", "railway", "locomotive", "sleeper car",
         "treno", "espresso", "vagone", "carrozza", "binari", "ferrovia", "stazione"),
        2.35, "un espresso notturno con una sola finestra accesa", concrete=3),
    Art("lente", lente,
        ("detective", "clue", "mystery", "investigation", "whodunnit", "suspect",
         "indizio", "mistero", "indagine", "giallo", "sospetto", "delitto", "enigma"),
        1.25, "una lente sopra una griglia di indizi", concrete=2),
    Art("elenco", elenco,
        ("deduction", "logic", "puzzle", "elimination", "grid",
         "deduzione", "logica", "enigmistica", "eliminazione"),
        1.45, "un elenco di sospetti barrati, uno solo in piedi"),
    Art("orologio", orologio,
        ("hour", "time", "morning", "minute", "schedule", "routine", "day", "clock",
         "ora", "ore", "tempo", "mattina", "giornata", "agenda", "abitudine", "orario"),
        1.0, "un quadrante con uno spicchio in accento", concrete=2),
    Art("scala", scala,
        ("method", "system", "step", "guide", "level", "growth", "progress", "habit",
         "metodo", "sistema", "passo", "guida", "livello", "crescita", "percorso"),
        1.5, "gradini che salgono verso un punto in accento"),
    Art("porta", porta,
        ("house", "home", "door", "secret", "border", "return", "night",
         "casa", "porta", "segreto", "confine", "ritorno", "notte", "soglia"),
        0.72, "una porta socchiusa e la luce che ne esce", concrete=3),
)

#: se il contenuto non dice niente di riconoscibile, decide il genere
GENRE_ART = {"enigmi": "elenco", "non-fiction": "scala", "fiction": "porta"}

BY_NAME = {art.name: art for art in ARTS}


def pick(subject: str, genre: str = "non-fiction", wanted: str = "auto") -> Art:
    """L'illustrazione che rappresenta *questo* libro.

    Prima si guarda che cosa il libro dice di essere (titolo, sottotitolo,
    argomento); solo se non emerge niente si ricade su quella del genere. La
    scelta d'autore (`cover_art` in `book.json`) vince su tutto.
    """
    if wanted in BY_NAME:
        return BY_NAME[wanted]
    if wanted == "nessuna":
        raise KeyError("nessuna")

    text = f" {subject.lower()} "
    best: tuple[int, int, Art] | None = None
    for art in ARTS:
        hits = sum(1 for keyword in art.keywords if keyword in text)
        score = (hits, art.concrete)
        if hits and (best is None or score > best[:2]):
            best = (*score, art)
    if best:
        return best[2]
    return BY_NAME[GENRE_ART.get(genre, "scala")]


def draw(canvas, art: Art, area: Area, palette: Palette) -> None:
    """Disegna l'illustrazione isolando lo stato grafico.

    Trasparenze, tratteggi e spessori restano nello stato della pagina: senza
    `saveState` un'illustrazione si porterebbe dietro il resto della copertina.
    """
    canvas.saveState()
    try:
        art.draw(canvas, area, palette)
    finally:
        canvas.restoreState()

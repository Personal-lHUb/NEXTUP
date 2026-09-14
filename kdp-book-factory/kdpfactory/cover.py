"""Copertina full-wrap (quarta + dorso + prima) in PDF, pronta per KDP.

Il PDF prodotto ha le dimensioni esatte richieste da KDP per il numero di
pagine reale del libro: cambiando il numero di pagine cambia lo spessore del
dorso, quindi la copertina va rigenerata **dopo** l'impaginazione definitiva.
"""

from __future__ import annotations

import hashlib
import textwrap
from dataclasses import dataclass
from pathlib import Path

from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas as pdfcanvas

from . import kdpspecs
from .models import BookSpec
from .typography import register_family, set_default_canvas_font

INCH = kdpspecs.INCH
SAFE_MARGIN_IN = 0.25


@dataclass(frozen=True)
class Theme:
    name: str
    background: str
    panel: str
    title: str
    accent: str
    body: str


THEMES: tuple[Theme, ...] = (
    Theme("notte", "#131A2B", "#1C2740", "#FFFFFF", "#E8B23A", "#C8D2E4"),
    Theme("bosco", "#14271F", "#1B3429", "#F4F1E8", "#8FBF6F", "#CBD8CB"),
    Theme("terracotta", "#2A1512", "#3A1F19", "#FBF3EA", "#D4703A", "#E3CDBE"),
    Theme("indaco", "#1B1636", "#262046", "#FFFFFF", "#7B6CF6", "#CFC9EC"),
    Theme("carta", "#EFE7D8", "#E4D9C4", "#1E1B16", "#9A5B2E", "#4A4338"),
    Theme("grafite", "#1A1A1A", "#262626", "#FFFFFF", "#D93A3A", "#CFCFCF"),
)


def pick_theme(spec: BookSpec) -> Theme:
    """Tema scelto dall'utente o derivato in modo stabile dal titolo."""
    wanted = getattr(spec, "cover_theme", "auto")
    if wanted and wanted != "auto":
        for theme in THEMES:
            if theme.name == wanted:
                return theme
    digest = hashlib.sha256(spec.title.encode("utf-8")).digest()
    return THEMES[digest[0] % len(THEMES)]


def _fit_font_size(text: str, font: str, max_width: float, start: float, minimum: float) -> float:
    size = start
    while size > minimum and pdfmetrics.stringWidth(text, font, size) > max_width:
        size -= 0.5
    return size


def _wrap_lines(text: str, font: str, size: float, max_width: float) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        trial = " ".join(current + [word])
        if pdfmetrics.stringWidth(trial, font, size) <= max_width or not current:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def build_cover(
    spec: BookSpec,
    pages: int,
    output: Path,
    *,
    back_cover_text: str = "",
    bullets: list[str] | None = None,
    author_line: str = "",
    guides: bool = False,
) -> dict:
    """Genera il PDF di copertina. Restituisce le misure usate."""
    theme = pick_theme(spec)
    display = register_family("sans")
    serif = register_family("serif")
    set_default_canvas_font(serif)

    trim_w, trim_h = kdpspecs.trim_size_in(spec.trim)
    spine_in = kdpspecs.spine_width_in(pages, spec.paper)
    cover_w_in, cover_h_in = kdpspecs.cover_size_in(spec.trim, pages, spec.paper)
    bleed = kdpspecs.BLEED_IN

    width, height = cover_w_in * INCH, cover_h_in * INCH
    output.parent.mkdir(parents=True, exist_ok=True)
    c = pdfcanvas.Canvas(str(output), pagesize=(width, height))
    c.setTitle(f"{spec.title} — copertina")

    back_x0 = bleed * INCH
    spine_x0 = (bleed + trim_w) * INCH
    front_x0 = (bleed + trim_w + spine_in) * INCH
    trim_w_pt, trim_h_pt = trim_w * INCH, trim_h * INCH
    safe = SAFE_MARGIN_IN * INCH

    # Fondo
    c.setFillColor(colors.HexColor(theme.background))
    c.rect(0, 0, width, height, stroke=0, fill=1)

    # --- prima di copertina ------------------------------------------------
    c.setFillColor(colors.HexColor(theme.panel))
    c.rect(front_x0, 0, trim_w_pt + bleed * INCH, height, stroke=0, fill=1)

    # Cornice sottile all'interno dell'area di sicurezza
    c.setStrokeColor(colors.HexColor(theme.accent))
    c.setLineWidth(0.8)
    c.rect(
        front_x0 + safe * 1.3,
        (bleed + SAFE_MARGIN_IN * 1.3) * INCH,
        trim_w_pt - 2.6 * safe,
        trim_h_pt - 2.6 * safe,
        stroke=1,
        fill=0,
    )

    inner_w = trim_w_pt - 3.4 * safe
    title_size = _fit_font_size(max(spec.title.split(), key=len, default="A"), display,
                                inner_w, 46, 18)
    title_lines = _wrap_lines(spec.title.upper(), display, title_size, inner_w)
    y = height - (bleed + 1.15) * INCH
    c.setFillColor(colors.HexColor(theme.title))
    for line in title_lines:
        c.setFont(display, title_size)
        c.drawCentredString(front_x0 + trim_w_pt / 2, y, line)
        y -= title_size * 1.12

    # Filetto decorativo
    y -= 0.22 * INCH
    c.setStrokeColor(colors.HexColor(theme.accent))
    c.setLineWidth(2)
    c.line(front_x0 + trim_w_pt / 2 - 0.6 * INCH, y, front_x0 + trim_w_pt / 2 + 0.6 * INCH, y)
    y -= 0.42 * INCH

    if spec.subtitle:
        sub_size = _fit_font_size(spec.subtitle, serif, inner_w, 17, 10)
        c.setFillColor(colors.HexColor(theme.body))
        for line in _wrap_lines(spec.subtitle, serif, sub_size, inner_w):
            c.setFont(serif, sub_size)
            c.drawCentredString(front_x0 + trim_w_pt / 2, y, line)
            y -= sub_size * 1.35

    author_size = _fit_font_size(spec.author.upper(), display, inner_w, 16, 9)
    author_y = (bleed + 0.95) * INCH
    c.setStrokeColor(colors.HexColor(theme.accent))
    c.setLineWidth(0.8)
    c.line(
        front_x0 + trim_w_pt / 2 - 0.45 * INCH,
        author_y + author_size * 1.5,
        front_x0 + trim_w_pt / 2 + 0.45 * INCH,
        author_y + author_size * 1.5,
    )
    c.setFillColor(colors.HexColor(theme.accent))
    c.setFont(display, author_size)
    c.drawCentredString(front_x0 + trim_w_pt / 2, author_y, spec.author.upper())

    # --- dorso -------------------------------------------------------------
    spine_pt = spine_in * INCH
    if kdpspecs.spine_text_allowed(pages) and spine_pt > 10:
        c.saveState()
        c.translate(spine_x0 + spine_pt / 2, height / 2)
        c.rotate(-90)  # lettura dall'alto verso il basso, come da standard
        spine_font_size = min(spine_pt * 0.42, 14)
        available = trim_h_pt - 1.6 * INCH
        spine_title = spec.title.upper()
        size = _fit_font_size(spine_title, display, available, spine_font_size, 6)
        c.setFillColor(colors.HexColor(theme.title))
        c.setFont(display, size)
        c.drawCentredString(0, -size * 0.35, spine_title)
        c.restoreState()
        # Nome autore in fondo al dorso
        c.saveState()
        c.translate(spine_x0 + spine_pt / 2, (bleed + 0.6) * INCH)
        c.rotate(-90)
        c.setFillColor(colors.HexColor(theme.accent))
        c.setFont(display, max(min(spine_pt * 0.34, 10), 6))
        c.drawRightString(0, -max(min(spine_pt * 0.34, 10), 6) * 0.35, spec.author.upper())
        c.restoreState()

    # --- quarta di copertina ----------------------------------------------
    text_x = back_x0 + safe
    text_w = trim_w_pt - 2 * safe
    y = height - (bleed + 0.9) * INCH

    if back_cover_text:
        headline, _, rest = back_cover_text.partition("\n\n")
        head_size = _fit_font_size(headline[:40] or "X", display, text_w, 19, 11)
        c.setFillColor(colors.HexColor(theme.title))
        for line in _wrap_lines(headline, display, head_size, text_w):
            c.setFont(display, head_size)
            c.drawString(text_x, y, line)
            y -= head_size * 1.25
        y -= 0.18 * INCH

        c.setFillColor(colors.HexColor(theme.body))
        body_size = 10.5
        for paragraph in [p for p in rest.split("\n\n") if p.strip()]:
            for line in _wrap_lines(paragraph.strip(), serif, body_size, text_w):
                c.setFont(serif, body_size)
                c.drawString(text_x, y, line)
                y -= body_size * 1.45
            y -= body_size * 0.6

    for bullet in bullets or []:
        # Il punto elenco è disegnato, non scritto: molti font privi del glifo
        # stamperebbero un rettangolo vuoto.
        c.setFillColor(colors.HexColor(theme.accent))
        c.rect(text_x, y + 2.5, 4.5, 4.5, stroke=0, fill=1)
        c.setFillColor(colors.HexColor(theme.body))
        for line in _wrap_lines(bullet, serif, 10.5, text_w - 0.22 * INCH):
            c.setFont(serif, 10.5)
            c.drawString(text_x + 0.22 * INCH, y, line)
            y -= 10.5 * 1.35
        y -= 10.5 * 0.4

    if author_line:
        c.setFillColor(colors.HexColor(theme.body))
        for line in _wrap_lines(author_line, serif, 9.5, text_w):
            c.setFont(serif, 9.5)
            c.drawString(text_x, y, line)
            y -= 9.5 * 1.35

    # Area riservata al codice a barre (KDP la sovrastampa: va lasciata libera).
    bar_w, bar_h = kdpspecs.BARCODE_ZONE_IN
    bar_x = spine_x0 - (SAFE_MARGIN_IN + bar_w) * INCH
    bar_y = (bleed + SAFE_MARGIN_IN) * INCH
    c.setFillColor(colors.white)
    c.rect(bar_x, bar_y, bar_w * INCH, bar_h * INCH, stroke=0, fill=1)

    if guides:
        _draw_guides(c, width, height, bleed, trim_w, trim_h, spine_in, bar_x, bar_y, bar_w, bar_h)

    c.showPage()
    c.save()

    return {
        "cover_pdf": str(output),
        "pages": pages,
        "spine_in": round(spine_in, 4),
        "cover_width_in": round(cover_w_in, 4),
        "cover_height_in": round(cover_h_in, 4),
        "theme": theme.name,
        "spine_text": kdpspecs.spine_text_allowed(pages),
    }


def _draw_guides(c, width, height, bleed, trim_w, trim_h, spine_in, bar_x, bar_y, bar_w, bar_h):
    """Linee di controllo: NON usare questa versione per l'upload su KDP."""
    c.setStrokeColor(colors.magenta)
    c.setLineWidth(0.5)
    c.rect(bleed * INCH, bleed * INCH, width - 2 * bleed * INCH, height - 2 * bleed * INCH)
    c.setStrokeColor(colors.cyan)
    c.line((bleed + trim_w) * INCH, 0, (bleed + trim_w) * INCH, height)
    c.line((bleed + trim_w + spine_in) * INCH, 0, (bleed + trim_w + spine_in) * INCH, height)
    c.setStrokeColor(colors.red)
    c.rect(bar_x, bar_y, bar_w * INCH, bar_h * INCH)
    c.setFillColor(colors.red)
    c.setFont(register_family("sans"), 7)
    c.drawString(bar_x + 3, bar_y + bar_h * INCH - 10, "area codice a barre")


def wrap_back_cover(text: str, width: int = 78) -> str:
    return "\n".join(textwrap.wrap(text, width=width))

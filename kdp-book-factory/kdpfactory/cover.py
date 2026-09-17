"""Copertina full-wrap (quarta + dorso + prima) in PDF, pronta per KDP.

Il PDF prodotto ha le dimensioni esatte richieste da KDP per il numero di
pagine reale del libro: cambiando il numero di pagine cambia lo spessore del
dorso, quindi la copertina va rigenerata **dopo** l'impaginazione definitiva.
"""

from __future__ import annotations

import textwrap
from dataclasses import asdict
from pathlib import Path

from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas as pdfcanvas

from . import coverdesign, coverimage, kdpspecs
from .coverdesign import CoverCopy, FrontBox, Palette
from .models import BookSpec
from .typography import register_family, set_default_canvas_font

INCH = kdpspecs.INCH
#: unico riferimento per il margine di sicurezza: disegno e verifica devono
#: usare lo stesso numero, altrimenti il controllo non controlla niente.
SAFE_MARGIN_IN = coverdesign.SAFE_MARGIN_IN


def pick_theme(spec: BookSpec, genre: str = "non-fiction") -> Palette:
    """Palette della copertina: scelta dall'autore o la migliore per il genere."""
    return coverdesign.pick_palette(spec, genre)


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
    image_path: Path | None = None,
    enhance_image: bool = True,
    copy: CoverCopy | None = None,
    genre: str = "",
    metadata: dict | None = None,
) -> dict:
    """Genera il PDF di copertina e ne verifica la resa in miniatura.

    La prima di copertina segue il sistema di `coverdesign`: un solo elemento
    dominante, titolo leggibile a 160 px, contrasto misurato, codice di genere.
    """
    genre = genre or ("enigmi" if getattr(spec, "genre", "") == "puzzle" else spec.genre)
    theme = pick_theme(spec, genre)
    cover_copy = copy or coverdesign.derive_copy(spec, metadata, genre)
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
    front_width = trim_w_pt + bleed * INCH
    image_report = None
    if image_path is not None:
        prepared = output.parent / f"{spec.slug}-copertina-immagine.jpg"
        image_report = coverimage.prepare(
            image_path, prepared, spec.trim, enhance=enhance_image
        )
        c.drawImage(
            str(prepared), front_x0, 0, width=front_width, height=height,
            preserveAspectRatio=False, anchor="c", mask=None,
        )
        # La velatura per la leggibilità è già dentro il JPEG preparato.
    else:
        c.setFillColor(colors.HexColor(theme.deep))
        c.rect(front_x0, 0, front_width, height, stroke=0, fill=1)

    front_box = FrontBox(
        x0=front_x0,
        y0=0.0,
        width=front_width,
        height=height,
        trim_width=trim_w_pt,
        trim_height=trim_h_pt,
        bleed=bleed * INCH,
        safe=safe,
    )
    draw_result = coverdesign.draw_front(
        c,
        front_box,
        cover_copy,
        theme,
        display=display,
        text_font=serif,
        genre=genre,
        over_image=image_report is not None,
    )

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

        c.setFillColor(colors.HexColor(theme.muted))
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
        c.setFillColor(colors.HexColor(theme.muted))
        for line in _wrap_lines(bullet, serif, 10.5, text_w - 0.22 * INCH):
            c.setFont(serif, 10.5)
            c.drawString(text_x + 0.22 * INCH, y, line)
            y -= 10.5 * 1.35
        y -= 10.5 * 0.4

    if author_line:
        c.setFillColor(colors.HexColor(theme.muted))
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

    # La copertina si giudica come la vede il cliente: in miniatura.
    verdict = coverdesign.audit(
        output, trim=spec.trim, pages=pages, paper=spec.paper,
        palette=theme, title=spec.title,
    )
    thumbnail = None
    try:
        thumbnail = coverdesign.render_thumbnail(
            output, output.parent / f"{spec.slug}-copertina-miniatura.png",
            trim=spec.trim, pages=pages, paper=spec.paper,
        )
    except ImportError:  # pragma: no cover - senza PyMuPDF si salta l'anteprima
        pass

    return {
        "cover_pdf": str(output),
        "miniatura": str(thumbnail) if thumbnail else None,
        "immagine": image_report.to_dict() if image_report else None,
        "pages": pages,
        "spine_in": round(spine_in, 4),
        "cover_width_in": round(cover_w_in, 4),
        "cover_height_in": round(cover_h_in, 4),
        "theme": theme.name,
        "spine_text": kdpspecs.spine_text_allowed(pages),
        "titolo_corpo": draw_result.title_size,
        "testi": asdict(cover_copy),
        "verifica": verdict.to_dict(),
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

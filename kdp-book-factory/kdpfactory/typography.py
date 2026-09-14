"""Font e metriche tipografiche.

KDP richiede che tutti i font siano incorporati nel PDF. I font standard
PostScript di ReportLab (Times-Roman, Helvetica...) **non** vengono
incorporati: qui si registrano sempre file TrueType, che ReportLab include
nel PDF come subset.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from reportlab.lib.fonts import addMapping
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

PROJECT_FONTS_DIR = Path(__file__).resolve().parent.parent / "fonts"

# Directory in cui cercare i file .ttf, in ordine di priorità.
FONT_SEARCH_DIRS = [
    PROJECT_FONTS_DIR,
    Path(os.environ.get("KDPFACTORY_FONTS_DIR", "/nonexistent")),
    Path("/usr/share/fonts/truetype/liberation"),
    Path("/usr/share/fonts/truetype/dejavu"),
    Path("/usr/share/fonts/truetype/freefont"),
    Path("/Library/Fonts"),
    Path("/System/Library/Fonts/Supplemental"),
    Path("C:/Windows/Fonts"),
]

# Famiglie: nome logico -> elenco di candidati (regular, bold, italic, bold-italic).
FONT_CANDIDATES: dict[str, list[tuple[str, str, str, str]]] = {
    "serif": [
        ("EBGaramond-Regular.ttf", "EBGaramond-Bold.ttf", "EBGaramond-Italic.ttf", "EBGaramond-BoldItalic.ttf"),
        ("LiberationSerif-Regular.ttf", "LiberationSerif-Bold.ttf", "LiberationSerif-Italic.ttf", "LiberationSerif-BoldItalic.ttf"),
        ("DejaVuSerif.ttf", "DejaVuSerif-Bold.ttf", "DejaVuSerif-Italic.ttf", "DejaVuSerif-BoldItalic.ttf"),
        ("FreeSerif.ttf", "FreeSerifBold.ttf", "FreeSerifItalic.ttf", "FreeSerifBoldItalic.ttf"),
        ("Georgia.ttf", "Georgiab.ttf", "Georgiai.ttf", "Georgiaz.ttf"),
    ],
    "sans": [
        ("LiberationSans-Regular.ttf", "LiberationSans-Bold.ttf", "LiberationSans-Italic.ttf", "LiberationSans-BoldItalic.ttf"),
        ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans-Oblique.ttf", "DejaVuSans-BoldOblique.ttf"),
        ("FreeSans.ttf", "FreeSansBold.ttf", "FreeSansOblique.ttf", "FreeSansBoldOblique.ttf"),
    ],
}

_registered: dict[str, str] = {}


class FontNotFoundError(RuntimeError):
    pass


def _find(filename: str) -> Path | None:
    for directory in FONT_SEARCH_DIRS:
        candidate = directory / filename
        if candidate.exists():
            return candidate
    return None


def register_family(family: str) -> str:
    """Registra una famiglia TrueType e restituisce il nome del font regular.

    Aggiungendo i quattro file .ttf in `fonts/` si sostituisce la scelta
    automatica (utile per usare un font con licenza commerciale a piacere).
    """
    if family in _registered:
        return _registered[family]
    if family not in FONT_CANDIDATES:
        raise ValueError(f"Famiglia sconosciuta: {family!r} (usa 'serif' o 'sans')")

    for regular, bold, italic, bold_italic in FONT_CANDIDATES[family]:
        paths = [_find(regular), _find(bold), _find(italic), _find(bold_italic)]
        if not paths[0]:
            continue
        base = f"KDP-{family}"
        # Se mancano le varianti si ripiega sul regular: meglio un PDF valido
        # che un errore in fase di build.
        resolved = [p or paths[0] for p in paths]
        names = (base, f"{base}-Bold", f"{base}-Italic", f"{base}-BoldItalic")
        for name, path in zip(names, resolved, strict=True):
            pdfmetrics.registerFont(TTFont(name, str(path)))
        pdfmetrics.registerFontFamily(
            base, normal=names[0], bold=names[1], italic=names[2], boldItalic=names[3]
        )
        # addMapping permette a <b>/<i> di funzionare nei Paragraph.
        addMapping(base, 0, 0, names[0])
        addMapping(base, 1, 0, names[1])
        addMapping(base, 0, 1, names[2])
        addMapping(base, 1, 1, names[3])
        _registered[family] = base
        return base

    raise FontNotFoundError(
        f"Nessun font TrueType trovato per la famiglia {family!r}. "
        f"Copia i file .ttf in {PROJECT_FONTS_DIR} oppure installa i font Liberation/DejaVu."
    )


def set_default_canvas_font(font_name: str) -> None:
    """Sostituisce Helvetica come font di default del canvas.

    ReportLab dichiara Helvetica nelle risorse di ogni pagina anche quando non
    viene usata: essendo un font PostScript standard non viene incorporata e
    un controllo di preflight la segnala come font mancante.
    """
    from reportlab import rl_config

    rl_config.canvas_basefontname = font_name


@dataclass(frozen=True)
class FontMetrics:
    avg_char_width: float
    avg_chars_per_word: float
    font_name: str


def average_metrics(family: str, size: float, sample: str) -> FontMetrics:
    """Metriche medie reali del font: larghezza media del carattere e
    lunghezza media della parola (spazio incluso)."""
    font_name = register_family(family)
    width = pdfmetrics.stringWidth(sample, font_name, size)
    chars = len(sample)
    words = len(sample.split())
    return FontMetrics(
        avg_char_width=width / chars,
        avg_chars_per_word=chars / words,
        font_name=font_name,
    )


def enable_hyphenation(language: str) -> bool:
    """Attiva la sillabazione se `pyphen` è installato (testo giustificato più pulito)."""
    try:
        import pyphen  # noqa: F401
    except ImportError:
        return False
    from reportlab import rl_config

    lang_map = {"it": "it_IT", "en": "en_GB"}
    rl_config.hyphenationLang = lang_map.get(language, "it_IT")
    rl_config.hyphenationMinWordLength = 6
    return True

"""Controlli di qualità e di conformità prima del caricamento su KDP.

Due categorie:
- ERRORE: il libro non va caricato così com'è;
- AVVISO: da guardare, non necessariamente bloccante.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from . import kdpspecs, mdlite
from .models import BookSpec, Outline
from .prompts import BANNED_OPENERS

#: Righe fatte per essere riempite a mano: file di trattini bassi o di puntini
#: di guida. Sono il segno di un medium-content, e su un full-content — il cui
#: valore «risiede interamente nella sostanza del testo» — non ci devono stare.
#: I trattini restano fuori di proposito: `---` in Markdown è una linea
#: orizzontale legittima, non uno spazio da compilare.
FILL_LINE = re.compile(r"^[ \t_]{12,}$|^[ \t.·]{12,}$", flags=re.M)

PLACEHOLDER_PATTERNS = [
    r"\bsegnaposto\b",
    r"\blorem ipsum\b",
    r"\bTODO\b",
    r"\bTBD\b",
    r"\[inserire[^\]]*\]",
    r"\[insert[^\]]*\]",
    r"\bXXX\b",
    r"come modello linguistico",
    r"as an AI language model",
]

STOPWORDS = {
    "it": {"che", "di", "il", "la", "per", "non", "una", "con", "del", "come"},
    "en": {"the", "of", "and", "to", "that", "for", "with", "this", "from", "your"},
}

LEVEL_ORDER = {"errore": 0, "avviso": 1, "info": 2}


@dataclass
class Finding:
    level: str      # errore | avviso | info
    code: str
    message: str

    def __str__(self) -> str:
        symbol = {"errore": "✗", "avviso": "!", "info": "·"}[self.level]
        return f"  {symbol} [{self.code}] {self.message}"


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    def add(self, level: str, code: str, message: str) -> None:
        self.findings.append(Finding(level, code, message))

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "errore"]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "avviso"]

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "stats": self.stats,
            "findings": [{"level": f.level, "code": f.code, "message": f.message} for f in self.findings],
        }

    def render(self) -> str:
        lines = ["Controllo qualità e conformità KDP", "=" * 42]
        for finding in sorted(self.findings, key=lambda f: LEVEL_ORDER[f.level]):
            lines.append(str(finding))
        lines.append("-" * 42)
        lines.append(
            f"  {len(self.errors)} errori, {len(self.warnings)} avvisi — "
            + ("PRONTO PER IL CARICAMENTO" if self.ok else "NON CARICARE: risolvi gli errori")
        )
        return "\n".join(lines)


def _normalized_sentences(text: str) -> list[str]:
    plain = mdlite.plain_text(text).lower()
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", plain) if len(s.split()) >= 8]


def check_manuscript(
    spec: BookSpec,
    outline: Outline,
    chapters: list[tuple[int, str, str]],
    report: Report | None = None,
) -> Report:
    report = report or Report()
    if not chapters:
        report.add("errore", "MANOSCRITTO", "Nessun capitolo trovato: esegui prima `write`.")
        return report

    total_words = 0
    all_sentences: list[tuple[int, str]] = []

    for number, title, markdown in chapters:
        words = mdlite.count_words(markdown)
        total_words += words
        plan = next((c for c in outline.chapters if c.number == number), None)

        for pattern in PLACEHOLDER_PATTERNS:
            if re.search(pattern, markdown, flags=re.I):
                report.add(
                    "errore",
                    "SEGNAPOSTO",
                    f"Capitolo {number} ({title}): contiene testo segnaposto o meta-commento "
                    f"che corrisponde a /{pattern}/.",
                )
                break

        if words < 300:
            report.add("errore", "LUNGHEZZA", f"Capitolo {number} troppo corto: {words} parole.")
        elif plan and plan.target_words:
            deviation = (words - plan.target_words) / plan.target_words
            if abs(deviation) > 0.25:
                report.add(
                    "avviso",
                    "LUNGHEZZA",
                    f"Capitolo {number}: {words} parole contro {plan.target_words} previste "
                    f"({deviation:+.0%}).",
                )

        sections = len(re.findall(r"^##\s+", markdown, flags=re.M))
        if sections == 0 and words > 900:
            report.add(
                "avviso",
                "STRUTTURA",
                f"Capitolo {number}: nessuna sezione `##` in {words} parole, lettura pesante.",
            )

        if spec.wants_exercises and plan and plan.role == "chapter":
            if not re.search(r"^##\s+In pratica", markdown, flags=re.M | re.I):
                report.add(
                    "avviso",
                    "ESERCIZI",
                    f"Capitolo {number}: manca la sezione finale `## In pratica`.",
                )

        if not spec.is_medium_content:
            righe_da_riempire = FILL_LINE.findall(markdown)
            if righe_da_riempire:
                report.add(
                    "avviso",
                    "CATEGORIA",
                    f"Capitolo {number}: {len(righe_da_riempire)} righe da riempire a mano "
                    "in un libro full-content, dove il valore sta tutto nel testo.",
                )

        for opener in BANNED_OPENERS:
            if re.search(re.escape(opener), markdown, flags=re.I):
                report.add(
                    "avviso",
                    "FORMULE",
                    f"Capitolo {number}: contiene la formula da evitare «{opener}».",
                )

        for sentence in _normalized_sentences(markdown):
            all_sentences.append((number, sentence))

        if plan and plan.title.strip().lower() != title.strip().lower():
            report.add(
                "avviso",
                "TITOLI",
                f"Capitolo {number}: titolo nel file «{title}» diverso dalla scaletta «{plan.title}».",
            )

    # Frasi ripetute fra capitoli diversi
    counter = Counter(sentence for _, sentence in all_sentences)
    duplicates = [s for s, n in counter.items() if n > 1]
    if duplicates:
        sample = duplicates[0][:90]
        report.add(
            "avviso",
            "RIPETIZIONI",
            f"{len(duplicates)} frasi lunghe ripetute più volte nel libro. Esempio: «{sample}…»",
        )

    # Lingua
    words_lower = mdlite.plain_text(" ".join(c[2] for c in chapters)).lower().split()
    if words_lower:
        expected = STOPWORDS.get(spec.language, set())
        hits = sum(1 for w in words_lower[:4000] if w in expected)
        if hits / max(len(words_lower[:4000]), 1) < 0.02:
            report.add(
                "avviso",
                "LINGUA",
                f"Il testo potrebbe non essere in {spec.language}: poche parole funzione attese.",
            )

    report.stats["parole_totali"] = total_words
    report.stats["capitoli"] = len(chapters)
    report.stats["parole_per_capitolo"] = int(total_words / max(len(chapters), 1))
    return report


def check_print_pdf(
    spec: BookSpec, pdf_path: Path, pages: int, report: Report | None = None
) -> Report:
    report = report or Report()
    for problem in kdpspecs.validate_page_count(pages, spec.paper):
        report.add("errore", "PAGINE", problem)

    if pages % 2 == 1:
        report.add(
            "avviso",
            "PAGINE",
            f"{pages} pagine: un numero dispari lascia l'ultima facciata spaiata.",
        )

    gutter = kdpspecs.gutter_margin_in(pages)
    geo = kdpspecs.page_geometry(spec.trim, pages)
    if geo.inner_margin / kdpspecs.INCH < gutter:
        report.add(
            "errore",
            "MARGINI",
            f"Margine interno {geo.inner_margin/kdpspecs.INCH:.3f}\" inferiore al minimo KDP {gutter}\".",
        )
    if geo.outer_margin / kdpspecs.INCH < kdpspecs.MIN_OUTSIDE_MARGIN_NO_BLEED:
        report.add("errore", "MARGINI", "Margine esterno inferiore a 0.25\".")

    if not pdf_path.exists():
        report.add("errore", "PDF", f"File non trovato: {pdf_path}")
        return report

    report.stats["pagine"] = pages
    report.stats["dorso_in"] = round(kdpspecs.spine_width_in(pages, spec.paper), 4)
    _inspect_pdf(spec, pdf_path, report)
    return report


def _inspect_pdf(spec: BookSpec, pdf_path: Path, report: Report) -> None:
    """Controlli sul PDF reale (dimensione pagine, font incorporati).

    Richiede PyMuPDF; se non è installato il controllo viene saltato.
    """
    try:
        import pymupdf
    except ImportError:
        report.add(
            "info",
            "PDF",
            "PyMuPDF non installato: saltato il controllo su font incorporati e "
            "dimensioni pagina (pip install pymupdf).",
        )
        return

    expected_w, expected_h = kdpspecs.trim_size_in(spec.trim)
    document = pymupdf.open(pdf_path)
    bad_sizes = 0
    not_embedded: set[str] = set()
    for page in document:
        rect = page.rect
        if (
            abs(rect.width / kdpspecs.INCH - expected_w) > 0.01
            or abs(rect.height / kdpspecs.INCH - expected_h) > 0.01
        ):
            bad_sizes += 1
        for font in page.get_fonts(full=False):
            # (xref, ext, type, basefont, name, encoding)
            if font[1] == "n/a" or font[0] == 0:
                not_embedded.add(font[3])
    document.close()

    if bad_sizes:
        report.add(
            "errore",
            "FORMATO",
            f"{bad_sizes} pagine non corrispondono al formato {spec.trim} pollici.",
        )
    if not_embedded:
        report.add(
            "errore",
            "FONT",
            "Font non incorporati (KDP li rifiuta): " + ", ".join(sorted(not_embedded)),
        )
    else:
        report.add("info", "FONT", "Tutti i font risultano incorporati nel PDF.")


def check_cover(cover_info: dict, report: Report | None = None) -> Report:
    """Controlli sulla copertina, in particolare sull'immagine dell'autore."""
    report = report or Report()
    image = (cover_info or {}).get("immagine")
    if not image:
        return report
    dpi = int(image.get("effective_dpi", 0))
    if dpi < 200:
        report.add(
            "errore",
            "IMMAGINE",
            f"Immagine di copertina a {dpi} DPI reali: sotto i 200 KDP la stampa esce "
            f"sgranata. Serve un originale di almeno "
            f"{image['prepared_px'][0]}x{image['prepared_px'][1]} px.",
        )
    elif dpi < 300:
        report.add(
            "avviso",
            "IMMAGINE",
            f"Immagine di copertina a {dpi} DPI reali invece di 300: stampabile, ma i "
            "dettagli fini si ammorbidiscono.",
        )
    else:
        report.add("info", "IMMAGINE", f"Immagine di copertina a {dpi} DPI: adatta alla stampa.")
    for warning in image.get("warnings", []):
        if "Risoluzione insufficiente" not in warning and "sotto i" not in warning:
            report.add("avviso", "IMMAGINE", warning)
    return report


def check_metadata(metadata: dict, spec: BookSpec, report: Report | None = None) -> Report:
    report = report or Report()
    title = metadata.get("title", spec.title)
    subtitle = metadata.get("subtitle", spec.subtitle)
    if len(title) + len(subtitle) > 200:
        report.add(
            "errore",
            "METADATI",
            f"Titolo + sottotitolo = {len(title) + len(subtitle)} caratteri: il limite KDP è 200.",
        )

    description = metadata.get("description_html", "")
    if len(description) > 4000:
        report.add(
            "errore", "METADATI", f"Descrizione di {len(description)} caratteri: limite 4000."
        )
    if description and len(description) < 600:
        report.add(
            "avviso",
            "METADATI",
            "Descrizione molto corta: le schede più efficaci stanno fra 1.200 e 2.500 caratteri.",
        )

    keywords = metadata.get("keywords", [])
    if len(keywords) != 7:
        report.add(
            "avviso", "KEYWORD", f"{len(keywords)} keyword invece delle 7 previste da KDP."
        )
    title_words = {w.lower() for w in re.findall(r"\w+", f"{title} {subtitle}")}
    for keyword in keywords:
        if len(keyword) > 50:
            report.add("errore", "KEYWORD", f"Keyword troppo lunga (>50 caratteri): «{keyword}»")
        overlap = {w.lower() for w in re.findall(r"\w+", keyword)} & title_words
        if len(overlap) == len(re.findall(r"\w+", keyword)):
            report.add(
                "avviso",
                "KEYWORD",
                f"«{keyword}» ripete solo parole già presenti nel titolo: spreca uno slot.",
            )

    banned = ["bestseller", "best seller", "il migliore", "gratis", "offerta", "sconto"]
    for term in banned:
        if re.search(rf"\b{re.escape(term)}\b", description, flags=re.I):
            report.add(
                "errore",
                "METADATI",
                f"La descrizione contiene «{term}»: KDP vieta claim promozionali e sul prezzo.",
            )
    return report


def merge(*reports: Report) -> Report:
    merged = Report()
    for report in reports:
        merged.findings.extend(report.findings)
        merged.stats.update(report.stats)
    return merged

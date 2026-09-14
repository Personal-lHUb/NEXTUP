"""Parser di un sottoinsieme di Markdown, sufficiente per un libro.

Supporta: titoli (`#`, `##`, `###`), paragrafi, elenchi puntati e numerati,
citazioni (`>`), stacchi (`---`), grassetto, corsivo e `codice`.
Volutamente non supporta tabelle, immagini e HTML: sono le cose che rompono
l'impaginazione di un libro generato in automatico.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from html import escape


@dataclass
class Heading:
    level: int
    text: str


@dataclass
class Paragraph:
    text: str


@dataclass
class BulletList:
    items: list[str] = field(default_factory=list)
    ordered: bool = False


@dataclass
class Quote:
    text: str


@dataclass
class Rule:
    pass


Block = Heading | Paragraph | BulletList | Quote | Rule

_BULLET_RE = re.compile(r"^\s*[-*+]\s+(.*)$")
_ORDERED_RE = re.compile(r"^\s*\d+[.)]\s+(.*)$")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_RULE_RE = re.compile(r"^\s*([-*_])\1{2,}\s*$")


def parse(markdown: str) -> list[Block]:
    blocks: list[Block] = []
    paragraph: list[str] = []
    list_items: list[str] = []
    list_ordered = False
    quote: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            blocks.append(Paragraph(" ".join(paragraph).strip()))
            paragraph = []

    def flush_list() -> None:
        nonlocal list_items
        if list_items:
            blocks.append(BulletList(items=list_items, ordered=list_ordered))
            list_items = []

    def flush_quote() -> None:
        nonlocal quote
        if quote:
            blocks.append(Quote(" ".join(quote).strip()))
            quote = []

    def flush_all() -> None:
        flush_paragraph()
        flush_list()
        flush_quote()

    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()

        if not line.strip():
            flush_all()
            continue

        if _RULE_RE.match(line):
            flush_all()
            blocks.append(Rule())
            continue

        heading = _HEADING_RE.match(line)
        if heading:
            flush_all()
            blocks.append(Heading(level=len(heading.group(1)), text=heading.group(2).strip()))
            continue

        if line.lstrip().startswith(">"):
            flush_paragraph()
            flush_list()
            quote.append(line.lstrip()[1:].strip())
            continue

        ordered = _ORDERED_RE.match(line)
        if ordered:
            flush_paragraph()
            flush_quote()
            if list_items and not list_ordered:
                flush_list()
            list_ordered = True
            list_items.append(ordered.group(1).strip())
            continue

        bullet = _BULLET_RE.match(line)
        if bullet:
            flush_paragraph()
            flush_quote()
            if list_items and list_ordered:
                flush_list()
            list_ordered = False
            list_items.append(bullet.group(1).strip())
            continue

        flush_list()
        flush_quote()
        paragraph.append(line.strip())

    flush_all()
    return blocks


def inline_to_markup(text: str, mono_font: str = "Courier") -> str:
    """Converte il markup inline nel mini-HTML accettato da ReportLab."""
    out = escape(text, quote=False)
    out = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", out, flags=re.S)
    out = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", out, flags=re.S)
    out = re.sub(r"(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?![\w_])", r"<i>\1</i>", out, flags=re.S)
    out = re.sub(r"`(.+?)`", rf'<font face="{mono_font}">\1</font>', out, flags=re.S)
    # Virgolette dritte -> virgolette tipografiche (solo per le doppie).
    out = re.sub(r'"([^"]*)"', "“\\1”", out)
    return out


def plain_text(markdown: str) -> str:
    """Testo senza markup, per conteggi e controlli qualità."""
    text = re.sub(r"`{1,3}", "", markdown)
    text = re.sub(r"[*_#>]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def count_words(markdown: str) -> int:
    return len(plain_text(markdown).split())


def strip_title(markdown: str) -> tuple[str, str]:
    """Separa il titolo `# ...` iniziale dal corpo del capitolo."""
    lines = markdown.lstrip().splitlines()
    if lines and lines[0].startswith("# "):
        return lines[0][2:].strip(), "\n".join(lines[1:]).strip()
    return "", markdown.strip()

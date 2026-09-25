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


@dataclass
class Figure:
    """Un'immagine nel testo, con quello che deve mostrare.

    `descrizione` non è una didascalia: è il **committente** dell'immagine.
    È il testo che `immagini` trasforma in prompt, ed è quello che resta nel
    manoscritto quando il file non c'è ancora — così il libro si impagina
    comunque e il conteggio pagine tiene già il posto della figura.

    La didascalia, se serve, si scrive nella riga dopo, fra parentesi tonde.
    """

    descrizione: str
    percorso: str
    didascalia: str = ""


Block = Heading | Paragraph | BulletList | Quote | Rule | Figure

_BULLET_RE = re.compile(r"^\s*[-*+]\s+(.*)$")
_ORDERED_RE = re.compile(r"^\s*\d+[.)]\s+(.*)$")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_RULE_RE = re.compile(r"^\s*([-*_])\1{2,}\s*$")
_FIGURE_RE = re.compile(r"^\s*!\[(?P<descrizione>[^\]]*)\]\((?P<percorso>[^)]+)\)\s*$")


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

        figura = _FIGURE_RE.match(line)
        if figura:
            flush_all()
            blocks.append(
                Figure(
                    descrizione=figura.group("descrizione").strip(),
                    percorso=figura.group("percorso").strip(),
                )
            )
            continue

        # La didascalia sta fra parentesi sulla riga subito dopo la figura.
        # Attaccarla lì invece che dentro `![...]` tiene separate due cose che
        # servono a due mestieri: quello che l'immagine deve mostrare (il
        # prompt) e quello che il lettore legge sotto (la didascalia).
        if line.strip().startswith("(") and line.strip().endswith(")") and blocks:
            if isinstance(blocks[-1], Figure) and not paragraph and not blocks[-1].didascalia:
                blocks[-1].didascalia = line.strip()[1:-1].strip()
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


def inline_to_markup(text: str, mono_font: str = "") -> str:
    """Converte il markup inline nel mini-HTML accettato da ReportLab.

    `mono_font` accetta solo una famiglia già registrata da `typography`. Senza,
    il testo fra apici inversi resta nel font del corpo, senza apici: Courier è
    un font PostScript standard, ReportLab non lo incorpora (misurato: zero
    `/FontFile`) e il controllo di stampa rifiuta il PDF. Il corsivo non è
    un'alternativa: confonderebbe il codice in linea con l'enfasi `*…*`.
    """
    out = escape(text, quote=False)
    # Le virgolette tipografiche vanno messe **prima** dei tag. Fatte dopo,
    # questa stessa sostituzione arricciava anche gli apici di `face="..."`:
    # ReportLab non riusciva più a leggere il nome del font e l'impaginazione
    # moriva a manoscritto già scritto e pagato, per un solo apice inverso in
    # un capitolo qualunque.
    out = re.sub(r'"([^"]*)"', "“\\1”", out)
    out = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", out, flags=re.S)
    out = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", out, flags=re.S)
    out = re.sub(r"(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?![\w_])", r"<i>\1</i>", out, flags=re.S)
    codice = rf'<font face="{mono_font}">\1</font>' if mono_font else r"\1"
    return re.sub(r"`(.+?)`", codice, out, flags=re.S)


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

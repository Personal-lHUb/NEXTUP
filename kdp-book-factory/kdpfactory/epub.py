"""Generazione dell'EPUB 3 (edizione Kindle) senza dipendenze esterne.

KDP accetta l'EPUB per l'ebook e lo converte internamente. L'interno del
cartaceo e l'ebook nascono dallo stesso Markdown, quindi restano allineati.
"""

from __future__ import annotations

import uuid
import zipfile
from datetime import date
from html import escape
from pathlib import Path

from . import mdlite
from .i18n import L, part_label
from .models import BookSpec, Outline

CSS = """\
@page { margin: 1em; }
body { font-family: serif; line-height: 1.5; margin: 0 1em; hyphens: auto; }
h1 { font-size: 1.6em; margin: 2em 0 0.2em; text-align: center; page-break-before: always; }
h2 { font-size: 1.2em; margin: 1.6em 0 0.4em; }
h3 { font-size: 1.05em; margin: 1.2em 0 0.3em; }
p { margin: 0; text-indent: 1.2em; text-align: justify; }
p.first, h1 + p, h2 + p, h3 + p { text-indent: 0; }
p.first { margin-top: 0.6em; }
blockquote { margin: 1em 1.5em; font-style: italic; color: #444; }
ul, ol { margin: 0.8em 0 0.8em 1.4em; }
li { margin-bottom: 0.3em; text-align: left; }
hr.scene { border: 0; text-align: center; margin: 1.2em 0; }
hr.scene:after { content: "* * *"; }
.titlepage { text-align: center; margin-top: 25%; }
.titlepage h1 { page-break-before: avoid; font-size: 2em; }
.titlepage .author { margin-top: 2em; font-variant: small-caps; }
.copyright { font-size: 0.85em; color: #333; margin-top: 3em; }
.part { text-align: center; margin-top: 30%; }
.part h1 { page-break-before: avoid; margin-top: 0.4em; }
.part .label { text-indent: 0; text-align: center; letter-spacing: 0.15em; text-transform: uppercase; }
"""


def _xhtml(title: str, body: str, language: str) -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="{language}" lang="{language}">
<head><meta charset="utf-8"/><title>{escape(title)}</title>
<link rel="stylesheet" type="text/css" href="style.css"/></head>
<body>
{body}
</body>
</html>
"""


def markdown_to_xhtml(markdown: str) -> str:
    out: list[str] = []
    first_para = True
    for block in mdlite.parse(markdown):
        if isinstance(block, mdlite.Heading):
            level = min(max(block.level, 2), 4)
            out.append(f"<h{level}>{_inline(block.text)}</h{level}>")
            first_para = True
        elif isinstance(block, mdlite.Paragraph):
            css_class = ' class="first"' if first_para else ""
            out.append(f"<p{css_class}>{_inline(block.text)}</p>")
            first_para = False
        elif isinstance(block, mdlite.BulletList):
            tag = "ol" if block.ordered else "ul"
            items = "".join(f"<li>{_inline(item)}</li>" for item in block.items)
            out.append(f"<{tag}>{items}</{tag}>")
            first_para = True
        elif isinstance(block, mdlite.Quote):
            out.append(f"<blockquote><p>{_inline(block.text)}</p></blockquote>")
            first_para = True
        elif isinstance(block, mdlite.Rule):
            out.append('<hr class="scene"/>')
            first_para = True
    return "\n".join(out)


def _inline(text: str) -> str:
    import re

    out = escape(text, quote=False)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out, flags=re.S)
    out = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", out, flags=re.S)
    out = re.sub(r"(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?![\w_])", r"<em>\1</em>", out, flags=re.S)
    out = re.sub(r"`(.+?)`", r"<code>\1</code>", out, flags=re.S)
    return out


def build_epub(
    spec: BookSpec,
    outline: Outline,
    chapters: list[tuple[int, str, str]],
    output: Path,
    *,
    author_bio: str = "",
    year: int | None = None,
) -> dict:
    year = year or spec.year or date.today().year
    lang = spec.language
    book_id = f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, 'kdpfactory/' + spec.slug)}"
    output.parent.mkdir(parents=True, exist_ok=True)

    documents: list[tuple[str, str, str]] = []  # (filename, title, xhtml)

    title_body = f"""<div class="titlepage">
<h1>{escape(spec.title)}</h1>
{f'<p class="first"><em>{escape(spec.subtitle)}</em></p>' if spec.subtitle else ''}
<p class="author first">{escape(spec.author)}</p>
</div>
<div class="copyright">
<p class="first">© {year} {escape(spec.author)}. {L(lang, 'copyright')}</p>
<p class="first">{L(lang, 'copyright_body')}</p>
<p class="first">{L(lang, 'ai_disclosure')}</p>
<p class="first">{L(lang, 'disclaimer_title')}: {L(lang, 'disclaimer_body')}</p>
</div>"""
    documents.append(("title.xhtml", spec.title, _xhtml(spec.title, title_body, lang)))

    # L'indice di navigazione: con le parti, i capitoli stanno dentro la loro.
    voci: list[tuple[str, str, list[tuple[str, str]]]] = []
    dentro_una_parte = False
    for number, chapter_title, markdown in chapters:
        apertura = outline.part_opening(number)
        if apertura:
            indice, parte = apertura
            etichetta = part_label(lang, indice)
            nome = f"part{indice:02d}.xhtml"
            titolo = f"{etichetta} — {parte.title}"
            body = (
                f'<div class="part">\n<p class="label">{escape(etichetta)}</p>\n'
                f"<h1>{escape(parte.title)}</h1>\n</div>"
            )
            documents.append((nome, titolo, _xhtml(titolo, body, lang)))
            voci.append((nome, titolo, []))
            dentro_una_parte = True
        nome = f"ch{number:02d}.xhtml"
        body = f"<h1>{escape(chapter_title)}</h1>\n{markdown_to_xhtml(markdown)}"
        documents.append((nome, chapter_title, _xhtml(chapter_title, body, lang)))
        if dentro_una_parte:
            voci[-1][2].append((nome, chapter_title))
        else:
            voci.append((nome, chapter_title, []))

    if author_bio:
        body = f"<h1>{escape(L(lang, 'about_author'))}</h1>\n{markdown_to_xhtml(author_bio)}"
        about = L(lang, "about_author")
        documents.append(("author.xhtml", about, _xhtml(about, body, lang)))
        voci.append(("author.xhtml", about, []))

    review_body = (
        f"<h1>{escape(L(lang, 'review_title'))}</h1>\n<p class=\"first\">{escape(L(lang, 'review_text'))}</p>"
    )
    review = L(lang, "review_title")
    documents.append(("review.xhtml", review, _xhtml(review, review_body, lang)))
    voci.append(("review.xhtml", review, []))

    def _voce(name: str, title: str, figli: list[tuple[str, str]]) -> str:
        link = f'<a href="{name}">{escape(title)}</a>'
        if not figli:
            return f"      <li>{link}</li>"
        sotto = "\n".join(f'          <li><a href="{n}">{escape(t)}</a></li>' for n, t in figli)
        return f"      <li>{link}\n        <ol>\n{sotto}\n        </ol>\n      </li>"

    nav_items = "\n".join(_voce(*voce) for voce in voci)
    nav = _xhtml(
        L(lang, "toc"),
        f"""<nav epub:type="toc" xmlns:epub="http://www.idpf.org/2007/ops" id="toc">
    <h1>{escape(L(lang, 'toc'))}</h1>
    <ol>
{nav_items}
    </ol>
  </nav>""",
        lang,
    )

    manifest = "\n".join(
        f'    <item id="{Path(name).stem}" href="{name}" media-type="application/xhtml+xml"/>'
        for name, _, _ in documents
    )
    spine = "\n".join(f'    <itemref idref="{Path(name).stem}"/>' for name, _, _ in documents)
    description = escape((outline.back_cover or spec.promise or spec.topic)[:900])
    subjects = "\n".join(
        f"    <dc:subject>{escape(keyword)}</dc:subject>" for keyword in spec.keywords
    )

    opf = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid"
         prefix="rendition: http://www.idpf.org/vocab/rendition/#">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="bookid">{book_id}</dc:identifier>
    <dc:title>{escape(spec.title)}</dc:title>
{subjects}
    <dc:creator>{escape(spec.author)}</dc:creator>
    <dc:language>{lang}</dc:language>
    <dc:date>{year}-01-01</dc:date>
    <dc:description>{description}</dc:description>
    <dc:rights>© {year} {escape(spec.author)}</dc:rights>
    <meta property="dcterms:modified">{date.today().isoformat()}T00:00:00Z</meta>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="css" href="style.css" media-type="text/css"/>
{manifest}
  </manifest>
  <spine>
{spine}
  </spine>
</package>
"""

    with zipfile.ZipFile(output, "w") as zf:
        # `mimetype` deve essere il primo file e non compresso.
        zf.writestr(
            zipfile.ZipInfo("mimetype"), "application/epub+zip", compress_type=zipfile.ZIP_STORED
        )
        zf.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
""",
            compress_type=zipfile.ZIP_DEFLATED,
        )
        zf.writestr("OEBPS/content.opf", opf, compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr("OEBPS/nav.xhtml", nav, compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr("OEBPS/style.css", CSS, compress_type=zipfile.ZIP_DEFLATED)
        for name, _, content in documents:
            zf.writestr(f"OEBPS/{name}", content, compress_type=zipfile.ZIP_DEFLATED)

    return {"epub": str(output), "documents": len(documents)}

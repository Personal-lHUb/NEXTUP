"""L'avvertenza della pagina di copyright può essere quella del libro.

Dal rodaggio di household-bills: il controllo di conformità ha chiesto per un
libro sulle bollette un'avvertenza che dica di che consulenza non si tratta
(legale, finanziaria, fiscale, sul credito) e che le regole cambiano da stato a
stato. L'avvertenza era una sola per tutti i libri, scritta in `i18n`, senza
nessun campo per cambiarla.
"""

import tempfile
import unittest
import zipfile
from pathlib import Path

from kdpfactory import epub, typeset
from kdpfactory.i18n import L
from kdpfactory.models import BookSpec, ChapterPlan, Outline

PROPRIA = (
    "This book explains how household bills work. It is not legal, financial, tax or "
    "credit advice, and rules and programs vary by state and change over time."
)


def _libro(**extra) -> tuple[BookSpec, Outline, list]:
    spec = BookSpec(slug="t", title="Bills in Order", author="A. Author", language="en", **extra)
    piani = [ChapterPlan(number=1, title="One", role="chapter")]
    capitoli = [(1, "One", "# One\n\n" + "A plain sentence about bills. " * 40 + "\n")]
    return spec, Outline(title=spec.title, chapters=piani), capitoli


class TestAvvertenzaDelLibro(unittest.TestCase):
    def _testo_pdf(self, spec, outline, capitoli) -> str:
        import fitz

        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "x.pdf"
            typeset.typeset(spec, outline, capitoli, pdf)
            with fitz.open(pdf) as doc:
                return " ".join(" ".join(pagina.get_text().split()) for pagina in doc)

    def test_senza_campo_resta_quella_generica(self):
        testo = self._testo_pdf(*_libro())
        generica = " ".join(L("en", "disclaimer_body").split())
        self.assertIn(generica[:60], testo)

    def test_con_il_campo_il_pdf_stampa_quella_del_libro(self):
        testo = self._testo_pdf(*_libro(disclaimer=PROPRIA))
        self.assertIn("It is not legal, financial, tax or credit advice", testo)
        self.assertNotIn(" ".join(L("en", "disclaimer_body").split())[:60], testo)

    def test_anche_l_epub_la_porta(self):
        spec, outline, capitoli = _libro(disclaimer=PROPRIA)
        with tempfile.TemporaryDirectory() as tmp:
            uscita = Path(tmp) / "x.epub"
            epub.build_epub(spec, outline, capitoli, uscita)
            with zipfile.ZipFile(uscita) as z:
                pagine = " ".join(z.read(n).decode("utf-8") for n in z.namelist() if n.endswith(".xhtml"))
        self.assertIn("It is not legal, financial, tax or credit advice", pagine)

    def test_avvertenza_lunga_a_paragrafi_su_una_pagina(self):
        # b0gjr36xwt: cinque paragrafi, ~300 parole; qui un po' di più. Con la
        # calata fissa il colophon finiva sulla pagina dopo.
        lunga = "\n\n".join(
            f"Paragraph {n} of the notice. " + "Laws and policies differ by state and change. " * 9
            for n in range(1, 6)
        )
        spec, outline, capitoli = _libro(disclaimer=lunga, trim="6x9")
        self.assertEqual(len(spec.disclaimer_paragraphs), 5)
        import fitz

        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "x.pdf"
            typeset.typeset(spec, outline, capitoli, pdf)
            with fitz.open(pdf) as doc:
                pagine = [" ".join(p.get_text().split()) for p in doc]
        con_avvertenza = [i for i, p in enumerate(pagine) if "of the notice" in p]
        self.assertEqual(len(set(con_avvertenza)), 1, "il colophon deve stare su una pagina")
        pagina = pagine[con_avvertenza[0]]
        self.assertIn("Paragraph 1 of the notice", pagina)
        self.assertIn("Paragraph 5 of the notice", pagina)
        self.assertIn(L("en", "printed_by").split()[0], pagina)

    def test_epub_un_paragrafo_per_blocco(self):
        spec, outline, capitoli = _libro(disclaimer="First block.\n\nSecond block.")
        with tempfile.TemporaryDirectory() as tmp:
            uscita = Path(tmp) / "x.epub"
            epub.build_epub(spec, outline, capitoli, uscita)
            with zipfile.ZipFile(uscita) as z:
                titolo = z.read(next(n for n in z.namelist() if n.endswith("title.xhtml"))).decode()
        self.assertIn("First block.</p>", titolo)
        self.assertIn('<p class="first">Second block.</p>', titolo)

    def test_book_json_accetta_il_campo(self):
        spec = BookSpec.from_dict({"slug": "t", "title": "T", "disclaimer": PROPRIA})
        self.assertEqual(spec.disclaimer, PROPRIA)
        self.assertIn("disclaimer", spec.to_dict())


if __name__ == "__main__":
    unittest.main()

"""Le note in riquadro, e le citazioni che tengono i loro capoversi.

b0gjr36xwt mette a confronto, capitolo per capitolo, una nota clinica debole e
la stessa nota riscritta. La nota riscritta ha tre capoversi (anamnesi,
valutazione, piano), separati nel testo da una riga `>` vuota: il parser li
fondeva in un blocco solo, e in stampa il piano cominciava a metà riga.
L'autore ha scelto le note in riquadro, come nei libri del genere.
"""

import tempfile
import unittest
import zipfile
from pathlib import Path

from kdpfactory import epub, mdlite, typeset
from kdpfactory.models import BookSpec, ChapterPlan, Outline

NOTA = (
    "Prima del confronto.\n\n"
    "> 79F on apixaban, fell at home. Exam: GCS 15.\n"
    ">\n"
    "> Assessment: mechanical fall, scalp contusion.\n"
    ">\n"
    "> Plan: home with daughter; return precautions given.\n\n"
    "Dopo il confronto.\n"
)


def _libro(**extra):
    spec = BookSpec(slug="t", title="Hard Calls", author="A. Author", language="en", **extra)
    outline = Outline(title=spec.title, chapters=[ChapterPlan(number=1, title="One", role="chapter")])
    return spec, outline, [(1, "One", "# One\n\n" + NOTA)]


class TestCapoversi(unittest.TestCase):
    def test_la_riga_vuota_separa_i_capoversi(self):
        citazione = next(b for b in mdlite.parse(NOTA) if isinstance(b, mdlite.Quote))
        self.assertEqual(len(citazione.paragrafi), 3)
        self.assertTrue(citazione.paragrafi[2].startswith("Plan:"))
        self.assertIn("Assessment:", citazione.text)

    def test_una_citazione_costruita_a_mano_ha_il_suo_capoverso(self):
        self.assertEqual(mdlite.Quote("solo").paragrafi, ["solo"])


class TestRiquadro(unittest.TestCase):
    def _pdf(self, **extra):
        import fitz

        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "x.pdf"
            typeset.typeset(*_libro(**extra), pdf)
            with fitz.open(pdf) as doc:
                pagina = next(p for p in doc if "Assessment:" in p.get_text())
                righe = [r.strip() for r in pagina.get_text().splitlines()]
                grigi = [
                    d for d in pagina.get_drawings()
                    if d.get("fill") and all(abs(c - 0xEF / 255) < 0.01 for c in d["fill"])
                ]
        return righe, grigi

    def test_il_piano_comincia_a_capo_anche_senza_riquadro(self):
        righe, grigi = self._pdf()
        self.assertTrue(any(r.startswith("Plan:") for r in righe))
        self.assertTrue(any(r.startswith("Assessment:") for r in righe))
        self.assertEqual(grigi, [])

    def test_con_quote_box_la_nota_sta_in_un_riquadro(self):
        righe, grigi = self._pdf(quote_box=True)
        self.assertTrue(any(r.startswith("Plan:") for r in righe))
        self.assertEqual(len(grigi), 1, "un riquadro solo per i tre capoversi")

    def test_anche_l_epub_ha_il_riquadro(self):
        with tempfile.TemporaryDirectory() as tmp:
            uscita = Path(tmp) / "x.epub"
            epub.build_epub(*_libro(quote_box=True), uscita)
            with zipfile.ZipFile(uscita) as z:
                testo = " ".join(z.read(n).decode() for n in z.namelist() if n.endswith(".xhtml"))
        self.assertIn('<blockquote class="nota">', testo)
        self.assertIn('<p class="first">Plan: home with daughter', testo)


if __name__ == "__main__":
    unittest.main()

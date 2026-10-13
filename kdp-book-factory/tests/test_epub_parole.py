"""Le parole chiave dell'EPUB sono quelle della scheda prodotto.

Da b0gjr36xwt: la scheda della fase 6 aveva sostituito le sette parole chiave
della prima stesura, ma l'EPUB scriveva ancora quelle di `book.json` nei
`dc:subject`, fra cui una che prometteva la protezione che il libro nega.
"""

import tempfile
import unittest
import zipfile
from pathlib import Path

from kdpfactory import epub
from kdpfactory.models import BookSpec, ChapterPlan, Outline


def _opf(**extra) -> str:
    spec = BookSpec(slug="t", title="T", author="A", language="en",
                    keywords=["old keyword one", "old keyword two"])
    outline = Outline(title="T", chapters=[ChapterPlan(number=1, title="One", role="chapter")])
    capitoli = [(1, "One", "# One\n\nA sentence.\n")]
    with tempfile.TemporaryDirectory() as tmp:
        uscita = Path(tmp) / "x.epub"
        epub.build_epub(spec, outline, capitoli, uscita, **extra)
        with zipfile.ZipFile(uscita) as z:
            return z.read(next(n for n in z.namelist() if n.endswith(".opf"))).decode()


class TestParoleChiaveEpub(unittest.TestCase):
    def test_vincono_quelle_della_scheda(self):
        opf = _opf(keywords=["listing keyword"])
        self.assertIn("<dc:subject>listing keyword</dc:subject>", opf)
        self.assertNotIn("old keyword one", opf)

    def test_senza_scheda_restano_quelle_del_libro(self):
        opf = _opf()
        self.assertIn("<dc:subject>old keyword one</dc:subject>", opf)


if __name__ == "__main__":
    unittest.main()

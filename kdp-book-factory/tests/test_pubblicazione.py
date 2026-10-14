"""Il pacchetto di pubblicazione: i file finali in git e la scheda di caricamento.

Da b0gjr36xwt: `build/` non entra in git, e i file finali devono restare. Dal
14 ottobre 2026 su KDP carica l'autore (Cowork non apre i siti di Amazon), e
un libro su un tema escluso non ha pacchetto.
"""

import json
import tempfile
import unittest
from pathlib import Path

from kdpfactory import decisioni, kdpspecs, pubblicazione
from kdpfactory.models import BookProject, BookSpec

PAGINE = 180


def _spec(**extra) -> BookSpec:
    base = dict(slug="libro", title="Hard Calls", subtitle="A Casebook", author="A. Author",
                language="en", trim="6x9", paper="cream", price_eur=21.99,
                keywords=["one", "two"], categories=["GAMES & ACTIVITIES / Puzzles"])
    base.update(extra)
    return BookSpec(**base)


class TestPubblicazione(unittest.TestCase):
    def setUp(self):
        import fitz

        self.tmp = tempfile.TemporaryDirectory()
        self.radice = Path(self.tmp.name)
        (self.radice / ".git").mkdir()
        self.project = BookProject(self.radice / "kdp-book-factory" / "books" / "libro")
        build = self.project.build_dir
        build.mkdir(parents=True)
        spec = _spec()
        interno = fitz.open()
        for _ in range(4):
            interno.new_page(width=6 * 72, height=9 * 72)
        interno.save(build / "libro-interno.pdf")
        larghezza, altezza = kdpspecs.cover_size_in("6x9", PAGINE, "cream")
        copertina = fitz.open()
        pagina = copertina.new_page(width=larghezza * 72, height=altezza * 72)
        fronte = (kdpspecs.BLEED_IN + 6 + kdpspecs.spine_width_in(PAGINE, "cream")) * 72
        pagina.draw_rect(fitz.Rect(0, 0, fronte, altezza * 72), color=None, fill=(1, 0, 0))
        pagina.draw_rect(fitz.Rect(fronte, 0, larghezza * 72, altezza * 72), color=None, fill=(0, 0, 1))
        copertina.save(build / "libro-copertina.pdf")
        (build / "libro.epub").write_bytes(b"PK epub")
        (build / "kdp-listing.md").write_text("# scheda\n", encoding="utf-8")
        (build / "metadata.json").write_text(json.dumps({
            "description_html": "<p><b>Hook.</b></p>", "keywords": ["k1", "k2"],
            "categories": ["GAMES & ACTIVITIES / Puzzles"],
            "prezzi": [{"marketplace": "amazon.com", "costo_stampa": 3.14, "royalty_per_copia": 10.06}],
        }), encoding="utf-8")
        (build / "qa-report.json").write_text(json.dumps({"ok": True}), encoding="utf-8")
        self.project.update_state(build={"pagine": PAGINE}, cover={"immagine": {"file": "x"}})
        for chiave in pubblicazione.DECISIONI:
            decisioni.scegli(self.project, chiave, "scelta")
        self.spec = spec

    def tearDown(self):
        self.tmp.cleanup()

    def _prepara(self, **extra):
        spec = _spec(**extra)
        return spec, pubblicazione.prepara(self.project, spec, "Owner/Repo", "ramo")

    def test_pronto_quando_il_cancello_e_chiuso(self):
        self.assertEqual(pubblicazione.problemi(self.project, self.spec), [])

    def test_qa_con_errori_ferma_il_pacchetto(self):
        (self.project.build_dir / "qa-report.json").write_text('{"ok": false}', encoding="utf-8")
        self.assertTrue(any("qa" in p for p in pubblicazione.problemi(self.project, self.spec)))
        with self.assertRaises(ValueError):
            self._prepara()

    def test_senza_illustrazione_della_direzione_scelta_non_si_carica(self):
        (self.project.root / "copertina-direzioni.json").write_text(json.dumps(
            {"direzioni": [{"nome": "uno"}], "scelta": {"direzione": 1}}), encoding="utf-8")
        self.project.update_state(cover={"immagine": None})
        problemi = pubblicazione.problemi(self.project, self.spec)
        self.assertTrue(any("tipografica" in p for p in problemi), problemi)

    def test_manca_una_decisione_dell_autore(self):
        voci = [v for v in decisioni.leggi(self.project) if v["chiave"] != "prezzo"]
        decisioni.salva(self.project, voci)
        self.assertIn("manca la decisione dell'autore sul prezzo",
                      pubblicazione.problemi(self.project, self.spec))

    def test_pacchetto_con_kindle(self):
        spec, manifest = self._prepara(price_ebook=7.99)
        cartella = pubblicazione.cartella(self.project)
        self.assertIn("libro-copertina-kindle.jpg", manifest["file"])
        voce = manifest["file"]["libro-interno.pdf"]
        self.assertEqual(voce["url"], "https://raw.githubusercontent.com/Owner/Repo/ramo/"
                                      "kdp-book-factory/books/libro/pubblicazione/libro-interno.pdf")
        self.assertEqual(voce["byte"], (cartella / "libro-interno.pdf").stat().st_size)
        self.assertEqual(manifest["prezzo_kindle"], 7.99)

        from PIL import Image
        with Image.open(cartella / "libro-copertina-kindle.jpg") as immagine:
            self.assertEqual(immagine.height, pubblicazione.KINDLE_ALTEZZA)
            self.assertAlmostEqual(immagine.width / immagine.height, 6 / 9, places=2)
            rosso, verde, blu = immagine.getpixel((immagine.width // 2, immagine.height // 2))
        self.assertGreater(blu, 200, "il JPG dell'ebook è il fronte, non la quarta")
        self.assertLess(rosso, 60)

        scheda = (cartella / pubblicazione.SCHEDA).read_text(encoding="utf-8")
        self.assertIn("Black & white interior with cream paper", scheda)
        self.assertIn("No Bleed", scheda)
        self.assertIn("List price: 21.99 USD", scheda)
        self.assertIn("List price: 7.99 USD", scheda)
        self.assertIn("Mai «Publish Your Kindle eBook»", scheda)
        self.assertIn("<p><b>Hook.</b></p>", scheda)

    def test_senza_prezzo_kindle_solo_cartaceo(self):
        _, manifest = self._prepara()
        self.assertNotIn("libro-copertina-kindle.jpg", manifest["file"])
        scheda = (pubblicazione.cartella(self.project) / pubblicazione.SCHEDA).read_text(encoding="utf-8")
        self.assertNotIn("Kindle eBook Pricing", scheda)

    def test_un_tema_escluso_non_ha_pacchetto(self):
        spec = _spec(categories=["MEDICAL / Nursing / Issues"])
        problemi = pubblicazione.problemi(self.project, spec)
        self.assertTrue(any("tema escluso" in p for p in problemi), problemi)
        with self.assertRaises(ValueError):
            pubblicazione.prepara(self.project, spec, "Owner/Repo", "ramo")
        self.assertFalse(pubblicazione.cartella(self.project).exists())

    def test_niente_richiesta_a_cowork(self):
        self._prepara(price_ebook=7.99)
        nomi = {f.name for f in pubblicazione.cartella(self.project).iterdir()}
        self.assertFalse(any(n.startswith("cowork-") for n in nomi), nomi)

    def test_book_json_accetta_i_campi_nuovi(self):
        spec = BookSpec.from_dict({"slug": "x", "title": "X", "price_ebook": 7.99, "cover_finish": "glossy"})
        self.assertEqual(spec.validate(), [])
        self.assertTrue(BookSpec(slug="x", title="X", cover_finish="lucida").validate())


if __name__ == "__main__":
    unittest.main()

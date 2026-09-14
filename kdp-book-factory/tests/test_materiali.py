"""Test dei materiali dell'autore: brief degli argomenti e immagine di copertina."""

import tempfile
import unittest
from pathlib import Path

from kdpfactory import coverimage, kdpspecs, prompts, qa
from kdpfactory.cli import create_author_inputs
from kdpfactory.cover import build_cover
from kdpfactory.models import BookProject, BookSpec

PIXELS_6x9 = (round(6.125 * 300), round(9.25 * 300))


def make_image(path: Path, size=(2400, 3600), color=(40, 80, 140)) -> Path:
    from PIL import Image

    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path, quality=92)
    return path


class TestBrief(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = BookProject(Path(self.tmp.name) / "libro")
        self.project.ensure_dirs()
        self.spec = BookSpec(slug="libro", title="Libro di Prova")
        self.spec.save(self.project.spec_path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_init_crea_i_punti_di_ingresso(self):
        create_author_inputs(self.project, self.spec)
        self.assertTrue(self.project.brief_path.exists())
        self.assertTrue((self.project.assets_dir / "LEGGIMI.md").exists())

    def test_modulo_vuoto_non_conta_come_compilato(self):
        create_author_inputs(self.project, self.spec)
        self.assertFalse(self.project.brief_is_filled())

    def test_brief_compilato(self):
        self.project.brief_path.write_text(
            "# Argomenti\n\n## Di che cosa parla\nCome organizzare la giornata quando il "
            "lavoro arriva a ondate, per chi lavora da solo e viene interrotto di continuo "
            "dai clienti ogni mezz'ora.\n\n## Argomenti da coprire\n"
            "- perché le liste di cose da fare falliscono con il lavoro a ondate\n"
            "- come si sceglie il blocco della mattina\n",
            encoding="utf-8",
        )
        self.assertTrue(self.project.brief_is_filled())

    def test_commenti_e_segnaposto_non_vengono_letti(self):
        self.project.brief_path.write_text(
            "<!-- istruzioni da non leggere -->\n"
            "## Argomenti\n"
            "(suggerimento del modulo)\n"
            "- primo argomento vero\n",
            encoding="utf-8",
        )
        brief = self.project.read_brief()
        self.assertNotIn("istruzioni da non leggere", brief)
        self.assertNotIn("suggerimento del modulo", brief)
        self.assertIn("primo argomento vero", brief)

    def test_il_brief_arriva_nel_prompt(self):
        self.project.brief_path.write_text(
            "## Argomenti\n- misurare il lavoro senza contare le ore\n", encoding="utf-8"
        )
        spec = self.project.load_spec()
        bible = prompts.book_bible(spec)
        self.assertIn("misurare il lavoro senza contare le ore", bible)
        self.assertIn("ARGOMENTI RICHIESTI DALL'AUTORE", bible)

    def test_il_brief_non_finisce_in_book_json(self):
        spec = BookSpec(slug="x", title="X", brief="testo del brief")
        self.assertNotIn("brief", spec.to_dict())


class TestImmagineDiCopertina(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.project = BookProject(self.root / "libro")
        self.project.ensure_dirs()
        self.spec = BookSpec(slug="libro", title="Libro di Prova", author="Autore")

    def tearDown(self):
        self.tmp.cleanup()

    def test_trova_l_immagine_in_assets(self):
        make_image(self.project.assets_dir / "copertina.jpg")
        self.assertIsNotNone(self.project.cover_image_path(self.spec))

    def test_ignora_file_con_altri_nomi(self):
        make_image(self.project.assets_dir / "foto-autore.jpg")
        self.assertIsNone(self.project.cover_image_path(self.spec))

    def test_percorso_esplicito_nella_scheda(self):
        path = make_image(self.root / "altrove" / "immagine.png")
        spec = BookSpec(slug="libro", title="T", cover_image=str(path))
        self.assertEqual(self.project.cover_image_path(spec), path)

    def test_prepara_alle_misure_esatte(self):
        source = make_image(self.project.assets_dir / "copertina.jpg")
        report = coverimage.prepare(source, self.root / "out.jpg", "6x9")
        self.assertEqual(report.prepared_px, PIXELS_6x9)
        self.assertGreaterEqual(report.effective_dpi, 300)
        self.assertFalse(report.upscaled)
        self.assertEqual(report.warnings, [])

    def test_immagine_piccola_viene_segnalata(self):
        source = make_image(self.project.assets_dir / "copertina.jpg", size=(600, 900))
        report = coverimage.prepare(source, self.root / "out.jpg", "6x9")
        self.assertTrue(report.upscaled)
        self.assertLess(report.effective_dpi, coverimage.MIN_ACCEPTABLE_DPI)
        self.assertTrue(any("Risoluzione insufficiente" in w for w in report.warnings))

    def test_proporzioni_molto_diverse_vengono_segnalate(self):
        source = make_image(self.project.assets_dir / "copertina.jpg", size=(4000, 1500))
        report = coverimage.prepare(source, self.root / "out.jpg", "6x9")
        self.assertTrue(any("proporzioni" in w for w in report.warnings))

    def test_la_velatura_scurisce_i_bordi(self):
        from PIL import Image

        source = make_image(self.project.assets_dir / "copertina.jpg", color=(200, 200, 200))
        coverimage.prepare(source, self.root / "out.jpg", "6x9", enhance=False)
        with Image.open(self.root / "out.jpg") as prepared:
            width, height = prepared.size
            alto = prepared.getpixel((width // 2, 5))
            centro = prepared.getpixel((width // 2, height // 2))
            basso = prepared.getpixel((width // 2, height - 5))
        self.assertLess(alto[0], centro[0] - 60, "il bordo alto deve risultare più scuro")
        self.assertLess(basso[0], centro[0] - 60, "il bordo basso deve risultare più scuro")

    def test_copertina_con_immagine(self):
        source = make_image(self.project.assets_dir / "copertina.jpg")
        output = self.project.build_dir / "copertina.pdf"
        info = build_cover(self.spec, 120, output, image_path=source)
        self.assertTrue(output.exists())
        self.assertIsNotNone(info["immagine"])
        expected = kdpspecs.cover_size_in(self.spec.trim, 120, self.spec.paper)
        self.assertAlmostEqual(info["cover_width_in"], expected[0], places=3)
        self.assertTrue((self.project.build_dir / "libro-copertina-immagine.jpg").exists())

    def test_copertina_senza_immagine_resta_tipografica(self):
        info = build_cover(self.spec, 120, self.project.build_dir / "copertina.pdf")
        self.assertIsNone(info["immagine"])

    def test_qa_blocca_la_bassa_risoluzione(self):
        report = qa.check_cover(
            {"immagine": {"effective_dpi": 150, "prepared_px": [1838, 2775], "warnings": []}}
        )
        self.assertFalse(report.ok)
        self.assertTrue(any(f.code == "IMMAGINE" for f in report.errors))

    def test_qa_accetta_i_300_dpi(self):
        report = qa.check_cover(
            {"immagine": {"effective_dpi": 320, "prepared_px": [1838, 2775], "warnings": []}}
        )
        self.assertTrue(report.ok)


if __name__ == "__main__":
    unittest.main()

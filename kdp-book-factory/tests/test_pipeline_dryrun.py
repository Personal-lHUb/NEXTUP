"""Test end-to-end della pipeline in modalità dry-run (nessuna chiamata API)."""

import tempfile
import unittest
import zipfile
from pathlib import Path

from kdpfactory import kdpspecs, pipeline, planner, qa, writer
from kdpfactory.llm import LLMClient, LLMConfig
from kdpfactory.models import BookProject, BookSpec


class TestPipelineDryRun(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name) / "libro-di-prova"
        cls.project = BookProject(root)
        cls.project.ensure_dirs()
        cls.spec = BookSpec(
            slug="libro-di-prova",
            title="Libro di Prova",
            subtitle="Sottotitolo di prova",
            author="Autore Test",
            topic="collaudo della pipeline",
            audience="sviluppatori",
            target_pages=80,
            chapters=6,
        )
        cls.spec.save(cls.project.spec_path)
        cls.client = LLMClient(LLMConfig(dry_run=True, verbose=False))
        budget = planner.build_budget(cls.spec)
        cls.outline = writer.generate_outline(cls.spec, cls.client, budget)
        cls.outline.save(cls.project.outline_path)
        writer.write_chapters(cls.project, cls.spec, cls.outline, cls.client)
        cls.result = pipeline.build_until_in_range(
            cls.project, cls.spec, cls.outline, cls.client, max_iterations=4
        )
        pipeline.build_package(cls.project, cls.spec, cls.outline, cls.result)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_scaletta_contiene_intro_e_conclusione(self):
        ruoli = [c.role for c in self.outline.chapters]
        self.assertEqual(ruoli[0], "intro")
        self.assertEqual(ruoli[-1], "conclusion")
        self.assertEqual(ruoli.count("chapter"), 6)

    def test_tutti_i_capitoli_scritti(self):
        self.assertEqual(len(self.project.chapter_files()), len(self.outline.chapters))

    def test_pagine_nell_intervallo_richiesto(self):
        low, high = pipeline.acceptance_window(self.spec)
        self.assertTrue(
            low <= self.result.pages <= high,
            f"{self.result.pages} pagine fuori da {low}-{high} "
            f"(storico: {self.result.history})",
        )

    def test_pagine_nei_limiti_di_progetto(self):
        self.assertGreaterEqual(self.result.pages, kdpspecs.PROJECT_MIN_PAGES)
        self.assertLessEqual(self.result.pages, kdpspecs.PROJECT_MAX_PAGES)

    def test_numero_di_pagine_pari(self):
        self.assertEqual(self.result.pages % 2, 0)

    def test_pdf_interno_creato(self):
        self.assertTrue(self.result.interior_pdf.exists())
        self.assertGreater(self.result.interior_pdf.stat().st_size, 20_000)

    def test_copertina_ha_le_misure_giuste(self):
        self.assertTrue(self.result.cover_pdf.exists())
        expected = kdpspecs.cover_size_in(self.spec.trim, self.result.pages, self.spec.paper)
        info = self.project.load_state()["cover"]
        self.assertAlmostEqual(info["cover_width_in"], expected[0], places=3)
        self.assertAlmostEqual(info["cover_height_in"], expected[1], places=3)

    def test_epub_valido(self):
        self.assertTrue(self.result.epub_path.exists())
        with zipfile.ZipFile(self.result.epub_path) as zf:
            names = zf.namelist()
            self.assertEqual(names[0], "mimetype")
            self.assertEqual(zf.read("mimetype").decode(), "application/epub+zip")
            self.assertIn("META-INF/container.xml", names)
            self.assertIn("OEBPS/content.opf", names)
            self.assertIn("OEBPS/nav.xhtml", names)
            self.assertTrue(zf.getinfo("mimetype").compress_type == zipfile.ZIP_STORED)

    def test_qa_blocca_il_testo_segnaposto(self):
        report = pipeline.run_qa(self.project, self.spec, self.outline, self.result)
        self.assertFalse(report.ok)
        self.assertTrue(any(f.code == "SEGNAPOSTO" for f in report.errors))

    def test_qa_non_segnala_font_mancanti(self):
        report = qa.Report()
        qa.check_print_pdf(self.spec, self.result.interior_pdf, self.result.pages, report)
        font_errors = [f for f in report.errors if f.code == "FONT"]
        self.assertEqual(font_errors, [], f"font non incorporati: {font_errors}")

    def test_qa_metadati(self):
        report = qa.check_metadata(
            {
                "title": "T" * 150,
                "subtitle": "S" * 100,
                "description_html": "<p>bestseller garantito</p>",
                "keywords": ["una", "due"],
            },
            self.spec,
        )
        codes = {f.code for f in report.errors}
        self.assertIn("METADATI", codes)


if __name__ == "__main__":
    unittest.main()

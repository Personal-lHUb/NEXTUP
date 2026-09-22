"""Test end-to-end della pipeline in modalità dry-run (nessuna chiamata API)."""

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from kdpfactory import backup, kdpspecs, pipeline, planner, qa, writer
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
        # I test non devono scrivere nella cartella di backup del progetto.
        backup.configure(enabled=False)
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
        backup.configure(enabled=True, directory=None)
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

    def test_il_titolo_della_scheda_deve_essere_quello_stampato(self):
        """In copertina è stampato `spec.title`; su KDP si incolla la scheda.

        Amazon li confronta: se non coincidono il libro non passa la revisione.
        Il sistema non sceglie per te quale dei due sia giusto — lo dice e basta.
        """
        report = qa.check_metadata({"title": "Un Altro Titolo", "subtitle": ""}, self.spec)
        diversi = [f for f in report.errors if "copertina stampa" in f.message]
        self.assertEqual(len(diversi), 1)
        self.assertIn(self.spec.title, diversi[0].message)

        uguale = qa.check_metadata({"title": self.spec.title, "subtitle": ""}, self.spec)
        self.assertEqual([f for f in uguale.errors if "copertina stampa" in f.message], [])

    def test_in_prova_a_secco_i_due_titoli_coincidono(self):
        """Il segnaposto non deve far scattare il controllo vero a ogni dry-run.

        Il titolo si riprende dal prompt, dove la scheda del libro lo scrive in
        chiaro: un «Titolo segnaposto» non coincide mai con quello stampato in
        copertina, e trasformerebbe ogni prova a secco in un falso allarme.
        """
        from kdpfactory import prompts
        from kdpfactory.llm import dry_run_text

        richiesta = prompts.metadata_prompt(self.spec, self.outline, "estratto del libro")
        prodotto = json.loads(dry_run_text(richiesta, label="metadati kdp (json)"))
        self.assertEqual(prodotto["title"], self.spec.title)


if __name__ == "__main__":
    unittest.main()


class TestCicloDiImpaginazione(unittest.TestCase):
    """Il ciclo che converge sulle pagine, con l'impaginazione simulata.

    Ogni capitolo si apre su pagina dispari e occupa quindi un numero pari di
    pagine; la correzione scala tutti i capitoli insieme e li fa scavallare
    insieme, così il totale salta di due pagine per capitolo. Su un libro con
    molti capitoli il salto diventa più largo della finestra di accettazione e
    l'obiettivo ci finisce dentro: continuare a riscrivere ricompra il libro
    senza avvicinarlo.
    """

    def esegui(self, pagine: list[int], target_pages: int, capitoli: int = 8):
        """Fa girare `build_until_in_range` su un'impaginazione scriptata."""
        from unittest import mock

        from kdpfactory.models import ChapterPlan, Outline
        from kdpfactory.typeset import TypesetResult

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        backup.configure(enabled=False)
        self.addCleanup(backup.configure, enabled=True, directory=None)
        project = BookProject(Path(tmp.name) / "libro")
        project.ensure_dirs()
        spec = BookSpec(slug="libro", title="Libro", topic="t", target_pages=target_pages)
        chapters = [
            ChapterPlan(number=i, title=f"C{i}", summary="s", target_words=1700)
            for i in range(1, capitoli + 1)
        ]
        outline = Outline(title="Libro", chapters=chapters)
        outline.save(project.outline_path)

        sequenza = iter(pagine)
        def finto_typeset(*_args, **_kwargs):
            n = next(sequenza)
            return TypesetResult(
                pdf_path=project.build_dir / "x.pdf", pages=n, words=n * 250,
                words_by_chapter={c.number: 1700 for c in chapters},
            )

        client = LLMClient(LLMConfig(dry_run=True, verbose=False))
        with mock.patch.object(pipeline, "typeset_only", finto_typeset), \
             mock.patch.object(pipeline.writer, "revise_length", lambda *a, **k: [1]):
            return pipeline.build_until_in_range(
                project, spec, outline, client, max_iterations=4, tolerance=0.05
            )

    def test_si_ferma_quando_il_salto_supera_la_finestra(self):
        """240 pagine, 32 capitoli: 288 → 220 salta 68 pagine su una finestra di 12."""
        result = self.esegui([288, 220, 288, 220], target_pages=240, capitoli=32)
        self.assertEqual(result.iterations, 2)
        self.assertEqual(result.pages, 220)
        self.assertFalse(result.in_range)

    def test_si_tiene_l_ultima_misura_anche_quando_e_la_peggiore(self):
        """Limite dichiarato del freno, non una svista.

        Su `[288, 220]` l'ultima misura è anche la migliore, ed è facile
        credere che il freno scelga la migliore. Non è così: `revise_length` ha
        già riscritto i capitoli su disco, quindi tornare a 226 costerebbe
        un'altra riscrittura dell'intero libro. Il freno serve a non spendere
        un giro inutile, non a scegliere.
        """
        result = self.esegui([226, 300], target_pages=240, capitoli=32)
        self.assertEqual(result.iterations, 2)
        self.assertEqual(result.pages, 300)        # 226 era più vicino: si perde
        self.assertFalse(result.in_range)

    def test_un_libro_che_converge_non_viene_toccato(self):
        """Salti piccoli: il ciclo lavora come prima e rientra."""
        result = self.esegui([86, 84], target_pages=80, capitoli=8)
        self.assertEqual(result.iterations, 2)
        self.assertEqual(result.pages, 84)
        self.assertTrue(result.in_range)

    def test_il_terzo_giro_si_fa_se_il_salto_resta_stretto(self):
        """Tre impaginazioni sono legittime finché il libro si muove piano."""
        result = self.esegui([100, 96, 92, 81], target_pages=80, capitoli=8)
        self.assertGreaterEqual(result.iterations, 3)

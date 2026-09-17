"""Test del sistema di copertine: misure, testi, verifica sul PDF reale.

Nessuno di questi test chiede un giudizio estetico: verificano le sole cose
che di una copertina si possono misurare — e che sono anche quelle che
decidono se in miniatura il libro si vede o no.
"""

import tempfile
import unittest
from pathlib import Path

from kdpfactory import backup, cover, coverdesign, kdpspecs
from kdpfactory.agents import AgentContext, get_agent
from kdpfactory.coverdesign import (
    CoverCopy,
    FrontBox,
    contrast_ratio,
    fit_size,
    luminance,
    title_block_size,
    tracked_width,
)
from kdpfactory.models import BookSpec
from kdpfactory.typography import register_family

INCH = kdpspecs.INCH


def demo_spec(**overrides) -> BookSpec:
    data = dict(
        slug="prova-copertina",
        title="Twelve Carriages, One Killer",
        subtitle="Thirteen cases aboard a night express: one pencil, no guesswork",
        author="Iris Vane",
        language="en",
        topic="deduction puzzles",
        audience="solvers",
        promise="thirteen cases solvable with a pencil",
        genre="non-fiction",
        target_pages=100,
        trim="6x9",
        paper="white",
    )
    data.update(overrides)
    return BookSpec(**data)


def demo_box(trim="6x9") -> FrontBox:
    trim_w, trim_h = kdpspecs.trim_size_in(trim)
    bleed = kdpspecs.BLEED_IN * INCH
    return FrontBox(
        x0=100.0,
        y0=0.0,
        width=trim_w * INCH + bleed,
        height=trim_h * INCH + 2 * bleed,
        trim_width=trim_w * INCH,
        trim_height=trim_h * INCH,
        bleed=bleed,
        safe=coverdesign.SAFE_MARGIN_IN * INCH,
    )


class TestColore(unittest.TestCase):
    def test_luminanza_agli_estremi(self):
        self.assertAlmostEqual(luminance("#000000"), 0.0, places=4)
        self.assertAlmostEqual(luminance("#FFFFFF"), 1.0, places=4)

    def test_contrasto_massimo_e_simmetrico(self):
        self.assertAlmostEqual(contrast_ratio("#000000", "#FFFFFF"), 21.0, places=2)
        self.assertEqual(
            round(contrast_ratio("#10243A", "#FFFFFF"), 6),
            round(contrast_ratio("#FFFFFF", "#10243A"), 6),
        )

    def test_ogni_palette_supera_le_soglie_del_sistema(self):
        for palette in coverdesign.PALETTES:
            with self.subTest(palette=palette.name):
                self.assertGreaterEqual(palette.title_contrast, coverdesign.MIN_CONTRAST)
                self.assertTrue(palette.pops_on_white)

    def test_palette_scelta_dallautore_ha_la_precedenza(self):
        spec = demo_spec(cover_theme="bosco")
        self.assertEqual(coverdesign.pick_palette(spec, "enigmi").name, "bosco")

    def test_scelta_automatica_stabile_e_dentro_il_genere(self):
        spec = demo_spec(cover_theme="auto")
        first = coverdesign.pick_palette(spec, "enigmi")
        self.assertEqual(first.name, coverdesign.pick_palette(spec, "enigmi").name)
        self.assertIn("enigmi", first.genres)


class TestMisure(unittest.TestCase):
    def setUp(self):
        self.font = register_family("sans")

    def test_la_spaziatura_entra_nella_larghezza(self):
        plain = tracked_width("ABCDE", self.font, 20)
        spaced = tracked_width("ABCDE", self.font, 20, tracking=2.0)
        self.assertAlmostEqual(spaced - plain, 8.0, places=6)

    def test_fit_size_tiene_conto_della_spaziatura(self):
        wide = fit_size("DEDUCTION PUZZLES", self.font, 200, 40, 6)
        tracked = fit_size("DEDUCTION PUZZLES", self.font, 200, 40, 6, tracking_ratio=0.28)
        self.assertLess(tracked, wide)
        self.assertLessEqual(tracked_width("DEDUCTION PUZZLES", self.font, tracked,
                                           tracked * 0.28), 200)

    def test_il_titolo_sta_nella_misura_e_resta_leggibile(self):
        box = demo_box()
        copy = CoverCopy(title="Twelve Carriages, One Killer")
        size, lines = title_block_size(copy, self.font, box)
        self.assertLessEqual(len(lines), 3)
        for line in lines:
            self.assertLessEqual(tracked_width(line, self.font, size), box.measure)
        self.assertGreaterEqual(size * 0.72 / box.trim_height, coverdesign.MIN_TITLE_CAP_RATIO)

    def test_titolo_lunghissimo_non_scende_sotto_la_soglia(self):
        box = demo_box()
        copy = CoverCopy(title="Una guida completa e ragionata alla manutenzione preventiva")
        size, _ = title_block_size(copy, self.font, box)
        # il pavimento è esatto: si arriva a toccarlo, mai a scenderci sotto
        self.assertGreaterEqual(
            size * 0.72 / box.trim_height, coverdesign.MIN_TITLE_CAP_RATIO - 1e-9
        )

    def test_il_centro_e_quello_dellarea_rifilata(self):
        box = demo_box()
        self.assertAlmostEqual(box.center, box.x0 + box.trim_width / 2)


class TestTesti(unittest.TestCase):
    def test_il_gancio_e_la_prima_proposizione_del_sottotitolo(self):
        copy = coverdesign.derive_copy(demo_spec(), genre="non-fiction")
        self.assertEqual(copy.hook, "Thirteen cases aboard a night express")

    def test_sottotitolo_senza_separatori_viene_troncato(self):
        spec = demo_spec(subtitle="x" * 90)
        self.assertTrue(coverdesign.derive_copy(spec).hook.endswith("…"))

    def test_metadata_ha_la_precedenza_sul_sottotitolo(self):
        copy = coverdesign.derive_copy(
            demo_spec(), {"cover_hook": "E se il colpevole fosse già sceso?"}
        )
        self.assertEqual(copy.hook, "E se il colpevole fosse già sceso?")

    def test_il_genere_porta_il_proprio_occhiello(self):
        self.assertEqual(coverdesign.derive_copy(demo_spec(), genre="enigmi").kicker,
                         "DEDUCTION PUZZLES")
        self.assertEqual(coverdesign.derive_copy(demo_spec(), genre="fiction").kicker, "")


class TestCopertinaGenerata(unittest.TestCase):
    """La verifica gira sul PDF vero: è l'unica che conta davvero."""

    @classmethod
    def setUpClass(cls):
        backup.configure(enabled=False)
        cls.tmp = tempfile.TemporaryDirectory()
        cls.pages = 120
        cls.spec = demo_spec()
        cls.output = Path(cls.tmp.name) / "copertina.pdf"
        cls.info = cover.build_cover(
            cls.spec,
            cls.pages,
            cls.output,
            back_cover_text="Tredici casi. Una matita.\n\nNessuna congettura.",
            bullets=["12 casi", "una soluzione sola"],
            genre="enigmi",
            copy=CoverCopy(
                title=cls.spec.title,
                kicker="DEDUCTION PUZZLES",
                hook="Can you name the killer in every carriage?",
                stats="13 CASES · 908 SUSPECTS · 1 MASTERMIND",
                badge="Every case has exactly one solution",
                author=cls.spec.author,
            ),
        )

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()
        backup.configure(enabled=True)

    def test_la_verifica_non_trova_problemi(self):
        self.assertEqual(self.info["verifica"]["problemi"], [])

    def test_titolo_dentro_larea_di_sicurezza(self):
        self.assertTrue(self.info["verifica"]["dentro_area_sicura"])

    def test_dimensioni_del_pdf_come_le_vuole_kdp(self):
        expected = kdpspecs.cover_size_in(self.spec.trim, self.pages, self.spec.paper)
        self.assertAlmostEqual(self.info["cover_width_in"], expected[0], places=3)
        self.assertAlmostEqual(self.info["cover_height_in"], expected[1], places=3)

    def test_la_spaziatura_non_dilata_il_testo_disegnato_dopo(self):
        """`Tc` resta nello stato grafico: se non lo si azzera, ogni riga
        disegnata dopo un testo tracciato esce più larga di quanto calcolato."""
        import pymupdf

        font = register_family("sans")
        trim_w, _ = kdpspecs.trim_size_in(self.spec.trim)
        spine = kdpspecs.spine_width_in(self.pages, self.spec.paper)
        front_x0 = (kdpspecs.BLEED_IN + trim_w + spine) * INCH

        document = pymupdf.open(self.output)
        page = document[0]
        title_words = {word.upper() for word in self.spec.title.split() if len(word) > 3}
        checked = 0
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span["text"].strip()
                    if span["bbox"][0] < front_x0 or text.upper() not in title_words:
                        continue
                    drawn = span["bbox"][2] - span["bbox"][0]
                    from reportlab.pdfbase import pdfmetrics

                    expected = pdfmetrics.stringWidth(text, font, span["size"])
                    self.assertAlmostEqual(drawn, expected, delta=1.0)
                    checked += 1
        document.close()
        self.assertGreater(checked, 0, "nessuna riga di titolo trovata da misurare")

    def test_la_miniatura_inquadra_solo_larea_rifilata(self):
        import pymupdf

        thumbnail = self.info["miniatura"]
        self.assertIsNotNone(thumbnail)
        pixmap = pymupdf.Pixmap(thumbnail)
        trim_w, trim_h = kdpspecs.trim_size_in(self.spec.trim)
        # un pixel di arrotondamento: la larghezza in punti non è intera
        self.assertAlmostEqual(pixmap.width, coverdesign.THUMBNAIL_WIDTH_PX, delta=1)
        self.assertAlmostEqual(pixmap.height / pixmap.width, trim_h / trim_w, places=2)


class TestAgenteCopertina(unittest.TestCase):
    def setUp(self):
        backup.configure(enabled=False)
        self.tmp = tempfile.TemporaryDirectory()
        self.spec = demo_spec()
        self.pdf = Path(self.tmp.name) / "copertina.pdf"
        self.info = cover.build_cover(self.spec, 120, self.pdf, genre="enigmi")

    def tearDown(self):
        self.tmp.cleanup()
        backup.configure(enabled=True)

    def context(self, **copy) -> AgentContext:
        return AgentContext(
            spec=self.spec, pages=120, cover_pdf=self.pdf, cover_copy=copy
        )

    def test_senza_copertina_lo_dichiara(self):
        ctx = AgentContext(spec=self.spec, pages=120, cover_pdf=None)
        findings = get_agent("copertina").run(ctx).findings
        self.assertEqual(findings[0].category, "copertina mancante")

    def test_rivendicazione_vietata_e_bloccante(self):
        findings = get_agent("copertina").run(
            self.context(title=self.spec.title, hook="Il bestseller numero uno?")
        ).findings
        blocking = [f for f in findings if f.category == "rivendicazione vietata"]
        self.assertEqual(len(blocking), 1)
        self.assertEqual(blocking[0].severity, "bloccante")

    def test_gancio_mancante_segnalato(self):
        findings = get_agent("copertina").run(self.context(title=self.spec.title)).findings
        self.assertTrue(any(f.category == "ciclo aperto" for f in findings))

    def test_gancio_con_domanda_non_segnalato(self):
        findings = get_agent("copertina").run(
            self.context(title=self.spec.title, hook="Can you name the killer?")
        ).findings
        self.assertFalse(any(f.category == "ciclo aperto" for f in findings))

    def test_numeri_in_lettere_segnalati(self):
        findings = get_agent("copertina").run(
            self.context(title=self.spec.title, hook="Can you?", stats="TREDICI CASI")
        ).findings
        self.assertTrue(any(f.category == "numeri in lettere" for f in findings))

    def test_copertina_conforme_non_produce_bloccanti(self):
        findings = get_agent("copertina").run(
            self.context(
                title=self.spec.title,
                hook="Can you name the killer in every carriage?",
                stats="13 CASES · 908 SUSPECTS",
            )
        ).findings
        self.assertFalse([f for f in findings if f.severity == "bloccante"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

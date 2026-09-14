"""Test delle specifiche KDP, del planner e del parser Markdown."""

import unittest

from kdpfactory import kdpspecs, mdlite, planner
from kdpfactory.models import BookSpec, ChapterPlan


class TestKdpSpecs(unittest.TestCase):
    def test_gutter_scala_con_le_pagine(self):
        self.assertEqual(kdpspecs.gutter_margin_in(60), 0.375)
        self.assertEqual(kdpspecs.gutter_margin_in(150), 0.375)
        self.assertEqual(kdpspecs.gutter_margin_in(151), 0.5)
        self.assertEqual(kdpspecs.gutter_margin_in(240), 0.5)

    def test_spine_width(self):
        self.assertAlmostEqual(kdpspecs.spine_width_in(100, "cream"), 0.25, places=4)
        self.assertAlmostEqual(kdpspecs.spine_width_in(100, "white"), 0.2252, places=4)

    def test_cover_size(self):
        width, height = kdpspecs.cover_size_in("6x9", 200, "cream")
        # 2 x 6" + dorso 0.5" + 0.25" di abbondanza
        self.assertAlmostEqual(width, 12.75, places=3)
        self.assertAlmostEqual(height, 9.25, places=3)

    def test_limiti_di_progetto(self):
        self.assertEqual(kdpspecs.validate_page_count(120, "cream"), [])
        self.assertTrue(kdpspecs.validate_page_count(40, "cream"))
        self.assertTrue(kdpspecs.validate_page_count(300, "cream"))

    def test_testo_sul_dorso(self):
        self.assertFalse(kdpspecs.spine_text_allowed(78))
        self.assertTrue(kdpspecs.spine_text_allowed(79))

    def test_geometria_rispetta_i_minimi(self):
        for pages in (60, 120, 240):
            geo = kdpspecs.page_geometry("6x9", pages)
            self.assertGreaterEqual(
                geo.inner_margin / kdpspecs.INCH, kdpspecs.gutter_margin_in(pages)
            )
            self.assertGreaterEqual(
                geo.outer_margin / kdpspecs.INCH, kdpspecs.MIN_OUTSIDE_MARGIN_NO_BLEED
            )


class TestPlanner(unittest.TestCase):
    def spec(self, **kwargs) -> BookSpec:
        base = dict(slug="t", title="Titolo", topic="argomento")
        base.update(kwargs)
        return BookSpec(**base)

    def test_budget_cresce_con_le_pagine(self):
        piccolo = planner.build_budget(self.spec(target_pages=60))
        grande = planner.build_budget(self.spec(target_pages=240))
        self.assertLess(piccolo.total_words, grande.total_words)
        self.assertGreater(piccolo.total_words, 5000)

    def test_parole_per_pagina_dipendono_dal_corpo(self):
        piccolo = planner.words_per_page(self.spec(body_font_size=10, leading=13))
        grande = planner.words_per_page(self.spec(body_font_size=13, leading=18))
        self.assertGreater(piccolo, grande)

    def test_distribuzione_include_intro_e_conclusione(self):
        spec = self.spec(target_pages=120)
        budget = planner.build_budget(spec)
        words = planner.distribute_words(budget, spec)
        self.assertEqual(len(words), budget.chapters + 2)
        self.assertLess(words[0], words[1])   # l'introduzione è più corta
        self.assertLess(words[-1], words[1])  # la conclusione pure

    def test_ricalibrazione_riduce_se_troppe_pagine(self):
        spec = self.spec(target_pages=120)
        chapters = [ChapterPlan(number=i, title=f"C{i}", target_words=2000) for i in range(1, 11)]
        calibration = planner.recalibrate(
            measured_pages=180,
            measured_words=20000,
            spec=spec,
            chapters=chapters,
            chapter_words={c.number: 2000 for c in chapters},
        )
        self.assertLess(calibration.scale, 1.0)
        self.assertTrue(all(v < 2000 for v in calibration.per_chapter.values()))

    def test_ricalibrazione_aumenta_se_poche_pagine(self):
        spec = self.spec(target_pages=200)
        chapters = [ChapterPlan(number=i, title=f"C{i}", target_words=1500) for i in range(1, 11)]
        calibration = planner.recalibrate(
            measured_pages=90,
            measured_words=15000,
            spec=spec,
            chapters=chapters,
            chapter_words={c.number: 1500 for c in chapters},
        )
        self.assertGreater(calibration.scale, 1.0)


class TestMarkdown(unittest.TestCase):
    def test_parsing_blocchi(self):
        blocks = mdlite.parse(
            "# Titolo\n\nUn paragrafo.\n\n## Sezione\n\n- uno\n- due\n\n1. primo\n\n> citazione\n\n---\n"
        )
        kinds = [type(b).__name__ for b in blocks]
        self.assertEqual(
            kinds,
            ["Heading", "Paragraph", "Heading", "BulletList", "BulletList", "Quote", "Rule"],
        )
        self.assertTrue(blocks[4].ordered)
        self.assertFalse(blocks[3].ordered)

    def test_markup_inline_e_escape(self):
        out = mdlite.inline_to_markup("**forte** e *corsivo* con <tag> & simboli")
        self.assertIn("<b>forte</b>", out)
        self.assertIn("<i>corsivo</i>", out)
        self.assertIn("&lt;tag&gt;", out)
        self.assertIn("&amp;", out)

    def test_conteggio_parole_ignora_markup(self):
        self.assertEqual(mdlite.count_words("# Titolo\n\n**due** parole"), 3)

    def test_strip_title(self):
        title, body = mdlite.strip_title("# Il titolo\n\ncorpo del testo")
        self.assertEqual(title, "Il titolo")
        self.assertEqual(body, "corpo del testo")


if __name__ == "__main__":
    unittest.main()

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

    def test_i_capitoli_stanno_fra_1500_e_2000_parole(self):
        """Il metro con cui si generano i libri: un capitolo non sfora, mai.

        Si prova tutto lo spazio dei formati — pagine di progetto per densità
        di pagina plausibili — perché è il numero di capitoli a doversi
        adattare, e gli unici due modi di sbagliare sono i suoi estremi.
        """
        fuori = []
        for wpp in (220, 250, 267.6, 300.9, 325.2, 360, 385.3, 420):
            for pagine in (60, 80, 100, 140, 180, 200, 240):
                for extra in (False, True):
                    spec = self.spec(
                        target_pages=pagine, include_intro=extra, include_conclusion=extra
                    )
                    budget = planner.build_budget(spec, words_per_page_override=wpp)
                    parti = planner.distribute_words(budget, spec)
                    capitoli = parti[1:-1] if extra else parti
                    for parole in capitoli:
                        if not (
                            planner.MIN_WORDS_PER_CHAPTER
                            <= parole
                            <= planner.MAX_WORDS_PER_CHAPTER
                        ):
                            fuori.append((wpp, pagine, extra, budget.chapters, parole))
                            break
        self.assertEqual(fuori, [], f"capitoli fuori dall'intervallo: {fuori}")

    def test_il_numero_di_capitoli_scelto_a_mano_vince(self):
        """L'autore che fissa `chapters` decide lui: l'intervallo non lo scavalca."""
        budget = planner.build_budget(self.spec(target_pages=140, chapters=7))
        self.assertEqual(budget.chapters, 7)

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


class TestTaraturaDellePagine(unittest.TestCase):
    """Le pagine non sono una funzione continua delle parole: sono una scalinata.

    Ogni sezione si apre su pagina dispari e quindi occupa un numero pari di
    pagine. Fra un gradino e l'altro c'è una pedata piatta dove mille parole in
    più non spostano niente: è lì che il vecchio calcolo si perdeva, ed è
    perché il libro usciva sempre sotto l'obiettivo.
    """

    def spec(self, **kwargs) -> BookSpec:
        base = dict(slug="t", title="Titolo", topic="argomento", language="it")
        base.update(kwargs)
        return BookSpec(**base)

    def test_una_sezione_occupa_sempre_un_numero_pari_di_pagine(self):
        modello = planner.PageModel(
            words_per_body_page=350, opening_pages=1.5, fixed_pages=12
        )
        for parole in (900, 1500, 1750, 2000, 3000):
            corpo = modello.pages_for([parole]) - 12
            self.assertEqual(corpo % 2, 0, f"{parole} parole → {corpo} pagine di corpo")

    def test_fra_due_gradini_le_parole_non_spostano_le_pagine(self):
        modello = planner.PageModel(
            words_per_body_page=350, opening_pages=1.5, fixed_pages=12
        )
        sezioni = [1700] * 20
        cresciute = [1750] * 20
        self.assertEqual(modello.pages_for(sezioni), modello.pages_for(cresciute))

    def test_il_fit_ritrova_il_modello_che_ha_generato_le_misure(self):
        vero = planner.PageModel(words_per_body_page=400, opening_pages=1.8, fixed_pages=13)
        osservazioni = [
            (parole, vero.pages_for([parole]) - 13)
            for parole in (900, 1200, 1500, 1800, 2100, 2400, 3000)
        ]
        stimato = planner._fit_model(osservazioni, 13)
        for parole in (1000, 1600, 2200, 2800):
            self.assertEqual(
                stimato.pages_for([parole]),
                vero.pages_for([parole]),
                f"il modello stimato sbaglia il gradino a {parole} parole",
            )

    def test_la_taratura_porta_il_libro_nella_finestra(self):
        """La prova che conta: si impagina davvero e si guarda dove cade.

        Senza taratura il PDF esce intorno al 10% sotto l'obiettivo, cioè
        fuori; con la taratura ci deve cadere dentro, e i capitoli devono
        restare nell'intervallo di progetto.
        """
        import tempfile
        from pathlib import Path

        from kdpfactory import typeset
        from kdpfactory.models import Outline

        spec = self.spec(target_pages=100)

        def pagine(wpp: float, cartella: str) -> tuple[int, int]:
            budget = planner.build_budget(spec, wpp)
            piani, capitoli = planner._sections_of(spec, planner.distribute_words(budget, spec))
            esito = typeset.typeset(
                spec, Outline(title=spec.title, chapters=piani), capitoli,
                Path(cartella) / "prova.pdf",
            )
            return esito.pages, budget.words_per_chapter

        with tempfile.TemporaryDirectory() as tmp:
            senza, _ = pagine(planner.words_per_page(spec), tmp)
            tarate = planner.calibrate_words_per_page(spec)
            con, parole_capitolo = pagine(tarate, tmp)

        basso, alto = round(spec.target_pages * 0.95), round(spec.target_pages * 1.05)
        self.assertLess(senza, basso, "la stima analitica non sbaglia più per difetto?")
        self.assertTrue(
            basso <= con <= alto, f"{con} pagine fuori dalla finestra [{basso}-{alto}]"
        )
        self.assertTrue(
            planner.MIN_WORDS_PER_CHAPTER <= parole_capitolo <= planner.MAX_WORDS_PER_CHAPTER,
            f"capitoli da {parole_capitolo} parole, fuori intervallo",
        )


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

    def test_apice_inverso_non_rompe_limpaginazione(self):
        """Un solo apice inverso in un capitolo fermava `build` a libro pagato.

        Le virgolette tipografiche si applicavano dopo i tag e arricciavano
        anche quelle di `face="..."`: ReportLab non leggeva più il nome del
        font e sollevava. E Courier, che era il default, non viene incorporato:
        il controllo di stampa rifiuta il PDF.
        """
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph

        markup = mdlite.inline_to_markup('Usa `git status` e poi le "virgolette".')
        self.assertNotIn("<font", markup)
        self.assertNotIn("Courier", markup)
        self.assertIn("“virgolette”", markup)
        Paragraph(markup, getSampleStyleSheet()["Normal"])  # non deve sollevare

    def test_una_famiglia_mono_registrata_viene_usata(self):
        """Chi ha un font monospaziato vero lo può passare: è l'unico modo."""
        markup = mdlite.inline_to_markup("il file `book.json`", mono_font="LiberationMono")
        self.assertIn('<font face="LiberationMono">book.json</font>', markup)

    def test_conteggio_parole_ignora_markup(self):
        self.assertEqual(mdlite.count_words("# Titolo\n\n**due** parole"), 3)

    def test_strip_title(self):
        title, body = mdlite.strip_title("# Il titolo\n\ncorpo del testo")
        self.assertEqual(title, "Il titolo")
        self.assertEqual(body, "corpo del testo")


class TestCategorieDiProdotto(unittest.TestCase):
    """Medium-content e full-content: le definizioni di CLAUDE.md, rese eseguibili."""

    def spec(self, **kwargs) -> BookSpec:
        base = dict(slug="t", title="Titolo", topic="argomento")
        base.update(kwargs)
        return BookSpec(**base)

    def test_full_content_e_il_valore_predefinito(self):
        self.assertEqual(self.spec().content_type, "full")
        self.assertFalse(self.spec().is_medium_content)

    def test_una_categoria_inventata_non_passa_la_validazione(self):
        problemi = self.spec(content_type="low").validate()
        self.assertTrue(any("content_type" in p for p in problemi))

    def test_gli_esercizi_seguono_la_categoria(self):
        """Un medium-content vive di esercizi; un full-content vive del testo."""
        self.assertTrue(self.spec(content_type="medium").wants_exercises)
        self.assertFalse(self.spec(content_type="full").wants_exercises)

    def test_la_scelta_esplicita_dell_autore_vince(self):
        self.assertTrue(self.spec(content_type="full", include_exercises=True).wants_exercises)
        self.assertFalse(self.spec(content_type="medium", include_exercises=False).wants_exercises)

    def test_la_linea_enigmistica_e_medium_content(self):
        from kdpfactory.puzzle.book import default_book_spec
        from kdpfactory.puzzle.theme import COLLAUDO

        spec = default_book_spec("x", "Autore", COLLAUDO)
        self.assertEqual(spec.content_type, "medium")
        self.assertEqual(spec.validate(), [])


class TestConfineDelFullContent(unittest.TestCase):
    """Su un full-content non ci devono essere pagine da compilare."""

    def controlla(self, markdown: str, content_type: str):
        from kdpfactory import qa
        from kdpfactory.models import ChapterPlan, Outline

        spec = BookSpec(slug="t", title="T", topic="a", content_type=content_type)
        capitolo = ChapterPlan(number=1, title="Capitolo", summary="s", target_words=1700)
        outline = Outline(title="T", chapters=[capitolo])
        report = qa.check_manuscript(spec, outline, [(1, "Capitolo", markdown)])
        return [f for f in report.findings if f.code == "CATEGORIA"]

    def test_righe_da_riempire_segnalate_su_un_full_content(self):
        testo = "# Capitolo\n\nUn paragrafo.\n\n" + "_" * 40 + "\n\n" + "_" * 40 + "\n"
        rilievi = self.controlla(testo, "full")
        self.assertEqual(len(rilievi), 1)
        self.assertIn("2 righe da riempire", rilievi[0].message)

    def test_su_un_medium_content_sono_il_prodotto(self):
        testo = "# Capitolo\n\nUn paragrafo.\n\n" + "_" * 40 + "\n"
        self.assertEqual(self.controlla(testo, "medium"), [])

    def test_una_linea_orizzontale_markdown_non_e_uno_spazio_da_compilare(self):
        testo = "# Capitolo\n\nUn paragrafo.\n\n---\n\nAltro paragrafo.\n"
        self.assertEqual(self.controlla(testo, "full"), [])


if __name__ == "__main__":
    unittest.main()

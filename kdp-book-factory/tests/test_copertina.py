"""Test del sistema di copertine: misure, testi, verifica sul PDF reale.

Nessuno di questi test chiede un giudizio estetico: verificano le sole cose
che di una copertina si possono misurare — e che sono anche quelle che
decidono se in miniatura il libro si vede o no.
"""

import tempfile
import unittest
from pathlib import Path

from kdpfactory import backup, cover, coverart, coverbrief, coverdesign, kdpspecs
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


class TestIllustrazioni(unittest.TestCase):
    """Le illustrazioni sono vettoriali e deterministiche: si possono provare tutte."""

    def area(self) -> coverart.Area:
        return coverart.Area(x=100.0, y=50.0, width=390.0, height=240.0)

    def test_fit_rispetta_le_proporzioni_e_sta_dentro(self):
        area = self.area()
        for ratio in (0.72, 1.0, 2.35, 3.0):
            with self.subTest(ratio=ratio):
                scene = area.fit(ratio)
                self.assertAlmostEqual(scene.width / scene.height, ratio, places=6)
                self.assertGreaterEqual(scene.x, area.x - 1e-9)
                self.assertLessEqual(scene.right, area.right + 1e-9)
                self.assertGreaterEqual(scene.y, area.y - 1e-9)
                self.assertLessEqual(scene.top, area.top + 1e-9)

    def test_fit_ancorato_in_basso_poggia_sul_bordo(self):
        area = self.area()
        self.assertAlmostEqual(area.fit(2.35, anchor="bottom").y, area.y)

    def test_ogni_illustrazione_si_disegna_in_ogni_palette(self):
        from reportlab.pdfgen import canvas as pdfcanvas

        for art in coverart.ARTS:
            for palette in coverdesign.PALETTES:
                with self.subTest(art=art.name, palette=palette.name):
                    with tempfile.TemporaryDirectory() as tmp:
                        c = pdfcanvas.Canvas(str(Path(tmp) / "a.pdf"), pagesize=(600, 400))
                        coverart.draw(c, art, self.area(), palette)
                        c.showPage()
                        c.save()

    def test_lo_stato_grafico_torna_come_prima(self):
        """La trasparenza resta nello stato della pagina: se un'illustrazione se
        la porta dietro, tutto quello disegnato dopo esce slavato.

        Si verifica sul risultato, non sugli attributi: dopo l'illustrazione si
        stampa un rosso pieno e si legge il pixel."""
        import pymupdf
        from reportlab.lib import colors
        from reportlab.pdfgen import canvas as pdfcanvas

        for art in coverart.ARTS:
            with self.subTest(art=art.name), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "a.pdf"
                c = pdfcanvas.Canvas(str(path), pagesize=(600, 400))
                c.setFillColor(colors.white)
                c.rect(0, 0, 600, 400, stroke=0, fill=1)
                c.setLineWidth(1)
                coverart.draw(c, art, coverart.Area(20, 120, 320, 260), coverdesign.PALETTES[0])
                self.assertEqual(c._lineWidth, 1)
                c.setFillColor(colors.HexColor("#FF0000"))
                c.rect(420, 40, 120, 60, stroke=0, fill=1)
                c.showPage()
                c.save()

                document = pymupdf.open(path)
                pixmap = document[0].get_pixmap()
                self.assertEqual(pixmap.pixel(480, 400 - 70), (255, 0, 0))
                document.close()

    def test_scelta_dal_contenuto(self):
        self.assertEqual(
            coverart.pick("Twelve Carriages: a night express, one sleeper car", "enigmi").name,
            "treno",
        )
        self.assertEqual(
            coverart.pick("Il metodo delle tre ore: recuperare una mattina", "non-fiction").name,
            "orologio",
        )
        self.assertEqual(
            coverart.pick("La casa sul confine: un segreto dietro la porta", "fiction").name,
            "porta",
        )

    def test_a_parita_di_parole_vince_la_scena_piu_concreta(self):
        """Una parola a testa: «puzzle» pesca l'elenco astratto, «door» la
        porta. A parità vince la scena, che in miniatura si ricorda."""
        self.assertEqual(coverart.pick("a puzzle behind a door", "enigmi").name, "porta")

    def test_senza_parole_riconoscibili_decide_il_genere(self):
        for genre, expected in coverart.GENRE_ART.items():
            with self.subTest(genre=genre):
                self.assertEqual(coverart.pick("zzz qqq", genre).name, expected)

    def test_scelta_dellautore_ha_la_precedenza(self):
        self.assertEqual(
            coverart.pick("Twelve Carriages, One Killer", "enigmi", wanted="orologio").name,
            "orologio",
        )

    def test_nessuna_illustrazione_su_richiesta(self):
        with self.assertRaises(KeyError):
            coverart.pick("Twelve Carriages", "enigmi", wanted="nessuna")

    def test_la_scelta_del_libro_arriva_fino_al_pdf(self):
        backup.configure(enabled=False)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                info = cover.build_cover(
                    demo_spec(cover_art="treno"), 120, Path(tmp) / "c.pdf", genre="enigmi",
                    copy=CoverCopy(title="Twelve Carriages, One Killer", author="Iris Vane"),
                )
                self.assertEqual(info["illustrazione"], "treno")
                self.assertEqual(info["verifica"]["problemi"], [])
        finally:
            backup.configure(enabled=True)

    def test_con_foto_dellautore_non_si_disegna_nulla(self):
        """Regola 1: un solo elemento dominante. Se c'è già una fotografia,
        l'illustrazione non ci va sopra."""
        box = demo_box()
        from reportlab.pdfgen import canvas as pdfcanvas

        with tempfile.TemporaryDirectory() as tmp:
            c = pdfcanvas.Canvas(str(Path(tmp) / "a.pdf"), pagesize=(box.width, box.height))
            result = coverdesign.draw_front(
                c, box, CoverCopy(title="Twelve Carriages", subject="night express train",
                                  author="Iris Vane"),
                coverdesign.PALETTES[0],
                display=register_family("sans"), text_font=register_family("serif"),
                genre="enigmi", over_image=True,
            )
        self.assertEqual(result.art, "")

    def test_cover_art_sconosciuta_non_passa_la_validazione(self):
        problems = demo_spec(cover_art="astronave").validate()
        self.assertTrue(any("cover_art" in problem for problem in problems))


class TestAgenteCopertina(unittest.TestCase):
    def setUp(self):
        backup.configure(enabled=False)
        self.tmp = tempfile.TemporaryDirectory()
        # un libro di enigmi è un medium-content: la sua copertina vive di
        # segnale di categoria e quantificatore
        self.spec = demo_spec(content_type="medium")
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
                kicker="DEDUCTION PUZZLES",
                hook="Can you name the killer in every carriage?",
                stats="13 CASES · 908 SUSPECTS",
                content_type="medium",
                facts=["13", "908"],
            )
        ).findings
        self.assertFalse([f for f in findings if f.severity == "bloccante"])


class TestAuditCheVedeIDifetti(unittest.TestCase):
    """L'audit deve vedere proprio i difetti che manda il libro in stampa storto.

    Sono i due casi in cui prima guardava altrove: la riga di titolo più larga
    della copertina — che il filtro scartava perché comincia prima del taglio —
    e il titolo fatto di sole parole corte, che dichiarava assente.
    """

    def setUp(self):
        backup.configure(enabled=False)
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()
        backup.configure(enabled=True)

    def verifica(self, titolo: str) -> dict:
        spec = demo_spec(
            title=titolo, subtitle="Un metodo in dodici settimane",
            language="it", content_type="medium",
        )
        info = cover.build_cover(
            spec, 140, Path(self.tmp.name) / "c.pdf",
            genre="non-fiction", chapters=12, practice=12,
        )
        return info["verifica"]

    def test_la_parola_che_esce_dalla_copertina_viene_vista(self):
        problemi = self.verifica("Esercizi per la concentrazione")["problemi"]
        self.assertEqual(len(problemi), 1)
        self.assertIn("area di sicurezza", problemi[0])
        self.assertIn("CONCENTRAZIONE", problemi[0])

    def test_il_titolo_al_corpo_minimo_non_e_troppo_piccolo(self):
        """Il disegno si ferma *sul* minimo: senza tolleranza, il confronto in
        virgola mobile bocciava la copertina che il sistema ha appena fatto."""
        verifica = self.verifica("Esercizi per la concentrazione")
        self.assertEqual(verifica["titolo_percentuale_altezza"], 6.0)
        self.assertFalse([p for p in verifica["problemi"] if "troppo piccolo" in p])

    def test_un_titolo_di_sole_parole_corte_viene_trovato(self):
        verifica = self.verifica("Tre Ore")
        self.assertEqual(verifica["problemi"], [])
        self.assertGreater(verifica["titolo_percentuale_altezza"], 6.0)

    def test_la_parola_piu_larga_non_e_quella_con_piu_lettere(self):
        """PRINCIPIANTI ha 12 lettere, MEDITAZIONE 11: la più larga è la seconda.

        Tarare il corpo sul conteggio delle lettere lo tara sulla parola
        sbagliata, e quella vera esce dalla copertina.
        """
        font = register_family("sans")
        self.assertGreater(len("PRINCIPIANTI"), len("MEDITAZIONE"))
        self.assertGreater(
            tracked_width("MEDITAZIONE", font, 100), tracked_width("PRINCIPIANTI", font, 100)
        )
        self.assertEqual(self.verifica("Meditazione per principianti")["problemi"], [])


class TestFormulaDellaCategoria(unittest.TestCase):
    """Le due formule di CLAUDE.md, rese eseguibili sui testi di copertina.

    Non si giudica la bellezza: si guarda se la copertina vende il prodotto
    giusto. Un medium-content che non dice quanto contiene e un full-content
    vestito da prodotto da scaffale parlano al cliente sbagliato.
    """

    def problemi(self, **campi) -> list[str]:
        campi.setdefault("title", "Il Titolo")
        campi["facts"] = tuple(campi.get("facts", ()))
        return coverdesign.copy_problems(CoverCopy(**campi))

    def test_medium_senza_quantificatore_non_passa(self):
        problemi = self.problemi(content_type="medium", kicker="SCHEDE PRATICHE")
        self.assertTrue(any("senza quantificatore" in p for p in problemi))

    def test_medium_senza_segnale_di_categoria(self):
        problemi = self.problemi(content_type="medium", stats="120 ESERCIZI")
        self.assertTrue(any("senza segnale di categoria" in p for p in problemi))

    def test_medium_completo_non_ha_rilievi(self):
        problemi = self.problemi(
            content_type="medium", kicker="SCHEDE PRATICHE",
            stats="120 ESERCIZI", facts=("120",),
        )
        self.assertEqual(problemi, [])

    def test_full_con_specifiche_da_scaffale_non_passa(self):
        problemi = self.problemi(
            content_type="full", stats="240 PAGINE", badge="Caratteri grandi",
            facts=("240",),
        )
        self.assertEqual(len(problemi), 1)
        self.assertIn("numeri, garanzia", problemi[0])

    def test_full_nudo_non_ha_rilievi(self):
        self.assertEqual(
            self.problemi(content_type="full", hook="E se bastasse un'ora?"), []
        )

    def test_una_cifra_che_il_libro_non_ha_non_si_stampa(self):
        problemi = self.problemi(
            content_type="medium", kicker="ENIGMI", stats="1000 ENIGMI", facts=("120", "240"),
        )
        self.assertTrue(any("non corrispondono a nessun dato" in p for p in problemi))
        self.assertIn("1000", [p for p in problemi if "nessun dato" in p][0])

    def test_i_separatori_delle_migliaia_non_fanno_due_numeri_diversi(self):
        problemi = self.problemi(
            content_type="medium", kicker="ENIGMI", stats="1,234 SOSPETTI", facts=("1234",),
        )
        self.assertEqual(problemi, [])

    def test_senza_fatti_dichiarati_il_controllo_tace(self):
        """Un libro lavorato prima di questa regola non va accusato a vuoto."""
        problemi = self.problemi(content_type="medium", kicker="ENIGMI", stats="13 CASI")
        self.assertEqual(problemi, [])


class TestDatiFunzionali(unittest.TestCase):
    """Il quantificatore si conta sul libro, non si dichiara."""

    def test_le_schede_pratiche_si_contano_nel_manoscritto(self):
        capitoli = [
            "# Uno\n\nTesto.\n\n## In pratica\n\n1. fai questo\n",
            "# Due\n\nTesto senza esercizi.\n",
            "# Tre\n\nTesto.\n\n## in pratica\n\n1. fai quest'altro\n",
        ]
        self.assertEqual(coverdesign.count_practice_sections(capitoli), 2)

    def test_il_quantificatore_e_nella_lingua_del_libro(self):
        spec = demo_spec(language="it", content_type="medium")
        self.assertEqual(
            coverdesign.quantifier(spec, pages=140, practice=18), "18 SCHEDE PRATICHE · 140 PAGINE"
        )
        spec = demo_spec(language="en", content_type="medium")
        self.assertEqual(
            coverdesign.quantifier(spec, pages=140, chapters=12), "12 CHAPTERS · 140 PAGES"
        )

    def test_i_caratteri_grandi_sono_una_garanzia_misurata(self):
        self.assertEqual(coverdesign.guarantee(demo_spec(body_font_size=14, language="it")),
                         "Caratteri grandi")
        self.assertEqual(coverdesign.guarantee(demo_spec(body_font_size=11)), "")

    def test_il_medium_riceve_i_numeri_contati_e_il_full_no(self):
        medium = coverdesign.derive_copy(
            demo_spec(content_type="medium", language="it"), pages=140, practice=18
        )
        self.assertEqual(medium.stats, "18 SCHEDE PRATICHE · 140 PAGINE")
        self.assertIn("140", medium.facts)

        full = coverdesign.derive_copy(demo_spec(content_type="full"), pages=140, practice=18)
        self.assertEqual(full.stats, "")
        self.assertEqual(full.badge, "")

    def test_la_scheda_prodotto_batte_il_numero_calcolato(self):
        copy = coverdesign.derive_copy(
            demo_spec(content_type="medium"), {"cover_stats": "13 CASES"}, pages=140
        )
        self.assertEqual(copy.stats, "13 CASES")

    def test_locchiello_del_genere_parla_la_lingua_del_libro(self):
        self.assertEqual(
            coverdesign.derive_copy(demo_spec(language="it"), genre="enigmi").kicker,
            "ENIGMI DI DEDUZIONE",
        )
        self.assertEqual(
            coverdesign.derive_copy(demo_spec(language="en"), genre="enigmi").kicker,
            "DEDUCTION PUZZLES",
        )


class TestBriefDiCopertina(unittest.TestCase):
    """Il brief per lo strumento grafico: quello che il motore non sa disegnare."""

    def brief(self, **overrides) -> str:
        pagine = overrides.pop("pages", 140)
        metadata = overrides.pop("metadata", {})
        return coverbrief.brief(demo_spec(**overrides), pages=pagine, metadata=metadata)

    def test_la_categoria_porta_la_sua_formula(self):
        medium = self.brief(content_type="medium")
        self.assertIn("BOOK TYPE: MEDIUM-CONTENT", medium)
        self.assertIn("INTERIOR PREVIEW + QUANTIFIER", medium)
        self.assertIn("FUNCTION over atmosphere", medium)

        full = self.brief(content_type="full")
        self.assertIn("BOOK TYPE: FULL-CONTENT", full)
        self.assertIn("WORLD / EMOTION + VISUAL METAPHOR", full)
        self.assertIn("EMOTION, IDENTITY and TRANSFORMATION", full)

    def test_le_soglie_del_motore_sono_quelle_scritte_nel_brief(self):
        """Il brief non inventa regole: cita le costanti che poi verificano il PDF."""
        testo = self.brief()
        self.assertIn(f"{coverdesign.THUMBNAIL_WIDTH_PX} px", testo)
        self.assertIn(f"at least {coverdesign.MIN_CONTRAST:.0f}:1", testo)
        self.assertIn(f"at most {coverdesign.MAX_TITLE_LINES} lines", testo)

    def test_i_numeri_veri_si_citano_e_gli_altri_si_vietano(self):
        medium = self.brief(content_type="medium", language="it", pages=146)
        self.assertIn('Quantifier: "146 PAGINE"', medium)
        self.assertIn("do not invent, round or add any other number", medium)

        full = self.brief(content_type="full")
        self.assertIn("Do not print any figure on the cover", full)

    def test_dice_in_che_lingua_va_stampato_il_testo(self):
        self.assertIn("Written in Italian", self.brief(language="it"))
        self.assertIn("Written in English", self.brief(language="en"))

    def test_porta_le_misure_di_stampa_del_libro(self):
        testo = self.brief(trim="6x9", paper="cream", pages=200)
        larghezza, altezza = kdpspecs.cover_size_in("6x9", 200, "cream")
        self.assertIn("1800 x 2700 px", testo)              # la sola prima, a 300 DPI
        self.assertIn(f"{larghezza:.3f}\" x {altezza:.3f}\"", testo)

    def test_vieta_di_imitare_e_di_inventare_riconoscimenti(self):
        testo = self.brief()
        self.assertIn("Do not imitate", testo)
        self.assertIn("No award stamps, star ratings", testo)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

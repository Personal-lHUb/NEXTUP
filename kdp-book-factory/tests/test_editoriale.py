"""Lo standard di un editore di saggistica: numerazione, caratteri, aperture, indice.

Sono le cose che distinguono a colpo d'occhio un libro fatto da un editore da
uno fatto in casa: la pagina 1 è la prima del testo, titoli e testo stanno in
una famiglia sola, il capitolo comincia più in basso e con le prime parole in
maiuscoletto, un titoletto non lascia un quarto di pagina bianco sopra di sé,
e l'indice porta davvero dove dice, nei due sensi.
"""

import tempfile
import unittest
from pathlib import Path

import pymupdf

from kdpfactory import coerenza, typeset
from kdpfactory.models import BookSpec, ChapterPlan, Outline

PROSA = (
    "Every household bill has a due date, an amount and an account behind it, and "
    "the reader learns to find all three before anything else. "
) * 18

TITOLI = [
    "Finding the Due Date on a Utility Bill",
    "Reading the Minimum Payment on a Credit Card",
    "Lining Up Paydays With the Calendar",
    "Calling the Lender Before a Missed Payment",
]


def spec(**campi) -> BookSpec:
    base = dict(slug="ed", title="Test Book", language="en", target_pages=60)
    base.update(campi)
    return BookSpec(**base)


def libro() -> tuple[Outline, list[tuple[int, str, str]]]:
    capitoli = [ChapterPlan(number=1, title="Introduction", role="intro")]
    capitoli += [ChapterPlan(number=n + 2, title=t) for n, t in enumerate(TITOLI)]
    temi = ["due date utility meter", "minimum payment credit card interest",
            "payday calendar paycheck", "lender missed payment hardship"]
    testi = [(1, "Introduction", "Who this book is for, and how to use it. " * 40)]
    for (n, t), tema in zip([(c.number, c.title) for c in capitoli[1:]], temi, strict=True):
        testi.append((n, t, PROSA + f" {tema} " * 12 + "\n\n## A first section\n\n" + PROSA))
    return Outline(title="Test Book", chapters=capitoli), testi


class TestImpaginazione(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        outline, capitoli = libro()
        cls.outline, cls.capitoli = outline, capitoli
        cls.esito = typeset.typeset(spec(), outline, capitoli, Path(cls.tmp.name) / "libro.pdf")
        with pymupdf.open(cls.esito.pdf_path) as pdf:
            cls.testi = [pagina.get_text() for pagina in pdf]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_la_pagina_uno_e_la_prima_del_testo(self):
        prima = self.esito.chapter_pages["Introduction"]
        self.assertEqual(self.esito.folio_offset, prima - 1)
        self.assertEqual(prima % 2, 1, "il testo comincia su una pagina destra")
        # la pagina dopo l'apertura di un capitolo porta il folio contato dal testo
        apertura = self.esito.chapter_pages[TITOLI[0]]
        righe = [r.strip() for r in self.testi[apertura].splitlines() if r.strip()]
        self.assertIn(str(apertura + 1 - self.esito.folio_offset), righe)

    def test_l_indice_stampa_i_numeri_che_il_lettore_vede(self):
        pdf = self.esito.pdf_path
        voci = coerenza.leggi_indice(pdf, coerenza.pagine_indice(pdf, "Contents"), "Contents")
        self.assertEqual((voci[0].testo, voci[0].folio), ("Introduction", 1))
        apertura = self.esito.chapter_pages[TITOLI[0]] - self.esito.folio_offset
        self.assertEqual((voci[1].testo, voci[1].folio), (f"1 {TITOLI[0]}", apertura),
                         "il capitolo porta il suo numero anche nell'indice")

    def test_titoli_e_testo_nella_stessa_famiglia(self):
        with pymupdf.open(self.esito.pdf_path) as pdf:
            famiglie = {f[3].split("+")[-1].split("-")[0] for p in pdf for f in p.get_fonts()}
        self.assertEqual(len(famiglie), 1, f"più famiglie nel testo pieno: {famiglie}")

    def test_il_capitolo_comincia_col_maiuscoletto(self):
        pagina = self.testi[self.esito.chapter_pages[TITOLI[0]] - 1]
        self.assertIn("EVERY HOUSEHOLD BILL", pagina)

    def test_il_medium_content_resta_compatto_e_senza_maiuscoletto(self):
        outline, capitoli = libro()
        with tempfile.TemporaryDirectory() as tmp:
            esito = typeset.typeset(spec(content_type="medium"), outline, capitoli,
                                    Path(tmp) / "m.pdf")
            with pymupdf.open(esito.pdf_path) as pdf:
                pagina = pdf[esito.chapter_pages[TITOLI[0]] - 1].get_text()
        self.assertNotIn("EVERY HOUSEHOLD BILL", pagina)


class TestMaiuscoletto(unittest.TestCase):
    def test_si_ferma_alla_prima_pausa(self):
        markup = typeset._maiuscoletto("Take Dana, a mother of two, at home.", 11)
        self.assertTrue(markup.startswith('<font size="9.2">TAKE DANA,</font>'))
        self.assertTrue(markup.endswith(" a mother of two, at home."))

    def test_lascia_stare_il_markup(self):
        self.assertIsNone(typeset._maiuscoletto("The *other* card was paid.", 11))
        self.assertIsNone(typeset._maiuscoletto('"Rent on the first," she said.', 11))
        self.assertIsNone(typeset._maiuscoletto("Short.", 11))


class TestCoda(unittest.TestCase):
    def test_l_ultima_riga_non_resta_con_una_parola_corta(self):
        legata = typeset._lega_coda("one two three four five six seven eight it.")
        self.assertTrue(legata.endswith("seven\u00a0eight\u00a0it."))
        self.assertEqual(typeset._lega_coda("A short one."), "A short one.")
        self.assertTrue(typeset._lega_coda("a b c d e f g h of the whole month.")
                        .endswith(" the whole\u00a0month."))

    def test_le_parole_legate_vanno_a_capo_insieme(self):
        stili = typeset.build_styles(spec())
        testo = "word " * 13 + "endings it."
        paragrafo = typeset.markdown_to_flowables(testo, stili)[0]
        paragrafo.wrap(200, 1000)
        ultima = paragrafo.blPara.lines[-1][1]
        self.assertGreaterEqual(len(" ".join(ultima)), typeset.CODA_MIN_CARATTERI)


class TestTitoletti(unittest.TestCase):
    def test_un_capoverso_lungo_non_viene_trascinato_intero(self):
        stili = typeset.build_styles(spec())
        markdown = "## A heading\n\n" + PROSA
        flowables = typeset.markdown_to_flowables(markdown, stili, measure=300, frame_height=500)
        self.assertIsInstance(flowables[0], typeset.CondPageBreak)
        self.assertNotIsInstance(flowables[1], typeset.KeepTogether)

    def test_un_capoverso_breve_resta_attaccato(self):
        stili = typeset.build_styles(spec())
        flowables = typeset.markdown_to_flowables("## A heading\n\nOne line.", stili,
                                                  measure=300, frame_height=500)
        self.assertIsInstance(flowables[0], typeset.KeepTogether)


class TestCoerenzaIndice(unittest.TestCase):
    def capitoli(self):
        _, testi = libro()
        return testi

    def test_un_libro_coerente_non_ha_rilievi(self):
        esito = coerenza.controlla(self.capitoli(), "en", generici={1})
        self.assertEqual(esito.errori, [])
        self.assertEqual(esito.avvisi, [])

    def test_il_titolo_che_promette_un_altro_argomento(self):
        capitoli = self.capitoli()
        numero, _, testo = capitoli[2]
        capitoli[2] = (numero, "Choosing Insurance for a Rental Apartment", testo)
        esito = coerenza.controlla(capitoli, "en", generici={1})
        self.assertTrue(any("non usa mai" in a and "Insurance" in a for a in esito.avvisi))

    def test_il_titolo_che_starebbe_su_ogni_capitolo(self):
        capitoli = self.capitoli()
        numero, _, testo = capitoli[3]
        capitoli[3] = (numero, "Every Household Bill", testo)
        esito = coerenza.controlla(capitoli, "en", generici={1})
        avviso = next(a for a in esito.avvisi if "Every Household Bill" in a)
        self.assertIn("starebbe bene su un altro capitolo", avviso)
        self.assertIn("«payday»", avviso, "propone le parole che distinguono il capitolo")

    def test_i_nomi_dei_personaggi_non_sono_argomenti(self):
        capitoli = self.capitoli()
        numero, titolo, testo = capitoli[1]
        capitoli[1] = (numero, titolo, testo + " Hank called. Hank paid. Hank waited. Hank left.")
        esito = coerenza.controlla(capitoli, "en", generici={1})
        self.assertNotIn("hank", esito.distintive[numero])

    def test_il_capitolo_aggiunto_dopo_l_indice(self):
        capitoli = self.capitoli()
        decisi = [t for _, t, _ in capitoli[1:3]] + [capitoli[4][1]]
        esito = coerenza.controlla(capitoli, "en", indice_titoli=decisi,
                                   numerati=[2, 3, 4, 5], generici={1})
        self.assertEqual(len(esito.errori), 1)
        self.assertIn(TITOLI[2], esito.errori[0])

    def test_un_rimando_al_titolo_vecchio(self):
        capitoli = self.capitoli()
        numero, titolo, testo = capitoli[0]
        capitoli[0] = (numero, titolo, testo + " Then read *Calling the Lender After a Missed Payment*.")
        esito = coerenza.controlla(capitoli, "en", generici={1})
        self.assertTrue(any("rimanda a *Calling the Lender After a Missed Payment*" in a
                            and f"«{TITOLI[3]}»" in a for a in esito.avvisi))
        giusto = self.capitoli()
        giusto[0] = (numero, titolo, testo + f" Then read *{TITOLI[3]}*, and *really* do it.")
        self.assertEqual(coerenza.controlla(giusto, "en", generici={1}).avvisi, [])

    def test_la_scaletta_e_il_manoscritto_divergono(self):
        capitoli = self.capitoli()
        esito = coerenza.controlla(capitoli, "en", outline_titoli={2: "A Different Title"},
                                   generici={1})
        self.assertIn("la scaletta dice «A Different Title»", esito.errori[0])

    def test_l_indice_stampato_porta_alle_aperture(self):
        outline, capitoli = libro()
        with tempfile.TemporaryDirectory() as tmp:
            esito = typeset.typeset(spec(), outline, capitoli, Path(tmp) / "libro.pdf")
            buono = coerenza.controlla(capitoli, "en", generici={1}, pdf=esito.pdf_path,
                                       folio_offset=esito.folio_offset, titolo_indice="Contents")
            sbagliato = coerenza.controlla(capitoli, "en", generici={1}, pdf=esito.pdf_path,
                                           folio_offset=esito.folio_offset + 2,
                                           titolo_indice="Contents")
            voci = coerenza.leggi_indice(esito.pdf_path,
                                         coerenza.pagine_indice(esito.pdf_path, "Contents"),
                                         "Contents")
        self.assertEqual(buono.errori, [])
        self.assertTrue(any("non si apre" in e for e in sbagliato.errori))
        self.assertEqual(voci[0].testo, "Introduction")
        self.assertEqual(voci[0].folio, 1)


if __name__ == "__main__":
    unittest.main()

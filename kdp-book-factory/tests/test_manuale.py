"""Test della linea manuale: la fabbrica senza chiave API.

Il punto di questi test non è che il codice giri: è che il libro prodotto a
mano sia **lo stesso libro** di quello prodotto chiamando il modello. Stessa
scaletta normalizzata, stesso manoscritto sul disco, stessi controlli — solo
la scrittura arriva da un'altra strada.
"""

import json
import tempfile
import unittest
from pathlib import Path

from kdpfactory import manuale, planner, writer
from kdpfactory.llm import LLMClient, LLMConfig
from kdpfactory.models import BookProject, BookSpec, Outline

SCALETTA = {
    "title": "What They Remembered",
    "subtitle": "Past-Life Sessions, Honestly Told",
    "thesis": "Testimony is not history, and the difference is the book.",
    "back_cover": "Gancio di quarta.\n\nSecondo paragrafo.",
    "chapters": [
        {
            "number": i,
            "title": f"Chapter {i}",
            "summary": f"Quello che fa il capitolo {i}.",
            "beats": ["punto uno", "punto due"],
        }
        for i in range(1, 7)
    ],
}


def demo_spec(**overrides) -> BookSpec:
    dati = dict(
        slug="prova",
        title="What They Remembered",
        subtitle="Past-Life Sessions, Honestly Told",
        author="Thea Bramwell",
        language="en",
        topic="what people say under hypnotic regression",
        audience="readers of this niche",
        promise="you will know what was said and what stands up",
        target_pages=100,
    )
    dati.update(overrides)
    return BookSpec(**dati)


class TestLineaManuale(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = BookProject(Path(self.tmp.name) / "libro")
        self.project.ensure_dirs()
        self.spec = demo_spec()
        self.spec.save(self.project.spec_path)
        self.budget = planner.build_budget(self.spec, 360.0)

    def tearDown(self):
        self.tmp.cleanup()

    # --- scaletta ---------------------------------------------------------
    def test_il_brief_della_scaletta_contiene_il_prompt_vero(self):
        percorso = manuale.brief_scaletta(self.project, self.spec, self.budget)
        testo = percorso.read_text(encoding="utf-8")
        self.assertIn("SISTEMA", testo)
        self.assertIn("Sei un editor", testo)          # il prompt di sistema vero
        self.assertIn(self.spec.title, testo)          # la scheda del libro
        self.assertIn("JSON valido", testo)            # il contratto di risposta
        self.assertIn(str(self.budget.chapters), testo)

    def test_la_scaletta_incollata_diventa_outline_json(self):
        outline = manuale.importa_scaletta(
            self.project, self.spec, self.budget, json.dumps(SCALETTA)
        )
        self.assertTrue(self.project.outline_path.exists())
        # introduzione e conclusione sono aggiunte dal sistema, non dal modello
        ruoli = [c.role for c in outline.chapters]
        self.assertEqual(ruoli[0], "intro")
        self.assertEqual(ruoli[-1], "conclusion")
        self.assertEqual([c.number for c in outline.chapters], list(range(1, len(ruoli) + 1)))
        self.assertTrue(all(c.target_words > 0 for c in outline.chapters))

    def test_le_due_linee_producono_la_stessa_scaletta(self):
        """La prova che conta: a mano o col modello, il libro è lo stesso.

        La normalizzazione sta in un posto solo (`writer.normalize_outline`),
        e questo test fallisce il giorno in cui qualcuno la duplica.
        """
        a_mano = manuale.importa_scaletta(
            self.project, self.spec, self.budget, json.dumps(SCALETTA)
        )
        dal_modello = writer.normalize_outline(
            self.spec, Outline.from_dict(SCALETTA), self.budget
        )
        self.assertEqual(a_mano.to_dict(), dal_modello.to_dict())

    def test_una_scaletta_senza_capitoli_viene_rifiutata(self):
        with self.assertRaises(SystemExit) as caso:
            manuale.importa_scaletta(self.project, self.spec, self.budget, '{"chapters": []}')
        self.assertIn("nessun capitolo", str(caso.exception))

    def test_un_capitolo_senza_titolo_viene_rifiutato(self):
        rotta = {**SCALETTA, "chapters": [{"number": 1, "title": "  ", "summary": "x"}]}
        with self.assertRaises(SystemExit) as caso:
            manuale.importa_scaletta(self.project, self.spec, self.budget, json.dumps(rotta))
        self.assertIn("senza titolo", str(caso.exception))

    # --- capitoli ---------------------------------------------------------
    def outline(self) -> Outline:
        return manuale.importa_scaletta(
            self.project, self.spec, self.budget, json.dumps(SCALETTA)
        )

    def test_il_brief_del_capitolo_porta_quello_che_è_già_stato_detto(self):
        outline = self.outline()
        percorso = manuale.brief_capitolo(self.project, self.spec, outline, 4)
        testo = percorso.read_text(encoding="utf-8")
        quarto = outline.chapters[3]
        self.assertIn(quarto.title, testo)
        self.assertIn(str(quarto.target_words), testo)
        # il contesto viene dai riassunti della scaletta: senza modello non
        # esistono riassunti scritti dopo la stesura
        self.assertIn(outline.chapters[2].summary, testo)

    def test_un_capitolo_che_non_esiste_lo_dice(self):
        with self.assertRaises(SystemExit) as caso:
            manuale.brief_capitolo(self.project, self.spec, self.outline(), 99)
        self.assertIn("non c'è un capitolo 99", str(caso.exception))

    def test_il_capitolo_importato_finisce_nel_manoscritto(self):
        outline = self.outline()
        testo = "Prima riga del capitolo. " * 200
        esito = manuale.importa_capitolo(self.project, outline, 2, testo)
        scritto = self.project.chapter_path(2).read_text(encoding="utf-8")
        self.assertTrue(scritto.startswith(f"# {outline.chapters[1].title}"))
        self.assertEqual(esito["parole"], 800)
        self.assertIn("scarto", esito)

    def test_un_capitolo_fuori_budget_viene_detto_ma_accettato(self):
        outline = self.outline()
        esito = manuale.importa_capitolo(self.project, outline, 2, "poche parole in croce")
        self.assertTrue(esito["fuori_tolleranza"])
        self.assertTrue(self.project.chapter_path(2).exists())

    def test_un_capitolo_vuoto_non_tocca_il_manoscritto(self):
        outline = self.outline()
        with self.assertRaises(SystemExit):
            manuale.importa_capitolo(self.project, outline, 2, "   \n  ")
        self.assertFalse(self.project.chapter_path(2).exists())

    def test_il_manoscritto_si_rilegge_come_quello_automatico(self):
        """`writer.load_chapters` è la porta d'ingresso di tutto il resto."""
        outline = self.outline()
        manuale.importa_capitolo(self.project, outline, 1, "Testo del primo. " * 100)
        capitoli = writer.load_chapters(self.project, outline)
        self.assertEqual([n for n, _, _ in capitoli], [1])

    # --- scheda prodotto --------------------------------------------------
    def test_la_scheda_senza_capitoli_non_si_prepara(self):
        with self.assertRaises(SystemExit) as caso:
            manuale.brief_scheda(self.project, self.spec, self.outline())
        self.assertIn("Nessun capitolo scritto", str(caso.exception))

    def test_una_scheda_incompleta_viene_rifiutata(self):
        with self.assertRaises(SystemExit) as caso:
            manuale.importa_scheda(self.project, '{"title": "T", "subtitle": "S"}')
        for campo in ("description_paragraphs", "keywords", "categories"):
            self.assertIn(campo, str(caso.exception))

    def test_una_scheda_completa_passa(self):
        dati = {
            "title": "T", "subtitle": "S",
            "description_paragraphs": ["gancio"],
            "keywords": ["una frase"], "categories": ["A"],
        }
        self.assertEqual(manuale.importa_scheda(self.project, json.dumps(dati))["title"], "T")

    # --- stato ------------------------------------------------------------
    def test_il_riepilogo_dice_che_cosa_manca(self):
        outline = self.outline()
        manuale.importa_capitolo(self.project, outline, 1, "Testo. " * 100)
        testo = manuale.riepilogo(self.project)
        self.assertIn("scaletta: sì", testo)
        self.assertIn(f"capitoli: 1 su {len(outline.chapters)}", testo)
        self.assertIn("scheda prodotto: no", testo)


class TestNessunaChiamataAlModello(unittest.TestCase):
    """La linea manuale non deve poter chiamare il modello nemmeno per sbaglio."""

    def test_il_modulo_non_usa_il_client(self):
        sorgente = Path(manuale.__file__).read_text(encoding="utf-8")
        for vietato in ("LLMClient", "complete_json", "client."):
            self.assertNotIn(vietato, sorgente, f"`{vietato}` in manuale.py")

    def test_un_client_in_dry_run_resta_inutilizzato(self):
        """Sanity check: i prompt si costruiscono senza toccare la rete."""
        client = LLMClient(LLMConfig(dry_run=True, verbose=False))
        self.assertEqual(client.usage_report()["calls"], 0)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

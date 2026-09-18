"""Test del reparto di acquisizione: da una scheda Amazon incollata a un libro."""

import json
import tempfile
import unittest
from pathlib import Path

from kdpfactory import concorrente
from kdpfactory.agents.base import REGISTRY, AgentFinding, ReviewAgent
from kdpfactory.llm import LLMClient, LLMConfig
from kdpfactory.models import BookProject

PAGINA = """Gestire il tempo per liberi professionisti Copertina flessibile - 12 marzo 2024
di Mario Esempio (Autore)
4,1 su 5 stelle   128 voti
Prezzo: 14,99 EUR
Copertina flessibile: 210 pagine
n. 42 in Gestione del tempo
Recensioni clienti
3,0 su 5 stelle  Tanta teoria, pochi esempi
Il metodo si capisce ma non ci sono casi concreti. Avrei voluto vedere giornate vere.
2,0 su 5 stelle  Non serve a chi lavora da solo
Parla sempre di team e riunioni. Io sono partita IVA da sola.
5,0 su 5 stelle  Chiaro e scorrevole
Si legge benissimo, la struttura in blocchi e convincente.
"""

PIANO = {
    "titolo": "Il libro nuovo",
    "sottotitolo": "Un sottotitolo",
    "lingua": "it",
    "argomento": "argomento del libro",
    "lettore": "liberi professionisti che lavorano da soli",
    "promessa": "una promessa",
    "genere": "non-fiction",
    "pagine_obiettivo": 140,
    "prezzo": 12.99,
    "parole_chiave": [f"frase di ricerca {i}" for i in range(1, 8)],
    "categorie": ["A / B", "C / D", "E / F"],
    "la_lacuna_che_copre": "mancano gli esempi concreti",
    "che_cosa_tiene": ["la scorrevolezza"],
    "che_cosa_non_fa": ["non parla di team"],
    "argomenti": [f"tema {i}" for i in range(1, 11)],
}


class TestContrattoDeiRevisori(unittest.TestCase):
    """Un revisore che dimentica il contratto JSON produce prosa in silenzio.

    È già successo due volte durante lo sviluppo: la pipeline non se ne accorge
    finché non prova a leggere la risposta, e in dry-run il difetto si vede solo
    eseguendo il comando. Questo test lo intercetta sempre.
    """

    def test_ogni_revisore_chiede_il_json(self):
        senza_contratto = []
        for nome, agente in REGISTRY.items():
            if not isinstance(agente, ReviewAgent):
                continue
            from kdpfactory.agents.base import AgentContext
            from kdpfactory.models import BookSpec

            try:
                blocchi = agente.system(AgentContext(spec=BookSpec(slug="t", title="T")))
            except NotImplementedError:
                continue
            if not any('"findings"' in blocco for blocco in blocchi):
                senza_contratto.append(nome)
        self.assertEqual(senza_contratto, [], f"revisori senza contratto JSON: {senza_contratto}")


class TestPaginaIncollata(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = BookProject(Path(self.tmp.name) / "libro")

    def tearDown(self):
        self.tmp.cleanup()

    def test_le_istruzioni_del_modulo_non_finiscono_nell_analisi(self):
        percorso = concorrente.prepara(self.project, "B0TEST")
        self.assertIn("B0TEST", percorso.read_text(encoding="utf-8"))
        with percorso.open("a", encoding="utf-8") as fh:
            fh.write(PAGINA)
        letto = concorrente.leggi_pagina(self.project)
        self.assertNotIn("Incolla qui sotto", letto)
        self.assertNotIn("recensioni da 2 e 3 stelle", letto)
        self.assertIn("Gestire il tempo", letto)

    def test_una_pagina_mai_creata_lo_dice(self):
        with self.assertRaises(SystemExit) as caso:
            concorrente.leggi_pagina(self.project)
        self.assertIn("concorrente new", str(caso.exception))

    def test_una_pagina_quasi_vuota_ferma_il_reparto(self):
        concorrente.prepara(self.project, "B0TEST")
        client = LLMClient(LLMConfig(dry_run=True, verbose=False))
        with self.assertRaises(SystemExit) as caso:
            concorrente.analizza(self.project, client)
        self.assertIn("sembra vuoto", str(caso.exception))


class TestDalPianoAllaScheda(unittest.TestCase):
    def test_le_pagine_restano_nei_limiti_di_progetto(self):
        corto = concorrente.spec_dal_piano("s", {**PIANO, "pagine_obiettivo": 12}, "A")
        lungo = concorrente.spec_dal_piano("s", {**PIANO, "pagine_obiettivo": 900}, "A")
        assurdo = concorrente.spec_dal_piano("s", {**PIANO, "pagine_obiettivo": "molte"}, "A")
        self.assertEqual(corto.target_pages, 60)
        self.assertEqual(lungo.target_pages, 240)
        self.assertEqual(assurdo.target_pages, 140)

    def test_la_scheda_prodotta_e_valida(self):
        spec = concorrente.spec_dal_piano("il-libro-nuovo", PIANO, "Iris Vane")
        self.assertEqual(spec.validate(), [])
        self.assertEqual(spec.author, "Iris Vane")
        self.assertEqual(len(spec.keywords), 7)
        self.assertEqual(len(spec.categories), 3)

    def test_una_lingua_sconosciuta_ricade_sull_italiano(self):
        spec = concorrente.spec_dal_piano("s", {**PIANO, "lingua": "portoghese"}, "A")
        self.assertEqual(spec.language, "it")


class TestOriginalita(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = BookProject(Path(self.tmp.name) / "libro")

    def tearDown(self):
        self.tmp.cleanup()

    def _risultato(self, severity: str) -> concorrente.Acquisizione:
        return concorrente.Acquisizione(
            asin="B0TEST",
            scheda={"titolo": "Gestire il tempo per liberi professionisti"},
            lacune={},
            piano=PIANO,
            segnalazioni=[
                AgentFinding.from_dict(
                    {
                        "severity": severity,
                        "category": "titolo troppo vicino",
                        "issue": "il titolo riprende quello del libro di partenza",
                        "quote": "Il libro nuovo",
                    },
                    "originalita",
                    None,
                )
            ],
        )

    def test_un_bloccante_impedisce_di_scrivere_la_scheda(self):
        with self.assertRaises(SystemExit) as caso:
            concorrente.scrivi(self.project, self._risultato("bloccante"), "Iris Vane")
        self.assertIn("originalità", str(caso.exception))
        self.assertFalse(self.project.spec_path.exists())

    def test_una_segnalazione_minore_non_blocca(self):
        spec = concorrente.scrivi(self.project, self._risultato("minore"), "Iris Vane")
        self.assertTrue(self.project.spec_path.exists())
        self.assertEqual(spec.title, "Il libro nuovo")

    def test_il_brief_non_consegna_il_libro_di_partenza_a_chi_scrive(self):
        """Il titolo del concorrente sta in un commento, e i commenti non si leggono."""
        concorrente.scrivi(self.project, self._risultato("minore"), "Iris Vane")
        brief_letto = self.project.read_brief()
        self.assertNotIn("Gestire il tempo", brief_letto)
        self.assertNotIn("B0TEST", brief_letto)
        self.assertIn("mancano gli esempi concreti", brief_letto)
        self.assertIn("tema 1", brief_letto)


class TestGiroCompleto(unittest.TestCase):
    """Da pagina incollata a `book.json`, senza spendere token."""

    def test_in_dry_run_il_reparto_arriva_in_fondo(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = BookProject(Path(tmp) / "libro")
            percorso = concorrente.prepara(project, "B0ABCD1234")
            with percorso.open("a", encoding="utf-8") as fh:
                fh.write(PAGINA)
            client = LLMClient(LLMConfig(dry_run=True, verbose=False))

            risultato = concorrente.analizza(project, client, asin="B0ABCD1234")
            self.assertTrue(risultato.scheda.get("titolo"))
            self.assertTrue(risultato.lacune.get("lacune"))
            self.assertTrue(risultato.piano.get("titolo"))

            spec = concorrente.scrivi(project, risultato, "Iris Vane")
            self.assertEqual(spec.validate(), [])
            self.assertTrue(project.brief_path.exists())

            salvato = json.loads(
                concorrente.acquisizione_path(project).read_text(encoding="utf-8")
            )
            self.assertEqual(salvato["asin"], "B0ABCD1234")
            self.assertIn("scheda", salvato)
            self.assertIn("originalita", salvato)
            self.assertIn("LIBRO DI PARTENZA", concorrente.render(risultato))

"""Le linee rosse legali che si misurano: temi esclusi e riferimenti al concorrente.

Decisione dell'autore del 14 ottobre 2026 (`docs/rischi-legali.md`): niente
libri di salute, diritto, finanza o psicologia, e mai il nome del libro da cui
la fabbrica è partita. b0gjr36xwt, un libro di documentazione clinica per
nurse practitioner, è stato eliminato per questo.
"""

import json
import tempfile
import unittest
from pathlib import Path

from kdpfactory import legale, temi
from kdpfactory.i18n import L
from kdpfactory.models import BookProject, BookSpec


class Rapporto:
    def __init__(self):
        self.voci = []

    def add(self, livello, area, testo):
        self.voci.append((livello, area, testo))


class TestTemiEsclusi(unittest.TestCase):
    def test_le_quattro_famiglie(self):
        casi = {
            "salute": (["Hard Calls, Clear Notes", "documentation for nurse practitioners"],
                       ["MEDICAL / Nursing / Issues"]),
            "diritto": (["Chart Like a Lawyer"], []),
            "finanza": (["Bills in Order"],
                        ["Books > Business & Money > Personal Finance > Budgeting"]),
            "psicologia": (["Calm Your Anxiety"], ["PSYCHOLOGY / Mental Health"]),
        }
        for famiglia, (testi, categorie) in casi.items():
            with self.subTest(famiglia=famiglia):
                trovati = temi.motivi(testi, categorie)
                self.assertTrue(any(t.startswith(famiglia) for t in trovati), trovati)

    def test_i_temi_ammessi_passano(self):
        for testi, categorie in (
            (["Logic Puzzles for Clever Kids", "Brain teasers"], ["GAMES & ACTIVITIES / Puzzles"]),
            (["Soups and Stocks", "A cookbook"], ["COOKING / Courses & Dishes / Soups & Stews"]),
            (["The Night Train Mysteries"], ["Books > Mystery, Thriller & Suspense"]),
        ):
            with self.subTest(testi=testi):
                self.assertEqual(temi.motivi(testi, categorie), [])

    def test_il_concorrente_si_ferma_prima_degli_agenti(self):
        scheda = {"titolo": "Chart Like a Lawyer",
                  "sottotitolo": "Legal-Proof Documentation for Nurses & NPs",
                  "categorie": [{"nome": "Nursing Issues", "rango": 12}]}
        self.assertTrue(temi.per_concorrente(scheda))

    def test_il_banco_di_prova_non_conta(self):
        spec = BookSpec(slug="collaudo", title="Collaudo", banco_di_prova=True,
                        categories=["MEDICAL / Nursing"])
        self.assertEqual(temi.per_libro(spec), [])


class TestConcorrenteNelLibro(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = BookProject(Path(self.tmp.name) / "libro")
        (self.project.root / "concorrente").mkdir(parents=True)
        (self.project.root / "concorrente" / "scheda.json").write_text(json.dumps(
            {"titolo": "The Other Puzzle Book", "autore": "Jane Rival", "asin": "B0TEST1234",
             "editore": "X"}), encoding="utf-8")
        self.spec = BookSpec(slug="libro", title="Night Train Puzzles",
                             categories=["GAMES & ACTIVITIES / Puzzles"])

    def tearDown(self):
        self.tmp.cleanup()

    def test_nome_del_concorrente_nel_testo_e_nella_scheda(self):
        capitoli = [(1, "Uno", "# Uno\n\nUnlike The Other Puzzle Book, this one explains.\n")]
        meta = {"keywords": ["puzzles like jane rival"], "description_paragraphs": ["Fun."]}
        rapporto = Rapporto()
        legale.controlla(self.project, self.spec, capitoli,
                         {"metadata": meta, "cover": {"testi": {"hook": "Better than B0TEST1234"}}},
                         rapporto)
        dove = [v[2] for v in rapporto.voci if v[1] == "CONCORRENTE"]
        self.assertEqual(len(dove), 3, dove)
        # l'editore di due lettere è troppo corto per cercarlo senza falsi allarmi
        self.assertFalse(any("editore" in d for d in dove))

    def test_libro_pulito(self):
        rapporto = Rapporto()
        legale.controlla(self.project, self.spec, [(1, "Uno", "# Uno\n\nA clean chapter.\n")],
                         {}, rapporto)
        self.assertEqual(rapporto.voci, [])

    def test_tema_escluso_e_un_errore_di_qa(self):
        spec = BookSpec(slug="libro", title="Budgeting Made Simple")
        rapporto = Rapporto()
        legale.controlla(self.project, spec, [], {}, rapporto)
        self.assertIn(("errore", "TEMA"), [(v[0], v[1]) for v in rapporto.voci])


class TestDichiarazioneIA(unittest.TestCase):
    def test_non_promette_una_revisione_umana(self):
        # AI Act, art. 50(4), e KDP: il testo scritto dall'IA è «AI-generated»;
        # la frase non può dire che una persona l'ha rivisto se non è vero.
        for lingua in ("en", "it"):
            frase = L(lingua, "ai_disclosure").lower()
            with self.subTest(lingua=lingua):
                self.assertNotIn("review", frase)
                self.assertNotIn("revisione", frase)
                self.assertTrue("artificial intelligence" in frase or "intelligenza artificiale" in frase)


if __name__ == "__main__":
    unittest.main()

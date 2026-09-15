"""Test della linea enigmistica: il valore del prodotto è che i casi sono dimostrati."""

import tempfile
import unittest
from pathlib import Path
from random import Random

from kdpfactory import backup, kdpspecs
from kdpfactory.agents import AgentContext, get_agent
from kdpfactory.models import BookProject
from kdpfactory.puzzle import generate_book, solver
from kdpfactory.puzzle.book import PuzzleSpec, build, check, default_book_spec
from kdpfactory.puzzle.generator import build_cast, generate_case, shared_attributes
from kdpfactory.puzzle.model import Attribute, Case, Is, IsNot, Suspect
from kdpfactory.puzzle.theme import CASES, EXAMPLE

SEED = 20260915

HAT = Attribute(
    key="hat", label="Hat", noun="hat", values=("fedora", "bowler", "cloche"),
    template="wore {a} {value}", negative_template="did not wear {a} {value}",
)
COAT = Attribute(
    key="coat", label="Coat", noun="coat", values=("navy", "olive"),
    template="wore {a} {value} coat", negative_template="did not wear {a} {value} coat",
)


def suspect(name, hat, coat):
    return Suspect(name=name, attrs=(("hat", hat), ("coat", coat)))


SMALL_CAST = [
    suspect("Mr A", "fedora", "navy"),
    suspect("Mr B", "fedora", "olive"),
    suspect("Mr C", "bowler", "navy"),
    suspect("Mr D", "cloche", "olive"),
]


class TestSolver(unittest.TestCase):
    def test_isola_un_solo_sospetto(self):
        clues = [Is("hat", "fedora"), Is("coat", "navy")]
        self.assertEqual(solver.survivors(SMALL_CAST, clues), [SMALL_CAST[0]])
        self.assertTrue(solver.is_unique(SMALL_CAST, clues))

    def test_riconosce_un_caso_ambiguo(self):
        self.assertFalse(solver.is_unique(SMALL_CAST, [Is("hat", "fedora")]))

    def test_toglie_gli_indizi_superflui(self):
        clues = [Is("hat", "cloche"), Is("coat", "olive"), IsNot("hat", "bowler")]
        kept = solver.minimize(SMALL_CAST, clues)
        self.assertEqual(len(kept), 1)          # il cappello basta da solo
        self.assertTrue(solver.is_unique(SMALL_CAST, kept))

    def test_necessita(self):
        self.assertTrue(solver.all_necessary(SMALL_CAST, [Is("hat", "fedora"), Is("coat", "navy")]))
        self.assertFalse(
            solver.all_necessary(SMALL_CAST, [Is("hat", "cloche"), Is("coat", "olive")])
        )

    def test_traccia_le_eliminazioni(self):
        steps = solver.trace(SMALL_CAST, [Is("hat", "fedora"), Is("coat", "navy")])
        self.assertEqual([(s.before, s.after) for s in steps], [(4, 2), (2, 1)])

    def test_verify_segnala_il_colpevole_sbagliato(self):
        case = Case(
            number=1, title="t", setting="s",
            attributes={"hat": HAT, "coat": COAT},
            suspects=SMALL_CAST,
            clues=[Is("hat", "fedora"), Is("coat", "navy")],
            culprit=SMALL_CAST[2],
        )
        verdict = solver.verify(case)
        self.assertFalse(verdict.ok)
        self.assertTrue(any("colpevole dichiarato" in p for p in verdict.problems))

    def test_verify_segnala_indizi_superflui(self):
        case = Case(
            number=1, title="t", setting="s",
            attributes={"hat": HAT, "coat": COAT},
            suspects=SMALL_CAST,
            clues=[Is("hat", "cloche"), Is("coat", "olive")],
            culprit=SMALL_CAST[3],
        )
        verdict = solver.verify(case)
        self.assertFalse(verdict.ok)
        self.assertTrue(any("superfluo" in p for p in verdict.problems))


class TestGeneratore(unittest.TestCase):
    def test_il_cast_e_il_prodotto_cartesiano(self):
        rng = Random(1)
        attributes, cast = build_cast(CASES[0], rng)
        self.assertEqual(len(cast), CASES[0].cast_size)
        self.assertEqual(len({s.attrs for s in cast}), len(cast))
        self.assertEqual(len({s.name for s in cast}), len(cast))

    def test_cognomi_unici_dentro_un_caso(self):
        """Gli indizi citano i sospetti per cognome: due uguali sarebbero ambigui."""
        rng = Random(2)
        _, cast = build_cast(CASES[-1], rng)
        surnames = [s.name.split()[-1] for s in cast]
        self.assertEqual(len(set(surnames)), len(surnames))

    def test_ogni_caso_generato_supera_la_verifica(self):
        rng = Random(SEED)
        for theme in (EXAMPLE, CASES[0], CASES[5], CASES[-1]):
            case = generate_case(theme, rng)
            verdict = solver.verify(case)
            self.assertTrue(verdict.ok, f"Caso {theme.number}: {verdict.problems}")
            self.assertEqual(verdict.solution, case.culprit)

    def test_solo_indizi_veri_sul_colpevole(self):
        rng = Random(3)
        case = generate_case(CASES[4], rng)
        for clue in case.clues:
            self.assertTrue(clue.keeps(case.culprit), f"indizio falso: {clue}")

    def test_stesso_seme_stesso_libro(self):
        first, second = generate_book(SEED), generate_book(SEED)
        self.assertEqual(
            [c.culprit.name for c in first.cases], [c.culprit.name for c in second.cases]
        )
        self.assertEqual(first.finale.mastermind.name, second.finale.mastermind.name)

    def test_semi_diversi_libri_diversi(self):
        self.assertNotEqual(
            [c.culprit.name for c in generate_book(SEED).cases],
            [c.culprit.name for c in generate_book(SEED + 1).cases],
        )


class TestLibro(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.book = generate_book(SEED)

    def test_dodici_casi_piu_esempio_e_finale(self):
        self.assertEqual(len(self.book.cases), 12)
        self.assertIsNotNone(self.book.example)
        self.assertIsNotNone(self.book.finale)

    def test_difficolta_crescente(self):
        sizes = [len(case.suspects) for case in self.book.cases]
        self.assertEqual(sizes, sorted(sizes))
        self.assertLess(sizes[0], sizes[-1])

    def test_tutti_i_casi_sono_corretti(self):
        for case in [self.book.example, *self.book.cases]:
            self.assertTrue(solver.verify(case).ok, f"caso {case.number}")

    def test_il_finale_si_gioca_sui_dodici_colpevoli(self):
        finale = self.book.finale
        culprits = {case.culprit.name for case in self.book.cases}
        self.assertEqual({s.name for s in finale.suspects}, culprits)
        self.assertIn(finale.mastermind.name, culprits)

    def test_il_finale_ha_una_sola_soluzione_e_nessun_indizio_di_troppo(self):
        finale = self.book.finale
        self.assertEqual(solver.survivors(finale.suspects, finale.clues), [finale.mastermind])
        self.assertTrue(solver.all_necessary(finale.suspects, finale.clues))

    def test_il_finale_chiama_in_causa_quasi_tutti_i_casi(self):
        cited = {n for clue in self.book.finale.clues for n in clue.cases}
        cited.add(int(self.book.finale.mastermind.get("case")))
        self.assertGreaterEqual(len(cited), 8)

    def test_gli_attributi_condivisi_permettono_i_confronti(self):
        common = shared_attributes(self.book.cases)
        self.assertGreaterEqual(len(common), 2)
        for case in self.book.cases:
            for key in common:
                self.assertIn(key, case.attributes)

    def test_le_risposte_sono_esportabili(self):
        answers = self.book.answers()
        self.assertEqual(len(answers["cases"]), 12)
        self.assertEqual(answers["finale"]["mastermind"], self.book.finale.mastermind.name)


class TestProduzione(unittest.TestCase):
    """Produzione completa: PDF, copertina, scheda, controlli."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        backup.configure(enabled=False)
        cls.project = BookProject(Path(cls.tmp.name) / "enigmi")
        cls.project.ensure_dirs()
        cls.spec = default_book_spec("enigmi", "Autore Test")
        cls.spec.save(cls.project.spec_path)
        cls.result = build(cls.project, cls.spec, PuzzleSpec(seed=SEED))

    @classmethod
    def tearDownClass(cls):
        backup.configure(enabled=True, directory=None)
        cls.tmp.cleanup()

    def test_pagine_nei_limiti_di_progetto(self):
        self.assertGreaterEqual(self.result["pages"], kdpspecs.PROJECT_MIN_PAGES)
        self.assertLessEqual(self.result["pages"], kdpspecs.PROJECT_MAX_PAGES)

    def test_numero_di_pagine_pari(self):
        self.assertEqual(self.result["pages"] % 2, 0)

    def test_interno_e_copertina_esistono(self):
        self.assertTrue(self.result["interior"].exists())
        self.assertTrue(self.result["cover"].exists())

    def test_le_risposte_sono_salvate_fuori_dal_libro(self):
        answers = self.project.build_dir / "answers.json"
        self.assertTrue(answers.exists())

    def test_controlli_senza_errori(self):
        report = check(self.project, self.spec, self.result["pages"], self.result["interior"])
        self.assertTrue(report.ok, f"errori: {[str(f) for f in report.errors]}")

    def test_nessun_font_mancante(self):
        report = check(self.project, self.spec, self.result["pages"], self.result["interior"])
        self.assertFalse([f for f in report.findings if f.code == "FONT" and f.level == "errore"])

    def test_agente_impaginazione_non_trova_difetti_bloccanti(self):
        state = self.project.load_state()
        result = get_agent("impaginazione").run(
            AgentContext(
                spec=self.spec,
                pdf_path=self.result["interior"],
                pages=self.result["pages"],
                chapter_pages=state["build"]["chapter_pages"],
            )
        )
        blocking = [f for f in result.findings if f.severity in ("bloccante", "importante")]
        self.assertEqual(blocking, [], f"difetti: {[f.issue for f in blocking]}")

    def test_i_capitoli_si_aprono_a_destra(self):
        pages = self.project.load_state()["build"]["chapter_pages"]
        self.assertTrue(pages)
        for title, page in pages.items():
            self.assertEqual(page % 2, 1, f"«{title}» si apre a pagina {page}")


if __name__ == "__main__":
    unittest.main()

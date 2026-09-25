"""Le parti: nella scaletta, nell'indice del PDF, nell'EPUB e nel revisore.

Un indice di trenta righe tutte uguali, nell'anteprima Amazon, non dice come
è costruito il libro; cinque parti con i loro capitoli sì. Le parti sono
facoltative: un libro senza deve uscire identico a prima.
"""

import tempfile
import unittest
import zipfile
from pathlib import Path

import pymupdf

from kdpfactory import epub, typeset
from kdpfactory.agents.scaletta import esamina
from kdpfactory.i18n import numero_romano, part_label
from kdpfactory.models import BookSpec, ChapterPlan, Outline, PartPlan

TESTO = "A paragraph of plain test prose, long enough to fill a line or two. " * 30

TITOLI = [
    "Why the Chair Matters",
    "The Hour Before",
    "Counting the Stairs",
    "What the Record Holds",
    "Names and Dates",
    "The Weeks After",
]


def libro(parti: list[PartPlan], quanti: int = 6) -> tuple[Outline, list[tuple[int, str, str]]]:
    capitoli = [
        ChapterPlan(number=n, title=TITOLI[(n - 1) % len(TITOLI)] + ("" if n <= 6 else f" {n}"))
        for n in range(1, quanti + 1)
    ]
    outline = Outline(title="Test Book", chapters=capitoli, parts=parti)
    return outline, [(c.number, c.title, TESTO) for c in capitoli]


def spec() -> BookSpec:
    return BookSpec(slug="parti", title="Test Book", language="en", target_pages=60)


DUE_PARTI = [PartPlan("Inside the Room", 1), PartPlan("Outside the Room", 4)]


class TestScaletta(unittest.TestCase):
    def test_le_parti_sopravvivono_al_salvataggio(self):
        outline, _ = libro(DUE_PARTI)
        riletta = Outline.from_dict(outline.to_dict())
        self.assertEqual([(p.title, p.first_chapter) for p in riletta.parts],
                         [("Inside the Room", 1), ("Outside the Room", 4)])

    def test_una_scaletta_senza_parti_resta_com_era(self):
        outline, _ = libro([])
        self.assertNotIn("parts", outline.to_dict())
        self.assertEqual(Outline.from_dict({"title": "T", "chapters": []}).parts, [])

    def test_la_parte_si_riconosce_dal_primo_capitolo(self):
        outline, _ = libro(list(reversed(DUE_PARTI)))
        self.assertEqual(outline.part_opening(4)[0], 2)
        self.assertEqual(outline.part_opening(1)[1].title, "Inside the Room")
        self.assertIsNone(outline.part_opening(2))

    def test_la_rinumerazione_porta_con_se_le_parti(self):
        """La scaletta arriva senza introduzione: il sistema la aggiunge in testa,
        tutti i numeri scalano di uno, e le parti devono scalare con loro."""
        from kdpfactory import planner, writer

        s = BookSpec(slug="p", title="T", language="en", target_pages=60,
                     include_intro=True, include_conclusion=False)
        capitoli = [ChapterPlan(number=n, title=TITOLI[n - 1]) for n in range(1, 7)]
        grezza = Outline(title="T", chapters=capitoli, parts=[PartPlan("A", 1), PartPlan("B", 4)])
        fatta = writer.normalize_outline(s, grezza, planner.build_budget(s, planner.words_per_page(s)))
        self.assertEqual(fatta.chapters[0].role, "intro")
        self.assertEqual([p.first_chapter for p in fatta.parts], [2, 5])
        self.assertEqual(fatta.chapters[4].title, "What the Record Holds")

    def test_numeri_romani(self):
        self.assertEqual([numero_romano(n) for n in (1, 4, 5, 9, 14, 40)],
                         ["I", "IV", "V", "IX", "XIV", "XL"])
        self.assertEqual(part_label("en", 3), "Part III")
        self.assertEqual(part_label("it", 2), "Parte II")


class TestImpaginazione(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cartella = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def pagine(self, parti: list[PartPlan]) -> list[str]:
        outline, capitoli = libro(parti)
        esito = typeset.typeset(spec(), outline, capitoli, self.cartella / "libro.pdf")
        with pymupdf.open(esito.pdf_path) as pdf:
            return [pagina.get_text() for pagina in pdf]

    def test_l_indice_mette_i_capitoli_sotto_le_parti(self):
        testi = self.pagine(DUE_PARTI)
        indice = next(t for t in testi if "Contents" in t)
        piatto = " ".join(indice.split())
        for voce in ("Part I — Inside the Room", "Part II — Outside the Room", "Counting the Stairs",
                     "What the Record Holds"):
            self.assertIn(voce, piatto)
        self.assertLess(piatto.index("Counting the Stairs"), piatto.index("Part II"))
        self.assertLess(piatto.index("Part II"), piatto.index("What the Record Holds"))

    def test_la_pagina_di_parte_sta_a_destra_e_non_ha_folio(self):
        testi = self.pagine(DUE_PARTI)
        # l'etichetta è spaziata lettera per lettera: si confronta senza spazi
        pagine_di_parte = [
            i + 1 for i, t in enumerate(testi)
            if any("".join(riga.split()) == "PARTII" for riga in t.splitlines())
        ]
        self.assertEqual(len(pagine_di_parte), 1)
        numero = pagine_di_parte[0]
        self.assertEqual(numero % 2, 1, "una parte si apre sempre su una pagina dispari")
        righe = [r.strip() for r in testi[numero - 1].splitlines() if r.strip()]
        self.assertFalse(any(r.isdigit() for r in righe), f"folio sulla pagina di parte: {righe}")
        # e il capitolo che la segue si apre anche lui a destra, dopo una bianca
        seguente = next(i + 1 for i, t in enumerate(testi) if "What the Record Holds" in t
                        and "Contents" not in t)
        self.assertEqual(seguente, numero + 2)

    def test_senza_parti_nessuna_pagina_in_piu(self):
        testi = self.pagine([])
        self.assertFalse(any("PARTI" in "".join(t.split()) for t in testi))
        self.assertFalse(any("Part I —" in t for t in testi))


class TestEpub(unittest.TestCase):
    def test_la_navigazione_annida_i_capitoli_nella_loro_parte(self):
        outline, capitoli = libro(DUE_PARTI)
        with tempfile.TemporaryDirectory() as tmp:
            percorso = Path(tmp) / "libro.epub"
            epub.build_epub(spec(), outline, capitoli, percorso)
            with zipfile.ZipFile(percorso) as zf:
                nav = zf.read("OEBPS/nav.xhtml").decode("utf-8")
                nomi = zf.namelist()
        self.assertIn("OEBPS/part01.xhtml", nomi)
        self.assertIn("OEBPS/part02.xhtml", nomi)
        seconda = nav.index('href="part02.xhtml"')
        self.assertLess(nav.index('href="ch03.xhtml"'), seconda)
        self.assertGreater(nav.index('href="ch04.xhtml"'), seconda)
        self.assertEqual(nav.count("<ol>"), 3, "un elenco principale e uno per ciascuna parte")


class TestRevisore(unittest.TestCase):
    def categorie(self, outline: Outline) -> set[str]:
        return {r.category for r in esamina(outline, spec())}

    def test_parti_corrette_nessun_rilievo(self):
        outline, _ = libro(DUE_PARTI)
        self.assertFalse({c for c in self.categorie(outline) if "part" in c})

    def test_una_parte_su_un_capitolo_che_non_c_e(self):
        outline, _ = libro([PartPlan("Inside the Room", 1), PartPlan("Nowhere", 9)])
        rilievi = [r for r in esamina(outline, spec()) if r.category == "parte senza capitolo"]
        self.assertEqual(rilievi[0].severity, "bloccante")

    def test_parti_in_disordine(self):
        outline, _ = libro([PartPlan("Outside the Room", 4), PartPlan("Inside the Room", 1)])
        self.assertIn("parti in disordine", self.categorie(outline))

    def test_capitoli_prima_della_prima_parte(self):
        outline, _ = libro([PartPlan("Outside the Room", 3)])
        self.assertIn("capitoli fuori dalle parti", self.categorie(outline))

    def test_un_introduzione_puo_restare_fuori(self):
        outline, _ = libro([PartPlan("Inside the Room", 2), PartPlan("Outside the Room", 4)])
        outline.chapters[0].role = "intro"
        self.assertNotIn("capitoli fuori dalle parti", self.categorie(outline))

    def test_una_parte_di_un_capitolo_solo(self):
        outline, _ = libro([PartPlan("Inside the Room", 1), PartPlan("Last Word", 6)])
        self.assertIn("parte di un solo capitolo", self.categorie(outline))

    def test_un_indice_lungo_senza_parti_lo_dice(self):
        outline, _ = libro([], quanti=24)
        self.assertIn("indice senza parti", self.categorie(outline))
        breve, _ = libro([], quanti=12)
        self.assertNotIn("indice senza parti", self.categorie(breve))


if __name__ == "__main__":
    unittest.main()

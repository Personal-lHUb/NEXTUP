"""Test della diagnostica: i numeri su cui ragiona il team di miglioramento.

Se questi sbagliano, il team propone lavoro inutile — o peggio, non segnala
quello che conta. Sono i test più importanti del modulo: non verificano che
il codice giri, verificano che i fatti siano veri.
"""

import json
import tempfile
import unittest
from pathlib import Path

from kdpfactory import diagnostica
from kdpfactory.diagnostica import BookReport, Finding, _ricorrenze
from kdpfactory.models import BookProject, BookSpec


def demo_spec(**overrides) -> BookSpec:
    data = dict(
        slug="prova", title="Il Metodo delle Tre Ore",
        subtitle="Recuperare una mattina di lavoro profondo",
        author="Marco Ferri", language="it", topic="produttività",
        audience="professionisti", promise="tre ore al giorno",
        genre="non-fiction", target_pages=140, trim="6x9", paper="cream",
        keywords=[], categories=[],
    )
    data.update(overrides)
    return BookSpec(**data)


class TestScheda(unittest.TestCase):
    """I limiti della scheda KDP sono numeri del modulo, non opinioni."""

    def scheda(self, metadata: dict, spec: BookSpec | None = None) -> BookReport:
        report = BookReport(slug="prova")
        diagnostica._scheda({"metadata": metadata}, spec or demo_spec(), report)
        return report

    def test_slot_vuoti_sono_ad_alto_impatto(self):
        report = self.scheda({"keywords": ["logic puzzles for adults"]})
        finding = next(f for f in report.rilievi if "slot disponibili" in f.fatto)
        self.assertEqual(finding.impatto, "alto")
        self.assertIn("6 slot vuoti", finding.fatto)

    def test_parola_chiave_gia_nel_titolo_e_uno_slot_buttato(self):
        report = self.scheda({
            "title": "Il Metodo delle Tre Ore",
            "keywords": ["metodo per la produttività", "svegliarsi presto"],
        })
        finding = next(f for f in report.rilievi if "già nel titolo" in f.fatto)
        self.assertEqual(finding.impatto, "alto")
        self.assertIn("metodo per la produttività", finding.fatto)

    def test_parola_chiave_diversa_dal_titolo_non_viene_segnalata(self):
        report = self.scheda({"title": "Tre Ore", "keywords": ["svegliarsi presto"]})
        self.assertFalse([f for f in report.rilievi if "già nel titolo" in f.fatto])

    def test_parole_chiave_che_si_sovrappongono(self):
        report = self.scheda({"keywords": ["logic puzzles adults", "adults logic puzzles"]})
        self.assertTrue(any("si sovrappongono" in f.fatto for f in report.rilievi))

    def test_parole_chiave_generiche(self):
        report = self.scheda({"keywords": ["libro regalo"]})
        self.assertTrue(any("generiche" in f.fatto for f in report.rilievi))

    def test_la_soglia_del_taglio_e_una_sola_per_tutto_il_sistema(self):
        """Il numero che misura la diagnostica è lo stesso che riceve chi scrive
        la scheda: due copie dello stesso limite prima o poi divergono."""
        from kdpfactory import kdpspecs, prompts
        from kdpfactory.models import ChapterPlan, Outline

        self.assertEqual(diagnostica.TITLE_TRUNCATION_CHARS, kdpspecs.TITLE_TRUNCATION_CHARS)
        testo = prompts.metadata_prompt(
            demo_spec(), Outline(title="T", chapters=[ChapterPlan(number=1, title="C")]), "x"
        )
        self.assertIn(f"tagliato dopo {kdpspecs.TITLE_TRUNCATION_CHARS} caratteri", testo)
        # e si misura sulla stringa intera, non sul solo titolo
        self.assertIn("«Titolo: Sottotitolo»", testo)

    def test_titolo_troncato_nei_risultati(self):
        lungo = "Un titolo deliberatamente lunghissimo che nei risultati di ricerca non ci sta"
        report = self.scheda({}, demo_spec(title=lungo, subtitle=""))
        self.assertGreater(len(lungo), diagnostica.TITLE_TRUNCATION_CHARS)
        self.assertTrue(any("tronca" in f.fatto for f in report.rilievi))

    def test_il_taglio_si_misura_su_titolo_piu_sottotitolo(self):
        """È la stringa intera che Amazon tronca, non il solo titolo.

        Un titolo da 30 caratteri passa; con un sottotitolo da 40 la stringa
        che compare nei risultati ne fa 72, e la promessa sparisce dopo i
        puntini.
        """
        spec = demo_spec(title="T" * 30, subtitle="S" * 40)
        report = self.scheda({}, spec)
        self.assertEqual(report.scheda["titolo_caratteri"], 30)
        self.assertEqual(report.scheda["titolo_piu_sottotitolo"], 72)
        self.assertTrue(any("tronca" in f.fatto for f in report.rilievi))

    def test_book_json_batte_il_segnaposto_della_lavorazione(self):
        """`build/metadata.json` è una proposta del modello; in dry-run è finto.

        Se vince lui, la diagnostica misura il segnaposto e dichiara conforme
        un titolo che non lo è.
        """
        spec = demo_spec(title="T" * 30, subtitle="S" * 40)
        report = self.scheda(
            {"title": "Titolo segnaposto", "subtitle": "Sottotitolo segnaposto"}, spec
        )
        self.assertEqual(report.scheda["titolo_caratteri"], 30)
        self.assertEqual(report.scheda["titolo_piu_sottotitolo"], 72)

    def test_la_scheda_prodotta_vale_dove_book_json_tace(self):
        """Parole chiave e categorie di un libro mai compilato a mano."""
        report = self.scheda({"keywords": ["logic puzzles for adults"], "categories": ["A"]})
        self.assertEqual(report.scheda["parole_chiave_usate"], 1)
        self.assertEqual(report.scheda["categorie_usate"], 1)

    def test_i_primi_caratteri_della_descrizione_sono_estratti(self):
        testo = "A" * 400
        report = self.scheda({"description_paragraphs": [testo]})
        self.assertEqual(
            len(report.scheda["prima_dello_stacco"]), diagnostica.DESCRIPTION_FOLD_CHARS
        )

    def test_scheda_completa_non_produce_rilievi_sulla_scheda(self):
        report = self.scheda({
            "keywords": [
                "svegliarsi presto senza sveglia", "lavoro profondo concentrazione",
                "gestione del tempo per liberi professionisti", "routine mattutina efficace",
                "smettere di procrastinare oggi", "abitudini per imprenditori",
                "produttività senza burnout",
            ],
            "categories": ["A", "B", "C"],
            "description_paragraphs": ["x" * 2000],
        }, demo_spec(title="Tre Ore", subtitle="Il metodo"))
        self.assertEqual([f.fatto for f in report.rilievi if f.area == "scheda"], [])


class TestEconomia(unittest.TestCase):
    def test_copie_per_ripagare_i_token(self):
        report = BookReport(slug="prova")
        diagnostica._economia(
            demo_spec(), {"usage": {"estimated_cost_usd": 6.0}}, 120, report
        )
        royalty = report.economia["royalty_per_copia"]
        self.assertGreater(royalty, 0)
        self.assertAlmostEqual(
            report.economia["copie_per_ripagare_api"], round(6.0 / royalty, 1), places=1
        )
        self.assertTrue(any("si ripaga con" in f.fatto for f in report.rilievi))

    def test_costo_zero_dichiarato_e_non_allarmante(self):
        report = BookReport(slug="prova")
        diagnostica._economia(demo_spec(), {}, 120, report)
        finding = next(f for f in report.rilievi if f.area == "economia")
        self.assertEqual(finding.impatto, "basso")
        # zero copie per ripagare zero dollari: è la risposta giusta, non un
        # dato mancante — la linea enigmistica produce libri così
        self.assertEqual(report.economia["copie_per_ripagare_api"], 0.0)
        self.assertEqual(report.economia["costo_api_usd"], 0.0)

    def test_piu_pagine_costano_piu_stampa(self):
        corto, lungo = BookReport(slug="a"), BookReport(slug="b")
        diagnostica._economia(demo_spec(), {}, 80, corto)
        diagnostica._economia(demo_spec(), {}, 240, lungo)
        self.assertGreater(lungo.economia["costo_stampa"], corto.economia["costo_stampa"])


class TestProduzione(unittest.TestCase):
    def test_troppe_iterazioni_sono_un_costo(self):
        report = BookReport(slug="prova")
        diagnostica._produzione({"build": {"iterazioni": 4, "pagine": 140}},
                                demo_spec(), report)
        finding = next(f for f in report.rilievi if "passate di impaginazione" in f.fatto)
        self.assertEqual(finding.impatto, "alto")

    def test_una_sola_passata_non_si_segnala(self):
        report = BookReport(slug="prova")
        diagnostica._produzione({"build": {"iterazioni": 1, "pagine": 140}},
                                demo_spec(), report)
        self.assertEqual(report.rilievi, [])

    def test_scarto_sulle_pagine(self):
        report = BookReport(slug="prova")
        diagnostica._produzione({"build": {"iterazioni": 1, "pagine": 82}},
                                demo_spec(target_pages=100), report)
        self.assertTrue(any("18% di scarto" in f.fatto for f in report.rilievi))


class TestRicorrenze(unittest.TestCase):
    """Un difetto su un libro è del libro; su tre libri è del sistema."""

    def report(self, slug: str, codici: list[str]) -> BookReport:
        return BookReport(slug=slug, qualita={"per_codice": dict.fromkeys(codici, 1)})

    def test_un_solo_libro_non_fa_ricorrenza(self):
        self.assertEqual(_ricorrenze([self.report("a", ["FONT"])]), [])

    def test_due_libri_fanno_una_ricorrenza(self):
        findings = _ricorrenze([self.report("a", ["FONT"]), self.report("b", ["FONT"])])
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].impatto, "medio")

    def test_tre_libri_alzano_limpatto(self):
        findings = _ricorrenze([self.report(s, ["FONT"]) for s in ("a", "b", "c")])
        self.assertEqual(findings[0].impatto, "alto")
        self.assertIn("non è un difetto del libro", findings[0].fatto)

    def test_i_problemi_di_copertina_entrano_nelle_ricorrenze(self):
        libri = [
            BookReport(slug=s, copertina={"problemi": ["Contrasto troppo basso"]})
            for s in ("a", "b")
        ]
        self.assertTrue(any("COPERTINA" in f.fatto for f in _ricorrenze(libri)))


class TestQualita(unittest.TestCase):
    def test_le_voci_informative_non_sono_difetti(self):
        """Un controllo passato produce una voce `info`: contarla fra i difetti
        farebbe risultare come ricorrente ciò che invece funziona sempre."""
        with tempfile.TemporaryDirectory() as tmp:
            project = BookProject(Path(tmp))
            project.ensure_dirs()
            (project.build_dir / "qa-report.json").write_text(json.dumps({
                "findings": [
                    {"level": "info", "code": "FONT", "message": "tutto a posto"},
                    {"level": "avviso", "code": "IMPAGINAZIONE", "message": "riga vedova"},
                    {"level": "errore", "code": "PAGINE", "message": "fuori intervallo"},
                ]
            }), encoding="utf-8")
            report = BookReport(slug="prova")
            diagnostica._qualita(project, {}, report)

        self.assertEqual(report.qualita["errori"], 1)
        self.assertEqual(report.qualita["avvisi"], 1)
        self.assertNotIn("FONT", report.qualita["per_codice"])
        self.assertTrue(any("bloccanti" in f.fatto for f in report.rilievi))


class TestBanchiDiProva(unittest.TestCase):
    """L'attrezzatura di prova non è un prodotto: fuori dai conti.

    `collaudo` ha per forza la scheda vuota e il manoscritto segnaposto. Se
    entra nel rapporto, i suoi difetti si presentano come rilievi ad alto
    impatto su un libro — e il team di miglioramento apre il piano di lavoro
    su rumore prodotto dal banco di prova.
    """

    def banco(self, tmp: Path, slug: str, **overrides) -> None:
        cartella = tmp / slug
        cartella.mkdir()
        demo_spec(slug=slug, **overrides).save(cartella / "book.json")

    def test_il_banco_non_entra_nel_rapporto(self):
        root = Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as tmp:
            libri = Path(tmp)
            self.banco(libri, "collaudo", banco_di_prova=True)
            self.banco(libri, "libro-vero")
            system = diagnostica.analyse(libri, root)

        self.assertEqual([b.slug for b in system.libri], ["libro-vero"])
        # l'esclusione si dichiara, non si nasconde: nei totali c'è scritta
        self.assertEqual(system.totali["banchi_di_prova_esclusi"], ["collaudo"])
        self.assertNotIn(
            "collaudo", json.dumps([b.to_dict() for b in system.libri], ensure_ascii=False)
        )

    def test_si_possono_misurare_lo_stesso_chiedendolo(self):
        root = Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as tmp:
            libri = Path(tmp)
            self.banco(libri, "collaudo", banco_di_prova=True)
            system = diagnostica.analyse(libri, root, includi_banchi=True)

        self.assertEqual([b.slug for b in system.libri], ["collaudo"])
        self.assertEqual(system.totali["banchi_di_prova_esclusi"], [])

    def test_il_collaudo_del_progetto_e_dichiarato_banco(self):
        """Il marcatore sta in `books/collaudo/book.json`, non in un elenco nel codice."""
        root = Path(__file__).resolve().parent.parent
        spec = BookSpec.load(root / "books" / "collaudo" / "book.json")
        self.assertTrue(spec.banco_di_prova)


class TestRapportoCompleto(unittest.TestCase):
    def test_gira_sui_libri_veri_e_si_salva(self):
        root = Path(__file__).resolve().parent.parent
        system = diagnostica.analyse(root / "books", root, includi_banchi=True)
        self.assertGreater(system.totali["libri"], 0)
        # deve essere serializzabile: è il file che legge il team di agenti
        json.dumps(system.to_dict(), ensure_ascii=False)
        self.assertIn("DIAGNOSTICA DEL SISTEMA", diagnostica.render(system))

    def test_senza_libri_il_rapporto_lo_dice(self):
        """Oggi è il caso vero: in `books/` c'è solo il banco di prova."""
        root = Path(__file__).resolve().parent.parent
        system = diagnostica.analyse(root / "books", root)
        testo = diagnostica.render(system)

        self.assertEqual(system.libri, [])
        self.assertEqual(system.totali["rilievi_ad_alto_impatto"], 0)
        self.assertIn("Nessun libro da misurare", testo)
        self.assertIn("collaudo", testo)
        # le misure sul codice restano: non dipendono dai libri
        self.assertGreater(system.codice["righe_codice"], 0)

    def test_i_rilievi_sono_ordinati_per_impatto(self):
        report = BookReport(slug="prova", rilievi=[
            Finding("scheda", "basso", "c"),
            Finding("scheda", "alto", "a"),
            Finding("scheda", "medio", "b"),
        ])
        report.rilievi.sort(key=lambda f: {"alto": 0, "medio": 1, "basso": 2}[f.impatto])
        self.assertEqual([f.fatto for f in report.rilievi], ["a", "b", "c"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

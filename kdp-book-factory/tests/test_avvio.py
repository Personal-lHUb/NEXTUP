"""Le domande d'avvio: sempre le stesse, per ogni libro nuovo, e le risposte lavorano da sole."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from kdpfactory import avvio, backup, concorrente, coverbrief
from kdpfactory.models import BookProject, BookSpec

PIANO = {
    "titolo": "Il libro nuovo",
    "sottotitolo": "Un sottotitolo",
    "lingua": "it",
    "argomento": "argomento del libro",
    "lettore": "lettori di prova",
    "promessa": "una promessa",
    "genere": "non-fiction",
    "categoria": "full",
    "pagine_obiettivo": 140,
    "prezzo": 12.99,
    "parole_chiave": [f"frase di ricerca {i}" for i in range(1, 8)],
    "categorie": ["A / B", "C / D"],
    "argomenti": [f"tema {i}" for i in range(1, 11)],
}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.books = Path(self.tmp.name)
        self.project = BookProject(self.books / "libro")
        backup.configure(enabled=False)
        self.addCleanup(backup.configure, enabled=True, directory=None)

    def tutte(self, **cambi) -> avvio.Avvio:
        risposte = avvio.Avvio()
        valori = {
            "concorrente": "B0CSSJMQP1", "mercato": "amazon.com", "categoria": "concorrente",
            "vantaggi": ["lacune", "pratico"], "vetrina": "copertina", "pseudonimo": "",
            "pagina": "cowork",
        }
        valori.update(cambi)
        self.assertEqual(avvio.registra(risposte, **valori), [])
        return risposte


class TestRisposte(Base):
    def test_l_asin_si_prende_anche_da_un_link(self):
        self.assertEqual(avvio.estrai_asin("https://www.amazon.com/Some-Title/dp/1797031856/ref=sr_1"),
                         "1797031856")
        self.assertEqual(avvio.estrai_asin("b0cssjmqp1"), "B0CSSJMQP1")
        self.assertEqual(avvio.estrai_asin("https://www.amazon.it/gp/product/B0ABCDEFGH?th=1"),
                         "B0ABCDEFGH")
        self.assertEqual(avvio.estrai_asin("un libro sulle bollette"), "")

    def test_una_risposta_sbagliata_non_si_registra(self):
        risposte = avvio.Avvio()
        errori = avvio.registra(risposte, mercato="amazon.de", vantaggi=["lacune", "magia"],
                                concorrente="non lo so")
        self.assertEqual(len(errori), 3)
        self.assertEqual(risposte.mercato, "amazon.com")
        self.assertEqual(risposte.risposte, [])

    def test_le_domande_mancanti_restano_finche_l_autore_non_le_vede(self):
        risposte = avvio.Avvio()
        self.assertEqual(len(risposte.mancanti()), len(avvio.DOMANDE))
        avvio.registra(risposte, mercato="amazon.it")
        self.assertNotIn("mercato", [d.chiave for d in risposte.mancanti()])
        self.assertEqual(risposte.lingua, "it")
        self.assertEqual(risposte.valuta, "EUR")

    def test_si_salva_e_si_rilegge(self):
        risposte = self.tutte()
        avvio.salva(self.project, risposte)
        self.assertEqual(avvio.leggi(self.project), risposte)


class TestDomande(Base):
    def test_il_concorrente_si_chiede_nel_messaggio(self):
        """Fra le opzioni l'autore sceglie «ti do l'ASIN» e l'ASIN non arriva: già successo."""
        giri = avvio.giri(avvio.Avvio(), self.books)
        self.assertIn("concorrente", [d["chiave"] for d in giri["testo"]])
        for giro in giri["giri"]:
            self.assertLessEqual(len(giro), 4)
            for domanda in giro:
                self.assertNotEqual(domanda["chiave"], "concorrente")
                self.assertGreaterEqual(len(domanda["options"]), 2)
                self.assertLessEqual(len(domanda["options"]), 4)
                self.assertLessEqual(len(domanda["header"]), 12)

    def test_gli_pseudonimi_in_uso_diventano_opzioni(self):
        giri = avvio.giri(avvio.Avvio(), self.books)
        self.assertIn("pseudonimo", [d["chiave"] for d in giri["testo"]])

        for slug, nome, banco in (("a", "Claire Halvorsen", False), ("b", "Prova Prova", True)):
            (self.books / slug).mkdir()
            (self.books / slug / "book.json").write_text(
                json.dumps({"author": nome, "banco_di_prova": banco}), encoding="utf-8"
            )
        giri = avvio.giri(avvio.Avvio(), self.books)
        pseudonimo = next(d for g in giri["giri"] for d in g if d["chiave"] == "pseudonimo")
        self.assertIn("Claire Halvorsen", pseudonimo["valori"].values())
        self.assertNotIn("Prova Prova", pseudonimo["valori"].values())


class TestVincoli(Base):
    def test_il_posizionamento_riceve_le_risposte(self):
        avvio.salva(self.project, self.tutte())
        vincoli = concorrente.leggi_vincoli(self.project)
        self.assertIn("amazon.com", vincoli)
        self.assertIn("USD", vincoli)
        self.assertIn(avvio.VANTAGGI["lacune"], vincoli)
        self.assertIn("titolo dev'essere corto", vincoli)

    def test_l_indicazione_dell_editore_resta_e_l_avvio_si_aggiunge(self):
        concorrente.cartella(self.project).mkdir(parents=True)
        concorrente.indicazione_path(self.project).write_text("Nessuna pagina da compilare.\n",
                                                              encoding="utf-8")
        avvio.salva(self.project, self.tutte())
        vincoli = concorrente.leggi_vincoli(self.project)
        self.assertTrue(vincoli.startswith("Nessuna pagina da compilare."))
        self.assertIn("domande d'avvio", vincoli)
        self.assertIn("Solo questa.", concorrente.leggi_vincoli(self.project, "Solo questa."))

    def test_le_risposte_battono_il_piano(self):
        avvio.salva(self.project, self.tutte(categoria="medium", pseudonimo="Claire Halvorsen"))
        risultato = concorrente.Acquisizione(piano=dict(PIANO))
        with contextlib.redirect_stdout(io.StringIO()):
            spec = concorrente.scrivi(self.project, risultato, "Autore Anonimo")
        self.assertEqual(spec.language, "en")
        self.assertEqual(spec.content_type, "medium")
        self.assertEqual(spec.author, "Claire Halvorsen")

    def test_come_il_concorrente_lascia_la_categoria_al_piano(self):
        avvio.salva(self.project, self.tutte())
        risultato = concorrente.Acquisizione(piano=dict(PIANO))
        with contextlib.redirect_stdout(io.StringIO()):
            spec = concorrente.scrivi(self.project, risultato, "Nome Scelto")
        self.assertEqual(spec.content_type, "full")
        self.assertEqual(spec.author, "Nome Scelto")


class TestCowork(Base):
    def test_con_l_asin_chiede_la_pagina(self):
        nome, testo = avvio.richiesta_cowork(self.tutte(), "libro", "ramo-x", "config/leggimi.md")
        self.assertEqual(nome, "cowork-concorrente.md")
        self.assertIn("https://www.amazon.com/dp/B0CSSJMQP1", testo)
        self.assertIn("cowork-concorrente-risposta.md", testo)
        self.assertIn("ramo-x", testo)
        self.assertIn("**Copertina.**", testo)
        self.assertIn("alla lettera", testo)
        # un ASIN Audible non ha pagine né classifica in Books: si passa al cartaceo
        self.assertIn("Audible o Kindle", testo)

    def test_senza_copertina_non_la_chiede(self):
        _, testo = avvio.richiesta_cowork(self.tutte(vetrina="prezzo"), "libro", "r", "l")
        self.assertNotIn("**Copertina.**", testo)
        self.assertIn("6. **Vicini di scaffale.**", testo)

    def test_con_la_nicchia_chiede_i_primi_venti(self):
        risposte = avvio.Avvio()
        avvio.registra(risposte, nicchia="household budgeting", mercato="amazon.co.uk")
        nome, testo = avvio.richiesta_cowork(risposte, "libro", "r", "l")
        self.assertEqual(nome, "cowork-nicchia.md")
        self.assertIn("household budgeting", testo)
        self.assertIn("GBP", testo)

    def test_la_risposta_di_cowork_fa_da_pagina(self):
        concorrente.prepara(self.project, "B0CSSJMQP1")
        concorrente.risposta_cowork_path(self.project).write_text(
            "Esito: completa\n\n" + "parola " * 60, encoding="utf-8"
        )
        self.assertTrue(concorrente.leggi_pagina(self.project).startswith("Esito: completa"))


class TestComando(Base):
    def main(self, *argomenti):
        from kdpfactory import cli

        uscita = io.StringIO()
        with contextlib.redirect_stdout(uscita):
            cli.main(["--no-backup", "--books-dir", str(self.books), "avvio", "libro", *argomenti])
        return uscita.getvalue()

    def test_senza_risposte_non_scrive_niente(self):
        testo = self.main()
        self.assertIn("Da chiedere all'autore", testo)
        self.assertFalse(avvio.percorso(self.project).exists())

    def test_finite_le_domande_prepara_la_fase_zero(self):
        self.main("--concorrente", "https://www.amazon.com/dp/B0CSSJMQP1", "--mercato", "amazon.com")
        cartella = concorrente.cartella(self.project)
        self.assertFalse((cartella / "cowork-concorrente.md").exists())

        testo = self.main("--predefinite")
        self.assertIn("Domande d'avvio complete", testo)
        for nome in ("avvio.json", "pagina.md", "copertina.md", "cowork-concorrente.md"):
            self.assertTrue((cartella / nome).exists(), nome)

    def test_una_richiesta_con_risposta_non_si_riscrive(self):
        self.main("--concorrente", "B0CSSJMQP1", "--predefinite")
        richiesta = concorrente.cartella(self.project) / "cowork-concorrente.md"
        prima = richiesta.read_text(encoding="utf-8")
        (richiesta.parent / "cowork-concorrente-risposta.md").write_text("Esito: completa\n",
                                                                         encoding="utf-8")
        testo = self.main("--vetrina", "prezzo")
        self.assertIn("-2.md", testo)
        self.assertEqual(richiesta.read_text(encoding="utf-8"), prima)

    def test_il_concorrente_non_ha_default(self):
        testo = self.main("--predefinite")
        self.assertIn("Quale libro deve sfidare", testo)
        self.assertFalse((concorrente.cartella(self.project) / "cowork-concorrente.md").exists())


class TestImporta(Base):
    """La linea manuale: i quattro agenti li chiama la sessione, i file chiudono la fase 0."""

    def scrivi_reparto(self, findings=()):
        cartella = concorrente.cartella(self.project)
        cartella.mkdir(parents=True, exist_ok=True)
        for nome, dati in (
            ("scheda.json", {"titolo": "Il libro di partenza"}),
            ("lacune.json", {"lacune": []}),
            ("piano.json", PIANO),
            ("originalita.json", {"notes": "indipendente", "findings": list(findings)}),
        ):
            (cartella / nome).write_text(json.dumps(dati), encoding="utf-8")

    def test_senza_un_agente_non_si_importa(self):
        self.scrivi_reparto()
        (concorrente.cartella(self.project) / "lacune.json").unlink()
        with self.assertRaises(SystemExit) as caso:
            concorrente.importa(self.project)
        self.assertIn("analista-recensioni", str(caso.exception))

    def test_l_importazione_porta_l_avvio_fino_a_book_json(self):
        avvio.salva(self.project, self.tutte(pseudonimo="Claire Halvorsen"))
        self.scrivi_reparto()
        risultato = concorrente.importa(self.project)
        self.assertEqual(risultato.asin, "B0CSSJMQP1")
        self.assertIn("domande d'avvio", risultato.indicazione)
        with contextlib.redirect_stdout(io.StringIO()):
            spec = concorrente.scrivi(self.project, risultato, "Autore Anonimo")
        self.assertEqual((spec.language, spec.author), ("en", "Claire Halvorsen"))
        self.assertTrue(self.project.brief_path.exists())

    def test_un_bloccante_di_originalita_ferma_la_scheda(self):
        self.scrivi_reparto([{"severity": "bloccante", "category": "titolo", "issue": "uguale"}])
        risultato = concorrente.importa(self.project)
        with self.assertRaises(SystemExit):
            concorrente.scrivi(self.project, risultato, "Autore")
        self.assertFalse(self.project.spec_path.exists())

    def test_i_subagent_sanno_dove_leggere_l_avvio(self):
        from kdpfactory.agents.base import get_agent
        from kdpfactory.agents.install import render_agent_markdown

        self.assertIn("avvio.json", render_agent_markdown(get_agent("posizionamento")))
        self.assertIn("cowork-concorrente-risposta.md",
                      render_agent_markdown(get_agent("scheda-concorrente")))
        self.assertIn("originalita.json", render_agent_markdown(get_agent("originalita")))


class TestCopertina(Base):
    def test_il_brief_chiede_di_distinguersi(self):
        spec = BookSpec(slug="libro", title="Bills in Order", author="Claire Halvorsen")
        senza = coverbrief.brief(spec, pages=192)
        self.assertNotIn("Stand out from the cover", senza)
        con = coverbrief.brief(spec, pages=192, concorrente="Navy background, a stock calculator.")
        self.assertIn("Stand out from the cover", con)
        self.assertIn("> Navy background, a stock calculator.", con)

    def test_la_descrizione_si_legge_senza_istruzioni(self):
        avvio.copertina_path(self.project).parent.mkdir(parents=True)
        avvio.copertina_path(self.project).write_text(
            avvio.COPERTINA_TEMPLATE + "Sfondo blu, una calcolatrice.\n", encoding="utf-8"
        )
        self.assertEqual(avvio.leggi_copertina(self.project), "Sfondo blu, una calcolatrice.")


if __name__ == "__main__":
    unittest.main()

"""Il giro automatico: corriere su Drive, decisioni con silenzio-assenso, bussola della produzione."""

import contextlib
import io
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from kdpfactory import (
    backup,
    corriere,
    coverbrief,
    cowork,
    decisioni,
    imagebrief,
    produzione,
    richiesteimmagini,
)
from kdpfactory import figure as figure_module
from kdpfactory.models import BookProject, BookSpec

CANALE = {
    "canale": "drive",
    "corriere": {"cartella": "NEXTUP — corriere Cowork", "cartella_id": "abc123"},
    "ruoli": {"concorrente": {}, "immagini": {}},
}


def scrivi(radice: Path, relativo: str, testo: str) -> Path:
    percorso = radice / relativo
    percorso.parent.mkdir(parents=True, exist_ok=True)
    percorso.write_text(testo, encoding="utf-8")
    return percorso


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.radice = Path(self._tmp.name)
        backup.configure(enabled=False)
        self.addCleanup(backup.configure, enabled=True, directory=None)
        self.richiesta = "books/libro/concorrente/cowork-concorrente.md"
        scrivi(self.radice, self.richiesta,
               cowork.intestazione("T", "cowork-concorrente-risposta.md", "concorrente", CANALE,
                                   "books/libro/concorrente"))
        scrivi(self.radice, "config/leggimi-cowork.md", "# LEGGIMI\n")

    def elenco(self):
        return cowork.richieste(self.radice)


class TestCorriere(Base):
    def test_i_nomi_su_drive_sono_i_percorsi(self):
        self.assertEqual(corriere.nome_drive(self.richiesta),
                         "books__libro__concorrente__cowork-concorrente.md")
        self.assertEqual(corriere.percorso_da_nome("books__libro__assets__copertina-1.png"),
                         "books/libro/assets/copertina-1.png")

    def test_l_intestazione_dice_il_nome_della_risposta_su_drive(self):
        testo = (self.radice / self.richiesta).read_text(encoding="utf-8")
        self.assertIn("`books__libro__concorrente__cowork-concorrente-risposta.md`", testo)
        self.assertIn("NEXTUP — corriere Cowork", testo)
        self.assertNotIn("ramo", testo)

    def test_il_piano_carica_una_volta_e_ricarica_se_cambia(self):
        piano = corriere.piano(self.radice, self.elenco())
        self.assertEqual({c["percorso"] for c in piano["carica"]},
                         {self.richiesta, "config/leggimi-cowork.md"})
        self.assertEqual(piano["attesi"], ["books__libro__concorrente__cowork-concorrente-risposta.md"])
        corriere.registra_caricato(self.radice, self.richiesta, "id-1")
        corriere.registra_caricato(self.radice, "config/leggimi-cowork.md", "id-2")
        self.assertEqual(corriere.piano(self.radice, self.elenco())["carica"], [])
        scrivi(self.radice, "config/leggimi-cowork.md", "# LEGGIMI versione nuova\n")
        carica = corriere.piano(self.radice, self.elenco())["carica"]
        self.assertEqual([(c["percorso"], c["vecchio_id"]) for c in carica],
                         [("config/leggimi-cowork.md", "id-2")])

    def test_cowork_scrive_solo_risposte_e_immagini(self):
        elenco = self.elenco()
        ammessa = corriere.destinazione_ammessa
        risposta = "books__libro__concorrente__cowork-concorrente-risposta.md"
        self.assertEqual(ammessa(self.radice, risposta, elenco),
                         "books/libro/concorrente/cowork-concorrente-risposta.md")
        self.assertEqual(ammessa(self.radice, "books__libro__assets__copertina-2.png", elenco),
                         "books/libro/assets/copertina-2.png")
        for nome in ("books__libro__book.json", "kdpfactory__cli.py", "books__libro__assets__..__x.png",
                     "books__altro__assets__copertina-1.png", "books__libro__assets__note.md"):
            self.assertEqual(ammessa(self.radice, nome, elenco), "", nome)

    def test_una_richiesta_applicata_si_toglie_da_drive(self):
        corriere.registra_caricato(self.radice, self.richiesta, "id-1")
        with (self.radice / self.richiesta).open("a", encoding="utf-8") as fh:
            fh.write("\nStato: applicata il 2026-10-05\n")
        self.assertEqual(corriere.piano(self.radice, self.elenco())["togli"],
                         [{"percorso": self.richiesta, "id": "id-1"}])

    def test_una_richiesta_ritirata_si_toglie_da_drive(self):
        corriere.registra_caricato(self.radice, self.richiesta, "id-1")
        corriere.registra_caricato(self.radice, "config/leggimi-cowork.md", "id-2")
        (self.radice / self.richiesta).unlink()
        self.assertEqual(corriere.piano(self.radice, self.elenco())["togli"],
                         [{"percorso": self.richiesta, "id": "id-1"}])

    def test_la_risposta_di_cowork_arriva_e_non_si_riscrive(self):
        from kdpfactory import cli

        scaricato = scrivi(self.radice, "tmp/risposta.md", "Esito: completa\n")
        nome = "books__libro__concorrente__cowork-concorrente-risposta.md"
        args = type("A", (), {"caricato": "", "tolto": "", "scarica": nome, "id": "id-9",
                              "file": str(scaricato)})()
        with contextlib.redirect_stdout(io.StringIO()):
            cli._cmd_corriere(args, self.radice, CANALE, self.elenco())
        risposta = self.radice / "books/libro/concorrente/cowork-concorrente-risposta.md"
        self.assertEqual(risposta.read_text(encoding="utf-8"), "Esito: completa\n")
        args.id = "id-10"
        with self.assertRaises(SystemExit):
            cli._cmd_corriere(args, self.radice, CANALE, self.elenco())


PNG = b"\x89PNG\r\n\x1a\n" + b"\0" * 32


class FintoGit:
    """Fa le veci di git: il ramo con i suoi file, senza rete."""

    def __init__(self, file: dict[str, bytes] | None):
        self.file = file          # None: il ramo non c'è
        self.blob = {f"b{i}": dati for i, dati in enumerate((file or {}).values())}

    def __call__(self, comando, capture_output=True):
        import subprocess

        azione = comando[3]
        if azione == "fetch":
            return subprocess.CompletedProcess(comando, 0 if self.file is not None else 128, b"", b"")
        if azione == "ls-tree":
            righe = "".join(f"100644 blob b{i}\t{p}\n" for i, p in enumerate(self.file))
            return subprocess.CompletedProcess(comando, 0, righe.encode(), b"")
        return subprocess.CompletedProcess(comando, 0, self.blob[comando[-1]], b"")


class TestRamoImmagini(Base):
    def setUp(self):
        super().setUp()
        _, testo = richiesteimmagini.scaricamento(
            "libro", "Titolo",
            [("copertina-1.png", "https://cdn.example/a.png"), ("copertina-2.png", "https://cdn.example/b.png")],
            CANALE,
        )
        scrivi(self.radice, "books/libro/manuale/cowork-immagini-scarica.md", testo)

    def test_dal_ramo_arrivano_solo_le_immagini_chieste(self):
        finto = FintoGit({
            "kdp-book-factory/books/libro/assets/copertina-1.png": PNG,
            "kdp-book-factory/books/libro/assets/copertina-2.png": b"<html>non un'immagine</html>",
            "kdp-book-factory/books/libro/assets/vecchia.png": PNG,      # non chiesta
            "kdp-book-factory/books/altro/assets/copertina-1.png": PNG,  # libro che non c'è
            "kdp-book-factory/kdpfactory/cli.py": b"print('no')",
            "README.md": b"#",
        })
        immagini, avvisi = corriere.preleva_dal_ramo(self.radice, self.elenco(), esegui=finto)
        self.assertEqual([i.percorso for i in immagini], ["books/libro/assets/copertina-1.png"])
        self.assertEqual(len(avvisi), 1)
        self.assertIn("copertina-2.png", avvisi[0])
        # una volta presa, la stessa immagine non torna a ogni giro
        corriere.registra_dal_ramo(self.radice, immagini[0].percorso, immagini[0].blob)
        immagini, _ = corriere.preleva_dal_ramo(self.radice, self.elenco(), esegui=finto)
        self.assertEqual(immagini, [])

    def test_dal_ramo_arriva_la_risposta_e_non_si_riscrive(self):
        risposta = "kdp-book-factory/books/libro/concorrente/cowork-concorrente-risposta.md"
        finto = FintoGit({
            risposta: b"Esito: completa\n",
            "kdp-book-factory/books/libro/concorrente/cowork-altro-risposta.md": b"Esito: completa\n",
            "kdp-book-factory/books/libro/book.json": b"{}",
        })
        presi, _ = corriere.preleva_dal_ramo(self.radice, self.elenco(), esegui=finto)
        self.assertEqual([p.percorso for p in presi],
                         ["books/libro/concorrente/cowork-concorrente-risposta.md"])
        # una risposta che c'è già nel repository non arriva una seconda volta
        scrivi(self.radice, "books/libro/concorrente/cowork-concorrente-risposta.md", "Esito: parziale\n")
        presi, _ = corriere.preleva_dal_ramo(self.radice, self.elenco(), esegui=finto)
        self.assertEqual(presi, [])

    def test_senza_ramo_si_dice_e_non_si_scrive_niente(self):
        immagini, avvisi = corriere.preleva_dal_ramo(self.radice, self.elenco(), esegui=FintoGit(None))
        self.assertEqual(immagini, [])
        self.assertIn("non c'è ancora", avvisi[0])

    def test_le_firme_delle_immagini(self):
        self.assertTrue(corriere.e_un_immagine(PNG))
        self.assertTrue(corriere.e_un_immagine(b"\xff\xd8\xff\xe0" + b"\0" * 8))
        self.assertTrue(corriere.e_un_immagine(b"RIFF\0\0\0\0WEBPVP8 "))
        self.assertFalse(corriere.e_un_immagine(b"GIF89a"))
        self.assertFalse(corriere.e_un_immagine(b"RIFF\0\0\0\0WAVE"))


CANALE_GITHUB = {
    "canale": "github",
    "repository": "o/r",
    "ramo": "fabbrica",
    "ramo_consegna": corriere.RAMO_IMMAGINI,
    "ruoli": {
        "concorrente": {"trigger": "trig_c", "cloud": False},
        "fonti": {"trigger": "trig_f", "cloud": True},
    },
}


class TestCanaleGithub(Base):
    def setUp(self):
        super().setUp()
        self.fonti = "books/libro/manuale/cowork-fonti.md"
        self.kdp = "books/libro/manuale/cowork-fonti-kdp.md"
        scrivi(self.radice, self.fonti,
               cowork.intestazione("F", "cowork-fonti-risposta.md", "fonti", CANALE_GITHUB,
                                   "books/libro/manuale"))
        scrivi(self.radice, self.kdp,
               cowork.intestazione("K", "cowork-fonti-kdp-risposta.md", "fonti", CANALE_GITHUB,
                                   "books/libro/manuale", serve="l'accesso a KDP"))

    def test_l_intestazione_manda_la_risposta_su_drive(self):
        testo = (self.radice / self.fonti).read_text(encoding="utf-8")
        # la risposta va su Drive col nome che la fabbrica sa riportare su GitHub
        self.assertIn("`books__libro__manuale__cowork-fonti-risposta.md`", testo)
        self.assertIn("in `kdp-book-factory/books/libro/manuale/cowork-fonti-risposta.md`", testo)
        self.assertNotIn("Commit", testo)
        self.assertEqual(corriere.destinazione_ammessa(
            self.radice, "books__libro__manuale__cowork-fonti-risposta.md", self.elenco()),
            "books/libro/manuale/cowork-fonti-risposta.md")

    def test_su_drive_resta_solo_il_leggimi(self):
        scrivi(self.radice, "config/progetto-cowork.md", "# progetto\n")
        corriere.registra_caricato(self.radice, self.richiesta, "id-1")
        corriere.registra_caricato(self.radice, "config/progetto-cowork.md", "id-3")
        piano = corriere.piano(self.radice, self.elenco(), CANALE_GITHUB)
        self.assertEqual([c["percorso"] for c in piano["carica"]], ["config/leggimi-cowork.md"])
        # le copie caricate quando il canale era Drive — richieste ancora aperte, progetto — si tolgono
        self.assertEqual(piano["togli"], [{"percorso": self.richiesta, "id": "id-1"},
                                          {"percorso": "config/progetto-cowork.md", "id": "id-3"}])

    def test_si_lancia_solo_quello_che_si_fa_nel_cloud_e_una_volta_sola(self):
        avvia = corriere.da_avviare(self.radice, self.elenco(), CANALE_GITHUB)
        # concorrente lavora col browser del portatile; la richiesta con Serve aspetta l'autore
        self.assertEqual(avvia, [{"ruolo": "fonti", "trigger": "trig_f", "richieste": [self.fonti]}])
        self.assertEqual(corriere.registra_avviato(self.radice, "fonti", self.elenco(), CANALE_GITHUB),
                         [self.fonti])
        self.assertEqual(corriere.da_avviare(self.radice, self.elenco(), CANALE_GITHUB), [])
        # una richiesta corretta è una richiesta nuova: si lancia di nuovo
        with (self.radice / self.fonti).open("a", encoding="utf-8") as fh:
            fh.write("\n3. Un punto in più.\n")
        self.assertEqual(len(corriere.da_avviare(self.radice, self.elenco(), CANALE_GITHUB)), 1)

    def test_l_indice_dice_dove_leggere_e_come_si_chiama_la_risposta(self):
        testo = corriere.indice(self.elenco(), CANALE_GITHUB)
        self.assertIn("## Ruolo fonti", testo)
        self.assertIn("- `kdp-book-factory/books/libro/manuale/cowork-fonti.md`", testo)
        self.assertIn("si fa: solo col browser del portatile — serve l'accesso a KDP", testo)
        self.assertIn("leggi: https://raw.githubusercontent.com/o/r/fabbrica/kdp-book-factory/books/libro/"
                      "manuale/cowork-fonti.md", testo)
        self.assertIn("risposta su Drive: `books__libro__manuale__cowork-fonti-risposta.md`", testo)
        # l'indice si chiama come una richiesta, ma non lo è
        scrivi(self.radice, "config/cowork-aperte.md", testo)
        self.assertNotIn("config/cowork-aperte.md", [r.percorso for r in self.elenco()])
        # una richiesta applicata esce dall'indice
        with (self.radice / self.fonti).open("a", encoding="utf-8") as fh:
            fh.write("\nStato: applicata il 2026-10-06\n")
        self.assertNotIn("cowork-fonti.md`", corriere.indice(self.elenco(), CANALE_GITHUB))


class TestDecisioni(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.project = BookProject(Path(self._tmp.name) / "libro")
        self.t0 = datetime(2026, 10, 5, 8, 0, tzinfo=timezone.utc)

    def test_il_silenzio_vale_assenso_dopo_la_scadenza(self):
        decisioni.proponi(self.project, "titolo", "Bills in Order", ["Paid on Time"], adesso=self.t0)
        self.assertEqual(decisioni.chiudi_scadute(self.project, self.t0 + timedelta(hours=23)), [])
        chiuse = decisioni.chiudi_scadute(self.project, self.t0 + timedelta(hours=24))
        self.assertEqual([v["stato"] for v in chiuse], [decisioni.SILENZIO])
        self.assertEqual(decisioni.valore(self.project, "titolo"), "Bills in Order")
        self.assertEqual(len(decisioni.da_applicare(self.project)), 1)
        decisioni.segna_applicata(self.project, "titolo")
        self.assertEqual(decisioni.da_applicare(self.project), [])

    def test_la_risposta_dell_autore_vince(self):
        decisioni.proponi(self.project, "prezzo", "12.99", adesso=self.t0)
        decisioni.scegli(self.project, "prezzo", "14.99", adesso=self.t0 + timedelta(hours=2))
        self.assertEqual(decisioni.chiudi_scadute(self.project, self.t0 + timedelta(days=3)), [])
        self.assertEqual(decisioni.valore(self.project, "prezzo"), "14.99")

    def test_la_pubblicazione_non_passa_dal_silenzio(self):
        with self.assertRaises(ValueError):
            decisioni.proponi(self.project, "pubblicazione", "sì")


class TestProduzione(Base):
    def test_il_libro_fermo_aspetta_solo_quello_che_gli_serve(self):
        from kdpfactory import avvio

        project = BookProject(self.radice / "books" / "libro")
        risposte = avvio.Avvio()
        avvio.registra(risposte, concorrente="B0CSSJMQP1")
        risposte.risposte = [d.chiave for d in avvio.DOMANDE]
        avvio.salva(project, risposte)
        stato = produzione.stato_libro(project, self.elenco())
        self.assertEqual(stato.fase, "0")
        self.assertTrue(stato.fermo)
        self.assertIn("cowork-concorrente.md", stato.blocca[0])

    def test_un_seguito_con_serve_aspetta_l_autore_non_cowork(self):
        from kdpfactory import avvio

        project = BookProject(self.radice / "books" / "libro")
        risposte = avvio.Avvio()
        avvio.registra(risposte, concorrente="B0CSSJMQP1")
        risposte.risposte = [d.chiave for d in avvio.DOMANDE]
        avvio.salva(project, risposte)
        scrivi(self.radice, "books/libro/concorrente/cowork-concorrente-risposta.md",
               "Esito: parziale — punto 5: accesso\n\n" + "scheda prezzo pagine recensioni " * 15)
        with (self.radice / self.richiesta).open("a", encoding="utf-8") as fh:
            fh.write("\nStato: applicata il 2026-10-05\n")
        seguito = cowork.intestazione("T", "cowork-concorrente-2-risposta.md", "concorrente", CANALE,
                                      "books/libro/concorrente", serve="l'accesso ad Amazon")
        self.assertIn("Serve: l'accesso ad Amazon", seguito)
        self.assertIn("non\nscrivere nessuna risposta", seguito)
        scrivi(self.radice, "books/libro/concorrente/cowork-concorrente-2.md", seguito)
        elenco = self.elenco()
        self.assertEqual([r.serve for r in elenco if r.stato == cowork.APERTA], ["l'accesso ad Amazon"])
        stato = produzione.stato_libro(project, elenco)
        self.assertEqual(stato.blocca, [], "la pagina c'è già: il seguito non ferma il libro")
        self.assertTrue(any(v.startswith("autore: aprire l'accesso ad Amazon") for v in stato.in_corso))

    def test_il_seguito_conta_come_la_richiesta(self):
        base = produzione._nome_base
        self.assertEqual(base("books/x/manuale/cowork-copertina-2.md"), "cowork-copertina.md")
        self.assertEqual(base("config/cowork-kdp-12.md"), "cowork-kdp.md")
        self.assertEqual(base("books/x/cowork-parole-chiave.md"), "cowork-parole-chiave.md")

    def test_le_varianti_pagate_si_scaricano_non_si_rigenerano(self):
        import io as _io
        from types import SimpleNamespace

        from kdpfactory import cli

        project = BookProject(self.radice / "books" / "libro")
        scrivi(self.radice, "books/libro/build/copertina-higgsfield.json", json.dumps([
            {"variante": 1, "url": "https://cdn.example/a.png"},
            {"variante": 2, "url": "https://cdn.example/b.png"},
        ]))
        self.assertEqual([v["variante"] for v in produzione.generate_senza_file(project)], [1, 2])

        from PIL import Image
        buffer = _io.BytesIO()
        Image.new("RGB", (4, 6)).save(buffer, "PNG")
        png = buffer.getvalue()

        def apri(url, timeout=0):
            if url.endswith("b.png"):
                raise OSError("connect_rejected")
            return contextlib.closing(_io.BytesIO(png))

        args = SimpleNamespace(no_backup=True, slug="libro")
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as errori:
            esito = cli._scarica_generate(project, args, apri=apri)
        self.assertEqual(esito, 1)
        self.assertIn("cdn.example", errori.getvalue())
        self.assertTrue((project.assets_dir / "copertina-1.png").exists())
        # resta da scaricare solo quella bloccata
        self.assertEqual([v["variante"] for v in produzione.generate_senza_file(project)], [2])

    def test_solo_i_libri_attivi(self):
        (self.radice / "books" / "altro" / "concorrente").mkdir(parents=True)
        stati = produzione.tutti(self.radice / "books", self.elenco(), attivi=["altro"])
        self.assertEqual([s.slug for s in stati], ["altro"])


class TestImmagini(unittest.TestCase):
    def spec(self, **campi):
        base = dict(
            slug="bills", title="Bills in Order", subtitle="A Household Guide",
            topic="household bills", categories=["Books > Personal Finance > Budgeting"],
            audience="The adult who handles the bills. Second sentence, not needed.",
            promise="A way of handling bills. More detail that a prompt does not need.",
        )
        base.update(campi)
        return BookSpec(**base)

    def test_la_richiesta_di_copertina_porta_il_prompt_e_i_nomi(self):
        nome, testo = richiesteimmagini.copertina(
            "libro", "Titolo", "Front cover illustration. No text.", (1838, 2775), CANALE
        )
        self.assertEqual(nome, "cowork-copertina.md")
        self.assertIn("Ruolo: immagini", testo)
        self.assertIn("---\nFront cover illustration. No text.\n---", testo)
        self.assertIn(richiesteimmagini.PROSSIMA_VARIANTE, testo)
        for i in (1, 2, 3):
            self.assertIn(f"`kdp-book-factory/books/libro/assets/copertina-{i}.png`", testo)
        self.assertIn("ramo `cowork-immagini`", testo)
        self.assertIn("Serve: l'accesso a ChatGPT e a GitHub", testo)
        self.assertIn("1838 x 2775", testo)
        self.assertIn("`books__libro__manuale__cowork-copertina-risposta.md`", testo)

    def test_le_immagini_gia_generate_si_chiedono_da_scaricare(self):
        nome, testo = richiesteimmagini.scaricamento(
            "libro", "Titolo", [("copertina-1.png", "https://cdn.example/a.png")], CANALE,
        )
        self.assertEqual(nome, "cowork-immagini-scarica.md")
        self.assertIn("Ruolo: immagini", testo)
        # le immagini viaggiano sul ramo di GitHub: serve il suo accesso, non Drive
        self.assertIn("Serve: l'accesso a GitHub", testo)
        self.assertIn("`kdp-book-factory/books/libro/assets/copertina-1.png` ← https://cdn.example/a.png",
                      testo)
        self.assertIn("ramo `cowork-immagini`", testo)
        self.assertIn("`books__libro__manuale__cowork-immagini-scarica-risposta.md`", testo)
        nome, testo = richiesteimmagini.scaricamento(
            "libro", "Titolo", [("copertina-1.png", "https://cdn.example/a.png")], CANALE, seguito=2,
        )
        self.assertEqual(nome, "cowork-immagini-scarica-2.md")
        self.assertIn("`books__libro__manuale__cowork-immagini-scarica-2-risposta.md`", testo)

    def test_il_prompt_da_incollare_ha_solo_quello_che_decide_l_immagine(self):
        prompt = coverbrief.prompt_da_incollare(self.spec(), pages=192)
        self.assertTrue(prompt.startswith("Front cover illustration for a paperback book: "
                                          "«Bills in Order — A Household Guide»"))
        self.assertIn("variant 1 of 3", prompt)
        self.assertIn("paper envelope", prompt)         # la rappresentazione della categoria
        self.assertIn("Direction: Keep it simple: one clear focal subject", prompt)
        self.assertIn("portrait, 2:3", prompt)
        self.assertIn("Absolutely no text", prompt)
        self.assertIn("1838 x 2775 px", prompt)
        self.assertIn("The adult who handles the bills.", prompt)
        self.assertNotIn("Second sentence", prompt)     # dei campi lunghi, la prima frase
        # niente specifiche di stampa: fanno disegnare un wrap invece di una prima
        for parola in ("spine", "barcode", "bleed", "wrap", "CMYK"):
            self.assertNotIn(parola, prompt)
        self.assertNotIn("#", prompt.splitlines()[0])  # testo semplice, nessun titolo markdown

    def test_le_scelte_fra_i_bozzetti_entrano_nei_prompt(self):
        with tempfile.TemporaryDirectory() as tmp:
            percorso = Path(tmp) / "direzione.json"
            coverbrief.registra_direzione(["luce", "serigrafia"], ["linea"], "più semplice",
                                          percorso=percorso)
            direzione = coverbrief.direzione_appresa(percorso)
            self.assertEqual(coverbrief.trattamenti_preferiti(direzione), ["luce", "serigrafia"])
            self.assertNotIn("linea", coverbrief.trattamenti_da_provare(direzione))
            # cambiare idea: una scartata torna fra le preferite, e viceversa
            coverbrief.registra_direzione(["linea"], ["luce"], percorso=percorso)
            direzione = coverbrief.direzione_appresa(percorso)
            self.assertEqual(coverbrief.trattamenti_preferiti(direzione), ["linea", "serigrafia"])
            self.assertEqual([s["trattamento"] for s in direzione["scartati"]], ["luce"])
            with self.assertRaises(ValueError):
                coverbrief.registra_direzione(["acquerello"], [], percorso=percorso)

    def test_il_bozzetto_cambia_solo_il_trattamento(self):
        luce = coverbrief.prompt_bozza(self.spec(), "luce", pages=192)
        carta = coverbrief.prompt_bozza(self.spec(), "carta", pages=192)
        self.assertIn("Subject: a single sealed paper envelope.", luce)
        self.assertIn(coverbrief.DIREZIONE_VISIVA, luce)
        self.assertIn("No text, letters or numbers anywhere", luce)
        diverse = [a for a, b in zip(luce.splitlines(), carta.splitlines(), strict=True) if a != b]
        self.assertEqual(len(diverse), 1)
        self.assertTrue(diverse[0].startswith("Treatment:"))

    def test_i_colori_si_dicono_a_parole(self):
        self.assertEqual(coverbrief.nome_colore("#0E1320"), "deep navy (#0E1320)")
        self.assertEqual(coverbrief.nome_colore("#F5B301"), "golden amber (#F5B301)")
        self.assertEqual(coverbrief.nome_colore("#f3e9d8"), "cream (#F3E9D8)")
        prompt = coverbrief.prompt_da_incollare(self.spec(), pages=192)
        self.assertRegex(prompt, r"Colour: a [a-z ]+ \(#[0-9A-F]{6}\) background")

    def test_il_prompt_da_incollare_si_distingue_dal_concorrente(self):
        prompt = coverbrief.prompt_da_incollare(
            self.spec(), pages=192, concorrente="Navy background,\na stock calculator."
        )
        self.assertIn("Navy background, a stock calculator.", prompt)
        self.assertIn("different dominant colour", prompt)

    def test_il_file_da_incollare_separa_le_istruzioni_dal_testo(self):
        testo = richiesteimmagini.testo_copertina("libro", "PROMPT")
        blocchi = [riga for riga in testo.splitlines() if riga.startswith("===")]
        self.assertEqual(len(blocchi), 3)
        self.assertIn("\n\nPROMPT\n\n", testo)
        self.assertIn(richiesteimmagini.PROSSIMA_VARIANTE, testo)
        self.assertIn("kdp-book-factory/books/libro/assets/copertina-3.png", testo)
        self.assertIn("«libro — copertina»", testo)

    def test_il_progetto_chatgpt_tiene_le_regole_fisse(self):
        testo = richiesteimmagini.progetto_chatgpt(CANALE)
        self.assertIn(richiesteimmagini.ISTRUZIONI_CHATGPT, testo)
        self.assertIn("NEXTUP — corriere Cowork", testo)
        self.assertIn(f"build/{richiesteimmagini.CHATGPT_COPERTINA}", testo)
        self.assertNotIn("allegat", testo)
        for regola in ("No text of any kind", "grayscale only", "portrait 2:3", "real person"):
            self.assertIn(regola, richiesteimmagini.ISTRUZIONI_CHATGPT)

    def test_ogni_figura_ha_il_suo_prompt_in_grigio_e_il_suo_nome(self):
        figura = figure_module.Figura(
            descrizione="A blank bill with its due date area circled.",
            percorso="immagini/03-bolletta.jpg", didascalia="Where the due date sits.",
            capitolo=3,
        )
        prompt = imagebrief.prompt_incollabile(self.spec(), figura)
        self.assertTrue(prompt.startswith("A blank bill"))
        self.assertIn("Greyscale illustration", prompt)
        self.assertIn("«Where the due date sits.»", prompt)
        testo = richiesteimmagini.testo_figure("libro", [(figura.percorso, prompt)])
        self.assertIn("kdp-book-factory/books/libro/assets/immagini/03-bolletta.jpg", testo)
        self.assertIn(prompt, testo)
        _, richiesta = richiesteimmagini.figure("libro", "Titolo", [(figura.percorso, prompt)], CANALE)
        self.assertIn("`kdp-book-factory/books/libro/assets/immagini/03-bolletta.jpg`", richiesta)
        self.assertIn(f"---\n{prompt}\n---", richiesta)
        self.assertIn("scala di grigi", richiesta)


class TestConfigurazioneVera(unittest.TestCase):
    def test_il_canale_vero_e_il_corriere_con_cinque_ruoli(self):
        radice = Path(__file__).resolve().parent.parent
        canale = json.loads((radice / "config" / "cowork.json").read_text(encoding="utf-8"))
        self.assertEqual(canale["canale"], "github")
        self.assertEqual(canale["ramo_consegna"], corriere.RAMO_IMMAGINI)
        self.assertTrue(canale["corriere"]["cartella_id"])
        self.assertEqual(set(canale["ruoli"]),
                         {"concorrente", "parole-chiave", "fonti", "regole-kdp", "immagini"})
        minuti = [r["minuto"] for r in canale["ruoli"].values()]
        self.assertEqual(len(minuti), len(set(minuti)), "due ruoli alla stessa ora")


if __name__ == "__main__":
    unittest.main()

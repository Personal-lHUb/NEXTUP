"""Il piano delle figure e le immagini pubbliche: nessuna chiamata di rete.

Gli archivi si simulano con risposte JSON finte, i file con immagini sintetiche.
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from kdpfactory import figure as figure_module
from kdpfactory import imagebrief, pubbliche
from kdpfactory.models import BookSpec


class Risposta(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def apri_finto(risposte: dict[str, bytes]):
    """Un `urlopen` che risponde secondo l'host chiesto, e ricorda le richieste."""
    chieste = []

    def apri(richiesta, timeout=0):
        url = richiesta.full_url if hasattr(richiesta, "full_url") else richiesta
        chieste.append(url)
        for chiave, corpo in risposte.items():
            if chiave in url:
                return Risposta(corpo)
        raise OSError(f"rete chiusa: {url}")

    apri.chieste = chieste
    return apri


def png(larghezza=2000, altezza=1500) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (larghezza, altezza), (120, 120, 120)).save(buffer, "PNG")
    return buffer.getvalue()


OPENVERSE = json.dumps({"results": [
    {"title": "Old map of Boston", "creator": "Unknown", "license": "pdm", "license_version": "1.0",
     "license_url": "https://creativecommons.org/publicdomain/mark/1.0/",
     "foreign_landing_url": "https://example.org/map", "url": "https://files.example/map.png",
     "width": 3000, "height": 2000, "source": "met"},
    {"title": "Photo with a licence we do not take", "creator": "Someone", "license": "by",
     "url": "https://files.example/by.png"},
]}).encode()

COMMONS = json.dumps({"query": {"pages": {
    "1": {"index": 1, "title": "File:Ledger.jpg", "imageinfo": [{
        "url": "https://upload.example/ledger.jpg", "descriptionurl": "https://commons.example/Ledger",
        "width": 2400, "height": 1800,
        "extmetadata": {"License": {"value": "pd"}, "LicenseShortName": {"value": "Public domain"},
                        "Artist": {"value": "<a href='x'>A. Clerk</a>"}}}]},
    "2": {"index": 2, "title": "File:Logo.png", "imageinfo": [{
        "url": "https://upload.example/logo.png", "width": 500, "height": 500,
        "extmetadata": {"License": {"value": "pd"}, "Restrictions": {"value": "trademarked"}}}]},
    "3": {"index": 3, "title": "File:Shared.jpg", "imageinfo": [{
        "url": "https://upload.example/shared.jpg", "width": 900, "height": 600,
        "extmetadata": {"License": {"value": "cc-by-sa-4.0"}}}]},
}}}).encode()


class TestPiano(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "libro"
        (self.root / "assets" / "immagini").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def figura(self, nome="03-mappa.jpg", capitolo=3, esiste=False) -> figure_module.Figura:
        if esiste:
            Image.new("L", (2000, 1500), 128).save(self.root / "assets" / "immagini" / nome)
        return figure_module.risolvi(
            type("B", (), {"descrizione": "a map", "percorso": f"immagini/{nome}", "didascalia": ""})(),
            self.root / "assets", capitolo,
        )

    def test_senza_piano_si_avvisa_soltanto(self):
        problemi = figure_module.problemi_piano(None, [self.figura()])
        self.assertEqual([g for g, _ in problemi], ["avviso"])

    def test_il_piano_dice_niente_figure_e_il_testo_ne_ha(self):
        piano = {"servono": False, "perche": "si legge", "figure": []}
        self.assertEqual(figure_module.problemi_piano(piano, [self.figura()])[0][0], "errore")

    def test_una_pubblica_senza_licenza_ammessa_non_si_stampa(self):
        piano = {"servono": True, "figure": [
            {"percorso": "immagini/03-mappa.jpg", "capitolo": 3, "fonte": "pubblica", "cerca": "map",
             "provenienza": {"licenza": "CC BY 4.0"}}]}
        problemi = figure_module.problemi_piano(piano, [self.figura(esiste=True)])
        self.assertTrue(any(g == "errore" and "licenza ammessa" in p for g, p in problemi))
        piano["figure"][0]["provenienza"]["licenza"] = "Public Domain Mark 1.0"
        self.assertEqual(figure_module.problemi_piano(piano, [self.figura(esiste=True)]), [])

    def test_una_generata_che_non_risulta_generata(self):
        piano = {"servono": True, "figure": [
            {"percorso": "immagini/03-mappa.jpg", "capitolo": 3, "fonte": "generata"}]}
        figura = self.figura(esiste=True)
        self.assertEqual(figure_module.problemi_piano(piano, [figura])[0][0], "avviso")
        self.assertEqual(figure_module.problemi_piano(piano, [figura], {"03-mappa.jpg"}), [])

    def test_il_ghostwriter_riceve_le_figure_del_suo_capitolo(self):
        piano = {"servono": True, "figure": [
            {"percorso": "immagini/03-mappa.jpg", "capitolo": 3, "mostra": "the harbour in 1890"}]}
        testo = figure_module.istruzioni_capitolo(piano, 3)
        self.assertIn("![the harbour in 1890](immagini/03-mappa.jpg)", testo)
        self.assertEqual(figure_module.istruzioni_capitolo(piano, 4), "")
        self.assertEqual(figure_module.istruzioni_capitolo({**piano, "servono": False}, 3), "")

    def test_il_prompt_porta_il_capitolo_e_il_mondo_del_libro(self):
        spec = BookSpec(slug="x", title="The Harbour", topic="a fishing town in 1890")
        prompt = imagebrief.prompt_incollabile(
            spec, self.figura(), mondo="Grey Atlantic port, wooden boats, oilskin coats.",
            titoli={3: "The Night of the Storm"})
        self.assertIn("chapter 3, «The Night of the Storm»", prompt)
        self.assertIn("a fishing town in 1890", prompt)
        self.assertIn("Grey Atlantic port", prompt)


class TestPubbliche(unittest.TestCase):
    def test_le_licenze(self):
        self.assertEqual(pubbliche.licenza_canonica("cc0"), "CC0 1.0")
        self.assertEqual(pubbliche.licenza_canonica("pdm"), "Public Domain Mark 1.0")
        self.assertEqual(pubbliche.licenza_canonica("Public domain"), "Public domain")
        for altra in ("by", "cc-by-sa-4.0", "by-nc", ""):
            self.assertEqual(pubbliche.licenza_canonica(altra), "")
        self.assertTrue(figure_module.licenza_ammessa("CC0 1.0"))
        self.assertFalse(figure_module.licenza_ammessa("CC BY 4.0"))

    def test_la_ricerca_tiene_solo_pubblico_dominio_e_cc0(self):
        apri = apri_finto({"api.openverse.org": OPENVERSE, "commons.wikimedia.org": COMMONS})
        candidati, errori = pubbliche.cerca("old ledger", apri)
        self.assertEqual(errori, [])
        self.assertEqual([c.titolo for c in candidati], ["Old map of Boston", "File:Ledger.jpg"])
        self.assertEqual(candidati[1].autore, "A. Clerk")
        self.assertIn("license=cc0%2Cpdm", apri.chieste[0])

    def test_con_la_rete_chiusa_lo_dice(self):
        candidati, errori = pubbliche.cerca("old ledger", apri_finto({}))
        self.assertEqual(candidati, [])
        self.assertEqual(len(errori), 2)

    def test_prendi_scrive_la_provenienza_e_rifiuta_le_altre_licenze(self):
        with tempfile.TemporaryDirectory() as cartella:
            destinazione = Path(cartella) / "immagini" / "03-mappa.jpg"
            candidato = {"archivio": "Openverse (met)", "titolo": "Old map", "autore": "Unknown",
                         "licenza": "Public Domain Mark 1.0", "file_url": "https://files.example/map.png",
                         "pagina": "https://example.org/map"}
            provenienza = pubbliche.prendi(candidato, destinazione, apri_finto({"files.example": png()}))
            self.assertTrue(destinazione.exists())
            self.assertEqual(provenienza["pixel"], [2000, 1500])
            self.assertEqual(provenienza["licenza"], "Public Domain Mark 1.0")
            with self.assertRaises(ValueError):
                pubbliche.prendi({**candidato, "licenza": "CC BY 4.0"}, destinazione,
                                 apri_finto({"files.example": png()}))
            with self.assertRaises(ValueError):
                pubbliche.prendi(candidato, destinazione, apri_finto({"files.example": b"<html>"}))


if __name__ == "__main__":
    unittest.main()


class TestComandoImmagini(unittest.TestCase):
    """`immagini --cerca` e `--prendi` dalla CLI, con gli archivi finti."""

    def setUp(self):
        from kdpfactory import backup

        backup.configure(enabled=False)
        self.tmp = tempfile.TemporaryDirectory()
        from kdpfactory.models import BookProject

        self.project = BookProject(Path(self.tmp.name) / "libro")
        (self.project.root / "assets").mkdir(parents=True)
        self.spec = BookSpec(slug="libro", title="The Harbour", topic="a fishing town")
        self.piano = {"servono": True, "perche": "", "mondo": "", "figure": [
            {"percorso": "immagini/03-mappa.jpg", "capitolo": 3, "mostra": "the old harbour map",
             "fonte": "pubblica", "cerca": "old harbour map"}]}
        figure_module.piano_path(self.project.root).write_text(json.dumps(self.piano), encoding="utf-8")

    def tearDown(self):
        from kdpfactory import backup

        self.tmp.cleanup()
        backup.configure(enabled=True)

    def test_cerca_e_prendi(self):
        from types import SimpleNamespace

        from kdpfactory import cli

        apri = apri_finto({"api.openverse.org": OPENVERSE, "commons.wikimedia.org": COMMONS,
                           "files.example": png(), "upload.example": png()})
        piano = figure_module.leggi_piano(self.project.root)
        self.assertEqual(cli._cerca_pubbliche(self.project, None, piano, apri=apri), 0)
        candidati = json.loads((self.project.build_dir / "immagini-pubbliche.json").read_text())
        self.assertEqual(len(candidati["immagini/03-mappa.jpg"]), 2)

        args = SimpleNamespace(prendi="immagini/03-mappa.jpg", candidato=2)
        self.assertEqual(cli._prendi_pubblica(self.project, args, self.spec, piano, apri=apri), 0)
        voce = figure_module.leggi_piano(self.project.root)["figure"][0]
        self.assertEqual(voce["provenienza"]["archivio"], "Wikimedia Commons")
        self.assertEqual(voce["provenienza"]["licenza"], "Public domain")
        self.assertTrue((self.project.assets_dir / "immagini" / "03-mappa.jpg").exists())

    def test_con_la_rete_chiusa_dice_che_domini_aprire(self):
        import contextlib

        from kdpfactory import cli

        errori = io.StringIO()
        with contextlib.redirect_stderr(errori):
            esito = cli._cerca_pubbliche(self.project, None, self.piano, apri=apri_finto({}))
        self.assertEqual(esito, 1)
        self.assertIn("api.openverse.org", errori.getvalue())

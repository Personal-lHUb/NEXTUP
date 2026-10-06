"""Higgsfield: il CLI si chiama con il prompt del sistema e la resa più alta.

Nessun test chiama il servizio vero: il CLI è sostituito da un finto che
risponde come lui, e il download da una funzione che scrive un'immagine.
"""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from kdpfactory import coverbrief, higgsfield
from kdpfactory.models import BookSpec

SCHEMA = {
    "params": [
        {"name": "prompt", "type": "string"},
        {"name": "aspect_ratio", "enum": ["1:1", "2:3", "3:2", "16:9"]},
        {"name": "resolution", "enum": ["1k", "2k", "4k"]},
        {"name": "quality", "enum": ["low", "medium", "high"]},
    ]
}


def finto(risposte: dict):
    """Un CLI finto: risponde secondo il primo argomento dopo `higgsfield`, e ricorda le chiamate."""
    chiamate = []

    def esegui(comando, **_):
        chiamate.append(comando)
        chiave = " ".join(comando[1:3])
        codice, uscita, errore = risposte.get(chiave, (0, "{}", ""))
        return subprocess.CompletedProcess(comando, codice, uscita, errore)

    esegui.chiamate = chiamate
    return esegui


def scrivi_immagine(larghezza: int, altezza: int):
    def scarica(_url, destinazione: Path):
        Image.new("RGB", (larghezza, altezza), (20, 30, 50)).save(destinazione, "PNG")

    return scarica


class TestPronto(unittest.TestCase):
    def test_senza_cli(self):
        self.assertIn("non è installato", higgsfield.pronto(finto({}), cerca=lambda _: None))

    def test_senza_accesso(self):
        esegui = finto({"auth token": (1, "", "Not authenticated.")})
        self.assertIn("auth login", higgsfield.pronto(esegui, cerca=lambda _: "/bin/hf"))

    def test_senza_area_di_lavoro(self):
        esegui = finto({"model get": (1, "", "Error: No workspace selected.")})
        self.assertIn("workspace set", higgsfield.pronto(esegui, cerca=lambda _: "/bin/hf"))

    def test_pronto(self):
        esegui = finto({"model get": (0, json.dumps(SCHEMA), "")})
        self.assertIsNone(higgsfield.pronto(esegui, cerca=lambda _: "/bin/hf"))


class TestParametri(unittest.TestCase):
    def test_la_resa_piu_alta_che_il_modello_dichiara(self):
        flag = higgsfield.parametri(SCHEMA, "2:3")
        self.assertEqual(flag, ["--aspect_ratio", "2:3", "--resolution", "4k", "--quality", "high"])

    def test_la_proporzione_piu_vicina_se_manca(self):
        schema = {"params": [{"name": "aspect_ratio", "enum": ["1:1", "3:4", "9:16"]}]}
        self.assertEqual(higgsfield.parametri(schema, "2:3"), ["--aspect_ratio", "3:4"])

    def test_uno_schema_muto_passa_solo_la_proporzione(self):
        self.assertEqual(higgsfield.parametri({}, "2:3"), ["--aspect_ratio", "2:3"])


class TestGenera(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cartella = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_genera_scarica_e_misura(self):
        risposta = [{"id": "job-1", "status": "completed",
                     "results": {"raw": {"url": "https://cdn.example/img.png"}}}]
        esegui = finto({"generate create": (0, json.dumps(risposta), "")})
        destinazione = self.cartella / "assets" / "copertina-1.png"
        generata = higgsfield.genera("A prompt.", destinazione, proporzione="2:3",
                                     eseguitore=esegui, scarica=scrivi_immagine(2048, 3072),
                                     schema_modello=SCHEMA)
        self.assertEqual((generata.larghezza, generata.altezza), (2048, 3072))
        self.assertEqual((generata.url, generata.job), ("https://cdn.example/img.png", "job-1"))
        self.assertTrue(generata.basta((1838, 2775)))
        comando = esegui.chiamate[0]
        self.assertEqual(comando[:4], ["higgsfield", "generate", "create", higgsfield.MODELLO_IMMAGINI])
        for atteso in ("--prompt", "A prompt.", "--wait", "--json", "4k"):
            self.assertIn(atteso, comando)
        self.assertEqual(list(destinazione.parent.iterdir()), [destinazione], "niente file di passaggio")

    def test_il_formato_segue_il_nome(self):
        esegui = finto({"generate create": (0, json.dumps({"url": "https://cdn.example/a.webp"}), "")})
        destinazione = self.cartella / "immagini" / "03-mappa.jpg"
        higgsfield.genera("Figure.", destinazione, proporzione="4:3", eseguitore=esegui,
                          scarica=scrivi_immagine(1600, 1200), schema_modello={})
        with Image.open(destinazione) as immagine:
            self.assertEqual(immagine.format, "JPEG")

    def test_un_lavoro_rifiutato_si_dice(self):
        esegui = finto({"generate create": (1, "", "Job ended with status \"failed\"")})
        with self.assertRaises(RuntimeError) as errore:
            higgsfield.genera("P.", self.cartella / "x.png", proporzione="2:3", eseguitore=esegui,
                              scarica=scrivi_immagine(10, 10), schema_modello={})
        self.assertIn("failed", str(errore.exception))

    def test_il_registro_si_allunga(self):
        g = higgsfield.Generata(file="a.png", modello="m", larghezza=1, altezza=2)
        higgsfield.registra(self.cartella, [g])
        percorso = higgsfield.registra(self.cartella, [g])
        self.assertEqual(len(json.loads(percorso.read_text(encoding="utf-8"))), 2)


class TestConfigurazione(unittest.TestCase):
    def test_senza_file_le_immagini_restano_a_cowork(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(higgsfield.attivo(Path(tmp)))
            (Path(tmp) / "config").mkdir()
            (Path(tmp) / "config" / "immagini.json").write_text('{"generatore": "higgsfield"}')
            self.assertTrue(higgsfield.attivo(Path(tmp)))

    def test_la_fabbrica_usa_higgsfield(self):
        radice = Path(__file__).resolve().parent.parent
        self.assertTrue(higgsfield.attivo(radice))


class TestPromptGeneratore(unittest.TestCase):
    def test_niente_frasi_da_chat_e_una_composizione_per_variante(self):
        spec = BookSpec(slug="b", title="Bills", categories=["Books > Personal Finance > Budgeting"])
        prima = coverbrief.prompt_da_incollare(spec, pages=192, variante=1, per_chat=False)
        seconda = coverbrief.prompt_da_incollare(spec, pages=192, variante=2, per_chat=False)
        for testo in (prima, seconda):
            self.assertNotIn("variant 1 of", testo)
            self.assertNotIn("tell me", testo)
            self.assertIn("Absolutely no text", testo)
        self.assertNotIn("Composition for this version", prima)
        self.assertIn("Composition for this version: a closer view", seconda)
        self.assertNotEqual(prima, seconda)


if __name__ == "__main__":
    unittest.main()

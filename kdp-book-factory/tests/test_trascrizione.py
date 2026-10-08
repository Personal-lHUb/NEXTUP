import json
import tempfile
import unittest
from pathlib import Path

from kdpfactory import trascrizione


def _riga(ruolo: str, testo: str) -> str:
    return json.dumps({"message": {"role": ruolo, "content": [{"type": "text", "text": testo}]}})


class TestTrascrizione(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.radice = Path(self.tmp.name)
        self.cartella = self.radice / "progetto" / "sessione" / "subagents"
        self.cartella.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def _scrivi(self, agente: str, *righe: str) -> Path:
        percorso = self.cartella / f"agent-{agente}.jsonl"
        percorso.write_text("\n".join(righe) + "\n", encoding="utf-8")
        return percorso

    def test_salva_l_ultimo_oggetto_dell_agente_cosi_come_e_uscito(self):
        self._scrivi(
            "abc",
            _riga("user", 'Rispondi con {"titolo": "dal prompt"}'),
            _riga("assistant", "Leggo i file."),
            _riga("assistant", '```json\n{"titolo": "Hard Calls", "note": "«virgolette» & più"}\n```'),
        )
        uscita = self.radice / "libro" / "scheda.json"
        dati = trascrizione.salva("abc", uscita, radice=self.radice)
        self.assertEqual(dati["titolo"], "Hard Calls")
        self.assertEqual(json.loads(uscita.read_text(encoding="utf-8")), dati)
        self.assertIn("«virgolette» & più", uscita.read_text(encoding="utf-8"))

    def test_con_l_etichetta_prende_l_oggetto_che_la_segue(self):
        percorso = self._scrivi(
            "arch",
            _riga("assistant", 'SCALETTA\n{"chapters": [1, 2]}\n\nFIGURE\n{"servono": false}'),
        )
        self.assertEqual(trascrizione.oggetto(percorso, "SCALETTA"), {"chapters": [1, 2]})
        self.assertEqual(trascrizione.oggetto(percorso, "FIGURE"), {"servono": False})

    def test_senza_oggetto_lo_dice(self):
        percorso = self._scrivi("vuoto", _riga("assistant", "Non ho trovato la pagina."))
        with self.assertRaises(ValueError):
            trascrizione.oggetto(percorso)
        with self.assertRaises(FileNotFoundError):
            trascrizione.trova("inesistente", self.radice)


if __name__ == "__main__":
    unittest.main()

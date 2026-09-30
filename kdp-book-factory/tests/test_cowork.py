"""Il canale con Cowork: dove stanno le richieste, in che stato sono, come si chiamano su Drive."""

import tempfile
import unittest
from pathlib import Path

from kdpfactory import cowork


def scrivi(radice: Path, relativo: str, testo: str = "# richiesta\n") -> Path:
    percorso = radice / relativo
    percorso.parent.mkdir(parents=True, exist_ok=True)
    percorso.write_text(testo, encoding="utf-8")
    return percorso


class TestCanaleCowork(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.radice = Path(self._tmp.name)
        scrivi(self.radice, "books/bollette/manuale/cowork-amazon.md")
        scrivi(self.radice, "books/bollette/manuale/cowork-fonti.md")
        scrivi(self.radice, "books/bollette/manuale/cowork-fonti-risposta.md", "# risposta\n")
        scrivi(self.radice, "config/cowork-kdp.md", "# regole\n\nStato: applicata il 2026-10-01\n")
        # copie che non sono richieste vere
        scrivi(self.radice, "backup/bollette/20260930-100000/manuale/cowork-amazon.md")
        scrivi(self.radice, "books/bollette/build/cowork-amazon.md")

    def tearDown(self):
        self._tmp.cleanup()

    def elenco(self):
        return cowork.richieste(self.radice)

    def test_trova_le_richieste_e_ignora_backup_e_build(self):
        self.assertEqual(
            [r.percorso for r in self.elenco()],
            [
                "books/bollette/manuale/cowork-amazon.md",
                "books/bollette/manuale/cowork-fonti.md",
                "config/cowork-kdp.md",
            ],
        )

    def test_lo_stato_viene_dai_file(self):
        stati = {r.argomento: r.stato for r in self.elenco()}
        self.assertEqual(stati, {"amazon": "aperta", "fonti": "risposta arrivata", "kdp": "applicata"})

    def test_nella_casella_la_cartella_diventa_un_prefisso(self):
        """La casella su Drive è piatta: due libri con la stessa richiesta non si scontrano."""
        amazon, _, kdp = self.elenco()
        self.assertEqual(amazon.nome_drive, "bollette--cowork-amazon.md")
        self.assertEqual(amazon.risposta_drive, "bollette--cowork-amazon-risposta.md")
        self.assertEqual(amazon.risposta, "books/bollette/manuale/cowork-amazon-risposta.md")
        self.assertEqual(kdp.nome_drive, "sistema--cowork-kdp.md")

    def test_dal_nome_su_drive_al_percorso_nel_repo(self):
        elenco = self.elenco()
        trovata = cowork.da_nome_drive(elenco, "bollette--cowork-amazon-risposta.md")
        self.assertEqual(trovata.risposta, "books/bollette/manuale/cowork-amazon-risposta.md")
        # salvata come documento Google, la risposta perde l'estensione nel titolo
        self.assertIs(cowork.da_nome_drive(elenco, "bollette--cowork-amazon-risposta"), trovata)
        self.assertIsNone(cowork.da_nome_drive(elenco, "altro--cowork-amazon-risposta.md"))

    def test_l_avviso_elenca_solo_le_richieste_aperte(self):
        testo = cowork.avviso(self.elenco(), "NEXTUP — libri/cowork")
        self.assertIn(
            "`bollette--cowork-amazon.md` → rispondi in `bollette--cowork-amazon-risposta.md`", testo
        )
        self.assertNotIn("cowork-fonti", testo)
        self.assertNotIn("cowork-kdp", testo)
        self.assertIn("non pubblicare", testo)

    def test_senza_richieste_aperte_l_avviso_lo_dice(self):
        chiuse = [r for r in self.elenco() if r.stato != "aperta"]
        self.assertIn("non ci sono richieste aperte", cowork.avviso(chiuse, "casella"))


if __name__ == "__main__":
    unittest.main()

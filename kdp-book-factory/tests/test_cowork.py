"""Il canale con Cowork su GitHub: dove stanno le richieste, se sono inviate, se la risposta vale."""

import subprocess
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
        scrivi(self.radice, "books/bollette/manuale/cowork-fonti-risposta.md", "Esito: completa\n")
        scrivi(self.radice, "config/cowork-kdp.md", "# regole\n\nStato: applicata il 2026-10-01\n")
        # copie che non sono richieste vere
        scrivi(self.radice, "backup/bollette/20260930-100000/manuale/cowork-amazon.md")
        scrivi(self.radice, "books/bollette/build/cowork-amazon.md")

    def tearDown(self):
        self._tmp.cleanup()

    def elenco(self, **kw):
        return cowork.richieste(self.radice, **kw)

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
        amazon = self.elenco()[0]
        self.assertEqual(amazon.chiave, "bollette")
        self.assertEqual(amazon.risposta, "books/bollette/manuale/cowork-amazon-risposta.md")
        self.assertEqual(self.elenco()[2].chiave, "sistema")

    def test_inviata_vuol_dire_la_stessa_versione_sul_ramo(self):
        """Una correzione fatta qui e non pubblicata, Cowork non la vede."""
        remoto = {"books/bollette/manuale/cowork-amazon.md": "# richiesta\n",
                  "books/bollette/manuale/cowork-fonti.md": "# versione vecchia\n"}
        invio = {r.argomento: r.invio for r in self.elenco(remoto=remoto.get)}
        self.assertEqual(invio, {"amazon": "inviata", "fonti": "da inviare", "kdp": "da inviare"})
        self.assertEqual({r.invio for r in self.elenco()}, {"non controllata"})

    def test_una_richiesta_corretta_dopo_la_risposta_la_rende_superata(self):
        """Cowork ha risposto alla domanda vecchia: la risposta non vale per quella nuova."""
        tempi = {"books/bollette/manuale/cowork-fonti.md": 200,
                 "books/bollette/manuale/cowork-fonti-risposta.md": 100}
        fonti = next(r for r in self.elenco(ultimo_commit=tempi.get) if r.argomento == "fonti")
        self.assertEqual(fonti.stato, "risposta superata")
        tempi["books/bollette/manuale/cowork-fonti-risposta.md"] = 300
        fonti = next(r for r in self.elenco(ultimo_commit=tempi.get) if r.argomento == "fonti")
        self.assertEqual(fonti.stato, "risposta arrivata")

    def test_la_richiesta_di_seguito_e_una_richiesta_a_se(self):
        """Se una risposta è incompleta, i punti mancanti vanno in cowork-<argomento>-2.md."""
        scrivi(self.radice, "books/bollette/manuale/cowork-amazon-2.md")
        seguito = next(r for r in self.elenco() if r.argomento == "amazon-2")
        self.assertEqual(seguito.risposta, "books/bollette/manuale/cowork-amazon-2-risposta.md")
        self.assertEqual(seguito.stato, "aperta")

    def test_l_avviso_elenca_solo_le_richieste_aperte_con_i_percorsi_del_repo(self):
        canale = {"repository": "prova/NEXTUP", "ramo": "canale",
                  "leggimi": "kdp-book-factory/config/leggimi-cowork.md"}
        testo = cowork.avviso(self.elenco(), canale, lambda p: "kdp-book-factory/" + p)
        self.assertIn("prova/NEXTUP, ramo canale", testo)
        self.assertIn("kdp-book-factory/config/leggimi-cowork.md", testo)
        self.assertIn(
            "`kdp-book-factory/books/bollette/manuale/cowork-amazon.md` → rispondi in "
            "`kdp-book-factory/books/bollette/manuale/cowork-amazon-risposta.md`",
            testo,
        )
        self.assertNotIn("cowork-fonti", testo)
        self.assertNotIn("cowork-kdp", testo)
        self.assertIn("non pubblicare", testo)

    def test_senza_richieste_aperte_l_avviso_lo_dice(self):
        chiuse = [r for r in self.elenco() if r.stato != "aperta"]
        self.assertIn("non ci sono richieste aperte", cowork.avviso(chiuse, {}))


class TestRuoli(unittest.TestCase):
    """Ogni chat di Cowork prende solo le richieste del suo ruolo."""

    CANALE = {
        "ramo": "ramo-x",
        "ruoli": {
            "concorrente": {"chat": "Concorrente", "attivita": "NEXTUP — Concorrente",
                            "orari": ["7:52", "13:52"], "compito": "la pagina del concorrente"},
            "parole-chiave": {"chat": "Parole chiave", "attivita": "NEXTUP — Parole chiave",
                              "orari": ["8:07"], "compito": "le parole chiave"},
        },
        "progetto": {"nome": "NEXTUP — Cowork", "attivita_dismessa": "Cowork — casella NEXTUP"},
    }

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.radice = Path(self._tmp.name)
        for relativo, ruolo in (
            ("books/a/concorrente/cowork-concorrente.md", "concorrente"),
            ("books/a/concorrente/cowork-parole-chiave.md", "parole-chiave"),
        ):
            scrivi(self.radice, relativo,
                   cowork.intestazione("Titolo", "x-risposta.md", ruolo, self.CANALE))
        scrivi(self.radice, "books/a/manuale/cowork-vecchia.md", "# senza ruolo\n")

    def test_il_ruolo_si_legge_dalla_richiesta(self):
        ruoli = {r.argomento: r.ruolo for r in cowork.richieste(self.radice)}
        self.assertEqual(ruoli, {"concorrente": "concorrente", "parole-chiave": "parole-chiave",
                                 "vecchia": ""})

    def test_l_avviso_di_un_ruolo_elenca_solo_le_sue(self):
        testo = cowork.avviso(cowork.richieste(self.radice), self.CANALE, ruolo="parole-chiave")
        self.assertIn("cowork-parole-chiave.md", testo)
        self.assertNotIn("cowork-concorrente.md", testo)
        self.assertIn("«parole-chiave»", testo)

    def test_l_avviso_generale_raggruppa_per_ruolo(self):
        """Incollato in una chat senza ruolo, deve dire che le fa tutte."""
        testo = cowork.avviso(cowork.richieste(self.radice), self.CANALE)
        self.assertIn("fai le richieste di tutti i ruoli", testo)
        self.assertLess(testo.index("Ruolo «concorrente»:"), testo.index("Ruolo «parole-chiave»:"))
        self.assertIn("Senza ruolo:", testo)
        self.assertIn("Fetch e Pull", testo)
        self.assertIn("push", testo)

    def test_le_attivita_si_applicano_con_il_loro_trigger(self):
        canale = {**self.CANALE, "ruoli": {"fonti": {"trigger": "trig_x", "attivita": "NEXTUP — Fonti",
                                                       "ogni": "ora", "minuto": 25, "note": ["una nota"]}}}
        [voce] = cowork.attivita(canale)
        self.assertEqual(voce["trigger_id"], "trig_x")
        self.assertEqual(voce["cron_expression"], "CRON_TZ=Europe/Rome 25 * * * *")
        self.assertIn("«Ruolo: fonti»", voce["prompt"])
        self.assertIn("- una nota", voce["prompt"])

    def test_lo_stato_segnala_le_richieste_che_nessuno_prende(self):
        testo = cowork.rapporto(cowork.richieste(self.radice), set(self.CANALE["ruoli"]))
        self.assertIn("nessun giro di Cowork le prende: books/a/manuale/cowork-vecchia.md", testo)

    def test_il_progetto_ha_una_attivita_per_ruolo(self):
        testo = cowork.progetto(self.CANALE)
        for ruolo, dati in self.CANALE["ruoli"].items():
            self.assertIn(f"### {dati['attivita']}", testo)
            self.assertIn(f"«Ruolo: {ruolo}»", testo)
        self.assertIn("alle 7:52 e alle 13:52", testo)
        self.assertIn("Disattiva l'attività «Cowork — casella NEXTUP»", testo)
        self.assertIn("non compri e non cambi niente", testo)
        self.assertIn("NEXTUP — corriere Cowork", testo)
        orario = cowork.progetto({**self.CANALE, "ruoli": {"fonti": {"ogni": "ora", "minuto": 5}}})
        self.assertIn("ogni ora, al minuto 05", orario)


class TestGitVero(unittest.TestCase):
    """L'adattatore a git, su un repository vero con un remoto locale: niente rete."""

    def git(self, cwd, *argomenti):
        subprocess.run(["git", *argomenti], cwd=cwd, check=True, capture_output=True)

    def test_remoto_e_ultimo_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            self.git(base, "init", "--bare", "-q", "remoto.git")
            repo = base / "lavoro"
            self.git(base, "init", "-q", "-b", "canale", "lavoro")
            for chiave, valore in (("user.email", "t@example.org"), ("user.name", "t")):
                self.git(repo, "config", chiave, valore)
            fabbrica = repo / "kdp-book-factory"
            scrivi(fabbrica, "config/cowork-kdp.md", "# inviata\n")
            self.git(repo, "add", ".")
            self.git(repo, "commit", "-q", "-m", "richiesta")
            self.git(repo, "remote", "add", "origin", str(base / "remoto.git"))
            self.git(repo, "push", "-q", "origin", "canale")
            self.git(repo, "fetch", "-q", "origin")

            g = cowork.Git(fabbrica, "canale")
            self.assertEqual(g.remoto("config/cowork-kdp.md"), "# inviata\n")
            self.assertIsNone(g.remoto("config/cowork-altro.md"))
            self.assertIsInstance(g.ultimo_commit("config/cowork-kdp.md"), int)
            self.assertEqual(
                g.percorso_repo("config/cowork-kdp.md"), "kdp-book-factory/config/cowork-kdp.md"
            )

            scrivi(fabbrica, "config/cowork-kdp.md", "# corretta, non pubblicata\n")
            (kdp,) = cowork.richieste(fabbrica, g.remoto, g.ultimo_commit)
            self.assertEqual(kdp.invio, "da inviare")


if __name__ == "__main__":
    unittest.main()

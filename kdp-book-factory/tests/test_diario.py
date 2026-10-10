"""Il contesto che non si perde: diario, prompt, consegne, guardia, ricarica.

Il 10 ottobre, dopo un riassunto della chat, i prompt degli editor si sono
dovuti ripescare dalla trascrizione grezza, e ogni editor rimandava in chat tre
capitoli interi. Questi test tengono fermo il rimedio: gli hook scrivono il
diario e i prompt da soli, la guardia lascia scrivere agli agenti solo la loro
consegna, la consegna entra nel libro con un comando e una copia di backup.
"""

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from kdpfactory import backup, consegne, diario
from kdpfactory.agents import REGISTRY
from kdpfactory.agents.install import render_agent_markdown
from kdpfactory.models import BookProject, ChapterPlan, Outline

ORA = datetime(2026, 10, 10, 9, 30, tzinfo=timezone.utc)


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.radice = Path(self._tmp.name) / "kdp-book-factory"
        self.libro = self.radice / "books" / "libro"
        self.libro.mkdir(parents=True)
        (self.radice / "config").mkdir()
        (self.radice / "config" / "produzione.json").write_text(
            json.dumps({"attivi": ["libro"]}), encoding="utf-8")
        self.project = BookProject(self.libro)

    def hook(self, evento: str, **dati):
        return diario.hook(evento, dati, radice=self.radice, adesso=ORA)


class TestDiario(Base):
    def test_il_lancio_di_un_agente_salva_il_prompt_e_una_riga(self):
        self.hook("pre-agent", tool_input={
            "subagent_type": "editor", "description": "Correzioni sezioni 24-26",
            "prompt": "Correggi le sezioni 24, 25 e 26.",
        })
        prompt = list((self.libro / diario.PROMPT).iterdir())
        self.assertEqual(len(prompt), 1)
        self.assertIn("Correggi le sezioni 24, 25 e 26.", prompt[0].read_text(encoding="utf-8"))
        righe = diario.righe(self.project)
        self.assertEqual(len(righe), 1)
        self.assertIn("lanciato `editor` «Correzioni sezioni 24-26»", righe[0])
        self.assertIn("2026-10-10 09:30 UTC", righe[0])

    def test_l_agente_in_background_resta_in_volo_finche_non_finisce(self):
        entrata = {"subagent_type": "editor", "description": "Correzioni 24-26"}
        self.hook("post-agent", tool_input=entrata,
                  tool_response={"content": [{"type": "text", "text": "agentId: a1b2c3 (internal ID)"}]})
        self.assertEqual(len(diario.in_volo(self.project)), 1)
        self.assertIn("a1b2c3", diario.in_volo(self.project)[0])
        self.hook("subagent-stop", agent_id="a1b2c3", agent_type="editor",
                  last_assistant_message="books/libro/consegne/x.md: 3 capitoli, 5.400 parole")
        self.assertEqual(diario.in_volo(self.project), [])
        self.assertIn("3 capitoli", diario.righe(self.project)[-1])

    def test_una_risposta_lunga_non_si_perde_finisce_in_consegne(self):
        lunga = "# Capitolo\n\n" + "Testo del capitolo. " * 200
        self.hook("subagent-stop", agent_id="zz9", agent_type="editor", last_assistant_message=lunga)
        salvate = list((self.libro / diario.CONSEGNE).iterdir())
        self.assertEqual(len(salvate), 1)
        self.assertEqual(salvate[0].read_text(encoding="utf-8").strip(), lunga.strip())
        self.assertEqual(diario.da_importare(self.project), [salvate[0].name])

    def test_un_agente_interno_senza_tipo_non_entra_nel_diario(self):
        # Il suggerimento del prossimo messaggio non è una risposta dell'autore.
        self.hook("subagent-stop", agent_id="ab6", agent_type="",
                  last_assistant_message="Confermo 6x9 e prezzo 21,99")
        self.assertEqual(diario.righe(self.project), [])

    def test_una_risposta_spezzata_dal_limite_si_salva_intera(self):
        trascritta = Path(self._tmp.name) / "agent-x.jsonl"
        def detto(testo):
            return {"message": {"role": "assistant", "content": [{"type": "text", "text": testo}]}}

        righe = [
            {"message": {"role": "user", "content": [{"type": "tool_result", "content": "ok"}]}},
            detto("# Glossary\n\n" + "a " * 900 + "a second"),
            {"isMeta": True, "message": {"role": "user", "content": "Output token limit hit. Resume."}},
            detto("clinician adds a note."),
        ]
        trascritta.write_text("\n".join(json.dumps(r) for r in righe), encoding="utf-8")
        self.hook("subagent-stop", agent_id="x", agent_type="editor",
                  last_assistant_message="clinician adds a note.", agent_transcript_path=str(trascritta))
        salvata = next((self.libro / diario.CONSEGNE).iterdir()).read_text(encoding="utf-8")
        self.assertTrue(salvata.startswith("# Glossary"))
        self.assertIn("a second clinician adds a note.", salvata)
        self.assertIn("ricucita da 2 messaggi", diario.righe(self.project)[-1])

    def test_senza_libro_attivo_gli_hook_non_scrivono_niente(self):
        (self.radice / "config" / "produzione.json").write_text('{"attivi": []}', encoding="utf-8")
        self.assertEqual(self.hook("pre-agent", tool_input={"prompt": "x"})[0], 0)
        self.assertFalse(diario.percorso(self.project).exists())

    def test_il_riassunto_della_chat_lascia_un_segno(self):
        self.hook("pre-compact", trigger="auto")
        self.assertIn("la chat viene riassunta (auto)", diario.righe(self.project)[-1])

    def test_all_avvio_tornano_stato_agenti_consegne_e_diario(self):
        (self.radice.parent / "STATO.md").write_text("# Stato\n\nfase 5 in corso\n", encoding="utf-8")
        self.hook("post-agent", tool_input={"subagent_type": "editor", "description": "Correzioni 24-26"},
                  tool_response="agentId: q7")
        (self.libro / diario.CONSEGNE).mkdir()
        (self.libro / diario.CONSEGNE / "editor-24-26.md").write_text("# T\n", encoding="utf-8")
        codice, testo, _ = self.hook("session-start", source="compact")
        self.assertEqual(codice, 0)
        self.assertIn("Contesto dopo il riassunto della chat", testo)
        self.assertIn("fase 5 in corso", testo)
        self.assertIn("«Correzioni 24-26» (id `q7`)", testo)
        self.assertIn("editor-24-26.md", testo)


class TestGuardia(Base):
    def test_un_agente_scrive_solo_la_sua_consegna(self):
        dentro = "/x/kdp-book-factory/books/libro/consegne/editor.md"
        fuori = "/x/kdp-book-factory/books/libro/manuale/capitolo-01.md"
        self.assertEqual(self.hook("guardia", agent_id="a1", agent_type="editor",
                                   tool_input={"file_path": dentro})[0], 0)
        codice, _, messaggio = self.hook("guardia", agent_id="a1", agent_type="editor",
                                         tool_input={"file_path": fuori})
        self.assertEqual(codice, 2)
        self.assertIn("consegne", messaggio)

    def test_niente_scappatoie_col_percorso(self):
        furbo = "/x/books/libro/consegne/../book.json"
        self.assertEqual(self.hook("guardia", agent_id="a1", tool_input={"file_path": furbo})[0], 2)

    def test_la_sessione_principale_non_e_toccata(self):
        self.assertEqual(self.hook("guardia", tool_input={"file_path": "/x/book.json"})[0], 0)


class TestConsegne(Base):
    def setUp(self):
        super().setUp()
        Outline(title="Libro", chapters=[
            ChapterPlan(number=1, title="Uno", role="chapter", target_words=50),
            ChapterPlan(number=2, title="Due", role="chapter", target_words=50),
        ]).save(self.project.outline_path)
        (self.libro / "manuale").mkdir()
        (self.libro / "manuale" / "capitolo-01.md").write_text("# Uno\n\nprima versione\n", encoding="utf-8")
        backup.configure(directory=Path(self._tmp.name) / "backup")
        self.addCleanup(backup.configure)
        (self.libro / "consegne").mkdir()
        self.file = self.libro / "consegne" / "editor-1-2.md"

    def test_i_capitoli_entrano_con_il_backup_e_il_diario(self):
        self.file.write_text("Ecco i capitoli.\n\n# Uno\n\nnuovo testo\n\n# Due\n\naltro testo\n```\n",
                             encoding="utf-8")
        esiti = consegne.importa_capitoli(self.project, self.file, [1, 2], adesso=ORA)
        self.assertEqual([e["numero"] for e in esiti], [1, 2])
        self.assertEqual((self.libro / "manuale" / "capitolo-02.md").read_text(encoding="utf-8"),
                         "# Due\n\naltro testo\n")
        self.assertTrue(self.project.chapter_path(1).exists())
        prima = list((Path(self._tmp.name) / "backup").rglob("capitolo-01.md.prima"))
        self.assertEqual(prima[0].read_text(encoding="utf-8"), "# Uno\n\nprima versione\n")
        self.assertEqual(diario.da_importare(self.project), [])

    def test_un_titolo_cambiato_non_sovrascrive_niente(self):
        self.file.write_text("# Uno\n\nnuovo\n\n# Tre\n\naltro\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            consegne.importa_capitoli(self.project, self.file, [1, 2])
        self.assertIn("prima versione",
                      (self.libro / "manuale" / "capitolo-01.md").read_text(encoding="utf-8"))

    def test_un_rapporto_va_dove_serve(self):
        self.file.write_text("# Rapporto\n\n[minore] …\n", encoding="utf-8")
        arrivo = consegne.importa_file(self.project, self.file, "revisioni/lettore-cieco.md")
        self.assertEqual(arrivo.read_text(encoding="utf-8"), "# Rapporto\n\n[minore] …\n")
        with self.assertRaises(ValueError):
            consegne.importa_file(self.project, self.file, "../../fuori.md")


class TestAgentiConsegnano(unittest.TestCase):
    def test_chi_usa_il_modello_ha_write_e_la_regola_della_consegna(self):
        editor = render_agent_markdown(REGISTRY["editor"])
        self.assertIn("tools: Read, Grep, Glob, Write", editor)
        self.assertIn("## Consegna", editor)
        self.assertIn("books/<slug>/consegne/", editor)

    def test_chi_esegue_un_comando_non_cambia(self):
        impaginazione = render_agent_markdown(REGISTRY["impaginazione"])
        self.assertIn("tools: Read, Grep, Glob, Bash", impaginazione)
        self.assertNotIn("Write", impaginazione.split("---")[1])


if __name__ == "__main__":
    unittest.main()

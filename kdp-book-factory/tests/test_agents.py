"""Test del collegio editoriale: registro, prompt, rilevatori tipografici, ciclo di revisione."""

import tempfile
import unittest
from pathlib import Path

from kdpfactory import agents, backup, planner, writer
from kdpfactory.agents.base import AgentContext, AgentFinding
from kdpfactory.agents.install import install_claude_code_agents
from kdpfactory.agents.layout import (
    Line,
    _check_frame_overflow,
    _check_hyphen_ladders,
    _check_widows_orphans,
    _flush_left_by_parity,
    _measure_first_line_indent,
)
from kdpfactory.llm import LLMClient, LLMConfig
from kdpfactory.models import BookProject, BookSpec, ChapterPlan, Outline

LEFT = 36.0
INDENT = 15.84
MEASURE = 360.0
BODY = 11.0


def line(page, x0, width, size=BODY, text="testo", y0=100.0):
    return Line(
        page=page, text=text, x0=x0, x1=x0 + width, y0=y0, y1=y0 + 15, size=size, font="F"
    )


def full_page(page, count=10, y_start=80.0):
    """Pagina di righe piene a filo di margine."""
    return [line(page, LEFT, MEASURE, y0=y_start + i * 16) for i in range(count)]


class TestRegistro(unittest.TestCase):
    def test_agenti_attesi_presenti(self):
        attesi = {
            "architetto",
            "ghostwriter",
            "voce",
            "editor",
            "lettore-cieco",
            "fact-checker",
            "conformita",
            "correttore",
            "editor-sviluppo",
            "impaginazione",
        }
        self.assertTrue(attesi.issubset(set(agents.REGISTRY)))

    def test_due_famiglie(self):
        self.assertTrue(agents.agents_by_stage("produzione"))
        self.assertTrue(agents.agents_by_stage("controllo"))
        for agent in agents.review_agents():
            self.assertEqual(agent.stage, "controllo")

    def test_livelli_di_lavorazione(self):
        self.assertEqual(agents.QUALITY_LEVELS["bozza"]["reviewers"], ())
        self.assertIn("impaginazione", agents.QUALITY_LEVELS["standard"]["reviewers"])
        self.assertIn("correttore", agents.QUALITY_LEVELS["alta"]["reviewers"])

    def test_agente_sconosciuto(self):
        with self.assertRaises(ValueError):
            agents.get_agent("non-esiste")


class TestLettoreCieco(unittest.TestCase):
    """Il punto del lettore cieco è che non sa nulla: va verificato sul prompt."""

    def setUp(self):
        self.spec = BookSpec(
            slug="t",
            title="Il Titolo Segreto",
            topic="un argomento riconoscibile",
            promise="una promessa riconoscibile",
        )
        self.outline = Outline(
            title=self.spec.title,
            thesis="tesi riconoscibile",
            chapters=[ChapterPlan(number=1, title="Capitolo Uno", summary="sintesi riconoscibile")],
        )

    def test_non_riceve_scheda_ne_scaletta(self):
        agent = agents.get_agent("lettore-cieco")
        ctx = AgentContext(
            spec=self.spec, outline=self.outline, chapter=self.outline.chapters[0], text="testo"
        )
        prompt = "\n".join(agent.system(ctx)) + agent.user(ctx)
        for segreto in ("Il Titolo Segreto", "tesi riconoscibile", "sintesi riconoscibile",
                        "una promessa riconoscibile"):
            self.assertNotIn(segreto, prompt)

    def test_e_marcato_come_cieco(self):
        self.assertTrue(agents.get_agent("lettore-cieco").blind)
        self.assertFalse(agents.get_agent("fact-checker").blind)

    def test_altri_revisori_ricevono_il_contesto(self):
        agent = agents.get_agent("editor-sviluppo")
        ctx = AgentContext(spec=self.spec, outline=self.outline, text="digest")
        self.assertIn("Il Titolo Segreto", "\n".join(agent.system(ctx)))


class TestFinding(unittest.TestCase):
    def test_accetta_chiavi_italiane_e_inglesi(self):
        italiano = AgentFinding.from_dict(
            {"gravita": "BLOCCANTE", "categoria": "claim", "problema": "dato inventato"},
            agent="fact-checker",
            chapter=3,
        )
        self.assertEqual(italiano.severity, "bloccante")
        self.assertEqual(italiano.chapter, 3)
        inglese = AgentFinding.from_dict(
            {"severity": "importante", "category": "x", "issue": "y", "chapter": 5},
            agent="conformita",
        )
        self.assertEqual(inglese.chapter, 5)

    def test_gravita_sconosciuta_diventa_minore(self):
        finding = AgentFinding(agent="x", severity="catastrofico", category="c", issue="i")
        self.assertEqual(finding.severity, "minore")

    def test_filtro_per_gravita(self):
        findings = [
            AgentFinding(agent="a", severity="bloccante", category="c", issue="i"),
            AgentFinding(agent="a", severity="importante", category="c", issue="i"),
            AgentFinding(agent="a", severity="minore", category="c", issue="i"),
        ]
        self.assertEqual(len(agents.filter_findings(findings, "bloccante")), 1)
        self.assertEqual(len(agents.filter_findings(findings, "importante")), 2)
        self.assertEqual(len(agents.filter_findings(findings, "minore")), 3)


class TestImpaginazione(unittest.TestCase):
    """I rilevatori tipografici lavorano su coordinate: si testano su righe sintetiche."""

    def test_misura_il_rientro_di_capoverso(self):
        pages = {1: full_page(1)}
        pages[1][3] = line(1, LEFT + INDENT, MEASURE - INDENT, y0=pages[1][3].y0)
        flush = _flush_left_by_parity([ln for p in pages.values() for ln in p])
        self.assertAlmostEqual(_measure_first_line_indent(pages, flush, BODY), INDENT, places=1)

    def test_riconosce_riga_orfana(self):
        page = full_page(11)
        page[-1] = line(11, LEFT + INDENT, MEASURE - INDENT, y0=page[-1].y0)  # capoverso nuovo
        page[4] = line(11, LEFT + INDENT, MEASURE - INDENT, y0=page[4].y0)    # capoverso certo
        findings = _check_widows_orphans({11: page}, 11, MEASURE, BODY, "F", {1: LEFT}, INDENT, 1)
        self.assertIn("riga orfana", {f.category for f in findings})

    def test_riconosce_riga_vedova(self):
        page = full_page(12)
        page[0] = line(12, LEFT, MEASURE * 0.3, y0=page[0].y0)                 # coda di capoverso
        page[1] = line(12, LEFT + INDENT, MEASURE - INDENT, y0=page[1].y0)     # capoverso nuovo
        page[5] = line(12, LEFT + INDENT, MEASURE - INDENT, y0=page[5].y0)
        findings = _check_widows_orphans({12: page}, 12, MEASURE, BODY, "F", {0: LEFT}, INDENT, 1)
        self.assertIn("riga vedova", {f.category for f in findings})

    def test_riconosce_titolo_a_piede_di_pagina(self):
        page = full_page(13)
        page[-1] = line(13, LEFT, 200, size=BODY + 2, text="Una sezione", y0=page[-1].y0)
        page[-1].font = "Display"
        findings = _check_widows_orphans({13: page}, 13, MEASURE, BODY, "F", {1: LEFT}, INDENT, 1)
        self.assertIn("titolo a piede di pagina", {f.category for f in findings})

    def test_pagina_pulita_non_produce_segnalazioni(self):
        page = full_page(14)
        page[3] = line(14, LEFT + INDENT, MEASURE - INDENT, y0=page[3].y0)
        findings = _check_widows_orphans({14: page}, 14, MEASURE, BODY, "F", {0: LEFT}, INDENT, 1)
        self.assertEqual(findings, [])

    def test_elenco_puntato_non_e_una_riga_orfana(self):
        """Un elenco rientra tutte le sue righe: non va scambiato per un capoverso."""
        page = full_page(15)
        bullet_x = LEFT + 21.6
        page[-2] = line(15, bullet_x, 200, y0=page[-2].y0)
        page[-1] = line(15, bullet_x, 200, y0=page[-1].y0)
        page[4] = line(15, LEFT + INDENT, MEASURE - INDENT, y0=page[4].y0)
        findings = _check_widows_orphans({15: page}, 15, MEASURE, BODY, "F", {1: LEFT}, INDENT, 1)
        self.assertEqual(findings, [])

    def test_testo_fuori_gabbia(self):
        from kdpfactory import kdpspecs

        geo = kdpspecs.page_geometry("6x9", 100)
        lines = [line(3, geo.inner_margin, geo.text_width + 20)]
        findings = _check_frame_overflow(lines, geo)
        self.assertEqual(findings[0].severity, "bloccante")

    def test_scaletta_di_sillabazione(self):
        page = [line(7, LEFT, MEASURE, text=f"parola spez-{i}-") for i in range(4)]
        for ln in page:
            ln.text = ln.text.rstrip("-") + "-"
        findings = _check_hyphen_ladders({7: page})
        self.assertEqual(findings[0].category, "scaletta di sillabazione")

    def test_senza_pdf_lo_dichiara(self):
        result = agents.get_agent("impaginazione").run(AgentContext(spec=BookSpec(slug="t", title="T")))
        self.assertEqual(result.findings[0].category, "pdf mancante")


class TestCicloDiRevisione(unittest.TestCase):
    """Ciclo completo in dry-run: revisione, rapporto, applicazione delle modifiche."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.project = BookProject(Path(cls.tmp.name) / "libro")
        cls.project.ensure_dirs()
        cls.spec = BookSpec(
            slug="libro", title="Libro di Prova", topic="collaudo", target_pages=60, chapters=3
        )
        cls.spec.save(cls.project.spec_path)
        # I test non devono scrivere nella cartella di backup del progetto.
        backup.configure(enabled=False)
        cls.client = LLMClient(LLMConfig(dry_run=True, verbose=False))
        budget = planner.build_budget(cls.spec)
        cls.outline = writer.generate_outline(cls.spec, cls.client, budget)
        cls.outline.save(cls.project.outline_path)
        writer.write_chapters(cls.project, cls.spec, cls.outline, cls.client)

    @classmethod
    def tearDownClass(cls):
        backup.configure(enabled=True, directory=None)
        cls.tmp.cleanup()

    def test_revisione_produce_segnalazioni_e_rapporto(self):
        report = agents.run_review(
            self.project,
            self.spec,
            self.outline,
            self.client,
            agent_names=["lettore-cieco", "fact-checker"],
            only=[2],
        )
        self.assertTrue(report.findings)
        self.assertTrue(all(f.chapter == 2 for f in report.findings))
        self.assertTrue((self.project.build_dir / "revisioni.md").exists())
        self.assertTrue((self.project.build_dir / "revisioni.json").exists())

    def test_rapporto_si_rilegge_da_disco(self):
        agents.run_review(
            self.project, self.spec, self.outline, self.client,
            agent_names=["conformita"], only=[2],
        )
        riletto = agents.ReviewReport.load(self.project)
        self.assertTrue(riletto.findings)
        self.assertEqual(riletto.findings[0].agent, "conformita")

    def test_editor_conserva_il_capitolo(self):
        """In dry-run l'editor restituisce il testo invariato: il file resta valido."""
        path = self.project.chapter_path(2)
        before = path.read_text(encoding="utf-8")
        report = agents.ReviewReport()
        report.findings.append(
            AgentFinding(
                agent="fact-checker",
                severity="importante",
                category="dato",
                issue="numero non verificabile",
                chapter=2,
            )
        )
        revised = agents.apply_revisions(
            self.project, self.spec, self.outline, self.client, report, min_severity="importante"
        )
        self.assertEqual(revised, [2])
        after = path.read_text(encoding="utf-8")
        self.assertTrue(after.startswith("# "))
        self.assertAlmostEqual(len(after.split()), len(before.split()), delta=10)

    def test_passata_di_stile_non_perde_testo(self):
        path = self.project.chapter_path(3)
        before = len(path.read_text(encoding="utf-8").split())
        agents.voice_pass(self.project, self.spec, self.outline, self.client, only=[3])
        after = len(path.read_text(encoding="utf-8").split())
        self.assertGreaterEqual(after, before * 0.7)


class TestInstallazioneSubagent(unittest.TestCase):
    def test_scrive_un_file_per_agente(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / ".claude" / "agents"
            written = install_claude_code_agents(target)
            self.assertEqual(len(written), len(agents.REGISTRY))
            content = (target / "lettore-cieco.md").read_text(encoding="utf-8")
            self.assertTrue(content.startswith("---\nname: lettore-cieco\n"))
            self.assertIn("description:", content)


if __name__ == "__main__":
    unittest.main()

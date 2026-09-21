"""Test del collegio editoriale: registro, prompt, rilevatori tipografici, ciclo di revisione."""

import tempfile
import unittest
from pathlib import Path

from kdpfactory import agents, backup, planner, prompts, writer
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
            "copertina",
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


class _ClienteFinto:
    """Client minimo: restituisce la risposta preparata e registra le chiamate."""

    def __init__(self, risposta: dict):
        self.risposta = risposta
        self.chiamate = 0

    def complete_json(self, **kwargs) -> dict:
        self.chiamate += 1
        return self.risposta


class TestAgenteIndice(unittest.TestCase):
    """L'indice è la pagina che il cliente guarda prima di comprare."""

    def outline(self) -> Outline:
        return Outline(
            title="Titolo",
            chapters=[
                ChapterPlan(number=1, title="Introduzione", role="intro"),
                ChapterPlan(number=2, title="La gestione delle richieste"),
                ChapterPlan(number=3, title="L'ottimizzazione del processo"),
            ],
        )

    def test_e_registrato_fra_gli_agenti_di_produzione(self):
        agente = agents.get_agent("indice")
        self.assertEqual(agente.stage, "produzione")

    def test_applica_i_titoli_alla_scaletta(self):
        outline = self.outline()
        client = _ClienteFinto(
            {
                "chapters": [
                    {"number": 1, "title": "Perché tre ore bastano"},
                    {"number": 2, "title": "Dire di no senza perdere il cliente"},
                    {"number": 3, "title": "Chiudere la giornata alle 15"},
                ],
                "notes": "ordine solido",
            }
        )
        note = writer.apply_index(BookSpec(slug="t", title="Titolo"), outline, client)
        self.assertEqual(client.chiamate, 1)
        self.assertEqual(
            [c.title for c in outline.chapters],
            [
                "Perché tre ore bastano",
                "Dire di no senza perdere il cliente",
                "Chiudere la giornata alle 15",
            ],
        )
        self.assertEqual(note, "ordine solido")

    def test_un_indice_parziale_non_viene_applicato(self):
        """Metà titoli nuovi e metà vecchi sarebbe peggio di nessun titolo nuovo."""
        outline = self.outline()
        prima = [c.title for c in outline.chapters]
        client = _ClienteFinto({"chapters": [{"number": 2, "title": "Solo questo"}]})
        writer.apply_index(BookSpec(slug="t", title="Titolo"), outline, client)
        self.assertEqual([c.title for c in outline.chapters], prima)


class TestLettoreCiecoSulLibro(unittest.TestCase):
    """Sul libro intero il lettore cieco riceve l'indice, non la scaletta."""

    def test_sul_capitolo_non_riceve_nessun_indice(self):
        agente = agents.get_agent("lettore-cieco")
        ctx = AgentContext(spec=BookSpec(slug="t", title="T"), text="Un capitolo.")
        self.assertNotIn("indice", agente.user(ctx).lower())

    def test_sul_libro_riceve_l_indice_e_cambia_regole(self):
        agente = agents.get_agent("lettore-cieco")
        ctx_capitolo = AgentContext(spec=BookSpec(slug="t", title="T"), text="Un capitolo.")
        ctx_libro = AgentContext(
            spec=BookSpec(slug="t", title="T"),
            text="Il libro.",
            metadata={"indice": "1. Primo capitolo\n2. Secondo capitolo"},
        )
        self.assertIn("1. Primo capitolo", agente.user(ctx_libro))
        self.assertNotEqual(agente.system(ctx_capitolo), agente.system(ctx_libro))
        # Senza il contratto JSON la pipeline non saprebbe leggere la risposta.
        self.assertIn('"findings"', agente.system(ctx_libro)[0])


class TestContestoFocalizzato(unittest.TestCase):
    """Il blocco «già trattato» non deve crescere con la lunghezza del libro.

    Viaggia nel messaggio dell'utente, quindi fuori dalla cache, e soprattutto
    spinge in fondo l'istruzione che conta: scrivi QUESTO capitolo, questi
    punti, questa lunghezza.
    """

    def riassunto(self, n: int) -> str:
        return f"Riassunto del capitolo {n}: " + "parola " * 55

    def test_un_libro_corto_non_viene_toccato(self):
        covered = [self.riassunto(i) for i in range(1, 4)]
        tenuti, omessi = prompts.focus_covered(covered)
        self.assertEqual(tenuti, covered)
        self.assertEqual(omessi, 0)

    def test_si_tengono_i_piu_recenti(self):
        covered = [self.riassunto(i) for i in range(1, 21)]
        tenuti, omessi = prompts.focus_covered(covered)
        self.assertGreater(omessi, 0)
        self.assertEqual(tenuti[-1], covered[-1])          # l'ultimo scritto c'è sempre
        self.assertNotIn(covered[0], tenuti)               # il primo no
        self.assertLessEqual(sum(len(t.split()) for t in tenuti), prompts.COVERED_BUDGET_WORDS)

    def test_il_minimo_vince_sul_budget(self):
        """Con riassunti lunghissimi arrivano comunque gli ultimi capitoli."""
        covered = ["parola " * 5000 for _ in range(10)]
        tenuti, _ = prompts.focus_covered(covered)
        self.assertEqual(len(tenuti), prompts.COVERED_MIN_CHAPTERS)
        self.assertEqual(tenuti[-1], covered[-1])

    def test_il_prompt_dice_dove_sono_finiti_gli_altri(self):
        spec = BookSpec(slug="t", title="T")
        chapter = ChapterPlan(number=20, title="Capitolo", summary="s", target_words=1700)
        testo = prompts.chapter_prompt(
            spec, chapter, covered=[self.riassunto(i) for i in range(1, 20)]
        )
        self.assertIn("GIÀ TRATTATO", testo)
        self.assertIn("struttura completa del libro", testo)
        self.assertIn("non ripetere nemmeno quelli", testo)

    def test_il_contesto_smette_di_crescere(self):
        """Il capitolo 30 non riceve più contesto del capitolo 12."""
        spec = BookSpec(slug="t", title="T")
        chapter = ChapterPlan(number=99, title="Capitolo", summary="s", target_words=1700)
        dodici = prompts.chapter_prompt(
            spec, chapter, covered=[self.riassunto(i) for i in range(1, 12)]
        )
        trenta = prompts.chapter_prompt(
            spec, chapter, covered=[self.riassunto(i) for i in range(1, 30)]
        )
        # la coda che nomina gli omessi cresce di poche decine di caratteri
        self.assertLess(len(trenta) - len(dodici), 120)


class TestVarietaDellePagine(unittest.TestCase):
    """Il confine fra medium-content e low-content, misurato sulla pagina.

    Il banco di prova è quello scritto in CLAUDE.md: se due pagine si possono
    scambiare senza che cambi niente, il libro è un quaderno.
    """

    def contesto(self, content_type: str) -> AgentContext:
        return AgentContext(
            spec=BookSpec(slug="t", title="T", content_type=content_type),
            chapter_pages={"1": 1},
        )

    def pagina_uguale(self, numero: int) -> list:
        return [line(numero, 36.0, 300.0, text="riga di testo corrente uguale a tutte")
                for _ in range(20)]

    def pagina_varia(self, numero: int) -> list:
        """Pagine con numero di righe, corpi e bordi diversi fra loro."""
        righe = []
        for i in range(3 + numero % 9):
            righe.append(
                line(numero, 36.0 + (i * numero % 4) * 18, 120.0 + numero,
                     size=9.0 + (numero % 3), text="x" * (10 + numero * 3 + i))
            )
        return righe

    def _misura(self, pagine: dict, content_type: str = "medium"):
        from kdpfactory.agents.layout import _check_page_variety

        return _check_page_variety(pagine, self.contesto(content_type), body_start=1)

    def test_pagine_tutte_uguali_sono_low_content(self):
        pagine = {n: self.pagina_uguale(n) for n in range(1, 31)}
        findings = self._misura(pagine)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, "varietà delle pagine")
        self.assertIn("100%", findings[0].issue)

    def test_pagine_diverse_non_segnalano_niente(self):
        pagine = {n: self.pagina_varia(n) for n in range(1, 31)}
        self.assertEqual(self._misura(pagine), [])

    def test_su_un_full_content_la_misura_non_si_applica(self):
        """Un saggio ha pagine di testo tutte uguali per costruzione."""
        pagine = {n: self.pagina_uguale(n) for n in range(1, 31)}
        self.assertEqual(self._misura(pagine, content_type="full"), [])

    def test_troppe_poche_pagine_non_dicono_niente(self):
        pagine = {n: self.pagina_uguale(n) for n in range(1, 6)}
        self.assertEqual(self._misura(pagine), [])

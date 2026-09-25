"""Una competenza, un solo responsabile: la regola che tiene insieme il collegio.

Prima di questa tabella il lettore cieco, l'editor di sviluppo e la conformità
controllavano tutti e tre se il libro manteneva le sue promesse, e il
fact-checker contava i casi del libro insieme all'editor di sviluppo: sullo
stesso libro sono arrivate quattro segnalazioni della stessa contraddizione,
scritte in quattro modi. Questi test tengono chiusa quella porta.
"""

import json
import tempfile
import unittest
from pathlib import Path

from kdpfactory import agents, coverbrief, vetrina, writer
from kdpfactory.agents import REGISTRY, AgentContext
from kdpfactory.agents.competenze import COMPETENZE, CONFINANTI, FASI, competenze_di, fuori_campo
from kdpfactory.agents.install import render_agent_markdown
from kdpfactory.agents.review import BLIND_READER_BOOK_RULES, COMPLIANCE_RULES, STRUCTURAL_RULES
from kdpfactory.agents.scaletta import esamina
from kdpfactory.models import BookProject, BookSpec, ChapterPlan, Outline, PartPlan


class TestTabella(unittest.TestCase):
    def test_ogni_agente_del_collegio_ha_un_campo(self):
        senza = [nome for nome in REGISTRY if not competenze_di(nome)]
        self.assertEqual(senza, [], "un agente senza competenze non sa che cosa non fare")

    def test_ogni_responsabile_esiste(self):
        for competenza in COMPETENZE:
            with self.subTest(competenza=competenza.cosa[:40]):
                self.assertIn(competenza.agente, REGISTRY)
                self.assertIn(competenza.fase, FASI)
        for a, b in CONFINANTI:
            self.assertIn(a, REGISTRY)
            self.assertIn(b, REGISTRY)

    def test_nessuna_competenza_due_volte(self):
        voci = [c.cosa for c in COMPETENZE]
        self.assertEqual(len(voci), len(set(voci)))

    def test_nessuno_si_esclude_da_solo(self):
        for nome in REGISTRY:
            self.assertNotIn(nome, {c.agente for c in fuori_campo(nome)})


class TestConfiniNeiPrompt(unittest.TestCase):
    """Il campo e il fuori campo arrivano davvero a chi legge."""

    def spec(self) -> BookSpec:
        return BookSpec(slug="t", title="T")

    def test_i_revisori_sanno_che_cosa_non_guardare(self):
        for nome in ("lettore-cieco", "fact-checker", "conformita", "correttore", "editor-sviluppo"):
            with self.subTest(agente=nome):
                ctx = AgentContext(spec=self.spec(), outline=Outline(title="T"), text="x")
                sistema = REGISTRY[nome].system(ctx)[0]
                self.assertIn("IL TUO CAMPO", sistema)
                self.assertIn("NON È COMPITO TUO", sistema)
                # e il contratto JSON resta in fondo, dove la pipeline lo cerca
                self.assertIn('"findings"', sistema)

    def test_le_promesse_hanno_un_solo_guardiano(self):
        """Promessa della vetrina: solo il lettore cieco, che la legge da cliente."""
        self.assertIn("LE PROMESSE DELLA VETRINA", BLIND_READER_BOOK_RULES)
        self.assertNotIn("PROMESSE NON MANTENUTE", STRUCTURAL_RULES)
        self.assertNotIn("COERENZA CON LA PROMESSA", COMPLIANCE_RULES)

    def test_ordine_e_ripetizioni_sono_dell_editor_di_sviluppo(self):
        corpo_lettore = BLIND_READER_BOOK_RULES.split("IL TUO CAMPO")[0]
        self.assertNotIn("L'ORDINE", corpo_lettore)
        self.assertNotIn("RIPETIZIONI FRA CAPITOLI", corpo_lettore)
        self.assertIn("SOVRAPPOSIZIONI E RIPETIZIONI", STRUCTURAL_RULES)
        self.assertIn("CONTRADDIZIONI E CONTI", STRUCTURAL_RULES)

    def test_l_indice_non_tocca_l_ordine(self):
        regole = REGISTRY["indice"].system(AgentContext(spec=self.spec()))[0]
        self.assertIn("Non cambi l'ordine", regole)
        self.assertNotIn("La sequenza\n", regole)


class TestFileEsportati(unittest.TestCase):
    def test_ogni_file_dice_il_suo_campo(self):
        for nome, agente in REGISTRY.items():
            with self.subTest(agente=nome):
                testo = render_agent_markdown(agente)
                self.assertIn("## Il tuo campo", testo)
                self.assertEqual(testo.count("## Il tuo campo"), 1)
                self.assertNotIn("IL TUO CAMPO", testo, "i confini del prompt vanno tolti")
                if fuori_campo(nome):
                    self.assertIn("## Non è compito tuo", testo)

    def test_il_lettore_cieco_resta_cieco_anche_in_claude_code(self):
        testo = render_agent_markdown(REGISTRY["lettore-cieco"])
        for vietato in ("outline.json", "book.json", "brief.md", "manuale/"):
            self.assertIn(vietato, testo.split("**Non aprire mai:**")[1][:600])
        self.assertIn("build/vetrina.md", testo)
        self.assertIn("## Sul capitolo", testo)
        self.assertIn("## Sul libro intero", testo)

    def test_la_copertina_passa_dal_comando(self):
        testo = render_agent_markdown(REGISTRY["copertina"])
        self.assertIn("python3 -m kdpfactory copertina <slug>", testo)
        self.assertIn("il prompt lo scrive il sistema", testo)
        self.assertIn("--agents copertina", testo)
        self.assertIn("assets/copertina.jpg", testo)

    def test_l_indice_consegna_titoli_e_parti(self):
        testo = render_agent_markdown(REGISTRY["indice"])
        self.assertIn('"parts"', testo)
        self.assertIn("scaletta --esamina", testo)
        self.assertNotIn("Elenca le segnalazioni", testo, "l'indice produce, non segnala")

    def test_la_conformita_legge_anche_la_scheda(self):
        testo = render_agent_markdown(REGISTRY["conformita"])
        self.assertIn("## Sulla scheda prodotto", testo)
        ctx = AgentContext(spec=BookSpec(slug="t", title="T"), metadata={"scheda": "Parole chiave: x"})
        self.assertIn("PAROLE CHIAVE", REGISTRY["conformita"].system(ctx)[0])


class TestIndice(unittest.TestCase):
    def outline(self) -> Outline:
        return Outline(
            title="T",
            chapters=[ChapterPlan(number=n, title=f"Titolo {n}") for n in range(1, 5)],
            parts=[PartPlan("Prima parte", 1), PartPlan("Seconda parte", 3)],
        )

    def test_riceve_le_parti(self):
        ctx = AgentContext(spec=BookSpec(slug="t", title="T"), outline=self.outline())
        messaggio = REGISTRY["indice"].user(ctx)
        self.assertIn("dal capitolo 3: Seconda parte", messaggio)
        self.assertIn("2 parti con gli stessi capitoli", messaggio)

    def test_applica_i_titoli_delle_parti_solo_se_ci_sono_tutti(self):
        class Cliente:
            def __init__(self, risposta):
                self.risposta = risposta

            def complete_json(self, **kwargs):
                return self.risposta

        capitoli = [{"number": n, "title": f"Nuovo {n}"} for n in range(1, 5)]
        outline = self.outline()
        writer.apply_index(BookSpec(slug="t", title="T"), outline, Cliente({
            "chapters": capitoli,
            "parts": [{"first_chapter": 1, "title": "Dentro"}, {"first_chapter": 3, "title": "Fuori"}],
        }))
        self.assertEqual([p.title for p in outline.parts], ["Dentro", "Fuori"])
        self.assertEqual([p.first_chapter for p in outline.parts], [1, 3])

        outline = self.outline()
        writer.apply_index(BookSpec(slug="t", title="T"), outline, Cliente({
            "chapters": capitoli, "parts": [{"first_chapter": 1, "title": "Dentro"}],
        }))
        self.assertEqual([p.title for p in outline.parts], ["Prima parte", "Seconda parte"])


class TestVetrina(unittest.TestCase):
    def test_contiene_quello_che_vede_il_cliente_e_niente_altro(self):
        spec = BookSpec(slug="v", title="Il Titolo", subtitle="Il sottotitolo", language="it",
                        keywords=["parola segreta"], notes="nota d'autore riservata")
        outline = Outline(
            title="Il Titolo",
            chapters=[ChapterPlan(number=1, title="Uno"), ChapterPlan(number=2, title="Due")],
            parts=[PartPlan("La parte", 1)],
        )
        meta = {"description_paragraphs": ["La descrizione."], "bullets": ["un punto"],
                "keywords": ["parola segreta"]}
        testo = vetrina.testo(spec, outline, meta, cover_copy={"hook": "Ci riesci?"},
                              chapter_pages={"Uno": 9, "Due": 15},
                              part_pages={"Parte I — La parte": 7})
        for atteso in ("Il Titolo", "Il sottotitolo", "«Ci riesci?»", "La descrizione.",
                       "un punto", "**Parte I — La parte** · p. 7", "2. Due · p. 15"):
            self.assertIn(atteso, testo)
        self.assertNotIn("parola segreta", testo, "le parole chiave il cliente non le vede")
        self.assertNotIn("nota d'autore", testo)

    def test_il_build_la_scrive(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = BookProject(Path(tmp) / "v")
            project.ensure_dirs()
            spec = BookSpec(slug="v", title="T")
            outline = Outline(title="T", chapters=[ChapterPlan(number=1, title="Uno")])
            (project.build_dir / "metadata.json").write_text(
                json.dumps({"description_paragraphs": ["Descr."]}), encoding="utf-8"
            )
            path = vetrina.scrivi(project, spec, outline)
            self.assertEqual(path.name, "vetrina.md")
            self.assertIn("Descr.", path.read_text(encoding="utf-8"))


class TestRigheDelSommario(unittest.TestCase):
    def test_un_titolo_che_va_a_capo_si_misura(self):
        spec = BookSpec(slug="t", title="Titolo breve", language="en")
        lungo = "Your First Session: What to Bring, What to Ask, What Nobody Can Promise"
        outline = Outline(title="Titolo breve", chapters=[
            ChapterPlan(number=1, title="A Short Title"), ChapterPlan(number=2, title=lungo)])
        rilievi = [r for r in esamina(outline, spec) if r.category == "titolo su due righe"]
        self.assertEqual([r.chapter for r in rilievi], [2])


class TestBriefSenzaContraddizioni(unittest.TestCase):
    def test_chiede_solo_l_illustrazione_della_prima(self):
        testo = " ".join(coverbrief.brief(BookSpec(slug="b", title="B"), pages=140).split())
        self.assertIn("ONE image: the FRONT illustration only", testo)
        self.assertIn("What the engine then sends to KDP", testo)
        self.assertIn("There is no text, letter or number anywhere in the image", testo)


class TestLineeGuida(unittest.TestCase):
    """Il documento e la tabella non devono separarsi: un agente nuovo senza
    riga nelle linee guida è un agente che nessuno sa quando chiamare."""

    def test_la_tabella_nomina_ogni_responsabile(self):
        testo = (Path(__file__).resolve().parent.parent / "docs" / "linee-guida.md").read_text(
            encoding="utf-8"
        )
        tabella = testo.split("## Chi fa che cosa")[1].split("## Le fasi")[0]
        for nome in sorted({c.agente for c in COMPETENZE}):
            with self.subTest(agente=nome):
                self.assertIn(f"`{nome}`", tabella)


class TestPannello(unittest.TestCase):
    def test_la_conformita_sta_anche_fra_i_revisori_del_libro(self):
        self.assertIn("conformita", agents.panel.BOOK_REVIEWERS)
        self.assertIn("conformita", agents.panel.CHAPTER_REVIEWERS)


if __name__ == "__main__":
    unittest.main()

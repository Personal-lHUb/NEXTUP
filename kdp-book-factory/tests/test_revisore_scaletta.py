"""Test del revisore di scaletta.

Il punto di questi test non è che l'agente giri: è che **segnali davvero**.
Un controllo che non scatta mai su una scaletta rotta è decorazione, e una
decorazione in mezzo a un collaudo è peggio di niente, perché fa credere che
qualcuno abbia guardato. Ogni controllo qui ha la sua scaletta rotta.

L'altra metà dei test difende il confine opposto: le scaletta scritte bene non
devono essere bloccate. Un revisore che grida su un capitolo intitolato
«Perché non la chiamo una prova» costringe l'autore a peggiorare il libro per
far tacere il controllo.
"""

import copy
import unittest

from kdpfactory.agents import scaletta as revisore
from kdpfactory.models import BookSpec, Outline

BRIEF = """# Che cosa copre il libro

## Argomenti da coprire

- What a regression session is, minute by minute: induction, the questions,
  the person's own words, the return.
- How to choose a practitioner, and the questions that separate a serious one
  from a performer.

## What must NOT be in it

- Promises: healing, cure, guaranteed outcomes.
"""


def capitolo(numero: int, titolo: str, riassunto: str, beats: list[str]) -> dict:
    return {"number": numero, "title": titolo, "summary": riassunto,
            "beats": beats, "role": "chapter"}


BUONA = {
    "title": "What They Remembered",
    "subtitle": "Past-Life Sessions, Honestly Told",
    "thesis": "Testimony is not history, and the difference is the book.",
    "back_cover": (
        "She described the staircase before I asked about the house.\n\n"
        + "I have sat with people in that chair for years and this book reports what they "
          "said, at length, in their own words, with the pauses left in where they fell.\n\n"
        + "What I will not do is dress a session up as something it is not. A regression is "
          "testimony, and you will finish this book able to tell the two apart anywhere."
    ),
    "chapters": [
        capitolo(1, "The Induction, Minute by Minute",
                 "A complete walk through the induction for a reader who has never had a "
                 "session: what is said, what the body does, how long each stage takes.",
                 ["The chair, the breathing, the script and why it is boring on purpose",
                  "Deepening, and the signs that tell me it is working",
                  "What being under actually means: awake, aware, able to stop",
                  "The people it does not work on, and how quickly I can tell"]),
        capitolo(2, "How to Tell a Serious Practitioner From a Performer",
                 "The questions to ask before booking, the answers that should reassure "
                 "you, and the ones that should end the conversation straight away.",
                 ["Questions to ask on the phone, with the answers a serious one gives",
                  "The answers that should end the call, including the impressive one",
                  "Price, length, recording, consent: what is normal and what is a warning",
                  "What a good practitioner refuses to promise, and why that reassures"]),
    ],
}


def spec_demo(**extra) -> BookSpec:
    dati = dict(slug="prova", title="What They Remembered",
                subtitle="Past-Life Sessions, Honestly Told", language="en", brief=BRIEF)
    dati.update(extra)
    return BookSpec(**dati)


def esamina(dati: dict, *, attesi: int = 0, spec: BookSpec | None = None):
    return revisore.esamina(
        Outline.from_dict(dati), spec or spec_demo(), brief=BRIEF, capitoli_attesi=attesi
    )


def gravita(rilievi, severita: str) -> list:
    return [r for r in rilievi if r.severity == severita]


def categorie(rilievi) -> set[str]:
    return {r.category for r in rilievi}


class TestScalettaBuona(unittest.TestCase):
    """Il confine che si dimentica sempre: non bloccare il lavoro fatto bene."""

    def test_una_scaletta_sana_non_ha_bloccanti(self):
        rilievi = esamina(BUONA, attesi=2)
        self.assertEqual(gravita(rilievi, "bloccante"), [], [r.issue for r in rilievi])

    def test_una_parola_vietata_fra_virgolette_e_una_citazione(self):
        """«Le parole che mi rifiuto di usare: "confermato"» non è una rivendicazione.

        È la distinzione fra usare una parola e nominarla. Senza, il revisore
        bloccherebbe proprio il capitolo che insegna a non usarla.
        """
        dati = copy.deepcopy(BUONA)
        dati["chapters"][0]["beats"].append(
            "The words I refuse: 'proved', 'confirmed', 'verified' — what each one asserts"
        )
        self.assertNotIn("linguaggio da prova", categorie(esamina(dati)))

    def test_una_negazione_vicina_salva_la_frase(self):
        dati = copy.deepcopy(BUONA)
        dati["chapters"][0]["beats"].append("Why I will never call a session proof of anything")
        self.assertNotIn("linguaggio da prova", categorie(esamina(dati)))


class TestControlliChePescano(unittest.TestCase):
    """Un controllo che non scatta mai non è un controllo."""

    def test_un_argomento_del_brief_senza_capitolo_blocca(self):
        dati = copy.deepcopy(BUONA)
        dati["chapters"] = [dati["chapters"][0]]        # via la scelta del praticante
        rilievi = gravita(esamina(dati), "bloccante")
        self.assertIn("argomento scoperto", categorie(rilievi))
        self.assertIn("practitioner", rilievi[0].issue)

    def test_due_capitoli_gemelli_bloccano(self):
        dati = copy.deepcopy(BUONA)
        clone = copy.deepcopy(dati["chapters"][0])
        clone["number"] = 3
        clone["title"] = "The Induction, Step by Step"
        dati["chapters"].append(clone)
        rilievi = gravita(esamina(dati), "bloccante")
        self.assertIn("sovrapposizione", categorie(rilievi))

    def test_una_promessa_di_guarigione_blocca(self):
        dati = copy.deepcopy(BUONA)
        dati["chapters"][1]["beats"].append("How this work heals grief for good, guaranteed")
        rilievi = gravita(esamina(dati), "bloccante")
        self.assertIn("promessa di risultato", categorie(rilievi))

    def test_il_conteggio_sbagliato_blocca(self):
        rilievi = gravita(esamina(BUONA, attesi=30), "bloccante")
        self.assertIn("conteggio", categorie(rilievi))
        self.assertIn("28", rilievi[0].suggestion)

    def test_la_lingua_sbagliata_blocca(self):
        dati = copy.deepcopy(BUONA)
        for c in dati["chapters"]:
            c["summary"] = (
                "Questo capitolo spiega che cosa succede nella seduta e perche sta qui, "
                "con le parole di chi c'era e non con le mie che non servono a nessuno."
            )
            c["beats"] = ["il primo punto della seduta che il lettore deve avere",
                          "il secondo punto, quello che nessuno racconta mai nei libri"]
        self.assertIn("lingua sbagliata", categorie(gravita(esamina(dati), "bloccante")))

    def test_due_titoli_uguali_bloccano(self):
        dati = copy.deepcopy(BUONA)
        dati["chapters"][1]["title"] = dati["chapters"][0]["title"]
        self.assertIn("titolo doppio", categorie(gravita(esamina(dati), "bloccante")))

    def test_un_titolo_segnaposto_si_dice(self):
        dati = copy.deepcopy(BUONA)
        dati["chapters"][0]["title"] = "Introduction to the Method"
        self.assertIn("titolo generico", categorie(gravita(esamina(dati), "importante")))

    def test_una_data_in_scaletta_si_dice(self):
        dati = copy.deepcopy(BUONA)
        dati["chapters"][0]["beats"].append("The trench in 1916, established from the record")
        rilievi = gravita(esamina(dati), "importante")
        self.assertIn("data in scaletta", categorie(rilievi))

    def test_un_capitolo_senza_punti_si_dice(self):
        dati = copy.deepcopy(BUONA)
        dati["chapters"][0]["beats"] = ["uno solo"]
        self.assertIn("capitolo senza punti", categorie(gravita(esamina(dati), "importante")))

    def test_un_capitolo_senza_riassunto_si_dice(self):
        dati = copy.deepcopy(BUONA)
        dati["chapters"][0]["summary"] = "Boh."
        self.assertIn("capitolo senza programma", categorie(gravita(esamina(dati), "importante")))

    def test_la_quarta_mancante_si_dice(self):
        dati = copy.deepcopy(BUONA)
        dati["back_cover"] = ""
        self.assertIn("quarta mancante", categorie(esamina(dati)))

    def test_un_titolo_illeggibile_in_miniatura_si_dice(self):
        dati = copy.deepcopy(BUONA)
        dati["title"] = "An Extraordinarily Circumlocutory Disquisition Concerning Remembrance"
        self.assertTrue(
            {"titolo in copertina", "titolo troppo lungo"} & categorie(esamina(dati)),
            "un titolo che non entra in copertina deve essere detto qui, non a libro stampato",
        )


class TestQuantitaDichiarate(unittest.TestCase):
    """Ogni cifra stampata dev'essere un numero contato sul libro (CLAUDE.md)."""

    def test_le_cifre_dell_indice_finiscono_nell_elenco_da_verificare(self):
        dati = copy.deepcopy(BUONA)
        dati["chapters"][0]["title"] = "Eight Sessions, One Threshold"
        quantita = revisore.quantita_dichiarate(Outline.from_dict(dati))
        trovate = {numero for _, numero in quantita}
        self.assertIn("eight (8)", trovate)
        self.assertIn("one (1)", trovate)

    def test_una_scaletta_senza_cifre_non_produce_l_elenco(self):
        dati = copy.deepcopy(BUONA)
        dati["back_cover"] = "Un gancio.\n\nUn paragrafo che non conta niente.\n\nE un altro."
        self.assertEqual(revisore.quantita_dichiarate(Outline.from_dict(dati)), [])


class TestLetturaDelBrief(unittest.TestCase):
    def test_i_divieti_del_brief_non_diventano_argomenti_da_coprire(self):
        argomenti = revisore.argomenti_del_brief(BRIEF)
        self.assertEqual(len(argomenti), 2)
        self.assertFalse(any("Promises" in a for a in argomenti))

    def test_un_brief_vuoto_non_inventa_argomenti(self):
        self.assertEqual(revisore.argomenti_del_brief(""), [])
        rilievi = revisore.esamina(Outline.from_dict(BUONA), spec_demo(brief=""), brief="")
        self.assertNotIn("argomento scoperto", categorie(rilievi))


class TestNessunaChiamataAlModello(unittest.TestCase):
    def test_il_modulo_non_usa_il_client(self):
        from pathlib import Path
        sorgente = Path(revisore.__file__).read_text(encoding="utf-8")
        for vietato in ("LLMClient", "complete_json", "client."):
            self.assertNotIn(vietato, sorgente, f"`{vietato}` in {revisore.__file__}")

    def test_l_agente_e_registrato_e_gira_senza_client(self):
        from kdpfactory.agents import REGISTRY, AgentContext
        agente = REGISTRY[revisore.NOME]
        ctx = AgentContext(spec=spec_demo(), outline=Outline.from_dict(BUONA), text=BRIEF)
        esito = agente.run(ctx, client=None)
        self.assertEqual(esito.agent, revisore.NOME)
        self.assertTrue(esito.notes)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

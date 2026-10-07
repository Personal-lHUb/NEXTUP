"""Le regole dei due video nel motore di copertina, e le tre direzioni d'arte.

Nessun test fa chiamate di rete: le immagini sono sintetiche, Higgsfield e
Cowork non si chiamano.
"""

from __future__ import annotations

import copy as _copy
import dataclasses
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image, ImageDraw

from kdpfactory import (
    backup,
    cover,
    coverbrief,
    coverdesign,
    coverimage,
    direzioni,
    higgsfield,
    kdpspecs,
    produzione,
)
from kdpfactory.agents.base import AgentContext
from kdpfactory.agents.copertina import _severity, inspect_cover
from kdpfactory.models import BookProject, BookSpec

INCH = kdpspecs.INCH


def libro(**campi) -> BookSpec:
    base = dict(
        slug="bills", title="Bills in Order", subtitle="A Household Guide to Paying on Time",
        author="Claire Halvorsen", language="en", topic="household bills",
        categories=["Books > Business & Money > Personal Finance > Budgeting & Money Management"],
        audience="The adult who handles the bills.", promise="A way of handling bills.",
    )
    base.update(campi)
    return BookSpec(**base)


def direzione(**campi) -> dict:
    base = {
        "nome": "La busta in luce",
        "idea": "Una busta sola, sotto una lampada: la sera in cui si mettono in ordine i conti.",
        "perche": "Il lettore riconosce il suo tavolo di casa, non un ufficio.",
        "distacco": "Il concorrente è chiaro e pieno di righe: questa è scura e vuota.",
        "soggetto": "a single sealed paper envelope on a dark kitchen table",
        "elementi": ["a sealed paper envelope", "a pool of warm lamp light"],
        "tecnica": "editorial gouache illustration with soft edges",
        "luce": "one warm lamp from above",
        "emozione": "calm relief",
        "composizione": "alto",
        "palette": "notturno",
        "tipografia": "deciso",
    }
    base.update(campi)
    return base


def tre_direzioni() -> dict:
    return {
        "libro": "bills",
        "codici_del_genere": "Fondi chiari, foto di scrivanie, titoli condensati in alto.",
        "fonti": ["concorrente/cowork-copertine-categoria-risposta.md"],
        "direzioni": [
            direzione(),
            direzione(nome="Il calendario", soggetto="a wall calendar with blank squares",
                      elementi=["a blank wall calendar"], tecnica="flat screen-print poster",
                      composizione="centro", palette="inchiostro"),
            direzione(nome="Le chiavi di casa", soggetto="a ring of house keys on a hook",
                      elementi=["a ring of house keys"], tecnica="cut-paper illustration",
                      palette="terracotta", tipografia="elegante"),
        ],
        "scelta": None,
    }


class TestRegoleDeiVideoNelMotore(unittest.TestCase):
    def setUp(self):
        backup.configure(enabled=False)
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()
        backup.configure(enabled=True)

    def costruisci(self, spec: BookSpec, immagine: Path | None = None, nome: str = "c") -> dict:
        return cover.build_cover(spec, 192, self.dir / f"{nome}.pdf", genre="non-fiction",
                                 image_path=immagine)

    def immagine(self, chiara: bool = False) -> Path:
        file = self.dir / ("chiara.png" if chiara else "scura.png")
        fondo = (225, 225, 220) if chiara else (14, 19, 32)
        img = Image.new("RGB", (1838, 2775), fondo)
        ImageDraw.Draw(img).rectangle((520, 1500, 1320, 2050), fill=(235, 225, 200))
        img.save(file)
        return file

    def test_nessuna_preposizione_appesa_a_fine_riga(self):
        """«BILLS IN / ORDER» lascia la preposizione appesa (video A, 24:27)."""
        info = self.costruisci(libro())
        self.assertEqual(coverdesign.weak_endings(info["titolo_righe"]), 0)
        self.assertEqual(info["titolo_righe"][-1], "IN ORDER")

    def test_il_testo_sta_a_un_centimetro_dal_taglio(self):
        for titolo in ("Bills in Order", "Meditazione per principianti", "Tre Ore"):
            with self.subTest(titolo=titolo):
                verifica = self.costruisci(libro(title=titolo))["verifica"]
                self.assertTrue(verifica["testo_a_1_cm_dal_taglio"], verifica["problemi"])

    def test_due_famiglie_di_caratteri_al_massimo(self):
        """Anche quando il titolo va nel condensato, il gancio passa al bastone."""
        for titolo in ("Bills in Order", "Remembered"):
            with self.subTest(titolo=titolo):
                verifica = self.costruisci(libro(title=titolo))["verifica"]
                self.assertLessEqual(len(verifica["famiglie_di_caratteri"]), 2)

    def test_l_audit_conta_le_famiglie_che_trova(self):
        from reportlab.pdfgen import canvas as pdfcanvas

        from kdpfactory.typography import register_condensed_display, register_family

        spec = libro()
        w, h = kdpspecs.cover_size_in(spec.trim, 192, spec.paper)
        front_x0 = (kdpspecs.BLEED_IN + 6 + kdpspecs.spine_width_in(192, spec.paper)) * INCH
        pdf = self.dir / "tre.pdf"
        c = pdfcanvas.Canvas(str(pdf), pagesize=(w * INCH, h * INCH))
        for i, font in enumerate((register_family("sans"), register_family("serif"),
                                  register_condensed_display())):
            c.setFont(font, 40 if i == 0 else 14)
            c.drawString(front_x0 + 60, h * INCH - 150 - i * 60, "BILLS IN ORDER" if i == 0 else "riga")
        c.save()
        verdetto = coverdesign.audit(pdf, trim=spec.trim, pages=192, paper=spec.paper,
                                     palette=coverdesign.PALETTES[0], title=spec.title)
        self.assertEqual(len(verdetto.font_families), 3)
        problema = next(p for p in verdetto.problems if "famiglie di caratteri" in p)
        self.assertEqual(_severity(problema), "importante")

    def test_il_contorno_non_raddoppia_le_righe_del_titolo(self):
        """Sull'immagine il titolo si disegna due volte (contorno e pieno): si conta una."""
        info = self.costruisci(libro(), self.immagine())
        self.assertEqual(info["verifica"]["titolo_righe"], len(info["titolo_righe"]))
        self.assertEqual(info["verifica"]["problemi"], [])

    def test_titolo_al_centro(self):
        spec = libro(cover_layout="centro")
        info = self.costruisci(spec, self.immagine())
        self.assertEqual(info["composizione"], "centro")
        self.assertEqual(info["verifica"]["problemi"], [])
        prompt = coverbrief.prompt_da_incollare(spec, pages=192)
        self.assertIn("calm, plain area in the middle", prompt)
        self.assertIn("turned towards the centre", prompt)

    def test_su_un_immagine_chiara_la_velatura_cresce_fino_al_contrasto(self):
        info = self.costruisci(libro(), self.immagine(chiara=True))
        rapporto = info["immagine"]
        self.assertGreater(rapporto["title_scrim"], 0)
        self.assertGreaterEqual(rapporto["title_contrast"], coverdesign.MIN_CONTRAST_ON_IMAGE)

    def test_il_contrasto_si_misura_sulla_fascia_peggiore(self):
        """Una macchia chiara sotto una sola riga basta a bocciare la zona."""
        img = Image.new("RGB", (400, 400), (10, 10, 10))
        ImageDraw.Draw(img).rectangle((0, 350, 400, 400), fill=(250, 250, 250))
        self.assertLess(coverimage.zone_contrast(img, (0, 0, 1, 1)), 2)
        self.assertGreater(coverimage.zone_contrast(img, (0, 0, 1, 0.8)), 10)

    def test_sfondo_rumoroso_e_dominante_senape(self):
        righe = Image.new("RGB", (400, 400), (20, 20, 40))
        disegno = ImageDraw.Draw(righe)
        for y in range(0, 400, 6):
            disegno.rectangle((0, y, 400, y + 2), fill=(230, 230, 230))
        self.assertGreater(coverimage.zone_noise(righe, (0, 0, 1, 1)), coverimage.MAX_ZONE_NOISE)
        piatta = Image.new("RGB", (400, 400), (20, 20, 40))
        self.assertLess(coverimage.zone_noise(piatta, (0, 0, 1, 1)), 0.01)
        senape = Image.new("RGB", (400, 600), (200, 165, 60))
        self.assertGreater(coverimage.mustard_share(senape), coverimage.MAX_MUSTARD)
        accento = Image.new("RGB", (400, 600), (245, 179, 1))   # il giallo pieno della palette
        self.assertLess(coverimage.mustard_share(accento), 0.05)

    def test_l_agente_vede_i_problemi_dell_immagine(self):
        spec = libro()
        info = self.costruisci(spec, self.immagine())
        rapporto = dict(info["immagine"], title_noise=0.2, mustard=0.6)
        ctx = AgentContext(spec=spec, pages=192, cover_pdf=Path(info["cover_pdf"]),
                           cover_copy=info["testi"], cover_image=rapporto)
        problemi = {f.issue: f.severity for f in inspect_cover(ctx)}
        self.assertTrue(any("rumoroso" in p and s == "importante" for p, s in problemi.items()))
        self.assertTrue(any("giallo-senape" in p for p in problemi))

    def test_la_voce_tipografica_segue_il_genere(self):
        self.assertEqual(coverbrief.tipografia(libro()), "deciso")
        spirito = libro(title="Trust Your Gut", categories=["Books > Religion & Spirituality > New Age"])
        self.assertEqual(coverbrief.tipografia(spirito), "elegante")
        self.assertEqual(coverbrief.tipografia(dataclasses.replace(spirito, cover_type="deciso")),
                         "deciso")
        info = self.costruisci(spirito)
        self.assertEqual(info["tipografia"], "elegante")
        self.assertIn("EBGaramond", info["verifica"]["famiglie_di_caratteri"])

    def test_book_json_rifiuta_composizioni_sconosciute(self):
        self.assertTrue(libro(cover_layout="basso").validate())
        self.assertTrue(libro(cover_type="corsivo").validate())
        self.assertFalse(libro(cover_layout="centro", cover_type="elegante").validate())


class TestPromptDeiVideo(unittest.TestCase):
    def test_il_concorrente_si_batte_dentro_il_genere(self):
        prompt = coverbrief.prompt_da_incollare(libro(), pages=192, concorrente="Pale cover, a desk.")
        self.assertIn("Keep the conventions of the genre", prompt)
        self.assertIn("different dominant colour", prompt)
        self.assertNotIn("different kind of image", prompt)

    def test_niente_dominante_ne_elementi_difettosi(self):
        prompt = coverbrief.prompt_da_incollare(libro(), pages=192)
        self.assertIn("no overall yellow, mustard or sepia cast", prompt)
        self.assertIn("No deformed or half-formed objects", prompt)
        self.assertIn("same style", prompt)


class TestTreDirezioni(unittest.TestCase):
    def setUp(self):
        backup.configure(enabled=False)
        self.tmp = tempfile.TemporaryDirectory()
        self.project = BookProject(Path(self.tmp.name) / "books" / "bills")
        self.project.root.mkdir(parents=True)
        self.memoria = Path(self.tmp.name) / "copertine-direzione.json"

    def tearDown(self):
        self.tmp.cleanup()
        backup.configure(enabled=True)

    def scrivi(self, dati: dict) -> None:
        direzioni.percorso(self.project).write_text(json.dumps(dati), encoding="utf-8")

    def test_il_modello_vuoto_non_passa(self):
        dati = direzioni.modello(libro())
        self.assertEqual(len(dati["direzioni"]), 3)
        self.assertTrue(direzioni.problemi(dati))
        self.scrivi(dati)
        self.assertEqual(direzioni.stato(self.project), "da-compilare")

    def test_tre_direzioni_complete_passano(self):
        self.assertEqual(direzioni.problemi(tre_direzioni()), [])

    def test_quello_che_le_direzioni_non_possono_chiedere(self):
        casi = {
            "elementi": dict(elementi=["a", "b", "c", "d"]),
            "testo all'immagine": dict(soggetto="an envelope with the title written on it"),
            "imitare": dict(tecnica="in the style of a famous painter"),
            "palette": dict(palette="arcobaleno"),
            "composizione": dict(composizione="basso"),
        }
        for attesa, campi in casi.items():
            with self.subTest(attesa=attesa):
                dati = tre_direzioni()
                dati["direzioni"][0].update(campi)
                self.assertTrue(any(attesa in p for p in direzioni.problemi(dati)),
                                direzioni.problemi(dati))

    def test_tre_varianti_della_stessa_idea_non_sono_una_scelta(self):
        dati = tre_direzioni()
        dati["direzioni"][1] = _copy.deepcopy(dati["direzioni"][0])
        self.assertTrue(any("si somigliano" in p for p in direzioni.problemi(dati)))

    def test_mancano_i_codici_del_genere(self):
        dati = tre_direzioni()
        dati["codici_del_genere"] = ""
        self.assertTrue(any("codici del genere" in p for p in direzioni.problemi(dati)))

    def test_il_prompt_nasce_dalla_direzione(self):
        spec = libro()
        d = tre_direzioni()["direzioni"][1]
        prompt = direzioni.prompt_bozzetto(spec, d, pages=192)
        self.assertIn("Show a wall calendar with blank squares.", prompt)
        self.assertIn("Rendering: flat screen-print poster.", prompt)
        self.assertIn("middle of the image", prompt)          # composizione al centro
        inchiostro = next(p for p in coverdesign.PALETTES if p.name == "inchiostro")
        self.assertIn(inchiostro.accent.upper().lstrip("#"), prompt)
        self.assertIn("Absolutely no text", prompt)
        # il bozzetto è la variante finale a bassa risoluzione: lo stesso prompt
        self.assertEqual(prompt, coverbrief.prompt_da_incollare(
            spec, pages=192, per_chat=False, variante=1, direzione=d))

    def test_bozzetti_e_scelta(self):
        self.scrivi(tre_direzioni())
        self.assertEqual(direzioni.stato(self.project), "senza-bozzetti")
        prompt_file, riepilogo = direzioni.scrivi_bozzetti(self.project, libro(), tre_direzioni(),
                                                            pages=192)
        self.assertEqual(len(json.loads(prompt_file.read_text(encoding="utf-8"))), 3)
        self.assertIn("## 2. Il calendario", riepilogo.read_text(encoding="utf-8"))
        direzioni.registra_bozzetti(self.project, [
            {"direzione": n, "url": f"https://cdn.example/{n}.png"} for n in (1, 2, 3)])
        self.assertEqual(direzioni.stato(self.project), "da-scegliere")

        scelta = direzioni.scegli(self.project, 2, "più pulita", quando="2026-10-07",
                                  memoria=self.memoria)
        self.assertEqual(scelta["nome"], "Il calendario")
        self.assertEqual(direzioni.stato(self.project), "scelta")
        storia = json.loads(self.memoria.read_text(encoding="utf-8"))["direzioni_scelte"]
        self.assertEqual(storia[0]["scelta"]["composizione"], "centro")
        self.assertEqual(storia[0]["scartate"], ["La busta in luce", "Le chiavi di casa"])

    def test_produzione_aspetta_l_autore_e_non_il_silenzio(self):
        self.scrivi(tre_direzioni())
        direzioni.registra_bozzetti(self.project, [
            {"direzione": n, "url": f"https://cdn.example/{n}.png"} for n in (1, 2, 3)])
        testo, aspetta, autore = produzione._passo_direzioni(self.project, "bills")
        self.assertIn("direzione scelta dall'autore", testo)
        self.assertIn("non passa dal silenzio-assenso", autore)

    def test_produzione_chiede_prima_lo_studio_della_categoria(self):
        testo, _ = produzione._passo_direzioni(self.project, "bills")
        self.assertIn("--direzioni", testo)
        direzioni.studio_path(self.project).parent.mkdir(parents=True)
        direzioni.studio_path(self.project).write_text("richiesta", encoding="utf-8")
        testo, aspetta = produzione._passo_direzioni(self.project, "bills")
        self.assertEqual(aspetta, (direzioni.STUDIO,))

    def test_la_richiesta_dello_studio(self):
        nome, testo = direzioni.richiesta_studio("bills", "amazon.com", "Books > Budgeting",
                                                 {"canale": "github"})
        self.assertEqual(nome, "cowork-copertine-categoria.md")
        self.assertIn("Ruolo: concorrente", testo)
        self.assertIn("Niente screenshot", testo)
        self.assertIn("della categoria «Books > Budgeting»", testo)


class TestBozzettiAPocoPrezzo(unittest.TestCase):
    def test_il_bozzetto_chiede_la_risoluzione_piu_bassa(self):
        schema = {"properties": {"resolution": {"enum": ["1k", "2k", "4k"]},
                                 "quality": {"enum": ["medium", "high", "max"]}}}
        with mock.patch.object(higgsfield, "_valori",
                               side_effect=lambda s, nome: s["properties"].get(nome, {}).get("enum", [])):
            finale = higgsfield.parametri(schema, "2:3")
            bozza = higgsfield.parametri(schema, "2:3", bozza=True)
        self.assertEqual(finale[finale.index("--resolution") + 1], "4k")
        self.assertEqual(bozza[bozza.index("--resolution") + 1], "1k")
        self.assertEqual(bozza[bozza.index("--quality") + 1], "medium")


if __name__ == "__main__":
    unittest.main()

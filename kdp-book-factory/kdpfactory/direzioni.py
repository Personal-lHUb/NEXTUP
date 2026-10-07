"""Le tre direzioni d'arte di una copertina: si ragiona da casa editrice, si sceglie da autore.

Un editore non chiede «una copertina»: guarda che cosa vende nella categoria,
decide da che cosa il libro si deve distinguere e commissiona più concetti, che
mette a confronto prima di spendere sulla versione finale. È anche quello che
chiede il video A (36:46: «mostrate due tre versioni diverse della copertina»).
Questo modulo fa quel percorso con gli attrezzi della fabbrica:

1. **lo studio della categoria** — le copertine che vendono, descritte da Cowork
   (`concorrente/cowork-copertine-categoria.md`): colori, tipo d'immagine,
   posizione e carattere del titolo, quello che hanno in comune;
2. **tre direzioni** — le scrive l'agente `copertina`, ragionando da direttore
   artistico e da illustratore, in `books/<slug>/copertina-direzioni.json`:
   idea, soggetto, al massimo tre elementi, resa, luce, palette del motore,
   composizione, voce tipografica, e perché venderebbe;
3. **un bozzetto per direzione** — il prompt lo scrive il sistema da quei dati
   (`coverbrief.prompt_da_incollare(direzione=…)`, la regola di CLAUDE.md), e
   si genera a bassa risoluzione;
4. **la scelta dell'autore** — non passa dal silenzio-assenso: è la direzione
   del libro, e la vede lui. La direzione scelta scrive in `book.json` palette,
   composizione e carattere, e da lì in poi le varianti finali, alla
   risoluzione più alta, nascono da lei.

Le scelte restano anche in `config/copertine-direzione.json`, che vale per
tutta la fabbrica: l'agente le legge prima di proporre le direzioni del libro
dopo. È così che il sistema impara il gusto dell'autore.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from . import avvio, coverbrief, coverdesign, cowork
from .models import BookSpec

#: dove l'agente scrive le tre direzioni, nella cartella del libro
FILE = "copertina-direzioni.json"
#: i prompt dei bozzetti, uno per direzione, scritti dal sistema
PROMPT_BOZZETTI = "copertina-bozzetti-prompt.json"
#: la traccia dei bozzetti generati (modello, pixel, crediti, indirizzo)
BOZZETTI = "copertina-bozzetti.json"
#: il riepilogo per l'autore: le tre direzioni da guardare accanto ai bozzetti
RIEPILOGO = "copertina-direzioni.md"
#: lo studio delle copertine che vendono nella categoria, chiesto a Cowork
STUDIO = "cowork-copertine-categoria.md"

QUANTE = 3
#: dove sta il titolo, detto all'autore
POSTO = {"alto": "in alto, l'immagine sotto", "centro": "al centro, i soggetti intorno"}
#: i campi che finiscono nel prompt, in inglese come il prompt
CAMPI_PROMPT = ("soggetto", "tecnica", "luce", "emozione")
#: i campi che legge l'autore, in italiano
CAMPI_AUTORE = ("nome", "idea", "perche", "distacco")
OBBLIGATORI = ("nome", "idea", "soggetto", "elementi", "composizione", "tecnica", "palette",
               "perche", "distacco")

#: un prompt di copertina non chiede mai testo: lo compone il motore
_TESTO = re.compile(
    r"\b(text|title|titles|lettering|letters|words|typography|typeface|font|logo|caption|"
    r"author name|signature|watermark)\b", re.I,
)
#: né l'imitazione di qualcuno: una copertina che somiglia a un'altra KDP la toglie
_IMITAZIONE = re.compile(r"\b(in the style of|style of [A-Z]|à la|inspired by|like the cover)\b", re.I)


def percorso(project) -> Path:
    return project.root / FILE


def studio_path(project) -> Path:
    return project.root / "concorrente" / STUDIO


def risposta_studio(project) -> Path:
    return project.root / "concorrente" / STUDIO.replace(".md", "-risposta.md")


def leggi(project) -> dict | None:
    try:
        return json.loads(percorso(project).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def modello(spec: BookSpec) -> dict:
    """Il file da compilare: le istruzioni per l'agente e tre direzioni vuote."""
    vuota = {
        "nome": "", "idea": "", "perche": "", "distacco": "",
        "soggetto": "", "elementi": [], "tecnica": "", "luce": "", "emozione": "",
        "composizione": "alto", "palette": "", "tipografia": "",
    }
    return {
        "_nota": (
            "Tre direzioni d'arte per la copertina, diverse fra loro, scritte dall'agente "
            "`copertina` come le scriverebbe il direttore artistico di un editore. In italiano "
            "per l'autore: nome, idea, perche, distacco, codici_del_genere. In inglese, perché "
            "entrano nel prompt: soggetto, elementi (da 1 a 3), tecnica, luce, emozione. "
            f"composizione: {' | '.join(coverdesign.LAYOUTS)}. palette: una del motore "
            f"({', '.join(p.name for p in coverdesign.PALETTES)}). tipografia: "
            f"{' | '.join(coverdesign.TIPOGRAFIE)} (vuota = la decide la categoria). "
            "Niente testo nell'immagine, niente nomi o stili altrui. Il prompt lo scrive "
            "`kdpfactory copertina <slug> --direzioni`."
        ),
        "libro": spec.slug,
        "codici_del_genere": "",
        "fonti": [],
        "direzioni": [dict(vuota) for _ in range(QUANTE)],
        "scelta": None,
    }


def _normale(testo: str) -> str:
    return " ".join(re.findall(r"[a-z]+", (testo or "").lower()))


def problemi(dati: dict | None) -> list[str]:
    """Che cosa impedisce a queste direzioni di diventare bozzetti. Solo conti.

    Tre, complete, ognuna con al massimo tre elementi (video A, 4:01: «un
    elemento visivo forte… tutto il resto è superfluo»), con una composizione e
    una palette che il motore sa comporre, senza testo né imitazioni, e
    diverse fra loro: tre varianti della stessa idea non sono una scelta.
    """
    if not dati:
        return [f"Manca {FILE}: le tre direzioni le scrive l'agente `copertina`."]
    out: list[str] = []
    if not str(dati.get("codici_del_genere", "")).strip():
        out.append("Mancano i codici del genere: che cosa hanno in comune le copertine che "
                   "vendono nella categoria (lo studio di Cowork, o la pagina del concorrente).")
    direzioni = dati.get("direzioni") or []
    if len(direzioni) != QUANTE:
        out.append(f"Le direzioni sono {len(direzioni)}: ne servono {QUANTE}.")
    palette = {p.name for p in coverdesign.PALETTES}
    for numero, d in enumerate(direzioni, 1):
        manca = [k for k in OBBLIGATORI if not d.get(k)]
        if manca:
            out.append(f"Direzione {numero}: manca {', '.join(manca)}.")
        elementi = d.get("elementi") or []
        if not isinstance(elementi, list) or len(elementi) > 3:
            out.append(f"Direzione {numero}: gli elementi sono {len(elementi)}, al massimo 3 "
                       "(un elemento forte, il resto è superfluo).")
        if d.get("composizione") and d["composizione"] not in coverdesign.LAYOUTS:
            out.append(f"Direzione {numero}: composizione «{d['composizione']}», ammesse "
                       f"{', '.join(coverdesign.LAYOUTS)}.")
        if d.get("palette") and d["palette"] not in palette:
            out.append(f"Direzione {numero}: palette «{d['palette']}» sconosciuta al motore "
                       f"({', '.join(sorted(palette))}).")
        if d.get("tipografia") and d["tipografia"] not in coverdesign.TIPOGRAFIE:
            out.append(f"Direzione {numero}: tipografia «{d['tipografia']}», ammesse "
                       f"{', '.join(coverdesign.TIPOGRAFIE)}.")
        prompt = " ".join([*(str(d.get(k, "")) for k in CAMPI_PROMPT), *map(str, elementi)])
        if _TESTO.search(prompt):
            out.append(f"Direzione {numero}: chiede del testo all'immagine "
                       f"(«{_TESTO.search(prompt).group(0)}»): il testo lo compone il motore.")
        if _IMITAZIONE.search(prompt):
            out.append(f"Direzione {numero}: chiede di imitare qualcuno "
                       f"(«{_IMITAZIONE.search(prompt).group(0)}»).")
    for a in range(len(direzioni)):
        for b in range(a + 1, len(direzioni)):
            da, db = direzioni[a], direzioni[b]
            diverse = sum(
                1 for chiave in ("soggetto", "tecnica")
                if _normale(da.get(chiave, "")) != _normale(db.get(chiave, ""))
            ) + sum(1 for chiave in ("composizione", "palette") if da.get(chiave) != db.get(chiave))
            if diverse < 2:
                out.append(f"Le direzioni {a + 1} e {b + 1} si somigliano troppo: cambiano in "
                           f"{diverse} su quattro fra soggetto, tecnica, composizione e palette.")
    return out


def scelta(dati: dict | None) -> tuple[int, dict] | None:
    """La direzione scelta dall'autore, col suo numero (da 1)."""
    if not dati or not dati.get("scelta"):
        return None
    numero = int(dati["scelta"].get("direzione") or 0)
    direzioni = dati.get("direzioni") or []
    if not 1 <= numero <= len(direzioni):
        return None
    return numero, direzioni[numero - 1]


def bozzetti(project) -> list[dict]:
    try:
        voci = json.loads((project.root / "build" / BOZZETTI).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [v for v in voci if isinstance(v, dict) and v.get("direzione")]


def stato(project) -> str:
    """A che punto sono le direzioni di questo libro.

    `nessuna` (non c'è il file), `da-compilare` (c'è il modello vuoto),
    `da-correggere` (ci sono problemi), `senza-bozzetti`, `da-scegliere`
    (bozzetti pronti, l'autore non ha scelto), `scelta`.
    """
    dati = leggi(project)
    if dati is None:
        return "nessuna"
    if not any(d.get("nome") for d in dati.get("direzioni") or []):
        return "da-compilare"
    if problemi(dati):
        return "da-correggere"
    if scelta(dati):
        return "scelta"
    fatti = {int(v["direzione"]) for v in bozzetti(project)}
    return "da-scegliere" if fatti >= set(range(1, QUANTE + 1)) else "senza-bozzetti"


def prompt_bozzetto(spec: BookSpec, direzione: dict, **kwargs) -> str:
    """Il prompt del bozzetto: lo stesso della variante finale, a bassa risoluzione.

    Il bozzetto serve a scegliere: deve mostrare quello che la versione finale
    sarà, non un'altra cosa. Per questo il prompt è quello delle varianti
    (`coverbrief.prompt_da_incollare`, modo generatore), costruito dai dati
    della direzione; cambia solo quanto si spende per generarlo.
    """
    return coverbrief.prompt_da_incollare(spec, per_chat=False, variante=1,
                                          direzione=direzione, **kwargs)


def scrivi_bozzetti(project, spec: BookSpec, dati: dict, **kwargs) -> tuple[Path, Path]:
    """I prompt dei tre bozzetti e il riepilogo per l'autore, in build/."""
    build = project.root / "build"
    build.mkdir(parents=True, exist_ok=True)
    voci = []
    righe = [
        f"# Le tre direzioni di copertina — {spec.title}",
        "",
        "<!-- Prodotto da `kdpfactory copertina <slug> --direzioni` dalle direzioni",
        f"     dell'agente `copertina` ({FILE}). La scelta è dell'autore e non passa dal",
        "     silenzio-assenso: `copertina <slug> --direzione N`. -->",
        "",
        "## Che cosa vende nella categoria",
        "",
        str(dati.get("codici_del_genere", "")).strip(),
        "",
    ]
    for numero, d in enumerate(dati.get("direzioni") or [], 1):
        prompt = prompt_bozzetto(spec, d, **kwargs)
        voci.append({"direzione": numero, "nome": d.get("nome", ""), "prompt": prompt})
        palette = next((p for p in coverdesign.PALETTES if p.name == d.get("palette")), None)
        colori = (f"{coverbrief.nome_colore(palette.background)}, accento "
                  f"{coverbrief.nome_colore(palette.accent)}" if palette else d.get("palette", ""))
        righe += [
            f"## {numero}. {d.get('nome', '')}",
            "",
            str(d.get("idea", "")).strip(),
            "",
            f"- **Perché vende**: {str(d.get('perche', '')).strip()}",
            f"- **Come si distingue**: {str(d.get('distacco', '')).strip()}",
            f"- **Titolo**: {POSTO.get(d.get('composizione'), POSTO['alto'])}"
            f" · carattere {d.get('tipografia') or coverbrief.tipografia(spec)}",
            f"- **Palette**: «{d.get('palette', '')}» ({colori})",
            "",
            "Prompt del bozzetto:",
            "",
            "```text",
            prompt,
            "```",
            "",
        ]
    prompt_file = build / PROMPT_BOZZETTI
    prompt_file.write_text(json.dumps(voci, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    riepilogo = build / RIEPILOGO
    riepilogo.write_text("\n".join(righe), encoding="utf-8")
    return prompt_file, riepilogo


def registra_bozzetti(project, voci: list[dict]) -> Path:
    """La traccia dei bozzetti generati: le voci nuove sostituiscono quelle della stessa direzione."""
    file = project.root / "build" / BOZZETTI
    tenute = [v for v in bozzetti(project)
              if int(v["direzione"]) not in {int(n["direzione"]) for n in voci}]
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(sorted(tenute + voci, key=lambda v: int(v["direzione"])),
                               ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return file


def scegli(project, numero: int, perche: str = "", quando: str = "",
           memoria: Path | None = None) -> dict:
    """Registra la direzione scelta dall'autore e la ricorda per i libri dopo.

    Restituisce la direzione. Chi chiama porta palette, composizione e
    carattere in `book.json`: il motore li legge da lì.
    """
    dati = leggi(project)
    if problemi(dati):
        raise ValueError("Le direzioni hanno ancora problemi: " + " ".join(problemi(dati)))
    direzioni = dati["direzioni"]
    if not 1 <= numero <= len(direzioni):
        raise ValueError(f"Direzione {numero}: sono {len(direzioni)}.")
    dati["scelta"] = {"direzione": numero, "perche": perche, "quando": quando}
    percorso(project).write_text(json.dumps(dati, ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8")
    memoria = memoria or coverbrief.DIREZIONE_APPRESA
    try:
        appresa = json.loads(memoria.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        appresa = {}
    storia = appresa.setdefault("direzioni_scelte", [])
    storia.append({
        "libro": dati.get("libro", project.root.name),
        "quando": quando,
        "scelta": {k: direzioni[numero - 1].get(k) for k in
                   ("nome", "idea", "tecnica", "composizione", "palette", "tipografia")},
        "scartate": [d.get("nome", "") for i, d in enumerate(direzioni, 1) if i != numero],
        "perche": perche,
    })
    memoria.parent.mkdir(parents=True, exist_ok=True)
    memoria.write_text(json.dumps(appresa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return direzioni[numero - 1]


def richiesta_studio(slug: str, mercato: str, categoria: str, canale: dict,
                     asin: str = "") -> tuple[str, str]:
    """La richiesta a Cowork delle copertine che vendono nella categoria (ruolo concorrente).

    È lo studio che il video A chiede prima di disegnare (32:10: «analizzare i
    bestseller del proprio genere»), e che l'agente `copertina` usa per i codici
    del genere: che cosa le accomuna, da rispettare, e che cosa nessuna fa, dove
    il libro si può distinguere. Solo descrizioni a parole: sono copertine di altri.
    """
    dove = (f"della categoria «{categoria}»" if categoria
            else "della prima categoria nella riga «Best Sellers Rank» di\n"
                 f"https://www.{mercato}/dp/{asin}")
    corpo = (
        cowork.intestazione(f"Cowork · le copertine che vendono nella categoria — {slug}",
                            STUDIO.replace(".md", "-risposta.md"), "concorrente", canale,
                            f"books/{slug}/concorrente")
        + f"\nLa copertina di un libro nuovo si progetta come farebbe un editore: prima si\n"
        f"guarda che cosa vende nella sua categoria. Su {mercato}, reparto Books, apri la\n"
        f"pagina Best Sellers {dove} e riporta il percorso della categoria e l'URL.\n\n"
        + (avvio.consegna(mercato) + "\n" if mercato in avvio.MERCATI else "")
        + "1. **Le prime dieci.** Per i primi dieci libri cartacei della classifica (salta\n"
        "   Audible e Kindle), guardando la miniatura nei risultati, uno per riga:\n"
        "   - posizione in classifica e ASIN (non serve il titolo);\n"
        "   - i colori principali, da due a quattro, e quale domina;\n"
        "   - il tipo d'immagine: fotografia o illustrazione; figurativa o astratta;\n"
        "     che cosa mostra, in poche parole;\n"
        "   - il titolo: in alto, al centro o in basso; quanta altezza prende (un\n"
        "     quinto, un terzo…); se si legge in miniatura;\n"
        "   - il carattere del titolo: con grazie, senza grazie, condensato o\n"
        "     corsivo/calligrafico; neretto o sottile; maiuscolo o no;\n"
        "   - quanti elementi ci sono in tutto (immagine, scritte, bollini) e dove sta\n"
        "     il nome dell'autore.\n"
        "2. **I codici del genere.** In cinque righe al massimo: che cosa hanno in\n"
        "   comune quasi tutte (colori, tipo d'immagine, posizione e carattere del\n"
        "   titolo), cioè quello che un lettore della categoria si aspetta.\n"
        "3. **Lo spazio libero.** In tre righe: che cosa non fa nessuna, o quasi —\n"
        "   un colore, un tipo d'immagine, una composizione — dove un libro nuovo si\n"
        "   può distinguere senza uscire dal genere.\n"
        "4. **La più forte in miniatura.** Quale delle dieci si nota per prima in\n"
        "   mezzo alle altre, e perché, in due righe.\n\n"
        "Niente screenshot né immagini salvate, e niente titoli o nomi d'autore nella\n"
        "risposta: sono copertine di altri, e il brief di copertina non le nomina.\n\n"
        "Chi usa i risultati: l'agente `copertina` della fabbrica, per le tre direzioni\n"
        f"d'arte della copertina di {slug} (`{FILE}`).\n"
    )
    return STUDIO, corpo

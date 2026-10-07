"""Il brief di copertina da dare a uno strumento grafico.

Il motore di `coverdesign` disegna copertine funzionanti e non costa niente, ma
c'è una cosa che per costruzione non sa fare: l'atmosfera. Una silhouette
vettoriale su fondo piatto dice *che libro è*; non dice *che mondo è*. Su un
full-content — dove si compra un'esperienza, non una specifica — quella
differenza si paga in clic.

Per quei casi il sistema non disegna: **scrive il brief**. Prende i dati che il
libro ha già (categoria, promessa, pubblico, palette, misure di stampa) e li
mette nella forma che uno strumento di generazione grafica esegue bene. Il
brief esce in inglese perché è la lingua in cui quegli strumenti sbagliano
meno — ma i testi che finiscono *stampati* sulla copertina restano nella lingua
del libro, ed è scritto dentro il brief.

L'immagine che torna rientra dalla porta che esiste già: si salva in
`assets/copertina.jpg` e `coverimage.py` la misura, la ritaglia sulle
proporzioni esatte della prima, la porta a 300 DPI e dice se i pixel bastano.

Una regola che questo modulo non negozia: nel brief non entrano mai nomi di
autori, editori, personaggi, marchi o copertine esistenti da imitare. Non è
prudenza legale astratta — è che una copertina che somiglia a un'altra viene
rimossa da KDP, e il libro con lei.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from . import coverart, coverdesign, coverimage, kdpspecs
from .models import BookSpec

#: quanto deve essere larga l'immagine della sola prima, a 300 DPI
FRONT_DPI = 300

#: il brief è in inglese, ma deve dire in inglese *quale* lingua va stampata
LANGUAGE_NAMES = {"it": "Italian", "en": "English"}


def _lines(items: list[str], prefix: str = "- ") -> str:
    return "\n".join(f"{prefix}{item}" for item in items if item) or "- (not specified)"


#: Che cosa deve *mostrare* la copertina, categoria per categoria.
#:
#: È la parte del brief che decide se la copertina funziona, e non si può
#: ricavare dai dati del libro: un motore che sceglie da solo finisce sempre
#: sull'ornamento astratto, perché è l'unica cosa che va bene per tutti. Qui
#: si dice all'illustratore che cosa esiste nel mondo del libro.
RAPPRESENTAZIONE: dict[str, str] = {
    "enigmi": (
        "Show the puzzles: a readable grid, numbers, clues, a pencil, the shape "
        "of the thing the buyer will be doing. Someone who solves puzzles must "
        "recognise the kind of puzzle from the thumbnail alone."
    ),
    "coloring": (
        "Show the artwork the buyer will colour: real illustrations from the "
        "inside, in the actual style and line weight, not a generic cover drawing."
    ),
    "attivita": (
        "Show the activity: children doing it, the objects involved — scissors, "
        "letters, numbers, shapes — and a glimpse of a worksheet."
    ),
    "planner": (
        "Show the layouts: a spread, a calendar grid, the stationery of someone "
        "who plans. The buyer is choosing a system, so show the system."
    ),
    "journal": (
        "Show the act of writing and the life around it: a hand, a page, a quiet "
        "table — the situation the buyer is imagining for themselves."
    ),
    "self-help": (
        "Show the person, the situation or the one object that stands for the "
        "change. Not an abstract sunrise: the concrete thing the reader is stuck on."
    ),
    "casa-finanze": (
        "Show the one object that stands for a household's bills — a paper envelope, "
        "or a small neat stack of them — as a single, clearly drawn subject: not a "
        "whole room, not a busy kitchen table, not an office, a chart or a pile of "
        "coins. Paper stays blank: a bill with readable dates and amounts is text."
    ),
    "business": (
        "Show the professional world of the book: the setting, the person, the "
        "object or the mechanism the argument turns on."
    ),
    "cucina": (
        "Show the food: one finished dish, appetising and specific, shot or drawn "
        "the way the reader wants it to come out."
    ),
    "viaggi": (
        "Show the destination: a landscape or a place that is recognisably *that* "
        "place, not a generic beach."
    ),
    "bambini": (
        "Show the characters, expressive and mid-action, in their environment."
    ),
    "romance": (
        "Show the people and what is between them: an interaction, a look, a "
        "setting that carries the relationship."
    ),
    "fiction": (
        "Show the world: a character, an environment or the one object the story "
        "turns on. The reader must be able to tell the genre before reading a word."
    ),
    "non-fiction": (
        "Show the concrete subject of the book — the place, the object, the scene "
        "or the situation it is actually about — rendered as a real thing rather "
        "than as a symbol of itself."
    ),
}

#: La direzione visiva di ogni copertina. L'ha chiesta l'autore il 6 ottobre
#: 2026 (semplice, pulita, poco articolata, impatto dal contrasto) e la
#: completano le regole dei due video sulle copertine che vendono
#: (`config/cowork-copertine-video-2-risposta.md`), che dove dicono altro
#: vincono: pochi elementi nello stesso stile (B 9:45, 21:52), colori del
#: genere, da due a quattro (A 10:28, 12:53), chiaro contro scuro (A 7:15),
#: niente sfondo rumoroso dove vanno le scritte (A 12:42), nitidezza (A 15:01) e
#: niente dominante giallo-senape (B 2:24). Sta in ogni prompt, prima dello stile.
DIREZIONE_VISIVA = (
    "Keep it simple: one clear focal subject and at most three elements in the whole "
    "image, all drawn in the same style and under the same light, with bold shapes that "
    "still read at thumbnail size and generous calm space. No small scattered details, no "
    "busy texture where the title will sit. The impact comes from strong light-against-dark "
    "contrast and a palette of two to four colours that belongs to the genre. Pin-sharp, "
    "high-resolution rendering, with no overall yellow, mustard or sepia cast."
)

#: Dove il titolo verrà composto, detto al generatore: l'immagine gli lascia il
#: posto, perché è il titolo che ferma chi scorre (video B, 3:37) e l'immagine
#: lo sostiene, non lo soffoca (video A, 5:06).
POSTO_DEL_TITOLO = {
    "alto": (
        "Keep the upper third calm and simple, because the title will be set there "
        "afterwards in large type; the subject sits in the middle and lower part."
    ),
    "centro": (
        "Keep a calm, plain area in the middle of the image — roughly a circle over the "
        "central third — because the title will be set there afterwards in large type. "
        "Place the subjects around it, at the sides and below, turned towards the centre, "
        "with soft shadows that give depth."
    ),
}


def posto_del_titolo(spec: BookSpec) -> str:
    layout = getattr(spec, "cover_layout", "auto")
    return POSTO_DEL_TITOLO.get(layout, POSTO_DEL_TITOLO["alto"])


#: Che cosa disegnare nei bozzetti, quando la rappresentazione della categoria è
#: una scena: l'oggetto solo, che il trattamento poi riduce all'essenziale.
OGGETTO: dict[str, str] = {
    "casa-finanze": "a single sealed paper envelope",
}

#: I modi di ridurre l'oggetto all'essenziale, da provare nei bozzetti. Quelli che
#: l'autore sceglie finiscono in `config/copertine-direzione.json` e da lì nei
#: prompt delle copertine vere: è così che il sistema impara il gusto dell'autore.
TRATTAMENTI: dict[str, str] = {
    "luce": "the subject caught in one hard pool of light on an almost black field; "
            "everything else falls into shadow",
    "silhouette": "the subject as a bold flat silhouette in the accent colour on the dark "
                  "field, no inner detail",
    "serigrafia": "a flat graphic poster look, like a screen print: two or three solid "
                  "colours, crisp edges, no gradients",
    "campo-diviso": "the field split into two solid colour blocks, dark and accent, with the "
                    "subject sitting across the split",
    "carta": "cut-paper style: a few layered paper shapes with soft shadows, very few pieces",
    "dettaglio": "a tight close-up of one part of the subject filling the lower half; the "
                 "rest of the frame is a calm dark field",
    "linea": "a single continuous line drawing in the accent colour on the dark field",
    "fotografia": "a still-life photograph of the subject alone, studio-lit, on a seamless "
                  "dark backdrop",
}

#: Dove sta quello che l'autore ha scelto fra i bozzetti.
DIREZIONE_APPRESA = Path(__file__).resolve().parent.parent / "config" / "copertine-direzione.json"


def direzione_appresa(percorso: Path | None = None) -> dict:
    """I trattamenti preferiti e scartati dall'autore, se ha già scelto dei bozzetti."""
    percorso = percorso or DIREZIONE_APPRESA
    try:
        return json.loads(percorso.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def registra_direzione(
    preferiti: list[str], scartati: list[str], perche: str = "", percorso: Path | None = None,
    quando: str = "",
) -> dict:
    """Le scelte dell'autore fra i bozzetti: entrano nei prompt delle copertine vere.

    Un trattamento scelto passa in testa ai preferiti; uno scartato esce dai
    preferiti ed entra fra gli scartati. Le scelte più recenti vincono.
    """
    sconosciuti = [k for k in [*preferiti, *scartati] if k not in TRATTAMENTI]
    if sconosciuti:
        raise ValueError(f"Trattamenti sconosciuti: {', '.join(sconosciuti)} "
                         f"(validi: {', '.join(TRATTAMENTI)})")
    percorso = percorso or DIREZIONE_APPRESA
    direzione = direzione_appresa(percorso) or {
        "_nota": "Le scelte dell'autore fra i bozzetti di copertina (coverbrief.TRATTAMENTI). "
                 "I preferiti, in quest'ordine, diventano il trattamento delle varianti; "
                 "gli scartati non si propongono più nei bozzetti.",
        "principio": DIREZIONE_VISIVA,
        "preferiti": [],
        "scartati": [],
    }
    tenuti = [p for p in direzione.get("preferiti", [])
              if p.get("trattamento") not in preferiti and p.get("trattamento") not in scartati]
    direzione["preferiti"] = [{"trattamento": k, "perche": perche, "quando": quando}
                              for k in preferiti] + tenuti
    via = [s for s in direzione.get("scartati", [])
           if s.get("trattamento") not in scartati and s.get("trattamento") not in preferiti]
    direzione["scartati"] = [{"trattamento": k, "perche": perche, "quando": quando}
                             for k in scartati] + via
    percorso.parent.mkdir(parents=True, exist_ok=True)
    percorso.write_text(json.dumps(direzione, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return direzione


def trattamenti_da_provare(direzione: dict | None = None) -> list[str]:
    """I trattamenti per i bozzetti: tutti, tranne quelli che l'autore ha scartato."""
    direzione = direzione_appresa() if direzione is None else direzione
    scartati = {s.get("trattamento") for s in direzione.get("scartati", [])}
    return [k for k in TRATTAMENTI if k not in scartati]


def trattamenti_preferiti(direzione: dict | None = None) -> list[str]:
    direzione = direzione_appresa() if direzione is None else direzione
    return [p["trattamento"] for p in direzione.get("preferiti", [])
            if p.get("trattamento") in TRATTAMENTI]


#: lo stile contemporaneo che regge meglio in quella categoria
STILE: dict[str, str] = {
    "enigmi": "Clean, high-contrast retail design: the grid is the hero.",
    "coloring": "Modern illustrated, with the interior line style visible.",
    "attivita": "Colourful lifestyle illustration, warm and busy but organised.",
    "planner": "Premium graphic design or clean minimalist.",
    "journal": "Premium editorial or sophisticated photography.",
    "self-help": "Premium editorial or bold typography with one strong object.",
    "casa-finanze": "Clean minimalist or premium graphic design: one everyday object, calm flat "
                    "colour, strong contrast — warm, never corporate.",
    "business": "Premium graphic design or sophisticated photography.",
    "cucina": "Sophisticated photography — food sells on appetite.",
    "viaggi": "Cinematic or sophisticated photography.",
    "bambini": "Character-based illustration.",
    "romance": "Modern illustrated or cinematic.",
    "fiction": "Cinematic, or modern illustrated with a strong central image.",
    "non-fiction": "Premium editorial or cinematic, depending on how much "
    "atmosphere the subject carries.",
}


#: come si riconosce la sotto-categoria dalle categorie KDP e dall'argomento.
#: `spec.genre` distingue solo fiction da non-fiction, che è troppo poco per
#: dire a un illustratore che cosa disegnare.
SPIE_CATEGORIA: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("coloring", ("coloring", "colouring", "colorare", "da colorare")),
    ("attivita", ("activity book", "attività", "workbook", "worksheet")),
    ("planner", ("planner", "agenda", "organizer")),
    ("journal", ("journal", "diario", "gratitude")),
    ("cucina", ("cook", "recipe", "cucina", "ricett", "food & wine", "baking")),
    ("viaggi", ("travel", "viagg", "guidebook")),
    ("bambini", ("children", "juvenile", "kids", "bambin", "ragazz", "picture book")),
    ("romance", ("romance", "rosa")),
    # Prima di «business»: un libro sulle bollette di casa parla di soldi, ma la
    # sua immagine è una cucina, non un ufficio (rodaggio household-bills).
    ("casa-finanze", ("personal finance", "household", "budgeting", "bollette", "finanze di casa")),
    ("business", ("business", "money", "finance", "marketing", "career", "economia")),
    ("self-help", ("self-help", "self help", "psycholog", "crescita personale",
                   "spiritual", "new age", "mind & spirit", "hypnosis", "benessere")),
)


#: Le categorie dove il carattere del titolo è elegante (il Garamond del libro)
#: invece che deciso: dove il genere parla sottovoce — sentimenti, diario,
#: spiritualità, cura, lutto, memorie — un bastone condensato urla (video A,
#: 7:59: «un romanzo rosa richiede caratteri più morbidi e più eleganti»).
TIPOGRAFIA_ELEGANTE = frozenset({"romance", "journal"})
SPIE_ELEGANTE = (
    "spiritual", "new age", "mind & spirit", "intuition", "intuizione", "meditation",
    "meditazione", "mindfulness", "memoir", "biograph", "grief", "lutto", "caregiv",
    "dementia", "alzheimer", "demenza", "poetry", "poesia",
)


def tipografia(spec: BookSpec, genre: str = "", metadata: dict | None = None) -> str:
    """La voce del titolo: quella scelta in `book.json`, o quella della categoria."""
    scelta = getattr(spec, "cover_type", "auto")
    if scelta in coverdesign.TIPOGRAFIE:
        return scelta
    metadata = metadata or {}
    genre = genre or ("enigmi" if spec.genre == "puzzle" else spec.genre)
    nicchia = ", ".join(metadata.get("categories") or spec.categories) or spec.topic
    if _chiave(spec, genre, nicchia) in TIPOGRAFIA_ELEGANTE:
        return "elegante"
    testo = f"{nicchia} {spec.topic} {spec.title}".lower()
    return "elegante" if any(spia in testo for spia in SPIE_ELEGANTE) else "deciso"


def _chiave(spec: BookSpec, genre: str, nicchia: str = "") -> str:
    """La categoria da cui prendere la rappresentazione e lo stile."""
    if (genre or "").strip().lower() == "enigmi":
        return "enigmi"
    testo = f"{nicchia} {spec.topic} {' '.join(spec.categories)}".lower()
    for chiave, spie in SPIE_CATEGORIA:
        if any(spia in testo for spia in spie):
            return chiave
    chiave = (genre or spec.genre or "").strip().lower()
    return chiave if chiave in RAPPRESENTAZIONE else "non-fiction"


def _unique_factor(spec: BookSpec, copy: coverdesign.CoverCopy, genre: str) -> str:
    """Un punto di partenza per il fattore distintivo, non un ordine.

    Si propone l'illustrazione che il motore avrebbe scelto per questo libro:
    è già tarata sul contenuto, e dà allo strumento grafico un appiglio
    concreto invece di una richiesta di originalità a vuoto.
    """
    try:
        art = coverart.pick(copy.subject or spec.topic, genre, wanted=spec.cover_art)
    except KeyError:
        return "one memorable visual metaphor for the book's central idea — choose it yourself"
    return (
        f"the engine's own reading of this book is «{art.name}» "
        f"({', '.join(art.keywords[:4])}): use it as a starting point for a single "
        "distinctive element, or replace it with a better one — but keep exactly one"
    )


def _prima_frase(testo: str) -> str:
    """La prima frase di un campo lungo: in un prompt d'immagine il resto è rumore."""
    testo = " ".join((testo or "").split())
    for fine in (". ", "? ", "! "):
        if fine in testo:
            return testo.split(fine, 1)[0] + fine.strip()
    return testo


def nome_colore(esadecimale: str) -> str:
    """Un colore detto a parole, col suo codice: «deep navy (#0E1320)».

    Un generatore d'immagini segue un nome meglio di un codice esadecimale, che
    da solo legge come un numero qualunque. Il nome è approssimato, il codice resta
    accanto per chi vuole stare dentro la serie.
    """
    import colorsys

    codice = esadecimale.strip().lstrip("#")
    r, g, b = (int(codice[i:i + 2], 16) / 255 for i in (0, 2, 4))
    tinta, luce, saturazione = colorsys.rgb_to_hls(r, g, b)
    gradi = tinta * 360
    if saturazione < 0.12 or luce < 0.06 or luce > 0.96:
        nome = "near-black" if luce < 0.2 else "white" if luce > 0.9 else "grey"
    else:
        nomi = ((15, "red"), (40, "orange"), (55, "golden amber"), (70, "yellow"),
                (160, "green"), (195, "teal"), (250, "blue"), (290, "purple"),
                (345, "magenta"), (361, "red"))
        nome = next(n for limite, n in nomi if gradi < limite)
        if nome == "blue" and luce < 0.25:
            nome = "navy"
        # Un rosso o un arancio molto scuri si vedono marroni: chiamarli «deep
        # red» fa dipingere al generatore un fondo vinaccia al posto del bruno.
        if nome in ("red", "orange") and luce < 0.2 and gradi < 40:
            nome = "brown"
        if luce > 0.85 and 30 <= gradi < 60:
            nome = "cream"
        elif luce < 0.25:
            nome = f"deep {nome}"
        elif luce < 0.35:
            nome = f"dark {nome}"
        elif saturazione < 0.3:
            nome = f"muted {nome}"
        elif luce > 0.8:
            nome = f"pale {nome}"
    return f"{nome} (#{codice.upper()})"


#: Come cambia la composizione da una variante all'altra quando le genera un
#: programma: ogni chiamata è indipendente e non sa delle altre, quindi la
#: differenza va chiesta dentro il prompt.
COMPOSIZIONE_VARIANTI = (
    "",
    "Composition for this version: a closer view, from a nearer and lower viewpoint, "
    "so the main subject fills more of the frame.",
    "Composition for this version: a wider view, seen from further back or slightly "
    "from above, with more calm space around the subject.",
)


def prompt_da_incollare(
    spec: BookSpec,
    *,
    pages: int,
    metadata: dict | None = None,
    copy: coverdesign.CoverCopy | None = None,
    genre: str = "",
    concorrente: str = "",
    varianti: int = 3,
    variante: int = 1,
    per_chat: bool = True,
    direzione: dict | None = None,
) -> str:
    """Il prompt della copertina in un blocco solo, da incollare in una chat di ChatGPT.

    `brief` resta il riferimento di chi progetta la copertina: porta dorso,
    codice a barre e specifiche di stampa, che a un generatore d'immagini non
    servono e rischiano di sviarlo: «full wrap» e «spine» invitano a disegnare
    l'intera copertina col dorso invece della prima. Qui restano solo le cose che decidono
    l'immagine, prese dagli stessi dati: che cosa mostrare, lo stile, il
    fattore distintivo, la palette, la composizione, i divieti. In inglese, la
    lingua in cui i generatori sbagliano meno.

    Con `per_chat=False` è il prompt per un generatore che si chiama da
    programma (Higgsfield): niente frasi di conversazione, e la variante
    `variante` porta la sua indicazione di composizione.

    Con `direzione` (una delle tre direzioni d'arte di `direzioni.py`, quella
    scelta dall'autore) soggetto, elementi, resa, luce, palette e posto del
    titolo vengono da lì invece che dalla categoria: la categoria dice che cosa
    mostra un libro così, la direzione come lo mostra questo.
    """
    metadata = metadata or {}
    genre = genre or ("enigmi" if spec.genre == "puzzle" else spec.genre)
    copy = copy or coverdesign.derive_copy(spec, metadata, genre, pages=pages)
    palette = coverdesign.pick_palette(spec, genre)
    if direzione:
        palette = next((t for t in coverdesign.PALETTES if t.name == direzione.get("palette")),
                       palette)
    panel_w, panel_h = coverimage.front_panel_size_in(spec.trim)
    px_w, px_h = math.ceil(panel_w * FRONT_DPI), math.ceil(panel_h * FRONT_DPI)
    nicchia = ", ".join(metadata.get("categories") or spec.categories) or spec.topic
    chiave = _chiave(spec, genre, nicchia)
    titolo = f"{spec.title} — {spec.subtitle}" if spec.subtitle else spec.title

    try:
        art = coverart.pick(copy.subject or spec.topic, genre, wanted=spec.cover_art)
        distintivo = (
            "exactly one distinctive element that makes the cover memorable, built on the "
            f"idea of {', '.join(art.keywords[:3])}; nothing else may compete with it."
        )
    except KeyError:
        distintivo = (
            "exactly one distinctive element that makes the cover memorable: one visual "
            "metaphor for the book's central idea; nothing else may compete with it."
        )

    if per_chat:
        testa = (f"Front cover illustration for a paperback book: «{titolo}». "
                 f"This is variant 1 of {varianti}.")
    else:
        testa = f"Front cover illustration for a paperback book: «{titolo}»."
        composizione = COMPOSIZIONE_VARIANTI[(variante - 1) % len(COMPOSIZIONE_VARIANTI)]
        if composizione:
            testa += f" {composizione}"
    if direzione:
        elementi = [e for e in direzione.get("elementi") or [] if e]
        rappresentazione = (
            f"Show {direzione['soggetto'].rstrip('.')}. "
            + (f"The image holds only: {'; '.join(elementi)}. " if elementi else "")
            + "Nothing else may compete with the main subject."
        )
    else:
        rappresentazione = RAPPRESENTAZIONE[chiave]
    righe = [testa, "", rappresentazione]
    if spec.audience:
        righe.append(f"Who it is for: {_prima_frase(spec.audience)}")
    if spec.promise or spec.topic:
        righe.append(f"What the book does: {_prima_frase(spec.promise or spec.topic)}")
    if copy.hook:
        righe.append(f"The question it answers, for the mood only (never write it): «{copy.hook}»")
    # Il trattamento: quello che l'autore ha scelto fra i bozzetti, uno per
    # variante a giro; senza scelte resta lo stile della categoria.
    if direzione:
        stile = (
            f"Rendering: {direzione['tecnica'].rstrip('.')}."
            + (f" Light: {direzione['luce'].rstrip('.')}." if direzione.get("luce") else "")
            + (f" Mood: {direzione['emozione'].rstrip('.')}." if direzione.get("emozione") else "")
        )
        posto = POSTO_DEL_TITOLO.get(direzione.get("composizione"), POSTO_DEL_TITOLO["alto"])
        distinto = []
    else:
        preferiti = trattamenti_preferiti()
        trattamento = (
            f" Treatment: {TRATTAMENTI[preferiti[(variante - 1) % len(preferiti)]]}."
            if preferiti else ""
        )
        stile = f"Style: {STILE[chiave]}{trattamento}"
        posto = posto_del_titolo(spec)
        distinto = [f"Include {distintivo}"]
    righe += [
        "",
        f"Direction: {DIREZIONE_VISIVA}",
        f"{stile} Art-directed and current, like a cover a major publisher would release "
        "this year: not a stock template, not a generic AI image.",
        *distinto,
        f"Colour: a {nome_colore(palette.background)} background, {nome_colore(palette.deep)} "
        f"for depth and a single accent of {nome_colore(palette.accent)}. Strong contrast, so "
        "the cover stands out on Amazon's white search page.",
        "",
        f"Composition: portrait, 2:3. One dominant focal point. {posto} Keep anything "
        "important at least 4% of the width inside every edge: the print is trimmed. It must "
        "still read as a 160-pixel-wide thumbnail.",
        "",
        "Absolutely no text: no letters, numbers, title, author name, logo, signature or "
        "watermark anywhere. Any paper, screen or calendar in the scene stays blank.",
        "No deformed or half-formed objects, and no stray marks that look like lettering: "
        "every element must be finished and recognisable.",
        "Original work: do not imitate any existing book cover, artist, brand or character, "
        "and do not show a recognisable real person. No border, no frame, no 3D book mock-up.",
    ]
    if concorrente.strip():
        rivale = " ".join(concorrente.split())
        righe += [
            "",
            "Readers of this category must recognise it as one of theirs, and tell it apart at "
            f"a glance from the best-selling cover it sits next to, which looks like this: {rivale} "
            "Keep the conventions of the genre — the kind of image and the layout its readers "
            "expect — and change the nuance: a different dominant colour and a different "
            "distinctive element. Do not copy, parody or answer that cover.",
        ]
    if per_chat:
        righe += [
            "",
            "Make the image at the largest size you can. The print needs at least "
            f"{px_w} x {px_h} px: if yours is smaller, deliver it anyway and say so. After the "
            "image, tell me its exact size in pixels and the model that made it.",
        ]
    else:
        righe += ["", "Portrait 2:3, at the highest resolution available, full bleed."]
    return "\n".join(righe)


def prompt_bozza(
    spec: BookSpec,
    trattamento: str,
    *,
    pages: int,
    metadata: dict | None = None,
    copy: coverdesign.CoverCopy | None = None,
    genre: str = "",
) -> str:
    """Il prompt di un bozzetto: l'oggetto del libro ridotto all'essenziale in un trattamento.

    I bozzetti servono a scegliere una direzione, non a stampare: costano poco,
    sono corti, e cambiano una cosa sola — il trattamento — tenendo fermi
    oggetto, palette e direzione visiva. Quelli che l'autore sceglie diventano
    il trattamento delle copertine vere (`config/copertine-direzione.json`).
    """
    metadata = metadata or {}
    genre = genre or ("enigmi" if spec.genre == "puzzle" else spec.genre)
    copy = copy or coverdesign.derive_copy(spec, metadata, genre, pages=pages)
    palette = coverdesign.pick_palette(spec, genre)
    nicchia = ", ".join(metadata.get("categories") or spec.categories) or spec.topic
    chiave = _chiave(spec, genre, nicchia)
    oggetto = OGGETTO.get(chiave, "the one object that best stands for the book's subject")
    return "\n".join([
        f"Rough cover sketch for a paperback book: «{spec.title}», about "
        f"{_prima_frase(spec.promise or spec.topic).rstrip('.').lower()}.",
        f"Subject: {oggetto}.",
        f"Treatment: {TRATTAMENTI[trattamento]}.",
        f"Direction: {DIREZIONE_VISIVA}",
        f"Colours: a {nome_colore(palette.background)} field and {nome_colore(palette.accent)} "
        "for the subject; nothing else.",
        f"{posto_del_titolo(spec)} No text, letters or numbers anywhere. Portrait 2:3.",
    ])


def brief(
    spec: BookSpec,
    *,
    pages: int,
    metadata: dict | None = None,
    copy: coverdesign.CoverCopy | None = None,
    genre: str = "",
    concorrente: str = "",
) -> str:
    """Il brief compilato coi dati di questo libro, pronto da incollare.

    `concorrente` è la descrizione della copertina da battere, quando l'autore
    l'ha chiesto all'avvio: senza titolo né autore, solo come appare in
    miniatura. Il brief chiede un'immagine che se ne distingua a colpo d'occhio.
    """
    metadata = metadata or {}
    genre = genre or ("enigmi" if spec.genre == "puzzle" else spec.genre)
    copy = copy or coverdesign.derive_copy(spec, metadata, genre, pages=pages)
    palette = coverdesign.pick_palette(spec, genre)

    trim_w, trim_h = kdpspecs.trim_size_in(spec.trim)
    # I pixel si chiedono sull'area che il motore ritaglia davvero — la prima
    # con la sua abbondanza —, non sul formato rifilato: 1800 x 2700 px su un
    # 6x9 uscivano a 291 DPI e davano l'avviso (rodaggio household-bills).
    panel_w, panel_h = coverimage.front_panel_size_in(spec.trim)
    px_w, px_h = math.ceil(panel_w * FRONT_DPI), math.ceil(panel_h * FRONT_DPI)
    cover_w, cover_h = kdpspecs.cover_size_in(spec.trim, pages, spec.paper)
    spine = kdpspecs.spine_width_in(pages, spec.paper)
    medium = copy.is_medium

    tipo = "MEDIUM-CONTENT" if medium else "FULL-CONTENT"
    formula = (
        "CATEGORY SIGNAL + BENEFIT / FEATURE + INTERIOR PREVIEW + QUANTIFIER + UNIQUE FACTOR"
        if medium
        else "GENRE / PROBLEM + BIG PROMISE + WORLD / EMOTION + VISUAL METAPHOR + UNIQUE FACTOR"
    )
    priorita = (
        "Prioritise FUNCTION over atmosphere: what kind of product this is, who it is for, "
        "what the buyer will find inside, how much of it there is."
        if medium
        else "Prioritise EMOTION, IDENTITY and TRANSFORMATION over technical information: "
        "genre, central desire, emotional tone, the world of the book."
    )
    strategia = (
        [
            "Show a recognisable preview of the actual interior content when it helps.",
            "Treat the functional information as part of the design, not as fine print.",
            "Use badges, banners or geometric blocks only when they improve the hierarchy.",
            "Favour strong retail readability over decorative complexity.",
        ]
        if medium
        else [
            "Use one strong central image, scene, object or metaphor.",
            "Favour atmosphere and emotional storytelling over feature lists.",
            "Keep the composition simple enough to survive as a thumbnail.",
            "Let the visual concept reinforce the meaning of the title.",
        ]
    )
    colore = (
        "Strong, clear, retail-oriented colour blocking."
        if medium
        else "Colour may be atmospheric and emotional, but thumbnail contrast comes first."
    )

    cifre = (
        "Any figure printed on the cover must be one of the counted numbers "
        "quoted above, exactly as written. There are no others."
        if copy.stats
        else "Do not print any figure on the cover: this book has no counted "
        "quantity to claim, and an invented one is a promise nobody keeps."
    )
    contenuti = metadata.get("bullets") or []
    nicchia = ", ".join(metadata.get("categories") or spec.categories) or spec.topic
    chiave = _chiave(spec, genre, nicchia)
    rappresentazione = RAPPRESENTAZIONE[chiave]
    stile = STILE[chiave]
    bar_w, bar_h = kdpspecs.BARCODE_ZONE_IN
    dorso = (
        f"- Spine width {spine:.3f}\", calculated from {pages} pages on "
        f"{spec.paper} paper at {spec.trim}. Text is allowed at this page count.\n"
        f"- Keep at least {coverdesign.SPINE_TEXT_CLEARANCE_IN}\" clear on each side of "
        "the spine text: the fold moves in production."
        if kdpspecs.spine_text_allowed(pages)
        else f"- Spine width {spine:.3f}\". **No spine text**: KDP does not allow it "
        f"below {kdpspecs.SPINE_TEXT_MIN_PAGES} pages and this book has {pages}."
    )
    testi = [
        f'Kicker (category signal): "{copy.kicker}"' if copy.kicker else "",
        f'Hook: "{copy.hook}"' if copy.hook else "",
        f'Quantifier: "{copy.stats}" — these figures are counted from the finished '
        "book; do not invent, round or add any other number" if copy.stats else "",
        f'Badge: "{copy.badge}"' if copy.badge else "",
        f'Author line: "{spec.author}"',
    ]

    rivale = (
        "\n## Stand out from the cover it competes with\n\n"
        "In search results this cover sits next to the best-selling cover in its niche,\n"
        "described here as it looks at thumbnail size:\n\n"
        + "\n".join(f"> {r}" if r.strip() else ">" for r in concorrente.strip().splitlines())
        + "\n\nReaders of this category must recognise this cover as one of theirs: keep the\n"
        "conventions of the genre — the kind of image and the layout they expect — and\n"
        "differ by a nuance, so the buyer notices this one first and tells them apart:\n"
        "- a different dominant colour, chosen for contrast against that one;\n"
        "- a different distinctive element: not the same object or scene;\n"
        "- a calmer area where the title goes, so it reads larger than theirs.\n"
        "Do not copy, parody or answer that cover: it is a reference to move away from.\n"
        if concorrente.strip()
        else ""
    )

    return f"""# Cover brief — {spec.title}

<!-- Prodotto da `kdpfactory copertina {spec.slug}`. Incollalo nello strumento
     grafico. L'immagine che torna va salvata in `assets/copertina.jpg`: da lì
     `build` la ritaglia sulla prima, la porta a 300 DPI e dice se basta. -->

Create a professional Amazon KDP book cover optimised for high click-through
rate and strong thumbnail recognition on Amazon.

BOOK TYPE: {tipo}
BOOK TITLE: {spec.title}
SUBTITLE: {spec.subtitle or "(none)"}
NICHE / CATEGORY: {nicchia}
TARGET AUDIENCE: {spec.audience}
MAIN BENEFIT / PROMISE: {spec.promise or spec.topic}
KEY CONTENT / FEATURES:
{_lines(contenuti[:5])}
UNIQUE FACTOR: {_unique_factor(spec, copy, genre)}

## Core design system

CATEGORY SIGNAL -> BIG PROMISE -> REPRESENTATIVE VISUAL -> TYPOGRAPHIC HIERARCHY -> UNIQUE FACTOR

Formula for this category: {formula}
{priorita}

## The visual must represent the book

This is the instruction that decides whether the cover works. Use figures,
characters, objects, scenes, illustrations, photography or visual symbols that
show **what this book is actually about**.

Do not produce an abstract cover when a representative image would say it
faster. A shape, a gradient or a geometric ornament decorates; a recognisable
image explains. On a search page the customer is not reading — they are
scanning for the one cover that looks like the thing they came for.

{rappresentazione}

Avoid: unrelated stock imagery, meaningless abstract shapes, generic decorative
icons, random objects, visual clutter, and the smooth symmetrical look of an
image generated without direction. The visual should explain the book, not
decorate it.

## Visual style

{DIREZIONE_VISIVA}

Pick the ONE contemporary approach that fits this niche and commit to it:
premium editorial · modern illustrated · cinematic · clean minimalist · bold
typography · colourful lifestyle illustration · sophisticated photography ·
character-based illustration · premium graphic design · infographic-inspired
commercial design.

{stile}

The result should look art-directed and current — a cover a working publisher
would put out this year — not a self-published template and not a generic
generated image.

The cover must say what the book is within 1-2 seconds when seen as a small
Amazon thumbnail, {coverdesign.THUMBNAIL_WIDTH_PX} px wide on a white page,
surrounded by twenty others.

## Rules

- One dominant visual concept; no competing focal points.
- The title is the primary text element and must stay readable at thumbnail size:
  its capital height must reach at least {coverdesign.MIN_TITLE_CAP_RATIO * 100:g}% of the
  cover height ({coverdesign.GOOD_TITLE_CAP_RATIO * 100:g}% is where it becomes dominant),
  on at most {coverdesign.MAX_TITLE_LINES} lines.
- Contrast between title and background of at least {coverdesign.MIN_CONTRAST:.0f}:1.
- The background must separate from the white search page: avoid pale, washed
  backgrounds that dissolve into it.
- At most {coverdesign.MAX_TOP_ELEMENTS} text blocks in the upper half.
- Exactly ONE unique factor. It must aid recognition without competing with the title.
- Intentional negative space; no clutter, no decorative filler.
- Every element in the same style and the same light; two to four main colours.
- No deformed or half-formed generated element left in the image.
- Commercial publishing aesthetics, not a stock template.
{_lines(strategia)}

## Colour

{colore}
The engine's palette for this book, if you want to stay inside the series:
background {palette.background}, deep {palette.deep}, title {palette.title},
accent {palette.accent}, muted {palette.muted} (palette «{palette.name}»).
Do not use many colours without a reason.

## Text on the cover — do not put it in the image

**Deliver the illustration only. No text, no lettering, no title, no author
name, no logo, no signature, no watermark anywhere in the image.**

The engine draws every line of text itself, in vector, over what you deliver.
That is not a preference: it is what keeps the cover checkable. A vector title
can be measured — cap height against cover height, contrast ratio against the
background, distance from the trim — and those measurements are what stop a
cover going out illegible or getting trimmed in print. A title baked into
pixels can be measured by nobody, keeps whatever spelling the model gave it,
and shows its edges at 300 DPI.

So: {posto_del_titolo(spec)} A busy area where the title goes costs the
cover its contrast.

For reference only: the engine will set the following text, written in
{LANGUAGE_NAMES.get(spec.language, spec.language)} because that is the language
of the book. Read it to understand what the image has to support, and do not
render any of it.

{_lines([t for t in testi if t])}

## Production specification — PAPERBACK

The engine assembles the printed wrap from the front illustration you deliver.
These numbers are the shape it will be printed at: make the illustration for
that shape, not the wrap itself.

- Trim size: {spec.trim} in ({trim_w}" x {trim_h}"), {pages} pages, {spec.paper} paper.
- Front cover with its bleed ({panel_w:.3f}" x {panel_h:.3f}"), at {FRONT_DPI} DPI: {px_w} x {px_h} px.
- Full wrap: ONE continuous image, BACK + SPINE + FRONT, {cover_w:.3f}" x {cover_h:.3f}",
  including a {kdpspecs.BLEED_IN}" bleed on every side, with a {spine:.3f}" spine.
  These are the numbers from the page count above; if the page count changes, they
  all change, and a cover built on the old one is rejected at upload.
- Every background or image meant to reach the edge must run through the bleed.
- Keep all text at least {coverdesign.SAFE_MARGIN_IN}" away from every trimmed edge:
  KDP cuts up to 3 mm and what crosses that line is lost in print.
- At least {FRONT_DPI} DPI, placed at 100% scale, prepared for CMYK printing.
- No thin decorative border near the trim edge: production variance makes it
  visibly uneven on one side. If a border is essential, set it well inside.

## Spine

{dorso}

- Spine text must never run onto the front or the back.
- Keep spine typography simple: it is read at an angle, on a shelf, once.

## Barcode area

Leave {bar_w}" x {bar_h}" free in the lower-right corner of the BACK cover,
{coverdesign.SAFE_MARGIN_IN}" in from the trim and from the spine. KDP prints the
barcode there, over whatever is underneath.

- No artwork, text, faces, product information or ornament in that rectangle.
- A clean white background is the safe choice.

## The file to deliver

- ONE image: the FRONT illustration only, portrait, at least
  {px_w} x {px_h} px, RGB, PNG or high-quality JPEG.
  More pixels are fine; fewer are not.
- Let the artwork run to every edge: the engine crops it to the trim with its
  bleed, so keep anything important at least {coverdesign.SAFE_MARGIN_IN}" inside.
- No text of any kind, no border, no frame, no mock-up, no 3D book render.

What the engine then sends to KDP, for reference, so nobody has to redo it:
ONE single PDF, unlocked, back + spine + front in one continuous image, fonts
and images embedded, transparency flattened. No crop marks, no trim marks, no
colour bars, no template guides, no placeholder text, no comments or
annotations, no hidden objects, no white border from a wrong bleed. Practical
target under 40 MB (hard limit 650 MB).

## If the format is not paperback

- HARDCOVER: do not reuse these dimensions. Use the KDP hardcover template; the
  artwork must extend about 0.51" (15 mm) past the front cover edge for the wrap,
  and nothing important may sit near the hinge.
- EBOOK: front cover only, 2560 x 1600 px (2560 tall, 1600 wide: ratio 1.6:1 or
  taller), RGB, JPEG or TIFF. Designed on its own, not cropped out of the wrap.
{rivale}
## Originality and compliance

- Original design. Do not imitate, reference or evoke any existing book cover,
  author, publisher, character, mascot, logo or copyrighted artwork.
- No trademarked visual identities, no recognisable proprietary characters.
- No award stamps, star ratings, review quotes or bestseller claims: Amazon
  forbids them on the cover, and a new book cannot keep those promises anyway.
- {cifre}

## Final check before delivering

1. The category is recognisable at a glance.
2. The promise is understandable immediately.
3. The area where the title goes is calm enough for a large title to stay readable at thumbnail size.
4. There is one dominant visual idea.
5. There is exactly one unique factor.
6. It does not look generic.
7. The hierarchy is obvious once the title is set over it.
8. Nothing resembles a competitor's cover.
9. No trademark, logo, mascot or proprietary identity is used.
10. It looks like a commercially viable Amazon KDP cover.
11. There is no text, letter or number anywhere in the image.
"""

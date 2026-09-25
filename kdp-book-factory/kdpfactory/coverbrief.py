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

from . import coverart, coverdesign, kdpspecs
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

#: lo stile contemporaneo che regge meglio in quella categoria
STILE: dict[str, str] = {
    "enigmi": "Clean, high-contrast retail design: the grid is the hero.",
    "coloring": "Modern illustrated, with the interior line style visible.",
    "attivita": "Colourful lifestyle illustration, warm and busy but organised.",
    "planner": "Premium graphic design or clean minimalist.",
    "journal": "Premium editorial or sophisticated photography.",
    "self-help": "Premium editorial or bold typography with one strong object.",
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
    ("business", ("business", "money", "finance", "marketing", "career", "economia")),
    ("self-help", ("self-help", "self help", "psycholog", "crescita personale",
                   "spiritual", "new age", "mind & spirit", "hypnosis", "benessere")),
)


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


def brief(
    spec: BookSpec,
    *,
    pages: int,
    metadata: dict | None = None,
    copy: coverdesign.CoverCopy | None = None,
    genre: str = "",
) -> str:
    """Il brief compilato coi dati di questo libro, pronto da incollare."""
    metadata = metadata or {}
    genre = genre or ("enigmi" if spec.genre == "puzzle" else spec.genre)
    copy = copy or coverdesign.derive_copy(spec, metadata, genre, pages=pages)
    palette = coverdesign.pick_palette(spec, genre)

    trim_w, trim_h = kdpspecs.trim_size_in(spec.trim)
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
  its capital height must reach at least {coverdesign.MIN_TITLE_CAP_RATIO:.0%} of the
  cover height ({coverdesign.GOOD_TITLE_CAP_RATIO:.0%} is where it becomes dominant),
  on at most {coverdesign.MAX_TITLE_LINES} lines.
- Contrast between title and background of at least {coverdesign.MIN_CONTRAST:.0f}:1.
- The background must separate from the white search page: avoid pale, washed
  backgrounds that dissolve into it.
- At most {coverdesign.MAX_TOP_ELEMENTS} text blocks in the upper half.
- Exactly ONE unique factor. It must aid recognition without competing with the title.
- Intentional negative space; no clutter, no decorative filler.
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

So: leave the upper third of the composition calm and uncluttered. That is
where the title goes, and a busy area there costs the cover its contrast.

For reference only: the engine will set the following text, written in
{LANGUAGE_NAMES.get(spec.language, spec.language)} because that is the language
of the book. Read it to understand what the image has to support, and do not
render any of it.

{_lines([t for t in testi if t])}

## Production specification — PAPERBACK

- Trim size: {spec.trim} in ({trim_w}" x {trim_h}"), {pages} pages, {spec.paper} paper.
- Front cover alone, at {FRONT_DPI} DPI: {round(trim_w * FRONT_DPI)} x {round(trim_h * FRONT_DPI)} px.
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

- ONE single PDF, unlocked, with back + spine + front in one continuous image.
- Fonts embedded, images embedded, transparency and layers flattened.
- No crop marks, no trim marks, no colour bars, no template guides, no
  placeholder text, no comments or annotations, no hidden objects.
- No white border from a wrong bleed.
- Practical target under 40 MB (hard limit 650 MB).

## If the format is not paperback

- HARDCOVER: do not reuse these dimensions. Use the KDP hardcover template; the
  artwork must extend about 0.51" (15 mm) past the front cover edge for the wrap,
  and nothing important may sit near the hinge.
- EBOOK: front cover only, 2560 x 1600 px (ratio 1.6:1 or taller), RGB, JPEG or
  TIFF. Designed on its own, not cropped out of the wrap.

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
3. The title is readable at thumbnail size.
4. There is one dominant visual idea.
5. There is exactly one unique factor.
6. It does not look generic.
7. The hierarchy is obvious.
8. Nothing resembles a competitor's cover.
9. No trademark, logo, mascot or proprietary identity is used.
10. It looks like a commercially viable Amazon KDP cover.
"""

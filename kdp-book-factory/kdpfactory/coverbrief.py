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

CATEGORY SIGNAL -> BIG PROMISE -> VISUAL PROOF -> TYPOGRAPHIC HIERARCHY -> UNIQUE FACTOR

Formula for this category: {formula}
{priorita}

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

## Text on the cover

Written in {LANGUAGE_NAMES.get(spec.language, spec.language)} — the language of
the book. Do not translate these strings, and do not add any text that is not
listed here.

{_lines([t for t in testi if t])}

## Production specification

- Trim size: {spec.trim} in ({trim_w}" x {trim_h}"), {pages} pages, {spec.paper} paper.
- Front cover alone, at {FRONT_DPI} DPI: {round(trim_w * FRONT_DPI)} x {round(trim_h * FRONT_DPI)} px.
- Full wrap, if you produce one: {cover_w:.3f}" x {cover_h:.3f}" including a
  {kdpspecs.BLEED_IN}" bleed on every side, with a {spine:.3f}" spine.
- Keep all text at least {coverdesign.SAFE_MARGIN_IN}" away from every trimmed edge:
  KDP cuts up to 3 mm and what crosses that line is lost in print.
- No transparency, no colour profile other than the one you export; flatten before saving.

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

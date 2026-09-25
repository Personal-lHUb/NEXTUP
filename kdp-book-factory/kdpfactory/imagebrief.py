"""I prompt delle immagini dell'interno.

`coverbrief.py` scrive il brief di **una** immagine, la copertina, che deve
vendere. Questo modulo scrive i prompt delle immagini che stanno **dentro** il
libro, e il mestiere è un altro: non devono vendere, devono spiegare — e devono
farlo in bianco e nero, su carta, accanto a un testo che le ha già annunciate.

Da cui tre vincoli che la copertina non ha:

- **Niente colore che porti significato.** L'interno si stampa in grigio: se
  due elementi si distinguono solo perché uno è rosso e l'altro verde, sulla
  pagina sono la stessa cosa. Il prompt lo chiede in grigio fin da subito.
- **Coerenza fra le figure.** Venti immagini prodotte con venti prompt scollegati
  sembrano prese da venti libri. Il prompt porta una riga di stile comune,
  identica per tutte le figure dello stesso libro.
- **Niente testo dentro l'immagine.** Le etichette le compone la tipografia, che
  usa il font del libro e le può correggere; un'etichetta generata è pixel, e
  quando ha un refuso si rifà l'immagine.

La forma è prosa descrittiva, perché è quella che i modelli conversazionali
eseguono meglio e l'unica che regge le istruzioni negative complesse. In coda
c'è il blocco dei parametri per gli strumenti che li vogliono: così il brief
resta valido anche cambiando strumento.
"""

from __future__ import annotations

from . import figure as figure_module
from . import kdpspecs
from .models import BookSpec

#: la lingua del brief: inglese, come per la copertina, perché è quella in cui
#: gli strumenti grafici sbagliano meno. Il libro resta nella sua.
LANGUAGE_NAMES = {"it": "Italian", "en": "English"}

#: lo stile di base per categoria di prodotto. Non è un gusto: un medium-content
#: mostra al cliente che cosa comprerà, un full-content illustra un argomento.
STILE_BASE = {
    "medium": (
        "Clean instructional line art: confident black strokes on white, no "
        "shading gradients, no background texture. It must stay legible when "
        "printed small on uncoated paper and photocopied by a reader."
    ),
    "full": (
        "Restrained editorial illustration in greyscale: one clear subject, "
        "generous white space, tonal range that survives black-and-white "
        "printing. Documentary rather than decorative."
    ),
}


def _stile(spec: BookSpec) -> str:
    return STILE_BASE["medium" if spec.content_type == "medium" else "full"]


def _dimensioni(spec: BookSpec) -> tuple[float, float, int, int]:
    """Larghezza stampata e pixel minimi per starci a 300 DPI."""
    geo = kdpspecs.page_geometry(spec.trim, spec.target_pages)
    larghezza_in = geo.text_width / kdpspecs.INCH
    altezza_in = larghezza_in * 0.75
    return (
        larghezza_in,
        altezza_in,
        round(larghezza_in * figure_module.MIN_DPI),
        round(altezza_in * figure_module.MIN_DPI),
    )


def brief(spec: BookSpec, figure: list[figure_module.Figura]) -> str:
    """Il documento con tutti i prompt delle figure di questo libro."""
    larghezza_in, altezza_in, px_w, px_h = _dimensioni(spec)
    lingua = LANGUAGE_NAMES.get(spec.language, spec.language)
    mancanti = [f for f in figure if not f.esiste]

    testa = f"""# Prompt delle immagini — {spec.title}

<!-- Prodotto da `kdpfactory immagini {spec.slug}`. Un prompt per ogni figura
     dichiarata nel manoscritto. L'immagine che torna si salva nel percorso
     indicato sotto ciascun prompt: da lì `build` la impagina, la converte in
     scala di grigi e ne verifica i DPI. -->

{len(figure)} figure dichiarate, {len(mancanti)} ancora da produrre.

## Regole comuni a tutte le figure di questo libro

Queste valgono per ogni prompt qui sotto. Ripetile allo strumento se lavori una
figura per volta e lo strumento non tiene il contesto.

- **Greyscale only.** This book's interior prints in black and white. Produce
  the image in greyscale from the start; never rely on colour to distinguish
  two elements, because on the page they become the same grey.
- **No text inside the image.** No labels, captions, numbers, letters,
  handwriting or signage. The book sets its own labels in its own typeface.
- **One subject.** The image explains one thing. A second subject competing for
  attention makes the reader look for a relationship that the text does not
  claim.
- **Room to breathe.** Generous white space; the image sits between paragraphs,
  not on a poster.
- **Consistent style across all figures.** {_stile(spec)}
- **Original work.** Do not imitate an existing illustrator, photographer,
  character, brand or copyrighted image. No recognisable real people, no
  trademarks, no logos.

## Production specification, identical for every figure

- Printed width: {larghezza_in:.2f}" (the text measure of a {spec.trim} page).
- Minimum pixels: {px_w} x {px_h} px, which is {figure_module.MIN_DPI} DPI at
  that printed width. Bigger is fine; upscaled is not — the check measures the
  real pixels.
- Greyscale, no transparency, no alpha channel.
- No border, no frame, no drop shadow: the page provides the margin.
- The book's own language is {lingua}, but there is no text in these images,
  so nothing to translate.
"""

    corpo = [_prompt_figura(spec, index, f, larghezza_in, altezza_in, px_w, px_h)
             for index, f in enumerate(figure, start=1)]

    coda = f"""
## Parameter block, if your tool wants one

The prompts above are written as prose because that is what conversational
models execute best. If you are pasting into a tool that takes parameters,
append the line for that tool:

- Midjourney: `--ar 4:3 --style raw --no text, letters, watermark, signature, border`
- Flux / Ideogram: aspect ratio 4:3, rendering style «photographic» or
  «illustration» per the style line above, negative prompt
  `text, letters, watermark, signature, frame, colour`
- Stable Diffusion: negative prompt
  `text, watermark, signature, border, colour, oversaturated, blurry`

Whatever the tool, the output must land at {px_w} px wide or more.

## When the images come back

Save each one at the path given under its prompt, then:

```bash
python3 -m kdpfactory build {spec.slug}
python3 -m kdpfactory qa {spec.slug}
```

`build` impagina le figure e le converte in scala di grigi; `qa` verifica che
ci siano tutte, che stiano sopra i {figure_module.MIN_DPI} DPI alla misura
stampata e segnala quelle ancora a colori. Il conteggio pagine non cambia
quando le immagini arrivano: il segnaposto occupava già il loro spazio.
"""
    return testa + "\n" + "\n".join(corpo) + coda


def _prompt_figura(
    spec: BookSpec,
    indice: int,
    figura: figure_module.Figura,
    larghezza_in: float,
    altezza_in: float,
    px_w: int,
    px_h: int,
) -> str:
    stato = "già prodotta" if figura.esiste else "da produrre"
    dove = f"capitolo {figura.capitolo}" if figura.capitolo else "libro"
    didascalia = (
        f"\nThe book prints this caption underneath, so the image must not "
        f"repeat it: «{figura.didascalia}»"
        if figura.didascalia
        else ""
    )
    return f"""
---

### Figura {indice} — {dove} · {stato}

**Salvala in:** `books/{spec.slug}/assets/{figura.percorso}`

```
{figura.descrizione}

Greyscale illustration for the interior of a printed book. One subject, plenty
of white space, no text or lettering anywhere in the image, no border or frame.
{_stile(spec)}
Composition sized for {larghezza_in:.2f} x {altezza_in:.2f} inches at
{figure_module.MIN_DPI} DPI, so at least {px_w} x {px_h} pixels.
```
{didascalia}
"""

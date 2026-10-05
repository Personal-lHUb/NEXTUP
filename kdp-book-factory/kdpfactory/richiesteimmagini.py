"""Le richieste di immagini per Cowork, ruolo «immagini», con il prompt del sistema dentro.

La regola resta quella di sempre: ogni immagine nasce da un prompt scritto da
un comando (`copertina`, `immagini`), non in chat. Cambia chi la genera: non più
l'autore a mano, ma Cowork con ChatGPT, dal portatile. Qui il prompt diventa una
richiesta completa: che cosa incollare, quante varianti, quanto grande, e con
che nome lasciare ogni file sul corriere perché arrivi da solo in `assets/`.

La scelta fra le varianti della copertina resta una decisione dell'autore: la
propone l'agente copertina dopo averle misurate, e vale il silenzio-assenso.
"""

from __future__ import annotations

import re

from . import cowork

RUOLO = "immagini"
COPERTINA = "cowork-copertina.md"
FIGURE = "cowork-figure.md"
VARIANTI = 3


def _senza_commenti(testo: str) -> str:
    return re.sub(r"<!--.*?-->", "", testo, flags=re.S).strip()


def nome_variante(slug: str, numero: int) -> str:
    """Il nome su Drive della variante `numero` della copertina: arriva in assets/."""
    return f"books__{slug}__assets__copertina-{numero}.png"


def copertina(
    slug: str, titolo: str, brief: str, minimo_px: tuple[int, int], canale: dict, varianti: int = VARIANTI
) -> tuple[str, str]:
    """La richiesta dell'illustrazione di copertina, con il brief di `copertina <slug>` dentro."""
    larghezza, altezza = minimo_px
    nomi = "\n".join(f"   - `{nome_variante(slug, i)}`" for i in range(1, varianti + 1))
    corpo = (
        cowork.intestazione(
            f"Cowork · illustrazione di copertina — {slug}",
            COPERTINA.replace(".md", "-risposta.md"),
            RUOLO,
            canale,
            f"books/{slug}/manuale",
        )
        + f"\nIl libro: «{titolo}». Serve l'illustrazione della prima di copertina: solo\n"
        "l'immagine, senza nessun testo. Titolo, sottotitolo e autore li compone la\n"
        "fabbrica sopra l'immagine.\n\n"
        f"1. **Genera.** In ChatGPT incolla il prompt qui sotto, fra le due righe `---`,\n"
        "   così com'è. Formato verticale 2:3, alla risoluzione più alta che consente.\n"
        f"2. **Varianti.** Generane {varianti}, diverse fra loro nella composizione, e\n"
        "   salvale nella cartella del corriere con questi nomi:\n"
        f"{nomi}\n"
        f"3. **Misure.** Per ogni variante, le misure in pixel. Il minimo per la stampa\n"
        f"   è {larghezza} x {altezza}: se l'immagine è più piccola, consegnala lo stesso\n"
        "   e scrivilo.\n"
        "4. **Strumento.** Con quale strumento e modello le hai generate (KDP chiede di\n"
        "   dichiarare le immagini fatte con l'IA), e se ChatGPT ha rifiutato o\n"
        "   cambiato qualcosa del prompt.\n\n"
        "---\n"
        f"{_senza_commenti(brief)}\n"
        "---\n\n"
        "Chi usa i risultati: l'agente `copertina`, che misura le varianti e propone\n"
        "all'autore quella da usare. La applica la sessione della fabbrica.\n"
    )
    return COPERTINA, corpo


def figure(slug: str, titolo: str, brief: str, percorsi: list[str], canale: dict) -> tuple[str, str]:
    """La richiesta delle figure dell'interno, con il brief di `immagini <slug>` dentro."""
    nomi = "\n".join(
        f"   - `{p}` → nella cartella come `{('books/' + slug + '/assets/' + p).replace('/', '__')}`"
        for p in percorsi
    )
    corpo = (
        cowork.intestazione(
            f"Cowork · figure dell'interno — {slug}",
            FIGURE.replace(".md", "-risposta.md"),
            RUOLO,
            canale,
            f"books/{slug}/manuale",
        )
        + f"\nIl libro: «{titolo}». L'interno si stampa in bianco e nero: le figure si\n"
        "generano già in scala di grigi, e nessuna contiene testo.\n\n"
        "1. **Genera.** In ChatGPT, una figura alla volta, incolla il prompt di quella\n"
        "   figura dal brief qui sotto, così com'è, alla risoluzione più alta.\n"
        "2. **Salva.** Ogni figura nella cartella del corriere, con il nome indicato:\n"
        f"{nomi}\n"
        "3. **Misure e strumento.** Per ogni figura le misure in pixel; per tutte, lo\n"
        "   strumento e il modello usati.\n\n"
        "---\n"
        f"{_senza_commenti(brief)}\n"
        "---\n\n"
        "Chi usa i risultati: l'impaginazione, che mette ogni figura al suo posto, e\n"
        "il controllo qualità, che ne misura i DPI sulla misura stampata.\n"
    )
    return FIGURE, corpo

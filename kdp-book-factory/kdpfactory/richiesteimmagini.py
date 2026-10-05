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

#: Il progetto ChatGPT dove nascono le immagini: le regole fisse nelle sue
#: istruzioni, il brief di ogni lavoro allegato alla sua chat.
PROGETTO_CHATGPT = "NEXTUP — Immagini"
#: I file da allegare in ChatGPT, accanto ai brief in build/.
CHATGPT_COPERTINA = "copertina-chatgpt.md"
CHATGPT_FIGURE = "immagini-chatgpt.md"

#: Le regole uguali per ogni libro. In inglese, come i brief: è la lingua in cui
#: il generatore le segue meglio, e l'autore non deve tradurle.
ISTRUZIONI_CHATGPT = """\
You make the illustrations for books produced by the NEXTUP book factory: front
cover art and interior figures for paperback books sold on Amazon KDP.

Every chat in this project is one job for one book. The brief for that job is
the file attached to the first message. Follow that brief, and do not carry over
the style, palette or subject of another chat unless the brief asks for it.

Rules for every image:
1. Illustration only. No text of any kind in the image: no title, letters,
   numbers, labels, signatures, logos or watermarks. The book's own software
   sets every word afterwards, in vector.
2. Use the brief as the prompt, as written. Do not rewrite it into a prompt of
   your own. If something in it cannot be done, say so before generating,
   instead of changing it silently.
3. Covers: portrait 2:3, at the largest size you can produce. Keep the upper
   third calm: the title goes there.
4. Interior figures: grayscale only. Two elements must never differ by colour
   alone, because the book prints in black and white.
5. Originality: never imitate an existing book cover, artist, character, brand
   or logo, and never show a recognisable real person.
6. One image per message. When the brief asks for several variants, make them
   differ in composition, not just in colour.
7. After every image, state its exact size in pixels and the model that made
   it: Amazon asks authors to disclose AI-generated content. If the image is
   smaller than the minimum in the brief, deliver it anyway and say so."""


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


# --------------------------------------------------------------------------
# ChatGPT: il file da allegare alla chat e le istruzioni del progetto
# --------------------------------------------------------------------------
def chatgpt_copertina(
    slug: str, titolo: str, brief: str, minimo_px: tuple[int, int], varianti: int = VARIANTI
) -> str:
    """Il file da allegare in una chat del progetto ChatGPT: il lavoro, poi il brief così com'è.

    È lo stesso brief della richiesta a Cowork, senza i commenti per la sessione:
    chi lo allega, l'autore o Cowork, ottiene le stesse immagini.
    """
    larghezza, altezza = minimo_px
    nomi = "\n".join(f"- variant {i}: `{nome_variante(slug, i)}`" for i in range(1, varianti + 1))
    return (
        f"# Cover illustration — {titolo}\n\n"
        f"This file is the brief for one job: the front cover illustration of «{titolo}».\n\n"
        "What to do:\n"
        "1. Use the brief below, between the two `---` lines, as the prompt, as written.\n"
        f"2. Make {varianti} variants, one per message, different from each other in composition.\n"
        f"3. Portrait 2:3, at the largest size you can produce. The print minimum is {larghezza} x\n"
        f"   {altezza} px: if your image is smaller, deliver it anyway and say so.\n"
        "4. After each image: its size in pixels, the model that made it, and whether you had to\n"
        "   refuse or change anything in the brief.\n"
        "5. No text anywhere in the image.\n\n"
        "---\n"
        f"{_senza_commenti(brief)}\n"
        "---\n\n"
        "File names, for whoever saves the variants in the factory's Drive folder:\n"
        f"{nomi}\n"
    )


def chatgpt_figure(slug: str, titolo: str, brief: str, percorsi: list[str]) -> str:
    """Il file da allegare per le figure dell'interno: una figura per messaggio, in scala di grigi."""
    nomi = "\n".join(f"- `{p}` → `{('books/' + slug + '/assets/' + p).replace('/', '__')}`" for p in percorsi)
    return (
        f"# Interior figures — {titolo}\n\n"
        f"This file is the brief for one job: the interior figures of «{titolo}», which prints in\n"
        "black and white.\n\n"
        "What to do:\n"
        "1. One figure per message, in the order of the brief below. Use each figure's prompt as\n"
        "   written.\n"
        "2. Grayscale only, no text in the image, at the largest size you can produce.\n"
        "3. After each figure: its size in pixels and the model that made it.\n\n"
        "---\n"
        f"{_senza_commenti(brief)}\n"
        "---\n\n"
        "File names, for whoever saves the figures in the factory's Drive folder:\n"
        f"{nomi}\n"
    )


def progetto_chatgpt(canale: dict) -> str:
    """Il testo per creare in ChatGPT il progetto delle immagini, e come usarlo libro per libro."""
    cartella, _ = cowork.corriere(canale)
    return "\n".join([
        f"# Il progetto ChatGPT — {PROGETTO_CHATGPT}",
        "",
        "<!-- Scritto da `python3 -m kdpfactory cowork progetto`. Non si modifica a mano:",
        "     le regole stanno in kdpfactory/richiesteimmagini.py, e si rigenera. -->",
        "",
        "Un progetto in ChatGPT per tutte le immagini dei libri NEXTUP. Le regole che",
        "valgono per ogni libro stanno nelle istruzioni del progetto, scritte una volta.",
        "Il brief di ogni lavoro arriva come file allegato alla sua chat, e lo scrive il",
        "sistema: il prompt di un'immagine non si scrive a mano.",
        "",
        "## 1. Il progetto",
        "",
        f"Nome: **{PROGETTO_CHATGPT}**. Istruzioni del progetto, da incollare così:",
        "",
        "```",
        ISTRUZIONI_CHATGPT,
        "```",
        "",
        "- **Memoria**: se ChatGPT chiede quale usare, quella limitata al progetto. Un",
        "  libro non deve prendere lo stile di un altro.",
        "- **File del progetto**: nessuno. Il brief va allegato alla chat del suo libro:",
        "  caricato nei file del progetto lo vedrebbero tutte le chat, e due libri si",
        "  mescolerebbero.",
        "",
        "## 2. Una chat per lavoro",
        "",
        "| lavoro | nome della chat | file da allegare | lo scrive |",
        "|---|---|---|---|",
        f"| copertina | `<slug> — copertina` | `books/<slug>/build/{CHATGPT_COPERTINA}` "
        "| `kdpfactory copertina <slug>` |",
        f"| figure dell'interno | `<slug> — figure` | `books/<slug>/build/{CHATGPT_FIGURE}` "
        "| `kdpfactory immagini <slug>` |",
        "",
        "Primo messaggio, con il file allegato: «Follow the attached brief. First variant.»",
        "Poi, per ogni variante: «Next variant.» Per le figure: «Next figure.»",
        "",
        "## 3. Dove vanno le immagini",
        "",
        "Ogni immagine si scarica alla risoluzione piena (non l'anteprima) e si salva",
        f"nella cartella Drive «{cartella}», con il nome che il file allegato indica in",
        "fondo, per esempio `books__<slug>__assets__copertina-1.png`. Il giro orario la",
        "porta nel libro da sola; l'agente `copertina` misura le varianti e propone",
        "quella da usare, con il silenzio-assenso.",
        "",
        "## 4. Cowork",
        "",
        "Il ruolo `immagini` di Cowork lavora nello stesso progetto, se c'è: lo dice il",
        "LEGGIMI. Che la copertina la generi l'autore o Cowork, il file allegato è lo",
        "stesso, e vale la prima serie di varianti che arriva sul corriere.",
        "",
    ])

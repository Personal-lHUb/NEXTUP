"""Le richieste di immagini per Cowork, ruolo «immagini», con il prompt del sistema dentro.

La regola resta quella di sempre: ogni immagine nasce da un prompt scritto da
un comando (`copertina`, `immagini`), non in chat. Cambia chi la genera: non più
l'autore a mano, ma Cowork con ChatGPT, dal portatile. Qui il prompt diventa una
richiesta completa: che cosa incollare, quante varianti, quanto grande, e dove
caricare ogni file perché arrivi da solo in `assets/`.

Le immagini non viaggiano sul corriere di Drive: il connettore porta testo, non
file da qualche megabyte. Cowork le carica su GitHub, nel ramo
`cowork-immagini`, al percorso che la richiesta indica, e `cowork corriere
--dal-ramo` le porta nel libro. Per caricarle serve il GitHub dell'autore aperto
nel browser: le richieste lo dicono nella riga `Serve:`.

La scelta fra le varianti della copertina resta una decisione dell'autore: la
propone l'agente copertina dopo averle misurate, e vale il silenzio-assenso.
"""

from __future__ import annotations

from . import corriere, cowork

RUOLO = "immagini"
#: L'accesso che Cowork usa per consegnare: il GitHub dell'autore, nel browser.
SERVE_GITHUB = "l'accesso a GitHub (github.com, account dell'autore)"
COPERTINA = "cowork-copertina.md"
FIGURE = "cowork-figure.md"
VARIANTI = 3

#: Il progetto ChatGPT dove nascono le immagini: le regole fisse nelle sue
#: istruzioni, il prompt di ogni lavoro incollato nella sua chat.
PROGETTO_CHATGPT = "NEXTUP — Immagini"
#: Il testo da incollare in ChatGPT, accanto ai brief in build/: un file di
#: testo semplice, perché si copia e incolla così com'è.
CHATGPT_COPERTINA = "copertina-prompt.txt"
CHATGPT_FIGURE = "immagini-prompt.txt"

#: Il messaggio di ogni variante dopo la prima: stesso prompt, composizione nuova.
PROSSIMA_VARIANTE = (
    "Next variant. Same brief and same rules, but a clearly different composition: change "
    "the viewpoint, the framing or the arrangement of the scene, not just the colours. Then "
    "tell me its exact size in pixels and the model that made it."
)

#: Le regole uguali per ogni libro. In inglese, come i brief: è la lingua in cui
#: il generatore le segue meglio, e l'autore non deve tradurle.
ISTRUZIONI_CHATGPT = """\
You make the illustrations for books produced by the NEXTUP book factory: front
cover art and interior figures for paperback books sold on Amazon KDP.

Every chat in this project is one job for one book. The brief for that job is
the first message of the chat. Follow that brief, and do not carry over the
style, palette or subject of another chat unless the brief asks for it.

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


def _serve_chatgpt(canale: dict) -> str:
    if corriere.su_github(canale):
        return "l'accesso a ChatGPT (account dell'autore)"
    return "l'accesso a ChatGPT e a GitHub (account dell'autore)"


def percorso_variante(slug: str, numero: int) -> str:
    """Dove si carica la variante `numero` della copertina, sul ramo delle immagini."""
    return corriere.percorso_sul_ramo(f"books/{slug}/assets/copertina-{numero}.png")


def consegna(canale: dict) -> str:
    """Il punto di ogni richiesta d'immagini che dice dove caricarle: il ramo di GitHub."""
    repository = canale.get("repository", "Personal-lHUb/NEXTUP")
    if corriere.su_github(canale):
        return (
            f"   Caricale su GitHub, repository `{repository}`, ramo `{corriere.RAMO_IMMAGINI}`,\n"
            "   ognuna al percorso indicato. Con git (add_repo con accesso push, poi commit e\n"
            f"   push del solo ramo `{corriere.RAMO_IMMAGINI}`) o, se lavori col browser, con\n"
            "   «Add file → Upload files». Solo quei file: nessun altro ramo, nessuna pull\n"
            "   request, niente da unire o da cancellare.\n"
        )
    return (
        "   Non nella cartella Drive: il connettore non porta file così pesanti. Caricale\n"
        f"   su GitHub, repository `{repository}`, ramo `{corriere.RAMO_IMMAGINI}`, ognuna al\n"
        "   percorso indicato, con «Add file → Upload files». Se il ramo non c'è, crealo\n"
        "   dalla stessa pagina con «Create a new branch». Solo quei file: nessun altro\n"
        "   ramo, nessuna pull request, niente da unire o da cancellare.\n"
    )


def copertina(
    slug: str, titolo: str, prompt: str, minimo_px: tuple[int, int], canale: dict, varianti: int = VARIANTI
) -> tuple[str, str]:
    """La richiesta dell'illustrazione di copertina, con il prompt di `copertina <slug>` dentro.

    È lo stesso testo di `build/copertina-prompt.txt`: che la generi l'autore o
    Cowork, ChatGPT riceve le stesse parole.
    """
    larghezza, altezza = minimo_px
    nomi = "\n".join(f"   - `{percorso_variante(slug, i)}`" for i in range(1, varianti + 1))
    corpo = (
        cowork.intestazione(
            f"Cowork · illustrazione di copertina — {slug}",
            COPERTINA.replace(".md", "-risposta.md"),
            RUOLO,
            canale,
            f"books/{slug}/manuale",
            serve=_serve_chatgpt(canale),
        )
        + f"\nIl libro: «{titolo}». Serve l'illustrazione della prima di copertina: solo\n"
        "l'immagine, senza nessun testo. Titolo, sottotitolo e autore li compone la\n"
        "fabbrica sopra l'immagine.\n\n"
        f"1. **Genera.** In ChatGPT incolla il prompt qui sotto, fra le due righe `---`,\n"
        "   così com'è. Formato verticale 2:3, alla risoluzione più alta che consente.\n"
        f"2. **Varianti.** Generane {varianti}, una per messaggio. Dopo la prima, nella\n"
        f"   stessa chat scrivi: «{PROSSIMA_VARIANTE}»\n"
        "   Scaricale a piena risoluzione e caricale con questi percorsi:\n"
        f"{nomi}\n"
        + consegna(canale)
        +
        f"3. **Misure.** Per ogni variante, le misure in pixel. Il minimo per la stampa\n"
        f"   è {larghezza} x {altezza}: se l'immagine è più piccola, consegnala lo stesso\n"
        "   e scrivilo.\n"
        "4. **Strumento.** Con quale strumento e modello le hai generate (KDP chiede di\n"
        "   dichiarare le immagini fatte con l'IA), e se ChatGPT ha rifiutato o\n"
        "   cambiato qualcosa del prompt.\n\n"
        "---\n"
        f"{prompt.strip()}\n"
        "---\n\n"
        "Chi usa i risultati: l'agente `copertina`, che misura le varianti e propone\n"
        "all'autore quella da usare. La applica la sessione della fabbrica.\n"
    )
    return COPERTINA, corpo


SCARICA = "cowork-immagini-scarica.md"


def scaricamento(
    slug: str, titolo: str, immagini: list[tuple[str, str]], canale: dict, seguito: int = 0
) -> tuple[str, str]:
    """La richiesta a Cowork di portare nel libro immagini già generate.

    Higgsfield genera dal suo connettore, ma la rete del container non raggiunge
    la CDN dove mette i file: le immagini esistono a un indirizzo pubblico, e
    serve solo che qualcuno le scarichi e le carichi sul ramo delle immagini al
    percorso giusto. `immagini` è l'elenco (nome del file in assets/, indirizzo);
    `seguito` dà il nome di un seguito (`-2`, `-3`) della stessa richiesta.
    """
    nome = SCARICA if not seguito else SCARICA.replace(".md", f"-{seguito}.md")
    righe = "\n".join(
        f"   - `{corriere.percorso_sul_ramo(f'books/{slug}/assets/{file}')}` ← {url}"
        for file, url in immagini
    )
    corpo = (
        cowork.intestazione(
            f"Cowork · immagini da scaricare — {slug}",
            nome.replace(".md", "-risposta.md"),
            RUOLO,
            canale,
            f"books/{slug}/manuale",
            # Sul canale GitHub Cowork consegna con git dal suo container: nessun
            # accesso da aprire nel browser.
            serve="" if corriere.su_github(canale) else SERVE_GITHUB,
        )
        + f"\nIl libro: «{titolo}». Le immagini sono già generate (Higgsfield, dal prompt della\n"
        "fabbrica): non c'è niente da generare né da incollare in ChatGPT.\n\n"
        "1. **Scarica e carica.** Apri ogni indirizzo, scarica il file così com'è e\n"
        "   caricalo al percorso indicato:\n"
        f"{righe}\n"
        + consegna(canale)
        + "   Non ritagliarlo, non comprimerlo, non convertirlo: la fabbrica misura i pixel veri.\n"
        "2. **Misure.** Per ogni file, le misure in pixel e il peso, e il link del commit.\n\n"
        "Chi usa i risultati: l'agente `copertina`, che misura le varianti e propone\n"
        "all'autore quella da usare. La applica la sessione della fabbrica.\n"
    )
    return nome, corpo


def percorso_figura(slug: str, percorso: str) -> str:
    """Dove si carica una figura dell'interno, sul ramo delle immagini: il suo posto in assets/."""
    return corriere.percorso_sul_ramo(f"books/{slug}/assets/{percorso}")


def figure(
    slug: str, titolo: str, prompts: list[tuple[str, str]], canale: dict
) -> tuple[str, str]:
    """La richiesta delle figure dell'interno: per ognuna il nome e il prompt da incollare.

    `prompts` è l'elenco (percorso in assets/, prompt), lo stesso di
    `build/immagini-prompt.txt`.
    """
    sezioni = "\n\n".join(
        f"**Figura {i}** — caricala come `{percorso_figura(slug, percorso)}`\n\n"
        f"---\n{prompt.strip()}\n---"
        for i, (percorso, prompt) in enumerate(prompts, start=1)
    )
    corpo = (
        cowork.intestazione(
            f"Cowork · figure dell'interno — {slug}",
            FIGURE.replace(".md", "-risposta.md"),
            RUOLO,
            canale,
            f"books/{slug}/manuale",
            serve=_serve_chatgpt(canale),
        )
        + f"\nIl libro: «{titolo}». L'interno si stampa in bianco e nero: le figure si\n"
        "generano già in scala di grigi, e nessuna contiene testo.\n\n"
        "1. **Genera.** In ChatGPT, una figura per messaggio, incolla il prompt di quella\n"
        "   figura, fra le sue due righe `---`, così com'è, alla risoluzione più alta.\n"
        "2. **Carica.** Ogni figura a piena risoluzione, al percorso indicato sopra il suo\n"
        "   prompt.\n"
        + consegna(canale)
        +
        "3. **Misure e strumento.** Per ogni figura le misure in pixel; per tutte, lo\n"
        "   strumento e il modello usati.\n\n"
        f"{sezioni}\n\n"
        "Chi usa i risultati: l'impaginazione, che mette ogni figura al suo posto, e\n"
        "il controllo qualità, che ne misura i DPI sulla misura stampata.\n"
    )
    return FIGURE, corpo


# --------------------------------------------------------------------------
# ChatGPT: il testo da incollare nella chat e le istruzioni del progetto
# --------------------------------------------------------------------------
def _riga(testo: str) -> str:
    return f"=== {testo} ==="


def testo_copertina(slug: str, prompt: str, varianti: int = VARIANTI) -> str:
    """Il file da cui si copia e incolla: il prompt, il messaggio delle varianti, i nomi.

    Le righe `===` sono per chi copia e non vanno incollate: dicono che cosa
    incollare e dove. Fra una riga e l'altra c'è solo testo per ChatGPT.
    """
    nomi = "\n".join(f"variante {i}: {percorso_variante(slug, i)}" for i in range(1, varianti + 1))
    return (
        _riga(f"1 · Incolla questo in una chat nuova del progetto ChatGPT «{PROGETTO_CHATGPT}», "
              f"chiamata «{slug} — copertina»")
        + f"\n\n{prompt.strip()}\n\n"
        + _riga(f"2 · Per ognuna delle altre {varianti - 1} varianti, incolla questo nella stessa chat")
        + f"\n\n{PROSSIMA_VARIANTE}\n\n"
        + _riga(f"3 · Scarica ogni immagine a piena risoluzione e caricala su GitHub, ramo "
                f"{corriere.RAMO_IMMAGINI}, con questi percorsi")
        + f"\n\n{nomi}\n"
    )


def testo_figure(slug: str, prompts: list[tuple[str, str]]) -> str:
    """Il file da cui si copiano i prompt delle figure: uno per messaggio, ognuno col suo nome."""
    pezzi = [
        _riga(f"Le figure vanno in una chat nuova del progetto ChatGPT «{PROGETTO_CHATGPT}», "
              f"chiamata «{slug} — figure»: un messaggio per figura")
    ]
    for i, (percorso, prompt) in enumerate(prompts, start=1):
        pezzi.append(
            _riga(f"Figura {i} · incolla questo, poi carica l'immagine su GitHub, ramo "
                  f"{corriere.RAMO_IMMAGINI}, come {percorso_figura(slug, percorso)}")
            + f"\n\n{prompt.strip()}"
        )
    return "\n\n".join(pezzi) + "\n"


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
        "Il prompt di ogni lavoro si incolla nella sua chat, e lo scrive il sistema: il",
        "prompt di un'immagine non si scrive a mano.",
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
        "- **File del progetto**: nessuno. Il prompt va nella chat del suo libro: caricato",
        "  nei file del progetto lo vedrebbero tutte le chat, e due libri si mescolerebbero.",
        "",
        "## 2. Una chat per lavoro",
        "",
        "| lavoro | nome della chat | testo da incollare | lo scrive |",
        "|---|---|---|---|",
        f"| copertina | `<slug> — copertina` | `books/<slug>/build/{CHATGPT_COPERTINA}` "
        "| `kdpfactory copertina <slug>` |",
        f"| figure dell'interno | `<slug> — figure` | `books/<slug>/build/{CHATGPT_FIGURE}` "
        "| `kdpfactory immagini <slug>` |",
        "",
        "Il file è testo semplice, diviso da righe `===` che dicono che cosa incollare e",
        "dove; le righe `===` non si incollano. Per la copertina:",
        "",
        "1. in una chat nuova si incolla il prompt della prima variante;",
        f"2. per ogni altra variante, nella stessa chat: «{PROSSIMA_VARIANTE}»",
        "",
        "Per le figure, una chat sola e un messaggio per figura, ognuno col suo prompt.",
        "Ogni prompt di figura ripete il grigio e il divieto di testo: si possono",
        "incollare anche a giorni di distanza.",
        "",
        "Lo stesso testo lo stampa il comando nel terminale, pronto da copiare.",
        "",
        "## 3. Dove vanno le immagini",
        "",
        "Ogni immagine si scarica alla risoluzione piena (non l'anteprima) e si carica",
        f"su GitHub, nel ramo `{corriere.RAMO_IMMAGINI}`, al percorso che il file indica, per",
        "esempio `kdp-book-factory/books/<slug>/assets/copertina-1.png`. Non nella",
        f"cartella Drive «{cartella}»: lì viaggiano solo richieste e risposte, perché il",
        "connettore non porta file così pesanti. Il giro orario porta l'immagine nel",
        "libro da sola; l'agente `copertina` misura le varianti e propone quella da",
        "usare, con il silenzio-assenso.",
        "",
        "## 4. Cowork",
        "",
        "Il ruolo `immagini` di Cowork lavora nello stesso progetto, se c'è: lo dice il",
        "LEGGIMI. Che la copertina la generi l'autore o Cowork, il prompt è lo stesso,",
        "parola per parola, e vale la prima serie di varianti che arriva sul ramo.",
        "",
    ])

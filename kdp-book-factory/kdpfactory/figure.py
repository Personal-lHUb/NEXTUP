"""Le immagini dentro il libro: dove vanno, quanto devono pesare, che cosa le rifiuta.

`coverimage.py` prepara l'immagine di copertina, che è una sola e sta fuori dal
testo. Questo modulo si occupa dell'altra metà: le figure **dentro** il
manoscritto, che sono molte, stanno in mezzo ai capoversi e hanno vincoli di
stampa diversi.

Tre cose che valgono solo qui:

- **L'interno si stampa in bianco e nero.** Un'immagine a colori caricata così
  com'è viene convertita dalla tipografia, e il risultato lo vedi a libro
  stampato: due colori che a schermo si distinguono benissimo, in grigio
  diventano la stessa tacca. Qui si converte prima e si dice che è successo.
- **I 300 DPI sono sulla misura stampata**, non sul file. Un'immagine di 900
  pixel è magnifica a 3 pollici e inaccettabile a 5: il conto si fa sulla
  larghezza che l'immagine avrà in pagina.
- **Il posto viene prima dell'immagine.** Nel manoscritto la figura si dichiara
  con quello che deve mostrare; il file può non esistere ancora. Così il libro
  si impagina dal primo giorno, il conteggio pagine tiene già il posto, e
  `immagini` sa che prompt scrivere. Quello che manca lo dice il controllo
  qualità, che è il suo mestiere.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import kdpspecs, mdlite

#: risoluzione minima sulla misura stampata: sotto, KDP segnala in preflight
MIN_DPI = 300
#: quanto può essere alta una figura rispetto alla gabbia, prima di diventare
#: una pagina a sé: oltre, si porta dietro un buco di testo
ALTEZZA_MASSIMA = 0.58
#: una figura più stretta della misura non si allarga mai oltre il suo naturale
LARGHEZZA_MASSIMA = 1.0
#: dove vivono le figure dentro `books/<slug>/assets/`
CARTELLA = "immagini"


@dataclass
class Figura:
    """Una figura del manoscritto, risolta contro i file che esistono davvero."""

    descrizione: str
    percorso: str
    didascalia: str = ""
    capitolo: int = 0
    file: Path | None = None
    larghezza_px: int = 0
    altezza_px: int = 0
    a_colori: bool = False

    @property
    def esiste(self) -> bool:
        return self.file is not None and self.file.exists()

    @property
    def proporzione(self) -> float:
        """Larghezza / altezza. Senza file si assume 4:3, che è la forma più
        comune e tiene un posto credibile nel conteggio pagine."""
        if self.larghezza_px and self.altezza_px:
            return self.larghezza_px / self.altezza_px
        return 4 / 3

    def dpi_a(self, larghezza_pt: float) -> int:
        """La risoluzione effettiva alla larghezza con cui verrà stampata."""
        pollici = larghezza_pt / kdpspecs.INCH
        if not self.larghezza_px or pollici <= 0:
            return 0
        return int(self.larghezza_px / pollici)

    def to_dict(self) -> dict:
        return {
            "capitolo": self.capitolo,
            "descrizione": self.descrizione,
            "percorso": self.percorso,
            "didascalia": self.didascalia,
            "esiste": self.esiste,
            "pixel": [self.larghezza_px, self.altezza_px],
            "a_colori": self.a_colori,
        }


def cartella(assets_dir: Path) -> Path:
    return Path(assets_dir) / CARTELLA


def risolvi(blocco: mdlite.Figure, assets_dir: Path, capitolo: int = 0) -> Figura:
    """Dalla dichiarazione nel manoscritto alla figura, con le misure del file.

    Il percorso si legge relativo ad `assets/`: un manoscritto non deve
    contenere percorsi assoluti, o smette di funzionare sul computer di
    chiunque altro.
    """
    figura = Figura(
        descrizione=blocco.descrizione,
        percorso=blocco.percorso,
        didascalia=blocco.didascalia,
        capitolo=capitolo,
    )
    candidato = Path(assets_dir) / blocco.percorso
    if not candidato.exists():
        candidato = cartella(assets_dir) / Path(blocco.percorso).name
    if not candidato.exists():
        return figura

    figura.file = candidato
    try:
        from PIL import Image
    except ImportError:  # pragma: no cover - Pillow è una dipendenza del progetto
        return figura
    try:
        with Image.open(candidato) as immagine:
            figura.larghezza_px, figura.altezza_px = immagine.size
            figura.a_colori = immagine.mode not in {"L", "1", "LA"}
    except OSError:
        figura.file = None
    return figura


def figure_del_manoscritto(markdown: str, assets_dir: Path, capitolo: int = 0) -> list[Figura]:
    return [
        risolvi(blocco, assets_dir, capitolo)
        for blocco in mdlite.parse(markdown)
        if isinstance(blocco, mdlite.Figure)
    ]


def misura(figura: Figura, larghezza_pt: float, altezza_gabbia_pt: float) -> tuple[float, float]:
    """Quanto grande va stampata: piena misura, ma mai oltre mezza gabbia.

    Una figura alta quanto la pagina non è una figura, è una tavola: si porta
    dietro il testo che le stava intorno e lascia un buco dove stava.
    """
    larghezza = larghezza_pt * LARGHEZZA_MASSIMA
    altezza = larghezza / figura.proporzione
    massimo = altezza_gabbia_pt * ALTEZZA_MASSIMA
    if altezza > massimo:
        altezza = massimo
        larghezza = altezza * figura.proporzione
    return larghezza, altezza


def prepara(figura: Figura, destinazione: Path) -> Path | None:
    """Converte in scala di grigi per la stampa in bianco e nero.

    Si scrive un file nuovo invece di toccare l'originale: l'originale è quello
    che l'autore ha ricevuto dallo strumento grafico, e va rigenerato solo
    rifacendo il prompt.
    """
    if not figura.esiste:
        return None
    if not figura.a_colori:
        return figura.file
    try:
        from PIL import Image
    except ImportError:  # pragma: no cover
        return figura.file
    destinazione.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(figura.file) as immagine:
        immagine.convert("L").save(destinazione)
    return destinazione


def problemi(figura: Figura, larghezza_pt: float) -> list[str]:
    """Quello che impedisce a questa figura di andare in stampa."""
    elenco: list[str] = []
    dove = f"capitolo {figura.capitolo}" if figura.capitolo else "il libro"
    if not figura.esiste:
        elenco.append(
            f"L'immagine «{figura.percorso}» dichiarata in {dove} non c'è ancora: "
            f"il libro si impagina con un segnaposto, ma non si carica."
        )
        return elenco

    dpi = figura.dpi_a(larghezza_pt)
    if dpi < MIN_DPI:
        elenco.append(
            f"«{figura.percorso}» in {dove} va in stampa a {dpi} DPI "
            f"({figura.larghezza_px} px su {larghezza_pt / kdpspecs.INCH:.2f} pollici): "
            f"il minimo è {MIN_DPI}. Serve l'immagine più grande, non ingrandita."
        )
    if figura.a_colori:
        elenco.append(
            f"«{figura.percorso}» in {dove} è a colori e l'interno si stampa in "
            "bianco e nero: viene convertita, e due colori che a schermo si "
            "distinguono possono diventare lo stesso grigio. Controlla la prova."
        )
    return elenco


@dataclass
class Rapporto:
    """Che cosa c'è e che cosa manca, per chi deve produrre le immagini."""

    figure: list[Figura] = field(default_factory=list)

    @property
    def mancanti(self) -> list[Figura]:
        return [f for f in self.figure if not f.esiste]

    def to_dict(self) -> dict:
        return {
            "totale": len(self.figure),
            "mancanti": len(self.mancanti),
            "figure": [f.to_dict() for f in self.figure],
        }


# --------------------------------------------------------------------------
# Il piano delle figure: se servono, quali, da dove
# --------------------------------------------------------------------------
# Non tutti i libri hanno bisogno di figure, e una figura che non spiega niente
# costa pagine, DPI da verificare e una riga in più nella dichiarazione dell'IA.
# Il piano lo decide libro per libro l'architetto, insieme alla scaletta, e dice
# per ogni figura da dove viene: **generata** (dal prompt del sistema, in
# grigio, coerente con il mondo del libro) o **pubblica** — quando il contesto
# non lascia generarla: persone o luoghi reali da riconoscere, documenti,
# fatti storici, opere d'arte. Le pubbliche sono solo di pubblico dominio o
# CC0, e la loro provenienza resta scritta qui.

#: il piano, nella cartella del libro
PIANO = "figure.json"
FONTI = ("generata", "pubblica")
#: le licenze che una figura pubblica può avere: nessun obbligo di citazione,
#: nessun rischio con KDP (scelta dell'autore, 7 ottobre 2026)
LICENZE_AMMESSE = ("cc0", "pdm", "public domain")


def piano_path(root: Path) -> Path:
    return Path(root) / PIANO


def leggi_piano(root: Path) -> dict | None:
    import json

    try:
        return json.loads(piano_path(root).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def modello_piano() -> dict:
    return {
        "_nota": (
            "Il piano delle figure, deciso dall'architetto con la scaletta. `servono`: se il "
            "libro ha bisogno di figure; `perche`: perché sì o perché no, in italiano. "
            "`mondo`: in inglese, il mondo visivo comune a tutte le figure generate "
            "(ambiente, epoca, personaggi ricorrenti), perché siano coerenti con la trama. "
            "Per ogni figura: `percorso` (immagini/NN-nome.jpg, lo stesso del manoscritto), "
            "`capitolo`, `mostra` (che cosa deve mostrare), `perche` (che cosa spiega meglio "
            "del testo), `fonte` (generata | pubblica: pubblica solo quando il contesto non "
            "lascia generarla — persone o luoghi reali, documenti, fatti storici, opere "
            "d'arte) e, per le pubbliche, `cerca` (le parole da cercare negli archivi, in "
            "inglese). La `provenienza` la scrive il sistema quando prende l'immagine."
        ),
        "servono": None,
        "perche": "",
        "mondo": "",
        "figure": [],
    }


def licenza_ammessa(licenza: str) -> bool:
    valore = " ".join((licenza or "").lower().replace("-", " ").split())
    return any(valore == ammessa or valore.startswith(ammessa) for ammessa in LICENZE_AMMESSE) \
        or valore in {"cc0 1.0", "pdm 1.0", "public domain mark", "public domain mark 1.0"}


def voce_del_piano(piano: dict | None, percorso: str) -> dict | None:
    for voce in (piano or {}).get("figure") or []:
        suo = str(voce.get("percorso", ""))
        if suo == percorso or Path(suo).name == Path(percorso).name:
            return voce
    return None


def problemi_piano(piano: dict | None, figure: list[Figura],
                   generate: set[str] | None = None) -> list[tuple[str, str]]:
    """Le figure del manoscritto contro il piano: (gravità, problema).

    Senza piano si avvisa soltanto — i libri nati prima del piano esistono —,
    ma una figura pubblica senza una licenza ammessa è un errore: è
    l'immagine di qualcun altro stampata in un libro in vendita.
    """
    generate = generate or set()
    out: list[tuple[str, str]] = []
    if piano is None:
        if figure:
            out.append(("avviso", f"{len(figure)} figure nel manoscritto e nessun piano "
                                  f"({PIANO}): non si sa se servono né da dove vengono."))
        return out
    if piano.get("servono") is False and figure:
        out.append(("errore", f"Il piano dice che il libro non ha bisogno di figure, ma il "
                              f"manoscritto ne dichiara {len(figure)}: o il piano o il testo."))
    for figura in figure:
        voce = voce_del_piano(piano, figura.percorso)
        dove = f"capitolo {figura.capitolo}" if figura.capitolo else "il libro"
        if voce is None:
            if piano.get("servono") is not False:
                out.append(("avviso", f"«{figura.percorso}» in {dove} non è nel piano: non si sa "
                                      "se generarla o cercarla fra le immagini pubbliche."))
            continue
        fonte = voce.get("fonte")
        if fonte not in FONTI:
            out.append(("errore", f"«{figura.percorso}»: fonte «{fonte}», ammesse {', '.join(FONTI)}."))
            continue
        if fonte == "pubblica":
            provenienza = voce.get("provenienza") or {}
            if not voce.get("cerca") and not provenienza:
                out.append(("avviso", f"«{figura.percorso}» è da cercare fra le pubbliche, ma il "
                                      "piano non dice che cosa cercare (`cerca`)."))
            if figura.esiste and not licenza_ammessa(provenienza.get("licenza", "")):
                out.append(("errore", f"«{figura.percorso}» è un'immagine pubblica senza una "
                                      "licenza ammessa nel piano (solo pubblico dominio o CC0, "
                                      "con la sua provenienza): non si stampa."))
        elif figura.esiste and figura.percorso not in generate \
                and Path(figura.percorso).name not in {Path(g).name for g in generate}:
            out.append(("avviso", f"«{figura.percorso}» doveva essere generata, ma non risulta "
                                  "fra le immagini generate (build/immagini-generate.json): "
                                  "da dove viene?"))
    return out


def istruzioni_capitolo(piano: dict | None, numero: int) -> str:
    """Le figure che il piano mette in questo capitolo, da dichiarare nel testo.

    Il ghostwriter le scrive dove servono, con la riga che il sistema legge;
    il file non c'è ancora, e l'impaginazione tiene il posto.
    """
    voci = [v for v in (piano or {}).get("figure") or [] if v.get("capitolo") == numero]
    if not voci or (piano or {}).get("servono") is False:
        return ""
    righe = [
        "",
        "FIGURE DI QUESTO CAPITOLO",
        "Il piano delle figure ne mette qui " + ("una" if len(voci) == 1 else str(len(voci))) + ". "
        "Dichiarala nel punto del testo dove spiega, con questa riga esatta (il testo fra "
        "parentesi quadre dice che cosa mostra, la riga dopo fra parentesi è la didascalia "
        "che legge il lettore), e annunciala nel capoverso prima:",
    ]
    for voce in voci:
        righe.append(f"![{voce.get('mostra', '')}]({voce.get('percorso', '')})")
        righe.append("(una didascalia breve, nella lingua del libro)")
    return "\n".join(righe)

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

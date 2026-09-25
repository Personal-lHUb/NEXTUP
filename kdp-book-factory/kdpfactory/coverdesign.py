"""Sistema di copertine: le regole che decidono il clic, e come misurarle.

Su Amazon la copertina non viene mai vista come la vedi tu adesso. Viene vista
larga **160 pixel**, in mezzo ad altre venti, per meno di un secondo, su fondo
bianco. Tutto quello che non sopravvive a quella miniatura non esiste.

Da qui le sette regole che questo modulo applica e verifica:

1. **Un solo elemento dominante.** L'occhio ne mette a fuoco uno: se il titolo
   compete con un'immagine e con tre righe di sottotitolo, non vince nessuno.
2. **Titolo leggibile in miniatura.** Altezza delle maiuscole almeno il 6%
   dell'altezza della copertina — sotto quella soglia, a 160 px, il titolo è
   una macchia grigia. `audit()` la misura sul PDF vero.
3. **Contrasto reale.** Rapporto di contrasto fra titolo e fondo ≥ 7:1
   (la soglia AAA delle linee guida di accessibilità). Si calcola, non si valuta
   a occhio.
4. **Stacco dalla pagina.** La pagina dei risultati è bianca: un fondo scuro o
   molto saturo crea un bordo percettivo, un fondo chiaro si fonde e sparisce.
5. **Codice di genere in mezzo secondo.** Chi cerca enigmi cerca una griglia,
   chi cerca un metodo cerca una promessa. Il segno grafico dice *che libro è*
   prima che il titolo venga letto: si differenzia dentro il codice, non fuori.
6. **Un ciclo aperto.** Una domanda o una promessa incompleta genera la tensione
   che fa cliccare (è l'effetto Zeigarnik: l'incompiuto resta in testa).
7. **Numeri in cifre.** "13 CASES · 908 SUSPECTS" si legge in un colpo d'occhio;
   "tredici casi" va letto.

Le sette regole valgono per ogni libro. Quello che cambia con la **categoria di
prodotto** (CLAUDE.md) è che cosa si mette in copertina:

- **medium-content** — SEGNALE DI CATEGORIA + BENEFICIO + QUANTIFICATORE +
  GARANZIA. Prima la funzione: che prodotto è, per chi, quanto contiene. Il
  numero non è una scritta in piccolo, è parte del disegno — la banda d'accento
  in fondo alla prima esiste per quello.
- **full-content** — PROMESSA + MONDO + METAFORA VISIVA. Prima l'emozione: il
  titolo, un ciclo aperto, un'immagine che dice di che libro si tratta. Le
  specifiche da scaffale (numeri, garanzie, formato) qui non ci vanno: su
  un'opera a testo pieno raccontano il prodotto sbagliato.

Una cosa che questo modulo non fa, e non farà: finti timbri di bestseller,
stelline, recensioni o premi inventati. Oltre a essere vietati da KDP, sono
promesse che il libro non mantiene — e il reso arriva comunque. Per lo stesso
motivo **ogni cifra stampata in copertina deve corrispondere a un dato misurato
del libro**: i numeri veri li conta la pipeline, gli altri non si stampano.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from dataclasses import fields as dataclass_fields
from pathlib import Path

from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics

from . import coverart, kdpspecs
from .i18n import L

INCH = kdpspecs.INCH

#: soglie del sistema, usate sia per disegnare sia per verificare
MIN_TITLE_CAP_RATIO = 0.06      # altezza maiuscole / altezza copertina
GOOD_TITLE_CAP_RATIO = 0.085
MIN_CONTRAST = 7.0              # titolo contro fondo
THUMBNAIL_WIDTH_PX = 160        # com'è vista davvero nei risultati di ricerca
MAX_TOP_ELEMENTS = 4            # blocchi di testo nella metà alta della prima
MAX_TITLE_LINES = 3             # oltre, il titolo non è un'insegna ma un paragrafo
SAFE_MARGIN_IN = 0.25           # margine di sicurezza KDP dal taglio

#: spaziatura fra i caratteri, in frazione del corpo, per i testi in maiuscolo
KICKER_TRACKING = 0.28
STATS_TRACKING = 0.08
AUTHOR_TRACKING = 0.12
BADGE_TRACKING = 0.20


# --------------------------------------------------------------------------
# Colore
# --------------------------------------------------------------------------
def _channel(value: float) -> float:
    value /= 255.0
    return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4


def luminance(hex_color: str) -> float:
    """Luminanza relativa secondo WCAG."""
    raw = hex_color.lstrip("#")
    red, green, blue = (int(raw[i : i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _channel(red) + 0.7152 * _channel(green) + 0.0722 * _channel(blue)


def contrast_ratio(first: str, second: str) -> float:
    light, dark = sorted((luminance(first), luminance(second)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


@dataclass(frozen=True)
class Palette:
    """Fondo, accento e inchiostro di una copertina.

    `pops_on_white` dice se il fondo stacca dalla pagina dei risultati: una
    copertina chiara su fondo bianco perde il bordo e con esso metà dei clic.
    """

    name: str
    background: str
    deep: str          # banda/blocco più scuro o più chiaro del fondo
    title: str
    accent: str        # un solo colore d'accento, usato con parsimonia
    muted: str
    genres: tuple[str, ...] = ()

    @property
    def pops_on_white(self) -> bool:
        return contrast_ratio(self.background, "#FFFFFF") >= 3.0

    @property
    def title_contrast(self) -> float:
        return contrast_ratio(self.title, self.background)


PALETTES: tuple[Palette, ...] = (
    # Giallo su nero: la combinazione con più stacco che esista su fondo bianco.
    Palette("notturno", "#0E1320", "#161E31", "#FFFFFF", "#F5B301", "#A9B6CC",
            genres=("enigmi", "fiction", "non-fiction")),
    Palette("allarme", "#141414", "#1F1F1F", "#FFFFFF", "#FF3B30", "#C9C9C9",
            genres=("enigmi", "fiction")),
    Palette("inchiostro", "#10243A", "#0B1A2B", "#FFFFFF", "#2ED3B7", "#AFC4D6",
            genres=("non-fiction", "enigmi")),
    Palette("bosco", "#12291E", "#0D1F16", "#F6F3E7", "#9BE564", "#BFD3C1",
            genres=("non-fiction",)),
    Palette("terracotta", "#2B1410", "#1E0E0B", "#FFF3E8", "#FF7A45", "#E0C5B4",
            genres=("fiction", "non-fiction")),
    Palette("indaco", "#1A1340", "#120D2E", "#FFFFFF", "#8B7BFF", "#CFC9EC",
            genres=("fiction", "enigmi")),
)


def pick_palette(spec, genre: str) -> Palette:
    """Palette scelta dall'autore, o la migliore per il genere, in modo stabile."""
    wanted = getattr(spec, "cover_theme", "auto")
    for palette in PALETTES:
        if palette.name == wanted:
            return palette
    candidates = [p for p in PALETTES if genre in p.genres] or list(PALETTES)
    digest = hashlib.sha256(spec.title.encode("utf-8")).digest()
    return candidates[digest[0] % len(candidates)]


# --------------------------------------------------------------------------
# Che cosa va scritto sopra
# --------------------------------------------------------------------------
@dataclass
class CoverCopy:
    """I testi della prima di copertina, in ordine di importanza percettiva."""

    title: str
    kicker: str = ""        # riga piccola in alto: dice il genere in due parole
    hook: str = ""          # il ciclo aperto: una domanda o una promessa
    stats: str = ""         # numeri in cifre, separati da ·
    badge: str = ""         # una garanzia vera, breve
    author: str = ""
    #: di che cosa parla il libro, per scegliere l'illustrazione
    subject: str = ""
    #: categoria di prodotto: decide quale delle due formule si applica
    content_type: str = "full"      # full | medium
    #: i numeri che il libro ha davvero, in cifre nude («908», non «908 sospetti»).
    #: Chi costruisce la copertina li dichiara qui, e il controllo rifiuta
    #: qualunque cifra stampata che non sia in questo elenco.
    facts: tuple[str, ...] = ()

    @property
    def is_medium(self) -> bool:
        return self.content_type == "medium"

    def elements(self) -> int:
        return sum(1 for value in (self.kicker, self.title, self.hook, self.stats) if value)


#: L'occhiello dice *che prodotto è*, e va nella lingua del libro: un occhiello
#: inglese su una copertina italiana dice al cliente che il libro non è per lui.
#: Solo l'enigmistica ne ha uno di serie — «NON-FICTION» stampato in copertina
#: non è un segnale di categoria, è rumore.
GENRE_KICKERS = {"enigmi": "cover_kicker_puzzles"}

#: sopra questo corpo il libro è a caratteri grandi, ed è una garanzia vera
LARGE_PRINT_PT = 13.0

#: I numeri si leggono anche scritti con i separatori delle migliaia: «1,234» e
#: «1.234» sono lo stesso fatto.
_NUMBER = re.compile(r"\d[\d.,]*")


def numbers_in(text: str) -> set[str]:
    """Le cifre contenute in un testo, normalizzate: {«13», «908»}."""
    found = (re.sub(r"\D", "", match) for match in _NUMBER.findall(text or ""))
    return {digits for digits in found if digits}


def genre_kicker(genre: str, language: str) -> str:
    key = GENRE_KICKERS.get(genre, "")
    return L(language, key) if key else ""


def count_practice_sections(chapters: Iterable[str]) -> int:
    """Quante schede pratiche ha davvero il manoscritto.

    È il quantificatore del medium-content in prosa, e si conta invece di
    dichiararlo: la sezione `## In pratica` è quella che il ghostwriter riceve
    istruzione di scrivere, e o c'è o non c'è.
    """
    return sum(
        1 for markdown in chapters if re.search(r"^##\s+In pratica", markdown, flags=re.M | re.I)
    )


def measured_facts(*, pages: int = 0, chapters: int = 0, practice: int = 0) -> tuple:
    """I numeri del libro che la copertina ha il diritto di stampare.

    Solo quantità che il cliente può contare aprendo il libro: pagine,
    capitoli, schede pratiche. Il corpo del carattere, per dire, è misurato ma
    non è una quantità — metterlo qui aprirebbe la porta a un «11» stampato in
    copertina che non significa niente.
    """
    return tuple(str(v) for v in (pages, chapters, practice) if v)


def quantifier(spec, *, pages: int = 0, chapters: int = 0, practice: int = 0) -> str:
    """La banda di numeri del medium-content, nella lingua del libro.

    Si dice quello che si è contato, in cifre e in due voci al massimo: in
    miniatura una banda con tre numeri non si legge, si guarda.
    """
    language = getattr(spec, "language", "it")
    voci = []
    if practice:
        voci.append(L(language, "cover_practice").format(n=practice))
    elif chapters:
        voci.append(L(language, "cover_chapters").format(n=chapters))
    if pages:
        voci.append(L(language, "cover_pages").format(n=pages))
    return " · ".join(voci)


def guarantee(spec) -> str:
    """Una garanzia vera e verificabile: per ora, i caratteri grandi."""
    if getattr(spec, "body_font_size", 0) >= LARGE_PRINT_PT:
        return L(getattr(spec, "language", "it"), "cover_large_print")
    return ""


def derive_copy(
    spec,
    metadata: dict | None = None,
    genre: str = "non-fiction",
    *,
    pages: int = 0,
    chapters: int = 0,
    practice: int = 0,
) -> CoverCopy:
    """Ricava i testi di copertina dai dati che il libro ha già.

    Il sottotitolo completo non finisce in copertina: in miniatura non si legge
    e ruba spazio al titolo. Si usa la sua prima proposizione come gancio.

    La categoria decide il resto. Su un **medium-content** il quantificatore e
    la garanzia si calcolano dal libro vero quando la scheda non li propone: un
    numero contato non può mentire, ed è l'unico che KDP non contesta. Su un
    **full-content** non si calcolano affatto — se compaiono lo stesso, li ha
    voluti l'autore, e il controllo glielo dice.
    """
    metadata = metadata or {}
    language = getattr(spec, "language", "it")
    content_type = getattr(spec, "content_type", "full")
    facts = measured_facts(pages=pages, chapters=chapters, practice=practice)

    stats = metadata.get("cover_stats", "")
    badge = metadata.get("cover_badge", "")
    if content_type == "medium":
        stats = stats or quantifier(spec, pages=pages, chapters=chapters, practice=practice)
        badge = badge or guarantee(spec)

    return CoverCopy(
        title=spec.title,
        kicker=metadata.get("cover_kicker") or genre_kicker(genre, language),
        hook=metadata.get("cover_hook") or _first_clause(spec.subtitle),
        stats=stats,
        badge=badge,
        author=spec.author,
        subject=subject_of(spec),
        content_type=content_type,
        facts=facts,
    )


def title_problems(title: str, *, trim: str = "6x9") -> list[str]:
    """Questo titolo sta in copertina a misura leggibile? Solo conti, zero token.

    Il controllo sta qui e non nel controllo qualità perché qui costa un file e
    là costa un manoscritto: quando l'agente `copertina` se ne accorge il libro
    è già stato progettato, scritto, impaginato e pagato — centocinque chiamate
    al modello per scoprire una cosa che si misura in sedici millesimi di
    secondo. Su titoli italiani realistici non è un caso di scuola: una parola
    come «CONCENTRAZIONE», da sola, in un sans normale è più larga di una prima
    6x9 già al corpo minimo leggibile in miniatura, e ci entra solo se il
    progetto ha un condensato (`fonts/ofl/`).

    Qui stanno **solo i difetti insanabili**, quelli che nessuna scelta di
    impaginazione può salvare. Un titolo che va su quattro righe, per dire, non
    è qui: il disegno accetta di scendere di riga pur di non scendere sotto la
    soglia di leggibilità, e l'agente `copertina` lo segnala come importante
    sul PDF vero. Fermare la produzione per quello sarebbe severità, non
    misura.
    """
    from .typography import register_condensed_display, register_family

    display = register_family("sans")
    trim_width, trim_height = kdpspecs.trim_size_in(trim)
    measure = trim_width * INCH - 2.4 * SAFE_MARGIN_IN * INCH
    floor = trim_height * INCH * MIN_TITLE_CAP_RATIO / 0.72

    parole = title.upper().split()
    if not parole:
        return ["Il titolo è vuoto."]

    # Si ragiona con i caratteri che la copertina userà davvero: se c'è un
    # condensato e la parola ci entra, la copertina la comporrà lì. Misurare
    # solo il sans bloccherebbe in partenza un titolo che si stampa benissimo.
    caratteri = [display] + [f for f in (register_condensed_display(),) if f]

    def non_entra(font: str) -> bool:
        larga_qui = max(parole, key=lambda word: pdfmetrics.stringWidth(word, font, 100))
        return pdfmetrics.stringWidth(larga_qui, font, floor) > measure

    if all(non_entra(font) for font in caratteri):
        larga = max(parole, key=lambda word: pdfmetrics.stringWidth(word, display, 100))
        return [
            f"«{title}» non sta in copertina: la parola «{larga}» supera la larghezza "
            f"della prima ({trim}) già al corpo minimo leggibile in miniatura. Serve un "
            "titolo con parole più corte; quelle lunghe vanno nel sottotitolo, che in "
            "copertina si compone molto più piccolo."
        ]
    return []


def copy_from_dict(written: dict, spec) -> CoverCopy:
    """Ricostruisce i testi di copertina da come li ha salvati la lavorazione.

    La categoria e i fatti misurati possono mancare: succede su un libro
    lavorato prima che la copertina conoscesse le due formule. In quel caso la
    categoria si prende dalla scheda del libro, e senza fatti il controllo sui
    numeri tace invece di accusare cifre che nessuno ha mai dichiarato vere.
    """
    noti = {f.name for f in dataclass_fields(CoverCopy)}
    dati = {k: v for k, v in (written or {}).items() if k in noti}
    dati.setdefault("title", getattr(spec, "title", ""))
    dati.setdefault("content_type", getattr(spec, "content_type", "full"))
    dati["facts"] = tuple(str(v) for v in dati.get("facts") or ())
    return CoverCopy(**dati)


# --------------------------------------------------------------------------
# La formula della categoria, fatta rispettare
# --------------------------------------------------------------------------
def copy_problems(copy: CoverCopy) -> list[str]:
    """Che cosa, nei testi, tradisce la categoria di prodotto del libro.

    Si controlla solo ciò che si misura: la presenza di un quantificatore, la
    presenza di specifiche da scaffale su un'opera a testo pieno, e la
    corrispondenza fra le cifre stampate e i fatti del libro. Se una copertina
    sia *bella* qui non lo decide nessuno.
    """
    problems: list[str] = []
    if copy.is_medium:
        if not copy.stats:
            problems.append(
                "Medium-content senza quantificatore: la copertina non dice quanto "
                "contiene il libro, che è la prima cosa che questo cliente cerca."
            )
        if not copy.kicker:
            problems.append(
                "Medium-content senza segnale di categoria: in miniatura non si "
                "capisce che tipo di prodotto è."
            )
    else:
        scaffale = [name for name, value in (("numeri", copy.stats), ("garanzia", copy.badge))
                    if value]
        if scaffale:
            problems.append(
                f"Full-content con le specifiche da scaffale del medium-content "
                f"({', '.join(scaffale)}): su un'opera a testo pieno la copertina "
                "vende il mondo e la promessa, non il formato."
            )

    stampate = set()
    for text in (copy.kicker, copy.hook, copy.stats, copy.badge):
        stampate |= numbers_in(text)
    # Senza fatti dichiarati non c'è niente contro cui verificare, e accusare
    # una cifra di essere inventata quando nessuno ha detto quali siano vere
    # sarebbe un difetto costruito dal controllo, non trovato.
    inventate = (
        sorted(stampate - set(copy.facts) - numbers_in(copy.title), key=len)
        if copy.facts else []
    )
    if inventate:
        problems.append(
            f"In copertina compaiono cifre che non corrispondono a nessun dato "
            f"misurato del libro: {', '.join(inventate)}. Un numero stampato in "
            "copertina è una promessa al cliente, e questa non la mantiene nessuno."
        )
    return problems


def subject_of(spec) -> str:
    """Quello che il libro dice di essere: serve a scegliere l'illustrazione."""
    return " ".join(
        str(getattr(spec, field, "") or "")
        for field in ("title", "subtitle", "topic", "promise", "audience")
    )


def _first_clause(text: str, limit: int = 62) -> str:
    """La prima proposizione di un sottotitolo lungo: il resto è per la scheda."""
    if not text:
        return ""
    for separator in (": ", " — ", " – ", ". "):
        if separator in text:
            head, _, tail = text.partition(separator)
            candidate = tail if len(head) < 18 else head
            if len(candidate) <= limit:
                return candidate.strip(" .")
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "…"


# --------------------------------------------------------------------------
# Disegno
# --------------------------------------------------------------------------
@dataclass
class FrontBox:
    """L'area della prima di copertina, abbondanza compresa."""

    x0: float
    y0: float
    width: float
    height: float
    trim_width: float
    trim_height: float
    bleed: float
    safe: float

    @property
    def center(self) -> float:
        # L'abbondanza della prima sta sul taglio esterno (a destra), non a
        # sinistra: il centro ottico è quello dell'area rifilata.
        return self.x0 + self.trim_width / 2

    @property
    def measure(self) -> float:
        return self.trim_width - 2.4 * self.safe


@dataclass
class DrawResult:
    title_size: float
    title_lines: list[str] = field(default_factory=list)
    cap_ratio: float = 0.0
    contrast: float = 0.0
    art: str = ""           # l'illustrazione effettivamente disegnata


def tracked_width(text: str, font: str, size: float, tracking: float = 0.0) -> float:
    """Larghezza reale, spaziatura fra i caratteri compresa.

    `pdfmetrics.stringWidth` non conosce il tracking: usarla da sola per
    centrare o per far stare un testo nella misura porta fuori squadro.
    """
    return pdfmetrics.stringWidth(text, font, size) + tracking * max(len(text) - 1, 0)


def fit_size(
    text: str,
    font: str,
    max_width: float,
    start: float,
    minimum: float,
    tracking_ratio: float = 0.0,
) -> float:
    """Il corpo più grande che sta nella misura, tracking incluso.

    Il minimo è un pavimento vero: scendendo a passi di mezzo punto lo si
    supererebbe di poco, e quel poco è esattamente ciò che rende un titolo
    illeggibile in miniatura.
    """
    size = start
    while size > minimum and tracked_width(text, font, size, size * tracking_ratio) > max_width:
        size = max(minimum, size - 0.5)
    return size


def wrap(text: str, font: str, size: float, max_width: float) -> list[str]:
    lines: list[str] = []
    current: list[str] = []
    for word in text.split():
        trial = " ".join([*current, word])
        if pdfmetrics.stringWidth(trial, font, size) <= max_width or not current:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def _tracked(canvas, x: float, y: float, text: str, font: str, size: float, tracking: float):
    """Testo centrato in `x` con spaziatura fra i caratteri.

    La spaziatura (`Tc`) fa parte dello stato grafico del PDF, non del singolo
    blocco di testo: se non la si riazzera resta attiva per tutto il resto
    della pagina e allarga ogni riga disegnata dopo — titolo compreso, che
    finisce fuori squadro perché ReportLab lo centra senza saperlo.
    """
    obj = canvas.beginText(x - tracked_width(text, font, size, tracking) / 2, y)
    obj.setFont(font, size)
    obj.setCharSpace(tracking)
    obj.textOut(text)
    obj.setCharSpace(0)
    canvas.drawText(obj)


def title_block_size(copy: CoverCopy, display: str, box: FrontBox) -> tuple[float, list[str]]:
    """Il titolo occupa quanto può: è l'unico elemento che deve vincere.

    Si parte dal 13% dell'altezza e si scende solo se le righe non ci stanno —
    mai sotto la soglia di leggibilità in miniatura.
    """
    # La parola più larga non è quella con più lettere: PRINCIPIANTI (12) è più
    # stretta di MEDITAZIONE (11), perché le I non occupano niente. Tarare il
    # corpo sul conteggio delle lettere lo tara sulla parola sbagliata, e quella
    # vera esce dall'area di sicurezza: in stampa viene rifilata.
    words = copy.title.upper().split() or ["A"]
    longest = max(words, key=lambda word: pdfmetrics.stringWidth(word, display, 100))
    ceiling = box.trim_height * 0.13
    floor = box.trim_height * MIN_TITLE_CAP_RATIO / 0.72
    size = min(ceiling, fit_size(longest, display, box.measure, ceiling, floor))
    lines = wrap(copy.title.upper(), display, size, box.measure)
    while len(lines) > MAX_TITLE_LINES and size > floor:
        # Mai sotto la soglia di leggibilità: un titolo di quattro righe si
        # legge ancora, un titolo illeggibile in miniatura no. Se non ci sta
        # nemmeno così, il problema è il titolo — e `audit()` lo segnala.
        size = max(floor, size - 1)
        lines = wrap(copy.title.upper(), display, size, box.measure)
    return size, lines




#: il condensato si usa solo se fa crescere il titolo almeno di tanto: sotto,
#: in miniatura la differenza non si vede, e un cambio di carattere si paga
#: sempre in coerenza con il resto della copertina
CONDENSED_MIN_GAIN = 1.10


def title_font_and_size(
    copy: CoverCopy, display: str, condensed: str | None, box: FrontBox
) -> tuple[str, float, list[str]]:
    """Il carattere e il corpo del titolo: il sans di sempre, o il condensato.

    Decide la parola più larga. «TRE ORE» sta benissimo nel sans; «REMEMBERED»
    no, perché a tutta larghezza si ferma sotto la soglia che rende un titolo
    dominante. Il condensato entra solo quando la guadagna.
    """
    size, lines = title_block_size(copy, display, box)
    if not condensed:
        return display, size, lines
    c_size, c_lines = title_block_size(copy, condensed, box)
    # Se nel sans la parola più larga non entra nemmeno al corpo minimo, il
    # condensato non è un guadagno: è l'unico modo di non farla rifilare.
    parole = copy.title.upper().split() or ["A"]
    larga = max(parole, key=lambda word: pdfmetrics.stringWidth(word, display, 100))
    esce = pdfmetrics.stringWidth(larga, display, size) > box.measure + 0.5
    if esce or c_size >= size * CONDENSED_MIN_GAIN:
        return condensed, c_size, c_lines
    return display, size, lines


# -- prima di copertina -----------------------------------------------------
def draw_front(
    canvas,
    box: FrontBox,
    copy: CoverCopy,
    palette: Palette,
    *,
    display: str,
    text_font: str,
    genre: str = "non-fiction",
    over_image: bool = False,
    art_name: str = "auto",
    condensed: str | None = None,
) -> DrawResult:
    """Disegna la prima di copertina secondo il sistema.

    Ordine di lettura imposto: genere → titolo → gancio → motivo → numeri →
    autore. Chi guarda una miniatura si ferma ai primi due; chi apre la scheda
    scende fino ai numeri.
    """
    title_color = "#FFFFFF" if over_image else palette.title
    center = box.center
    top = box.y0 + box.height - box.bleed

    # 1. kicker: dice il genere in due parole, piccolo e tracciato
    y = top - box.safe * 1.5
    if copy.kicker:
        size = fit_size(
            copy.kicker.upper(), display, box.measure,
            max(box.trim_height * 0.016, 7.5), 6.5, KICKER_TRACKING,
        )
        canvas.setFillColor(colors.HexColor(palette.accent))
        _tracked(canvas, center, y - size, copy.kicker.upper(), display, size,
                 size * KICKER_TRACKING)
        y -= size * 2.6
    else:
        y -= box.safe * 0.4

    # 2. titolo: l'elemento dominante
    title_font, title_size, lines = title_font_and_size(copy, display, condensed, box)
    canvas.setFillColor(colors.HexColor(title_color))
    y -= title_size * 0.92
    for line in lines:
        canvas.setFont(title_font, title_size)
        canvas.drawCentredString(center, y, line)
        y -= title_size * 1.02

    # 3. filetto d'accento, largo quanto la riga più lunga del titolo
    widest = max(
        (pdfmetrics.stringWidth(line, title_font, title_size) for line in lines), default=0
    )
    y += title_size * 0.28
    canvas.setStrokeColor(colors.HexColor(palette.accent))
    canvas.setLineWidth(3)
    canvas.line(center - widest * 0.3, y, center + widest * 0.3, y)

    # 4. gancio: il ciclo aperto
    if copy.hook:
        hook_size = fit_size(copy.hook, text_font, box.measure, box.trim_height * 0.028, 9)
        y -= hook_size * 2.2
        canvas.setFillColor(colors.HexColor("#FFFFFF" if over_image else palette.muted))
        for line in wrap(copy.hook, text_font, hook_size, box.measure):
            canvas.setFont(text_font, hook_size)
            canvas.drawCentredString(center, y, line)
            y -= hook_size * 1.3

    # 5. il piede si misura prima di disegnarlo: serve al motivo per sapere
    #    dove fermarsi, e a ogni riga per non finire sotto il margine di
    #    sicurezza (la riga più bassa è quella dell'autore, discendenti comprese).
    floor = box.y0 + box.bleed + box.safe
    author_size = fit_size(
        copy.author.upper(), display, box.measure,
        box.trim_height * 0.024, 8, AUTHOR_TRACKING,
    )
    author_baseline = floor + author_size * 0.28
    foot_top = author_baseline + author_size * 0.8

    badge_size = badge_baseline = 0.0
    if copy.badge:
        badge_size = fit_size(
            copy.badge.upper(), display, box.measure,
            max(author_size * 0.62, 6.5), 6.0, BADGE_TRACKING,
        )
        badge_baseline = foot_top + badge_size * 1.05
        foot_top = badge_baseline + badge_size * 0.8

    stats_size = band_bottom = band_height = 0.0
    if copy.stats:
        stats_size = fit_size(
            copy.stats.upper(), display, box.measure * 0.92,
            box.trim_height * 0.026, 8, STATS_TRACKING,
        )
        band_height = stats_size * 2.1
        band_bottom = foot_top + stats_size * 0.85
        foot_top = band_bottom + band_height

    # 6. illustrazione, nello spazio che resta fra gancio e piede. Quando la
    #    copertina ha già una fotografia dell'autore non si disegna niente:
    #    l'immagine *è* l'elemento dominante, e sovrapporne un secondo
    #    romperebbe la prima regola del sistema.
    drawn_art = ""
    available = y - (foot_top + box.safe * 0.6)
    if not over_image and available > box.trim_height * 0.12:
        try:
            art = coverart.pick(copy.subject, genre, wanted=art_name)
        except KeyError:
            art = None
        if art is not None:
            area = coverart.Area(
                x=box.center - box.measure / 2,
                y=foot_top + box.safe * 0.6,
                width=box.measure,
                height=available,
            ).inset(0.03)
            coverart.draw(canvas, art, area, palette)
            drawn_art = art.name

    # 7. numeri in cifre, appoggiati a una banda che arriva fino al taglio:
    #    è il piede che tiene insieme la copertina anche in miniatura
    if copy.stats:
        canvas.setFillColor(colors.HexColor(palette.accent))
        canvas.rect(box.x0, band_bottom, box.width, band_height, stroke=0, fill=1)
        canvas.setFillColor(colors.HexColor(palette.background))
        _tracked(
            canvas, center, band_bottom + band_height * 0.36, copy.stats.upper(),
            display, stats_size, stats_size * STATS_TRACKING,
        )

    # 8. garanzia e autore, sotto la banda
    if copy.badge:
        canvas.setFillColor(colors.HexColor(palette.muted))
        _tracked(
            canvas, center, badge_baseline, copy.badge.upper(),
            display, badge_size, badge_size * BADGE_TRACKING,
        )
    canvas.setFillColor(colors.HexColor(title_color))
    _tracked(
        canvas, center, author_baseline, copy.author.upper(),
        display, author_size, author_size * AUTHOR_TRACKING,
    )

    cap_ratio = title_size * 0.72 / box.trim_height
    return DrawResult(
        title_size=title_size,
        title_lines=lines,
        cap_ratio=cap_ratio,
        contrast=contrast_ratio(title_color, palette.background),
        art=drawn_art,
    )


# --------------------------------------------------------------------------
# Verifica: la copertina vista come la vede il cliente
# --------------------------------------------------------------------------
@dataclass
class CoverAudit:
    title_cap_px: float           # altezza maiuscole del titolo, in pixel di miniatura
    title_cap_ratio: float
    contrast: float
    pops_on_white: bool
    top_elements: int
    inside_safe_area: bool
    title_lines: int = 0
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems

    def to_dict(self) -> dict:
        return {
            "titolo_px_in_miniatura": round(self.title_cap_px, 1),
            "titolo_percentuale_altezza": round(self.title_cap_ratio * 100, 1),
            "titolo_righe": self.title_lines,
            "contrasto": round(self.contrast, 1),
            "stacca_su_bianco": self.pops_on_white,
            "elementi_in_alto": self.top_elements,
            "dentro_area_sicura": self.inside_safe_area,
            "problemi": self.problems,
        }


def audit(
    pdf_path: Path,
    *,
    trim: str,
    pages: int,
    paper: str,
    palette: Palette,
    title: str,
) -> CoverAudit:
    """Misura la copertina finita: quanto è grande il titolo in miniatura, che
    contrasto ha, quanti elementi affollano la metà alta."""
    try:
        import pymupdf
    except ImportError:  # pragma: no cover - PyMuPDF è consigliato, non obbligatorio
        return CoverAudit(
            title_cap_px=0,
            title_cap_ratio=0,
            contrast=palette.title_contrast,
            pops_on_white=palette.pops_on_white,
            top_elements=0,
            inside_safe_area=True,
            problems=["PyMuPDF non installato: copertina non verificata."],
        )

    trim_w, trim_h = kdpspecs.trim_size_in(trim)
    spine = kdpspecs.spine_width_in(pages, paper)
    bleed = kdpspecs.BLEED_IN
    front_x0 = (bleed + trim_w + spine) * INCH
    scale = THUMBNAIL_WIDTH_PX / (trim_w * INCH)

    document = pymupdf.open(pdf_path)
    page = document[0]
    page_height = page.rect.height
    # Le parole corte si scartano perché «di» o «la» si ritrovano ovunque, nel
    # gancio come nella garanzia. Ma un titolo fatto *solo* di parole corte —
    # «Tre Ore» — è un titolo eccellente in miniatura: senza il ripiego l'audit
    # non ne trovava nessuna e lo dichiarava assente, bocciando la copertina
    # migliore che il sistema sa fare.
    parole = title.upper().split()
    words = [word for word in parole if len(word) > 3] or parole
    title_spans: list[dict] = []
    front_spans: list[dict] = []
    top_blocks: set[int] = set()

    for block_index, block in enumerate(page.get_text("dict")["blocks"]):
        for line in block.get("lines", []):
            # Il dorso è testo ruotato: la sua misura va letta in verticale e
            # non c'entra con l'area di sicurezza della prima.
            vertical = abs(line.get("dir", (1.0, 0.0))[0]) < 0.5
            for span in line.get("spans", []):
                text = span["text"].strip()
                # Si scarta solo ciò che sta *interamente* a sinistra della
                # prima. Con `bbox[0] < front_x0` sparivano proprio le righe di
                # titolo troppo larghe — quelle che cominciano dentro il dorso e
                # finiscono oltre il taglio — cioè il difetto peggiore che ci
                # sia da trovare: in stampa quella parola viene rifilata.
                if not text or span["bbox"][2] < front_x0 or vertical:
                    continue
                front_spans.append(span)
                if any(word in text.upper() for word in words):
                    title_spans.append(span)
                if span["bbox"][1] < page_height * 0.5:
                    top_blocks.add(block_index)
    document.close()

    # Fra le righe che contengono una parola del titolo, il titolo è la più
    # grande: il gancio può ripetere una parola del titolo, ma non il corpo.
    if title_spans:
        biggest = max(span["size"] for span in title_spans)
        title_spans = [span for span in title_spans if span["size"] >= biggest * 0.95]

    problems: list[str] = []
    if not title_spans:
        problems.append("Il titolo non è stato trovato sulla prima di copertina.")
        cap_pt = 0.0
    else:
        cap_pt = max(span["size"] for span in title_spans) * 0.72

    cap_px = cap_pt * scale
    cap_ratio = cap_pt / (trim_h * INCH) if cap_pt else 0.0
    # `title_block_size` si ferma *esattamente* sul minimo: senza tolleranza, il
    # confronto in virgola mobile (0.05999999999999999 < 0.06) boccia la
    # copertina che il sistema ha appena disegnato a regola d'arte.
    if cap_ratio and cap_ratio < MIN_TITLE_CAP_RATIO - 1e-6:
        problems.append(
            f"Titolo troppo piccolo per la miniatura: {cap_px:.0f} px a "
            f"{THUMBNAIL_WIDTH_PX} px di larghezza ({cap_ratio * 100:.1f}% dell'altezza, "
            f"minimo {MIN_TITLE_CAP_RATIO * 100:.0f}%)."
        )
    if palette.title_contrast < MIN_CONTRAST:
        problems.append(
            f"Contrasto titolo/fondo {palette.title_contrast:.1f}:1, sotto il minimo "
            f"{MIN_CONTRAST:.0f}:1."
        )
    if not palette.pops_on_white:
        problems.append(
            "Il fondo non stacca dalla pagina bianca dei risultati: la copertina perde "
            "il bordo e con esso metà della visibilità."
        )
    if len(title_spans) > MAX_TITLE_LINES:
        problems.append(
            f"Il titolo occupa {len(title_spans)} righe (massimo {MAX_TITLE_LINES}): "
            "in miniatura un titolo lungo si legge come un paragrafo, non come un'insegna."
        )
    if len(top_blocks) > MAX_TOP_ELEMENTS:
        problems.append(
            f"{len(top_blocks)} blocchi di testo nella metà alta (massimo {MAX_TOP_ELEMENTS}): "
            "in miniatura diventano una macchia."
        )

    # L'area rifilata della prima va da `front_x0` a `front_x0 + trim`:
    # l'abbondanza è oltre il taglio esterno e in stampa viene rifilata via.
    safe_left = front_x0 + SAFE_MARGIN_IN * INCH
    safe_right = front_x0 + (trim_w - SAFE_MARGIN_IN) * INCH
    safe_top = (bleed + SAFE_MARGIN_IN) * INCH
    safe_bottom = (bleed + trim_h - SAFE_MARGIN_IN) * INCH
    outside = [
        span
        for span in front_spans
        if span["bbox"][0] < safe_left - 1
        or span["bbox"][2] > safe_right + 1
        or span["bbox"][1] < safe_top - 1
        or span["bbox"][3] > safe_bottom + 1
    ]
    inside_safe = not outside
    if outside:
        listed = ", ".join(f"«{span['text'].strip()[:28]}»" for span in outside[:3])
        problems.append(
            f"Testo fuori dall'area di sicurezza ({len(outside)} righe): in stampa "
            f"rischia il taglio — {listed}."
        )

    return CoverAudit(
        title_cap_px=cap_px,
        title_cap_ratio=cap_ratio,
        contrast=palette.title_contrast,
        pops_on_white=palette.pops_on_white,
        top_elements=len(top_blocks),
        inside_safe_area=inside_safe,
        title_lines=len(title_spans),
        problems=problems,
    )


def render_thumbnail(pdf_path: Path, output: Path, *, trim: str, pages: int, paper: str) -> Path:
    """Salva la prima di copertina alla dimensione con cui la vede il cliente.

    Guardare questo file, e non il PDF a schermo intero, è l'unico modo onesto
    di giudicare una copertina.
    """
    import pymupdf

    trim_w, trim_h = kdpspecs.trim_size_in(trim)
    spine = kdpspecs.spine_width_in(pages, paper)
    bleed = kdpspecs.BLEED_IN
    front_x0 = (bleed + trim_w + spine) * INCH

    document = pymupdf.open(pdf_path)
    page = document[0]
    # Solo l'area rifilata della prima: l'abbondanza, che in stampa sparisce,
    # falserebbe il giudizio sulla miniatura.
    clip = pymupdf.Rect(
        front_x0,
        bleed * INCH,
        front_x0 + trim_w * INCH,
        (bleed + trim_h) * INCH,
    )
    scale = THUMBNAIL_WIDTH_PX / (trim_w * INCH)
    pixmap = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), clip=clip)
    output.parent.mkdir(parents=True, exist_ok=True)
    pixmap.save(output)
    document.close()
    return output


# --------------------------------------------------------------------------
# Controlli di produzione: quello che KDP rifiuta al caricamento
# --------------------------------------------------------------------------
# `audit()` guarda la copertina come la guarda il cliente: in miniatura, sulla
# pagina dei risultati. Questi controlli guardano il file come lo guarda la
# tipografia — e sono quelli che fanno rimbalzare un caricamento, che costa una
# settimana di pubblicazione ogni volta.
#
# Nessuno di questi è una questione di gusto. O le misure tornano o no.

#: distanza minima del testo di dorso dalle due pieghe (KDP: 1,6 mm)
SPINE_TEXT_CLEARANCE_IN = 0.0625
#: quanto può scostarsi il PDF dalle misure calcolate prima di essere sbagliato
SIZE_TOLERANCE_PT = 1.0
#: una zona del codice a barre si considera libera se è quasi bianca ovunque
BARCODE_MIN_LUMA = 235
#: si campiona un punto dentro il bordo della zona, non il bordo stesso: sul
#: contorno esatto del rettangolo l'antialiasing mescola i due colori e
#: produrrebbe una segnalazione su ogni copertina che il sistema disegna
BARCODE_INSET_PT = 1.0


def audit_production(
    pdf_path: Path,
    *,
    trim: str,
    pages: int,
    paper: str,
    author: str = "",
) -> list[str]:
    """I controlli tecnici sul PDF di copertina finito.

    Misura quello che l'elenco di controllo di KDP chiede e che nessuno
    verifica guardando il file a schermo: le dimensioni contro il calcolo del
    dorso, l'area del codice a barre, il testo di dorso dentro il dorso, i
    font incorporati e le linee guida rimaste nel file di produzione.
    """
    try:
        import pymupdf
    except ImportError:  # pragma: no cover - PyMuPDF è consigliato, non obbligatorio
        return ["PyMuPDF non installato: controlli di produzione non eseguiti."]
    if not Path(pdf_path).exists():
        return ["Nessun PDF di copertina da controllare."]

    trim_w, trim_h = kdpspecs.trim_size_in(trim)
    spine_in = kdpspecs.spine_width_in(pages, paper)
    attesa_w, attesa_h = kdpspecs.cover_size_in(trim, pages, paper)
    bleed = kdpspecs.BLEED_IN
    spine_x0 = (bleed + trim_w) * INCH
    spine_x1 = spine_x0 + spine_in * INCH

    document = pymupdf.open(pdf_path)
    problemi: list[str] = []
    try:
        problemi += _controlla_dimensioni(document, attesa_w, attesa_h, spine_in, pages, paper)
        if len(document) > 1:
            problemi.append(
                f"Il PDF di copertina ha {len(document)} pagine: KDP ne accetta una sola, "
                "con retro, dorso e prima in un'unica immagine continua."
            )
        page = document[0]
        problemi += _controlla_dorso(page, pages, spine_x0, spine_x1, spine_in)
        problemi += _controlla_codice_a_barre(page, spine_x0, bleed)
        problemi += _controlla_font(page)
        problemi += _controlla_guide(page, spine_x0, spine_x1)
        problemi += _controlla_autore(page, author, bleed, trim_w, spine_in)
    finally:
        document.close()
    return problemi


def _controlla_dimensioni(document, attesa_w, attesa_h, spine_in, pages, paper) -> list[str]:
    """Il difetto che rimbalza il caricamento e che nessuno vede a schermo.

    Il dorso dipende da pagine, carta e formato: se il PDF è stato fatto con un
    conteggio pagine vecchio, è largo quel tanto che basta a far slittare tutto
    e KDP lo respinge senza spiegare quale numero non torna.
    """
    rect = document[0].rect
    if (
        abs(rect.width - attesa_w * INCH) <= SIZE_TOLERANCE_PT
        and abs(rect.height - attesa_h * INCH) <= SIZE_TOLERANCE_PT
    ):
        return []
    return [
        f"Le dimensioni del PDF ({rect.width / INCH:.3f}\" x {rect.height / INCH:.3f}\") non "
        f"corrispondono al calcolo KDP ({attesa_w:.3f}\" x {attesa_h:.3f}\"): "
        f"{pages} pagine su carta {paper} fanno un dorso di {spine_in:.3f}\". "
        "Rigenera la copertina sul conteggio pagine definitivo."
    ]


def _controlla_dorso(page, pages, spine_x0, spine_x1, spine_in) -> list[str]:
    """Testo di dorso: ammesso solo da 79 pagine in su, e dentro le pieghe."""
    ruotato = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            if abs(line.get("dir", (1.0, 0.0))[0]) >= 0.5:
                continue                      # orizzontale: non è il dorso
            for span in line.get("spans", []):
                if span["text"].strip():
                    ruotato.append(span)
    if not ruotato:
        return []

    if not kdpspecs.spine_text_allowed(pages):
        return [
            f"C'è testo sul dorso ma il libro ha {pages} pagine: KDP non lo consente "
            f"sotto le {kdpspecs.SPINE_TEXT_MIN_PAGES}."
        ]

    margine = SPINE_TEXT_CLEARANCE_IN * INCH
    fuori = [
        span
        for span in ruotato
        if span["bbox"][0] < spine_x0 + margine - 0.5
        or span["bbox"][2] > spine_x1 - margine + 0.5
    ]
    if fuori:
        return [
            f"Il testo del dorso esce dalle pieghe ({len(fuori)} righe): su un dorso di "
            f"{spine_in:.3f}\" servono almeno {SPINE_TEXT_CLEARANCE_IN}\" liberi per lato, "
            "e in stampa la piega si sposta."
        ]
    return []


def _controlla_codice_a_barre(page, spine_x0, bleed) -> list[str]:
    """L'area che KDP sovrastampa: se ci finisce sopra qualcosa, lo copre.

    Si guardano i pixel invece degli oggetti: un'illustrazione di fondo che
    arriva fin lì non è un blocco di testo, ma il codice a barre ci finisce
    sopra lo stesso e diventa illeggibile allo scanner.
    """
    import pymupdf

    bar_w, bar_h = kdpspecs.BARCODE_ZONE_IN
    x0 = spine_x0 - (SAFE_MARGIN_IN + bar_w) * INCH
    y0 = (bleed + SAFE_MARGIN_IN) * INCH
    inset = BARCODE_INSET_PT
    zona = pymupdf.Rect(
        x0 + inset,
        page.rect.height - y0 - bar_h * INCH + inset,
        x0 + bar_w * INCH - inset,
        page.rect.height - y0 - inset,
    )
    pixmap = page.get_pixmap(clip=zona, colorspace=pymupdf.csGRAY)
    campioni = pixmap.samples
    if not campioni:
        return []
    minimo = min(campioni)
    if minimo >= BARCODE_MIN_LUMA:
        return []
    scuri = sum(1 for v in campioni if v < BARCODE_MIN_LUMA) / len(campioni)
    return [
        f"L'area del codice a barre non è libera: il {scuri:.0%} dell'area di "
        f'{bar_w}"x{bar_h}" in basso a destra della quarta ha inchiostro sopra '
        f"(il punto più scuro è a {minimo} di luminosità). KDP ci stampa sopra il codice."
    ]


def _controlla_font(page) -> list[str]:
    non_incorporati = {
        font[3]
        for font in page.get_fonts(full=False)
        if font[1] == "n/a" or font[0] == 0
    }
    if not non_incorporati:
        return []
    return [
        "Font non incorporati nella copertina (KDP li rifiuta): "
        + ", ".join(sorted(non_incorporati))
    ]


def _controlla_guide(page, spine_x0, spine_x1) -> list[str]:
    """Linee di taglio e di piega rimaste nel file di produzione.

    Il sistema le disegna solo con `--guides`, che serve a controllare il
    montaggio. Quel file non va caricato: KDP rifiuta i segni di taglio, e chi
    ha generato la copertina due settimane fa non si ricorda con quale opzione.
    """
    altezza = page.rect.height
    verticali = 0
    for disegno in page.get_drawings():
        for item in disegno["items"]:
            if item[0] != "l":
                continue
            p1, p2 = item[1], item[2]
            if abs(p1.x - p2.x) > 0.5 or abs(p1.y - p2.y) < altezza * 0.9:
                continue
            if any(abs(p1.x - piega) < 1.0 for piega in (spine_x0, spine_x1)):
                verticali += 1
    if verticali < 2:
        return []
    return [
        "Nel PDF ci sono le linee di piega del dorso: è il file prodotto con "
        "`--guides`, che serve a controllare il montaggio e non va caricato. "
        "Rigenera la copertina senza l'opzione."
    ]


def _controlla_autore(page, author, bleed, trim_w, spine_in) -> list[str]:
    """Il nome in copertina deve essere quello della scheda KDP, alla lettera.

    Amazon confronta i due e blocca la pubblicazione quando non coincidono: è
    un controllo che costa niente qui e una settimana di attesa lì.
    """
    if not author.strip():
        return []
    front_x0 = (bleed + trim_w + spine_in) * INCH
    testo = " ".join(
        span["text"]
        for block in page.get_text("dict")["blocks"]
        for line in block.get("lines", [])
        for span in line.get("spans", [])
        if span["bbox"][2] >= front_x0 and abs(line.get("dir", (1.0, 0.0))[0]) >= 0.5
    )
    piatto = " ".join(testo.upper().split())
    if " ".join(author.upper().split()) in piatto:
        return []
    return [
        f"Il nome dell'autore «{author}» non compare sulla prima di copertina come "
        "nella scheda: Amazon confronta copertina e metadati e blocca la pubblicazione."
    ]

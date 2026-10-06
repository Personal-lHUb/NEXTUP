"""Impaginazione dell'interno: da Markdown a PDF pronto per la stampa KDP.

Scelte tipografiche:
- margini speculari (il margine interno cambia lato tra pagina pari e dispari);
- ogni capitolo si apre su pagina dispari, con eventuale pagina bianca prima;
- testatine: titolo del libro sulle pari, titolo del capitolo sulle dispari,
  soppresse sulle pagine di apertura e sulle bianche;
- numerazione araba che parte da 1 sulla prima pagina del testo, come nei libri
  di un editore (Chicago Manual of Style, 1.5): le pagine preliminari contano
  ma non portano il numero, e l'indice stampa i numeri che il lettore vede;
- nell'opera a testo pieno titoli e testo nella stessa famiglia, aperture di
  capitolo calate di un quinto della gabbia e prime parole in maiuscoletto;
- font TrueType incorporati (requisito KDP).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    ActionFlowable,
    BaseDocTemplate,
    CondPageBreak,
    Flowable,
    Frame,
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

from . import figure as figure_module
from . import kdpspecs, mdlite
from .i18n import L, part_label
from .models import BookSpec, Outline
from .typography import enable_hyphenation, register_family, set_default_canvas_font

INCH = kdpspecs.INCH


def draw_tracked_string(canvas, x, y, text, font, size, tracking, align="left") -> None:
    """Disegna testo con spaziatura fra i caratteri (tracking).

    Il canvas non espone `setCharSpace`: si passa da un text object. La
    spaziatura fa parte dello stato grafico della pagina, non del blocco di
    testo: va riazzerata alla fine, o allarga tutto quello che viene disegnato
    dopo sulla stessa pagina.
    """
    from reportlab.pdfbase import pdfmetrics

    width = pdfmetrics.stringWidth(text, font, size) + tracking * max(len(text) - 1, 0)
    if align == "center":
        x -= width / 2.0
    elif align == "right":
        x -= width
    text_object = canvas.beginText(x, y)
    text_object.setFont(font, size)
    text_object.setCharSpace(tracking)
    text_object.textOut(text)
    text_object.setCharSpace(0)
    canvas.drawText(text_object)


# --------------------------------------------------------------------------
# Flowable di servizio
# --------------------------------------------------------------------------
class DocAction(ActionFlowable):
    """Esegue un'azione sul documento durante l'impaginazione."""

    def __init__(self, action: str, value=None):
        ActionFlowable.__init__(self)
        self.action = action
        self.value = value

    def apply(self, doc):  # noqa: D102
        if self.action == "body_start":
            doc.in_front_matter = False
            doc.body_start_page = doc.page
        elif self.action == "chapter_open":
            doc.current_chapter = self.value or ""
            doc.plain_pages.add(doc.page)
        elif self.action == "part_open":
            doc.in_parts = True
            doc.current_part_label = self.value or ""
            doc.current_chapter = ""
            doc.plain_pages.add(doc.page)
        elif self.action == "parts_end":
            doc.in_parts = False
        elif self.action == "front_matter_page":
            doc.plain_pages.add(doc.page)


class StartOnRecto(ActionFlowable):
    """Salta alla prossima pagina dispari (destra), inserendo una bianca se serve."""

    def apply(self, doc):  # noqa: D102
        # `handle_pageBreak` chiude la pagina corrente e *appende* l'inizio della
        # successiva: al momento della chiamata `doc.page` è ancora la pagina in
        # corso, quindi il contenuto finirà su `doc.page + 1`.
        doc.handle_pageBreak()
        if doc.page % 2 == 1:  # la prossima sarebbe pari (sinistra): inserisci una bianca
            doc.handle_pageBreak()


class BlankFiller(Flowable):
    """Occupa una pagina senza disegnare nulla (pagina bianca finale)."""

    def wrap(self, avail_width, avail_height):
        return 0, 0

    def draw(self):  # pragma: no cover - non disegna niente
        return


class ChapterNumber(Flowable):
    """Numero di capitolo tracciato, sopra il titolo."""

    def __init__(self, text: str, font: str, size: float, color):
        Flowable.__init__(self)
        self.text = text
        self.font = font
        self.size = size
        self.color = color
        self.width = 0
        self.height = size * 1.8

    def wrap(self, avail_width, avail_height):
        self.width = avail_width
        return avail_width, self.height

    def draw(self):
        canvas = self.canv
        canvas.saveState()
        canvas.setFillColor(self.color)
        draw_tracked_string(
            canvas,
            self.width / 2.0,
            self.size * 0.6,
            self.text.upper(),
            self.font,
            self.size,
            self.size * 0.18,
            align="center",
        )
        canvas.restoreState()


# --------------------------------------------------------------------------
# Documento
# --------------------------------------------------------------------------
class InteriorDoc(BaseDocTemplate):
    def __init__(self, filename: str, spec: BookSpec, geo: kdpspecs.PageGeometry, styles: dict):
        BaseDocTemplate.__init__(
            self,
            filename,
            pagesize=(geo.page_width, geo.page_height),
            title=spec.title,
            author=spec.author,
            subject=spec.subtitle or spec.topic,
            creator="kdp-book-factory",
            leftMargin=geo.inner_margin,
            rightMargin=geo.outer_margin,
            topMargin=geo.top_margin,
            bottomMargin=geo.bottom_margin,
            allowSplitting=1,
        )
        self.spec = spec
        self.geo = geo
        self.styles = styles
        self.toc_entries: list[tuple[int, str, int]] = []
        self.chapter_pages: dict[str, int] = {}
        self.part_pages: dict[str, int] = {}
        self._reset_state()

        # Padding a zero: i margini sono già quelli calcolati da `kdpspecs`, e i
        # 6 punti di default di ReportLab li renderebbero diversi dal dichiarato.
        padding = dict(leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        frame_recto = Frame(
            geo.inner_margin, geo.bottom_margin, geo.text_width, geo.text_height,
            id="recto", **padding,
        )
        frame_verso = Frame(
            geo.outer_margin, geo.bottom_margin, geo.text_width, geo.text_height,
            id="verso", **padding,
        )
        self.addPageTemplates(
            [
                PageTemplate(id="recto", frames=[frame_recto], onPageEnd=self._decorate),
                PageTemplate(id="verso", frames=[frame_verso], onPageEnd=self._decorate),
            ]
        )

    # -- stato -----------------------------------------------------------
    def _reset_state(self) -> None:
        self.in_front_matter = True
        self.body_start_page = 1
        self.current_chapter = ""
        self.page_has_content = False
        self.plain_pages: set[int] = set()
        # Con le parti, i capitoli scendono di un livello nell'indice.
        self.in_parts = False
        self.current_part_label = ""
        # La prima pagina del testo: da lì parte la numerazione stampata.
        self.first_body_page: int | None = None

    def folio(self, page: int) -> int:
        """Il numero stampato di una pagina fisica: 1 sulla prima pagina del testo."""
        if self.first_body_page is None:
            return page
        return page - self.first_body_page + 1

    @property
    def folio_offset(self) -> int:
        """Quante pagine fisiche precedono la pagina 1 stampata."""
        return (self.first_body_page or 1) - 1

    def handle_documentBegin(self):  # noqa: D102
        self._reset_state()
        BaseDocTemplate.handle_documentBegin(self)

    def handle_pageBegin(self):  # noqa: D102
        self._handle_pageBegin()
        # Margini speculari: la pagina successiva usa il template della sua parità.
        self.handle_nextPageTemplate("verso" if (self.page + 1) % 2 == 0 else "recto")

    def afterFlowable(self, flowable):  # noqa: D102
        if isinstance(flowable, (Paragraph, ChapterNumber, HRFlowable)):
            self.page_has_content = True
        if isinstance(flowable, Paragraph):
            style_name = getattr(flowable.style, "name", "")
            livello = 1 if self.in_parts else 0
            if style_name in ("PartTitle", "ChapterTitle") and self.first_body_page is None:
                self.first_body_page = self.page
            if style_name == "PartTitle":
                voce = f"{self.current_part_label} — {flowable.getPlainText()}"
                self.notify("TOCEntry", (0, voce, self.folio(self.page)))
                self.part_pages[voce] = self.page
            elif style_name == "ChapterTitle":
                text = flowable.getPlainText()
                # Nell'indice il capitolo porta il suo numero, come sulla pagina
                # d'apertura: è così che il lettore lo cerca.
                numero = getattr(flowable, "numero_capitolo", None)
                voce = f"{numero}\u2002{text}" if numero else text
                self.notify("TOCEntry", (livello, voce, self.folio(self.page)))
                self.chapter_pages[text] = self.page
            elif style_name == "Heading2" and self.spec.profondita_indice >= 2:
                self.notify(
                    "TOCEntry", (livello + 1, flowable.getPlainText(), self.folio(self.page))
                )

    # -- testatine e folio ------------------------------------------------
    def _decorate(self, canvas, doc):
        if not self.page_has_content:
            self.page_has_content = False
            return  # pagina bianca: niente testatina, niente numero
        if not self.in_front_matter and self.page not in self.plain_pages:
            self._draw_running_head(canvas)
            self._draw_folio(canvas)
        self.page_has_content = False

    def _draw_running_head(self, canvas):
        geo = self.geo
        is_recto = self.page % 2 == 1
        style = self.styles["running_head"]
        text = self.current_chapter if is_recto else self.spec.title
        if not text:
            return
        y = geo.page_height - geo.top_margin + 0.28 * INCH
        left = geo.inner_margin if is_recto else geo.outer_margin
        canvas.saveState()
        canvas.setFillColor(style.textColor)
        draw_tracked_string(
            canvas,
            left + geo.text_width if is_recto else left,
            y,
            text.upper(),
            style.fontName,
            style.fontSize,
            0.4,
            align="right" if is_recto else "left",
        )
        canvas.restoreState()

    def _draw_folio(self, canvas):
        geo = self.geo
        style = self.styles["folio"]
        canvas.saveState()
        canvas.setFont(style.fontName, style.fontSize)
        canvas.setFillColor(style.textColor)
        canvas.drawCentredString(
            geo.page_width / 2.0, geo.bottom_margin - 0.36 * INCH, str(self.folio(self.page))
        )
        canvas.restoreState()


# --------------------------------------------------------------------------
# Stili
# --------------------------------------------------------------------------
def build_styles(spec: BookSpec) -> dict[str, ParagraphStyle]:
    body_font = register_family(spec.body_font)
    if spec.is_medium_content:
        # Le schede di un medium-content vivono di contrasto: i titoli stanno in
        # un'altra famiglia, e si vedono da lontano.
        display_font = register_family("sans" if spec.body_font == "serif" else "serif")
        heading_font = display_font
        heading_size = spec.body_font_size + 1.5
    else:
        # Un'opera a testo pieno ha una famiglia sola, come i libri di un editore:
        # i titoli si distinguono per corpo e peso, non per un secondo carattere.
        # Il bastone sotto il testo graziato era il segno più visibile del libro
        # fatto in casa (rodaggio household-bills).
        display_font = body_font
        heading_font = f"{body_font}-Bold"
        heading_size = spec.body_font_size + 1
    size = spec.body_font_size
    lead = spec.leading
    ink = colors.HexColor("#111111")
    soft = colors.HexColor("#555555")

    def style(name, **kwargs) -> ParagraphStyle:
        base = dict(
            name=name,
            fontName=body_font,
            # Senza questo ReportLab userebbe Helvetica per i punti elenco:
            # è un font non incorporato e il PDF verrebbe segnalato in preflight.
            bulletFontName=body_font,
            fontSize=size,
            leading=lead,
            textColor=ink,
            alignment=TA_JUSTIFY,
            allowWidows=0,
            allowOrphans=0,
        )
        base.update(kwargs)
        return ParagraphStyle(**base)

    return {
        "body": style("Body", firstLineIndent=0.22 * INCH),
        "body_first": style("BodyFirst", firstLineIndent=0),
        # La didascalia è più piccola e centrata, e non è giustificata: una
        # riga sola giustificata si apre in mezzo e sembra un errore.
        "caption": style(
            "Caption",
            fontSize=size - 1.5,
            leading=(size - 1.5) * 1.25,
            textColor=soft,
            alignment=TA_CENTER,
            firstLineIndent=0,
        ),
        "quote": style(
            "Quote",
            leftIndent=0.28 * INCH,
            rightIndent=0.28 * INCH,
            fontSize=size - 0.5,
            leading=lead - 1,
            textColor=soft,
            spaceBefore=lead * 0.5,
            spaceAfter=lead * 0.5,
            alignment=TA_LEFT,
        ),
        "bullet": style(
            "Bullet",
            leftIndent=0.3 * INCH,
            bulletIndent=0.12 * INCH,
            spaceAfter=lead * 0.18,
            alignment=TA_LEFT,
        ),
        "h2": style(
            "Heading2",
            fontName=heading_font,
            fontSize=heading_size,
            leading=lead + 2,
            spaceBefore=lead * 1.2,
            spaceAfter=lead * 0.45,
            alignment=TA_LEFT,
            textColor=ink,
        ),
        "h3": style(
            "Heading3",
            fontName=body_font,
            fontSize=size + 0.5,
            leading=lead,
            spaceBefore=lead * 0.9,
            spaceAfter=lead * 0.3,
            alignment=TA_LEFT,
        ),
        "part_title": style(
            "PartTitle",
            fontName=display_font,
            fontSize=size + 11,
            leading=(size + 11) * 1.25,
            alignment=TA_CENTER,
            spaceBefore=0,
            spaceAfter=lead * 0.8,
        ),
        "chapter_title": style(
            "ChapterTitle",
            fontName=display_font,
            fontSize=size + 9,
            leading=(size + 9) * 1.2,
            alignment=TA_CENTER,
            spaceBefore=0,
            spaceAfter=lead * 0.6,
        ),
        "title_main": style(
            "TitleMain",
            fontName=display_font,
            fontSize=size + 15,
            leading=(size + 15) * 1.2,
            alignment=TA_CENTER,
        ),
        "title_sub": style(
            "TitleSub",
            fontName=body_font,
            fontSize=size + 2,
            leading=(size + 2) * 1.3,
            alignment=TA_CENTER,
            textColor=soft,
        ),
        "author": style("Author", fontSize=size + 1, alignment=TA_CENTER),
        "front": style("Front", fontSize=size - 1.5, leading=lead - 2, alignment=TA_LEFT),
        "front_center": style(
            "FrontCenter", fontSize=size - 1, leading=lead - 1, alignment=TA_CENTER, textColor=soft
        ),
        "toc_title": style(
            "TocTitle",
            fontName=display_font,
            fontSize=size + 7,
            leading=(size + 7) * 1.2,
            alignment=TA_CENTER,
            spaceAfter=lead * 1.5,
        ),
        "toc_part": style(
            "TocPart",
            fontName=display_font,
            alignment=TA_LEFT,
            fontSize=size,
            leading=lead * 1.1,
            spaceBefore=lead * 0.7,
            spaceAfter=lead * 0.15,
        ),
        "toc1": style("Toc1", alignment=TA_LEFT, fontSize=size, leading=lead * 1.1),
        "toc2": style(
            "Toc2",
            alignment=TA_LEFT,
            fontSize=size - 1,
            leading=lead,
            leftIndent=0.25 * INCH,
            textColor=soft,
        ),
        "running_head": style(
            "RunningHead", fontName=body_font, fontSize=size - 2.5, textColor=soft
        ),
        "folio": style("Folio", fontName=body_font, fontSize=size - 1, textColor=ink),
        "chapter_number": style("ChapterNumber", fontName=display_font, fontSize=size - 2),
    }


# --------------------------------------------------------------------------
# Costruzione della storia
# --------------------------------------------------------------------------
class Segnaposto(Flowable):
    """Il posto di una figura che non c'è ancora.

    Occupa esattamente lo spazio che occuperà l'immagine, così il conteggio
    pagine è già quello definitivo: quando il file arriva, il libro non cambia
    lunghezza. Dentro c'è scritto che cosa deve mostrare, perché una prova di
    stampa con dei rettangoli vuoti non dice a nessuno che cosa manca.
    """

    def __init__(self, larghezza: float, altezza: float, descrizione: str, font: str):
        super().__init__()
        self.width = larghezza
        self.height = altezza
        self.descrizione = descrizione
        self.font = font

    def draw(self) -> None:
        canvas = self.canv
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#BBBBBB"))
        canvas.setFillColor(colors.HexColor("#F4F4F4"))
        canvas.setDash(3, 3)
        canvas.setLineWidth(0.7)
        canvas.rect(0, 0, self.width, self.height, stroke=1, fill=1)
        canvas.setDash()
        canvas.setFillColor(colors.HexColor("#777777"))
        corpo = min(9.0, self.height * 0.14)
        canvas.setFont(self.font, corpo)
        canvas.drawCentredString(self.width / 2, self.height / 2 + corpo, "IMMAGINE DA PRODURRE")
        testo = self.descrizione[:90] + ("…" if len(self.descrizione) > 90 else "")
        canvas.setFont(self.font, corpo * 0.85)
        canvas.drawCentredString(self.width / 2, self.height / 2 - corpo * 0.6, testo)
        canvas.restoreState()


def _figura_flowables(
    block: mdlite.Figure, styles: dict, assets_dir: Path | None,
    measure: float, frame_height: float, prepared_dir: Path | None,
) -> list:
    """L'immagine, o il suo segnaposto, più l'eventuale didascalia."""
    figura = figure_module.risolvi(block, assets_dir or Path("."))
    larghezza, altezza = figure_module.misura(figura, measure, frame_height)

    if figura.esiste and prepared_dir is not None:
        sorgente = figure_module.prepara(
            figura, prepared_dir / f"grigio-{Path(figura.percorso).name}"
        )
        disegno = Image(str(sorgente), width=larghezza, height=altezza)
    elif figura.esiste:
        disegno = Image(str(figura.file), width=larghezza, height=altezza)
    else:
        disegno = Segnaposto(larghezza, altezza, block.descrizione, styles["body"].fontName)

    disegno.hAlign = "CENTER"
    pezzi: list = [Spacer(1, styles["body"].leading * 0.5), disegno]
    if block.didascalia:
        pezzi.append(Spacer(1, styles["body"].leading * 0.25))
        pezzi.append(Paragraph(mdlite.inline_to_markup(block.didascalia), styles["caption"]))
    pezzi.append(Spacer(1, styles["body"].leading * 0.5))
    # Didascalia e immagine non si separano mai: una didascalia orfana in cima
    # alla pagina dopo è il difetto tipografico più visibile che ci sia.
    return [KeepTogether(pezzi)]


#: Quanto scende l'apertura di capitolo, in frazione della gabbia. Nei libri di
#: un editore il testo del capitolo comincia intorno a un terzo della pagina: il
#: bianco sopra il titolo dice «qui comincia una cosa nuova» prima di ogni parola.
CALATA_TESTO_PIENO = 0.2
CALATA_MEDIUM_IN = 0.55

#: Le prime parole del capitolo in maiuscoletto: al massimo tante, e mai oltre
#: la prima pausa della frase.
PAROLE_MAIUSCOLETTO = 3
_PAUSA = (",", ".", ";", ":", "!", "?", "—")
#: caratteri che `mdlite.inline_to_markup` trasforma: se cadono nell'attacco, il
#: capoverso resta senza maiuscoletto (le virgolette diritte si accoppiano sul
#: capoverso intero, e tagliarlo a metà le girerebbe al contrario)
_MARKUP_INLINE = set('*_`[]<>&"\\')


def _calata(spec: BookSpec, geo: kdpspecs.PageGeometry) -> float:
    """Il bianco sopra il numero del capitolo.

    Il medium-content resta compatto: le sue pagine sono schede, e una scheda
    che comincia a metà pagina ne perde metà.
    """
    if spec.is_medium_content:
        return CALATA_MEDIUM_IN * INCH
    return geo.text_height * CALATA_TESTO_PIENO


def _maiuscoletto(testo: str, corpo: float) -> str | None:
    """Il primo capoverso con le prime parole in maiuscoletto, come markup.

    ReportLab non ha il maiuscoletto vero: lo si imita con il maiuscolo a corpo
    ridotto, che sulle tre parole d'attacco è quello che fa anche la tipografia
    editoriale senza font dedicati. Se le prime parole contengono markup
    (corsivo, codice, link) il capoverso resta com'è: spezzarlo a metà di un tag
    darebbe un PDF sbagliato, e un attacco senza maiuscoletto non è un difetto.
    """
    parole = testo.split(" ")
    attacco: list[str] = []
    for parola in parole:
        if not parola:
            break
        attacco.append(parola)
        if len(attacco) >= PAROLE_MAIUSCOLETTO or parola.endswith(_PAUSA):
            break
    if not attacco or len(attacco) == len(parole):
        return None
    testa = " ".join(attacco)
    if any(c in _MARKUP_INLINE for c in testa):
        return None
    resto = testo[len(testa):]
    return f'<font size="{corpo * 0.84:.1f}">{testa.upper()}</font>' + mdlite.inline_to_markup(resto)


#: La coda di un capoverso legata con spazi unificatori: almeno tanti caratteri,
#: al massimo tante parole. Un'ultima riga di una parola sola («it.») è il buco
#: che il compositore di un editore toglie per primo.
CODA_MIN_CARATTERI = 10
CODA_MAX_PAROLE = 3


def _lega_coda(testo: str) -> str:
    """Le ultime parole del capoverso unite da spazi unificatori, così l'ultima
    riga non resta mai con una parola corta da sola.

    ReportLab tratta lo spazio unificatore come parte della parola: le parole
    legate vanno a capo insieme. Un capoverso di poche parole resta com'è.
    """
    parole = testo.rstrip().split(" ")
    if len(parole) <= CODA_MAX_PAROLE * 2:
        return testo
    coda = [parole.pop()]
    while len(coda) < CODA_MAX_PAROLE and len(" ".join(coda)) < CODA_MIN_CARATTERI:
        coda.insert(0, parole.pop())
    return " ".join(parole) + " " + "\u00a0".join(coda)


#: Le righe di testo che un titoletto deve avere sotto di sé sulla stessa pagina:
#: due, la regola dei libri di un editore (un titoletto con una riga sola sotto
#: sembra un errore, con tre si allungano le pagine corte).
RIGHE_SOTTO_TITOLO = 2


def _riserva_titolo(titolo: Paragraph, seguito, measure: float) -> float:
    """Lo spazio da chiedere prima di un titoletto seguito da un capoverso lungo.

    Zero vuol dire «tienili insieme per intero»: succede quando il seguito non è
    un capoverso o è così corto che spostarlo non costa niente, e quando la
    giustezza non è nota (le pagine finali), perché senza non si misura niente.
    """
    if not measure or not isinstance(seguito, Paragraph):
        return 0.0
    interlinea = seguito.style.leading
    _, altezza_seguito = seguito.wrap(measure, 10_000)
    if altezza_seguito <= interlinea * (RIGHE_SOTTO_TITOLO + 0.5):
        return 0.0
    _, altezza_titolo = titolo.wrap(measure, 10_000)
    stile = titolo.style
    return stile.spaceBefore + altezza_titolo + stile.spaceAfter + interlinea * RIGHE_SOTTO_TITOLO


def markdown_to_flowables(
    markdown: str,
    styles: dict,
    *,
    first_paragraph_flush: bool = True,
    assets_dir: Path | None = None,
    measure: float = 0.0,
    frame_height: float = 0.0,
    prepared_dir: Path | None = None,
    lead_in: bool = False,
) -> list:
    flowables: list = []
    first_para_done = not first_paragraph_flush
    pending_heading: Paragraph | None = None
    # Il maiuscoletto d'attacco va sul primo capoverso del capitolo, se il
    # capitolo comincia con un capoverso: dopo un titoletto non serve.
    attacco_da_fare = lead_in

    def emit(flowable) -> None:
        """Un titolo non resta mai da solo in fondo alla pagina.

        Gli basta avere sotto qualche riga del capoverso che segue, non il
        capoverso intero: tenerli insieme in blocco spostava alla pagina dopo
        anche un capoverso di quindici righe, e lasciava un quarto di pagina
        bianco sopra un titoletto (rodaggio household-bills, 11 pagine corte su
        192). Con un capoverso lungo si chiede solo lo spazio per il titolo e
        `RIGHE_SOTTO_TITOLO` righe; il resto lo spezza il capoverso stesso,
        senza orfane. Un capoverso breve, un elenco o una citazione restano
        attaccati al titolo per intero: sono poche righe.
        """
        nonlocal pending_heading
        if pending_heading is None:
            flowables.append(flowable)
            return
        riserva = _riserva_titolo(pending_heading, flowable, measure)
        if riserva:
            flowables.extend([CondPageBreak(riserva), pending_heading, flowable])
        else:
            flowables.append(KeepTogether([pending_heading, flowable]))
        pending_heading = None

    for block in mdlite.parse(markdown):
        if isinstance(block, mdlite.Heading) and block.level <= 1:
            continue  # il titolo del capitolo è gestito a parte
        attacco, attacco_da_fare = attacco_da_fare, False
        if isinstance(block, mdlite.Heading):
            style = styles["h2"] if block.level == 2 else styles["h3"]
            if pending_heading is not None:
                flowables.append(pending_heading)
            pending_heading = Paragraph(mdlite.inline_to_markup(block.text), style)
            first_para_done = False
        elif isinstance(block, mdlite.Paragraph):
            style = styles["body"] if first_para_done else styles["body_first"]
            testo = _lega_coda(block.text)
            markup = _maiuscoletto(testo, style.fontSize) if attacco else None
            emit(Paragraph(markup or mdlite.inline_to_markup(testo), style))
            first_para_done = True
        elif isinstance(block, mdlite.BulletList):
            items = [
                Paragraph(
                    mdlite.inline_to_markup(_lega_coda(item)),
                    styles["bullet"],
                    bulletText=f"{index}." if block.ordered else "\u2022",
                )
                for index, item in enumerate(block.items, start=1)
            ]
            emit(items[0])
            flowables.extend(items[1:])
            first_para_done = True
        elif isinstance(block, mdlite.Quote):
            emit(Paragraph(mdlite.inline_to_markup(block.text), styles["quote"]))
            first_para_done = True
        elif isinstance(block, mdlite.Figure):
            if pending_heading is not None:
                flowables.append(pending_heading)
                pending_heading = None
            flowables.extend(
                _figura_flowables(
                    block, styles, assets_dir,
                    measure or styles["body"].leading * 24,
                    frame_height or styles["body"].leading * 40,
                    prepared_dir,
                )
            )
            first_para_done = True
        elif isinstance(block, mdlite.Rule):
            flowables.append(Spacer(1, styles["body"].leading * 0.4))
            flowables.append(
                Paragraph("* * *", ParagraphStyle("SceneBreak", parent=styles["body"],
                                                  alignment=TA_CENTER, firstLineIndent=0))
            )
            flowables.append(Spacer(1, styles["body"].leading * 0.4))
            first_para_done = False

    if pending_heading is not None:
        flowables.append(pending_heading)
    return flowables


def _front_matter(spec: BookSpec, outline: Outline, styles: dict, year: int) -> list:
    lang = spec.language
    story: list = []

    # Occhiello
    story.append(DocAction("front_matter_page"))
    story.append(Spacer(1, 1.6 * INCH))
    story.append(Paragraph(mdlite.inline_to_markup(spec.title), styles["title_sub"]))
    story.append(PageBreak())
    story.append(PageBreak())  # bianca

    # Frontespizio
    story.append(Spacer(1, 1.4 * INCH))
    story.append(Paragraph(mdlite.inline_to_markup(spec.title), styles["title_main"]))
    if spec.subtitle:
        story.append(Spacer(1, 0.18 * INCH))
        story.append(Paragraph(mdlite.inline_to_markup(spec.subtitle), styles["title_sub"]))
    story.append(Spacer(1, 0.6 * INCH))
    story.append(Paragraph(mdlite.inline_to_markup(spec.author), styles["author"]))
    story.append(PageBreak())

    # Colophon
    copyright_lines = [
        f"© {year} {spec.author}. {L(lang, 'copyright')}",
        L(lang, "copyright_body"),
        "",
        L(lang, "disclaimer_title") + ": " + (spec.disclaimer.strip() or L(lang, "disclaimer_body")),
        "",
        L(lang, "ai_disclosure"),
        "",
        L(lang, "first_edition") + f" – {year}",
    ]
    if spec.isbn:
        copyright_lines.append(f"{L(lang, 'isbn')}: {spec.isbn}")
    if spec.publisher:
        copyright_lines.append(spec.publisher)
    copyright_lines.append(L(lang, "printed_by"))
    story.append(Spacer(1, 3.2 * INCH))
    for line in copyright_lines:
        if line:
            story.append(Paragraph(mdlite.inline_to_markup(line), styles["front"]))
        else:
            story.append(Spacer(1, styles["front"].leading * 0.6))
    story.append(PageBreak())

    # Dedica
    if spec.dedication:
        story.append(Spacer(1, 2.2 * INCH))
        story.append(Paragraph(mdlite.inline_to_markup(spec.dedication), styles["front_center"]))
        story.append(PageBreak())
        story.append(PageBreak())

    # Indice
    toc = TableOfContents()
    toc.levelStyles = [styles["toc1"], styles["toc2"]]
    if outline.parts:
        toc.levelStyles = [styles["toc_part"], styles["toc1"], styles["toc2"]]
    toc.dotsMinLevel = 0
    # L'indice è costruito con una tabella e le celle di ReportLab nascono con
    # Helvetica: va forzato il font incorporato, altrimenti il PDF dichiara un
    # font non incorporato e non supera il preflight di KDP.
    toc.tableStyle = TableStyle(
        [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("FONTNAME", (0, 0), (-1, -1), styles["toc1"].fontName),
        ]
    )
    story.append(Paragraph(L(lang, "toc"), styles["toc_title"]))
    story.append(toc)
    return story


def _back_matter(spec: BookSpec, styles: dict, author_bio: str = "") -> list:
    lang = spec.language
    # Le pagine finali non appartengono all'ultima parte: nell'indice tornano
    # al primo livello.
    story: list = [DocAction("parts_end")]
    if author_bio:
        story.append(StartOnRecto())
        story.append(DocAction("chapter_open", L(lang, "about_author")))
        story.append(Spacer(1, 0.6 * INCH))
        story.append(Paragraph(L(lang, "about_author"), styles["chapter_title"]))
        story.append(Spacer(1, 0.25 * INCH))
        story.extend(markdown_to_flowables(author_bio, styles))

    story.append(StartOnRecto())
    story.append(DocAction("chapter_open", L(lang, "review_title")))
    story.append(Spacer(1, 0.6 * INCH))
    story.append(Paragraph(L(lang, "review_title"), styles["chapter_title"]))
    story.append(Spacer(1, 0.25 * INCH))
    story.append(Paragraph(L(lang, "review_text"), styles["body_first"]))
    return story


def _part_page(apertura, styles: dict, lang: str) -> list:
    """La pagina che apre una parte: etichetta, titolo, filetto. Niente folio."""
    indice, parte = apertura
    etichetta = part_label(lang, indice)
    return [
        DocAction("part_open", etichetta),
        Spacer(1, 2.3 * INCH),
        ChapterNumber(
            etichetta,
            styles["chapter_number"].fontName,
            styles["chapter_number"].fontSize + 1,
            colors.HexColor("#777777"),
        ),
        Paragraph(mdlite.inline_to_markup(parte.title), styles["part_title"]),
        HRFlowable(
            width="14%", thickness=0.7, color=colors.HexColor("#999999"),
            spaceBefore=2, spaceAfter=0, hAlign="CENTER",
        ),
    ]


@dataclass
class TypesetResult:
    pdf_path: Path
    pages: int
    words: int
    chapter_pages: dict[str, int] = field(default_factory=dict)
    words_by_chapter: dict[int, int] = field(default_factory=dict)
    part_pages: dict[str, int] = field(default_factory=dict)
    #: pagine fisiche prima della pagina 1 stampata: `chapter_pages` è fisico,
    #: il numero che legge il cliente è `pagina - folio_offset`
    folio_offset: int = 0

    def to_dict(self) -> dict:
        return {
            "pdf": str(self.pdf_path),
            "pages": self.pages,
            "words": self.words,
            "chapter_pages": self.chapter_pages,
            "part_pages": self.part_pages,
            "folio_offset": self.folio_offset,
            "words_by_chapter": {str(k): v for k, v in self.words_by_chapter.items()},
        }


def typeset(
    spec: BookSpec,
    outline: Outline,
    chapters: list[tuple[int, str, str]],
    output: Path,
    *,
    author_bio: str = "",
    year: int | None = None,
    assets_dir: Path | None = None,
) -> TypesetResult:
    """Impagina il libro. `chapters` è una lista (numero, titolo, markdown)."""
    import datetime

    year = year or spec.year or datetime.date.today().year
    styles = build_styles(spec)
    set_default_canvas_font(styles["body"].fontName)
    enable_hyphenation(spec.language)

    # La geometria dipende dal numero di pagine (margine interno): si parte
    # dalla stima e la si corregge dopo la prima misurazione.
    estimated_pages = spec.target_pages
    geo = kdpspecs.page_geometry(spec.trim, estimated_pages)

    output.parent.mkdir(parents=True, exist_ok=True)
    pad_to_even = False
    result = _run_typeset(spec, outline, chapters, output, styles, geo, author_bio,
                          year, pad_to_even, assets_dir)

    # Due correzioni successive: il margine interno dipende dal numero di pagine
    # (che si conosce solo dopo l'impaginazione) e il totale deve essere pari,
    # perché ogni foglio stampato ha due facciate.
    for _ in range(3):
        needs_gutter_fix = kdpspecs.gutter_margin_in(result.pages) != kdpspecs.gutter_margin_in(
            estimated_pages
        )
        needs_padding = result.pages % 2 == 1
        if not needs_gutter_fix and not needs_padding:
            break
        estimated_pages = result.pages
        geo = kdpspecs.page_geometry(spec.trim, result.pages)
        pad_to_even = pad_to_even or needs_padding
        result = _run_typeset(
            spec, outline, chapters, output, styles, geo, author_bio, year,
            pad_to_even, assets_dir,
        )
    return result


def _run_typeset(
    spec, outline, chapters, output, styles, geo, author_bio, year,
    pad_to_even=False, assets_dir=None,
) -> TypesetResult:
    doc = InteriorDoc(str(output), spec, geo, styles)
    lang = spec.language

    story: list = _front_matter(spec, outline, styles, year)
    story.append(StartOnRecto())
    story.append(DocAction("body_start"))

    words_by_chapter: dict[int, int] = {}
    chapter_index = 0
    display_number = 0
    for number, title, markdown in chapters:
        plan = next((c for c in outline.chapters if c.number == number), None)
        role = plan.role if plan else "chapter"
        apertura = outline.part_opening(number)
        if apertura:
            if chapter_index:
                story.append(StartOnRecto())
            story.extend(_part_page(apertura, styles, lang))
        if chapter_index or apertura:
            story.append(StartOnRecto())
        chapter_index += 1

        story.append(DocAction("chapter_open", title))
        story.append(Spacer(1, _calata(spec, geo)))
        titolo = Paragraph(mdlite.inline_to_markup(title), styles["chapter_title"])
        if role == "chapter":
            display_number += 1
            label = f"{L(lang, 'chapter')} {display_number}"
            story.append(
                ChapterNumber(
                    label,
                    styles["chapter_number"].fontName,
                    styles["chapter_number"].fontSize,
                    colors.HexColor("#777777"),
                )
            )
            titolo.numero_capitolo = display_number
        story.append(titolo)
        story.append(
            HRFlowable(
                width="22%", thickness=0.7, color=colors.HexColor("#999999"),
                spaceBefore=2, spaceAfter=14, hAlign="CENTER",
            )
        )
        story.extend(
            markdown_to_flowables(
                markdown,
                styles,
                assets_dir=assets_dir,
                measure=geo.text_width,
                frame_height=geo.text_height,
                prepared_dir=output.parent / "immagini",
                lead_in=not spec.is_medium_content,
            )
        )
        words_by_chapter[number] = mdlite.count_words(markdown)

    story.extend(_back_matter(spec, styles, author_bio))
    if pad_to_even:
        story.append(PageBreak())
        story.append(BlankFiller())

    doc.multiBuild(story)

    return TypesetResult(
        pdf_path=Path(output),
        pages=doc.page,
        words=sum(words_by_chapter.values()),
        chapter_pages=dict(doc.chapter_pages),
        words_by_chapter=words_by_chapter,
        part_pages=dict(doc.part_pages),
        folio_offset=doc.folio_offset,
    )

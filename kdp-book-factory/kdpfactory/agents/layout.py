"""Agente di impaginazione: controlla il PDF reale, non il manoscritto.

È l'unico agente del collegio che non usa il modello: i difetti tipografici si
misurano sulle coordinate del testo nella pagina, e una misura è più affidabile
di un giudizio. Serve PyMuPDF; senza, l'agente lo dichiara e si ferma.

Che cosa guarda, nell'ordine in cui un tipografo sfoglierebbe le bozze:
righe vedove e orfane, titoli rimasti in fondo alla pagina, code di capitolo
troppo corte, testo fuori dalla gabbia, scalette di sillabazione, aperture di
capitolo sulla pagina sbagliata.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .. import kdpspecs
from .base import Agent, AgentContext, AgentFinding, AgentResult, register

INDENT_TOLERANCE = 4.0     # punti: sotto questa soglia una riga è allineata al margine
MAX_INDENT = 40.0          # oltre non è un rientro di capoverso: è una colonna di tabella
SHORT_LINE_RATIO = 0.55    # riga "corta": meno del 55% della giustezza
TINY_LINE_RATIO = 0.12     # riga finale di paragrafo molto corta
FRAME_TOLERANCE = 2.0      # punti di tolleranza sul bordo della gabbia
CHAPTER_TAIL_RATIO = 0.12  # coda di capitolo: pagina riempita per meno del 12%


@dataclass
class Line:
    page: int
    text: str
    x0: float
    x1: float
    y0: float
    y1: float
    size: float
    font: str

    @property
    def width(self) -> float:
        return self.x1 - self.x0


def _collect_lines(document, geo: kdpspecs.PageGeometry) -> list[Line]:
    """Righe di testo dentro la gabbia, escluse testatine e numeri di pagina."""
    lines: list[Line] = []
    top = geo.top_margin - FRAME_TOLERANCE
    bottom = geo.page_height - geo.bottom_margin + FRAME_TOLERANCE
    for index, page in enumerate(document, start=1):
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue
                text = "".join(span["text"] for span in spans).strip()
                if not text:
                    continue
                x0, y0, x1, y1 = line["bbox"]
                if y0 < top or y1 > bottom:
                    continue  # testatina o folio
                biggest = max(spans, key=lambda s: s["size"])
                lines.append(
                    Line(
                        page=index,
                        text=text,
                        x0=x0,
                        x1=x1,
                        y0=y0,
                        y1=y1,
                        size=round(biggest["size"], 1),
                        font=biggest["font"],
                    )
                )
    return lines


def _pages_label(pages: list[int], limit: int = 6) -> str:
    shown = ", ".join(str(p) for p in pages[:limit])
    return shown + (f" e altre {len(pages) - limit}" if len(pages) > limit else "")


@register
class Impaginazione(Agent):
    name = "impaginazione"
    title = "Controllo impaginazione"
    description = (
        "Controlla il PDF impaginato: righe vedove e orfane, titoli in fondo alla pagina, "
        "code di capitolo, testo fuori gabbia, sillabazione, aperture di capitolo. "
        "Non usa il modello: misura le coordinate del testo."
    )
    stage = "controllo"

    def system(self, ctx: AgentContext) -> list[str]:  # pragma: no cover - non usato
        return []

    def user(self, ctx: AgentContext) -> str:  # pragma: no cover - non usato
        return ""

    def run(self, ctx: AgentContext, client=None) -> AgentResult:
        findings = inspect_layout(ctx)
        notes = (
            "Impaginazione senza difetti rilevanti."
            if not findings
            else f"{len(findings)} difetti di impaginazione da guardare."
        )
        return AgentResult(agent=self.name, findings=findings, notes=notes)


def inspect_layout(ctx: AgentContext) -> list[AgentFinding]:
    if not ctx.pdf_path or not ctx.pdf_path.exists():
        return [
            AgentFinding(
                agent=Impaginazione.name,
                severity="importante",
                category="pdf mancante",
                issue="Nessun PDF da controllare: esegui prima `build`.",
            )
        ]
    try:
        import pymupdf
    except ImportError:
        return [
            AgentFinding(
                agent=Impaginazione.name,
                severity="minore",
                category="strumento mancante",
                issue="PyMuPDF non installato: controllo impaginazione saltato.",
                suggestion="pip install pymupdf",
            )
        ]

    geo = kdpspecs.page_geometry(ctx.spec.trim, ctx.pages or 100)
    document = pymupdf.open(ctx.pdf_path)
    try:
        lines = _collect_lines(document, geo)
        page_count = document.page_count
        chapter_title_pages = _verify_chapter_openings(document, ctx)
    finally:
        document.close()

    if not lines:
        return [
            AgentFinding(
                agent=Impaginazione.name,
                severity="bloccante",
                category="pagina vuota",
                issue="Il PDF non contiene testo dentro la gabbia: impaginazione da rifare.",
            )
        ]

    measure = geo.text_width
    body_size, body_font = _body_face(lines, measure)
    by_page: dict[int, list[Line]] = {}
    for line in lines:
        by_page.setdefault(line.page, []).append(line)
    for page_lines in by_page.values():
        page_lines.sort(key=lambda line: line.y0)

    # Il bordo sinistro reale si misura sul PDF, non si deduce dai margini:
    # pagine pari e dispari hanno margini speculari.
    flush_left = _flush_left_by_parity(lines)
    # Le pagine preliminari (occhiello, frontespizio, colophon, indice) hanno
    # regole tipografiche proprie: i controlli partono dal primo capitolo.
    body_start = min(ctx.chapter_pages.values(), default=1)

    findings: list[AgentFinding] = []
    indent = _measure_first_line_indent(by_page, flush_left, body_size)
    findings += _check_widows_orphans(
        by_page, page_count, measure, body_size, body_font, flush_left, indent, body_start
    )
    findings += _check_frame_overflow(lines, geo)
    findings += _check_hyphen_ladders(by_page)
    findings += _check_short_last_lines(lines, measure, body_size, flush_left, indent)
    findings += _check_chapter_tails(by_page, ctx, geo)
    findings += _check_page_variety(by_page, ctx, body_start)
    findings += chapter_title_pages
    return findings


#: Oltre questa quota di pagine strutturalmente identiche il libro non è più un
#: medium-content: è un blocco di pagine uguali, cioè low-content.
MAX_IDENTICAL_PAGES_RATIO = 0.5
#: Sotto questo numero di pagine di testo la misura non dice niente.
MIN_PAGES_FOR_VARIETY = 12


def _page_signature(page_lines: list[Line]) -> tuple:
    """Impronta strutturale di una pagina: com'è fatta, non che cosa dice.

    Due pagine con la stessa impronta si possono scambiare senza che il lettore
    se ne accorga — è il banco di prova del confine col low-content.
    """
    righe = len(page_lines)
    corpi = tuple(sorted({round(line.size * 2) / 2 for line in page_lines}))
    # I bordi sinistri distinguono una griglia o una tabella dal testo corrente:
    # arrotondati a 6 punti per non contare gli scarti di misura.
    bordi = len({round(line.x0 / 6) for line in page_lines})
    caratteri = sum(len(line.text) for line in page_lines)
    return (righe // 3, corpi, bordi, caratteri // 200)


def _check_page_variety(
    by_page: dict[int, list[Line]], ctx: AgentContext, body_start: int
) -> list[AgentFinding]:
    """Solo per i medium-content: ogni pagina deve avere qualcosa di suo."""
    if not ctx.spec.is_medium_content:
        return []
    pagine = {n: righe for n, righe in by_page.items() if n >= body_start and righe}
    if len(pagine) < MIN_PAGES_FOR_VARIETY:
        return []

    conteggio: dict[tuple, list[int]] = {}
    for numero, righe in pagine.items():
        conteggio.setdefault(_page_signature(righe), []).append(numero)
    impronta, uguali = max(conteggio.items(), key=lambda voce: len(voce[1]))
    quota = len(uguali) / len(pagine)
    if quota <= MAX_IDENTICAL_PAGES_RATIO:
        return []
    return [
        AgentFinding(
            agent=Impaginazione.name,
            severity="importante",
            category="varietà delle pagine",
            issue=(
                f"{len(uguali)} pagine su {len(pagine)} ({quota:.0%}) hanno la stessa "
                f"struttura: {_pages_label(sorted(uguali))}. Un medium-content vive del "
                "fatto che ogni pagina offre qualcosa di diverso; a questa quota è un "
                "blocco di pagine uguali, cioè low-content."
            ),
            suggestion=(
                "Alternare i tipi di pagina — esercizio guidato, scheda pratica, domanda "
                "di riflessione, griglia operativa — invece di ripetere lo stesso modulo."
            ),
        )
    ]


def _standalone(page_lines: list[Line]) -> list[Line]:
    """Righe che stanno da sole alla loro altezza.

    Una riga di tabella ha accanto le altre celle, un elenco ha il numero o il
    pallino alla stessa altezza del testo: in entrambi i casi la riga non è
    testo corrente e le regole su vedove e orfane non la riguardano.
    """
    by_row: dict[int, int] = {}
    for line in page_lines:
        key = round(line.y0)
        by_row[key] = by_row.get(key, 0) + 1
    return [line for line in page_lines if by_row[round(line.y0)] == 1]


def _body_face(lines: list[Line], measure: float) -> tuple[float, str]:
    """Corpo e font del testo corrente, misurati sulle righe che riempiono la
    giustezza.

    Contare tutte le righe darebbe il corpo delle celle: in un libro di enigmi
    le tabelle hanno più righe del testo, e il testo verrebbe scambiato per una
    serie di titoli.
    """
    full = [line for line in lines if line.width > measure * 0.6] or lines
    size = Counter(line.size for line in full).most_common(1)[0][0]
    font = Counter(line.font for line in full if line.size == size).most_common(1)[0][0]
    return size, font


def _flush_left_by_parity(lines: list[Line]) -> dict[int, float]:
    """Bordo sinistro della gabbia, misurato separatamente su pagine pari e dispari."""
    flush: dict[int, float] = {}
    for parity in (0, 1):
        values = [round(line.x0, 1) for line in lines if line.page % 2 == parity]
        if values:
            # Il valore più frequente è il margine: le righe rientrate sono poche.
            flush[parity] = Counter(values).most_common(1)[0][0]
    return flush


def _measure_first_line_indent(
    by_page: dict[int, list[Line]], flush_left: dict[int, float], body_size: float
) -> float | None:
    """Misura il rientro di prima riga osservando i capoversi certi.

    Un capoverso certo è una riga rientrata seguita da una riga a filo di
    margine. Serve a distinguere il rientro di capoverso dai rientri degli
    elenchi puntati, che valgono per tutte le righe del blocco.
    """
    indents: list[float] = []
    for page_lines in by_page.values():
        alone = _standalone(page_lines)
        for line, following in zip(alone, alone[1:], strict=False):
            left = flush_left.get(line.page % 2)
            if left is None or round(line.size, 1) != body_size:
                continue
            offset = line.x0 - left
            if (
                INDENT_TOLERANCE < offset <= MAX_INDENT
                and abs(following.x0 - left) < INDENT_TOLERANCE
            ):
                indents.append(round(offset, 1))
    if not indents:
        return None
    return Counter(indents).most_common(1)[0][0]


def _is_prose(line: Line, flush_left: dict[int, float], indent: float | None) -> bool:
    """Righe di testo corrente: a filo di margine o rientrate di un capoverso.

    Tutto il resto — celle di tabella, elenchi, citazioni — ha margini propri e
    non va giudicato con le regole di vedove e orfane.
    """
    left = flush_left.get(line.page % 2)
    if left is None:
        return False
    offset = line.x0 - left
    if abs(offset) < INDENT_TOLERANCE:
        return True
    return indent is not None and abs(offset - indent) < 1.5


def _is_paragraph_opening(
    line: Line, flush_left: dict[int, float], indent: float | None
) -> bool:
    """Vero se la riga apre un capoverso (rientro di prima riga, non elenco)."""
    left = flush_left.get(line.page % 2)
    if left is None or indent is None:
        return False
    return abs(line.x0 - (left + indent)) < 1.5


def _check_widows_orphans(
    by_page: dict[int, list[Line]],
    page_count: int,
    measure: float,
    body_size: float,
    body_font: str,
    flush_left: dict[int, float],
    indent: float | None,
    body_start: int = 1,
) -> list[AgentFinding]:
    widows: list[int] = []
    orphans: list[int] = []
    headings: list[int] = []

    for page in range(body_start, page_count + 1):
        page_lines = by_page.get(page, [])
        if len(page_lines) < 3:
            continue  # apertura di capitolo o pagina di coda: non fanno testo

        prose = [
            line
            for line in _standalone(page_lines)
            if _is_prose(line, flush_left, indent)
        ]
        if len(prose) < 3:
            continue  # pagina di tabelle o di elenchi: altre regole, altro mestiere

        first, second = prose[0], prose[1]
        # Vedova: la prima riga della pagina chiude il capoverso rimasto di là
        # (non è rientrata, ed è corta o seguita da un nuovo capoverso).
        if (
            round(first.size, 1) == body_size
            and not _is_paragraph_opening(first, flush_left, indent)
            and first.width < measure * SHORT_LINE_RATIO
            and (_is_paragraph_opening(second, flush_left, indent) or second.size != body_size)
        ):
            widows.append(page)

        last = page_lines[-1]
        # Un titolo si riconosce da due cose insieme: corpo più grande *e* font
        # diverso da quello del testo. Solo la dimensione non basta — in un libro
        # pieno di tabelle il corpo più frequente è quello delle celle.
        if last.size >= body_size + 1.5 and last.font != body_font:
            headings.append(page)      # titolo di sezione rimasto in fondo
        elif last is prose[-1] and _is_paragraph_opening(last, flush_left, indent):
            orphans.append(page)       # prima riga di un capoverso in fondo alla pagina

    findings: list[AgentFinding] = []
    if widows:
        findings.append(
            AgentFinding(
                agent=Impaginazione.name,
                severity="importante" if len(widows) > 3 else "minore",
                category="riga vedova",
                issue=f"{len(widows)} pagine iniziano con la riga finale del capoverso "
                f"precedente: pagine {_pages_label(widows)}.",
                suggestion="Accorcia o allunga di qualche parola il capoverso a cavallo "
                "delle due pagine, oppure lascia che l'editor riscriva quel passaggio.",
            )
        )
    if orphans:
        findings.append(
            AgentFinding(
                agent=Impaginazione.name,
                severity="importante" if len(orphans) > 3 else "minore",
                category="riga orfana",
                issue=f"{len(orphans)} pagine finiscono con la prima riga di un capoverso "
                f"nuovo: pagine {_pages_label(orphans)}.",
                suggestion="Stesso rimedio delle vedove: agisci sul testo, non sull'interlinea.",
            )
        )
    if headings:
        findings.append(
            AgentFinding(
                agent=Impaginazione.name,
                severity="importante",
                category="titolo a piede di pagina",
                issue=f"Titolo di sezione rimasto in fondo alla pagina: {_pages_label(headings)}.",
                suggestion="Il titolo deve restare attaccato al capoverso che introduce.",
            )
        )
    return findings


def _check_frame_overflow(lines: list[Line], geo: kdpspecs.PageGeometry) -> list[AgentFinding]:
    outside: list[int] = []
    for line in lines:
        left_limit = min(geo.inner_margin, geo.outer_margin) - FRAME_TOLERANCE
        right_limit = geo.page_width - min(geo.inner_margin, geo.outer_margin) + FRAME_TOLERANCE
        if line.x0 < left_limit or line.x1 > right_limit:
            outside.append(line.page)
    if not outside:
        return []
    pages = sorted(set(outside))
    return [
        AgentFinding(
            agent=Impaginazione.name,
            severity="bloccante",
            category="testo fuori gabbia",
            issue=f"Testo oltre i margini su {len(pages)} pagine: {_pages_label(pages)}.",
            suggestion="Di solito è una parola più lunga della giustezza (URL, termine "
            "composto): spezzala o riformula.",
        )
    ]


def _check_hyphen_ladders(by_page: dict[int, list[Line]]) -> list[AgentFinding]:
    ladders: list[int] = []
    for page, page_lines in by_page.items():
        streak = 0
        for line in page_lines:
            if line.text.endswith(("-", "‐", "­")):
                streak += 1
                if streak >= 3:
                    ladders.append(page)
                    break
            else:
                streak = 0
    if not ladders:
        return []
    return [
        AgentFinding(
            agent=Impaginazione.name,
            severity="minore",
            category="scaletta di sillabazione",
            issue=f"Tre o più righe consecutive che finiscono con un a capo sillabato: "
            f"pagine {_pages_label(sorted(set(ladders)))}.",
            suggestion="Difetto tipografico classico: si risolve cambiando qualche parola "
            "nel capoverso.",
        )
    ]


def _check_short_last_lines(
    lines: list[Line],
    measure: float,
    body_size: float,
    flush_left: dict[int, float],
    indent: float | None,
) -> list[AgentFinding]:
    by_page: dict[int, list[Line]] = {}
    for line in lines:
        by_page.setdefault(line.page, []).append(line)
    tiny = [
        line
        for page_lines in by_page.values()
        for line in _standalone(page_lines)
        if round(line.size, 1) == body_size
        and line.width < measure * TINY_LINE_RATIO
        and _is_prose(line, flush_left, indent)
    ]
    if len(tiny) < 5:
        return []
    return [
        AgentFinding(
            agent=Impaginazione.name,
            severity="minore",
            category="righe finali troppo corte",
            issue=f"{len(tiny)} capoversi finiscono con una riga di poche lettere "
            f"(pagine {_pages_label(sorted({line.page for line in tiny}))}).",
            suggestion="Una riga finale sotto il 12% della giustezza lascia un buco visibile: "
            "aggiungi o togli una parola al capoverso.",
        )
    ]


def _check_chapter_tails(
    by_page: dict[int, list[Line]], ctx: AgentContext, geo: kdpspecs.PageGeometry
) -> list[AgentFinding]:
    """Pagine di coda: un capitolo che finisce con due righe su una pagina nuova."""
    opening_pages = set(ctx.chapter_pages.values())
    if not opening_pages:
        return []
    tails: list[int] = []
    for opening in sorted(opening_pages):
        previous = opening - 1
        page_lines = by_page.get(previous, [])
        if not page_lines:
            continue  # pagina bianca prima dell'apertura: è voluta
        used = page_lines[-1].y1 - page_lines[0].y0
        if used < geo.text_height * CHAPTER_TAIL_RATIO:
            tails.append(previous)
    if not tails:
        return []
    return [
        AgentFinding(
            agent=Impaginazione.name,
            severity="minore",
            category="coda di capitolo",
            issue=f"Capitoli che finiscono con poche righe su una pagina quasi vuota: "
            f"pagine {_pages_label(tails)}.",
            suggestion="Accorcia il capitolo di qualche riga per farlo chiudere sulla pagina "
            "precedente, oppure allungalo fino a riempire almeno mezza pagina.",
        )
    ]


def _verify_chapter_openings(document, ctx: AgentContext) -> list[AgentFinding]:
    """Ogni capitolo si apre su pagina dispari e il titolo è dove dice l'indice."""
    findings: list[AgentFinding] = []
    wrong_side = [
        (title, page) for title, page in ctx.chapter_pages.items() if page % 2 == 0
    ]
    if wrong_side:
        titles = ", ".join(f"«{t}» (p. {p})" for t, p in wrong_side[:4])
        findings.append(
            AgentFinding(
                agent=Impaginazione.name,
                severity="importante",
                category="apertura di capitolo",
                issue=f"{len(wrong_side)} capitoli si aprono su pagina pari (sinistra): {titles}.",
                suggestion="Nei libri i capitoli si aprono a destra: controlla le pagine bianche "
                "di raccordo.",
            )
        )

    missing: list[str] = []
    for title, page in ctx.chapter_pages.items():
        if not 1 <= page <= document.page_count:
            missing.append(title)
            continue
        text = document[page - 1].get_text()
        if title.split()[0].lower() not in text.lower():
            missing.append(title)
    if missing:
        findings.append(
            AgentFinding(
                agent=Impaginazione.name,
                severity="importante",
                category="indice",
                issue=f"{len(missing)} titoli non compaiono sulla pagina indicata dall'indice: "
                + ", ".join(f"«{t}»" for t in missing[:4]),
                suggestion="Rigenera l'impaginato: l'indice si aggiorna solo dopo due passate.",
            )
        )
    return findings

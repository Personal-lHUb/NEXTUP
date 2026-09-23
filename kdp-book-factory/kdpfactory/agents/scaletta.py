"""Revisore di scaletta: controlla l'indice prima che diventi un libro.

Un capitolo scritto male si riscrive. Una scaletta sbagliata si paga trenta
volte, perché ogni capitolo eredita il difetto: due capitoli che dicono la
stessa cosa diventano tremila parole ripetute, un argomento chiesto
dall'autore e dimenticato nella scaletta non comparirà mai nel libro, una
promessa di guarigione messa in un titolo finisce stampata.

Come l'agente di impaginazione e quello di copertina, **non usa il modello**:
tutto quello che segnala si conta. Le sovrapposizioni sono un rapporto fra
insiemi di parole, la copertura degli argomenti è un confronto con `brief.md`,
i divieti sono un lessico, la lingua è una conta di parole grammaticali. Un
giudizio letterario sulla scaletta lo dà l'architetto — che però la scaletta
l'ha scritta lui, e quindi non è il controllo di cui c'è bisogno qui.

Le tre cose che questo agente esiste per impedire:

1. un argomento che l'autore ha chiesto e la scaletta non copre;
2. due capitoli che fanno lo stesso lavoro con parole diverse;
3. una promessa, una prova o un fatto storico dichiarato dove va una
   testimonianza.
"""

from __future__ import annotations

import math
import re
import unicodedata

from .. import coverdesign, kdpspecs
from ..models import BookSpec, Outline
from .base import Agent, AgentContext, AgentFinding, AgentResult, register

NOME = "revisore-scaletta"

# --------------------------------------------------------------------------
# Soglie: tutte dichiarate qui, perché una soglia nascosta in mezzo al codice
# è una regola che nessuno può discutere.
# --------------------------------------------------------------------------

#: due capitoli con questo indice di somiglianza fanno lo stesso lavoro
SOGLIA_GEMELLI = 0.45
#: sopra questa si assomigliano abbastanza da meritare un'occhiata
SOGLIA_VICINI = 0.30
#: quante parole distintive di un argomento deve ritrovare un capitolo
COPERTURA_PAROLE = 3
COPERTURA_QUOTA = 0.15
#: un riassunto più corto di così non è un programma di capitolo
MINIMO_PAROLE_RIASSUNTO = 10
#: quanti punti servono perché un capitolo sappia che cosa deve fare
MINIMO_BEATS = 2
#: quarta di copertina: gancio più due paragrafi, in una misura da retro libro
QUARTA_BLOCCHI = 3
QUARTA_MINIMO = 300
QUARTA_MASSIMO = 1400
#: quante parole guardare intorno a una parola vietata per cercare la negazione
FINESTRA_NEGAZIONE = 10

PAROLE_VUOTE = {
    # italiano
    "il", "lo", "la", "i", "gli", "le", "un", "uno", "una", "che", "chi", "cui",
    "non", "con", "per", "tra", "fra", "del", "della", "dei", "delle", "dello",
    "nel", "nella", "nei", "sul", "sulla", "come", "più", "meno", "anche", "già",
    "quando", "dove", "perché", "questo", "questa", "quello", "quella", "suo",
    "sua", "loro", "essere", "avere", "fare", "dire", "sono", "sia", "ogni",
    "dal", "dalla", "alla", "allo", "agli", "alle", "ma", "poi", "così",
    # inglese
    "the", "and", "for", "with", "that", "this", "these", "those", "from",
    "what", "when", "where", "which", "who", "whom", "whose", "why", "how",
    "into", "onto", "over", "under", "about", "after", "before", "between",
    "than", "then", "there", "here", "have", "has", "had", "been", "being",
    "was", "were", "are", "can", "could", "would", "should", "will", "shall",
    "not", "but", "her", "his", "its", "our", "your", "their", "them", "they",
    "you", "she", "him", "one", "two", "all", "any", "out", "own", "off",
    "does", "did", "done", "doing", "just", "also", "very", "much", "more",
    "most", "some", "such", "only", "same", "other", "each", "both", "because",
}

#: parole grammaticali usate per riconoscere la lingua della scaletta
SPIE_LINGUA = {
    "it": ("che", "non", "della", "per", "come", "nel", "una", "gli", "dei", "sono"),
    "en": ("the", "and", "that", "with", "what", "from", "this", "they", "have", "which"),
}

#: titoli che non dicono niente: se dopo le parole vuote resta solo roba di
#: questo elenco, il titolo è un segnaposto, non un titolo
TITOLI_GENERICI = {
    "introduzione", "introduction", "intro", "premessa", "prefazione", "preface",
    "conclusione", "conclusioni", "conclusion", "epilogo", "epilogue",
    "panoramica", "overview", "basi", "basics", "fondamenti", "fundamentals",
    "metodo", "method", "approccio", "approach", "concetti", "concepts",
    "capitolo", "chapter", "parte", "part", "sezione", "section",
    "riepilogo", "summary", "generale", "general", "primi", "passi", "started",
    "getting", "understanding", "capire", "comprendere", "considerazioni",
    "finali", "final", "note", "appunti", "varie",
}

#: promesse di risultato: in un libro KDP di questa materia sono un rischio di
#: conformità, non una questione di gusto
PROMESSE = (
    "cure", "cured", "cures", "heal", "heals", "healed", "healing",
    "guarantee", "guaranteed", "guarantees", "miracle", "miraculous",
    "life-changing", "transform your life", "change your life", "risultati garantiti",
    "guarigione", "guarire", "guarisce", "garantito", "garantisce", "miracolo",
    "cura definitiva",
)

#: linguaggio da prova: ammesso solo se negato nella stessa frase
PROVE = (
    "proof", "proves", "proven", "confirms", "confirmed", "verified",
    "demonstrates", "establishes", "prova che", "dimostra", "conferma",
    "accertato", "verificato",
)

#: virgolette di ogni foggia: quello che sta dentro è **citato**, non detto
VIRGOLETTE = re.compile(r"[«\"“'‘]([^»\"”'’]{1,200})[»\"”'’]")

NEGAZIONI = (
    "not", "no", "never", "without", "won't", "wont", "cannot", "can't", "cant",
    "isn't", "isnt", "refuse", "refuses", "refused", "declin", "stop", "against",
    "instead", "rather", "non", "mai", "nessun", "nessuna", "senza", "rifiut",
    "invece",
)

#: una data scritta per esteso: in questo mestiere va detta come parola di chi
#: parla, non come fatto
DATA = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\b")

#: quantità da verificare sul libro vero, in cifre o in lettere
NUMERI_IN_LETTERE = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "twenty": 20,
    "thirty": 30, "forty": 40, "fifty": 50, "hundred": 100,
    "due": 2, "tre": 3, "quattro": 4, "cinque": 5, "sei": 6, "sette": 7,
    "otto": 8, "nove": 9, "dieci": 10, "dodici": 12, "venti": 20, "trenta": 30,
}

#: marcatori di capitolo pratico: servono a misurare la progressione
MARCATORI_PRATICI = (
    "how to choose", "what to bring", "questions to ask", "your first session",
    "before booking", "practitioner from", "prepare for", "preparing for",
    "come scegliere", "che cosa portare", "domande da fare", "prima seduta",
)


# --------------------------------------------------------------------------
# Attrezzi
# --------------------------------------------------------------------------
def _piatto(testo: str) -> str:
    """Minuscolo, senza accenti: due titoli che differiscono per un accento
    sono lo stesso titolo."""
    scomposto = unicodedata.normalize("NFKD", testo.lower())
    return "".join(c for c in scomposto if not unicodedata.combining(c))


def _parole(testo: str) -> set[str]:
    """Le parole che portano significato: niente parole grammaticali, niente
    parole corte."""
    grezze = re.findall(r"[a-z0-9']+", _piatto(testo))
    return {p for p in grezze if len(p) > 3 and p not in PAROLE_VUOTE}


def _testo(capitolo) -> str:
    return f"{capitolo.title} {capitolo.summary} {' '.join(capitolo.beats)}"


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _senza_citazioni(testo: str) -> str:
    """Toglie quello che sta fra virgolette.

    È la distinzione fra usare una parola e nominarla. «Le sei parole che mi
    rifiuto di usare: "provato", "confermato"» non è una rivendicazione: è
    l'elenco delle rivendicazioni da evitare. E in un libro di testimonianze
    quello che sta fra virgolette è per definizione quello che una persona ha
    detto — cioè esattamente ciò che la linea editoriale ammette.
    """
    return VIRGOLETTE.sub(" ", testo)


def _negato(testo: str, parola: str) -> bool:
    """C'è una negazione entro dieci parole dalla parola vietata?

    «Why I Still Won't Call It Proof» e «what I am not claiming: cure» sono
    frasi che rispettano la linea editoriale, non che la violano. Senza questo
    controllo il revisore bloccherebbe proprio i capitoli scritti bene.
    """
    parole = _piatto(testo).replace("-", " ").split()
    bersaglio = _piatto(parola).split()[0]
    for indice, corrente in enumerate(parole):
        if not corrente.strip(".,;:!?").startswith(bersaglio):
            continue
        intorno = parole[max(0, indice - FINESTRA_NEGAZIONE): indice + FINESTRA_NEGAZIONE]
        if any(any(n in p for n in NEGAZIONI) for p in intorno):
            return True
    return False


def _segnala(severita: str, categoria: str, problema: str, **extra) -> AgentFinding:
    return AgentFinding(
        agent=NOME, severity=severita, category=categoria, issue=problema, **extra
    )


# --------------------------------------------------------------------------
# I controlli, uno per regola
# --------------------------------------------------------------------------
def _controlla_conteggio(outline: Outline, attesi: int) -> list[AgentFinding]:
    if not attesi:
        return []
    contenuto = [c for c in outline.chapters if c.role == "chapter"]
    if len(contenuto) == attesi:
        return []
    return [
        _segnala(
            "bloccante",
            "conteggio",
            f"La scaletta ha {len(contenuto)} capitoli di contenuto, ne erano chiesti {attesi}: "
            "il conteggio pagine e il prezzo sono calcolati su quel numero.",
            suggestion=(
                f"Aggiungi {attesi - len(contenuto)} capitoli."
                if len(contenuto) < attesi
                else f"Unisci o togli {len(contenuto) - attesi} capitoli."
            ),
        )
    ]


def _controlla_titoli(outline: Outline) -> list[AgentFinding]:
    rilievi: list[AgentFinding] = []
    visti: dict[str, int] = {}
    for capitolo in outline.chapters:
        chiave = " ".join(_piatto(capitolo.title).split())
        if chiave in visti:
            rilievi.append(
                _segnala(
                    "bloccante",
                    "titolo doppio",
                    f"I capitoli {visti[chiave]} e {capitolo.number} hanno lo stesso titolo.",
                    chapter=capitolo.number,
                    quote=capitolo.title,
                    suggestion="Un indice con due righe uguali dice al cliente che il libro si ripete.",
                )
            )
        else:
            visti[chiave] = capitolo.number

        if capitolo.role != "chapter":
            continue
        significative = _parole(capitolo.title)
        if not significative or significative <= TITOLI_GENERICI:
            rilievi.append(
                _segnala(
                    "importante",
                    "titolo generico",
                    f"«{capitolo.title}» è un segnaposto: non dice al cliente che cosa trova dentro.",
                    chapter=capitolo.number,
                    quote=capitolo.title,
                    suggestion=(
                        "L'indice è la pagina che si legge nell'anteprima prima di comprare: "
                        "ogni riga deve promettere qualcosa di preciso."
                    ),
                )
            )
    return rilievi


def _controlla_sovrapposizioni(outline: Outline) -> list[AgentFinding]:
    """Due capitoli che si assomigliano troppo faranno lo stesso capitolo."""
    capitoli = [c for c in outline.chapters if c.role == "chapter"]
    insiemi = {c.number: _parole(_testo(c)) for c in capitoli}
    coppie = []
    for primo in range(len(capitoli)):
        for secondo in range(primo + 1, len(capitoli)):
            a, b = capitoli[primo], capitoli[secondo]
            punteggio = _jaccard(insiemi[a.number], insiemi[b.number])
            if punteggio >= SOGLIA_VICINI:
                coppie.append((punteggio, a, b))
    coppie.sort(key=lambda riga: -riga[0])

    rilievi = []
    for punteggio, a, b in coppie[:6]:
        gemelli = punteggio >= SOGLIA_GEMELLI
        comuni = sorted(insiemi[a.number] & insiemi[b.number])[:8]
        rilievi.append(
            _segnala(
                "bloccante" if gemelli else "importante",
                "sovrapposizione",
                f"I capitoli {a.number} e {b.number} condividono il {punteggio * 100:.0f}% "
                f"delle parole che portano significato: "
                + ("fanno lo stesso capitolo." if gemelli else "rischiano di ripetersi."),
                chapter=b.number,
                quote=f"{a.title} / {b.title}",
                suggestion=(
                    "Dai ai due capitoli beats diversi, oppure uniscili e usa il posto "
                    f"liberato per un argomento scoperto. In comune: {', '.join(comuni)}."
                ),
            )
        )
    return rilievi


def _controlla_programma(outline: Outline) -> list[AgentFinding]:
    """Un capitolo senza riassunto e senza punti non chiude quello che apre:
    chi lo scrive non sa dove finisce."""
    rilievi = []
    for capitolo in outline.chapters:
        if capitolo.role != "chapter":
            continue
        if len(capitolo.summary.split()) < MINIMO_PAROLE_RIASSUNTO:
            rilievi.append(
                _segnala(
                    "importante",
                    "capitolo senza programma",
                    f"Il capitolo {capitolo.number} non ha un riassunto che dica che cosa fa "
                    "e perché sta lì.",
                    chapter=capitolo.number,
                    quote=capitolo.title,
                    suggestion="Due frasi: che cosa spiega e perché sta in questo punto del libro.",
                )
            )
        if len(capitolo.beats) < MINIMO_BEATS:
            rilievi.append(
                _segnala(
                    "importante",
                    "capitolo senza punti",
                    f"Il capitolo {capitolo.number} ha {len(capitolo.beats)} punti da coprire: "
                    "chi lo scrive non sa dove deve arrivare.",
                    chapter=capitolo.number,
                    quote=capitolo.title,
                    suggestion=f"Almeno {MINIMO_BEATS} beats, meglio quattro.",
                )
            )
    return rilievi


def argomenti_del_brief(brief: str) -> list[str]:
    """Gli argomenti che l'autore ha chiesto, presi da `brief.md`.

    Sono i punti elenco del modulo: ognuno può continuare su più righe
    rientrate. Le sezioni di divieto (`must NOT`, `non deve`) restano fuori,
    perché sono vincoli, non capitoli da scrivere.
    """
    argomenti: list[str] = []
    corrente: list[str] = []
    saltare = False
    for riga in brief.splitlines():
        spoglia = riga.strip()
        if spoglia.startswith("#"):
            titolo = _piatto(spoglia)
            saltare = any(
                spia in titolo
                for spia in ("must not", "non deve", "da evitare", "what must", "tono", "tone")
            )
            if corrente:
                argomenti.append(" ".join(corrente))
                corrente = []
            continue
        if saltare:
            continue
        if spoglia.startswith(("- ", "* ", "• ")):
            if corrente:
                argomenti.append(" ".join(corrente))
            corrente = [spoglia[2:].strip()]
        elif corrente and spoglia:
            corrente.append(spoglia)
        elif corrente:
            argomenti.append(" ".join(corrente))
            corrente = []
    if corrente:
        argomenti.append(" ".join(corrente))
    return [a for a in argomenti if len(_parole(a)) >= COPERTURA_PAROLE]


def _controlla_copertura(outline: Outline, brief: str) -> list[AgentFinding]:
    """Ogni argomento chiesto dall'autore deve avere un capitolo che lo prende.

    È il controllo che vale di più: un argomento dimenticato qui non comparirà
    nel libro, e nessuno se ne accorgerà finché il libro non è stampato.
    """
    argomenti = argomenti_del_brief(brief)
    if not argomenti:
        return []
    capitoli = [c for c in outline.chapters if c.role == "chapter"]
    insiemi = {c.number: _parole(_testo(c)) for c in capitoli}

    rilievi = []
    for argomento in argomenti:
        chieste = _parole(argomento)
        richiesta = max(COPERTURA_PAROLE, math.ceil(len(chieste) * COPERTURA_QUOTA))
        migliore, quante = 0, 0
        for capitolo in capitoli:
            comuni = len(chieste & insiemi[capitolo.number])
            if comuni > quante:
                migliore, quante = capitolo.number, comuni
        if quante >= richiesta:
            continue
        vicino = (
            f" Il capitolo più vicino è il {migliore}, con {quante} parole in comune su "
            f"{richiesta} richieste."
            if migliore
            else ""
        )
        rilievi.append(
            _segnala(
                "bloccante",
                "argomento scoperto",
                "Un argomento chiesto in brief.md non ha un capitolo che lo copra: "
                f"«{argomento[:120]}».{vicino}",
                suggestion=(
                    "Aggiungi un capitolo, oppure porta l'argomento nei beats di uno esistente: "
                    "quello che non sta nella scaletta non finisce nel libro."
                ),
            )
        )
    return rilievi


def _controlla_divieti(outline: Outline) -> list[AgentFinding]:
    """Promesse di risultato e linguaggio da prova, negazioni escluse."""
    pezzi: list[tuple[int | None, str, str]] = [
        (None, "quarta di copertina", outline.back_cover),
        (None, "tesi", outline.thesis),
    ]
    pezzi += [(c.number, f"capitolo {c.number}", _testo(c)) for c in outline.chapters]

    rilievi = []
    for numero, dove, grezzo in pezzi:
        if not grezzo:
            continue
        testo = _senza_citazioni(grezzo)
        piatto = _piatto(testo)
        for parola in PROMESSE:
            if parola in piatto and not _negato(testo, parola):
                rilievi.append(
                    _segnala(
                        "bloccante",
                        "promessa di risultato",
                        f"In {dove} compare «{parola}»: il libro dice che cosa il lettore può "
                        "vivere, non che cosa otterrà.",
                        chapter=numero,
                        quote=testo[:160],
                        suggestion="Riscrivi come esperienza riportata da chi l'ha vissuta.",
                    )
                )
                break
        for parola in PROVE:
            if parola in piatto and not _negato(testo, parola):
                rilievi.append(
                    _segnala(
                        "importante",
                        "linguaggio da prova",
                        f"In {dove} compare «{parola}» senza negazione vicina: una seduta "
                        "produce una testimonianza, non una conferma.",
                        chapter=numero,
                        quote=testo[:160],
                        suggestion="Dillo come quello che la persona ha detto, o nega esplicitamente.",
                    )
                )
                break
    return rilievi


def _controlla_date(outline: Outline) -> list[AgentFinding]:
    rilievi = []
    for capitolo in outline.chapters:
        date = DATA.findall(_testo(capitolo))
        if not date:
            continue
        rilievi.append(
            _segnala(
                "importante",
                "data in scaletta",
                f"Il capitolo {capitolo.number} porta una data ({', '.join(sorted(set(date)))}): "
                "in questo libro una data si racconta come quello che una persona ha detto, "
                "mai come fatto accertato.",
                chapter=capitolo.number,
                quote=capitolo.title,
                suggestion="Togli la data dalla scaletta o scrivila già come parola di chi parla.",
            )
        )
    return rilievi


def quantita_dichiarate(outline: Outline) -> list[tuple[str, str]]:
    """Le cifre stampate in copertina, in quarta e nell'indice.

    Nessuna di queste si può dichiarare: si contano sul libro. L'agente non
    sa contarle al posto dell'autore, ma sa dire quali sono.
    """
    fonti = [("titolo", outline.title), ("sottotitolo", outline.subtitle),
             ("quarta", outline.back_cover)]
    fonti += [(f"capitolo {c.number}", c.title) for c in outline.chapters]
    trovate = []
    for dove, testo in fonti:
        if not testo:
            continue
        for numero in re.findall(r"\b\d+\b", testo):
            trovate.append((dove, numero))
        for parola in re.findall(r"[a-z]+", _piatto(testo)):
            if parola in NUMERI_IN_LETTERE:
                trovate.append((dove, f"{parola} ({NUMERI_IN_LETTERE[parola]})"))
    return trovate


def _controlla_quantita(outline: Outline) -> list[AgentFinding]:
    quantita = quantita_dichiarate(outline)
    if not quantita:
        return []
    elenco = "; ".join(f"{dove}: {numero}" for dove, numero in quantita[:12])
    return [
        _segnala(
            "minore",
            "cifre da contare",
            f"Quantità dichiarate nell'indice e in quarta ({len(quantita)}): {elenco}.",
            suggestion=(
                "Ogni cifra stampata dev'essere un numero contato sul libro finito. "
                "Verificale una per una prima della stampa."
            ),
        )
    ]


def _controlla_quarta(outline: Outline) -> list[AgentFinding]:
    testo = (outline.back_cover or "").strip()
    if not testo:
        return [
            _segnala(
                "importante",
                "quarta mancante",
                "La scaletta non porta il testo di quarta: è quello che legge chi ha già "
                "preso il libro in mano.",
                suggestion="Una frase-gancio, poi due paragrafi brevi.",
            )
        ]
    blocchi = [b for b in re.split(r"\n\s*\n", testo) if b.strip()]
    rilievi = []
    if len(blocchi) < QUARTA_BLOCCHI:
        rilievi.append(
            _segnala(
                "minore",
                "quarta senza gancio",
                f"La quarta ha {len(blocchi)} blocchi invece di {QUARTA_BLOCCHI} "
                "(gancio più due paragrafi).",
                quote=testo[:120],
                suggestion="Separa la frase-gancio dai paragrafi con una riga vuota.",
            )
        )
    if not QUARTA_MINIMO <= len(testo) <= QUARTA_MASSIMO:
        rilievi.append(
            _segnala(
                "minore",
                "quarta fuori misura",
                f"La quarta è di {len(testo)} caratteri: la misura che entra sul retro di un "
                f"libro sta fra {QUARTA_MINIMO} e {QUARTA_MASSIMO}.",
                suggestion="Accorcia, o allunga: quello che avanza finisce nella descrizione KDP.",
            )
        )
    return rilievi


def _controlla_lingua(outline: Outline, spec: BookSpec) -> list[AgentFinding]:
    """La scaletta deve essere nella lingua del libro: i titoli che scrivi qui
    sono definitivi, e finiscono nell'indice stampato."""
    atteso = (spec.language or "it")[:2].lower()
    if atteso not in SPIE_LINGUA:
        return []
    testo = " ".join(_piatto(_testo(c)) for c in outline.chapters).split()
    if len(testo) < 50:
        return []
    conta = {
        lingua: sum(1 for p in testo if p.strip(".,;:!?") in spie)
        for lingua, spie in SPIE_LINGUA.items()
    }
    vincente = max(conta, key=lambda lingua: conta[lingua])
    if vincente == atteso or conta[vincente] == conta[atteso]:
        return []
    return [
        _segnala(
            "bloccante",
            "lingua sbagliata",
            f"Il libro è dichiarato in «{spec.language}» ma la scaletta è scritta in "
            f"«{vincente}» ({conta[vincente]} parole grammaticali contro {conta[atteso]}).",
            suggestion="I titoli della scaletta sono definitivi: riscrivili nella lingua del libro.",
        )
    ]


def _controlla_progressione(outline: Outline) -> list[AgentFinding]:
    """Prima il quadro, poi il metodo, in fondo l'applicazione.

    Si misura dove stanno i capitoli pratici: se la parte operativa è sparsa
    all'inizio, il lettore riceve le istruzioni prima di sapere a che cosa
    servono.
    """
    capitoli = [c for c in outline.chapters if c.role == "chapter"]
    if len(capitoli) < 6:
        return []
    pratici = [
        indice
        for indice, capitolo in enumerate(capitoli)
        if any(m in _piatto(_testo(capitolo)) for m in MARCATORI_PRATICI)
    ]
    if not pratici:
        return []
    media = sum(pratici) / len(pratici)
    if media >= len(capitoli) / 2:
        return []
    return [
        _segnala(
            "minore",
            "progressione",
            f"I {len(pratici)} capitoli operativi stanno in media al posto "
            f"{media + 1:.0f} su {len(capitoli)}: il lettore riceve le istruzioni prima "
            "di sapere a che cosa servono.",
            suggestion="Sposta la parte applicativa nell'ultimo terzo del libro.",
        )
    ]


def _controlla_titolo(outline: Outline, spec: BookSpec) -> list[AgentFinding]:
    """Il titolo della scaletta è quello che finirà in copertina."""
    rilievi = [
        _segnala(
            "importante",
            "titolo in copertina",
            problema,
            quote=outline.title,
            suggestion="Un titolo che non si legge in miniatura non si clicca.",
        )
        for problema in coverdesign.title_problems(outline.title, trim=spec.trim)
    ]
    insieme = len(outline.title) + len(outline.subtitle)
    if insieme > kdpspecs.TITLE_AND_SUBTITLE_MAX_CHARS:
        rilievi.append(
            _segnala(
                "importante",
                "titolo troppo lungo",
                f"Titolo e sottotitolo fanno {insieme} caratteri: Amazon ne mostra "
                f"{kdpspecs.TITLE_AND_SUBTITLE_MAX_CHARS} nei risultati di ricerca.",
                quote=f"{outline.title}: {outline.subtitle}",
                suggestion="Accorcia il sottotitolo: quello che si taglia non vende.",
            )
        )
    return rilievi


# --------------------------------------------------------------------------
# L'esame
# --------------------------------------------------------------------------
def esamina(
    outline: Outline,
    spec: BookSpec,
    *,
    brief: str = "",
    capitoli_attesi: int = 0,
) -> list[AgentFinding]:
    """Tutti i controlli, in ordine di quanto costa il difetto se passa."""
    rilievi: list[AgentFinding] = []
    rilievi += _controlla_conteggio(outline, capitoli_attesi)
    rilievi += _controlla_lingua(outline, spec)
    rilievi += _controlla_copertura(outline, brief or spec.brief or "")
    rilievi += _controlla_divieti(outline)
    rilievi += _controlla_sovrapposizioni(outline)
    rilievi += _controlla_titoli(outline)
    rilievi += _controlla_programma(outline)
    rilievi += _controlla_date(outline)
    rilievi += _controlla_titolo(outline, spec)
    rilievi += _controlla_quarta(outline)
    rilievi += _controlla_progressione(outline)
    rilievi += _controlla_quantita(outline)
    return sorted(rilievi, key=lambda r: r.sort_key)


@register
class RevisoreScaletta(Agent):
    name = NOME
    title = "Revisore di scaletta"
    description = (
        "Esamina la scaletta prima che diventi un libro: argomenti del brief rimasti "
        "scoperti, capitoli che si sovrappongono, titoli generici, promesse di risultato, "
        "date dichiarate come fatti, quantità da contare. Non usa il modello: conta."
    )
    stage = "controllo"
    comando = "python3 -m kdpfactory manuale <slug> scaletta --esamina"
    istruzioni = """Questo agente non usa il modello: misura la scaletta.

```bash
cd kdp-book-factory
python3 -m kdpfactory manuale <slug> scaletta --esamina
```

Le segnalazioni **bloccanti** fermano l'importazione della scaletta: vanno
risolte riscrivendo `books/<slug>/manuale/scaletta.json`, non aggirate. Le
`importanti` si valutano una per una. Le `minori` — in particolare l'elenco
delle cifre dichiarate — sono una lista di verifica da fare sul libro finito.

Se ti viene chiesto di esaminare una scaletta a mano, applica le stesse
regole: ogni argomento di `brief.md` deve avere un capitolo, nessun capitolo
deve ripetere un altro, nessun titolo deve essere un segnaposto, nessuna
promessa di risultato, nessuna data presentata come fatto accertato, e ogni
cifra dichiarata dev'essere contata sul libro."""

    def system(self, ctx: AgentContext) -> list[str]:  # pragma: no cover - non usato
        return []

    def user(self, ctx: AgentContext) -> str:  # pragma: no cover - non usato
        return ""

    def run(self, ctx: AgentContext, client=None) -> AgentResult:
        if ctx.outline is None:
            mancante = _segnala(
                "bloccante", "scaletta mancante", "Non c'è nessuna scaletta da esaminare."
            )
            return AgentResult(agent=self.name, findings=[mancante], notes="Nessuna scaletta.")
        rilievi = esamina(
            ctx.outline,
            ctx.spec,
            brief=ctx.text,
            capitoli_attesi=int(ctx.metadata.get("capitoli_attesi", 0) or 0),
        )
        bloccanti = [r for r in rilievi if r.severity == "bloccante"]
        notes = (
            "Scaletta solida: nessun rilievo."
            if not rilievi
            else f"{len(rilievi)} rilievi sulla scaletta, di cui {len(bloccanti)} bloccanti."
        )
        return AgentResult(agent=self.name, findings=rilievi, notes=notes)

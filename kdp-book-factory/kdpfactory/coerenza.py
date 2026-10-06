"""Indice e capitoli: che si corrispondano nei due sensi.

Un editore controlla l'indice due volte. La prima, dall'indice al libro: ogni
voce porta al capitolo giusto, con il titolo e il numero di pagina che il
lettore troverà aprendo lì. La seconda, dal libro all'indice: ogni capitolo si
trova dall'indice, cioè il suo titolo dice di che cosa parla. Qui si misura,
senza modello, quello che si può misurare:

1. il titolo deciso — scaletta e `manuale/indice.json`, il lavoro dell'agente
   `indice` — è quello stampato in testa al capitolo;
2. nell'indice stampato ogni voce porta alla pagina dove il capitolo si apre, e
   ogni capitolo ha la sua voce, nello stesso ordine del libro;
3. dal titolo al testo: le parole portanti del titolo ricorrono nel capitolo;
4. dal testo al titolo: le parole che distinguono il capitolo dagli altri
   compaiono nel suo titolo;
5. i rimandi interni: un capitolo che ne cita un altro per nome usa il titolo
   che l'indice stampa.

I primi due sono errori: un indice che manda alla pagina sbagliata è un difetto
di stampa. Gli altri sono avvisi con le parole trovate: se il libro
mantiene le promesse dell'indice lo giudica il `lettore-cieco`, leggendo, e i
titoli li corregge l'agente `indice`. Qui ci sono i numeri che fanno da guida a
tutti e due.
"""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from . import mdlite

#: Parole che non portano argomento: in un titolo non promettono niente, e nel
#: testo ci sono ovunque.
VUOTE: dict[str, set[str]] = {
    "en": set(
        """a about after again all also an and any are as at be because been before
        being between both but by can could did do does doing done don't each even
        every few for from get gets getting had has have having her here hers him
        his how into its it's itself just keep keeps kind kinds know let like made
        make makes many may might more most much must need needs never next nobody
        none not now off once one only onto other others our out over own part
        people put rather really said same says see she should since some something
        still such sure take tell than that that's the their them then there these
        they thing things this those though through time times too under until upon
        very want wants was way ways well were what what's when where whether which
        while who whom whose why will with without won't would year years yet you
        your yours you're you'll you've don't doesn't isn't can't""".split()
    ),
    "it": set(
        """alla alle allo anche ancora avere come con cosa cose dalla dalle dallo
        degli della delle dello dentro dopo dove essere fare fino loro molto nella
        nelle nello niente nulla ogni oppure perché però poco prima quale quali
        quando quanto quella quelle quello questa queste questo senza sempre sono
        sotto stato sulla sulle sullo tanto tutti tutto una uno verso volta""".split()
    ),
}

#: Le parole più distintive di un capitolo che si guardano nel titolo.
DISTINTIVE = 5
#: Sotto queste occorrenze una parola non distingue un capitolo: è un incontro.
MIN_OCCORRENZE = 4


@dataclass
class Voce:
    """Una riga dell'indice stampato: il testo e il numero di pagina che porta."""

    testo: str
    folio: int


@dataclass
class Esito:
    errori: list[str] = field(default_factory=list)
    avvisi: list[str] = field(default_factory=list)
    #: per ogni capitolo, le parole che lo distinguono: la guida dell'agente `indice`
    distintive: dict[int, list[str]] = field(default_factory=dict)


# --------------------------------------------------------------------------
# Le parole
# --------------------------------------------------------------------------
def _piana(testo: str) -> str:
    testo = unicodedata.normalize("NFKD", testo)
    return "".join(c for c in testo if not unicodedata.combining(c)).lower()


def radice(parola: str, lingua: str) -> str:
    """Una radice rozza ma stabile: «Paydays», «payday» e «paydays'» si incontrano.

    Non serve un vero stemmer: serve che lo stesso argomento, al singolare o al
    plurale, nel titolo o nel testo, dia la stessa chiave. Le collisioni
    («statement» e «state» no, ma «credit» e «credits» sì) fanno al più sparire
    un avviso, mai comparirne uno falso.
    """
    p = _piana(parola).strip("'’")
    p = re.sub(r"['’]s$", "", p)
    if lingua == "it":
        if len(p) >= 5 and p[-1] in "aeio":
            p = p[:-1]
        return p[:6]
    for suffisso in ("ings", "ing", "ies", "es", "ed", "ly", "s"):
        if p.endswith(suffisso) and len(p) - len(suffisso) >= 4:
            p = p[: -len(suffisso)]
            break
    return p[:6]


def parole(testo: str, lingua: str) -> list[tuple[str, str]]:
    """Le parole portanti del testo: (radice, forma come scritta)."""
    vuote = VUOTE.get(lingua, set())
    trovate = []
    for forma in re.findall(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'’-]*", testo):
        pulita = forma.strip("'’-")
        if len(pulita) < 4 or _piana(pulita) in vuote:
            continue
        trovate.append((radice(pulita, lingua), pulita.lower()))
    return trovate


# --------------------------------------------------------------------------
# I titoli: deciso e stampato
# --------------------------------------------------------------------------
def _uguali(a: str, b: str) -> bool:
    return " ".join(_piana(a).split()) == " ".join(_piana(b).split())


def titoli_decisi(
    outline_titoli: dict[int, str],
    indice_titoli: list[str],
    stampati: dict[int, str],
    numerati: list[int],
) -> list[str]:
    """I titoli che non coincidono fra scaletta, indice deciso e manoscritto.

    La scaletta numera tutti i capitoli, introduzione compresa, e si confronta
    numero per numero. `manuale/indice.json` numera solo i capitoli veri, quelli
    che portano «Chapter N» (`numerati`, in ordine): si confronta per elenco,
    perché un capitolo aggiunto dopo l'indice sposta tutti i numeri successivi e
    darebbe venti differenze dove ce n'è una.
    """
    errori = []
    for numero, stampato in stampati.items():
        deciso = outline_titoli.get(numero)
        if deciso and not _uguali(deciso, stampato):
            errori.append(
                f"Capitolo {numero}: il libro stampa «{stampato}», la scaletta dice «{deciso}»."
            )
    if indice_titoli:
        veri = [stampati[n] for n in numerati if n in stampati]
        decisi = {_piana(" ".join(x.split())) for x in indice_titoli}
        stampa = {_piana(" ".join(x.split())) for x in veri}
        mai_decisi = [x for x in veri if _piana(" ".join(x.split())) not in decisi]
        non_stampati = [x for x in indice_titoli if _piana(" ".join(x.split())) not in stampa]
        if mai_decisi:
            errori.append(
                "Titoli stampati che l'agente `indice` non ha mai deciso (manuale/indice.json): "
                + ", ".join(f"«{x}»" for x in mai_decisi)
                + ". Di solito è un capitolo aggiunto o rinominato dopo l'indice."
            )
        if non_stampati:
            errori.append(
                "Titoli decisi in manuale/indice.json che il libro non stampa: "
                + ", ".join(f"«{x}»" for x in non_stampati)
                + "."
            )
    return errori


# --------------------------------------------------------------------------
# L'indice stampato, letto dal PDF
# --------------------------------------------------------------------------
_PUNTINI = re.compile(r"^[.·…\s]+$")


def leggi_indice(pdf: Path, pagine_indice: range, titolo_indice: str = "") -> list[Voce]:
    """Le voci dell'indice come le vede il lettore: righe con i puntini e un numero.

    Una voce lunga va a capo: la riga senza numero si unisce alla successiva. Il
    titolo della pagina («Contents») non è una voce.
    """
    import pymupdf

    voci: list[Voce] = []
    documento = pymupdf.open(pdf)
    try:
        sospesa = ""
        for indice_pagina in pagine_indice:
            if not 0 <= indice_pagina < documento.page_count:
                continue
            righe: dict[int, list[tuple[float, str]]] = {}
            for x0, y0, _x1, y1, parola, *_ in documento[indice_pagina].get_text("words"):
                righe.setdefault(round((y0 + y1) / 2 / 3), []).append((x0, parola))
            for chiave in sorted(righe):
                pezzi = [p for _, p in sorted(righe[chiave]) if not _PUNTINI.match(p)]
                if not pezzi or (titolo_indice and _uguali(" ".join(pezzi), titolo_indice)):
                    continue
                if pezzi[-1].isdigit():
                    testo = " ".join([sospesa, *pezzi[:-1]]).strip()
                    if testo:
                        voci.append(Voce(testo=testo, folio=int(pezzi[-1])))
                    sospesa = ""
                else:
                    sospesa = " ".join([sospesa, *pezzi]).strip()
    finally:
        documento.close()
    return voci


def pagine_indice(pdf: Path, titolo_indice: str, cerca_fino: int = 20) -> range | None:
    """Le pagine dell'indice: quella che si apre col suo titolo e le seguenti coi puntini.

    Il colophon ha righe che finiscono con un numero («First edition – 2026»):
    leggere tutte le pagine preliminari darebbe voci che non esistono.
    """
    import pymupdf

    documento = pymupdf.open(pdf)
    try:
        inizio = None
        for i in range(min(cerca_fino, documento.page_count)):
            righe = [r.strip() for r in documento[i].get_text().splitlines() if r.strip()]
            if righe and _uguali(righe[0], titolo_indice):
                inizio = i
                break
        if inizio is None:
            return None
        fine = inizio + 1
        while fine < documento.page_count and ". . ." in documento[fine].get_text().replace("  ", " "):
            fine += 1
        return range(inizio, fine)
    finally:
        documento.close()


def _senza_numero(testo: str) -> str:
    """«3 Tracking Down…» → «Tracking Down…»: il numero del capitolo nell'indice."""
    return re.sub(r"^\d+\s+", "", testo)


def verifica_indice_stampato(
    pdf: Path,
    voci: list[Voce],
    stampati: list[tuple[int, str]],
    folio_offset: int,
) -> list[str]:
    """Ogni voce porta all'apertura giusta, e ogni capitolo ha la sua voce."""
    import pymupdf

    errori: list[str] = []
    titoli_voci = [_senza_numero(v.testo) for v in voci]
    documento = pymupdf.open(pdf)
    try:
        for voce, titolo in zip(voci, titoli_voci, strict=True):
            fisica = voce.folio + folio_offset
            if not 1 <= fisica <= documento.page_count:
                errori.append(f"«{titolo}» porta a pagina {voce.folio}, che il libro non ha.")
                continue
            pagina = " ".join(documento[fisica - 1].get_text().split())
            # La voce di una parte è «Part I — Titolo»: in pagina c'è il titolo.
            cercato = titolo.split(" — ", 1)[-1]
            if _piana(cercato) not in _piana(pagina):
                errori.append(
                    f"«{titolo}» nell'indice porta a pagina {voce.folio}, ma lì il capitolo "
                    "non si apre."
                )
    finally:
        documento.close()

    nell_indice = [_piana(t) for t in titoli_voci]
    ordine = []
    for numero, titolo in stampati:
        chiave = _piana(" ".join(titolo.split()))
        if chiave not in nell_indice:
            errori.append(f"Il capitolo {numero}, «{titolo}», non ha la sua voce nell'indice.")
        else:
            ordine.append(nell_indice.index(chiave))
    if ordine != sorted(ordine):
        errori.append("Le voci dell'indice non sono nell'ordine dei capitoli del libro.")
    return errori


# --------------------------------------------------------------------------
# Dal titolo al testo, e dal testo al titolo
# --------------------------------------------------------------------------
#: Una parola del titolo «ancora» il capitolo quando lì è almeno tanto più
#: frequente che nel resto del libro: il titolo dice di che cosa parla *questo*
#: capitolo, non di che cosa parla il libro.
ANCORA_MIN = 1.5
#: Una parola scritta con la maiuscola quasi sempre è un nome: Hank e Martha
#: distinguono un capitolo, ma nessuno li cerca nell'indice.
QUOTA_NOME = 0.9


def corrispondenze(
    capitoli: list[tuple[int, str, str]], lingua: str, generici: set[int] | None = None
) -> tuple[list[str], dict[int, list[str]]]:
    """Gli avvisi nei due sensi, e le parole distintive di ogni capitolo.

    `generici` sono i capitoli col titolo di servizio — introduzione, conclusione
    — che non promettono un argomento e non si misurano.
    """
    generici = generici or set()
    conteggi: dict[int, Counter] = {}
    forme: dict[str, Counter] = {}
    maiuscole: Counter = Counter()
    for numero, _titolo, markdown in capitoli:
        testo = mdlite.plain_text(markdown)
        trovate = parole(testo, lingua)
        conteggi[numero] = Counter(r for r, _ in trovate)
        for r, forma in trovate:
            forme.setdefault(r, Counter())[forma] += 1
        for parola in re.findall(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'’-]*", testo):
            if parola[0].isupper():
                maiuscole[radice(parola, lingua)] += 1

    def forma(r: str) -> str:
        return forme[r].most_common(1)[0][0] if r in forme else r

    libro = Counter()
    for c in conteggi.values():
        libro.update(c)
    totale_libro = sum(libro.values()) or 1
    nomi = {r for r, n in libro.items() if maiuscole[r] >= QUOTA_NOME * n}
    n_capitoli = len(capitoli)
    presenza = Counter(r for c in conteggi.values() for r in c)

    avvisi: list[str] = []
    distintive: dict[int, list[str]] = {}
    for numero, titolo, _markdown in capitoli:
        testo = conteggi[numero]
        totale = sum(testo.values()) or 1
        punteggi = {
            r: (n / totale) * math.log(n_capitoli / presenza[r])
            for r, n in testo.items()
            if n >= MIN_OCCORRENZE and presenza[r] < n_capitoli and r not in nomi
        }
        prime = sorted(punteggi, key=lambda r: -punteggi[r])[:DISTINTIVE]
        distintive[numero] = [forma(r) for r in prime]
        if numero in generici or n_capitoli < 3:
            continue
        nel_titolo = {r for r, _ in parole(titolo, lingua)} - nomi
        if not nel_titolo:
            continue

        # 3. dal titolo al testo: le parole del titolo ci sono?
        assenti = sorted(r for r in nel_titolo if testo[r] == 0)
        if len(assenti) * 2 > len(nel_titolo):
            avvisi.append(
                f"Capitolo {numero}, «{titolo}»: il testo non usa mai "
                + ", ".join(f"«{forma(r)}»" for r in assenti)
                + ". Il titolo promette un argomento di cui il capitolo non parla con "
                "quelle parole."
            )
            continue

        # 4. dal testo al titolo: il titolo dice che cosa ha di proprio questo capitolo?
        ancore = [(testo[r] / totale) / ((libro[r] / totale_libro) or 1) for r in nel_titolo]
        if max(ancore) < ANCORA_MIN:
            avvisi.append(
                f"Capitolo {numero}, «{titolo}»: nessuna parola del titolo è più frequente qui "
                "che nel resto del libro, quindi il titolo starebbe bene su un altro capitolo. "
                "Le parole che distinguono questo sono "
                + ", ".join(f"«{w}»" for w in distintive[numero])
                + "."
            )
    return avvisi, distintive


#: il corsivo come lo legge `mdlite`: *così* o _così_, mai il grassetto **così**
_CORSIVO = re.compile(
    r"(?<![\w*])\*(?!\s)([^*\n]+?)(?<!\s)\*(?![\w*])"
    r"|(?<![\w_])_(?!\s)([^_\n]+?)(?<!\s)_(?![\w_])"
)
#: Quanto devono somigliarsi un corsivo e un titolo perché il corsivo sia un rimando.
SOMIGLIANZA_RIMANDO = 0.5


def rimandi(capitoli: list[tuple[int, str, str]], altri_titoli: list[str], lingua: str) -> list[str]:
    """I rimandi interni a un titolo che non c'è più.

    Un libro cita i propri capitoli per nome, in corsivo: «…ending with *Catching
    Up When Several Bills Are Behind*». Se il capitolo cambia titolo, il rimando
    resta indietro e il lettore cerca nell'indice una voce che non esiste
    (rodaggio household-bills: introduzione e conclusione citavano il titolo
    vecchio). Un corsivo di almeno tre parole che somiglia a un titolo senza
    esserlo è un rimando da aggiornare.
    """
    titoli = [t for _, t, _ in capitoli] + list(altri_titoli)
    esatti = {_piana(" ".join(t.split())) for t in titoli}
    impronte = [(t, {r for r, _ in parole(t, lingua)}) for t in titoli]
    avvisi = []
    for numero, _titolo, markdown in capitoli:
        for trovato in _CORSIVO.finditer(markdown):
            corsivo = " ".join((trovato.group(1) or trovato.group(2)).split())
            if len(corsivo.split()) < 3 or _piana(corsivo) in esatti:
                continue
            sue = {r for r, _ in parole(corsivo, lingua)}
            if not sue:
                continue
            vicino, somiglianza = max(
                ((t, len(sue & imp) / len(sue | imp)) for t, imp in impronte if imp),
                key=lambda x: x[1],
                default=("", 0.0),
            )
            if somiglianza >= SOMIGLIANZA_RIMANDO:
                avvisi.append(
                    f"Capitolo {numero} rimanda a *{corsivo}*, ma nessun capitolo si chiama così: "
                    f"il titolo è «{vicino}»."
                )
    return avvisi


def controlla(
    capitoli: list[tuple[int, str, str]],
    lingua: str,
    *,
    outline_titoli: dict[int, str] | None = None,
    indice_titoli: list[str] | None = None,
    numerati: list[int] | None = None,
    generici: set[int] | None = None,
    titoli_parti: list[str] | None = None,
    pdf: Path | None = None,
    folio_offset: int = 0,
    titolo_indice: str = "",
) -> Esito:
    """Tutti e quattro i controlli. Senza PDF si fanno quelli sul testo."""
    esito = Esito()
    stampati = {numero: titolo for numero, titolo, _ in capitoli}
    esito.errori += titoli_decisi(
        outline_titoli or {}, indice_titoli or [], stampati,
        numerati if numerati is not None else list(stampati),
    )
    if pdf is not None and pdf.exists() and titolo_indice:
        try:
            pagine = pagine_indice(pdf, titolo_indice)
            voci = leggi_indice(pdf, pagine, titolo_indice) if pagine else []
        except ImportError:
            voci = []
        if voci:
            esito.errori += verifica_indice_stampato(
                pdf, voci, [(n, t) for n, t, _ in capitoli], folio_offset
            )
    esito.avvisi, esito.distintive = corrispondenze(capitoli, lingua, generici)
    esito.avvisi += rimandi(capitoli, titoli_parti or [], lingua)
    return esito

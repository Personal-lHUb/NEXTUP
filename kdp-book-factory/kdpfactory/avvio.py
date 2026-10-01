"""Le domande d'avvio: quello che l'autore decide prima che parta un libro nuovo.

Ogni libro nuovo nasce contro un concorrente preciso, un libro che vende già
nella nicchia, e deve batterlo dove i suoi lettori restano scontenti. Prima
della fase 0 l'autore risponde sempre alle stesse sette domande; le risposte
stanno in `concorrente/avvio.json` e da lì lavorano da sole:

- il posizionamento le riceve come vincolo, insieme a `indicazione.md`;
- `concorrente build` ne prende lingua, categoria e pseudonimo;
- la richiesta a Cowork per la pagina del concorrente la scrive il sistema,
  uguale per ogni libro;
- se l'autore vuole una copertina più attraente di quella del concorrente, il
  brief di copertina riceve la descrizione di quella da cui distinguersi.

Una domanda senza risposta vale il suo default, ma resta segnata come non
fatta: il comando la ripropone finché l'autore non l'ha vista.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

from .models import BookProject

#: Mercati in cui la pipeline sa fare un libro: una lingua che i controlli
#: conoscono e costi di stampa verificati (`config/printing_costs.json`). Il
#: codice postale serve a Cowork per vedere i prezzi nella valuta del mercato
#: anche da un computer che sta altrove.
MERCATI = {
    "amazon.com": {"lingua": "en", "valuta": "USD", "paese": "degli Stati Uniti", "cap": "10001"},
    "amazon.co.uk": {"lingua": "en", "valuta": "GBP", "paese": "del Regno Unito", "cap": "SW1A 1AA"},
    "amazon.it": {"lingua": "it", "valuta": "EUR", "paese": "italiano", "cap": "00118"},
}

CATEGORIE = {
    "concorrente": "La stessa del libro di partenza: full-content se è un testo da leggere, "
    "medium-content se è un libro da compilare. Il posizionamento la propone, l'autore la "
    "conferma prima della scaletta.",
    "full": "Full-content obbligatorio: testo pieno da leggere, nessuna pagina da compilare.",
    "medium": "Medium-content obbligatorio: libro interattivo, ogni pagina con contenuti, "
    "layout o stimoli differenti.",
}

#: Dove il libro nuovo deve battere quello di partenza, dentro il libro.
VANTAGGI = {
    "lacune": "Le lacune delle recensioni: quello che chi ha già comprato l'altro libro dice "
    "di non aver trovato, soprattutto nelle recensioni da 2 e 3 stelle.",
    "pratico": "Più pratico: struttura chiara, esempi concreti, passi da seguire, un indice "
    "che si consulta.",
    "contenuto": "Contenuto migliore: più completo e più preciso, senza allungare e senza "
    "ripetere quello che l'altro libro fa già bene.",
    "lettore": "Un lettore più preciso: una situazione, un'età o un mestiere che l'altro "
    "libro serve male.",
}

#: Dove il libro nuovo deve batterlo in vetrina, prima che qualcuno lo apra.
VETRINE = {
    "copertina": "Una copertina più attraente: nei risultati di ricerca, accanto all'altra, "
    "si nota prima e il titolo si legge meglio.",
    "prezzo": "Un prezzo più conveniente: più pagine allo stesso prezzo, o lo stesso "
    "contenuto a meno, senza scendere sotto la soglia della royalty alta.",
    "entrambe": "",
    "nessuna": "",
}

PAGINE = {
    "cowork": "La pagina del concorrente la scarica Cowork: il sistema scrive la richiesta.",
    "incolla": "La pagina del concorrente la incolla l'autore in `concorrente/pagina.md`.",
}

#: Le risposte che valgono quando l'autore non ne dà una: sono quelle date per
#: il primo libro fatto con questo metodo, e il comando le propone come
#: raccomandate.
PREDEFINITE = {
    "mercato": "amazon.com",
    "categoria": "concorrente",
    "vantaggi": ["lacune", "pratico", "contenuto"],
    "vetrina": "copertina",
    "pseudonimo": "",
    "pagina": "cowork",
}

#: Gli ASIN sono dieci caratteri: B0 e otto lettere o cifre per i prodotti
#: Amazon, l'ISBN-10 (nove cifre e una cifra o X) per i libri stampati.
_ASIN = re.compile(r"(?:/dp/|/gp/product/|/product/|^|\s)(B0[A-Z0-9]{8}|\d{9}[\dX])(?=$|[/?\s#])", re.I)


@dataclass(frozen=True)
class Opzione:
    valore: str
    etichetta: str
    descrizione: str


@dataclass(frozen=True)
class Domanda:
    chiave: str
    intestazione: str  # al massimo 12 caratteri: è l'etichetta della domanda
    testo: str
    opzioni: tuple[Opzione, ...] = ()
    multipla: bool = False
    #: la risposta è un testo (un ASIN, un nome): si chiede nel messaggio,
    #: non con le opzioni, che l'autore sceglierebbe senza scrivere il dato
    libera: bool = False


def _opzioni(voci: dict[str, str], etichette: dict[str, str], raccomandata: str = "") -> tuple:
    return tuple(
        Opzione(v, etichette[v] + (" (Recommended)" if v == raccomandata else ""), voci[v] or etichette[v])
        for v in etichette
    )


DOMANDE: tuple[Domanda, ...] = (
    Domanda(
        "concorrente",
        "Concorrente",
        "Quale libro deve sfidare? Mandami l'ASIN o il link della pagina Amazon. Se non "
        "ce l'hai, dimmi la nicchia: il concorrente lo cerca Cowork fra i primi 20 della "
        "categoria.",
        libera=True,
    ),
    Domanda(
        "mercato",
        "Mercato",
        "Su quale mercato e in che lingua esce il libro?",
        _opzioni(
            {m: f"Lingua {d['lingua']}, prezzi in {d['valuta']}." for m, d in MERCATI.items()},
            {"amazon.com": "amazon.com, inglese", "amazon.co.uk": "amazon.co.uk, inglese",
             "amazon.it": "amazon.it, italiano"},
            PREDEFINITE["mercato"],
        ),
    ),
    Domanda(
        "categoria",
        "Categoria",
        "Che tipo di libro dev'essere?",
        _opzioni(
            CATEGORIE,
            {"concorrente": "Come il concorrente", "full": "Full-content", "medium": "Medium-content"},
            PREDEFINITE["categoria"],
        ),
    ),
    Domanda(
        "vantaggi",
        "Vantaggio",
        "Dentro il libro, su che cosa deve batterlo? Puoi sceglierne più di una.",
        _opzioni(
            VANTAGGI,
            {"lacune": "Lacune delle recensioni", "pratico": "Più pratico",
             "contenuto": "Contenuto migliore", "lettore": "Lettore più preciso"},
        ),
        multipla=True,
    ),
    Domanda(
        "vetrina",
        "Vetrina",
        "In vetrina, prima che qualcuno lo apra, dove deve batterlo?",
        _opzioni(
            {**VETRINE, "entrambe": "Copertina più attraente e prezzo più conveniente.",
             "nessuna": "Copertina e prezzo li decide il posizionamento, come per ogni libro."},
            {"copertina": "Copertina più attraente", "prezzo": "Prezzo più conveniente",
             "entrambe": "Tutte e due", "nessuna": "Nessuna delle due"},
            PREDEFINITE["vetrina"],
        ),
    ),
    Domanda(
        "pseudonimo",
        "Pseudonimo",
        "Con quale nome d'autore esce?",
        libera=True,
    ),
    Domanda(
        "pagina",
        "Pagina",
        "Chi porta la pagina Amazon del concorrente, recensioni comprese?",
        _opzioni(
            PAGINE,
            {"cowork": "La scarica Cowork", "incolla": "La incollo io"},
            PREDEFINITE["pagina"],
        ),
    ),
)

PER_CHIAVE = {d.chiave: d for d in DOMANDE}


@dataclass
class Avvio:
    """Le risposte dell'autore per un libro, con i default dove non ha risposto."""

    asin: str = ""
    #: la nicchia, quando il concorrente lo deve trovare Cowork
    nicchia: str = ""
    mercato: str = PREDEFINITE["mercato"]
    categoria: str = PREDEFINITE["categoria"]
    vantaggi: list[str] = field(default_factory=lambda: list(PREDEFINITE["vantaggi"]))
    vetrina: str = PREDEFINITE["vetrina"]
    #: vuoto: uno nuovo, adatto alla nicchia, proposto insieme al titolo
    pseudonimo: str = PREDEFINITE["pseudonimo"]
    pagina: str = PREDEFINITE["pagina"]
    #: le domande a cui l'autore ha risposto; le altre valgono il default
    risposte: list[str] = field(default_factory=list)
    data: str = ""

    @property
    def lingua(self) -> str:
        return MERCATI[self.mercato]["lingua"]

    @property
    def valuta(self) -> str:
        return MERCATI[self.mercato]["valuta"]

    @property
    def copertina(self) -> bool:
        return self.vetrina in {"copertina", "entrambe"}

    @property
    def prezzo(self) -> bool:
        return self.vetrina in {"prezzo", "entrambe"}

    def mancanti(self) -> list[Domanda]:
        """Le domande che l'autore non ha ancora visto, nell'ordine in cui si fanno."""
        return [d for d in DOMANDE if d.chiave not in self.risposte]

    def to_dict(self) -> dict:
        return asdict(self)


# --------------------------------------------------------------------------
# Percorsi
# --------------------------------------------------------------------------
def percorso(project: BookProject) -> Path:
    return project.root / "concorrente" / "avvio.json"


def copertina_path(project: BookProject) -> Path:
    return project.root / "concorrente" / "copertina.md"


def leggi(project: BookProject) -> Avvio | None:
    file = percorso(project)
    if not file.exists():
        return None
    dati = json.loads(file.read_text(encoding="utf-8"))
    noti = Avvio.__dataclass_fields__
    return Avvio(**{k: v for k, v in dati.items() if k in noti})


def salva(project: BookProject, avvio: Avvio) -> Path:
    file = percorso(project)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(avvio.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return file


# --------------------------------------------------------------------------
# Le risposte
# --------------------------------------------------------------------------
def estrai_asin(testo: str) -> str:
    """L'ASIN da un codice o da un link Amazon; vuoto se non c'è."""
    trovato = _ASIN.search(testo.strip())
    return trovato.group(1).upper() if trovato else ""


def registra(avvio: Avvio, **risposte) -> list[str]:
    """Scrive le risposte date; restituisce gli errori, senza applicare quelle sbagliate.

    `None` vuol dire «non chiesto in questo giro»: la risposta di prima resta.
    """
    errori: list[str] = []
    date_ora: list[str] = []

    concorrente = risposte.pop("concorrente", None)
    nicchia = risposte.pop("nicchia", None)
    if concorrente is not None:
        asin = estrai_asin(concorrente)
        if asin:
            avvio.asin = asin
            date_ora.append("concorrente")
        else:
            errori.append(f"«{concorrente}» non contiene un ASIN (dieci caratteri, B0… o un ISBN-10).")
    if nicchia is not None:
        if nicchia.strip():
            avvio.nicchia = nicchia.strip()
            date_ora.append("concorrente")
        else:
            errori.append("La nicchia è vuota.")

    ammessi = {
        "mercato": MERCATI,
        "categoria": CATEGORIE,
        "vetrina": VETRINE,
        "pagina": PAGINE,
    }
    for chiave, valore in risposte.items():
        if valore is None:
            continue
        if chiave == "vantaggi":
            scelti = [v.strip() for v in valore if v.strip()]
            fuori = [v for v in scelti if v not in VANTAGGI]
            if fuori or not scelti:
                errori.append(
                    f"Vantaggi non validi: {', '.join(fuori) or '(nessuno)'}. "
                    f"Ammessi: {', '.join(VANTAGGI)}."
                )
                continue
            avvio.vantaggi = scelti
        elif chiave == "pseudonimo":
            avvio.pseudonimo = valore.strip()
        elif chiave in ammessi:
            if valore not in ammessi[chiave]:
                errori.append(f"{chiave}: «{valore}» non è fra {', '.join(ammessi[chiave])}.")
                continue
            setattr(avvio, chiave, valore)
        else:
            errori.append(f"Domanda sconosciuta: {chiave}.")
            continue
        date_ora.append(chiave)

    for chiave in date_ora:
        if chiave not in avvio.risposte:
            avvio.risposte.append(chiave)
    avvio.risposte.sort(key=lambda c: [d.chiave for d in DOMANDE].index(c))
    if date_ora:
        avvio.data = date.today().isoformat()
    return errori


def pseudonimi(books: Path) -> list[str]:
    """I nomi d'autore già usati, dai libri veri (i banchi di prova non contano)."""
    nomi: list[str] = []
    for scheda in sorted(books.glob("*/book.json")):
        try:
            dati = json.loads(scheda.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        nome = str(dati.get("author") or "").strip()
        if dati.get("banco_di_prova") or not nome or nome == "Autore Anonimo" or nome in nomi:
            continue
        nomi.append(nome)
    return nomi


# --------------------------------------------------------------------------
# Le domande, per chi le fa
# --------------------------------------------------------------------------
def domande_pseudonimo(books: Path) -> Domanda:
    """La domanda sullo pseudonimo, con i nomi già in uso come opzioni."""
    base = PER_CHIAVE["pseudonimo"]
    nuovi = [Opzione("", "Uno nuovo (Recommended)",
                     "Adatto alla nicchia: lo propongo insieme al titolo e lo confermi tu.")]
    usati = [Opzione(n, n, "Già in uso su un altro libro: conviene se la nicchia è vicina.")
             for n in pseudonimi(books)[:3]]
    return Domanda(base.chiave, base.intestazione, base.testo, tuple(nuovi + usati))


def giri(avvio: Avvio, books: Path) -> dict:
    """Le domande ancora da fare, pronte per chi le pone all'autore.

    `testo` sono quelle che si chiedono nel messaggio, perché la risposta è un
    dato da scrivere; `giri` sono quelle a scelta, a gruppi di quattro.
    """
    mancanti = [domande_pseudonimo(books) if d.chiave == "pseudonimo" else d for d in avvio.mancanti()]
    # Una domanda a scelta vuole almeno due opzioni: lo pseudonimo, senza nomi
    # già in uso, si chiede nel messaggio.
    testo = [d for d in mancanti if d.libera or len(d.opzioni) < 2]
    scelte = [d for d in mancanti if d not in testo]
    blocchi = [scelte[i:i + 4] for i in range(0, len(scelte), 4)]
    return {
        "testo": [{"chiave": d.chiave, "domanda": d.testo} for d in testo],
        "giri": [
            [
                {
                    "chiave": d.chiave,
                    "question": d.testo,
                    "header": d.intestazione,
                    "multiSelect": d.multipla,
                    "options": [{"label": o.etichetta, "description": o.descrizione} for o in d.opzioni],
                    "valori": {o.etichetta: o.valore for o in d.opzioni},
                }
                for d in blocco
            ]
            for blocco in blocchi
        ],
    }


def riepilogo(avvio: Avvio) -> str:
    """Le risposte in vigore, una per riga, con quelle ancora per default."""

    def segno(chiave: str) -> str:
        return "" if chiave in avvio.risposte else "  (default, da chiedere)"

    concorrente = (
        f"ASIN {avvio.asin}" if avvio.asin
        else f"da trovare nella nicchia «{avvio.nicchia}»" if avvio.nicchia
        else "manca"
    )
    vetrina = {"entrambe": "copertina e prezzo", "nessuna": "nessuna"}.get(avvio.vetrina, avvio.vetrina)
    righe = [
        f"  concorrente  {concorrente}{segno('concorrente')}",
        f"  mercato      {avvio.mercato} ({avvio.lingua}, {avvio.valuta}){segno('mercato')}",
        f"  categoria    {avvio.categoria}{segno('categoria')}",
        f"  vantaggi     {', '.join(avvio.vantaggi)}{segno('vantaggi')}",
        f"  vetrina      {vetrina}{segno('vetrina')}",
        f"  pseudonimo   {avvio.pseudonimo or 'nuovo, proposto col titolo'}{segno('pseudonimo')}",
        f"  pagina       {avvio.pagina}{segno('pagina')}",
    ]
    return "\n".join(righe)


# --------------------------------------------------------------------------
# Quello che le risposte producono
# --------------------------------------------------------------------------
def vincoli(avvio: Avvio) -> str:
    """Le risposte come vincolo per il posizionamento, in coda all'indirizzo editoriale."""
    righe = [
        "Dalle domande d'avvio (`concorrente/avvio.json`), decise dall'autore:",
        "",
        f"- Mercato: {avvio.mercato}. Il libro è in lingua «{avvio.lingua}» e il prezzo "
        f"si propone in {avvio.valuta}.",
        f"- Categoria: {CATEGORIE[avvio.categoria]}",
        "- Dove il libro nuovo deve battere quello di partenza:",
        *(f"  - {VANTAGGI[v]}" for v in avvio.vantaggi),
    ]
    if avvio.copertina:
        righe.append(
            f"  - {VETRINE['copertina']} Per questo il titolo dev'essere corto e forte in "
            "miniatura: le parole lunghe vanno nel sottotitolo."
        )
    if avvio.prezzo:
        righe.append(f"  - {VETRINE['prezzo']}")
    if avvio.pseudonimo:
        righe.append(f"- Autore: {avvio.pseudonimo}.")
    return "\n".join(righe)


COPERTINA_TEMPLATE = """# La copertina da cui distinguersi

<!-- L'autore vuole una copertina più attraente di quella del concorrente.
     Qui va la descrizione della sua copertina in miniatura, come la riporta
     Cowork (punto «Copertina» di cowork-concorrente): colore dominante, che
     cosa mostra l'immagine, quanto spazio prende il titolo e se si legge,
     bollini o cifre. Senza titolo né nome dell'autore: finisce nel brief di
     copertina, e il brief non nomina libri altrui.

     `kdpfactory copertina` la legge e chiede un'immagine che se ne distingua.
     Le righe che cominciano con # o con <!-- non vengono lette. -->

"""


def leggi_copertina(project: BookProject) -> str:
    """La descrizione della copertina concorrente, senza commenti e titoli; vuota se manca."""
    file = copertina_path(project)
    if not file.exists():
        return ""
    testo = re.sub(r"<!--.*?-->", "", file.read_text(encoding="utf-8"), flags=re.S)
    return "\n".join(r for r in testo.splitlines() if not r.lstrip().startswith("#")).strip()


def richiesta_cowork(avvio: Avvio, slug: str, ramo: str, leggimi: str) -> tuple[str, str]:
    """Il nome e il testo della richiesta a Cowork per questo libro.

    Con l'ASIN chiede la pagina del concorrente; con la sola nicchia chiede i
    primi 20 della categoria, da cui la fabbrica sceglie il concorrente.
    """
    mercato = MERCATI[avvio.mercato]
    testa = (
        f"Richiesta della fabbrica per Cowork, con le regole di\n`{leggimi}`.\n"
        "La risposta va in `{risposta}`, accanto a questo file,\n"
        f"sul ramo `{ramo}`, con la stessa numerazione.\n"
        "Per ogni punto: il fatto visto sulla pagina, l'URL, la data e l'ora.\n"
        "Se una pagina chiede un captcha o l'accesso e non si riesce ad andare avanti,\n"
        "scrivilo invece di stimare: l'accesso non lo fai tu.\n"
    )
    consegna = (
        f"Prima di cominciare: dal pulsante «Deliver to» di {avvio.mercato} imposta un\n"
        f"indirizzo {mercato['paese']} (per esempio {mercato['cap']}), così prezzi e\n"
        f"disponibilità sono quelli del mercato, in {avvio.valuta}. Alla fine rimetti\n"
        "l'indirizzo com'era. Non serve l'accesso a nessun account.\n"
    )
    if avvio.asin:
        nome = "cowork-concorrente.md"
        punti = [
            f"1. **Scheda.** Apri https://www.{avvio.mercato}/dp/{avvio.asin} e riporta,\n"
            "   copiandoli dalla pagina: titolo e sottotitolo, autore, formato, prezzo del\n"
            f"   cartaceo e dell'eBook in {avvio.valuta}, e dal riquadro «Product details»\n"
            "   pagine, editore, data di pubblicazione e dimensioni.\n"
            "   Se l'ASIN apre l'edizione Audible o Kindle, passa dal selettore dei formati\n"
            "   al cartaceo («Paperback», o «Hardcover» se manca) e da lì in poi riporta i\n"
            "   dati di quello, con il suo ASIN o ISBN-10: è il formato con cui il libro\n"
            "   nuovo compete. Se il cartaceo non esiste, scrivilo e resta sull'edizione\n"
            "   aperta.",
            "2. **Classifica.** La riga «Best Sellers Rank» intera: la posizione in Books e\n"
            "   quella in ciascuna categoria, con il percorso della categoria.",
            "3. **Descrizione.** Il testo completo, alla lettera (apri «Read more»).",
            "4. **Indice.** Se c'è l'anteprima («Look inside»), i titoli dei capitoli come\n"
            "   appaiono nell'indice. Se non c'è, scrivi «nessuna anteprima».",
            "5. **Recensioni.** Voto medio, numero di valutazioni e la ripartizione per\n"
            "   stelle. Poi le recensioni alla lettera, con stelle, titolo e data: tutte\n"
            "   quelle da 1, 2 e 3 stelle che riesci ad aprire (filtro per stelle), e\n"
            "   almeno dieci da 4 e 5 stelle. Non riassumerle: la fabbrica cita le parole\n"
            "   esatte di chi ha pagato il libro, e un riassunto non si può citare.",
        ]
        if avvio.copertina:
            punti.append(
                "6. **Copertina.** Descrivi la copertina come appare in miniatura nei\n"
                "   risultati di ricerca: colore dominante, che cosa mostra l'immagine,\n"
                "   quanto spazio prende il titolo e se si legge, bollini o cifre. Senza\n"
                "   riportare titolo e autore. Non serve l'immagine."
            )
        punti.append(
            f"{len(punti) + 1}. **Vicini di scaffale.** I primi cinque libri cartacei che la pagina\n"
            "   propone fra i prodotti collegati: titolo, prezzo, pagine, voto e numero di\n"
            "   valutazioni."
        )
        uso = [
            "- i punti 1-5 vanno in `concorrente/pagina.md`, che leggono `scheda-concorrente`",
            "  e `analista-recensioni`;",
        ]
        if avvio.copertina:
            uso.append("- il 6 va in `concorrente/copertina.md`, per il brief di copertina;")
        uso.append("- i vicini di scaffale vanno al `posizionamento`, per prezzo e pagine.")
        corpo = (
            f"# Cowork · pagina del concorrente — {slug}\n\n"
            + testa.replace("{risposta}", "cowork-concorrente-risposta.md")
            + f"\nUn libro nuovo nasce contro questo: ASIN {avvio.asin}, su {avvio.mercato}. Serve\n"
            "la sua pagina Amazon, che dal container della fabbrica non si raggiunge.\n\n"
            + consegna
            + "\n"
            + "\n".join(punti)
            + "\n\nChi usa i risultati:\n"
            + "\n".join(uso)
            + "\n\nLi applica la sessione della fabbrica.\n"
        )
        return nome, corpo

    nome = "cowork-nicchia.md"
    punti = [
        f"1. **Categoria.** Cerca su {avvio.mercato}, reparto Books, «{avvio.nicchia}», e apri la\n"
        "   pagina Best Sellers della categoria più vicina. Riporta il percorso\n"
        "   completo della categoria e l'URL.",
        "2. **I primi 20.** Per i primi 20 libri cartacei della classifica (salta le\n"
        "   schede Audible e Kindle): titolo, autore, ASIN, prezzo in "
        f"{avvio.valuta}, pagine,\n"
        "   voto medio, numero di valutazioni, Best Sellers Rank in Books, e se è un\n"
        "   libro da leggere o da compilare.",
        "3. **Le recensioni deboli.** Per i cinque con più valutazioni: la ripartizione\n"
        "   per stelle, in percentuale, e i titoli delle tre recensioni da 1-3 stelle\n"
        "   più utili.",
    ]
    corpo = (
        f"# Cowork · la nicchia del concorrente — {slug}\n\n"
        + testa.replace("{risposta}", "cowork-nicchia-risposta.md")
        + f"\nUn libro nuovo deve sfidare un libro che vende già nella nicchia «{avvio.nicchia}».\n"
        "Il concorrente lo sceglie la fabbrica, fra quelli che riporti: quello che\n"
        "vende di più con le recensioni più scontente.\n\n"
        + consegna
        + "\n"
        + "\n".join(punti)
        + "\n\nChi usa i risultati: la fabbrica sceglie il concorrente e apre\n"
        "`cowork-concorrente.md` per la sua pagina.\n"
    )
    return nome, corpo

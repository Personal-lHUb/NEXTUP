"""Le parole chiave, cercate da Cowork in due tempi.

La fabbrica non vede Amazon, e le parole chiave non si indovinano: sono le
frasi che i lettori digitano davvero. Le cerca il ruolo «parole-chiave» di
Cowork, con quattro strumenti — Amazon, Helium 10, Publisher Rocket e Google
Trends —, in due momenti del libro:

1. **all'avvio**, sulla nicchia del concorrente (`concorrente/cowork-parole-chiave.md`):
   la tabella che arriva la legge il posizionamento, che sceglie da lì le
   sette frasi e le parole del titolo;
2. **alla scheda**, sulle sette frasi scelte (`manuale/cowork-verifica-parole-chiave.md`):
   prima di caricare il libro si controlla che ciascuna sia viva, e quanto
   sono affollate le categorie.

Le richieste le scrive il sistema, uguali per ogni libro. Gli strumenti a
pagamento si usano solo con l'accesso che l'autore ha già aperto nel browser:
Cowork non entra con le credenziali e non compra niente.
"""

from __future__ import annotations

from . import cowork
from .avvio import MERCATI, consegna

RUOLO = "parole-chiave"
ESPLORAZIONE = "cowork-parole-chiave.md"
VERIFICA = "cowork-verifica-parole-chiave.md"

#: Il paese di Google Trends per ogni mercato.
PAESE_TRENDS = {"amazon.com": "Stati Uniti", "amazon.co.uk": "Regno Unito", "amazon.it": "Italia"}

_STRUMENTI = (
    "Helium 10 e Publisher Rocket si usano solo se l'autore ha già aperto l'accesso\n"
    "nel browser: non si inseriscono credenziali, non si compra niente, non si\n"
    "cambiano impostazioni. Se uno strumento non è accessibile, i suoi punti restano\n"
    "vuoti e la risposta è «Esito: parziale», con il motivo. Le cifre degli\n"
    "strumenti sono stime loro: si riportano come le mostrano, con il nome dello\n"
    "strumento.\n"
)


def esplorazione(asin: str, mercato: str, slug: str, canale: dict) -> tuple[str, str]:
    """La richiesta del primo tempo: le parole chiave della nicchia, dal concorrente."""
    trends = PAESE_TRENDS.get(mercato, "il paese del mercato")
    punti = [
        f"1. **Semi.** Apri https://www.{mercato}/dp/{asin} (se è un'edizione Audible o\n"
        "   Kindle, passa al cartaceo dal selettore dei formati). Dal titolo, dal\n"
        "   sottotitolo e dalle categorie del libro ricava da cinque a otto frasi di\n"
        "   partenza, di due-quattro parole, e riportale con da dove vengono.",
        f"2. **Amazon.** Per ogni seme, nella barra di ricerca di {mercato}, reparto\n"
        "   Books: tutte le frasi che propone l'autocompletamento, alla lettera. Poi,\n"
        "   per le 20-30 frasi più pertinenti fra semi e suggerimenti: il numero di\n"
        "   risultati della ricerca con `i=stripbooks`, e i primi tre libri cartacei\n"
        "   in risultato (titolo, Best Sellers Rank in Books, numero di valutazioni).",
        "3. **Helium 10.** Cerebro sull'ASIN del cartaceo del concorrente: le prime 30\n"
        "   parole chiave per volume di ricerca, con il volume stimato e la posizione\n"
        "   organica del concorrente. Magnet su ciascun seme: le prime dieci frasi per\n"
        "   volume.",
        "4. **Publisher Rocket.** Keyword Search su ciascun seme, mercato Amazon\n"
        f"   {mercato}: ricerche mensili stimate, numero di libri in concorrenza e\n"
        "   punteggio di concorrenza.",
        f"5. **Google Trends.** I tre semi principali, {trends}, ultimi cinque anni:\n"
        "   se l'interesse cresce, è stabile o cala, e in quali mesi è più alto.",
        "6. **Tabella.** Una tabella unica con tutte le frasi trovate ai punti 2-4,\n"
        "   senza doppioni, con le colonne: frase · autocompletamento Amazon (sì/no) ·\n"
        "   risultati Amazon · volume Helium 10 · ricerche mensili Rocket ·\n"
        "   concorrenza Rocket. Una cella vuota dove lo strumento non ha dato il dato.",
    ]
    corpo = (
        cowork.intestazione(
            f"Cowork · parole chiave della nicchia — {slug}",
            ESPLORAZIONE.replace(".md", "-risposta.md"),
            RUOLO,
            canale,
            f"books/{slug}/concorrente",
        )
        + f"\nUn libro nuovo nasce contro l'ASIN {asin}, su {mercato}. Prima che la fabbrica\n"
        "decida titolo e parole chiave, servono le frasi che i lettori di questa nicchia\n"
        "digitano davvero, con quanto sono cercate e quanto sono affollate.\n\n"
        + consegna(mercato)
        + "\n"
        + _STRUMENTI
        + "\n"
        + "\n".join(punti)
        + "\n\nChi usa i risultati: il `posizionamento`, che sceglie da questa tabella le\n"
        "sette parole chiave del libro e le parole del titolo. Li applica la sessione\n"
        "della fabbrica.\n"
    )
    return ESPLORAZIONE, corpo


def verifica(
    titolo: str, parole: list[str], categorie: list[str], mercato: str, slug: str, canale: dict
) -> tuple[str, str]:
    """La richiesta del secondo tempo: le sette frasi della scheda, prima di caricarla."""
    if mercato not in MERCATI:
        raise ValueError(f"mercato sconosciuto: {mercato}")
    elenco = "\n".join(f"   - {p}" for p in parole) or "   - (nessuna: la scheda non ne ha)"
    scaffali = "\n".join(f"   - {c}" for c in categorie) or "   - (nessuna: la scheda non ne ha)"
    punti = [
        "1. **Le sette frasi.** Per ciascuna:\n"
        f"   - nella barra di ricerca di {mercato}, reparto Books, se l'autocompletamento\n"
        "     la propone (sì, simile o no; se simile, la proposta più vicina, alla\n"
        "     lettera);\n"
        "   - il numero di risultati con `i=stripbooks`;\n"
        "   - il volume stimato di Helium 10 (Magnet) e le ricerche mensili e la\n"
        "     concorrenza di Publisher Rocket.\n\n"
        + elenco,
        "2. **Le categorie.** Per ciascuna, la pagina Best Sellers di "
        f"{mercato} (Books):\n"
        "   il Best Sellers Rank in Books del 1° e del 20° libro cartaceo (salta le\n"
        "   schede Audible e Kindle), e se fra i primi 20 prevalgono libri da leggere\n"
        "   o da compilare.\n\n"
        + scaffali,
        "3. **Tabella.** Le sette frasi in una tabella: frase · autocompletamento ·\n"
        "   risultati Amazon · volume Helium 10 · ricerche Rocket · concorrenza Rocket.",
    ]
    corpo = (
        cowork.intestazione(
            f"Cowork · verifica delle parole chiave — {slug}",
            VERIFICA.replace(".md", "-risposta.md"),
            RUOLO,
            canale,
            f"books/{slug}/manuale",
        )
        + f"\nIl libro: «{titolo}», su {mercato}. Le sette parole chiave e le categorie\n"
        "qui sotto sono quelle della scheda che sta per essere caricata: si controlla\n"
        "che ciascuna frase sia cercata davvero e quanto è affollato ogni scaffale.\n\n"
        + consegna(mercato)
        + "\n"
        + _STRUMENTI
        + "\n"
        + "\n\n".join(punti)
        + "\n\nChi usa i risultati: la scheda del libro (`book.json` e `manuale/scheda.json`);\n"
        "una frase che non regge si sostituisce, e la sostituta passa dalla conformità.\n"
        "Li applica la sessione della fabbrica.\n"
    )
    return VERIFICA, corpo

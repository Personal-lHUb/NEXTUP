"""Chi fa che cosa: una competenza, un solo responsabile.

È la regola che tiene insieme il collegio. Se due agenti guardano la stessa
cosa, uno dei due spreca una chiamata, l'editor riceve due segnalazioni che
dicono la stessa cosa con parole diverse, e quando si contraddicono nessuno sa
quale vale. Qui sta l'elenco completo: da questa tabella ogni agente ricava il
proprio campo e, soprattutto, l'elenco di quello che **non** deve guardare, con
il nome di chi se ne occupa. Il test del collegio fa rispettare la regola: una
competenza con due responsabili, o un agente senza competenze, non passa.

Le competenze sono scritte come le leggerebbe l'agente: che cosa guarda, non
come lo guarda. Il come sta nel suo prompt.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Competenza:
    fase: str
    cosa: str
    agente: str


#: Le fasi nell'ordine in cui un libro le attraversa.
FASI = ("acquisizione", "progetto", "stesura", "controllo del testo", "oggetto stampato")

COMPETENZE: tuple[Competenza, ...] = (
    # -- acquisizione (solo per i libri che nascono da una scheda Amazon) ------
    Competenza("acquisizione", "i dati della scheda del concorrente: prezzo, pagine, categorie, recensioni",
               "scheda-concorrente"),
    Competenza("acquisizione", "le lacune che i lettori del concorrente scrivono nelle recensioni",
               "analista-recensioni"),
    Competenza("acquisizione", "il libro da fare: promessa, lettore, titolo, pagine, prezzo, temi del brief",
               "posizionamento"),
    Competenza("acquisizione", "la distanza dal libro del concorrente: titolo, marchi altrui, "
               "struttura copiata", "originalita"),
    # -- progetto -------------------------------------------------------------
    Competenza("progetto", "la struttura del libro: tesi, sequenza e contenuto dei capitoli, "
               "raggruppamento in parti, testo di quarta", "architetto"),
    Competenza("progetto", "il testo dell'indice: il titolo definitivo di ogni capitolo e di ogni parte",
               "indice"),
    Competenza("progetto", "le misure della scaletta: argomenti del brief scoperti, capitoli gemelli, "
               "conteggio dei capitoli, date e cifre dichiarate, parti valide, titoli che non stanno "
               "su una riga o in copertina", "revisore-scaletta"),
    # -- stesura --------------------------------------------------------------
    Competenza("stesura", "il testo dei capitoli, sul programma della scaletta e sul budget di parole",
               "ghostwriter"),
    Competenza("stesura", "il ritmo e la voce della frase: cadenze meccaniche, tic da testo generato, "
               "astrazioni", "voce"),
    Competenza("stesura", "l'applicazione delle segnalazioni del collegio al testo", "editor"),
    # -- controllo del testo --------------------------------------------------
    Competenza("controllo del testo", "l'esperienza di chi legge: dove ci si perde, dove ci si annoia, "
               "che cosa suona falso", "lettore-cieco"),
    Competenza("controllo del testo", "le promesse fatte al cliente prima dell'acquisto — titolo, "
               "sottotitolo, gancio di copertina, descrizione, indice — e se il libro le mantiene; "
               "gli annunci «lo vedremo più avanti» che non arrivano; il lettore o il lessico che "
               "cambiano per strada", "lettore-cieco"),
    Competenza("controllo del testo", "la coerenza interna del libro: contraddizioni e conti che non "
               "tornano fra un capitolo e l'altro, ripetizioni, concetti usati prima di essere "
               "spiegati, capitoli superflui o sbilanciati, aperture tutte uguali", "editor-sviluppo"),
    Competenza("controllo del testo", "le affermazioni sul mondo fuori dal libro: dati, statistiche, "
               "fonti, citazioni, norme, generalizzazioni assolute, casi inventati presentati come "
               "veri", "fact-checker"),
    Competenza("controllo del testo", "i rischi legali e le regole di contenuto KDP, nel testo e nella "
               "scheda prodotto: materiale di terzi, marchi e persone reali, consulenza professionale "
               "come prescrizione, promesse di risultato, avvertenze e risorse di crisi mancanti, "
               "parole chiave e categorie", "conformita"),
    Competenza("controllo del testo", "le bozze: refusi, accenti e apostrofi, accordi, punteggiatura, "
               "maiuscole, ripetizioni ravvicinate della stessa parola", "correttore"),
    # -- oggetto stampato -----------------------------------------------------
    Competenza("oggetto stampato", "l'interno impaginato: vedove, orfane, code di capitolo, testo "
               "fuori gabbia, aperture, varietà delle pagine di un medium-content", "impaginazione"),
    Competenza("oggetto stampato", "la copertina: il prompt dell'illustrazione e delle figure "
               "interne, le misure del PDF di copertina, i testi stampati sulla copertina",
               "copertina"),
)


def competenze_di(agente: str) -> list[Competenza]:
    return [c for c in COMPETENZE if c.agente == agente]


#: Agenti di fasi diverse i cui campi si toccano: è lì che nascono i doppioni.
#: L'architetto progetta la struttura e l'editor di sviluppo la verifica sul
#: libro scritto; la copertina stampa dei testi e la conformità controlla la
#: scheda; la voce lavora sulla frase e il correttore sulla parola.
CONFINANTI: tuple[tuple[str, str], ...] = (
    ("architetto", "editor-sviluppo"),
    ("indice", "lettore-cieco"),
    ("copertina", "conformita"),
    ("voce", "correttore"),
)


def fuori_campo(agente: str) -> list[Competenza]:
    """Quello che l'agente non deve guardare: i compagni di fase e i confinanti.

    Non serve elencargli tutto il collegio: a chi rilegge un capitolo interessa
    sapere che cosa fanno gli altri che rileggono, non chi legge le recensioni
    del concorrente né chi scrive i capitoli.
    """
    proprie = competenze_di(agente)
    if not proprie:
        return []
    fasi = {c.fase for c in proprie}
    vicini = {b for a, b in CONFINANTI if a == agente} | {a for a, b in CONFINANTI if b == agente}
    return [
        c for c in COMPETENZE
        if c.agente != agente and (c.fase in fasi or c.agente in vicini)
    ]


def confini(agente: str) -> str:
    """Il blocco che si aggiunge al prompt: il tuo campo, e quello degli altri."""
    proprie = competenze_di(agente)
    if not proprie:
        return ""
    righe = ["IL TUO CAMPO"]
    righe += [f"- {c.cosa}" for c in proprie]
    altre = fuori_campo(agente)
    if altre:
        righe += [
            "",
            "NON È COMPITO TUO — se lo noti, non segnalarlo: se ne occupa un altro agente, e due "
            "segnalazioni sulla stessa cosa confondono chi deve correggere.",
        ]
        righe += [f"- {c.cosa} → `{c.agente}`" for c in altre]
    return "\n".join(righe) + "\n\n"

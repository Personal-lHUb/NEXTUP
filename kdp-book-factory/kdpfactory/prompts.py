"""Prompt per la generazione dei contenuti.

Il prompt di sistema è diviso in blocchi: i primi due (regole d'autore +
"bibbia" del libro) sono identici per tutti i capitoli e vengono messi in
cache, il terzo cambia a ogni capitolo. È questo che rende economico scrivere
un libro intero: il contesto stabile si paga una volta.
"""

from __future__ import annotations

from . import kdpspecs
from .models import BookSpec, ChapterPlan, Outline

LANGUAGE_NAMES = {"it": "italiano", "en": "inglese"}

# Formule da evitare: sono i tic che rendono un testo immediatamente
# riconoscibile come generato in serie.
BANNED_OPENERS = [
    "Nel mondo di oggi",
    "Nell'era digitale",
    "In un mondo sempre più",
    "È importante notare che",
    "In questo capitolo esploreremo",
    "In conclusione, possiamo dire",
    "Che tu sia un principiante o un esperto",
    "Immagina di",
    "Non è un segreto che",
    "Approfondiamo",
]


AUTHOR_RULES = """Sei un autore professionista di libri pubblicati. Scrivi un capitolo alla volta di un libro che verrà stampato e venduto: il testo deve reggere la lettura su carta, senza possibilità di correzioni successive.

REGOLE DI SCRITTURA
1. Scrivi prosa continua, non appunti. Paragrafi di 3-6 frasi, lunghezza variabile. Mai elenchi puntati usati al posto delle spiegazioni.
2. Ogni affermazione deve essere sostenuta da un meccanismo, un esempio concreto o un ragionamento verificabile. Niente affermazioni generiche.
3. Usa esempi specifici e plausibili (persone con un nome, numeri, situazioni circostanziate). Non presentare esempi inventati come casi reali documentati: introducili come esempi.
4. Non citare studi, statistiche, ricerche, libri o persone reali con dati precisi se non sei certo della fonte: in un libro stampato una citazione sbagliata è un danno permanente. Preferisci il ragionamento diretto.
5. Vietato il riempitivo: niente riepiloghi di ciò che stai per dire, niente frasi che annunciano il capitolo successivo, niente ripetizioni di concetti già spiegati.
6. Vietati questi attacchi e formule: {banned}.
7. Varia la struttura delle frasi. Alterna frasi brevi e lunghe. Usa la seconda persona singolare quando ti rivolgi al lettore.
8. Non ripetere contenuti già coperti in altri capitoli: ti verrà indicato cosa è già stato scritto.
9. Scrivi contenuto originale. Non riprodurre testi protetti da copyright, testi di canzoni, poesie o brani di altri autori.
10. Rispetta il budget di parole richiesto con uno scarto massimo del 10%: il numero di pagine del libro dipende da questo.

FORMATO DI USCITA
- Markdown semplice, nient'altro. Nessun preambolo, nessun commento sul lavoro svolto.
- Prima riga: `# Titolo del capitolo` (esattamente il titolo fornito).
- Sottotitoli di sezione con `## `, eventuali sotto-sezioni con `### `.
- Sono ammessi: grassetto `**testo**`, corsivo `*testo*`, elenchi con `- `, elenchi numerati, citazioni con `> `.
- Non usare tabelle, immagini, link, note a piè di pagina, blocchi di codice o HTML.
- Non scrivere mai "Capitolo N" nel titolo: solo il titolo.
"""


def author_rules() -> str:
    return AUTHOR_RULES.format(banned="; ".join(f'"{b}"' for b in BANNED_OPENERS))


def book_bible(spec: BookSpec, outline: Outline | None = None) -> str:
    """Blocco stabile con tutto ciò che definisce il libro."""
    language = LANGUAGE_NAMES.get(spec.language, spec.language)
    lines = [
        "SCHEDA DEL LIBRO",
        f"Lingua: {language} (scrivi interamente in {language})",
        f"Titolo: {spec.title}",
        f"Sottotitolo: {spec.subtitle}" if spec.subtitle else "",
        f"Autore: {spec.author}",
        f"Genere: {spec.genre}",
        f"Argomento: {spec.topic}",
        f"Lettore tipo: {spec.audience}",
        f"Promessa al lettore: {spec.promise}" if spec.promise else "",
        f"Tono e voce: {spec.tone}",
        f"Formato di stampa: {spec.trim} pollici, circa {spec.target_pages} pagine",
    ]
    if spec.wants_exercises:
        lines.append(
            "Ogni capitolo si chiude con una sezione `## In pratica` contenente 3-5 azioni "
            "concrete, formulate come istruzioni eseguibili (non consigli generici)."
        )
    if spec.notes:
        lines.append(f"Istruzioni aggiuntive dell'editore: {spec.notes}")

    if spec.brief:
        # Gli argomenti scritti a mano dall'autore valgono più di qualsiasi
        # inferenza: vanno coperti tutti.
        lines.append("")
        lines.append("ARGOMENTI RICHIESTI DALL'AUTORE (da coprire tutti, senza aggiungerne di estranei)")
        lines.append(spec.brief.strip())

    if outline and outline.chapters:
        lines.append("")
        lines.append("STRUTTURA COMPLETA DEL LIBRO")
        if outline.thesis:
            lines.append(f"Tesi portante: {outline.thesis}")
        for chapter in outline.chapters:
            lines.append(f"{chapter.number}. {chapter.title} — {chapter.summary}")
    return "\n".join(line for line in lines if line)


# --------------------------------------------------------------------------
# Scaletta
# --------------------------------------------------------------------------
OUTLINE_SYSTEM = """Sei un editor di non-fiction e narrativa commerciale. Progetti la struttura di libri che devono funzionare in libreria: ogni capitolo deve avere una ragione d'essere e una promessa specifica.

Rispondi ESCLUSIVAMENTE con un oggetto JSON valido, senza testo prima o dopo, senza blocchi di codice."""


def outline_prompt(spec: BookSpec, chapters: int, words_total: int) -> str:
    language = LANGUAGE_NAMES.get(spec.language, spec.language)
    structure_hint = (
        "I capitoli devono seguire un percorso progressivo: prima il problema e il quadro "
        "concettuale, poi il metodo passo dopo passo, infine applicazione, ostacoli e "
        "consolidamento."
        if spec.genre == "non-fiction"
        else "I capitoli devono seguire una struttura narrativa in tre atti, con un punto di "
        "svolta a metà e un climax nell'ultimo quarto."
    )
    return f"""Progetta la scaletta completa di questo libro.

{book_bible(spec)}

Vincoli:
- Esattamente {chapters} capitoli di contenuto (oltre a eventuali introduzione e conclusione).
- Lunghezza complessiva prevista: circa {words_total} parole.
- {structure_hint}
- I titoli dei capitoli devono essere specifici e invoglianti, mai generici ("Introduzione al metodo" no, "Perché la lista delle cose da fare ti sta rallentando" sì).
- Nessun capitolo deve sovrapporsi a un altro: `beats` diversi, angolazioni diverse.
- Scrivi tutto in {language}.

Rispondi con questo JSON:
{{
  "title": "titolo definitivo (puoi migliorare quello proposto)",
  "subtitle": "sottotitolo orientato al beneficio, max 120 caratteri",
  "thesis": "l'idea portante del libro in due frasi",
  "back_cover": "testo di quarta di copertina: una frase-gancio, poi 2 paragrafi brevi",
  "chapters": [
    {{
      "number": 1,
      "title": "titolo del capitolo",
      "summary": "cosa spiega questo capitolo e perché sta qui, in due frasi",
      "beats": ["punto 1", "punto 2", "punto 3", "punto 4"],
      "role": "chapter"
    }}
  ]
}}"""


# --------------------------------------------------------------------------
# Capitoli
# --------------------------------------------------------------------------
#: Il blocco «già trattato» viaggia nel messaggio dell'utente, cioè fuori dalla
#: cache, e cresce di un riassunto a ogni capitolo: su un libro da 32 capitoli
#: l'ultimo ne riceve trentuno. Il costo è di pochi centesimi, ma l'istruzione
#: che conta — scrivi QUESTO capitolo, questi punti, questa lunghezza — finisce
#: sepolta in fondo. Si tengono i riassunti recenti, che sono quelli da cui ci si
#: ripete davvero; il piano completo del libro sta già nella scheda, che è un
#: blocco stabile e quindi in cache.
COVERED_BUDGET_WORDS = 350
COVERED_MIN_CHAPTERS = 3


def focus_covered(
    covered: list[str],
    budget_words: int = COVERED_BUDGET_WORDS,
    minimo: int = COVERED_MIN_CHAPTERS,
) -> tuple[list[str], int]:
    """I riassunti più recenti che stanno nel budget, e quanti ne restano fuori.

    Il minimo vince sul budget: anche con riassunti lunghi, gli ultimi capitoli
    arrivano sempre, perché è dal capitolo appena scritto che ci si ripete.
    """
    tenuti: list[str] = []
    parole = 0
    for voce in reversed(covered or []):
        lunghezza = len(voce.split())
        if len(tenuti) >= minimo and parole + lunghezza > budget_words:
            break
        tenuti.append(voce)
        parole += lunghezza
    tenuti.reverse()
    return tenuti, len(covered or []) - len(tenuti)


def chapter_prompt(
    spec: BookSpec,
    chapter: ChapterPlan,
    *,
    previous_summary: str = "",
    covered: list[str] | None = None,
    next_title: str = "",
) -> str:
    role_instructions = {
        "intro": (
            "Questa è l'introduzione. Deve aprire con una scena o un problema concreto, "
            "dichiarare cosa il lettore otterrà e come è organizzato il libro. Non riassumere "
            "i capitoli uno per uno: spiega il percorso."
        ),
        "conclusion": (
            "Questa è la conclusione. Deve chiudere il ragionamento del libro, non riassumerlo. "
            "Indica cosa fare nei primi 30 giorni e quale errore evitare."
        ),
        "chapter": "",
    }
    covered_text = ""
    if covered:
        recenti, omessi = focus_covered(covered)
        elenco = "\n".join(f"- {item}" for item in recenti)
        coda = (
            f"\nI {omessi} capitoli ancora precedenti stanno nella struttura completa del "
            "libro, nella scheda qui sopra: non ripetere nemmeno quelli.\n"
            if omessi
            else ""
        )
        covered_text = f"\nGIÀ TRATTATO NEI CAPITOLI PRECEDENTI (non ripeterlo):\n{elenco}\n{coda}"

    beats = "\n".join(f"- {b}" for b in chapter.beats) or "- (struttura libera, coerente con la sintesi)"

    return f"""Scrivi il capitolo indicato, completo e pronto per la stampa.

Numero del capitolo: {chapter.number}
Titolo del capitolo: {chapter.title}
Ruolo: {chapter.role}
Sintesi: {chapter.summary}

Punti da coprire:
{beats}
{covered_text}
{f"Sintesi del capitolo precedente: {previous_summary}" if previous_summary else ""}
{f"Il capitolo successivo sarà: {next_title} (non anticiparlo, non annunciarlo)" if next_title else ""}
{role_instructions.get(chapter.role, "")}

Lunghezza richiesta: {chapter.target_words} parole (scarto massimo 10%).
Comincia direttamente con `# {chapter.title}`."""


SUMMARY_SYSTEM = (
    "Riassumi il capitolo fornito in massimo 60 parole, elencando solo i concetti "
    "introdotti, in modo che un altro autore sappia cosa è già stato detto. "
    "Rispondi con il solo riassunto."
)


def revise_prompt(
    chapter: ChapterPlan, current_words: int, target_words: int, text: str
) -> str:
    delta = target_words - current_words
    if delta > 0:
        action = f"""Il capitolo è troppo corto: {current_words} parole invece di {target_words}.
Espandilo di circa {delta} parole AGGIUNGENDO sostanza: un esempio concreto in più, un passaggio
del ragionamento reso esplicito, un'obiezione affrontata, un caso limite. Non allungare le frasi
esistenti, non aggiungere riepiloghi, non ripetere concetti."""
    else:
        action = f"""Il capitolo è troppo lungo: {current_words} parole invece di {target_words}.
Accorcialo di circa {abs(delta)} parole TAGLIANDO: ripetizioni, premesse ovvie, aggettivi
superflui, esempi ridondanti. Mantieni tutti i concetti e tutti gli esempi migliori."""

    return f"""{action}

Restituisci il capitolo completo riscritto, in Markdown, iniziando da `# {chapter.title}`.
Nessun commento, nessuna spiegazione di cosa hai cambiato.

TESTO ATTUALE:
---
{text}
---"""


# --------------------------------------------------------------------------
# Metadati per la scheda prodotto KDP
# --------------------------------------------------------------------------
METADATA_SYSTEM = """Sei un esperto di posizionamento di libri su Amazon. Conosci i limiti della scheda prodotto KDP: titolo e sottotitolo entro 200 caratteri complessivi, descrizione entro 4000 caratteri, esattamente 7 keyword (ognuna max 50 caratteri).

Regole obbligatorie:
- Non inserire nella descrizione: nomi di altri autori o libri, affermazioni non verificabili ("bestseller", "il migliore"), promesse di risultati garantiti, riferimenti a prezzi o promozioni, link, indirizzi email.
- Le keyword non devono ripetere parole già presenti nel titolo o nel sottotitolo, non devono contenere nomi di marchi o autori, né termini soggettivi ("il migliore").
- Nei testi di copertina non scrivere cifre: quante pagine, quanti capitoli, quante schede lo conta il sistema sul libro finito, e un numero che il libro non ha viene rifiutato prima della stampa.
- Rispondi ESCLUSIVAMENTE con JSON valido, senza blocchi di codice."""


#: I testi della prima di copertina cambiano con la categoria di prodotto
#: (CLAUDE.md): il medium-content si vende dicendo che prodotto è, il
#: full-content dicendo che promessa mantiene.
COVER_FIELDS_MEDIUM = """  "cover_kicker": "che tipo di prodotto è, 2-3 parole in maiuscolo (es. SCHEDE PRATICHE, ESERCIZI GUIDATI): è il primo segnale che il cliente legge in miniatura",
  "cover_hook": "il beneficio funzionale in una riga, max 62 caratteri, meglio se resta in sospeso",
  "cover_badge": "una garanzia vera e verificabile sul contenuto, max 5 parole, senza cifre (stringa vuota se non ne esiste una onesta)\""""

COVER_FIELDS_FULL = """  "cover_kicker": "il genere in 2-3 parole maiuscole, oppure stringa vuota se il titolo lo dice già",
  "cover_hook": "il ciclo aperto: una domanda o una promessa incompleta, max 62 caratteri",
  "cover_badge": "lascia la stringa vuota: su un'opera a testo pieno le garanzie da scaffale raccontano il prodotto sbagliato\""""


def metadata_prompt(spec: BookSpec, outline: Outline, sample: str) -> str:
    language = LANGUAGE_NAMES.get(spec.language, spec.language)
    copertina = COVER_FIELDS_MEDIUM if spec.is_medium_content else COVER_FIELDS_FULL
    # I due limiti del titolo non sono la stessa cosa e non vanno confusi: 200
    # caratteri è quanto KDP accetta, 60 è dove Amazon taglia nei risultati —
    # ed è il secondo a decidere se il libro viene cliccato.
    taglio = kdpspecs.TITLE_TRUNCATION_CHARS
    insieme = kdpspecs.TITLE_AND_SUBTITLE_MAX_CHARS
    categoria = (
        "medium-content: un libro da usare, dove ogni pagina propone qualcosa di diverso"
        if spec.is_medium_content
        else "full-content: un'opera a testo pieno, dove il valore sta tutto nella sostanza del testo"
    )
    return f"""Prepara la scheda prodotto Amazon KDP per questo libro, in {language}.

Categoria di prodotto: {categoria}.

{book_bible(spec, outline)}

Estratto dal libro (per cogliere il tono reale):
---
{sample[:3000]}
---

Rispondi con questo JSON:
{{
  "title": "titolo corto e memorabile: «Titolo: Sottotitolo» viene tagliato dopo {taglio} caratteri nei risultati di ricerca, e a sparire è sempre la seconda metà — quindi la promessa deve stare prima del taglio, e le parole lunghe vanno nel sottotitolo",
  "subtitle": "sottotitolo orientato al beneficio; titolo e sottotitolo insieme entro {insieme} caratteri, che è il limite di KDP",
  "description_paragraphs": ["paragrafo 1 (gancio)", "paragrafo 2", "paragrafo 3"],
  "bullets": ["cosa impari 1", "cosa impari 2", "cosa impari 3", "cosa impari 4", "cosa impari 5"],
  "closing": "frase di chiusura con chiamata all'azione senza riferimenti al prezzo",
  "keywords": ["7 keyword da ricerca, frasi di 2-4 parole che un lettore digiterebbe"],
  "categories": ["categoria BISAC 1", "categoria BISAC 2", "categoria BISAC 3"],
  "author_bio": "biografia dell'autore in 60-80 parole, in terza persona",
  "back_cover": "testo di quarta di copertina: gancio + 2 paragrafi brevi",
  "back_cover_bullets": ["3 punti brevi per la quarta di copertina"],
{copertina}
}}

I testi di copertina vanno in {language} come il resto della scheda: un occhiello in un'altra lingua dice al cliente che il libro non è per lui."""

# NEXTUP — istruzioni per Claude Code

## Regola permanente: copia di backup di ogni file generato

**Ogni file prodotto deve avere una copia in una cartella di backup.** Vale per
la pipeline e per qualsiasi file generato a mano in una sessione.

- **Pipeline `kdp-book-factory`**: lo fa da sé (`kdpfactory/backup.py`). Ogni
  comando che scrive file lascia uno snapshot datato in
  `kdp-book-factory/backup/<slug>/<AAAAMMGG-hhmmss>/` con scheda del libro,
  scaletta, manoscritto e tutto `build/`. Non passare `--no-backup` se non è
  l'utente a chiederlo.
- **File generati fuori dalla pipeline** (script, export, documenti, immagini,
  configurazioni, risultati di analisi): copiarli subito in
  `backup/manuale/<AAAAMMGG-hhmmss>/`, mantenendo i percorsi relativi.
- **Prima di sovrascrivere o cancellare** un file generato in precedenza: copia
  di sicurezza forzata, anche se un backup recente esiste già.
- `backup/` non entra in git (contiene PDF e cresce in fretta): resta sul disco.
  Per liberare spazio: `python3 -m kdpfactory backup <slug> --prune 10`.

## Regola permanente: i prompt delle immagini li scrive il sistema

**Ogni immagine di un libro nasce da un prompt prodotto da un comando, non
scritto a mano nella chat.** Vale per la copertina e per le figure dell'interno.

```
python3 -m kdpfactory copertina <slug>   # build/copertina-brief.md
python3 -m kdpfactory immagini <slug>    # build/immagini-brief.md
```

Nessuno dei due chiama il modello: leggono i dati che il libro ha già —
categoria, promessa, pubblico, palette, misure di stampa calcolate sulle pagine
vere — e ne fanno un prompt. I file restano in `build/`, entrano nel backup e si
rigenerano quando il libro cambia: sono la traccia di come quell'immagine è
stata chiesta.

Tre cose che questi prompt non negoziano:

- **Il testo lo compone il motore**, sempre, in vettoriale. Il generatore
  consegna la sola illustrazione: un titolo in pixel non si può misurare, e
  sono le misure — corpo contro altezza, contrasto, distanza dal taglio — a
  impedire che esca una copertina illeggibile o rifilata.
- **L'immagine deve rappresentare il libro.** Una forma astratta decora, una
  figura riconoscibile spiega. Il brief porta la rappresentazione della
  categoria, ricavata dalle categorie KDP del libro.
- **L'interno si stampa in bianco e nero.** Le figure si chiedono già in scala
  di grigi: se due elementi si distinguono solo per il colore, sulla pagina
  sono la stessa cosa.

Le figure si dichiarano nel manoscritto **prima che il file esista**:

```markdown
![che cosa deve mostrare l'immagine](immagini/03-nome.jpg)
(didascalia facoltativa, fra parentesi, sulla riga dopo)
```

Finché il file manca, l'impaginazione mette un segnaposto della misura esatta:
il conteggio pagine è già quello definitivo e non cambia quando le immagini
arrivano. `qa` segnala come errore quelle mancanti e quelle sotto i 300 DPI
sulla misura stampata, e come avviso quelle ancora a colori.

## Regola permanente: un libro si fa con le linee guida, un agente per competenza

**La produzione segue `kdp-book-factory/docs/linee-guida.md`**: le fasi in
quell'ordine, e non si passa alla successiva col cancello aperto (zero
bloccanti del revisore di scaletta, pagine nell'intervallo, zero errori di
`qa`).

**Gli agenti si chiamano da soli.** Quando lavori a un libro, chiami tu
l'agente responsabile nel momento in cui la fase lo richiede — con il comando
se misura, come subagent se legge — **senza chiedere il permesso**: questa
regola è l'autorizzazione. La tabella «quando scatta chi» è in
`linee-guida.md`. Gli agenti di una stessa fase che non si toccano (il collegio
di controllo) partono in parallelo, in background. Un agente fermato da un
limite d'uso si rilancia quando il limite passa, non si salta. Ti fermi a
chiedere solo per le decisioni dell'autore (categoria, titolo, promessa, voce
narrante, prezzo, pubblicazione) e quando serve l'immagine di copertina.

**Ogni competenza ha un solo agente**, elencato in
`kdpfactory/agents/competenze.py`. Quando chiami un agente, chiedigli il suo
campo e nient'altro; non chiedere a due agenti la stessa cosa. Tre confini da
ricordare:

- le **promesse** del libro — titolo, descrizione, indice — le giudica solo il
  `lettore-cieco`, che le legge dalla vetrina (`build/vetrina.md`) e non apre
  mai scaletta, `book.json`, brief o rapporti di altri;
- i **conti interni** e le contraddizioni fra capitoli sono dell'`editor-sviluppo`;
  il `fact-checker` guarda solo il mondo fuori dal libro;
- la **copertina** è tutta dell'agente `copertina`: il prompt lo produce
  `kdpfactory copertina <slug>`, l'agente lo verifica e corregge i dati da cui
  nasce, poi misura quello che torna.

Per spostare un confine si cambia la tabella delle competenze e si rigenerano
i file degli agenti (`python3 -m kdpfactory agents --install ../.claude/agents`),
non si modifica a mano un file in `.claude/agents/`.

## Regola permanente: collaborazione con Cowork

Questo container non raggiunge amazon.com, kdp.amazon.com né il computer
dell'autore. Quello che serve da lì lo fa una sessione **Cowork** (app Claude
Desktop). Lo scambio passa da file, non dalla chat, e gira da solo
(`kdp-book-factory/docs/cowork.md`):

- **Richiesta a Cowork**: un file `cowork-<argomento>.md` nella cartella a cui
  serve (es. `books/<slug>/manuale/cowork-amazon.md`), con le istruzioni
  complete e il formato di risposta. Commit e push.
- **Casella su Google Drive** «NEXTUP — libri/cowork» (`config/cowork.json`):
  la fabbrica ci porta le richieste come `<slug>--cowork-<argomento>.md`
  (`sistema--…` per `config/`), Cowork risponde accanto con
  `…-risposta.md`. I nomi e lo stato li dà
  `python3 -m kdpfactory cowork stato --json`; l'avviso da mandare a Cowork
  `python3 -m kdpfactory cowork avviso`.
- **Giro automatico**: l'attività pianificata di Cowork «Cowork — casella
  NEXTUP» (7:52 e 13:52, sul portatile dell'autore: se un giro salta, la
  risposta arriva al giro dopo) risponde alle richieste aperte; la routine
  «Controllo Cowork» di questa sessione (9:59 e 15:59) carica le richieste
  nuove, scarica le risposte nel repo (`cowork-<argomento>-risposta.md`,
  accanto alla richiesta), le applica e segna la richiesta con
  `Stato: applicata il <data>`.
- **Regole di ingaggio** (`docs/cowork.md`):
  - una richiesta nuova si carica nella casella nello stesso giro in cui nasce,
    non solo nel repo, e si registra con `cowork registra`;
  - un file «-risposta.md» nella casella è di Cowork: non si modifica mai. Se
    una risposta è incompleta o bloccata (captcha, accesso), si apre
    `cowork-<argomento>-2.md` con i soli punti mancanti;
  - una richiesta modificata dopo l'invio: la copia vecchia va nel cestino di
    Drive prima di caricare la nuova, e una risposta già scritta alla vecchia è
    superata (se c'è, la nuova si carica come `-2`);
  - ci si ferma dall'autore solo per le sue decisioni (categoria, titolo,
    promessa, voce narrante, prezzo, pubblicazione) e per l'immagine di
    copertina.
- **Le regole per Cowork stanno nella casella**, nel file «LEGGIMI — regole
  della casella.md» (fonte `config/leggimi-casella.md`), che Cowork legge a ogni
  giro. Per cambiarle si aggiorna il LEGGIMI (nuova versione, copia vecchia nel
  cestino, id in `config/cowork.json`), non il prompt dell'attività di Cowork.
- **Resoconto**: per ogni risposta applicata, una riga all'autore:
  «<richiesta>: applicata, <cosa è cambiato>, <decisioni che ti servono>».
- **Riserva manuale**: Cowork può scrivere la risposta nella copia locale del
  repo, e l'autore la pubblica con un push da GitHub Desktop sul ramo
  `claude/dreamy-archimedes-hf8w45`. A inizio sessione: `git pull` e
  `python3 -m kdpfactory cowork stato`.
- Cowork non modifica codice, `book.json`, manoscritto né agenti: scrive solo i
  file di risposta. Applicare i risultati resta compito di questa sessione.
- Le cartelle dove serve una ricerca web, e che cosa cercare in ciascuna, sono
  elencate in `RICERCA-WEB.md`, alla radice del repo.

## Le due categorie di prodotto

Ogni libro di questo progetto è **medium-content** oppure **full-content**. La
categoria si decide prima della scaletta e vincola tutto quello che viene dopo:
impaginazione, scheda prodotto, categorie KDP, prezzo.

**Medium-content** — un libro interattivo cartaceo in cui **ogni pagina presenta
contenuti, layout o stimoli differenti**: esercizi guidati, schede pratiche,
domande di riflessione, griglie operative. Si riconosce dai due confini che non
deve superare:

- **non è low-content.** Un blocco di pagine vuote o di righe ripetitive non è
  un medium-content, è un quaderno. Il banco di prova: se due pagine qualsiasi
  si possono scambiare senza che cambi niente, il libro è dalla parte sbagliata.
- **non è full-content.** Non è un saggio di testo continuo con qualche
  esercizio in coda al capitolo.

**Full-content** — un'opera editoriale a **testo pieno**, destinata a eBook
Kindle e cartaceo, di narrazione continuativa o divulgazione manualistica
approfondita. Il valore risiede interamente nella sostanza del testo originale,
nell'articolazione logica dei capitoli e nella densità concettuale: **nessuna
pagina da compilare, nessuno schema interattivo vuoto**.

La categoria si dichiara in `book.json` con `content_type` (`full` o `medium`),
si sceglie alla creazione con `init --content-type`, e il sistema la fa
rispettare:

- gli esercizi a fine capitolo seguono la categoria (`include_exercises: null`
  lascia decidere a lei; un valore esplicito dell'autore vince);
- su un **full-content** il controllo qualità segnala le righe da riempire a
  mano, che contraddicono la definizione;
- su un **medium-content** l'agente di impaginazione misura quante pagine
  hanno la stessa struttura: oltre la metà, il libro è scivolato nel
  low-content e lo dice;
- la **copertina** segue la formula della categoria — il medium-content vende
  la funzione (che prodotto è, quanto contiene), il full-content la promessa —
  e ogni cifra stampata dev'essere un numero contato sul libro, mai dichiarato
  (`docs/copertine.md`).

La linea prosa (`outline` → `write` → `build`, cioè `all`) produce
full-content; la linea enigmistica (`puzzle`) produce medium-content, e **non
contiene nessun libro**: l'ambientazione — dove si svolge, chi ci abita, i testi
dei casi, la scheda — sta in `books/<slug>/ambientazione.json`, che `puzzle new`
lascia da compilare.

**Il sistema è una fabbrica, non un prodotto.** In `books/` c'è solo `collaudo`,
che non è un libro: serve alle prove a secco. Lo dichiara da sé, con
`"banco_di_prova": true` in `book.json`, e per questo la diagnostica lo lascia
fuori dai conti (`--banchi` per misurarlo lo stesso): i difetti
dell'attrezzatura di prova non sono difetti di un prodotto, e nel rapporto
hanno lo stesso aspetto. Se ti accorgi che un contenuto pubblicabile è finito
nel codice o nel collaudo, è nel posto sbagliato — va spostato in un libro suo.

## Il progetto

`kdp-book-factory/` è una pipeline che produce libri completi (60-240 pagine)
pronti per Amazon KDP: interno PDF, copertina full-wrap, EPUB, scheda prodotto.
Il libro passa da un collegio di agenti (stesura + controllo, fra cui un lettore
cieco, un fact-checker, la conformità e il controllo di impaginazione).

- Documentazione: `kdp-book-factory/README.md` e `kdp-book-factory/docs/`.
- Test: `cd kdp-book-factory && python3 -m unittest discover -s tests`
  (nessun test fa chiamate di rete).
- Lint: `ruff check kdpfactory tests` dalla stessa cartella.
- Per provare la pipeline senza spendere token: `--dry-run`.
- **Senza chiave API** si lavora lo stesso: `manuale <slug> <passo>` produce i
  brief dei passi che userebbero il modello e valida le risposte che incolli
  (`kdp-book-factory/docs/linea-manuale.md`). Tutto il resto — impaginazione,
  copertina, controlli, prezzi, EPUB — non ha mai chiamato il modello.
- Il testo dei libri e la documentazione del progetto sono in italiano.

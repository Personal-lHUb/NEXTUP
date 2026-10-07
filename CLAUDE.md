# NEXTUP — istruzioni per Claude Code

## Regola permanente: copia di backup di ogni file generato

**Ogni file prodotto deve avere una copia in una cartella di backup.** Vale per
la pipeline e per qualsiasi file generato a mano in una sessione.

- **Pipeline `kdp-book-factory`**: lo fa da sé (`kdpfactory/backup.py`). Ogni
  comando che scrive file lascia uno snapshot datato in
  `kdp-book-factory/backup/<slug>/<AAAAMMGG-hhmmss>/` con scheda del libro,
  scaletta, manoscritto, `concorrente/` e tutto `build/`. Non passare `--no-backup` se non è
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
stata chiesta. Con `--genera` lo stesso prompt va a **Higgsfield**
(`kdpfactory/higgsfield.py`, modello GPT Image 2.5, la risoluzione più alta che
dichiara): le varianti tornano in `assets/copertina-N.png`, le figure al loro
percorso, e la traccia — modello, pixel, prompt — in `build/immagini-generate.json`,
che serve anche per dichiarare a KDP i contenuti generati con l'IA. Gli stessi
comandi scrivono `build/copertina-prompt.txt` e `build/immagini-prompt.txt`,
il testo da incollare a mano in ChatGPT se Higgsfield non c'è.

**La copertina si progetta come in una casa editrice**
(`kdpfactory/direzioni.py`, `docs/copertine.md`): Cowork studia le copertine
che vendono nella categoria, l'agente `copertina` scrive tre direzioni d'arte in
`books/<slug>/copertina-direzioni.json`, il sistema ne fa i prompt e un bozzetto
per direzione a bassa risoluzione (`copertina <slug> --direzioni`, `--bozzetti
--genera`), e l'autore sceglie la direzione (`--direzione N`). Le varianti
finali, alla risoluzione più alta, nascono solo dalla direzione scelta. Le regole
dei due video sulle copertine che vendono (`config/cowork-copertine-video-2-risposta.md`)
stanno nel motore, nei prompt e nelle misure; dove contraddicevano la direzione
di prima, hanno vinto i video.

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

**Le figure si valutano libro per libro.** Se servono lo decide l'architetto con
la scaletta, nel piano `books/<slug>/figure.json` (`immagini <slug> --piano`):
una figura entra solo se spiega quello che il testo spiega peggio. Ognuna è
**generata** — coerente con la trama: il prompt porta il capitolo e il mondo
visivo comune del libro — oppure, quando il contesto non lascia generarla
(persone o luoghi reali, documenti, fatti storici, opere d'arte), **pubblica**:
solo pubblico dominio o CC0, cercata negli archivi aperti (`immagini <slug>
--cerca`, `--prendi`) con la provenienza scritta nel piano. `qa` non stampa una
figura pubblica senza licenza ammessa.

Le figure si dichiarano nel manoscritto **prima che il file esista**:

```markdown
![che cosa deve mostrare l'immagine](immagini/03-nome.jpg)
(didascalia facoltativa, fra parentesi, sulla riga dopo)
```

Finché il file manca, l'impaginazione mette un segnaposto della misura esatta:
il conteggio pagine è già quello definitivo e non cambia quando le immagini
arrivano. `qa` segnala come errore quelle mancanti e quelle sotto i 300 DPI
sulla misura stampata, e come avviso quelle ancora a colori.

## Regola permanente: lo standard è quello di un editore di saggistica

**Ogni libro esce come lo farebbe un grande editore di saggistica**
(`kdp-book-factory/docs/standard-editoriale.md`): un carattere da libro in una
famiglia sola (EB Garamond, in `fonts/ofl/`), pagina 1 sulla prima pagina del
testo, capitoli che si aprono a destra calati e col maiuscoletto, titoletti mai
soli in fondo alla pagina, nessuna vedova né orfana. Lo fa il motore, non la
chat: se un libro ne ha bisogno, si cambia il motore per tutti.

**L'indice corrisponde al libro nei due sensi**, e `qa` lo misura
(`kdpfactory/coerenza.py`): il titolo deciso dall'agente `indice` è quello
stampato, ogni voce porta alla pagina dove il capitolo si apre, le parole del
titolo ci sono nel capitolo e lo distinguono dagli altri, i rimandi interni
usano il titolo vero. Un capitolo aggiunto o rinominato torna all'agente
`indice` prima della stampa.

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
limite d'uso si rilancia quando il limite passa, non si salta.

**Le decisioni dell'autore passano dal silenzio-assenso.** Categoria, titolo,
promessa, voce narrante, prezzo, variante di copertina e pseudonimo: non ti
fermi ad aspettarle. Registri la proposta degli agenti con le alternative
(`python3 -m kdpfactory decisioni <slug> --proponi …`), mandi la notifica
all'autore e, se entro 24 ore non risponde, procedi con la proposta. Una sua
risposta vince sempre. La **pubblicazione** non passa mai dal silenzio-assenso:
la decide lui. Nemmeno la **direzione d'arte della copertina**, fra le tre dei
bozzetti: l'autore ha chiesto di sceglierla lui; la variante finale, fra quelle
della direzione scelta, torna al silenzio-assenso. Le immagini — copertina e figure — le genera **questa sessione
con Higgsfield**, dal prompt del sistema (`copertina <slug> --genera`,
`immagini <slug> --genera`; `config/immagini.json`). Serve l'accesso
dell'autore al CLI (`higgsfield auth login`), che nel container si perde
quando la sessione si chiude: se manca, il passo lo dice e aspetta lui. Se la
rete del container blocca Higgsfield, si genera dal **connettore Higgsfield**
(`generate_image_batch`) con gli stessi prompt del sistema
(`coverbrief.prompt_da_incollare(..., per_chat=False)`), e se blocca anche la
sua CDN le varianti restano lì (`build/copertina-higgsfield.json`) e si
scaricano con `copertina <slug> --scarica-generate` quando l'autore apre i
domini di Higgsfield, o le carica lui sul ramo `cowork-immagini`: non si
rigenerano.

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

## Regola permanente: ogni libro nuovo parte dalle domande d'avvio

**Un libro nuovo nasce contro un concorrente preciso** — un libro che vende già
nella nicchia — e deve batterlo dove i suoi lettori restano scontenti. Prima di
qualunque agente si fanno all'autore le sette domande d'avvio, sempre le
stesse, e le risposte le registra il sistema:

```
python3 -m kdpfactory avvio <slug> --json     # le domande ancora da fare
python3 -m kdpfactory avvio <slug> --<domanda> <valore> …
```

- **Il concorrente** (ASIN o link; o la nicchia, e lo cerca Cowork) si chiede
  nel messaggio, perché è un dato da scrivere. Le altre — mercato, categoria,
  dove batterlo nel libro e in vetrina, pseudonimo, chi porta la pagina — con
  le domande a scelta, come le dà `--json`.
- Se l'autore lascia decidere, `--predefinite`: valgono le risposte del primo
  libro fatto così (amazon.com in inglese, categoria come il concorrente,
  lacune + più pratico + contenuto migliore, copertina più attraente,
  pseudonimo nuovo, pagina da Cowork). Il concorrente non ha default.
- Finite le domande, `avvio` prepara la fase 0: il modulo della pagina, le
  richieste `concorrente/cowork-concorrente.md` e `concorrente/cowork-parole-chiave.md`
  da pubblicare nello stesso giro e, se serve, `concorrente/copertina.md`. Poi la
  fase 0 parte da sola quando arrivano la pagina e le parole chiave.
- **Le parole chiave si cercano in due tempi**, da Cowork, con Amazon, Helium 10,
  Publisher Rocket e Google Trends: all'avvio quelle della nicchia, da cui il
  posizionamento sceglie le sette frasi; alla scheda la verifica delle sette
  scelte, con `python3 -m kdpfactory parole-chiave <slug>`.
- Le risposte non si ripetono a mano agli agenti: il posizionamento le riceve
  come vincolo, `concorrente build` impone lingua, categoria scelta e
  pseudonimo, il brief di copertina riceve la copertina da battere.

## Regola permanente: collaborazione con Cowork, in automatico

Questo container non raggiunge amazon.com, kdp.amazon.com, ChatGPT né il
computer dell'autore. Quello che serve da lì lo fa **Cowork** (app Claude
Desktop), e il dialogo è automatico: nessuno dei due aspetta l'autore per
passarsi un file (`kdp-book-factory/docs/cowork.md`).

- **Canale: tutto su GitHub** (`config/cowork.json`, `canale: "github"`). Le
  richieste stanno sul ramo della fabbrica, elencate nell'indice
  `config/cowork-aperte.md` che `python3 -m kdpfactory cowork corriere` riscrive
  a ogni giro, e Cowork le legge dagli indirizzi pubblici del ramo. **Su GitHub
  Cowork non scrive**: niente credenziali, e la sua modalità automatica blocca
  la scrittura dal browser dell'autore come un aggiramento — non si aggira. Le
  risposte arrivano su Drive («NEXTUP — corriere Cowork») col nome che la
  richiesta indica, e questa sessione le porta su GitHub (`--scarica`); su
  Drive ci sono anche il LEGGIMI e gli esiti dei giri non riusciti. Le
  immagini non passano da Cowork: le scarica questa sessione (`copertina
  <slug> --scarica-generate`, coi domini di Higgsfield aperti nella rete
  dell'ambiente) o le carica l'autore sul ramo `cowork-immagini`. Il registro è
  `config/corriere.json`.
- **Ruoli**: un progetto di Claude Desktop con una chat e un'attività oraria per
  ruolo — `concorrente`, `parole-chiave`, `fonti`, `regole-kdp`, `immagini`. Il
  testo per crearli lo genera `python3 -m kdpfactory cowork progetto` in
  `config/progetto-cowork.md`.
- **Richiesta a Cowork**: `cowork-<argomento>.md` nella cartella a cui serve,
  con l'intestazione di `cowork.intestazione()` (titolo, **un ruolo solo** nella
  riga `Ruolo:`, nome della risposta su Drive) e tutto
  quello che serve dentro: Cowork legge l'indice e la richiesta, non il resto
  del repository. Le richieste di ogni libro le scrive il sistema (`avvio`,
  `parole-chiave`, `copertina`, `immagini`).
- **Risposta di Cowork**: un file nuovo su Drive, che `--scarica` porta accanto
  alla richiesta come `cowork-<argomento>-risposta.md`. La prima riga è `Esito:
  completa` o `Esito: parziale — punti …`. Dal ramo `cowork-immagini` arrivano in
  `books/<slug>/assets/` solo le immagini che una richiesta ha chiesto;
  nient'altro può arrivare dal corriere né dal ramo.
- **Senza attese**: dopo il push, la sessione lancia subito (`fire_trigger`) i
  ruoli che `cowork corriere` elenca in **avvia** — quelli che lavorano nel
  cloud (`"cloud": true`), per le richieste senza `Serve:` — e registra
  `--avviato <ruolo>`. Un giro lanciato così è nel cloud, senza il browser del
  portatile: le richieste col browser aspettano l'orario del ruolo. Alla fine
  di un giro in cui ha consegnato, Cowork lancia la routine della fabbrica.
  Ogni giro di Cowork costa: si lancia solo quello che c'è da fare.
- **Stato**: `python3 -m kdpfactory cowork stato`; a che punto è ogni libro:
  `python3 -m kdpfactory produzione`.
- **Giro orario**: la routine «Produzione NEXTUP» riprende questa sessione ogni
  ora (minuto 57) e quando Cowork consegna: `--dal-ramo`, risposte da applicare,
  decisioni scadute, il prossimo passo di ogni libro attivo
  (`config/produzione.json`), indice, push, lanci. Le attività di Cowork girano
  ogni ora sul portatile dell'autore, sfalsate di dieci minuti.
- **Regole di ingaggio**:
  - un file `-risposta.md` è di Cowork: non si modifica mai. Se una risposta è
    incompleta o bloccata (captcha, accesso), si apre
    `cowork-<argomento>-2.md` con i soli punti mancanti;
  - se il seguito dipende da un accesso che apre l'autore (KDP, ChatGPT,
    Helium 10, Amazon), la richiesta porta la riga `Serve:`: Cowork non
    risponde finché l'accesso manca, e `produzione` la dà in attesa dell'autore;
  - una richiesta corretta dopo la risposta rende la risposta superata: la
    versione corretta va in `-2`;
  - le decisioni dell'autore passano dal silenzio-assenso; la pubblicazione no.
- **Le regole per Cowork** stanno in `config/leggimi-cowork.md`, che viaggia
  anche su Drive e Cowork legge a ogni giro. Per cambiarle si aggiorna il LEGGIMI
  (nuova versione, anche in `config/cowork.json`), senza toccare il prompt di
  Cowork.
- **Resoconto**: per ogni risposta applicata, una riga all'autore:
  «<richiesta>: applicata, <cosa è cambiato>, <decisioni che ti servono>».
- Cowork non modifica codice, `book.json`, manoscritto né agenti: scrive solo
  risposte e immagini. Applicare i risultati resta compito di questa sessione.
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

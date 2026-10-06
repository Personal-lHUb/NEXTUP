# LEGGIMI — regole del canale con Cowork

Versione 10 · 6 ottobre 2026 · scritto dalla fabbrica di libri NEXTUP.

Queste regole valgono per ogni giro di Cowork. Se dicono una cosa diversa dal
prompt dell'attività pianificata, vale questo file: lo tiene aggiornato la
fabbrica, e ogni modifica porta un numero di versione nuovo.

**Novità della versione 10: niente git, niente credenziali.** Gli esiti del 6
ottobre l'hanno mostrato: le sessioni di Cowork non hanno `add_repo` e il proxy
rifiuta il push («not in this session's authorized repository set»). Da ora:

- **si legge** dagli indirizzi pubblici del repository, con WebFetch o col
  browser (`raw.githubusercontent.com/...`, li dà l'indice);
- **si consegna** col GitHub dell'autore già aperto nel browser del portatile:
  la pagina che crea il file sul ramo `cowork-immagini`, commit direttamente
  sul ramo;
- **senza browser** (giro nel cloud) o se il commit non riesce, la risposta di
  testo va su Drive col **nome di ripiego** che la richiesta e l'indice danno:
  la fabbrica la porta su GitHub. Le immagini su Drive no.

Restano gli esiti dei giri non riusciti (versione 9) e i giri lanciati dalla
fabbrica (versione 8).

## Dove si lavora

- **Repository** `Personal-lHUb/NEXTUP` su GitHub. Le richieste stanno sul
  ramo `claude/dreamy-archimedes-hf8w45`; l'indice di quelle aperte è
  https://raw.githubusercontent.com/Personal-lHUb/NEXTUP/claude/dreamy-archimedes-hf8w45/kdp-book-factory/config/cowork-aperte.md
  e la fabbrica lo riscrive a ogni giro. Per ogni richiesta l'indice dà:
  l'indirizzo per leggerla («leggi»), il percorso della risposta, la pagina
  per consegnarla («consegna»), il nome di ripiego su Drive e se si fa nel
  cloud o solo col browser del portatile.
- **Le consegne** vanno sul ramo `cowork-immagini`, ognuna al percorso che la
  richiesta indica, a partire dalla cartella `kdp-book-factory/`.
- **Drive** («NEXTUP — corriere Cowork», id `1yprHuxzFDGj12k8clTp0othzTXjiyn5N`)
  porta questo LEGGIMI, le risposte di ripiego e gli esiti dei giri non
  riusciti: nient'altro. Gli altri file della cartella sono vecchi: non aprirli.
- Se il prompt della tua attività parla di cercare le richieste su Drive, di
  `add_repo`, di git o di base64, vale questo file.

## Che cosa c'è da fare

- Le richieste del tuo ruolo che l'indice elenca sotto «Ruolo <il tuo ruolo>».
  Una richiesta di un altro ruolo è di un'altra chat: non aprirla. Una
  richiesta senza ruolo non la prende nessuno: se la trovi, dillo all'autore e
  lasciala lì.
- Una richiesta che ha già la risposta, sul ramo `cowork-immagini` o su Drive
  col nome di ripiego, è fatta: saltala (la fabbrica la porta via entro l'ora
  e la toglie dall'indice).
- Una richiesta con la riga `Serve: …` sotto il ruolo chiede un accesso che
  apre l'autore (KDP, ChatGPT, GitHub, Helium 10, Amazon, il browser del
  portatile). Prima di tutto guarda se c'è. Se manca, salta la richiesta senza
  scrivere niente: al giro dopo la ritrovi aperta. Se c'è, la fai come le altre.
- Una richiesta scritta prima di questa versione può dire di consegnare con
  git o in un altro modo: consegnala come dice questo file.

## Come si risponde

1. Leggi la richiesta per intero ed esegui quello che chiede, punto per punto,
   con la sua numerazione. Tutto quello che ti serve è nella richiesta: se
   manca qualcosa, scrivilo nella risposta invece di cercarlo altrove.
2. Scrivi la risposta in Markdown. La **prima riga** dice com'è andata:
   - `Esito: completa`
   - `Esito: parziale — punti 2, 4: <motivo>` (captcha, accesso, pagina che non
     c'è più, dato che non si trova, strumento non accessibile)
3. Per ogni punto: il fatto che hai visto sulla pagina, non una stima, con
   l'URL e la data e l'ora della verifica.
4. Consegnala come dice la sezione qui sotto. Le immagini che una richiesta
   chiede vanno sul ramo `cowork-immagini`, ognuna al percorso indicato; la
   risposta riporta per ognuna le misure in pixel e il peso.

## Leggere e consegnare

**Leggere.** Con WebFetch (o col browser) dagli indirizzi «leggi» dell'indice.
Non servono git, `gh` né credenziali: il repository è pubblico. Se un indirizzo
non si apre, scrivi l'esito (sezione «Se qualcosa non va»).

**Consegnare col browser** (il GitHub dell'autore è già aperto nel browser del
portatile; l'accesso non lo fai tu):

1. apri la pagina «consegna» della voce: crea un file nuovo sul ramo
   `cowork-immagini`, nella cartella giusta, col nome già scritto;
2. controlla che il ramo sia `cowork-immagini` e il nome del file quello della
   richiesta; incolla la risposta nell'editor;
3. «Commit changes…», scegli «Commit directly to the `cowork-immagini`
   branch», messaggio «Cowork: <nome della richiesta>», conferma. Se GitHub
   propone una pull request, non aprirla;
4. per un'immagine: nella stessa cartella del ramo, «Add file → Upload files»,
   il file col nome indicato, commit direttamente sul ramo.

**Consegnare senza browser** (giro nel cloud), o se il commit non riesce: la
stessa risposta su Drive, nella cartella, col **nome di ripiego** dell'indice
(per esempio `books__x__concorrente__cowork-concorrente-risposta.md`), con
`create_file`, contentMimeType text/markdown, disableConversionToGoogleType
true. La fabbrica la porta su GitHub. Le immagini non vanno su Drive: se non
puoi caricarle col browser, scrivi l'esito.

## Giri nel cloud

Un giro lanciato dalla fabbrica, o qualsiasi giro in cui il browser del
portatile non risponde, è un giro nel cloud.

- Fai solo le richieste che l'indice segna «si fa: nel cloud o col browser», e
  consegnale su Drive col nome di ripiego.
- Quelle segnate «solo col browser del portatile», e ogni richiesta con la riga
  `Serve:`, le salti senza scrivere niente: le riprende l'attività oraria, col
  portatile collegato.
- Se un sito risponde con un blocco (HTTP 403, 429, captcha) a una richiesta
  che si poteva fare nel cloud, la risposta è parziale con il motivo, come
  sempre.

## Se qualcosa non va

Se in questo giro c'era una richiesta del tuo ruolo da fare e un passo tecnico
non è riuscito — un indirizzo che non si apre, il commit nel browser che non
va, un download bloccato, il browser che non risponde, un passo di questo
LEGGIMI che non torna — scrivi su Drive, nella cartella, un file di testo
nuovo:

- nome `cowork-esito-<ruolo>-<AAAAMMGG-hhmm>.md`, con l'ora UTC (per esempio
  `cowork-esito-immagini-20261006-1845.md`);
- prima riga `Esito: non riuscito`;
- poi, per ogni passo che non è andato: che cosa volevi fare, il comando o lo
  strumento usato, il messaggio d'errore **esatto**, copiato;
- infine che cosa sei riuscito a consegnare, se qualcosa, e dove.

Con `create_file`, contentMimeType text/markdown,
disableConversionToGoogleType true. Niente immagini su Drive. Un giro senza
richieste da fare, o in cui tutto è andato, non scrive nessun esito.

## Alla fine del giro

Se in questo giro hai consegnato qualcosa e hai lo strumento `fire_trigger`,
lancia la routine della fabbrica: trigger_id `trig_014uG5o2CZ22kwnBS5FDxty7`,
testo `Cowork, ruolo <ruolo>: consegnato <percorsi>.` Se lo strumento non c'è,
non serve cercarlo: la fabbrica passa ogni ora.

## Che cosa non si fa

- Su GitHub si scrivono solo file nuovi, solo sul ramo `cowork-immagini`, solo
  quelli che una richiesta chiede: le risposte e le immagini. Nessun altro
  ramo, nessuna pull request, niente da unire, rinominare o cancellare,
  nessuna impostazione del repository. Il codice, i `book.json`, i manoscritti
  e gli agenti non si toccano.
- Le richieste, l'indice e questo LEGGIMI non si modificano.
- Una risposta già scritta non si riscrive. Se alla fabbrica serve altro, apre
  una richiesta nuova.
- Su Drive si scrivono solo le risposte di ripiego e gli esiti.
- Su KDP (kdp.amazon.com) si legge e basta: niente titoli nuovi, bozze,
  pubblicazioni o impostazioni cambiate.
- Negli strumenti a pagamento (Helium 10, Publisher Rocket, ChatGPT) e su
  GitHub si usa solo l'accesso che l'autore ha già aperto nel browser: non si
  inseriscono credenziali, non si compra, non si cambiano abbonamenti né
  impostazioni.
- Nessuna password, codice, token o cookie nei file o nei commit.
- `fire_trigger` si usa solo per la routine della fabbrica, alla fine del
  giro. Nessun'altra attività si lancia, si crea, si cambia o si cancella.

## Richieste di seguito e ritirate

`…-2.md`, `…-3.md` sono seguiti di una richiesta già fatta: contengono solo i
punti rimasti aperti, o la versione corretta di una domanda. Una richiesta che
sparisce dall'indice è applicata o ritirata: non si risponde a una copia
vecchia.

Se non ci sono richieste del tuo ruolo da fare, il giro finisce senza scrivere
niente.

## I ruoli

Ogni ruolo ha la sua chat nel progetto e la sua attività pianificata, ogni ora.
Il testo per crearle è in `kdp-book-factory/config/progetto-cowork.md`.

### Ruolo concorrente

Le pagine Amazon dei libri concorrenti: scheda, classifica, descrizione,
indice, recensioni, copertina in miniatura, vicini di scaffale, prezzi. Lavora
col browser del portatile.

- Le **recensioni si copiano alla lettera**, con stelle, titolo e data. Non si
  riassumono: la fabbrica cita le parole esatte, e un riassunto non si cita.
- Se l'ASIN apre un'edizione Audible o Kindle, si passa al **cartaceo** dal
  selettore dei formati: pagine e classifica in Books stanno lì.
- Prezzi nella valuta del mercato: si imposta l'indirizzo di consegna che la
  richiesta indica e alla fine si rimette com'era.

### Ruolo parole-chiave

Le parole chiave e le categorie: che cosa digitano i lettori e quanto sono
affollati gli scaffali. Lavora col browser del portatile.

- **Amazon**: l'autocompletamento si legge nella barra di ricerca, reparto
  Books, e si riporta alla lettera; il numero di risultati è quello della
  ricerca con `i=stripbooks`.
- **Helium 10** (Cerebro, Magnet) e **Publisher Rocket**: solo con l'accesso
  già aperto dall'autore. Se uno strumento non è accessibile, i suoi punti
  restano vuoti e la risposta è parziale, con il motivo. Le cifre sono stime
  dello strumento: si riportano come le mostra, con il suo nome.
- **Google Trends**: nel paese del mercato, sugli ultimi cinque anni.
- Si chiude sempre con la tabella che la richiesta chiede: una frase per riga,
  una cella vuota dove manca il dato. Mai un numero stimato da te.

### Ruolo fonti

Le affermazioni del libro sul mondo, prima della stampa. Si fa anche nel
cloud.

- La richiesta cita la frase esatta del libro: si verifica quella.
- Solo **fonti ufficiali**: il sito dell'ente, della legge, del programma.
  Un articolo di giornale o un blog non bastano: si scrive «non trovato».
- Per ogni punto: **vero**, **cambiato** o **non trovato**, con l'URL e la
  frase esatta che lo conferma o lo smentisce.

### Ruolo regole-kdp

Le regole di KDP che valgono per ogni libro: costi di stampa, limiti, pagine,
selettore delle categorie. Le pagine di aiuto si leggono anche nel cloud; il
flusso di un titolo nuovo solo col browser del portatile.

- Su KDP **si legge e basta**. Nel flusso di un titolo nuovo si guarda e si
  esce senza salvare: niente bozze.
- Se serve l'accesso a KDP e nel browser non è aperto: con la riga `Serve:`
  non rispondi e aspetti il giro dopo; senza, la risposta è parziale con quel
  motivo. L'accesso lo apre l'autore, non tu.
- La fonte preferita è la guida ufficiale di KDP (kdp.amazon.com/help); il
  calcolatore dei costi va citato con le cifre che mostra.

### Ruolo immagini

Le illustrazioni di copertina e le figure dell'interno: generate con
**ChatGPT**, o già generate e da scaricare. Sempre col browser del portatile
(le richieste hanno la riga `Serve:`): nel cloud la CDN delle immagini è
bloccata e le immagini si caricano su GitHub solo dalla pagina web.

- Se in ChatGPT c'è il progetto **«NEXTUP — Immagini»**, si lavora lì: una
  chat nuova del progetto per ogni richiesta, chiamata `<slug> — copertina` o
  `<slug> — figure`. Le istruzioni del progetto contengono già le regole fisse.
  Se il progetto non c'è, si usa una chat normale.
- Il prompt è nella richiesta, scritto dalla fabbrica: si incolla **così com'è**,
  senza aggiungere né togliere. Non si scrive un prompt proprio.
- **Nessun testo nell'immagine**: niente titoli, lettere, numeri, firme. Il
  titolo lo compone la fabbrica, in vettoriale, dopo.
- Formato verticale, nella proporzione che la richiesta indica, alla
  risoluzione più alta che lo strumento consente. Si riportano le misure in
  pixel di ogni immagine consegnata. Se la richiesta indica un minimo e
  l'immagine è più piccola, si consegna lo stesso e lo si scrive: decide la
  fabbrica.
- Le immagini si scaricano a piena risoluzione, così come sono: niente
  ritagli, compressione o conversione.
- Si generano tante varianti quante la richiesta ne chiede, ognuna caricata
  sul ramo `cowork-immagini` al percorso indicato, con «Add file → Upload
  files» nella cartella giusta e il commit direttamente sul ramo. Mai su Drive.
- Le figure dell'interno sono in **scala di grigi**: due elementi non si
  distinguono solo per il colore.
- Solo immagini generate nella sessione o già generate dalla fabbrica: mai
  prese dal web, mai persone reali riconoscibili, mai marchi, loghi o
  personaggi di altri.
- Nella risposta si scrive con quale strumento e modello sono state generate:
  KDP chiede di dichiarare i contenuti generati con l'IA.

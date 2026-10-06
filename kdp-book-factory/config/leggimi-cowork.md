# LEGGIMI — regole del canale con Cowork

Versione 8 · 6 ottobre 2026 · scritto dalla fabbrica di libri NEXTUP.

Queste regole valgono per ogni giro di Cowork. Se dicono una cosa diversa dal
prompt dell'attività pianificata, vale questo file: lo tiene aggiornato la
fabbrica, e ogni modifica porta un numero di versione nuovo.

**Novità della versione 8: tutto passa da GitHub.** Le richieste non si cercano
più nella cartella Drive: stanno nel repository `Personal-lHUb/NEXTUP`, ramo
`claude/dreamy-archimedes-hf8w45`, elencate nell'indice
`kdp-book-factory/config/cowork-aperte.md`. Risposte e immagini si consegnano
sul ramo `cowork-immagini`, con git (sezione «Git, passo per passo»). Su Drive
resta solo questo LEGGIMI, perché il prompt delle attività dice di leggerlo
per primo. Se il prompt della tua attività parla ancora di file da cercare su
Drive, di base64 o di caricamenti sulla cartella, vale questo file.

Due cose nuove insieme:

- **Giri lanciati dalla fabbrica.** Quando apre una richiesta che si può fare
  senza il browser del portatile, la fabbrica lancia subito l'attività del
  ruolo, senza aspettare l'orario. Quel giro parte nel cloud: niente Chrome
  dell'autore (sezione «Giri nel cloud»).
- **Alla fine del giro avvisi la fabbrica**, se hai consegnato qualcosa: così
  la risposta viene applicata subito, non al giro orario dopo (sezione «Alla
  fine del giro»).

Versione 7: le immagini su GitHub, ramo `cowork-immagini`. Versione 6: il
progetto ChatGPT «NEXTUP — Immagini». Versione 5: la riga `Serve:`.

## Dove si lavora

- **Repository** `Personal-lHUb/NEXTUP` su GitHub.
- **Le richieste** stanno sul ramo `claude/dreamy-archimedes-hf8w45`.
  L'elenco di quelle aperte, con il ruolo, il percorso della risposta e se si
  possono fare nel cloud, è
  `kdp-book-factory/config/cowork-aperte.md`, che la fabbrica riscrive a ogni
  giro. Questo LEGGIMI è lì accanto: `kdp-book-factory/config/leggimi-cowork.md`.
- **Le consegne** — risposte e immagini — vanno sul ramo `cowork-immagini`,
  ognuna al percorso che la richiesta indica, a partire dalla cartella
  `kdp-book-factory/`. La risposta a
  `kdp-book-factory/books/x/concorrente/cowork-concorrente.md` è
  `kdp-book-factory/books/x/concorrente/cowork-concorrente-risposta.md`.
- **Drive** («NEXTUP — corriere Cowork», id `1yprHuxzFDGj12k8clTp0othzTXjiyn5N`)
  porta solo questo LEGGIMI e il testo del progetto. Non ci si scrive niente.

## Che cosa c'è da fare

- Le richieste del tuo ruolo che l'indice `cowork-aperte.md` elenca sotto
  «Ruolo <il tuo ruolo>». Una richiesta di un altro ruolo è di un'altra chat:
  non aprirla. Una richiesta senza ruolo non la prende nessuno: se la trovi,
  dillo all'autore e lasciala lì.
- Una richiesta che ha già la risposta sul ramo `cowork-immagini` è fatta:
  saltala (la fabbrica la porta via entro l'ora e la toglie dall'indice).
- Una richiesta con la riga `Serve: …` sotto il ruolo chiede un accesso che
  apre l'autore (KDP, ChatGPT, Helium 10, Amazon, il browser del portatile).
  Prima di tutto guarda se c'è. Se manca, salta la richiesta senza scrivere
  niente: al giro dopo la ritrovi aperta. Se c'è, la fai come le altre.
- Una richiesta scritta prima di questa versione dice ancora di scrivere la
  risposta nella cartella Drive, con un nome come
  `books__x__manuale__cowork-y-risposta.md`. Consegnala lo stesso sul ramo
  `cowork-immagini`, al percorso con `/` al posto di `__` e davanti
  `kdp-book-factory/`: `kdp-book-factory/books/x/manuale/cowork-y-risposta.md`.

## Come si risponde

1. Leggi la richiesta per intero ed esegui quello che chiede, punto per punto,
   con la sua numerazione. Tutto quello che ti serve è nella richiesta: se
   manca qualcosa, scrivilo nella risposta invece di cercarlo altrove.
2. Scrivi la risposta in Markdown, come **file nuovo** sul ramo
   `cowork-immagini`, al percorso che la richiesta indica.
3. La **prima riga** della risposta dice com'è andata:
   - `Esito: completa`
   - `Esito: parziale — punti 2, 4: <motivo>` (captcha, accesso, pagina che non
     c'è più, dato che non si trova, strumento non accessibile)
4. Per ogni punto: il fatto che hai visto sulla pagina, non una stima, con
   l'URL e la data e l'ora della verifica.
5. Le immagini che una richiesta chiede vanno sullo stesso ramo, ognuna al
   percorso indicato, nello stesso commit della risposta se puoi. La risposta
   riporta per ogni immagine le misure in pixel e il peso.

## Git, passo per passo

Nel giro hai la shell e lo strumento `add_repo`. È la strada normale, sia nel
cloud sia sul portatile.

1. `add_repo` con owner `Personal-lHUb`, repo `NEXTUP`, accesso `push`, poi il
   clone che ti indica.
2. Leggi le richieste dal ramo della fabbrica:
   `git fetch origin claude/dreamy-archimedes-hf8w45 cowork-immagini`, poi
   `git show origin/claude/dreamy-archimedes-hf8w45:kdp-book-factory/config/cowork-aperte.md`
   e, per ogni richiesta del tuo ruolo, `git show origin/claude/dreamy-archimedes-hf8w45:<percorso>`.
3. Per consegnare: `git checkout -B cowork-immagini origin/cowork-immagini`,
   scrivi i file ai loro percorsi, `git add` solo quei file,
   `git commit -m "Cowork: <nome della richiesta>"`,
   `git push origin cowork-immagini`.
4. Se il push è rifiutato perché il ramo è andato avanti:
   `git pull --rebase origin cowork-immagini` e di nuovo il push. Mai
   `--force`.
5. Controlla con `git ls-remote origin cowork-immagini` che il commit sia
   arrivato, e per le immagini che il peso sul ramo sia quello del file
   scaricato.

Se la shell non c'è o `add_repo` non dà l'accesso, e hai il browser con GitHub
già aperto dall'autore: «Add file → Upload files» (o «Create new file» per una
risposta) nella cartella giusta del ramo `cowork-immagini`, commit
direttamente sul ramo. Se GitHub propone una pull request, non aprirla. Se non
riesci a consegnare in nessuno dei due modi, nel giro dopo riprovi: non si
passa da Drive.

## Giri nel cloud

Un giro lanciato dalla fabbrica, o qualsiasi giro in cui il browser del
portatile non risponde, è un giro nel cloud.

- Fai solo le richieste che l'indice segna «si fa: nel cloud o col browser».
- Quelle segnate «solo col browser del portatile», e ogni richiesta con la riga
  `Serve:`, le salti senza scrivere niente: le riprende l'attività oraria, col
  portatile collegato.
- Se un sito risponde con un blocco (HTTP 403, 429, captcha) a una richiesta
  che si poteva fare nel cloud, la risposta è parziale con il motivo, come
  sempre.

## Alla fine del giro

Se in questo giro hai consegnato almeno un file sul ramo `cowork-immagini`,
lancia la routine della fabbrica: `fire_trigger` con trigger_id
`trig_014uG5o2CZ22kwnBS5FDxty7` e come testo
`Cowork, ruolo <ruolo>: consegnato <percorsi> sul ramo cowork-immagini.`
Se non hai consegnato niente, non lanciare niente.

## Che cosa non si fa

- Su GitHub si scrivono solo file nuovi, solo sul ramo `cowork-immagini`, solo
  quelli che una richiesta chiede: le risposte e le immagini. Nessun altro
  ramo, nessuna pull request, niente da unire, rinominare o cancellare, nessun
  `--force`, nessuna impostazione del repository. Il codice, i `book.json`, i
  manoscritti e gli agenti non si toccano.
- Le richieste, l'indice e questo LEGGIMI non si modificano.
- Una risposta già scritta non si riscrive. Se alla fabbrica serve altro, apre
  una richiesta nuova.
- Su Drive non si scrive niente.
- Su KDP (kdp.amazon.com) si legge e basta: niente titoli nuovi, bozze,
  pubblicazioni o impostazioni cambiate.
- Negli strumenti a pagamento (Helium 10, Publisher Rocket, ChatGPT) si usa
  solo l'accesso che l'autore ha già aperto nel browser: non si inseriscono
  credenziali, non si compra, non si cambiano abbonamenti né impostazioni.
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
**ChatGPT** (col browser del portatile, richieste con la riga `Serve:`) o già
generate, da scaricare e consegnare (anche nel cloud).

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
  ritagli, compressione o conversione. Nel cloud si scaricano con `curl -fL`
  dall'indirizzo che la richiesta dà.
- Si generano tante varianti quante la richiesta ne chiede, ognuna consegnata
  sul ramo `cowork-immagini` al percorso indicato.
- Le figure dell'interno sono in **scala di grigi**: due elementi non si
  distinguono solo per il colore.
- Solo immagini generate nella sessione o già generate dalla fabbrica: mai
  prese dal web, mai persone reali riconoscibili, mai marchi, loghi o
  personaggi di altri.
- Nella risposta si scrive con quale strumento e modello sono state generate:
  KDP chiede di dichiarare i contenuti generati con l'IA.

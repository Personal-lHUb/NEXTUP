# LEGGIMI — regole del canale con Cowork

Versione 17 · 24 ottobre 2026 · scritto dalla fabbrica di libri NEXTUP.

Queste regole valgono per ogni giro di Cowork. Se dicono una cosa diversa dal
prompt dell'attività pianificata, vale questo file: lo tiene aggiornato la
fabbrica, e ogni modifica porta un numero di versione nuovo.

**Novità della versione 17: amazon.com si può aprire, solo per leggere.**
Decisione dell'autore del 24 ottobre 2026: il rischio sulle Condizioni d'uso di
Amazon lo accetta lui. Quindi, della versione 16 cambia solo questo:

- **puoi aprire amazon.com** (pagine prodotto e liste) **solo per leggere**,
  e solo i link o gli ASIN che l'autore ti allega: non cercare libri per conto
  tuo, non scorrere pagine in serie, non scaricare in massa; niente accesso con
  credenziali, niente acquisti, niente scrittura;
- **resta chiuso kdp.amazon.com** e il completamento automatico
  (completion.amazon.com): su KDP carica l'autore;
- **restano fuori** Helium 10, Publisher Rocket, Google Trends: i dati li
  esporta l'autore.

Il resto della versione 16 (qui sotto) vale ancora, tranne dove dice di non
aprire amazon.com.

**Novità della versione 16: niente siti di Amazon, niente strumenti a pagamento
guidati da te.** Decisione dell'autore del 14 ottobre 2026, per i rischi
legali (`kdp-book-factory/docs/rischi-legali.md`). Le Condizioni d'uso di
Amazon vietano robot e strumenti di raccolta dati, e la raccolta di schede,
descrizioni e prezzi: il rischio è l'account dell'autore, lo stesso di KDP.
Quindi:

- **non apri nessun sito di Amazon**: né amazon.com, né il servizio di
  autocompletamento (completion.amazon.com), né kdp.amazon.com, nemmeno per
  leggere; le bozze su KDP non si fanno più (la sezione è tolta);
- **non guidi Helium 10, Publisher Rocket, Google Trends**: i loro dati li
  esporta l'autore e li consegna alla fabbrica;
- le pagine di aiuto di KDP e le notizie su Amazon si leggono solo come
  **risultati di ricerca web** o da siti terzi, mai aprendo amazon.com.

Una richiesta scritta prima di questa versione che ti chiede una di queste
cose: rispondi `Esito: parziale — <punti>: vietato dal LEGGIMI 16` e non la
fai.

**Novità della versione 15: nelle bozze su KDP i file li allega l'autore.**
(Superata dalla versione 16: le bozze su KDP non si fanno più.)
Al primo giro il browser si è bloccato su KDP. Ora: prima si controlla che il
Bookshelf si veda, e se no ci si ferma e si scrive che cosa si vede; ai campi
di caricamento si chiede all'autore di trascinare il file e si aspetta; se un
passo non va, si salva la bozza e ci si ferma su quel passo.

**Versione 14** (le bozze su KDP) è superata dalla 16. Resta: le routine della
fabbrica sono spente per scelta dell'autore; se una richiesta dice di non
lanciare `fire_trigger`, la risposta intera va nell'ultimo messaggio del giro,
e la porta l'autore.

**Novità della versione 13: Google Drive non si usa più.** L'autore ha deciso
che i file si salvano in un posto solo, GitHub. Su GitHub Cowork continua a non
scrivere (versione 11): la risposta la **consegni come testo**, lanciando la
routine della fabbrica con `fire_trigger`, e la fabbrica la salva nel
repository, accanto alla richiesta. Nella cartella Drive del corriere non si
scrive più niente e non si legge più niente, nemmeno questo LEGGIMI: vale
quello sul ramo. Se il prompt della tua attività dice di scrivere su Drive con
`create_file`, vale questo file.

Restano: si legge solo con WebFetch (versione 12), su GitHub non si scrive
(versione 11), gli esiti dei giri non riusciti (versione 9), i giri lanciati
dalla fabbrica (versione 8).

## Dove si lavora

- **Le richieste** stanno su GitHub, repository `Personal-lHUb/NEXTUP`, ramo
  `claude/dreamy-archimedes-hf8w45`. L'indice di quelle aperte è
  https://raw.githubusercontent.com/Personal-lHUb/NEXTUP/claude/dreamy-archimedes-hf8w45/kdp-book-factory/config/cowork-aperte.md
  e la fabbrica lo riscrive a ogni giro. Per ogni richiesta l'indice dà
  l'indirizzo per leggerla («leggi»), la prima riga della consegna
  («consegna») e se si fa nel cloud o solo col browser del portatile.
- **Le risposte** si consegnano con `fire_trigger` alla routine della fabbrica,
  trigger_id `trig_014uG5o2CZ22kwnBS5FDxty7` (sezione «Come si consegna»). Non
  si scrivono file da nessuna parte: né su GitHub, né su Google Drive, né sul
  portatile.
- Se il prompt della tua attività parla di Drive, di `create_file`, di
  `add_repo`, di git, di commit dal browser o di base64, vale questo file.

## Che cosa c'è da fare

- Le richieste del tuo ruolo che l'indice elenca sotto «Ruolo <il tuo ruolo>».
  Una richiesta di un altro ruolo è di un'altra chat: non aprirla. Una
  richiesta senza ruolo non la prende nessuno: se la trovi, dillo all'autore e
  lasciala lì.
- L'indice elenca solo le richieste ancora senza risposta: una richiesta che ne
  esce ha la sua risposta su GitHub. Una richiesta consegnata in questo giro
  non si consegna una seconda volta. Se un giro dopo l'indice la dà ancora, la
  consegna non è arrivata: rifalla.
- Una richiesta con la riga `Serve: …` sotto il ruolo chiede un accesso che
  apre l'autore (KDP, ChatGPT, Helium 10, Amazon, il browser del portatile).
  Prima di tutto guarda se c'è. Se manca, salta la richiesta senza consegnare
  niente: al giro dopo la ritrovi aperta. Se c'è, la fai come le altre.
- Una richiesta scritta prima di questa versione può dire di rispondere su
  Drive, con git, col browser su GitHub o altrove: consegna come dice questo
  file, con la prima riga che l'indice dà.

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
4. Consegnala come dice la sezione «Come si consegna».
5. Se la richiesta chiede immagini, non caricarle da nessuna parte: scrivi
   nella risposta dove sono (indirizzo, chat di ChatGPT), con misure in pixel e
   peso. A portarle nel libro ci pensano la fabbrica o l'autore.

## Come si consegna

Ogni risposta è un lancio di `fire_trigger`:

- `trigger_id`: `trig_014uG5o2CZ22kwnBS5FDxty7` (la routine della fabbrica);
- `text`: sulla prima riga la consegna che l'indice dà per quella richiesta,
  lettera per lettera, per esempio

      Cowork · risposta · kdp-book-factory/books/x/concorrente/cowork-concorrente-risposta.md

  e dalla riga dopo la risposta intera, cominciando da `Esito: …`.

Una consegna per risposta. Il testo porta al massimo 64 KiB: una risposta oltre
50.000 caratteri si divide fra una riga e l'altra in parti, e ogni parte ha la
stessa prima riga seguita da ` · parte N/M` (per esempio `… -risposta.md ·
parte 1/3`). La fabbrica le ricuce quando sono arrivate tutte.

La fabbrica riceve la consegna, la salva su GitHub accanto alla richiesta e la
toglie dall'indice entro il giro. Rifiuta da sola tutto quello che non è la
risposta di una richiesta aperta: non serve controllarlo tu.

**Se `fire_trigger` non c'è** fra i tuoi strumenti, non cercare altre strade:
scrivi le consegne intere, ognuna con la sua prima riga, come ultimo messaggio
del giro, e in fondo la riga `Consegna non riuscita: manca fire_trigger`. Non
le salvi da nessuna parte: le porta l'autore.

## Leggere

Con WebFetch dagli indirizzi «leggi» dell'indice, e solo con WebFetch: è il
primo strumento da usare, non un ripiego. Non usare `curl`, `wget`, git o `gh`
dalla shell: la modalità automatica li nega, e dopo un rifiuto non si riprova
con un altro strumento. Non servono credenziali: il repository è pubblico. Se
un indirizzo non si apre, scrivi l'esito (sezione «Se qualcosa non va»). Il
browser del portatile serve per il lavoro del tuo ruolo (Amazon, KDP, YouTube,
ChatGPT), non per GitHub.

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

## Se qualcosa non va

Se in questo giro c'era una richiesta del tuo ruolo da fare e un passo tecnico
non è riuscito — un indirizzo che non si apre, un download bloccato, il browser
che non risponde, un permesso negato, un passo di questo LEGGIMI che non torna
— consegna l'esito come una risposta, con `fire_trigger` alla routine della
fabbrica:

- prima riga `Cowork · esito · <ruolo>` (per esempio `Cowork · esito · fonti`);
- poi `Esito: non riuscito` e l'ora UTC del giro;
- poi, per ogni passo che non è andato: che cosa volevi fare, il comando o lo
  strumento usato, il messaggio d'errore **esatto**, copiato;
- infine che cosa sei riuscito a consegnare, se qualcosa.

Un permesso negato non si aggira: si consegna l'esito e ci si ferma. Un giro
senza richieste da fare, o in cui tutto è andato, non consegna nessun esito.

## Che cosa non si fa

- Su GitHub non si scrive niente: né con git, né dal browser, né file, né
  commit, né pull request, né impostazioni.
- Google Drive non si usa più: né per scrivere, né per leggere. La cartella del
  corriere resta com'è: non si modifica e non si cancella niente.
- Una risposta consegnata non si cambia. Se alla fabbrica serve altro, apre
  una richiesta nuova.
- Su kdp.amazon.com e completion.amazon.com non si apre niente; su amazon.com
  solo per leggere i link o gli ASIN che l'autore allega, mai per scrivere
  (versione 17).
- Helium 10, Publisher Rocket e Google Trends non li guidi tu: i dati li
  esporta l'autore (versione 16).
- Negli strumenti a pagamento (Helium 10, Publisher Rocket, ChatGPT) si usa
  solo l'accesso che l'autore ha già aperto nel browser: non si inseriscono
  credenziali, non si compra, non si cambiano abbonamenti né impostazioni.
- Nessuna password, codice, token o cookie nei file.
- Un permesso negato dalla modalità automatica non si aggira con un'altra
  strada: si scrive l'esito.
- `fire_trigger` si usa solo per la routine della fabbrica, per consegnare
  risposte ed esiti. Nessun'altra attività si lancia, si crea, si cambia o si
  cancella.

## Richieste di seguito e ritirate

`…-2.md`, `…-3.md` sono seguiti di una richiesta già fatta: contengono solo i
punti rimasti aperti, o la versione corretta di una domanda. Una richiesta che
sparisce dall'indice è applicata o ritirata: non si risponde a una copia
vecchia.

Se non ci sono richieste del tuo ruolo da fare, il giro finisce senza
consegnare niente.

## I ruoli

Ogni ruolo ha la sua chat nel progetto e la sua attività pianificata, ogni ora.
Il testo per crearle è in `kdp-book-factory/config/progetto-cowork.md`.

### Ruolo concorrente

Il libro concorrente: le pagine di amazon.com che l'autore allega (solo per
leggere, versione 17), siti di librerie e di editori, Goodreads, Google Books,
ricerca web.

- Le **recensioni si copiano alla lettera**, con stelle, titolo, data e sito
  da cui vengono. Non si riassumono: la fabbrica cita le parole esatte.
- Classifica, categorie e prezzo si leggono dalla pagina Amazon allegata; i
  vicini di scaffale e quello che la pagina non mostra si segnano come non
  disponibili. Se l'autore incolla lui la pagina nella richiesta, si usa quella.

### Ruolo parole-chiave

Le parole chiave e le categorie, **senza Amazon e senza guidare strumenti a
pagamento** (versione 16).

- Le esportazioni di **Helium 10**, **Publisher Rocket** e **Google Trends**
  le fa l'autore e le allega alla richiesta: tu le leggi e ne ricavi la
  tabella. Se mancano, quelle colonne restano vuote e la risposta è parziale.
- Ricerca web su siti terzi per capire come i lettori chiamano il tema.
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
categorie, contenuti. **Solo dalla ricerca web** (i risultati che citano le
pagine di aiuto di KDP, e siti terzi): kdp.amazon.com non si apre, nemmeno
per leggere (versione 16). Ogni regola con la fonte e la data in cui è stata
vista; se la fonte non è ufficiale, lo si scrive.

### Ruolo immagini

Le illustrazioni di copertina e le figure dell'interno le genera la fabbrica
con Higgsfield. Al ruolo restano le richieste di **ChatGPT** e di analisi
(video, copertine da studiare), col browser del portatile: le richieste hanno
la riga `Serve:`. Le immagini non si caricano da nessuna parte (sezione «Come
si risponde», punto 5).

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
- Si generano tante varianti quante la richiesta ne chiede; la risposta dice
  dove sono e quanto misurano. Non si caricano da nessuna parte.
- Le figure dell'interno sono in **scala di grigi**: due elementi non si
  distinguono solo per il colore.
- Solo immagini generate nella sessione o già generate dalla fabbrica: mai
  prese dal web, mai persone reali riconoscibili, mai marchi, loghi o
  personaggi di altri.
- Nella risposta si scrive con quale strumento e modello sono state generate:
  KDP chiede di dichiarare i contenuti generati con l'IA.

# LEGGIMI — regole del canale con Cowork

Versione 3 · 1° ottobre 2026 · scritto dalla fabbrica di libri NEXTUP.

Queste regole valgono per ogni giro di Cowork. Se dicono una cosa diversa dal
prompt dell'attività pianificata, vale questo file: lo tiene aggiornato la
fabbrica, e ogni modifica porta un numero di versione nuovo.

**Novità della versione 3: i ruoli.** Cowork lavora in un progetto con una chat
e un'attività pianificata per ruolo: `concorrente`, `parole-chiave`, `fonti`,
`regole-kdp`. Ogni richiesta dice il suo ruolo nella riga `Ruolo: …` sotto il
titolo, e ogni ruolo prende solo le sue. Le regole comuni sono qui sotto; quelle
di ciascun ruolo sono nella sua sezione, in fondo.

Versione 2: il canale è GitHub. La casella su Google Drive «NEXTUP —
libri/cowork» è chiusa; lì non si risponde più.

## Dove si lavora

- Repository `Personal-lHUb/NEXTUP`, ramo `claude/dreamy-archimedes-hf8w45`.
  Su un altro ramo le richieste non ci sono o sono vecchie.
- Se lavori sulla copia locale, prima di ogni giro aggiornala dal ramo remoto
  (Fetch e Pull in GitHub Desktop). Se non puoi farlo tu, chiedilo all'autore.
  Una copia vecchia fa rispondere a domande superate.

## Che cosa c'è da fare

- **Richieste**: file `cowork-<argomento>.md`, nella cartella del libro a cui
  servono o in `kdp-book-factory/config/` per le regole comuni. L'elenco delle
  cartelle è in `RICERCA-WEB.md`, alla radice del repository.
- **Risposte**: accanto alla richiesta, stesso nome con `-risposta` prima di
  `.md`. Per esempio la risposta a
  `kdp-book-factory/books/household-bills/manuale/cowork-amazon.md` è
  `kdp-book-factory/books/household-bills/manuale/cowork-amazon-risposta.md`.
- Una richiesta con accanto la sua risposta è fatta: saltala.
- Una richiesta che contiene la riga `Stato: applicata` è chiusa: saltala.
- Una richiesta con un ruolo diverso dal tuo è di un'altra chat: non aprirla.
  Una richiesta senza la riga `Ruolo:` non la prende nessun ruolo: se la
  trovi, dillo all'autore e lasciala lì.

## Come si risponde

1. Leggi la richiesta per intero ed esegui quello che chiede, punto per punto,
   con la sua numerazione.
2. Scrivi la risposta in Markdown, nel file indicato.
3. La **prima riga** della risposta dice com'è andata:
   - `Esito: completa`
   - `Esito: parziale — punti 2, 4: <motivo>` (captcha, accesso, pagina che non
     c'è più, dato che non si trova)
4. Per ogni punto: il fatto che hai visto sulla pagina, non una stima, con
   l'URL e la data e l'ora della verifica.
5. Fai il commit della sola risposta sul ramo `claude/dreamy-archimedes-hf8w45`,
   con un messaggio come «Cowork: risposta a cowork-amazon». Poi il push:
   - se hai accesso diretto a GitHub, lo fai tu;
   - se no, lo fa l'autore da GitHub Desktop.

## Che cosa non si fa

- Nel repository si scrivono solo i file di risposta. Non si modificano le
  richieste, questo LEGGIMI, codice, `book.json`, manoscritto, documenti o
  agenti.
- Una risposta già scritta non si riscrive. Se alla fabbrica serve altro, apre
  una richiesta nuova.
- Su KDP (kdp.amazon.com) si legge e basta: niente titoli nuovi, bozze,
  pubblicazioni o impostazioni cambiate.
- Negli strumenti a pagamento (Helium 10, Publisher Rocket) si usa solo
  l'accesso che l'autore ha già aperto nel browser: non si inseriscono
  credenziali, non si compra, non si cambiano abbonamenti né impostazioni.
- Nessuna password, codice, token o cookie nei file o nei commit.

## Richieste di seguito

`cowork-<argomento>-2.md`, `-3.md` sono seguiti di una richiesta già fatta.
Contengono solo i punti rimasti aperti, oppure la versione corretta di una
domanda. Rispondi solo a quello che chiedono, nel loro file di risposta
(`…-2-risposta.md`).

## Richieste ritirate

Una richiesta cancellata dal ramo è ritirata: non si risponde a una copia
vecchia.

Se non ci sono richieste senza risposta, il giro finisce senza scrivere niente.

## I ruoli

Ogni ruolo ha la sua chat nel progetto e la sua attività pianificata. Il testo
per crearle è in `kdp-book-factory/config/progetto-cowork.md`.

### Ruolo concorrente

Le pagine Amazon dei libri concorrenti: scheda, classifica, descrizione,
indice, recensioni, copertina in miniatura, vicini di scaffale, prezzi.

- Le **recensioni si copiano alla lettera**, con stelle, titolo e data. Non si
  riassumono: la fabbrica cita le parole esatte, e un riassunto non si cita.
- Se l'ASIN apre un'edizione Audible o Kindle, si passa al **cartaceo** dal
  selettore dei formati: pagine e classifica in Books stanno lì.
- Prezzi nella valuta del mercato: si imposta l'indirizzo di consegna che la
  richiesta indica e alla fine si rimette com'era.

### Ruolo parole-chiave

Le parole chiave e le categorie: che cosa digitano i lettori e quanto sono
affollati gli scaffali.

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

Le affermazioni del libro sul mondo, prima della stampa.

- Solo **fonti ufficiali**: il sito dell'ente, della legge, del programma.
  Un articolo di giornale o un blog non bastano: si scrive «non trovato».
- Per ogni punto: **vero**, **cambiato** o **non trovato**, con l'URL e la
  frase esatta che lo conferma o lo smentisce.
- Il manoscritto non si tocca: le correzioni le fa la fabbrica.

### Ruolo regole-kdp

Le regole di KDP che valgono per ogni libro: costi di stampa, limiti, pagine,
selettore delle categorie.

- Su KDP **si legge e basta**. Nel flusso di un titolo nuovo si guarda e si
  esce senza salvare: niente bozze.
- Se serve l'accesso a KDP e nel browser non è aperto, la risposta è parziale
  con quel motivo: l'accesso lo apre l'autore, non tu.
- La fonte preferita è la guida ufficiale di KDP (kdp.amazon.com/help); il
  calcolatore dei costi va citato con le cifre che mostra.


# LEGGIMI — regole del canale con Cowork

Versione 4 · 5 ottobre 2026 · scritto dalla fabbrica di libri NEXTUP.

Queste regole valgono per ogni giro di Cowork. Se dicono una cosa diversa dal
prompt dell'attività pianificata, vale questo file: lo tiene aggiornato la
fabbrica, e ogni modifica porta un numero di versione nuovo.

**Novità della versione 4: il corriere su Drive.** Si lavora solo nella
cartella di Google Drive «NEXTUP — corriere Cowork». Niente più GitHub, niente
GitHub Desktop, niente Pull né push: i file fra la cartella e il repository li
porta la fabbrica, ogni ora. C'è un ruolo nuovo, `immagini`.

## Dove si lavora

- Cartella Google Drive **«NEXTUP — corriere Cowork»**, id
  `1yprHuxzFDGj12k8clTp0othzTXjiyn5N`. Le richieste, questo LEGGIMI
  (`config__leggimi-cowork.md`) e il testo del progetto
  (`config__progetto-cowork.md`) li trovi lì.
- Ogni file si chiama come il suo posto nell'archivio della fabbrica, con `__`
  al posto di `/`. La risposta a
  `books__x__concorrente__cowork-concorrente.md` si chiama
  `books__x__concorrente__cowork-concorrente-risposta.md`. Il nome giusto lo
  scrive sempre la richiesta: usa quello, lettera per lettera.

## Che cosa c'è da fare

- **Richieste**: i file della cartella che contengono `cowork-` nel nome,
  finiscono in `.md` e non finiscono in `-risposta.md`.
- Ogni richiesta dice il suo ruolo nella riga `Ruolo: …` sotto il titolo. Una
  richiesta di un ruolo diverso dal tuo è di un'altra chat: non aprirla. Una
  richiesta senza la riga `Ruolo:` non la prende nessun ruolo: se la trovi,
  dillo all'autore e lasciala lì.
- Una richiesta che ha già accanto il file con lo stesso nome e `-risposta` è
  fatta: saltala.

## Come si risponde

1. Leggi la richiesta per intero ed esegui quello che chiede, punto per punto,
   con la sua numerazione. Tutto quello che ti serve è nella richiesta: se
   manca qualcosa, scrivilo nella risposta invece di cercarlo altrove.
2. Scrivi la risposta in Markdown, come **file nuovo** nella cartella, con il
   nome che la richiesta indica.
3. La **prima riga** della risposta dice com'è andata:
   - `Esito: completa`
   - `Esito: parziale — punti 2, 4: <motivo>` (captcha, accesso, pagina che non
     c'è più, dato che non si trova, strumento non accessibile)
4. Per ogni punto: il fatto che hai visto sulla pagina, non una stima, con
   l'URL e la data e l'ora della verifica.
5. Le immagini che una richiesta chiede vanno nella cartella, ognuna con il nome
   che la richiesta indica.

## Che cosa non si fa

- Nella cartella si creano solo file nuovi: le risposte e le immagini chieste.
  Non si modificano, rinominano o cancellano file che non hai creato tu, né le
  richieste, né questo LEGGIMI.
- Una risposta già scritta non si riscrive. Se alla fabbrica serve altro, apre
  una richiesta nuova.
- Su KDP (kdp.amazon.com) si legge e basta: niente titoli nuovi, bozze,
  pubblicazioni o impostazioni cambiate.
- Negli strumenti a pagamento (Helium 10, Publisher Rocket, ChatGPT) si usa
  solo l'accesso che l'autore ha già aperto nel browser: non si inseriscono
  credenziali, non si compra, non si cambiano abbonamenti né impostazioni.
- Nessuna password, codice, token o cookie nei file.

## Richieste di seguito e ritirate

`…-2.md`, `…-3.md` sono seguiti di una richiesta già fatta: contengono solo i
punti rimasti aperti, o la versione corretta di una domanda. Una richiesta che
sparisce dalla cartella è ritirata: non si risponde a una copia vecchia.

Se non ci sono richieste del tuo ruolo senza risposta, il giro finisce senza
scrivere niente.

## I ruoli

Ogni ruolo ha la sua chat nel progetto e la sua attività pianificata, ogni ora.
Il testo per crearle è in `config__progetto-cowork.md`.

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

- La richiesta cita la frase esatta del libro: si verifica quella.
- Solo **fonti ufficiali**: il sito dell'ente, della legge, del programma.
  Un articolo di giornale o un blog non bastano: si scrive «non trovato».
- Per ogni punto: **vero**, **cambiato** o **non trovato**, con l'URL e la
  frase esatta che lo conferma o lo smentisce.

### Ruolo regole-kdp

Le regole di KDP che valgono per ogni libro: costi di stampa, limiti, pagine,
selettore delle categorie.

- Su KDP **si legge e basta**. Nel flusso di un titolo nuovo si guarda e si
  esce senza salvare: niente bozze.
- Se serve l'accesso a KDP e nel browser non è aperto, la risposta è parziale
  con quel motivo: l'accesso lo apre l'autore, non tu.
- La fonte preferita è la guida ufficiale di KDP (kdp.amazon.com/help); il
  calcolatore dei costi va citato con le cifre che mostra.

### Ruolo immagini

Le illustrazioni di copertina e le figure dell'interno, con **ChatGPT**.

- Il prompt è nella richiesta, scritto dalla fabbrica: si incolla **così com'è**,
  senza aggiungere né togliere. Non si scrive un prompt proprio.
- **Nessun testo nell'immagine**: niente titoli, lettere, numeri, firme. Il
  titolo lo compone la fabbrica, in vettoriale, dopo.
- Formato verticale, nella proporzione che la richiesta indica, alla
  risoluzione più alta che lo strumento consente. Si riportano le misure in
  pixel di ogni immagine consegnata. Se la richiesta indica un minimo e
  l'immagine è più piccola, si consegna lo stesso e lo si scrive: decide la
  fabbrica.
- Si generano tante varianti quante la richiesta ne chiede, ognuna salvata nella
  cartella con il nome indicato.
- Le figure dell'interno sono in **scala di grigi**: due elementi non si
  distinguono solo per il colore.
- Solo immagini generate nella sessione: mai prese dal web, mai persone reali
  riconoscibili, mai marchi, loghi o personaggi di altri.
- Nella risposta si scrive con quale strumento e modello sono state generate:
  KDP chiede di dichiarare i contenuti generati con l'IA.

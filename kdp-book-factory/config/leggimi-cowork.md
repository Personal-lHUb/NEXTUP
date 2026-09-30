# LEGGIMI — regole del canale con Cowork

Versione 2 · 30 settembre 2026 · scritto dalla fabbrica di libri NEXTUP.

Queste regole valgono per ogni giro di Cowork. Se dicono una cosa diversa dal
prompt dell'attività pianificata, vale questo file: lo tiene aggiornato la
fabbrica, e ogni modifica porta un numero di versione nuovo.

**Novità della versione 2: il canale è GitHub.** La casella su Google Drive
«NEXTUP — libri/cowork» è chiusa. Lì non si risponde più.

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

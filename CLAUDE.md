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
- Il testo dei libri e la documentazione del progetto sono in italiano.

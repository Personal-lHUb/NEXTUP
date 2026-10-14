# Stato della fabbrica

Aggiornato il 14 ottobre 2026 (sera). Si aggiorna alla fine di ogni sessione: chi apre la
sessione dopo parte da qui.

## Il libro in corso

**Nessuno.** Si aspetta dall'autore un **nuovo ASIN**, di un tema ammesso.

- **`b0gjr36xwt` eliminato il 14 ottobre**, su decisione dell'autore: *Hard
  Calls, Clear Notes* (documentazione clinica per nurse practitioner) era
  arrivato al pacchetto per KDP, ma è un tema di salute e diritto, ora esclusi.
  Tolto da `books/` e da `config/produzione.json`; resta nella storia di git
  (ultimo commit col libro: `9a1fcd0`) e in `backup/manuale/20261014-115012/`
  (solo su questo disco). Le 45 unità di credito Higgsfield delle varianti
  finali sono spese.
- **Rischi legali** (`kdp-book-factory/docs/rischi-legali.md`, 14 ottobre):
  temi esclusi salute, diritto, finanza, psicologia (regola 12 di CLAUDE.md);
  frase sull'IA veritiera nel colophon; mai il concorrente nel libro; Cowork
  fuori dai siti di Amazon; su KDP carica l'autore. Fisco (royalty di libri
  scritti con l'IA, partita IVA, W-8BEN) e GPSR: dal commercialista.
- **Da fare per il prossimo libro**: prima di qualunque agente,
  `python3 -m kdpfactory temi --testo "<titolo del concorrente>" --categoria
  "<sue categorie>"`. Se tocca un tema escluso, si chiede un altro ASIN.
- **Repository**: l'autore rende privato `NEXTUP` (vedi «In sospeso»).

## Contesto (10 ottobre, scelta dell'autore)

- Hook in `.claude/settings.json` (`kdpfactory/diario.py`): prompt di ogni
  agente in `books/<slug>/prompt/`, diario in `books/<slug>/diario.md`
  (lancio, id, fine, consegne importate, decisioni), risposte lunghe salvate in
  `consegne/`, guardia che lascia scrivere agli agenti solo lì. All'avvio e dopo
  ogni riassunto della chat tornano in contesto STATO.md, produzione, agenti in
  volo, consegne da importare e la coda del diario.
- Gli agenti che usano il modello hanno `Write` (solo per la consegna) e
  rispondono con una riga: la chat non si riempie di capitoli.

## Automazioni e consenso (10 ottobre, decisioni dell'autore)

- **Ogni passo lo fa partire l'autore.** Fra un suo messaggio e l'altro non
  parte niente (nemmeno i bozzetti di copertina); il compito che dà si chiude
  con commit e push, poi ci si ferma e gli si dice il passo dopo.
- **Niente si programma**: nessun `send_later`, nessuna routine, nessun lancio
  di Cowork. Le routine restano spente, non si cancellano. Un limite d'uso
  si annota nel diario, e si aspetta il suo «continua».
- **Silenzio-assenso spento**: ogni decisione d'autore aspetta la sua risposta,
  senza scadenza. In attesa ora: **prezzo** (21,99 USD, alternativa 19,99) e
  **formato** (6×9 proposto).
- Gli hook del contesto restano: registrano e rimettono in contesto, non
  avviano lavoro. Quando qualcosa aspetta l'autore: riga in chat e notifica push.
- Stamattina (10 ottobre) le cinque routine di Cowork risultano partite fra le
  08:05 e le 08:45 UTC e «Produzione NEXTUP» lanciata alle 08:55, poi di nuovo
  spente; questa sessione non le ha accese.
- Il prompt della routine «Produzione NEXTUP» parla ancora di silenzio-assenso
  e di lanci di Cowork: se l'autore la vuole riaccesa, prima va riscritto.

## Routine e Cowork

- **Tutte le routine sono spente** (8 ottobre, su richiesta dell'autore): la
  fabbrica «Produzione NEXTUP» e le cinque attività di Cowork. Si riaccendono
  solo col consenso dell'autore.
- **Cowork non apre i siti di Amazon** (LEGGIMI versione 16, 14 ottobre) e non
  guida Helium 10, Publisher Rocket, Google Trends: i ruoli `concorrente`,
  `parole-chiave`, `regole-kdp` lavorano sulla ricerca web e sulle
  esportazioni dell'autore. Le bozze su KDP non si fanno più. `config/cowork-kdp-3.md`
  ritirata. Nessuna richiesta aperta.
- Le attività di Cowork sul portatile hanno ancora il prompt vecchio: prima di
  riaccenderle, l'autore approva i prompt di `kdp-book-factory/config/attivita-cowork.json`.

## In sospeso, non bloccante

- **`NEXTUP` diventa privato** (scelta dell'autore, 14 ottobre): lo fa lui da
  GitHub (Settings → General → Danger Zone → Change visibility → Private), così
  nessun testo resta pubblico, storia e altri rami compresi. Dopo, Cowork non
  legge più i link `raw.githubusercontent.com`: i file glieli porta l'autore.
  Da verificare alla sessione dopo che il repository risulti privato.
- **CDN di Higgsfield bloccata** dalla rete del container (403): le immagini
  generate le carica l'autore sul ramo `cowork-immagini` e
  `copertina --scarica-generate` le prende da lì.
- I cinque libri precedenti sono stati eliminati il 7 ottobre su richiesta
  dell'autore: copie in `backup/manuale/20261007-143226/` (solo su questo disco) e
  nella storia di git.

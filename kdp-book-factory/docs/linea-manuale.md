# La linea manuale: la fabbrica senza chiave API

Metà di questo sistema non ha mai chiamato il modello. L'impaginazione misura,
la copertina disegna e verifica, il controllo qualità conta, la scheda calcola
prezzi e royalty, la taratura delle pagine impagina libri di prova. L'altra
metà — scaletta, capitoli, scheda prodotto — è scrittura, e per quella serve un
modello.

Senza credenziale si fermava tutto. Non è giusto: si ferma solo la scrittura.

La linea manuale fa lavorare le due metà separate, con lo stesso meccanismo che
il sistema usa già per le copertine: **non si disegna, si scrive il brief.**

```
python3 -m kdpfactory manuale <slug> stato        # che cosa c'è e che cosa manca
python3 -m kdpfactory manuale <slug> scaletta     # produce il brief
python3 -m kdpfactory manuale <slug> scaletta --importa
python3 -m kdpfactory manuale <slug> capitolo --numero 3
python3 -m kdpfactory manuale <slug> capitolo --numero 3 --importa
python3 -m kdpfactory manuale <slug> scheda
python3 -m kdpfactory manuale <slug> scheda --importa
```

Nessuno di questi comandi chiama il modello. Un test lo impedisce: se in
`manuale.py` comparisse un `LLMClient`, fallirebbe.

## Come funziona un passo

1. **Il sistema scrive il brief.** In `books/<slug>/manuale/` compare un file
   `<passo>-brief.md` che contiene *esattamente* il prompt che l'agente avrebbe
   ricevuto: prompt di sistema, regole d'autore, scheda del libro, budget di
   parole, contesto dei capitoli precedenti, contratto di risposta.
2. **Tu porti quel testo dove vuoi.** Un modello qualunque, una conversazione,
   o la tua testa: il brief non presuppone chi risponde.
3. **Incolli la risposta** nel file che il comando ti indica —
   `manuale/scaletta.json`, `manuale/capitolo-03.md`, `manuale/scheda.json`.
4. **Il sistema la valida e la importa** con `--importa`. Una scaletta senza
   capitoli, un capitolo senza titolo, una scheda a cui mancano le parole
   chiave: vengono rifiutati con il motivo, non ingoiati.

Da lì in poi il libro è un libro come gli altri: `build` impagina, la copertina
si disegna e si misura, `qa` controlla, la scheda calcola i prezzi.

## Che cosa cambia rispetto alla linea automatica

| | automatica | manuale |
|---|---|---|
| scaletta | l'agente la scrive, l'agente `indice` rifà i titoli | la scrivi tu; **i titoli che metti sono definitivi** |
| contesto fra capitoli | riassunti scritti dal modello dopo ogni capitolo | i riassunti della scaletta: più poveri, ma veri e gratis |
| collegio di revisione | lettore cieco, fact-checker, conformità, editor | fermi (usano il modello) |
| impaginazione, copertina | girano | girano, identici |
| `qa`, prezzi, EPUB, brief di copertina | girano | girano, identici |
| costo | fra $7 e $8 stimati a libro | zero |

Il libro che esce è lo stesso: stessi file, stessi controlli, stesso PDF. Un
test lo verifica confrontando la scaletta normalizzata dalle due strade — la
normalizzazione vive in un posto solo (`writer.normalize_outline`), e quel test
fallisce il giorno in cui qualcuno la duplica.

## Che cosa il sistema controlla su quello che incolli

**Scaletta** — JSON valido, almeno un capitolo, nessun capitolo senza titolo.
Poi numera le sezioni, aggiunge introduzione e conclusione se `book.json` le
prevede, e ripartisce il budget di parole calcolato sulle pagine vere.

**Capitolo** — non vuoto, e comincia dal titolo della scaletta (se non c'è, ce
lo mette). Conta le parole e le confronta con il budget: oltre il 25% di scarto
lo dice, perché è lì che il conteggio pagine comincia a sbagliare. Non blocca:
un capitolo lungo si accorcia, e `build` lo farà notare comunque.

**Scheda** — JSON valido, e ci devono essere i campi che il pannello KDP
pretende: titolo, sottotitolo, descrizione, parole chiave, categorie.

## Dove finiscono i file

```
books/<slug>/manuale/
    scaletta-brief.md        prodotto dal sistema
    scaletta.json            incollato da te
    capitolo-03-brief.md
    capitolo-03.md
    scheda-brief.md
    scheda.json
```

I brief e le risposte restano lì: sono la traccia di come il libro è stato
scritto, e servono a rifare un capitolo senza ricostruire il contesto a mano.

## Quando usarla anche con la chiave

- Per **scrivere un capitolo a mano** e lasciare che il resto del libro lo
  scriva il modello: le due strade convivono sullo stesso libro, perché il
  manoscritto è lo stesso `manuscript/NN.md`.
- Per **vedere il prompt vero** prima di spenderci sopra: il brief è il testo
  esatto che l'agente riceverebbe.
- Per **rifare un solo capitolo** senza far ripartire il collegio.

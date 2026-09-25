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
python3 -m kdpfactory manuale <slug> scaletta --esamina
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
| scaletta | l'agente la scrive, l'agente `indice` rifà i titoli | la scrivi tu; l'agente `indice` di Claude Code rifà i titoli se lo chiami («usa indice su books/<slug>/manuale/scaletta.json»), prima di `--esamina` |
| controllo della scaletta | `revisore-scaletta`, che non usa il modello | lo stesso, identico |
| contesto fra capitoli | riassunti scritti dal modello dopo ogni capitolo | i riassunti della scaletta: più poveri, ma veri e gratis |
| collegio di revisione | lettore cieco, fact-checker, conformità, editor | fermi nella pipeline; da Claude Code girano come subagent, uno per competenza ([`linee-guida.md`](linee-guida.md)) |
| impaginazione, copertina | girano | girano, identici |
| `qa`, prezzi, EPUB, brief di copertina | girano | girano, identici |
| costo | fra $7 e $8 stimati a libro | zero |

### I comandi che si fermavano per niente

Tre comandi chiedevano la credenziale perché *potevano* usare il modello, non
perché dovessero. Adesso:

- **`build`** senza chiave impagina lo stesso e lo dice. La riscrittura dei
  capitoli per far tornare le pagine è un di più: se le pagine non rientrano,
  il comando lo scrive e decidi tu che cosa tagliare. Rifiutarsi di stampare un
  libro già scritto non serviva a nessuno.
- **`review --agents impaginazione,copertina`** gira senza credenziale: quei
  due agenti misurano. Il client si costruisce solo se fra gli agenti chiesti
  ce n'è almeno uno che parla col modello (`Agent.deterministico`).
- **la scheda incollata** produce la descrizione HTML. Si costruiva solo dentro
  `generate_metadata`, cioè solo sulla linea automatica: la scheda scritta a
  mano usciva con **0 caratteri su 4000** nel campo che il cliente legge per
  primo. Adesso la costruisce `write_metadata_files`, da cui passano tutte e
  due le linee, e l'etichetta dell'elenco segue la lingua del libro invece di
  restare in italiano su una pagina di amazon.com.

Il libro che esce è lo stesso: stessi file, stessi controlli, stesso PDF. Un
test lo verifica confrontando la scaletta normalizzata dalle due strade — la
normalizzazione vive in un posto solo (`writer.normalize_outline`), e quel test
fallisce il giorno in cui qualcuno la duplica.

## Il revisore di scaletta

Un capitolo scritto male si riscrive. Una scaletta sbagliata si paga trenta
volte, perché ogni capitolo eredita il difetto: due capitoli che dicono la
stessa cosa diventano tremila parole ripetute, un argomento chiesto in
`brief.md` e dimenticato nella scaletta non comparirà mai nel libro.

Perciò la scaletta non entra da sola. Prima passa dall'agente
`revisore-scaletta`, che **non usa il modello**: tutto quello che segnala si
conta.

| controllo | che cosa misura | gravità |
|---|---|---|
| conteggio | i capitoli di contenuto contro quelli che il budget pagine ha pagato | bloccante |
| lingua | parole grammaticali italiane contro inglesi, rispetto a `language` | bloccante |
| argomento scoperto | ogni punto elenco di `brief.md` deve avere un capitolo che lo prende | bloccante |
| promessa di risultato | guarigione, cura, garanzia — negazioni e citazioni escluse | bloccante |
| sovrapposizione | parole in comune fra due capitoli: oltre il 45% fanno lo stesso capitolo | bloccante / importante |
| titolo doppio, titolo generico | l'indice è la pagina che si legge nell'anteprima | bloccante / importante |
| capitolo senza programma | riassunto e punti: chi scrive deve sapere dove finisce | importante |
| data in scaletta | un anno scritto per esteso va detto come parola di chi parla | importante |
| titolo in copertina | le stesse misure dell'audit di copertina, applicate qui | importante |
| quarta, progressione | gancio più due paragrafi; la parte operativa nell'ultimo terzo | minore |
| cifre da contare | elenca ogni quantità dichiarata in indice e quarta, da verificare sul libro | minore |
| parti | ogni parte si apre su un capitolo che c'è, in ordine, con almeno due capitoli; oltre i 20 capitoli un indice senza parti lo dice | bloccante / importante / minore |
| titolo su due righe | la larghezza del titolo nel sommario, col carattere, il corpo e la giustezza del PDF | minore |

Due regole che evitano al revisore di bloccare il lavoro fatto bene: una parola
vietata **fra virgolette** è citata, non detta (un capitolo intitolato «le sei
parole che mi rifiuto di usare» non è una rivendicazione), e una **negazione
entro dieci parole** salva la frase («perché non la chiamerò una prova»).

I bloccanti fermano l'importazione. `--forza` li scavalca, e lo si fa solo
sapendo perché.

## Che cosa il sistema controlla su quello che incolli

**Scaletta** — JSON valido, almeno un capitolo, nessun capitolo senza titolo,
poi il revisore qui sopra. Se passa: numera le sezioni, aggiunge introduzione e
conclusione se `book.json` le prevede — **o usa le tue**, se nella scaletta hai
previsto tu una sezione con `"role": "intro"` o `"conclusion"` — e ripartisce
il budget di parole calcolato sulle pagine vere.

**Parti** — facoltative, e utili oltre i venti capitoli: un indice di trenta
righe tutte uguali, nell'anteprima, non dice come è costruito il libro. Si
dichiarano accanto ai capitoli, con il titolo e il numero del primo capitolo
di ciascuna; la parte arriva fino al capitolo prima della successiva.

```json
"parts": [
  {"title": "Testimony, Not History", "first_chapter": 1},
  {"title": "Inside the Room", "first_chapter": 6}
]
```

I numeri sono quelli della tua scaletta: quando il sistema rinumera
(aggiungendo un'introduzione, per esempio), le parti lo seguono. Nell'interno
ogni parte ha la sua pagina, a destra e senza folio, seguita da una bianca;
nell'indice le parti sono il primo livello e i capitoli stanno sotto; l'EPUB
annida i capitoli nella loro parte. Un'introduzione può restare fuori dalle
parti, come una prefazione. Ogni parte costa due pagine: su un libro vicino al
limite del suo intervallo, contale prima.

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

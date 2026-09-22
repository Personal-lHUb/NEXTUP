# Da un ASIN a un libro

Un reparto di quattro agenti che sta **prima** del collegio editoriale. Riceve
la scheda Amazon di un libro che vende già e consegna `book.json` e `brief.md`:
da lì in poi lavora la pipeline di sempre, che non sa e non deve sapere da dove
è arrivata la scheda.

```
scheda Amazon incollata
        │
        ▼
scheda-concorrente ──► analista-recensioni ──► posizionamento ──► originalita
   (dati)                 (il buco)              (il libro)        (il freno)
        │                                                              │
        └──────────────────────► book.json + brief.md ◄────────────────┘
                                          │
                                          ▼
                              architetto → indice → ghostwriter → …
```

## Il principio, prima di tutto il resto

**L'ASIN entra come segnale di mercato, non come testo sorgente.** Il reparto
legge quello che è pubblico sulla pagina — prezzo, categorie, classifica,
descrizione, recensioni — e non legge il libro. Il risultato è un libro
indipendente sullo stesso argomento, non una rielaborazione di quello di
partenza: nessuno possiede un argomento, e quella è ricerca di mercato che fa
qualunque editore.

Due presidi lo rendono vero nel codice, non solo nelle intenzioni:

1. **L'agente `originalita`** verifica il piano *prima* che qualcuno scriva.
   Una segnalazione `bloccante` impedisce la scrittura di `book.json`: il
   comando esce con un errore e non produce niente.
2. **Il `brief.md` non contiene il libro di partenza.** Il titolo del
   concorrente compare solo dentro un commento `<!-- -->`, e `read_brief()`
   toglie i commenti prima che il testo arrivi a qualunque agente. Chi scrive il
   libro non sa che esiste un libro di partenza. C'è un test che lo verifica.

## Perché le recensioni sono il pezzo che vale di più

Chi scrive una recensione a due o tre stelle ha **pagato** il libro, l'ha letto,
e sta scrivendo alla lettera quale libro avrebbe voluto trovare. È l'unico dato
di mercato gratuito e onesto disponibile senza strumenti a pagamento.

Le cinque stelle servono a un'altra cosa: dicono perché quel libro viene
comprato, cioè che cosa il libro nuovo deve **mantenere**. Entrare in una
nicchia ripudiandone le premesse significa uscirne.

Per questo il modulo da riempire chiede per prima cosa le recensioni, e chiede
di aprirle tutte: con meno di cinque in mano l'analista abbassa da sé la
confidenza invece di costruirci sopra un posizionamento.

## Come si usa

Amazon non è raggiungibile dall'ambiente di lavoro (il proxy di rete risponde
`403` alla connessione), quindi la pagina si incolla a mano.

```bash
cd kdp-book-factory

# 1. crea il modulo da riempire
python3 -m kdpfactory concorrente new <slug> --asin B0ABCD1234
```

Apri `books/<slug>/concorrente/pagina.md` e incolla la scheda Amazon così com'è
— menu, banner e suggerimenti vengono scartati da soli. Conta che ci siano, in
ordine di importanza: le recensioni (tutte, non solo le prime), la descrizione
completa, il riquadro «Dettagli prodotto», la riga della classifica con tutte le
categorie, il prezzo con la valuta.

```bash
# 2. il reparto al lavoro
python3 -m kdpfactory concorrente build <slug> --asin B0ABCD1234 --author "Nome Autore"

# prima a vuoto, se vuoi vedere il giro senza spendere token:
python3 -m kdpfactory --dry-run concorrente build <slug>
```

Il comando stampa il libro di partenza, le lacune trovate con le citazioni che
le reggono, il libro proposto e l'esito del controllo di originalità; poi scrive
`book.json`, `brief.md` e `concorrente/acquisizione.json` con tutta l'analisi.

La categoria la sceglie l'agente guardando le recensioni: «mancano gli
esercizi» e «troppo teorico» spingono verso il medium-content, «poco
approfondito» e «volevo capire il perché» verso il full-content.

**Rileggi la scheda e il brief prima di andare avanti.** Il posizionamento è la
decisione più costosa da sbagliare: correggerla adesso costa un file, dopo costa
un manoscritto.

```bash
# 3. da qui è la pipeline di sempre
python3 -m kdpfactory all <slug>
```

Il comando esce con **0** quando la scheda è stata scritta: i bloccanti fermano
da soli la scrittura, dentro `scrivi()`, quindi arrivare in fondo significa che
il libro è pronto. Le segnalazioni non bloccanti vengono contate a schermo, da
rileggere prima di far scrivere il libro — ma non spezzano
`concorrente build && all`, che è la corsa per cui il comando esiste.

## L'indirizzo editoriale

Gli agenti decidono i **dati**: quale lacuna vale, che titolo, quante pagine,
che prezzo, quali parole chiave. Non decidono **che tipo di libro** si vuole
fare dentro quella nicchia: quella è una scelta di chi pubblica, e ha un posto
suo.

```
books/<slug>/concorrente/indicazione.md
```

Se il file c'è, `concorrente build` lo legge e lo passa a `posizionamento` come
**vincolo**, insieme alla scheda e alle lacune; finisce anche in
`acquisizione.json`, così resta scritto su cosa è stato deciso il libro. In
alternativa: `concorrente build <slug> --indicazione "…"`.

Il commento del modulo e i titoli Markdown non vengono letti, come nel brief.
E il vincolo non scavalca i divieti: un'indicazione che chiedesse di nominare
il concorrente o di promettere risultati resta una cosa che non si fa.

Serve quando la nicchia è buona ma il modo in cui la serve il concorrente non
lo è — per esempio quando le recensioni dicono che quel libro inventa i fatti
controllabili, e il libro nuovo deve essere quello che non lo fa.

## I quattro agenti

| agente | che cosa fa | dove sbaglia se sbaglia |
|---|---|---|
| `scheda-concorrente` | dal testo incollato ai campi strutturati: prezzo, pagine, categorie con la classifica, descrizione, recensioni | inventare un numero che nella pagina non c'era. Ha l'ordine esplicito di lasciare vuoto e segnalarlo in `problemi` |
| `analista-recensioni` | il buco di mercato: che cosa i lettori paganti dicono di non aver trovato, chi è il lettore vero, che cosa non va toccato | scambiare una lamentela sulla copia fisica («pagine staccate») per un difetto del contenuto. Le scarta e lo dichiara |
| `posizionamento` | la scheda del libro nuovo: **categoria di prodotto** (full o medium), promessa, lettore, titolo, pagine, prezzo, sette parole chiave, tre categorie, i temi del brief | partire dalla lacuna più interessante invece che dalla più ricorrente |
| `originalita` | verifica che il piano sia un libro indipendente prima che venga scritto | confondere «stesso argomento» con «stesso libro». Nessuno possiede un argomento: il problema è la forma, la sequenza e le parole |

Ogni lacuna dichiarata deve portare **almeno una citazione** presa alla lettera
dalle recensioni. Senza citazione è un'impressione, e non vale.

## Che cosa blocca `originalita`

| gravità | caso |
|---|---|
| `bloccante` | il titolo o il sottotitolo contengono il titolo del libro di partenza o il nome del suo autore |
| `bloccante` | il libro di partenza è nominato in scheda, parole chiave o copertina — sono marchi di terzi e KDP li rifiuta |
| `importante` | i temi proposti ricalcano l'indice dell'altro libro nello stesso ordine |
| `importante` | la lacuna dichiarata non compare fra quelle trovate nelle recensioni: il posizionamento è un'opinione travestita da dato |
| vario | formulazioni caratteristiche riprese, promesse non mantenibili, rivendicazioni vietate |

## Che cosa blocca il titolo

Oltre all'originalità, il titolo proposto da `posizionamento` deve **stare in
copertina**: se una sua parola è più larga della prima già al corpo minimo
leggibile in miniatura — «CONCENTRAZIONE», da sola, lo è su un 6x9 — la scheda
non viene scritta e il comando si ferma. Il controllo (`coverdesign.title_problems`)
costa sedici millesimi di secondo; l'alternativa era accorgersene alla fine di
`all`, cioè dopo aver progettato, scritto, impaginato e **pagato** il libro.

Allo stesso punto, e per lo stesso motivo, si controllano gli altri due limiti
del titolo — che prima vivevano uno in `qa` (cioè a libro pagato) e l'altro
solo nella diagnostica (cioè dopo la pubblicazione):

| limite | che cos'è | esito |
|---|---|---|
| **200 caratteri** titolo + sottotitolo | il limite di KDP: oltre, il libro non si carica | **blocca** |
| **60 caratteri** di «Titolo: Sottotitolo» | dove Amazon tronca nei risultati di ricerca, e a sparire è sempre la seconda metà | **avvisa**: quasi ogni titolo vero lo supera, bloccarlo sarebbe severità |

L'analisi resta comunque su disco in `concorrente/acquisizione.json`: si
corregge il titolo lì dentro e si riparte da `concorrente build`, senza
ricomprare le quattro chiamate sulla pagina incollata.

## Limiti dichiarati

- **Il reparto non vede Amazon.** Lavora su quello che incolli: se la pagina è
  parziale, l'analisi è parziale, e `problemi` dice che cosa mancava.
- **Non ha dati storici**: niente andamento del prezzo, niente stagionalità,
  niente volumi di ricerca. Per quelli servirebbe un'API a pagamento (Keepa,
  Rainforest) e la rete aperta.
- **Le recensioni sono un campione autoselezionato**: scrive chi è entusiasta e
  chi è arrabbiato, non chi è indifferente. Dicono che cosa manca, non quanto
  grande sia il mercato di chi lo vuole.

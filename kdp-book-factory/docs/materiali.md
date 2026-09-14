# Che cosa serve da te

Due cose, e stanno entrambe dentro la cartella del libro:

```
books/<slug>/
├── brief.md              ← gli argomenti da affrontare
└── assets/
    └── copertina.jpg     ← l'immagine di copertina da migliorare
```

Le crea `kdpfactory init`. Tutto il resto lo fa la pipeline.

---

## 1. Gli argomenti: `books/<slug>/brief.md`

È un file di testo, si scrive a mano, non ha regole di formato. Viene letto
dall'architetto quando progetta la scaletta e resta nella scheda del libro per
tutti i capitoli: **gli argomenti che scrivi lì vanno coperti tutti**, e il
modello non può inventarne di estranei.

Il modulo creato da `init` ha già le sezioni giuste:

| Sezione | Che cosa scriverci |
|---|---|
| Di che cosa parla il libro | il problema concreto del lettore e la soluzione che proponi, due o tre frasi |
| A chi si rivolge | chi è, che cosa ha già provato, che cosa lo blocca |
| Che cosa deve saper fare alla fine | i risultati verificabili, non le buone intenzioni |
| Argomenti da coprire | l'elenco, in ordine libero: è la materia prima della scaletta |
| Che cosa NON deve esserci | luoghi comuni del settore, temi da evitare, tesi con cui non sei d'accordo |
| Materiale tuo | esperienze, casi, numeri, metodi che hai già: è ciò che rende il libro diverso dagli altri |
| Tono | come vuoi suonare |

Le righe fra `<!--` e `-->` e i suggerimenti fra parentesi non vengono letti:
puoi lasciarli o cancellarli.

**La sezione che pesa di più è "Materiale tuo".** Senza, il libro può solo
riorganizzare quello che si trova ovunque; con tre esempi presi dalla tua
esperienza diventa un libro che nessun altro può scrivere.

Per vedere se il file è a posto:

```bash
python3 -m kdpfactory plan <slug>
```

mostra `Argomenti (brief.md) : compilato, N parole` oppure dice che manca.

---

## 2. L'immagine di copertina: `books/<slug>/assets/copertina.jpg`

Il nome deve essere `copertina` (o `cover`); l'estensione può essere `.jpg`,
`.jpeg`, `.png`, `.webp`, `.tif`.

### Che cosa ci fa la pipeline

1. La raddrizza se è una foto scattata col telefono (dati EXIF).
2. La ritaglia al centro sulle proporzioni esatte della prima di copertina,
   abbondanza inclusa — per un 6x9 pollici sono **1838 x 2775 pixel**.
3. La porta a 300 DPI, la risoluzione di stampa di KDP.
4. La ripulisce: contrasto automatico, colore e nitidezza leggermente alzati
   (di più si vedrebbe in stampa).
5. Ci sfuma sopra una velatura scura in alto e in basso, così titolo e nome
   dell'autore restano leggibili qualunque sia la foto.

Il risultato è `build/<slug>-copertina-immagine.jpg`: quello che vedi lì è
esattamente quello che va in stampa.

### Risoluzione minima

| DPI reali | Esito |
|---|---|
| 300 o più | ideale |
| 200-299 | stampabile, il controllo qualità avvisa: i dettagli fini si ammorbidiscono |
| sotto 200 | **bloccato**: in stampa si vede sgranata |

Ingrandire non inventa pixel che non ci sono. Per un 6x9 punta a un originale
di almeno 1900 x 2800 pixel; qualsiasi foto da smartphone recente li supera.

### Che immagine funziona

- Una sola cosa riconoscibile, non una scena affollata: sulla miniatura di
  Amazon il libro è alto due centimetri.
- Spazio libero in alto e in basso: lì vanno titolo e nome dell'autore.
- Niente testo dentro l'immagine: il titolo lo mette la pipeline, con il font
  del libro.
- **Diritti**: dev'essere tua o con licenza commerciale esplicita. Le immagini
  trovate con una ricerca non lo sono, e su KDP si dichiara di avere i diritti
  su tutto ciò che si carica.

### Se non carichi nessuna immagine

Non succede niente di male: la copertina esce tipografica (fondo, cornice,
titolo, filetto, autore) in uno dei sei temi di colore. Per forzare quella
scelta anche avendo un'immagine in `assets/`, in `book.json`:

```json
"cover_style": "tipografica"
```

Gli altri valori sono `"immagine"` (errore se il file manca) e `"auto"`, il
predefinito: usa l'immagine se c'è.

---

## Dopo il caricamento

```bash
python3 -m kdpfactory plan <slug>     # controlla che entrambi i materiali ci siano
python3 -m kdpfactory all <slug>      # scrive, impagina, revisiona, prepara la scheda
```

La preparazione dell'immagine viene stampata a schermo (misure di origine, misure
finali, DPI reali) e finisce in `state.json`; gli eventuali problemi compaiono nel
rapporto di `kdpfactory qa` con il codice `IMMAGINE`.

Originale e versione preparata entrano nelle copie di backup a ogni passaggio:
il file che hai caricato non viene mai modificato sul posto.

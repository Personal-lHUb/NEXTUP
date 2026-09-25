# kdp-book-factory

Pipeline per produrre **libri full content** pronti da caricare su Amazon KDP:
dal solo argomento fino al PDF dell'interno, alla copertina full-wrap, all'EPUB
e alla scheda prodotto.

Il libro non esce da una passata sola: lo lavora un **collegio editoriale** di
agenti — architetto, ghostwriter, revisore di stile, editor — e lo controllano
un **lettore cieco** (legge senza sapere nulla del progetto), un fact-checker,
un revisore di conformità e un controllo di impaginazione che misura il PDF
riga per riga. È la catena di una redazione, non un unico prompt lungo.

Due linee di produzione: **libri in prosa**, scritti dal collegio di agenti, e
**libri di enigmi di deduzione** ([`docs/enigmistica.md`](docs/enigmistica.md)),
che si generano da un seme e si *dimostrano* corretti senza chiamare nessun
modello — soluzione unica, nessun indizio superfluo, stesso seme stesso libro.

Il vincolo di progetto è il numero di pagine: **ogni libro esce fra 60 e 240
pagine**, con un obiettivo scelto da te e centrato entro il ±5%. Non è una stima
sulla fiducia: la pipeline impagina davvero, conta le pagine del PDF, ricalcola
il budget di parole e fa riscrivere i capitoli finché il libro non rientra.

```
argomento → scaletta → capitoli → [stile] → impaginazione → misura pagine
                          ↑                                       │
                          └────────── riscrittura mirata ◄─────────┘
                                                                  │
    lettore cieco · fact-checker · conformità · impaginazione ─────┤
    correttore · editor di sviluppo                               │
                          └─── segnalazioni → editor → rimpagina ──┘
                                                                  │
                               copertina + EPUB + scheda KDP + controlli
```

---

## Cosa produce

Per ogni libro, dentro `books/<slug>/build/`:

| File | A cosa serve |
|---|---|
| `<slug>-interno.pdf` | interno per la stampa: formato esatto, margini speculari, font incorporati |
| `<slug>-copertina.pdf` | copertina full-wrap (quarta + dorso + prima) con dorso calcolato sulle pagine reali |
| `<slug>-copertina-miniatura.png` | la prima larga 160 px, com'è vista nei risultati di ricerca: è lì che si giudica |
| `<slug>.epub` | edizione Kindle, generata dallo stesso testo |
| `<slug>-manoscritto.md` | manoscritto unico, per rileggere o passare a un editor umano |
| `kdp-listing.md` | titolo, descrizione HTML, 7 keyword, categorie, prezzi e royalty stimate |
| `metadata.json` | gli stessi dati in formato macchina |
| `revisioni.md` | segnalazioni del collegio, per capitolo, dalla più grave |

Tutto questo, insieme a `book.json`, alla scaletta e al manoscritto, viene anche
copiato in `backup/<slug>/<data-ora>/` a ogni passaggio: vedi
[Copie di sicurezza](#copie-di-sicurezza).
| `qa-report.json` | esito dei controlli di qualità e conformità |

L'interno rispetta le regole KDP che fanno scartare un file in fase di
caricamento: formato pagina uniforme, margine interno crescente col numero di
pagine, margini esterni ≥ 0,25", **tutti i font incorporati**, numero di pagine
pari, capitoli in apertura di pagina dispari.

---

## Che cosa serve da te

Due file, dentro la cartella del libro, creati da `init`:

```
books/<slug>/
├── brief.md              ← gli argomenti da affrontare (si scrive a mano)
└── assets/
    └── copertina.jpg     ← l'immagine di copertina da migliorare (facoltativa)
```

`brief.md` entra nella scheda del libro e vincola scaletta e capitoli: gli
argomenti che scrivi lì vanno coperti tutti. L'immagine viene raddrizzata,
ritagliata sulle proporzioni della copertina, portata a 300 DPI, ripulita e
velata quanto basta perché il titolo resti leggibile; senza immagine la
copertina esce tipografica. Istruzioni per esteso e requisiti di risoluzione in
[`docs/materiali.md`](docs/materiali.md).

```bash
python3 -m kdpfactory plan <slug>   # dice se i due materiali ci sono e sono a posto
```

---

## Installazione

```bash
cd kdp-book-factory
python3 -m pip install -r requirements.txt      # oppure: make install
export ANTHROPIC_API_KEY=sk-ant-...             # oppure: ant auth login
```

Serve Python 3.11+. I font: la pipeline cerca font TrueType di sistema
(Liberation, DejaVu, EB Garamond…). Per usarne uno tuo, copia i quattro file
(regular, bold, italic, bold-italic) nella cartella `fonts/`.

### Prova senza spendere token

```bash
python3 -m kdpfactory --dry-run all collaudo
```

Genera un libro completo con testo segnaposto: serve a collaudare impaginazione,
conteggio pagine, copertina ed EPUB senza una sola chiamata API. Il controllo
qualità blocca volutamente quel testo (`SEGNAPOSTO`): un libro in dry-run non va
mai caricato.

---

## Uso

```bash
# 1. crea il progetto
#    (oppure fallo nascere da un'analisi di mercato:
#     concorrente new <slug> --asin B0… , incolli la pagina, poi concorrente build)
python3 -m kdpfactory init "Il Metodo delle Tre Ore" \
    --subtitle "Come chiudere il lavoro che conta prima delle 15" \
    --author "Nome Cognome" \
    --pages 140 --trim 6x9 \
    --topic "organizzare la giornata attorno a tre blocchi di lavoro profondo" \
    --audience "freelance che lavorano a interruzione continua" \
    --promise "liberare il pomeriggio senza allungare la giornata"

# 2. completa books/<slug>/book.json (topic, audience, promise, notes)

# 3. pipeline completa
python3 -m kdpfactory all il-metodo-delle-tre-ore
```

**Il passaggio 2 è quello che decide la qualità del libro.** Con un `topic`
generico esce un libro generico. I campi che contano di più sono `topic`,
`audience`, `promise` e `notes` (istruzioni libere: cosa evitare, che tipo di
esempi usare, quale taglio dare).

### Comandi

| Comando | Cosa fa |
|---|---|
| `init "Titolo"` | crea `books/<slug>/book.json` (`--content-type full\|medium`) |
| `plan <slug>` | budget di pagine e parole, misure di stampa, stato dei capitoli |
| `outline <slug>` | genera la scaletta (`outline.json`) |
| `write <slug>` | scrive i capitoli mancanti (`--only 3,4`, `--overwrite`) |
| `build <slug>` | impagina, converge sulle pagine, genera copertina ed EPUB |
| `metadata <slug>` | scheda prodotto, keyword, categorie, prezzi |
| `manuale <slug> <passo>` | **la fabbrica senza chiave API**: il sistema scrive il brief di scaletta, capitolo o scheda, tu porti la risposta e lui la valida ([`docs/linea-manuale.md`](docs/linea-manuale.md)) |
| `copertina <slug>` | brief di copertina per uno strumento grafico, compilato coi dati del libro ([`docs/copertine.md`](docs/copertine.md)); nessuna chiamata API |
| `agents` | elenco del collegio (`--install` li installa in Claude Code) |
| `backup <slug>` | elenco delle copie, `--now`, `--restore <id>`, `--prune N` |
| `puzzle new/build <slug>` | libri di enigmi di deduzione, senza chiamate API |
| `concorrente new/build <slug>` | da una scheda Amazon incollata alla scheda di un libro nuovo che copre quello che i suoi lettori non hanno trovato ([`docs/acquisizione.md`](docs/acquisizione.md)) |
| `review <slug>` | fa leggere il libro agli agenti di controllo |
| `revise <slug>` | l'editor applica le segnalazioni raccolte |
| `qa <slug>` | controlli di qualità e conformità |
| `all <slug>` | tutto in sequenza |
| `list` | elenco dei libri e stato di avanzamento |
| `diagnostica` | misura tutti i libri e il sistema: costi, resa, sprechi della scheda, difetti ricorrenti (nessuna chiamata API). I banchi di prova — `book.json` con `banco_di_prova` — restano fuori; `--banchi` li include |
| `specs --pages 160 --trim 6x9` | misure KDP per una combinazione formato/pagine |

Opzioni globali: `--dry-run`, `--model` (default `claude-opus-5`), `--effort`
(`low`…`max`), `--max-tokens`, `--books-dir`.

Il livello di lavorazione decide quanti agenti entrano in gioco:
`--qualita bozza` (solo stesura), `standard` (default: stesura + collegio +
editor), `alta` (in più stile e correttore di bozze). Dettagli in
[`docs/agenti.md`](docs/agenti.md); la sequenza completa di produzione, fase
per fase, con i cancelli e l'agente responsabile di ogni passo, in
[`docs/linee-guida.md`](docs/linee-guida.md).

Ogni comando è ripetibile: `write` salta i capitoli già scritti, `build` si può
rilanciare quante volte serve. Il lavoro si interrompe e si riprende senza
perdere nulla (`state.json`).

---

## Copie di sicurezza

Ogni comando che scrive file lascia uno **snapshot datato** in
`backup/<slug>/<AAAAMMGG-hhmmss>/`: scheda del libro, scaletta, manoscritto e
tutto il contenuto di `build/`. Serve soprattutto contro sé stessi: l'editor, la
passata di stile e `write --overwrite` riscrivono i capitoli sul posto, e una
stesura che piaceva si perde in un istante. Prima di ogni riscrittura la copia
viene forzata, anche se l'ultima è di un minuto prima.

```bash
python3 -m kdpfactory backup <slug>                  # elenco delle copie
python3 -m kdpfactory backup <slug> --now            # copia subito
python3 -m kdpfactory backup <slug> --restore latest # torna all'ultima
python3 -m kdpfactory backup <slug> --prune 10       # tieni solo le ultime 10
```

- Due copie identiche non vengono duplicate: se nulla è cambiato, lo snapshot
  viene saltato.
- Il ripristino **sovrascrive ma non cancella**, e prima di procedere mette al
  sicuro lo stato attuale: un ripristino sbagliato non è definitivo.
- Ogni snapshot ha un `manifest.json` con dimensioni e hash SHA-256 di ogni file.
- Cartella diversa: `--backup-dir /percorso` oppure `KDPFACTORY_BACKUP_DIR`.
  Per disattivarle in una singola esecuzione: `--no-backup`.
- `backup/` è fuori da git: sta sul disco, dove puoi sincronizzarla come
  preferisci.

---

## Come viene controllato il numero di pagine

Prima di tutto, una cosa che non è ovvia: **le pagine sono una scalinata, non
una retta**. Ogni capitolo si apre su pagina dispari, quindi occupa un numero
pari di pagine; fra un gradino e l'altro mille parole in più non spostano
niente, e il salto successivo vale due pagine per capitolo. Cercare l'obiettivo
correggendo le parole, e basta, non funziona — ed è il motivo per cui il primo
PDF usciva sempre circa il 10% sotto.

1. **Taratura, prima di scrivere una riga.** Si impaginano due libri di prova
   con la struttura di quelli veri e si misura la scalinata: parole per pagina
   piena, costo di un'apertura di capitolo, pagine fisse. Poi si prova ogni
   budget ammissibile e si sceglie quello che cade sul gradino più vicino
   all'obiettivo. Costa qualche secondo di CPU e **nessuna chiamata API**;
   il risultato resta in `state.json` e si paga una volta sola.
   Misurato su sette formati: senza taratura 7 su 7 fuori dalla finestra ±5%,
   con la taratura 7 su 7 dentro.
2. **Misura.** Il PDF viene impaginato per davvero e le pagine si contano.
3. **Ricalibrazione.** Dal rapporto reale parole/pagina si ricalcola il budget e
   si assegna a ogni capitolo un nuovo obiettivo (correzione limitata a ±45% per
   evitare oscillazioni).
4. **Riscrittura mirata.** Solo i capitoli fuori tolleranza vengono riscritti,
   con l'istruzione di *aggiungere sostanza* o *tagliare ripetizioni*, non di
   allungare o accorciare le frasi.
5. Si ripete (default: 4 tentativi) finché il PDF non rientra nella finestra.

La misura parole/pagina viene salvata: dal libro vero in poi vince quella, che
conosce anche la densità della prosa e non solo la struttura. Se non vuoi spendere token in
riscritture: `build --no-rewrite`, oppure allarga la tolleranza
(`--tolerance 0.1`).

Esempio reale (in dry-run, obiettivo 80 pagine):

```
→ impaginazione 1: 98 pagine   parole/pagina 258.5   correzione -23.2%
→ impaginazione 2: 72 pagine   parole/pagina 308.5   correzione +15.5%
→ impaginazione 3: 84 pagine   ✓ dentro 76-84
```

---

## Quanto costa un libro

Con `claude-opus-5` ed effort `high`, un libro da 140 pagine (~35.000 parole)
richiede una ventina di chiamate: scaletta, un capitolo per volta, i riassunti
di continuità, la scheda prodotto, più le eventuali riscritture. Il prompt di
sistema (regole d'autore + scheda del libro + scaletta) è identico per tutti i
capitoli ed è messo in **cache**: si paga per intero una volta sola.

Il consumo effettivo viene stampato a fine esecuzione e salvato in `state.json`:

```json
{"calls": 21, "input_tokens": 18432, "output_tokens": 61240,
 "cache_read_tokens": 214880, "estimated_cost_usd": 1.83}
```

Per abbassare il costo: `--effort medium` per i libri più semplici,
`--model claude-sonnet-5` per le bozze, `build --no-rewrite` quando le pagine
sono già vicine all'obiettivo.

---

## Struttura del progetto

```
kdp-book-factory/
├── kdpfactory/
│   ├── cli.py          comandi
│   ├── models.py       BookSpec, Outline, struttura su disco
│   ├── kdpspecs.py     formati, margini, dorso, limiti KDP
│   ├── planner.py      pagine → parole, ricalibrazione
│   ├── prompts.py      prompt d'autore, scaletta, revisione, metadati
│   ├── llm.py          client Claude: streaming, cache, costi, dry-run
│   ├── writer.py       scaletta, capitoli, continuità, revisioni
│   ├── typeset.py      impaginazione PDF dell'interno
│   ├── cover.py        copertina full-wrap
│   ├── coverdesign.py  sistema di copertina: regole, palette, testi, verifica
│   ├── coverart.py     illustrazioni vettoriali della prima, scelte dal contenuto
│   ├── coverbrief.py   brief di copertina per uno strumento grafico esterno
│   ├── manuale.py      linea manuale: brief e importazioni, senza chiamate al modello
│   ├── epub.py         EPUB 3
│   ├── agents/         collegio editoriale: ruoli, revisione, impaginazione
│   ├── backup.py       snapshot, ripristino, pulizia
│   ├── puzzle/         enigmi di deduzione: modello, solver, generatore, impaginazione
│   ├── coverimage.py   preparazione dell'immagine di copertina (300 DPI, velatura)
│   ├── qa.py           controlli di qualità e conformità
│   ├── diagnostica.py  misure su tutti i libri: costi, resa, sprechi della scheda
│   ├── metadata.py     scheda prodotto, prezzi, royalty
│   └── pipeline.py     orchestrazione e convergenza sulle pagine
├── books/<slug>/       book.json, brief.md, assets/, manuscript/, build/
├── config/             costi di stampa per il calcolo delle royalty
├── docs/               checklist di pubblicazione, workflow, personalizzazione
└── tests/              170 test, nessuna chiamata API
```

```bash
make test     # python3 -m unittest discover -s tests
```

---

## Prima di pubblicare

Tre cose che il codice non può fare al posto tuo:

1. **Leggere il libro.** La pipeline produce un manoscritto coerente e della
   lunghezza giusta; non garantisce che ogni affermazione sia vera. I prompt
   vietano statistiche e citazioni non verificabili proprio perché su carta un
   errore resta. Rileggi, correggi, taglia.
2. **Dichiarare l'uso dell'IA.** KDP chiede se il contenuto è generato con
   intelligenza artificiale: va dichiarato (testo e, se generata, copertina). È
   una dichiarazione interna, non appare sulla scheda e non blocca la
   pubblicazione.
3. **Rispettare le regole di contenuto.** Niente materiale altrui, niente libri
   che si spacciano per opere di altri autori, niente consigli medici, legali o
   finanziari presentati come consulenza professionale.

Le linee guida di produzione sono in [`docs/linee-guida.md`](docs/linee-guida.md);
la checklist completa in [`docs/checklist-kdp.md`](docs/checklist-kdp.md); il
collegio editoriale in [`docs/agenti.md`](docs/agenti.md); la linea enigmistica
in [`docs/enigmistica.md`](docs/enigmistica.md); i materiali da
fornire in [`docs/materiali.md`](docs/materiali.md); il
metodo di lavoro per produrre più titoli in [`docs/workflow.md`](docs/workflow.md);
il sistema di copertina in [`docs/copertine.md`](docs/copertine.md);
il team che migliora il sistema in [`docs/team-miglioramento.md`](docs/team-miglioramento.md);
formati, font e palette in
[`docs/personalizzazione.md`](docs/personalizzazione.md).

> I costi di stampa in `config/printing_costs.json` e le specifiche KDP
> codificate in `kdpspecs.py` sono quelli pubblicati da Amazon al momento della
> scrittura. Amazon li aggiorna: verificali prima di fissare un prezzo.

# Linee guida per la creazione di un libro

Come si porta un libro dall'idea al caricamento su KDP, passo per passo, e chi
lavora in ogni passo. Valgono per tutte e due le linee della fabbrica: quella
con la chiave API (`all`, `outline`, `write`…) e quella manuale, senza chiave
(`manuale …` più gli agenti chiamati da Claude Code, [`linea-manuale.md`](linea-manuale.md)).

Le regole di dettaglio restano dove sono: la copertina in
[`copertine.md`](copertine.md), il collegio in [`agenti.md`](agenti.md), la
pubblicazione in [`checklist-kdp.md`](checklist-kdp.md). Qui c'è l'ordine in
cui si applicano e il confine fra un lavoro e l'altro.

---

## I quattro principi

**1. Una competenza, un solo responsabile.** Ogni cosa da produrre o da
controllare ha un agente, e uno solo. Due agenti sulla stessa cosa costano due
chiamate e producono due segnalazioni che dicono la stessa cosa con parole
diverse; quando si contraddicono, nessuno sa quale vale. L'elenco completo sta
in `kdpfactory/agents/competenze.py`, da lì ogni agente ricava il suo campo e
l'elenco di quello che non deve guardare, e un test impedisce di aggiungere una
competenza senza padrone o con due.

**2. Chi produce non controlla, chi controlla non corregge.** L'architetto
progetta, il ghostwriter scrive, i revisori segnalano. Nel testo mette le mani
una sola figura dopo la stesura: l'editor, che applica le segnalazioni e
nient'altro. Nella linea manuale l'editor sei tu, o la sessione di Claude Code
che applica i rilievi.

**3. Ogni fase ha un cancello.** Si passa alla fase successiva solo con il
cancello chiuso, e il cancello è una misura, non un'impressione: zero
bloccanti del revisore di scaletta, pagine dentro l'intervallo, zero errori del
controllo qualità. Un difetto che passa un cancello lo paga tutto quello che
viene dopo: una scaletta sbagliata la pagano trenta capitoli.

**4. Il sistema scrive, conta e misura; l'autore decide.** Tutto quello che si
può contare lo conta il sistema: pagine, dorso, cifre di copertina, corpo del
titolo, righe del sommario. Le decisioni che definiscono il libro — la
categoria, il titolo, la promessa, il prezzo, chi racconta — restano
all'autore, e sono elencate più avanti.

Due regole permanenti di `CLAUDE.md` valgono in ogni fase: **ogni file generato
ha una copia di backup** (la pipeline la fa da sé; per il resto
`backup/manuale/<data>/`), e **i prompt delle immagini li scrive il sistema**,
non la chat.

---

## Chi fa che cosa

Il campo di ogni agente del collegio di produzione. È la stessa tabella di
`competenze.py`, raggruppata per fase.

| fase | agente | il suo campo, e solo quello |
|---|---|---|
| acquisizione | `scheda-concorrente` | i dati della scheda del concorrente: prezzo, pagine, categorie, recensioni |
| acquisizione | `analista-recensioni` | le lacune che i lettori del concorrente scrivono nelle recensioni |
| acquisizione | `posizionamento` | il libro da fare: promessa, lettore, titolo, pagine, prezzo, temi del brief |
| acquisizione | `originalita` | la distanza dal concorrente: titolo, marchi altrui, struttura copiata |
| progetto | `architetto` | la struttura: tesi, sequenza e contenuto dei capitoli, parti, testo di quarta |
| progetto | `indice` | il testo dell'indice: il titolo definitivo di ogni capitolo e di ogni parte |
| progetto | `revisore-scaletta` | le misure della scaletta: argomenti scoperti, capitoli gemelli, conteggio, date e cifre, parti valide, titoli che non stanno su una riga o in copertina |
| stesura | `ghostwriter` | il testo dei capitoli, sul programma e sul budget di parole |
| stesura | `voce` | il ritmo e la voce della frase |
| stesura | `editor` | l'applicazione delle segnalazioni al testo |
| controllo | `lettore-cieco` | l'esperienza di chi legge; le promesse della vetrina (copertina, descrizione, indice) e se il libro le mantiene |
| controllo | `editor-sviluppo` | la coerenza interna: contraddizioni e conti fra capitoli, ripetizioni, ordine dei concetti, equilibrio, aperture |
| controllo | `fact-checker` | le affermazioni sul mondo fuori dal libro: dati, fonti, citazioni, norme, generalizzazioni |
| controllo | `conformita` | rischi legali e regole KDP nel testo e nella scheda: terzi, marchi, persone reali, consulenza, promesse di risultato, avvertenze, parole chiave |
| controllo | `correttore` | le bozze: refusi, accenti, accordi, punteggiatura, maiuscole |
| stampa | `impaginazione` | l'interno impaginato: vedove, orfane, code, gabbia, varietà delle pagine |
| stampa | `copertina` | la copertina: il prompt dell'illustrazione e delle figure, le misure del PDF, i testi stampati |

Tre confini che prima si sovrapponevano, e adesso no:

- **Le promesse** — che il libro mantenga quello che titolo, descrizione e
  indice promettono — sono solo del **lettore cieco**, perché è l'unico che le
  legge come il cliente: dalla vetrina, senza sapere che cosa l'autore voleva
  fare. L'editor di sviluppo e la conformità non le guardano più.
- **I conti interni** — «sei sedute», «quattro minuti», «nove persone» — sono
  dell'**editor di sviluppo**: sono coerenza del libro con sé stesso. Il
  fact-checker guarda solo il mondo fuori dal libro.
- **Ordine e ripetizioni** fra capitoli sono dell'**editor di sviluppo**;
  l'**indice** scrive i titoli senza toccare né l'ordine né il numero, che sono
  dell'architetto.

Gli agenti del team di miglioramento (`analista-mercato`, `capo-collana`,
`avvocato-del-diavolo`, `economo`, `ingegnere-pipeline`) non entrano nella
produzione di un libro: lavorano sul sistema, e sono documentati in
[`team-miglioramento.md`](team-miglioramento.md).

---

## Le fasi

```
0  acquisizione (facoltativa)   scheda-concorrente → analista-recensioni → posizionamento → originalita
1  progetto                     architetto → indice → revisore-scaletta          cancello: 0 bloccanti
2  stesura                      ghostwriter  (+ voce al livello alta)            cancello: il capitolo 1 ti convince
3  prima impaginazione          build → impaginazione                            cancello: pagine nell'intervallo
4  controllo del testo          lettore-cieco · editor-sviluppo · fact-checker · conformita  (+ correttore)
5  correzione                   editor → build                                   cancello: 0 bloccanti, 0 importanti aperti
6  scheda prodotto              scheda → conformita sulla scheda → vetrina       cancello: 0 bloccanti
7  copertina                    copertina (prompt) → l'immagine → copertina (misure)   cancello: 0 bloccanti
8  chiusura                     qa → checklist KDP                               cancello: 0 errori
```

In ogni fase qui sotto: chi lavora, che cosa entra, che cosa esce, come lo si
chiama nelle due linee, quando il cancello è chiuso.

### Prima di tutto: la categoria

Ogni libro è **full-content** (testo pieno, da leggere) oppure
**medium-content** (interattivo, ogni pagina diversa), e la categoria si
decide **prima della scaletta**: vincola impaginazione, indice, copertina,
scheda e prezzo. Si dichiara con `init --content-type full|medium` e resta in
`book.json` come `content_type`. La linea prosa produce full-content, la linea
enigmistica medium-content. Le definizioni sono in `CLAUDE.md`, e il sistema le
fa rispettare: un full-content con righe da compilare è un errore del
controllo qualità, un medium-content con più di metà pagine uguali è
scivolato nel low-content e l'impaginazione lo dice.

```bash
python3 -m kdpfactory init "Titolo di lavoro" --pages 200 --content-type full \
    --topic "…" --audience "…"
$EDITOR books/<slug>/book.json      # promessa, tono, note di linea editoriale
```

Le `notes` di `book.json` sono la **linea editoriale**: che cosa il libro si
vieta (una promessa, una parola, un tipo di affermazione). Tutti gli agenti
che scrivono le ricevono, e l'indice le rispetta nei titoli.

### 0 · Acquisizione — solo se il libro nasce da una scheda Amazon

| | |
|---|---|
| **Chi** | `scheda-concorrente` → `analista-recensioni` → `posizionamento` → `originalita` |
| **Entra** | la pagina del concorrente, copiata e incollata |
| **Esce** | `book.json` e `brief.md` del libro nuovo |
| **Comando** | `python3 -m kdpfactory concorrente …` ([`acquisizione.md`](acquisizione.md)) |
| **Cancello** | nessun bloccante di `originalita`: un libro troppo vicino all'altro non si scrive |

### 1 · Progetto — scaletta e indice

Il passaggio che conta di più: qui correggere costa un file, dopo costa un
libro.

| | |
|---|---|
| **Chi** | `architetto` progetta, `indice` scrive i titoli, `revisore-scaletta` misura |
| **Entra** | `book.json`, `brief.md`, il budget di pagine |
| **Esce** | `outline.json`: capitoli, parti, sintesi, punti, parole di ciascuno, quarta |
| **Linea API** | `python3 -m kdpfactory outline <slug>` — architetto, indice e revisore in un colpo solo |
| **Linea manuale** | `manuale <slug> scaletta` → scrivi `manuale/scaletta.json` → **«usa indice su books/<slug>/manuale/scaletta.json»** → applica i titoli → `manuale <slug> scaletta --esamina` → `--importa` |
| **Cancello** | zero bloccanti del revisore; gli importanti letti uno per uno |

Che cosa deve avere una scaletta prima di passare:

- **tesi** in due frasi, e ogni capitolo che la fa avanzare;
- **ogni argomento del brief** coperto da un capitolo (il revisore lo misura);
- **nessuna coppia di capitoli gemelli** (parole in comune oltre il 45%);
- **parti** oltre i venti capitoli: tre-sei, di almeno due capitoli ciascuna,
  con un'introduzione che può restare fuori come prefazione;
- **nessuna data né cifra presentata come fatto** nei titoli e nella quarta:
  quelle che restano finiscono nell'elenco delle cifre da contare sul libro
  finito;
- **il titolo del libro entra in copertina** a misura leggibile.

#### L'agente `indice`

L'indice è la pagina che il cliente apre nell'anteprima «Guarda dentro» prima
di decidere. L'agente riscrive i titoli perché **vendano** il capitolo invece
di descriverlo, e lavora **prima della stesura**: il ghostwriter scrive ogni
capitolo sul suo titolo.

- **Un titolo dice che cosa si ottiene o che cosa succede**, non di che cosa si
  parla; è concreto; sta in piedi da solo; non somiglia a nessun altro.
- **Sta su una riga del sommario.** Di norma sotto i 55 caratteri; il revisore
  lo misura con il carattere, il corpo e la giustezza veri del PDF e segnala
  `titolo su due righe`.
- **Le parti** hanno titoli di due-cinque parole che nominano il tratto di
  strada; il numero («Parte II») lo aggiunge l'impaginazione.
- **Rispetta la linea editoriale** del libro: niente parole che il libro si
  vieta, niente promesse che non fa.
- **Non tocca** l'ordine, il numero dei capitoli, i confini delle parti, il
  contenuto. Consegna un blocco JSON con gli stessi numeri; chi lo applica
  rilancia il revisore.

Profondità del sommario: nei full-content solo parti e capitoli; nei
medium-content anche le sezioni, perché lì le sezioni sono le schede che si
cercano (`toc_depth: null` lascia decidere alla categoria).

### 2 · Stesura

| | |
|---|---|
| **Chi** | `ghostwriter`; `voce` al livello `alta` |
| **Entra** | `outline.json`, la scheda del libro, il riassunto di quello che è già stato detto |
| **Esce** | `manuscript/NN.md`, un file per capitolo |
| **Linea API** | `python3 -m kdpfactory write <slug>` |
| **Linea manuale** | `manuale <slug> capitolo --numero N` → scrivi `manuale/capitolo-NN.md` → `--importa` |
| **Cancello** | hai letto il capitolo 1 per intero e ti convince |

Il capitolo 1 si legge **prima** di scrivere gli altri: se il tono non va, si
aggiustano `tone` e `notes` e si riscrive (`write <slug> --only 1
--overwrite`). Tutti gli altri capitoli ereditano quelle istruzioni.

Un capitolo che esce oltre il 25% dal suo budget lo dice l'importazione: è lì
che il conteggio pagine comincia a sbagliare.

### 3 · Prima impaginazione

| | |
|---|---|
| **Chi** | il motore di impaginazione; `impaginazione` misura il PDF |
| **Esce** | `build/<slug>-interno.pdf`, la copertina del motore, l'EPUB, `build/vetrina.md` |
| **Comando** | `python3 -m kdpfactory build <slug>` poi `review <slug> --agents impaginazione` |
| **Cancello** | pagine dentro l'intervallo dell'obiettivo (±5%) |

Si impagina **prima** della revisione per due ragioni: l'impaginazione dice se
il libro sta nelle pagine, e produce la **vetrina** (`build/vetrina.md`) —
titolo, sottotitolo, gancio, descrizione e indice con le pagine vere — che è
quello che il lettore cieco riceve come promessa del libro.

### 4 · Controllo del testo

Il collegio legge e **segnala**. Nessuno corregge.

| agente | come si chiama (Claude Code) | che cosa riceve |
|---|---|---|
| `lettore-cieco` | «usa lettore-cieco su books/<slug>/manuscript/07.md» e, alla fine, «usa lettore-cieco sul libro <slug>» | solo i capitoli e la vetrina: **mai** scaletta, `book.json`, brief o rapporti di altri |
| `editor-sviluppo` | «usa editor-sviluppo sul libro <slug>» | la scaletta e tutto il manoscritto |
| `fact-checker` | «usa fact-checker su books/<slug>/manuscript/NN.md», un blocco di capitoli per volta | i capitoli e l'argomento del libro |
| `conformita` | «usa conformita su books/<slug>/manuscript/NN.md» | i capitoli; la scheda la legge alla fase 6 |
| `correttore` | «usa correttore su …», al livello `alta` | un capitolo per volta |

Nella linea API: `python3 -m kdpfactory review <slug>` fa lavorare il collegio
del livello scelto (`--qualita bozza|standard|alta`, [`agenti.md`](agenti.md)).

Regole per chiamare il collegio:

- **Ognuno sul suo campo.** Non si chiede al fact-checker di dire se un
  capitolo annoia, né al lettore cieco se una statistica è vera: ciascuno ha
  nel suo file l'elenco di quello che non deve guardare, e se lo nota lo lascia.
- **Il lettore cieco resta cieco.** Non gli si passa un riassunto, un'intenzione
  dell'autore, il rapporto di un altro agente. Se lo si chiama sul libro intero
  e la vetrina non c'è, prima si fa `build`.
- **I blocchi grandi si dividono.** Un fact-checker su trentadue capitoli
  insieme legge peggio di quattro fact-checker su otto capitoli ciascuno: si
  dividono i capitoli, non le competenze.
- **Si aspetta il collegio intero** prima di correggere: una correzione fatta
  sulla prima segnalazione arrivata può essere smentita dalla seconda.

### 5 · Correzione

| | |
|---|---|
| **Chi** | `editor` (nella linea manuale: tu, sui file `manuale/capitolo-NN.md`) |
| **Entra** | le segnalazioni del collegio, ordinate per gravità |
| **Comando** | `python3 -m kdpfactory revise <slug> --severita importante`, poi `build <slug>` |
| **Linea manuale** | modifichi `manuale/capitolo-NN.md` → `manuale <slug> capitolo --numero N --importa` → `build` |
| **Cancello** | zero bloccanti e zero importanti aperti; il libro dentro l'intervallo di pagine |

Come si applica:

1. **Prima i bloccanti, poi gli importanti.** I minori al livello `alta`.
2. **Solo quello che è stato segnalato.** Chi rilegge deve riconoscere il
   proprio testo.
3. **Un dato non verificabile si riformula, non si cancella**: la frase deve
   reggere senza, senza lasciare un vuoto logico.
4. **Un conto sbagliato si rifà sul libro**, contando nei capitoli, non
   correggendo la cifra che sembra più plausibile.
5. **Se due segnalazioni si contraddicono** vince quella del responsabile della
   competenza (la tabella qui sopra), poi la più grave.
6. **Dopo la correzione si rimpagina**: l'editing cambia le parole, e le parole
   decidono le pagine.

### 6 · Scheda prodotto

| | |
|---|---|
| **Chi** | chi scrive la scheda (modello o autore); `conformita` la controlla |
| **Esce** | `build/kdp-listing.md`, `build/metadata.json`, la vetrina aggiornata |
| **Linea API** | `python3 -m kdpfactory metadata <slug>`; la conformità la legge dentro `review` |
| **Linea manuale** | `manuale <slug> scheda` → scrivi `manuale/scheda.json` → `--importa` → «usa conformita su books/<slug>/build/kdp-listing.md» |
| **Cancello** | nessun bloccante della conformità |

Le parole chiave non contengono **nomi di altri autori, titoli di altri libri,
marchi o metodi registrati da terzi**, né parole che descrivono il libro in
modo falso; non ripetono parole del titolo, che Amazon indicizza già (la
diagnostica lo segnala). La descrizione usa solo i tag che KDP accetta — il
sistema la scrive così e un test lo verifica — e non promette risultati.

### 7 · Copertina

Un solo agente, dall'inizio alla fine: `copertina`. Le regole sono in
[`copertine.md`](copertine.md); qui c'è la sequenza.

| | |
|---|---|
| **Chi** | `copertina` scrive il prompt e misura; **l'autore** genera l'immagine |
| **Entra** | i dati del libro: categoria, categorie KDP, promessa, pubblico, palette, occhiello e gancio della scheda, pagine vere |
| **Esce** | `build/copertina-brief.md` (il prompt), poi `build/<slug>-copertina.pdf` |
| **Come si chiama** | «usa copertina su <slug>» |
| **Cancello** | zero bloccanti delle misure; la miniatura supera le cinque domande |

**1. Il prompt.** Si fa dopo l'ultima impaginazione, perché dorso e misure
dipendono dalle pagine:

```bash
python3 -m kdpfactory build <slug>
python3 -m kdpfactory copertina <slug>     # build/copertina-brief.md
python3 -m kdpfactory immagini <slug>      # se il manoscritto dichiara figure
```

Il brief **non si riscrive a mano**. Se qualcosa non va — il gancio non è un
ciclo aperto, la rappresentazione non è quella del libro, la palette — si
corregge il dato da cui nasce (`cover_hook`, `categories`, `cover_art`,
`cover_theme`…) e si rigenera. L'agente verifica il brief su sette punti:
rappresentazione riconoscibile, un solo fattore distintivo, niente testo
nell'immagine, misure dell'ultima impaginazione, formula della categoria,
nessuna rivendicazione vietata, nessun nome altrui.

**2. L'immagine.** Il brief si incolla così com'è nel generatore (ChatGPT,
Gemini) o si passa a un grafico. Torna **solo l'illustrazione della prima**,
senza testo, almeno 1800 × 2700 px per un 6x9: si salva in
`books/<slug>/assets/copertina.jpg`. Il testo lo compone il motore, sempre, in
vettoriale: è l'unico modo di misurarlo.

**3. Le misure.**

```bash
python3 -m kdpfactory build <slug>
python3 -m kdpfactory review <slug> --agents copertina
```

Corpo del titolo in miniatura (almeno 6% dell'altezza, dominante dall'8,5%),
contrasto almeno 7:1, stacco su fondo bianco, area di sicurezza, dorso, area
del codice a barre, font incorporati, autore uguale alla scheda. Poi la
miniatura a occhio, in quest'ordine: si capisce la categoria in due secondi?
L'immagine mostra il soggetto vero? Un solo concetto dominante? Il titolo vince?
Sembra una copertina di quest'anno?

### 8 · Chiusura

```bash
python3 -m kdpfactory qa <slug>
python3 -m kdpfactory review <slug> --agents impaginazione,copertina
python3 -m kdpfactory diagnostica
```

Il cancello è **zero errori** del controllo qualità. Poi
[`checklist-kdp.md`](checklist-kdp.md): caricare l'interno, la copertina
generata **dopo** l'impaginazione finale, compilare la scheda da
`kdp-listing.md`, dichiarare l'uso dell'IA, controllare l'anteprima di stampa,
ordinare una copia di prova.

---

## Il lettore cieco, per intero

È l'agente che più facilmente si rovina senza accorgersene, perché il suo
valore è **non sapere**. Se sa che cosa il libro voleva dimostrare, lo trova
anche dove non c'è.

| modo | quando | che cosa legge | che cosa dice |
|---|---|---|---|
| sul capitolo | dopo la stesura di ogni capitolo, o in blocco alla fase 4 | `manuscript/NN.md` e basta | dove si è perso, dove ha saltato righe, che cosa si aspettava e non è arrivato, che cosa suona falso |
| sul libro | una volta, alla fine della fase 4 | `build/vetrina.md`, poi tutti i capitoli in ordine | se il libro mantiene le promesse della vetrina voce per voce, gli annunci non mantenuti, il lettore o il lessico che cambiano, dove avrebbe chiuso il libro |

Non apre mai: `outline.json`, `book.json`, `brief.md`, niente in `manuale/`,
`state.json`, i rapporti degli altri agenti, `metadata.json`,
`kdp-listing.md`. Nella pipeline la cecità la garantisce il codice (riceve
solo il testo e la vetrina); dentro Claude Code la garantisce il suo file, che
elenca i soli file ammessi.

## La copertina, per intero

| passo | chi | che cosa |
|---|---|---|
| dati | autore | categoria, categorie KDP, promessa, occhiello e gancio nella scheda |
| prompt | `copertina` | `kdpfactory copertina <slug>`; verifica dei sette punti; correzioni sui dati, mai sul brief |
| immagine | autore | il brief nel generatore; torna l'illustrazione della prima, senza testo |
| composizione | motore | `build`: ritaglio, 300 DPI, titolo in vettoriale, dorso, retro |
| misure | `copertina` | `review --agents copertina`; la miniatura a occhio |

Il titolo si compone nel condensato del progetto quando il sans non basta a
renderlo dominante ([`copertine.md`](copertine.md)); le cifre stampate in
copertina sono solo quelle contate sul libro (medium-content) o nessuna
(full-content).

---

## Quello che decide l'autore

Nessun agente decide queste cose, e nessun cancello le sostituisce:

- **la categoria** (full o medium) e il **tipo di libro**;
- **il titolo** e il sottotitolo, e se tenerli quando un agente li contesta;
- **la promessa** e la **linea editoriale** (`notes` di `book.json`);
- **chi racconta**: se il libro presenta casi reali, composti o inventati, e
  come lo dichiara al lettore;
- **il prezzo**;
- **l'immagine di copertina**: il sistema scrive il prompt, l'autore la genera
  e la sceglie;
- **la pubblicazione**, dopo aver letto il libro.

Quando un agente tocca una di queste, la segnala come domanda, non la risolve.

---

## Perché queste regole: gli errori già fatti

Ogni regola qui sopra viene da un difetto trovato su un libro vero.

| difetto | fase che l'avrebbe fermato | regola |
|---|---|---|
| il libro diceva «quattro» sedute senza niente da verificare, i capitoli ne davano sei | 4, `editor-sviluppo` | i conti interni hanno un responsabile solo |
| quattro revisori hanno segnalato la stessa contraddizione in quattro modi | 4 | una competenza, un responsabile |
| una «tradizione regionale con un nome» che non esisteva | 4, `fact-checker` | le affermazioni sul mondo si verificano o si riformulano |
| un titolo d'esempio uguale a un libro vero del genere | 4, `conformita` / `fact-checker` | niente titoli, autori o metodi altrui presentati come esempi |
| un marchio registrato fra le parole chiave | 6, `conformita` sulla scheda | la scheda ha il suo controllo |
| la descrizione con un `<h2>`, che KDP non accetta | 6, sistema | solo i tag ammessi, con un test |
| un sommario di undici pagine | 1, `indice` | nei full-content l'indice mostra parti e capitoli |
| un titolo di capitolo che va a capo nel sommario | 1, `revisore-scaletta` | la riga si misura sul PDF vero |
| il titolo di copertina al 5,8% dell'altezza | 7, `copertina` | il condensato quando il sans non basta |
| il brief chiedeva «solo l'illustrazione» e poi «un PDF con dorso e retro» | 7, `copertina` | si consegna l'illustrazione; il PDF lo fa il motore |
| il lettore cieco dentro Claude Code poteva aprire la scaletta | 4 | la vetrina e i capitoli, nient'altro |
| la linea API non passava dal revisore di scaletta | 1 | il cancello è lo stesso nelle due linee |

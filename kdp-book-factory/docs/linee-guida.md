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

## Chi chiama gli agenti: nessuno, si chiamano da soli

Gli agenti non aspettano che qualcuno si ricordi di loro: ognuno **scatta
quando la sua fase lo richiede**.

- **Con la chiave API** li chiama la pipeline: `all` fa lavorare architetto,
  indice, revisore di scaletta, ghostwriter, voce, collegio, editor,
  impaginazione e copertina — prompt compreso — nell'ordine delle fasi.
- **Nella linea manuale** li chiama la sessione di Claude Code che sta
  lavorando al libro, **senza chiedere il permesso**: è un'istruzione
  permanente di `CLAUDE.md`. Le decisioni dell'autore (elencate più avanti)
  non la fermano: le propone con il silenzio-assenso, e l'immagine di
  copertina la genera Cowork.
- **Il giro orario** la sveglia da solo: la routine «Produzione NEXTUP» porta
  i file fra Drive e il repository, applica le risposte di Cowork, chiude le
  decisioni scadute e fa il prossimo passo di ogni libro attivo, quello che
  dice `python3 -m kdpfactory produzione` ([`cowork.md`](cowork.md)).

| quando | chi scatta | come |
|---|---|---|
| l'autore chiede un libro nuovo | nessun agente: le **domande d'avvio** | `avvio <slug> --json`, poi le domande all'autore |
| arrivano la pagina del concorrente (`pagina.md` o la risposta di Cowork) e le parole chiave della nicchia | `scheda-concorrente` → `analista-recensioni` → `posizionamento` → `originalita` | subagent in fila: ognuno legge il lavoro del precedente |
| la scaletta è scritta o cambia | `indice`, poi `revisore-scaletta` | subagent, poi `manuale <slug> scaletta --esamina` |
| un capitolo è importato | nessuno: si continua a scrivere | — |
| il libro è impaginato (ogni `build`) | `impaginazione` | `review <slug> --agents impaginazione` |
| tutti i capitoli sono scritti e impaginati | `lettore-cieco` (libro), `editor-sviluppo`, `fact-checker` a blocchi di otto capitoli, `conformita` sul testo — **in parallelo**, perché i campi non si toccano | subagent in background |
| il livello è `alta` | in più `correttore`, capitolo per capitolo | subagent |
| le correzioni sono applicate | di nuovo `impaginazione`; e l'agente che aveva dato un bloccante, solo sui capitoli corretti, per verificare che sia chiuso | comando e subagent |
| la scheda è importata | `conformita` sulla scheda; Cowork, ruolo `parole-chiave`, verifica le sette frasi | subagent su `build/kdp-listing.md`; `parole-chiave <slug>` |
| la scheda è chiusa (fase 7) | `copertina`, le direzioni: legge lo studio della categoria e scrive le tre direzioni d'arte | `copertina <slug> --direzioni`, poi `--bozzetti --genera`; la scelta all'autore |
| l'autore ha scelto la direzione e l'impaginazione è definitiva | `copertina`, primo tempo: il prompt | `copertina <slug>` e `--genera` (e `immagini <slug>` se ci sono figure) |
| arrivano le varianti `assets/copertina-N.png` | `copertina`, secondo tempo: misura le varianti e propone la scelta all'autore | `copertina <slug> --scegli N` dopo il silenzio-assenso, poi `build` e `review <slug> --agents copertina` |
| prima di consegnare | `qa` e `diagnostica` | comandi |

Tre regole per la sessione che li chiama:

- **Un agente, il suo campo.** Il messaggio che lancia un agente gli chiede
  solo quello che la tabella delle competenze gli assegna, e al lettore cieco
  non passa niente oltre ai capitoli e alla vetrina.
- **Un agente che cade si rilancia.** Se si ferma per un limite d'uso o un
  errore, lo si rilancia quando il limite è passato: la sua competenza non la
  copre nessun altro, quindi saltarlo vuol dire lasciarla scoperta.
- **Si aspetta la fase intera** prima di correggere, e si riferisce all'autore
  quando la fase è chiusa, non a ogni agente che finisce.

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
A  avvio                        domande all'autore → pagina del concorrente     cancello: tutte le domande viste
0  acquisizione                 scheda-concorrente → analista-recensioni → posizionamento → originalita
1  progetto                     architetto → indice → revisore-scaletta          cancello: 0 bloccanti
2  stesura                      ghostwriter  (+ voce al livello alta)            cancello: il capitolo 1 ti convince
3  prima impaginazione          build → impaginazione                            cancello: pagine nell'intervallo
4  controllo del testo          lettore-cieco · editor-sviluppo · fact-checker · conformita  (+ correttore)
5  correzione                   editor → build                                   cancello: 0 bloccanti, 0 importanti aperti
6  scheda prodotto              scheda → conformita sulla scheda → vetrina       cancello: 0 bloccanti
7  copertina                    studio della categoria → copertina (tre direzioni) → bozzetti → scelta dell'autore
                                → copertina (prompt) → le varianti → copertina (misure)   cancello: 0 bloccanti
8  chiusura                     qa → checklist KDP                               cancello: 0 errori
```

In ogni fase qui sotto: chi lavora, che cosa entra, che cosa esce, come lo si
chiama nelle due linee, quando il cancello è chiuso.

### A · Avvio — le domande all'autore

Ogni libro nuovo nasce **contro un concorrente preciso**: un libro che vende
già nella nicchia, da battere dove i suoi lettori restano scontenti. Prima di
qualunque agente l'autore risponde a sette domande, sempre le stesse:

| domanda | risposte | se l'autore lascia decidere |
|---|---|---|
| il concorrente | l'ASIN o il link; oppure la nicchia, e il concorrente lo cerca Cowork fra i primi 20 | nessun default: senza concorrente non si parte |
| il mercato | amazon.com (inglese, USD), amazon.co.uk (inglese, GBP), amazon.it (italiano, EUR) | amazon.com |
| la categoria | come il concorrente, full-content, medium-content | come il concorrente: la propone il posizionamento, l'autore la conferma prima della scaletta |
| dove batterlo, nel libro | lacune delle recensioni, più pratico, contenuto migliore, lettore più preciso (anche più d'una) | lacune, più pratico, contenuto migliore |
| dove batterlo, in vetrina | copertina più attraente, prezzo più conveniente, tutte e due, nessuna | copertina più attraente |
| lo pseudonimo | uno nuovo, o uno già in uso su un libro della stessa area | uno nuovo, proposto col titolo |
| la pagina del concorrente | la scarica Cowork, la incolla l'autore | la scarica Cowork |

```bash
python3 -m kdpfactory avvio <slug> --json        # le domande ancora da fare
python3 -m kdpfactory avvio <slug> --concorrente B0… --mercato amazon.com \
    --categoria concorrente --vantaggi lacune,pratico --vetrina copertina \
    --pseudonimo nuovo --pagina cowork            # le risposte
python3 -m kdpfactory avvio <slug> --predefinite  # «fai tu»: il resto prende il default
```

- **Il concorrente si chiede nel messaggio**, non fra le opzioni: è un dato da
  scrivere, e un'opzione «ti do l'ASIN» viene scelta senza che l'ASIN arrivi.
  Le altre domande sono a scelta, a gruppi di quattro: `--json` le dà già
  pronte da porre.
- Le risposte stanno in `concorrente/avvio.json`. Una domanda non posta vale
  il suo default ma resta segnata come da chiedere, e il comando la ripropone.
- **Finite le domande**, il comando prepara la fase 0 da solo: il modulo
  `concorrente/pagina.md`, il file `concorrente/copertina.md` se l'autore vuole
  una copertina più attraente, e, se la pagina la porta Cowork, la richiesta
  `concorrente/cowork-concorrente.md` (o `cowork-nicchia.md`), sempre la stessa
  per ogni libro. Con l'ASIN scrive anche `concorrente/cowork-parole-chiave.md`:
  le parole chiave della nicchia, che Cowork cerca su Amazon, Helium 10,
  Publisher Rocket e Google Trends. Le richieste si pubblicano nello stesso giro.
- Da lì le risposte lavorano senza che nessuno le ripeta: il posizionamento le
  riceve come vincolo insieme a `indicazione.md`; `concorrente build` impone
  lingua, categoria scelta e pseudonimo anche se il piano dicesse altro; il
  brief di copertina riceve la descrizione della copertina da battere.

**Cancello:** tutte le domande viste, la pagina del concorrente arrivata e le
parole chiave della nicchia esplorate (una risposta parziale basta, se dice che
cosa manca).

### Prima di tutto: la categoria

Ogni libro è **full-content** (testo pieno, da leggere) oppure
**medium-content** (interattivo, ogni pagina diversa), e la categoria si
decide **prima della scaletta**: vincola impaginazione, indice, copertina,
scheda e prezzo. All'avvio l'autore la sceglie o la lascia al concorrente; in
quel caso la propone il posizionamento e l'autore la conferma. Si dichiara con `init --content-type full|medium` e resta in
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

Un libro che parla di soldi, salute o diritto ha bisogno anche di un'avvertenza
sua nella pagina di copyright: `disclaimer` in `book.json`, che dice di che
consulenza il libro non è e che le regole cambiano. Vuoto, vale quella generica,
uguale per tutti i libri. Lo chiede la conformità, e lo si scrive prima della
fase 8.

### 0 · Acquisizione — dalla pagina del concorrente al libro nuovo

| | |
|---|---|
| **Chi** | `scheda-concorrente` → `analista-recensioni` → `posizionamento` → `originalita` |
| **Entra** | la pagina del concorrente (`concorrente/pagina.md`, o la risposta di Cowork se il modulo è vuoto), i vincoli dell'avvio e le parole chiave della nicchia (`concorrente/cowork-parole-chiave-risposta.md`), da cui il posizionamento sceglie le sette frasi |
| **Esce** | `book.json` e `brief.md` del libro nuovo |
| **Comando** | con la chiave API `python3 -m kdpfactory concorrente build <slug>` ([`acquisizione.md`](acquisizione.md)) |
| **Linea manuale** | i quattro subagent in fila, ognuno legge i file del precedente; la sessione salva le risposte in `concorrente/scheda.json`, `lacune.json`, `piano.json`, `originalita.json`, poi `concorrente importa <slug>` |
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
- **le pagine previste stanno nell'intervallo**, parti comprese: il revisore
  le conta sulla scaletta con il modello tarato, perché il numero di capitoli
  e le parti li decide l'architetto dopo il budget, e ogni parte costa due
  pagine.

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
- **Ogni titolo stampato passa da lui.** Un capitolo aggiunto o rinominato dopo
  l'indice torna all'agente prima della stampa: `qa` confronta
  `manuale/indice.json` con i titoli stampati e lo dà come errore (`INDICE`),
  insieme ai rimandi interni che citano un titolo vecchio
  ([`standard-editoriale.md`](standard-editoriale.md), «L'indice, nei due sensi»).

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
| **Standard** | quello di un editore di saggistica: [`standard-editoriale.md`](standard-editoriale.md) |
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
| **Parole chiave** | `python3 -m kdpfactory parole-chiave <slug>` → richiesta a Cowork, ruolo `parole-chiave`: per ognuna delle sette frasi autocompletamento, risultati, Helium 10, Publisher Rocket; per ogni categoria il 1° e il 20° in classifica |
| **Cancello** | nessun bloccante della conformità; le sette frasi verificate |

Le sette frasi nascono dalla tabella che Cowork ha portato all'avvio, e prima
di caricare il libro si verificano di nuovo: una frase che l'autocompletamento
non propone più, o senza volume, si sostituisce con una della tabella, e la
sostituta passa dalla conformità.

Le parole chiave non contengono **nomi di altri autori, titoli di altri libri,
marchi o metodi registrati da terzi**, né parole che descrivono il libro in
modo falso; non ripetono parole del titolo, che Amazon indicizza già (la
diagnostica lo segnala). La descrizione usa solo i tag che KDP accetta — il
sistema la scrive così e un test lo verifica — e non promette risultati.

### 7 · Copertina

Un solo agente, dall'inizio alla fine: `copertina`. Le regole sono in
[`copertine.md`](copertine.md); qui c'è la sequenza. Si lavora come una casa
editrice: prima si guarda che cosa vende nella categoria, poi si propongono tre
direzioni d'arte, l'autore ne sceglie una sui bozzetti, e solo allora si spende
sulle varianti finali.

| | |
|---|---|
| **Chi** | Cowork studia le copertine della categoria; `copertina` scrive le tre direzioni e misura; il sistema scrive i prompt; **Higgsfield** genera bozzetti e varianti; l'autore sceglie la direzione (senza silenzio-assenso) e poi la variante (con) |
| **Entra** | i dati del libro: categoria, categorie KDP, promessa, pubblico, occhiello e gancio della scheda, pagine vere; lo studio della categoria (`concorrente/cowork-copertine-categoria-risposta.md`); la copertina del concorrente (`concorrente/copertina.md`), se all'avvio l'autore l'ha chiesta; le scelte dell'autore sui libri prima (`config/copertine-direzione.json`) |
| **Esce** | `copertina-direzioni.json`, `build/copertina-direzioni.md` e i bozzetti; poi `build/copertina-brief.md` (il prompt) e `build/<slug>-copertina.pdf` |
| **Come si chiama** | «usa copertina su <slug>» |
| **Cancello** | zero problemi nelle direzioni; la direzione scelta dall'autore; zero bloccanti delle misure; la miniatura supera le cinque domande |

**1. Lo studio della categoria.** `copertina <slug> --direzioni` apre a Cowork
(ruolo `concorrente`) la richiesta delle prime dieci copertine della
categoria, descritte a parole: colori, tipo d'immagine, posizione e carattere
del titolo, quanti elementi, che cosa le accomuna e che cosa non fa nessuna. Per
un libro nuovo parte già con le domande d'avvio.

**2. Le tre direzioni.** L'agente `copertina` le scrive in
`books/<slug>/copertina-direzioni.json` sul modello che lo stesso comando
lascia: per ciascuna idea, soggetto, al massimo tre elementi, resa, luce,
palette del motore, composizione (titolo in alto o al centro), voce tipografica,
perché venderebbe e come si distingue restando nel genere. Rilanciato,
`copertina <slug> --direzioni` le controlla — tre, complete, diverse fra loro,
senza testo né imitazioni — e scrive i prompt dei bozzetti e il riepilogo per
l'autore (`build/copertina-direzioni.md`).

**3. I bozzetti e la scelta.** `copertina <slug> --bozzetti --genera` fa un
bozzetto per direzione alla risoluzione più bassa, con lo stesso prompt delle
varianti finali. La direzione la sceglie l'autore guardandoli, e **non passa dal
silenzio-assenso**: `copertina <slug> --direzione N --perche "…"` scrive in
`book.json` palette, composizione e carattere, e la ricorda in
`config/copertine-direzione.json` per i libri dopo.

**4. Le varianti finali.** Dopo l'ultima impaginazione, perché dorso e misure
dipendono dalle pagine:

```bash
python3 -m kdpfactory build <slug>
python3 -m kdpfactory copertina <slug>            # build/copertina-brief.md
python3 -m kdpfactory copertina <slug> --genera   # tre varianti della direzione scelta
python3 -m kdpfactory immagini <slug>             # se il manoscritto dichiara figure
```

Il brief **non si riscrive a mano**. Se qualcosa non va si corregge il dato da
cui nasce — la direzione, `cover_hook`, `categories`, `cover_theme`… — e si
rigenera. `--genera` manda a Higgsfield un prompt per variante, nato dalla
direzione scelta, con una composizione diversa per ognuna, alla risoluzione più
alta del modello; le varianti si numerano dopo quelle che ci sono già, che
restano. Senza Higgsfield, in ChatGPT si incolla `build/copertina-prompt.txt`.
Torna **solo l'illustrazione della prima**, senza testo, almeno 1800 × 2700 px
per un 6x9. La variante la sceglie l'autore con il silenzio-assenso, e
`copertina <slug> --scegli N` la porta in `assets/copertina.jpg`. Il testo lo
compone il motore, sempre, in vettoriale: è l'unico modo di misurarlo.

**5. Le misure.**

```bash
python3 -m kdpfactory build <slug>
python3 -m kdpfactory review <slug> --agents copertina
```

Corpo del titolo in miniatura (almeno 6% dell'altezza, dominante dall'8,5%),
contrasto almeno 7:1 sul fondo e 4,5:1 sull'immagine che il titolo ha dietro,
sfondo calmo dove sta il titolo, testo a 1 cm dal taglio, due famiglie di
caratteri, titolo in alto o al centro, stacco su fondo bianco, area di
sicurezza, dorso, area del codice a barre, font incorporati, autore uguale alla
scheda, nessuna dominante giallo-senape. Poi la miniatura a occhio, in
quest'ordine: si capisce la categoria in due secondi? L'immagine mostra il
soggetto vero? Un solo concetto dominante? Il titolo vince? Sembra una
copertina di quest'anno? E c'è un elemento generato difettoso — un oggetto
deformato, segni che sembrano lettere? Se c'è, la variante non si usa.

### 8 · Chiusura

```bash
python3 -m kdpfactory qa <slug>
python3 -m kdpfactory review <slug> --agents impaginazione,copertina
python3 -m kdpfactory diagnostica
```

Il cancello è **zero errori** del controllo qualità, che comprende la
corrispondenza fra indice e capitoli nei due sensi (`INDICE`). Poi
[`checklist-kdp.md`](checklist-kdp.md): caricare l'interno, la copertina
generata **dopo** l'impaginazione finale, compilare la scheda da
`kdp-listing.md`, dichiarare l'uso dell'IA, controllare l'anteprima di stampa,
ordinare una copia di prova: i colori della copertina si giudicano anche stampati,
non solo a schermo (video A, 13:53).

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
| studio | Cowork | le prime dieci copertine della categoria, a parole |
| direzioni | `copertina` | tre direzioni d'arte in `copertina-direzioni.json`; il sistema le controlla e ne scrive i prompt |
| bozzetti | Higgsfield | uno per direzione, a bassa risoluzione, dal prompt del sistema |
| scelta | autore | la direzione, senza silenzio-assenso; poi la variante, con |
| prompt | `copertina` | `kdpfactory copertina <slug>`; verifica dei sette punti; correzioni sui dati, mai sul brief |
| immagine | Higgsfield | tre varianti della direzione scelta; torna l'illustrazione della prima, senza testo |
| composizione | motore | `build`: ritaglio, 300 DPI, velatura misurata, titolo in vettoriale col contorno, dorso, retro |
| misure | `copertina` | `review --agents copertina`; la miniatura a occhio |

Il titolo si compone nel condensato del progetto quando il sans non basta a
renderlo dominante ([`copertine.md`](copertine.md)); le cifre stampate in
copertina sono solo quelle contate sul libro (medium-content) o nessuna
(full-content).

---

## Quello che decide l'autore

Nessun agente decide queste cose, e nessun cancello le sostituisce:

- **il concorrente** da battere, il **mercato** e dove batterlo: le domande
  d'avvio;
- **la categoria** (full o medium) e il **tipo di libro**;
- **il titolo** e il sottotitolo, e se tenerli quando un agente li contesta;
- **la promessa** e la **linea editoriale** (`notes` di `book.json`);
- **chi racconta**: se il libro presenta casi reali, composti o inventati, e
  come lo dichiara al lettore;
- **il prezzo**;
- **la direzione d'arte della copertina**: il sistema scrive i prompt dalle tre
  direzioni dell'agente, Higgsfield genera i bozzetti, l'autore sceglie — senza
  silenzio-assenso; poi, fra le varianti della direzione scelta, la variante;
- **la pubblicazione**, dopo aver letto il libro.

Quando un agente tocca una di queste, la segnala come domanda, non la risolve.
La sessione la registra con la proposta degli agenti e le alternative
(`decisioni <slug> --proponi …`) e manda la notifica all'autore: se entro 24
ore non risponde, vale la proposta (**silenzio-assenso**). La sua risposta,
quando arriva, vince sempre. Non passano dal silenzio-assenso la
pubblicazione e la direzione d'arte della copertina: la prima è sua per
definizione, la seconda l'ha voluta vedere lui (7 ottobre 2026).

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
| progettato per 120 pagine, impaginato in 184: la taratura stimava 592 parole per pagina piena contro 355 vere, e le parti non erano nel conto | 1, `revisore-scaletta` | la taratura usa sezioni di lunghezza diversa e un budget che regge il ±5% di testo; le pagine si ricontano sulla scaletta |
| il revisore bloccava «secure» come promessa di guarigione e contava «due» come numero in un libro inglese | 1, `revisore-scaletta` | parole intere, cifre nella lingua del libro |
| 47 capoversi con l'ultima riga di poche lettere, e il rilievo dava solo i numeri di pagina | 5, `impaginazione` | il rilievo cita ogni capoverso con le sue ultime parole: si ritrova nel manoscritto e si accorcia di una parola |
| «Here is an example» in 26 capitoli su 27: la nota sulla voce in `book.json` citava la formula, e ogni ghostwriter l'ha usata | 2, `editor-sviluppo` | la voce dice che gli esempi non sono casi reali; lo dichiara l'introduzione una volta, e i personaggi entrano con il nome |
| il sottotitolo prometteva «Catching Up When You Fall Behind» e nessun capitolo mostrava il rientro | 4, `lettore-cieco` | ogni promessa del sottotitolo ha un capitolo che la mantiene; se manca, si scrive prima della scheda |
| il brief di copertina chiedeva 1800 x 2700 px, il motore ritaglia la prima con l'abbondanza: l'immagine usciva a 291 DPI | 7, `copertina` | i pixel si chiedono sull'area che il motore ritaglia davvero |
| un libro sulle bollette di casa riceveva la rappresentazione «business»: il mondo professionale, cioè un ufficio | 7, `copertina` | la finanza di casa ha la sua voce: una cucina la sera, non un ufficio |
| la diagnostica chiedeva la terza categoria come rilievo alto; due volte se n'è cercata una di riempimento, e due volte la conformità l'ha tolta | 6, `conformita` | una categoria sola è un buco; con due, la terza entra solo se descrive l'argomento del libro |
| fra le opzioni l'autore ha scelto «ti do l'ASIN», e l'ASIN non è arrivato | A, avvio | il concorrente si chiede nel messaggio; a scelta solo le domande che hanno risposte fisse |
| le domande d'avvio esistevano solo nella chat di un libro: il successivo sarebbe partito senza | A, avvio | le sette domande stanno nel sistema (`avvio`), e le risposte arrivano da sole a posizionamento, scheda e copertina |
| le parole chiave di Bills in Order le aveva inventate il posizionamento, e Cowork ne ha trovate sei su sette da rifare | A e 6, `parole-chiave` | all'avvio Cowork cerca le parole chiave della nicchia e il posizionamento sceglie da lì; alla scheda le sette scelte si verificano |
| una richiesta a Cowork mescolava pagina del concorrente, KDP e parole chiave: un solo accesso mancante la lasciava parziale tutta | canale Cowork | un ruolo per richiesta; le richieste che mescolano si dividono |
| da quattro giorni nessuna risposta di Cowork: il push da GitHub Desktop lo faceva l'autore, e quando non c'era il canale restava fermo | canale Cowork | il corriere su Drive, che Cowork e la fabbrica raggiungono da soli; GitHub resta l'archivio |
| un libro in automatico si sarebbe fermato sei volte ad aspettare l'autore | tutte | silenzio-assenso a 24 ore per le decisioni dell'autore; la pubblicazione resta fuori |
| quattro risposte su sei parziali per accessi non aperti nel browser di Cowork (ChatGPT, KDP, Helium 10, Amazon): un seguito uguale sarebbe tornato parziale a ogni giro | canale Cowork | la riga `Serve:` nel seguito: Cowork aspetta l'accesso senza rispondere, `produzione` dice che lo deve aprire l'autore |
| il testo in un clone del Times, i titoli in un clone dell'Arial, la pagina 1 sull'occhiello: il libro sembrava fatto in casa | 3, motore | una famiglia da libro sola (EB Garamond) nel testo pieno, numerazione dalla prima pagina del testo ([`standard-editoriale.md`](standard-editoriale.md)) |
| 32 pagine su 192 finivano a metà gabbia: un titoletto si portava dietro il capoverso intero | 3, `impaginazione` | il titoletto chiede due righe sotto di sé, non il capoverso; le pagine corte si contano a ogni build |
| un capitolo aggiunto dopo l'indice non era mai passato dall'agente `indice`, e introduzione e conclusione lo citavano per nome | 1 e 8, `indice` e `qa` | `qa` confronta i titoli decisi con quelli stampati e i rimandi interni con l'indice |
| il prompt di copertina da incollare era il brief intero, con dorso, codice a barre e specifiche di stampa | 7, `copertina` | per ChatGPT un testo da incollare con solo quello che decide l'immagine; il brief completo resta il riferimento |

# NEXTUP — stato del sistema

Documento di passaggio di consegne. Descrive **esattamente** che cosa esiste, come
funziona e perché è stato fatto così. Da incollare in una nuova finestra di contesto.

Aggiornato al 18 settembre 2026 · branch `claude/dreamy-archimedes-hf8w45` · ultimo
commit `4b30066` · 170 test verdi, lint pulito, tutto committato e spinto.

---

## 1. Che cos'è

Un sistema per **vendere libri creati con l'IA su Amazon KDP**. Non un generatore
di testo: una catena di produzione che arriva al file caricabile — interno PDF,
copertina full-wrap, EPUB, scheda prodotto — con i controlli che impediscono di
pubblicare un libro difettoso.

Vincolo di progetto: **ogni libro esce fra 60 e 240 pagine**, con un obiettivo
scelto dall'autore e centrato entro il ±5%. Non è una stima: la pipeline impagina
davvero, conta le pagine del PDF, ricalcola il budget di parole e fa riscrivere i
capitoli finché il libro non rientra. *(La linea enigmistica non ha questo ciclo:
vedi §8.)*

Secondo vincolo, sulla forma: **ogni capitolo sta fra 1.500 e 2.000 parole**. È il
metro con cui si generano i libri, e a doversi adattare è il numero di capitoli,
non la lunghezza del capitolo. Introduzione e conclusione fanno eccezione per
scelta: pesano meno di un capitolo pieno.

### Le due categorie di prodotto

Ogni libro è **medium-content** oppure **full-content**. La categoria si decide
prima della scaletta e vincola impaginazione, scheda, categorie KDP e prezzo.
La definizione completa, con i confini, sta in `CLAUDE.md`.

| | medium-content | full-content |
|---|---|---|
| che cos'è | libro interattivo cartaceo: ogni pagina ha contenuti, layout o stimoli **differenti** — esercizi guidati, schede pratiche, domande di riflessione, griglie operative | opera a **testo pieno** per Kindle e cartaceo: narrazione continuativa o divulgazione manualistica approfondita |
| dove sta il valore | nella progettazione della pagina e nella varietà degli stimoli | nella sostanza del testo originale, nell'articolazione dei capitoli, nella densità concettuale |
| confine da non passare | **non low-content**: niente blocchi di pagine vuote o righe ripetitive. Se due pagine si scambiano senza che cambi niente, è un quaderno | **niente pagine da compilare**, nessuno schema interattivo vuoto |
| nel sistema di oggi | solo la linea `puzzle`, che è un medium-content **specifico** (enigmi di deduzione) | la linea prosa: `all` / `outline` → `write` → `build` |

La categoria sta in `book.json` come `content_type` (`full` | `medium`), si
sceglie con `init --content-type`, e i due confini sono controllati:

| confine | dove | come |
|---|---|---|
| un full-content non ha pagine da compilare | `qa.py` | conta le righe fatte di trattini bassi o puntini di guida nel manoscritto |
| un medium-content non scivola nel low-content | `agents/layout.py` | firma strutturale di ogni pagina del PDF: se più della metà delle pagine ha la stessa struttura, lo segnala |

Misurato su un libro di enigmi da dodici casi: 75 pagine di testo, **35
strutture diverse**, la più ripetuta copre il 16% (sono le pagine di appunti,
una per caso).

La linea enigmistica è ora il **motore** della categoria, non un prodotto:
l'ambientazione — dove si svolge, chi ci abita, i testi dei casi, l'esempio, il
finale, la scheda — è un dato del libro (`books/<slug>/ambientazione.json`), non
codice. Il sistema non contiene nessun libro.

### Regole permanenti (valgono in ogni sessione)

| regola | dettaglio |
|---|---|
| **Branch** | sviluppare, committare e spingere **solo** su `claude/dreamy-archimedes-hf8w45`. Mai un altro branch senza permesso esplicito. |
| **Nessuna PR** | non aprire pull request se non richiesta esplicitamente. |
| **Backup** | ogni file generato deve avere una copia di sicurezza. La pipeline lo fa da sé (`kdpfactory/backup.py`); i file generati a mano vanno copiati in `backup/manuale/<AAAAMMGG-hhmmss>/` mantenendo i percorsi relativi. `backup/` non entra in git. Regola scritta in `CLAUDE.md`. |
| **Lingua** | codice, commenti, documentazione, messaggi e nomi in **italiano**. Il testo dei libri può essere in qualunque lingua. |
| **Attribuzione** | i commit finiscono con `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>` e `Claude-Session: <url>`. Mai identificativi di modello dentro codice, commenti o altri artefatti del repo. |

---

## 2. Struttura

```
NEXTUP/
├── CLAUDE.md                    regola dei backup + orientamento (governa le sessioni future)
├── SISTEMA.md                   questo file
├── .claude/
│   ├── agents/                  21 subagent: 16 del collegio (4 di acquisizione) + 5 del team
│   └── commands/migliora.md     comando /migliora
├── backup/                      copie di sicurezza (fuori da git)
└── kdp-book-factory/
    ├── kdpfactory/              il codice
    ├── books/<slug>/            book.json, brief.md, assets/, manuscript/, build/, state.json
    ├── config/printing_costs.json
    ├── docs/                    documentazione (vedi sotto)
    ├── tests/                   216 test, nessuna chiamata di rete
    └── fonts/                   font TrueType propri (facoltativo)
```

**Documentazione già scritta** (leggerla invece di ricostruire il ragionamento):
`docs/agenti.md`, `docs/checklist-kdp.md`, `docs/copertine.md`,
`docs/acquisizione.md`, `docs/enigmistica.md`, `docs/materiali.md`,
`docs/personalizzazione.md`,
`docs/team-miglioramento.md`, `docs/workflow.md`, più `README.md`.

**Comandi:**
```bash
cd kdp-book-factory
python3 -m unittest discover -s tests     # 216 test, nessuna rete
ruff check kdpfactory tests
python3 -m kdpfactory --dry-run all <slug>   # prova senza spendere token
```

---

## 3. I moduli

| modulo | che cosa fa |
|---|---|
| `kdpspecs.py` | specifiche KDP: formati, margini, dorso, limiti. `PROJECT_MIN_PAGES=60`, `PROJECT_MAX_PAGES=240` |
| `models.py` | `BookSpec`, `ChapterPlan`, `Outline`, `BookProject`, `state.json` |
| `planner.py` | pagine → parole, da metriche reali del font; capitoli fra 1.500 e 2.000 parole; ricalibrazione a posteriori |
| `prompts.py` | tutto il testo mandato al modello: `AUTHOR_RULES`, `BANNED_OPENERS`, `book_bible()`; il contesto per capitolo tenuto a budget (`focus_covered`) |
| `llm.py` | client Claude: streaming, cache del prefisso, conteggio token e costi, dry-run |
| `writer.py` | scaletta, capitoli, continuità, revisioni di lunghezza |
| `typeset.py` | interno PDF (ReportLab Platypus) |
| `cover.py` | copertina full-wrap: quarta + dorso + prima |
| `coverdesign.py` | **sistema** di copertina: regole, palette, testi, verifica |
| `coverart.py` | **illustrazioni vettoriali** della prima |
| `coverimage.py` | preparazione di una foto fornita dall'autore (300 DPI, velatura) |
| `epub.py` | EPUB 3 senza dipendenze esterne |
| `metadata.py` | scheda prodotto, prezzi, royalty |
| `qa.py` | controlli di qualità e conformità |
| `diagnostica.py` | **misure su tutti i libri**: i fatti per il team di miglioramento |
| `backup.py` | snapshot datati, ripristino, pulizia |
| `agents/` | collegio editoriale dentro la pipeline, reparto di acquisizione compreso |
| `concorrente.py` | **da un ASIN a un libro**: scheda Amazon incollata → `book.json` + `brief.md` |
| `puzzle/` | seconda linea: enigmi di deduzione, senza chiamate API |
| `pipeline.py` | orchestrazione e convergenza sulle pagine |
| `typography.py`, `i18n.py`, `mdlite.py` | font, etichette it/en, parser Markdown ridotto |

---

## 4. Vincoli KDP codificati

In `kdpspecs.py`, verificati contro il modulo di caricamento reale:

- **14 formati** di rifilo: `5x8`, `5.25x8`, `5.5x8.5`, `6x9`, `6.14x9.21`, `7x10`,
  `8.5x11`…
- **Dorso** = pagine × fattore carta: `white 0.002252`, `cream 0.0025`,
  `color-standard 0.002252`, `color-premium 0.002347`
- **Abbondanza** 0.125" su tre lati; totale copertina +0.25" in altezza
- **Margine interno** crescente col numero di pagine (`GUTTER_TABLE`)
- **Margine esterno** ≥ 0.25" senza abbondanza, ≥ 0.375" con
- **Testo sul dorso** ammesso solo da **79 pagine** in su
- **Area codice a barre** 2.0"×1.2" in basso a destra della quarta, da lasciare libera
- **Tutti i font incorporati**: obbligatorio, e in questo progetto è già costato tre
  difetti separati (§7)
- Numero di pagine **pari**, capitoli in apertura di pagina **dispari**

---

## 5. Le quattro parti del sistema

### 5.1 Pipeline in prosa + collegio editoriale

Un libro passa da una redazione, non da un prompt lungo.

```
architetto → indice → ghostwriter → [voce] → impaginazione + copertina
                                                 │
      lettore cieco (capitolo) ┐                 │
      fact-checker             ├─ segnalazioni ──┤
      conformità               │                 │
      correttore               │                 │
      lettore cieco (libro)    │                 ▼
      editor di sviluppo       →            editor  →  nuova impaginazione
```

**12 agenti registrati** in `kdpfactory/agents/` (`REGISTRY`):

| agente | ruolo | note |
|---|---|---|
| `architetto` | produzione | progetta la scaletta |
| `indice` | produzione | i titoli definitivi dei capitoli: la pagina dell'anteprima |
| `ghostwriter` | produzione | scrive i capitoli |
| `voce` | produzione | line editing: ritmo, tic da testo generato |
| `editor` | produzione | **l'unico che tocca il testo** |
| `lettore-cieco` | controllo | `blind=True`: non riceve né scaletta né scheda del libro. Sul capitolo dice dove ci si perde; sul libro intero riceve **l'indice** e verifica che sia mantenuto |
| `fact-checker` | controllo | affermazioni non verificabili |
| `conformita` | controllo | regole di contenuto KDP e rischi legali |
| `correttore` | controllo | bozze |
| `editor-sviluppo` | controllo | il libro nel suo insieme |
| `impaginazione` | controllo | **deterministico**: misura le coordinate nel PDF |
| `copertina` | controllo | **deterministico**: misura la prima + i testi |

Separazione fondamentale: **i revisori segnalano, solo l'editor modifica**. È la
struttura di una redazione e serve a evitare che ogni passaggio riscriva il libro
a modo suo.

**Livelli di lavorazione** (`--qualita`):
- `bozza` — solo stesura, nessuna revisione
- `standard` *(default)* — lettore cieco, fact-checker, conformità, editor di
  sviluppo, impaginazione, copertina. L'editor applica bloccanti e importanti
- `alta` — in più la passata di stile e il correttore; l'editor applica tutto

Dopo l'editor il libro viene **rimpaginato**: l'editing cambia le parole, e le
parole decidono le pagine.

**Convergenza sulle pagine**: stima da geometria e metriche del font → impaginato
vero → parole/pagina misurate → nuovo budget (limitato a ±45%) → riscritture
mirate → ripete. **Oggi non converge**: vedi §8.

**Contesto di chi scrive**: il blocco stabile (regole d'autore + scheda del libro
con la struttura completa) va in cache; il messaggio del capitolo no, e si
ricompra ogni volta. L'elenco di quello che è già stato detto è perciò tenuto a
budget (`prompts.COVERED_BUDGET_WORDS`, 350 parole, minimo tre capitoli): si
tengono i riassunti recenti, che sono quelli da cui ci si ripete, e i più
lontani restano nella struttura completa, che è già nel blocco in cache. Su un
libro corto non cambia niente; da 18 capitoli in su **il contesto per capitolo
smette di crescere**.

### 5.2 Linea enigmistica (`kdpfactory/puzzle/`)

Libri di enigmi di deduzione che si **dimostrano** corretti e **non chiamano
nessun modello**. Stesso seme, stesso libro.

- `model.py` — sospetti come prodotto cartesiano di 6 attributi; **9 tipi di
  indizio**: `Is`, `IsNot`, `OneOf`, `IfThen`, `NotBoth`, `SameAs`,
  `DiffersFrom`, `Cleared`, `ExactlyOneTrue`
- `solver.py` — dimostra **unicità** (una sola soluzione) e **necessità**
  (nessun indizio si può togliere senza romperla), più la traccia di eliminazione
- `generator.py` — selezione greedy degli indizi puntando a ~38% di eliminazione
  per indizio, con varietà decrescente per non ripetere lo stesso tipo
- `theme.py` — l'ambientazione: espresso notturno anni Trenta, 122 cognomi,
  10 titoli nobiliari/professionali, 12 casi con cast da 24 a 120 sospetti
- `layout.py` — impaginazione: tabelle del cast, griglia del finale, esempio
  svolto, soluzioni passo passo, pagina di appunti per ogni caso
- `book.py` — `build()` e `check()`: dal seme al pacchetto completo

**Meccanica**: 12 casi indipendenti + un **13° finale** che si può risolvere solo
avendo in mano tutte e dodici le risposte.

**L'ambientazione è un dato, non codice.** `theme.py` contiene il motore — la
forma di un caso, i livelli di difficoltà, la forma di un attributo — e carica
il resto da `books/<slug>/ambientazione.json`: titolo, luogo, attributi dei
sospetti, cognomi, i testi dei casi, l'esempio svolto, il finale, la scheda
prodotto e i testi di copertina. `puzzle new` lascia il file da compilare, come
`init` lascia `brief.md`.

Requisiti del finale e copertura dei casi **scalano col libro**: erano tarati su
dodici casi e su un libro più corto erano irraggiungibili.

### 5.3 Sistema di copertina

Principio: su Amazon la copertina si vede **larga 160 pixel**, su fondo bianco,
in mezzo ad altre venti, per meno di un secondo. Quello che non sopravvive a
quella miniatura non esiste. Documentato per esteso in `docs/copertine.md`.

**Sette regole misurabili** (`coverdesign.py`):

| # | regola | soglia |
|---|---|---|
| 1 | un solo elemento dominante | max 4 blocchi di testo nella metà alta (`MAX_TOP_ELEMENTS`) |
| 2 | titolo leggibile in miniatura | maiuscole ≥ 6% dell'altezza (`MIN_TITLE_CAP_RATIO`), bene a 8,5% (`GOOD_TITLE_CAP_RATIO`), max 3 righe (`MAX_TITLE_LINES`) |
| 3 | contrasto reale | titolo/fondo ≥ 7:1, soglia AAA (`MIN_CONTRAST`) |
| 4 | stacco dal bianco | fondo ≥ 3:1 contro il bianco |
| 5 | un'immagine che dice di che libro si tratta | un solo punto in accento |
| 6 | un ciclo aperto | una domanda o una promessa incompleta (Zeigarnik) |
| 7 | numeri in cifre | «13 CASES · 908 SUSPECTS», non «tredici casi» |

**Mai**: finti timbri di bestseller, stelline, premi o recensioni. Vietati da KDP
e comunque portano resi. L'agente `copertina` li blocca (`BANNED_CLAIMS`).

**Testi della prima** (`CoverCopy`): `kicker` (occhiello di genere), `title`,
`hook` (il ciclo aperto), `stats` (numeri in cifre), `badge` (una garanzia vera),
`author`, `subject` (serve a scegliere l'illustrazione). Il **sottotitolo completo
non va in copertina**: in miniatura non si legge e ruba spazio al titolo.
Sovrascrivibili da `metadata.json` con `cover_kicker`, `cover_hook`,
`cover_stats`, `cover_badge`.

**Sei palette** (`PALETTES`), tutte oltre 7:1 e tutte che staccano dal bianco:
`notturno` (nero-blu/giallo), `allarme` (nero/rosso), `inchiostro`
(blu notte/verde acqua), `bosco`, `terracotta`, `indaco`. `cover_theme` in
`book.json`; con `auto` la sceglie il sistema in modo stabile (dipende dal titolo).

**Sei illustrazioni vettoriali** (`coverart.py`), disegnate dalla pipeline e non
cercate — costano zero, sono nitide a qualunque risoluzione (KDP non le contesta
mai per i DPI), nascono nei colori della palette e non hanno diritti da pagare:

| nome | scena | il punto in accento |
|---|---|---|
| `treno` | espresso notturno di fianco | la finestra accesa |
| `lente` | lente su una griglia di indizi | l'unico indizio che conta |
| `elenco` | sospetti barrati | l'unico nome in piedi |
| `orologio` | quadrante con uno spicchio | le ore restituite |
| `scala` | gradini che salgono | l'ultimo gradino |
| `porta` | porta socchiusa | la luce che ne esce |

Scelta: `cover_art` in `book.json` → parole chiave di titolo/sottotitolo/argomento/
promessa (a parità vince la scena più **concreta**) → riserva di genere
(`enigmi`→`elenco`, `non-fiction`→`scala`, `fiction`→`porta`). Con una foto
dell'autore in `assets/` **non si disegna niente**: la foto è già l'elemento
dominante e un secondo segno romperebbe la regola 1.

**Verifica a ogni build**: `state.json` → `cover.verifica` con tutte le misure, e
`build/<slug>-copertina-miniatura.png` a 160 px — **è lì che si giudica una
copertina, non nel PDF a schermo intero**.

Le misure di copertina si leggono in `state.json` → `cover.verifica` dopo ogni
`build`, e la miniatura a 160 px sta in `build/<slug>-copertina-miniatura.png`.

### 5.4 Team di miglioramento

Cinque agenti che non producono libri: migliorano il **sistema** che li produce.
Stanno in `.claude/agents/` (non nella pipeline). Documentati in
`docs/team-miglioramento.md`.

**Prima le misure.** `python3 -m kdpfactory diagnostica` (in `diagnostica.py`, non
usa il modello) produce `diagnostica.json` con:

- **economia** — costo API per libro, token, costo di stampa, prezzo, royalty per
  copia, **quante copie servono per ripagare la produzione**
- **produzione** — iterazioni di impaginazione, parole/pagina misurate contro
  stimate, scarto dalle pagine obiettivo
- **qualità** — errori e avvisi rimasti sul libro finito, per codice
- **scheda** — i limiti veri di KDP: **7 slot** di parole chiave da **50 caratteri**,
  **3 categorie**, **4000 caratteri** di descrizione, i **185** prima di «Leggi di
  più», troncamento del titolo a **60**. Più gli sprechi misurabili: una parola
  chiave che ripete una parola già nel titolo è uno slot buttato, perché il titolo
  è indicizzato di suo
- **copertina** — le misure di `cover.verifica`
- **sistema** — i difetti che compaiono in **più libri** (`ricorrenze`) e il
  rapporto righe di codice / righe di test

Un difetto su un libro è del libro; lo stesso difetto su tre libri è della
pipeline, e si corregge una volta sola.

**Gli agenti:**

| agente | compito | consegna |
|---|---|---|
| `capo-collana` | guida, ordina per effetto sulle vendite, arbitra | **tre** cose da fare adesso, il resto in ordine, le scartate col motivo |
| `analista-mercato` | perché il libro non viene comprato | il testo sostitutivo **già scritto** |
| `ingegnere-pipeline` | difetti del codice per gravità **sul libro stampato** | la patch + come riprodurre il difetto |
| `economo` | costo per libro e copie per ripagarlo | il conto prima/dopo, col rischio |
| `avvocato-del-diavolo` | smonta le proposte prima che diventino lavoro | regge / con riserva / non regge |

**Nessuno dei cinque ha `Edit` o `Write`.** Il vincolo «propone, non applica» sta
nella lista degli strumenti, non in una raccomandazione che un agente può
interpretare male. L'avvocato del diavolo non ha proposte proprie: è lo stesso
principio del lettore cieco, applicato alle proposte invece che al testo.

Si usa con `/migliora` (o `/migliora <slug>`, `/migliora scheda`,
`/migliora codice`): misure → tre analisi in parallelo → verifica → piano → si
ferma e chiede che cosa applicare.

**Il team non ha** dati di vendita reali, classifiche o volumi di ricerca. Può
dire «questo slot è vuoto» perché lo vede; non «questa parola chiave porta
traffico». Le decisioni che li richiedono finiscono in una sezione apposta.

---

## 6. Gerarchia dei difetti

Usata da tutto il sistema per ordinare le priorità, dal più grave:

1. **Arriva alla stampa** — font non incorporati, margini sbagliati, testo
   tagliato dalla rifilatura, copertina fuori misura. Costano una ristampa.
2. **Arriva al lettore** — righe vedove, capitoli sulla pagina sbagliata.
   Diventano recensioni a tre stelle.
3. **Blocca la produzione** — costa tempo e token.
4. **Sporca il codice** — conta solo se rallenta una delle tre sopra, e va detto
   quale.

---

## 7. Difetti già trovati e risolti — NON riscoprirli

Sono costati tempo. Chi riprende il lavoro dovrebbe conoscerli.

**Stato grafico condiviso di ReportLab.** È la famiglia di bug più insidiosa del
progetto, e ne ha prodotti due veri:

- La **spaziatura fra i caratteri** (`Tc`) fa parte dello stato grafico della
  *pagina*, non del blocco di testo. Non riazzerandola, ogni riga disegnata dopo
  un testo tracciato usciva più larga del previsto — il titolo di copertina usciva
  26 pt più largo e ReportLab lo centrava senza saperlo, spingendolo **fuori
  dall'area di sicurezza**. Risolto con `setCharSpace(0)` in coda al text object,
  sia in `coverdesign._tracked` sia in `typeset.draw_tracked_string`.
- La **trasparenza** faceva lo stesso. Risolto isolando ogni illustrazione in
  `saveState`/`restoreState` dentro `coverart.draw`.

Regola: ogni `set*` sul canvas che non viene riazzerato o isolato è un sospetto.

**Font non incorporati — tre sorgenti separate**, tutte e tre necessarie:
il font di default del canvas (`set_default_canvas_font`), il `bulletFontName`
degli elenchi, e le celle delle `Table` di indice ed enigmi
(`("FONTNAME", (0,0), (-1,-1), font)`).

**Altri, già sistemati:**
- `ActionFlowable` va importato da `reportlab.platypus`
- `handle_pageBreak` aggancia l'inizio pagina: la condizione per aprire i capitoli
  su pagina dispari è `if doc.page % 2 == 1`
- I `Frame` di ReportLab aggiungono 6 pt di padding: azzerato, altrimenti i
  margini reali non corrispondono a quelli dichiarati
- Falsi positivi dell'agente di impaginazione: elenchi puntati scambiati per
  aperture di capoverso, colonne di tabella per rientri (`MAX_INDENT=40`),
  tabelle contate come prosa, corpo del testo misurato sulle celle
- I test scrivevano nella cartella `backup/` vera: `backup.configure(enabled=False)`
  nel `setUp`
- Il centro ottico della prima è quello dell'**area rifilata**, non della pagina
  con l'abbondanza (che sta solo sul taglio esterno)
- La garanzia veniva stampata **sopra** la banda dei numeri: il piede è ora una
  pila misurata prima di disegnarla
- La miniatura inquadrava l'abbondanza invece dell'area rifilata
- `fit_size` e `title_block_size` scendevano sotto la soglia di leggibilità: il
  minimo è ora un pavimento vero (`max(minimum, size - passo)`)

**Rete:** l'accesso ad Amazon è bloccato in questo ambiente (curl 403, WebFetch
`EGRESS_BLOCKED` su amazon.it/.com e kdp.amazon.com). Un ASIN si può identificare
solo via ricerca web. Non promettere dati di vendita che non si possono prendere.

---

## 8. Stato attuale

**Libri:**

| slug | stato |
|---|---|
| `collaudo` | **non è un libro**: è il bersaglio delle prove a secco e della diagnostica. Dichiaratamente vuoto di contenuto, così non c'è mai niente da ripulire |

Il sistema non contiene nessun libro pubblicabile: è una fabbrica. Un libro si
crea con `init`, con `concorrente new` (da un'analisi di mercato) o con
`puzzle new`.

**Test: 216**, nessuna chiamata di rete.

**Rilievi aperti** sul sistema (non su un libro: non ce ne sono):

- **3 moduli mai nominati nei test**: `agents/panel.py`, `agents/writing.py`,
  `i18n.py`. `panel.py` è il più serio: `apply_revisions` riscrive i capitoli
  sul posto e l'unica difesa contro un capitolo mutilato è una soglia non
  coperta da test
- il **ciclo di impaginazione non converge** quando i capitoli sono molti: ora
  si ferma da sé invece di insistere, ma la causa — tutti i capitoli scalati
  dello stesso fattore, che scavallano insieme — resta
- i **fattori di riempimento** di `planner.py` restano intoccati: le misure
  disponibili oscillano del 12% sullo stesso libro e vengono da testo
  segnaposto. Servirebbe un libro scritto davvero
- i **costi di stampa** in `config/printing_costs.json` sono dichiarati
  `DA VERIFICARE`: ogni royalty del sistema poggia su quel file

**Il passo successivo naturale** è `/migliora`, che prende in mano esattamente
questi rilievi. È un comando autosufficiente: legge `diagnostica.json` e il repo,
non ha bisogno della cronologia di nessuna conversazione.

---

## 9. Cose che non vanno fatte

- Mai togliere, disabilitare o aggirare un controllo per far passare i test
- Mai promesse in copertina o in scheda che il libro non mantiene
- Mai un libro prodotto in `--dry-run` caricato su KDP (il QA lo blocca apposta:
  il testo segnaposto contiene `SEGNAPOSTO`)
- Mai caricare la copertina generata con `--guides`
- Mai pubblicare senza dichiarare a KDP l'uso dell'IA (testo e, se generata,
  copertina)
- Non riscrivere moduli interi di propria iniziativa: è una decisione dell'autore

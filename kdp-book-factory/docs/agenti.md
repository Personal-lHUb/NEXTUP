# Il collegio editoriale

Un libro scritto da una persona non esce da una sola testa in una sola passata:
passa da chi lo progetta, chi lo scrive, chi lo rilegge, chi lo corregge e chi
lo controlla prima della stampa. Il collegio riproduce quella catena, con una
regola che vale per tutti: **i revisori segnalano, non riscrivono**. L'unico che
mette le mani nel testo dopo la stesura è l'editor, e lo fa applicando le
segnalazioni degli altri.

```
architetto → indice → ghostwriter → [voce] → impaginazione + copertina
                                                    │
        lettore cieco (capitolo) ┐                  │
        fact-checker             ├─ segnalazioni ───┤
        conformità               │                  │
        correttore               │                  │
        lettore cieco (libro)    │                  ▼
        editor di sviluppo       →             editor  →  nuova impaginazione
```

---

## Chi fa cosa

### Acquisizione

Solo per i libri che nascono da un ASIN. Stanno **prima** del collegio e
consegnano `book.json` + `brief.md`. Documentati per esteso in
[`acquisizione.md`](acquisizione.md).

| Agente | Mestiere |
|---|---|
| `scheda-concorrente` | Legge una scheda Amazon copiata e incollata e ne ricava i dati strutturati. Quello che nella pagina non c'è resta vuoto: non stima e non deduce. |
| `analista-recensioni` | Ricava il buco di mercato dalle recensioni: chi ha pagato il libro scrive alla lettera quale libro avrebbe voluto. Ogni lacuna deve portare una citazione. |
| `posizionamento` | Decide che libro scrivere per coprire quel buco: promessa, lettore, titolo, pagine, prezzo, parole chiave, temi del brief. |
| `originalita` | Verifica che il piano sia un libro indipendente **prima** che venga scritto. Un bloccante impedisce la scrittura della scheda. |

### Produzione

| Agente | Mestiere |
|---|---|
| `architetto` | Progetta la struttura: tesi portante, sequenza dei capitoli, promessa di ciascuno, testo di quarta. Non scrive il libro. |
| `indice` | Produce l'indice: il titolo definitivo di ogni capitolo e l'ordine in cui si leggono. L'architetto dà ai capitoli titoli che li **descrivono**; questo li riscrive perché li **vendano**, perché l'indice è la pagina che il cliente apre nell'anteprima «Guarda dentro» prima di decidere. Non aggiunge né toglie capitoli: il numero lo decide il budget di pagine. |
| `ghostwriter` | Scrive un capitolo per volta, con la scaletta, la voce del libro e il budget di parole. Riceve l'elenco di ciò che è già stato detto, per non ripetersi. |
| `voce` | Revisione di stile: ritmo delle frasi, varietà dei capoversi, tic da testo prodotto in serie, lessico concreto. Non aggiunge né toglie contenuti, e mantiene la lunghezza entro il 5%. |
| `editor` | Applica le segnalazioni del collegio, capitolo per capitolo, senza toccare ciò che nessuno ha segnalato e rispettando il budget di parole. |

### Controllo

| Agente | Che cosa cerca |
|---|---|
| `lettore-cieco` | Legge **senza scaletta, senza scheda del libro, senza sapere che cosa il capitolo dovrebbe dimostrare**: solo le pagine, come chi ha comprato il libro. Lavora a due livelli. **Sul capitolo**: dove ha perso il filo, dove ha saltato righe, quale promessa non è stata mantenuta, che cosa avrebbe chiesto all'autore. **Sul libro intero**: riceve l'indice — l'unica cosa che ha visto prima di pagare — e verifica che ogni capitolo consegni quello che il suo titolo annuncia e che il contesto non cambi per strada: il destinatario che si sposta, i termini che cambiano nome, una definizione contraddetta più avanti, un «lo vedremo poi» che non arriva mai. Continua a non ricevere la scaletta, nemmeno qui. |
| `fact-checker` | Affermazioni presentate come fatti e non verificabili: percentuali, "gli studi dimostrano", citazioni, nomi di istituti, cifre precise, generalizzazioni assolute. Le citazioni inventate sono sempre bloccanti: su carta non si correggono più. |
| `conformita` | Regole di contenuto KDP e rischi legali: materiale di terzi, marchi e persone reali, consulenza medica/legale/fiscale formulata come prescrizione, promesse di risultato, coerenza fra il capitolo e la promessa del libro. |
| `correttore` | Bozze, parola per parola: refusi, accenti e apostrofi (perché, qual è, po'), accordi, punteggiatura, maiuscole incoerenti, ripetizioni ravvicinate, frasi rimaste a metà. |
| `editor-sviluppo` | Il libro come oggetto unico: progressione, capitoli che si sovrappongono, contraddizioni fra capitoli, promesse dell'introduzione mai mantenute, aperture tutte uguali. |
| `impaginazione` | Il PDF impaginato, non il manoscritto: righe vedove e orfane, titoli rimasti in fondo alla pagina, code di capitolo, testo fuori gabbia, scalette di sillabazione, capitoli che si aprono sulla pagina sbagliata. **Non usa il modello**: misura le coordinate del testo, quindi non costa nulla e non sbaglia per opinione. |
| `copertina` | La prima di copertina vista come la vede il cliente: larga 160 pixel, su fondo bianco. Corpo del titolo, contrasto, stacco dalla pagina dei risultati, affollamento, testo dentro l'area di sicurezza; più i testi, che devono contenere un ciclo aperto e nessuna rivendicazione vietata da KDP. **Non usa il modello**: misura il PDF. Il sistema è documentato in [`copertine.md`](copertine.md). |

---

## Livelli di lavorazione

Il livello decide quali agenti entrano in gioco e con quale gravità l'editor
interviene.

```bash
python3 -m kdpfactory all <slug> --qualita standard
```

| Livello | Che cosa succede |
|---|---|
| `bozza` | Solo stesura. Serve a valutare un'idea o una scaletta, non a pubblicare. |
| `standard` *(default)* | Stesura, poi lettore cieco, fact-checker, conformità, editor di sviluppo, impaginazione e copertina. L'editor applica bloccanti e importanti, poi si rimpagina. |
| `alta` | Come standard, più la passata di stile su ogni capitolo e il correttore di bozze. L'editor applica anche le segnalazioni minori. |

Dopo l'intervento dell'editor il libro viene **rimpaginato**: l'editing cambia
il numero di parole, e il numero di parole decide il numero di pagine.

---

## Uso separato

```bash
# solo revisione, senza modificare niente
python3 -m kdpfactory review <slug>

# un agente solo, su un capitolo solo
python3 -m kdpfactory review <slug> --agents lettore-cieco --only 3

# controllo tipografico sul PDF (gratis: nessuna chiamata al modello)
python3 -m kdpfactory review <slug> --agents impaginazione

# l'editor applica quanto raccolto
python3 -m kdpfactory revise <slug> --severita importante
```

`review` scrive due file in `build/`: `revisioni.md` da leggere e
`revisioni.json` che l'editor rilegge. Le segnalazioni bloccanti e importanti
confluiscono anche nel rapporto di `kdpfactory qa`, così un bloccante del
fact-checker impedisce di dare il libro per pronto.

---

## Gli stessi agenti dentro Claude Code

```bash
python3 -m kdpfactory agents --install        # scrive .claude/agents/*.md
```

Da Claude Code puoi poi rivolgerti a un agente per nome, per esempio:

> usa `lettore-cieco` su `books/il-mio-libro/manuscript/03.md`

È utile quando vuoi discutere una segnalazione invece di limitarti a leggerla.
I file `.md` sono **generati** dal registro Python (`kdpfactory/agents/`): per
cambiare il comportamento di un agente si modifica il prompt nel codice e si
rilancia `--install`, non si modificano i file esportati.

---

## Il contesto che riceve chi scrive

Il ghostwriter riceve due cose, e la differenza fra le due decide sia il costo
sia la qualità.

**Il blocco stabile** — regole d'autore e scheda del libro, con la struttura
completa: tutti i capitoli, titolo e sintesi. È identico a ogni chiamata, quindi
finisce in cache e dalla seconda in poi si paga un decimo.

**Il messaggio del capitolo** — numero, titolo, punti da coprire, lunghezza, il
riassunto del capitolo precedente e l'elenco di quello che è già stato detto.
Questo **non** va in cache: si ricompra intero ogni volta.

Quell'elenco cresceva di un riassunto a ogni capitolo. Su un libro da 240 pagine
— che con capitoli da 1.500-2.000 parole sono una trentina — l'ultimo capitolo
ne riceveva trentuno: **1.900 token** di roba scritta da altri capitoli, con
dentro, in fondo, l'unica istruzione che conta davvero.

Ora il blocco è tenuto a un budget (`COVERED_BUDGET_WORDS` in `prompts.py`,
350 parole, minimo tre capitoli): si tengono i riassunti **recenti**, che sono
quelli da cui ci si ripete davvero, e i più lontani restano dove erano già —
nella struttura completa del libro, che è nel blocco stabile e quindi gratis
dalla seconda chiamata in poi. Il prompt lo dice esplicitamente, così chi scrive
sa che quei capitoli esistono e non li deve ripetere.

| libro | capitoli | «già trattato» all'ultimo capitolo | su tutto il libro |
|---|---|---|---|
| 60 pagine | 6 | 306 → 306 token (invariato) | invariato |
| 140 pagine | 18 | 1.040 → 551 token | −24% |
| 240 pagine | 32 | 1.897 → **551** token | −51% |

Il punto non è il risparmio, che vale pochi centesimi a libro: è che da lì in
poi **il contesto smette di crescere**. Un libro corto non viene toccato, e un
libro lungo riceve per ogni capitolo la stessa quantità di contesto recente.

---

## Costi

Ogni agente di controllo è una chiamata per capitolo: su un libro da 15 capitoli,
il livello `standard` aggiunge circa 45 chiamate di lettura più le riscritture
dell'editor. Il prompt di sistema di ogni ruolo è stabile e finisce in cache,
quindi il costo è dominato dall'output. In pratica la revisione costa quanto la
stesura, o poco più.

Modi per spendere meno senza rinunciare ai controlli:

- `--agents impaginazione` non costa niente: nessuna chiamata al modello;
- `--only 1,2,3` per far revisionare solo i capitoli che contano di più;
- `--qualita bozza` mentre si sperimenta sulla struttura, `standard` alla fine;
- `--effort medium` sui libri semplici.

---

## Una precisazione sulla naturalezza

L'agente `voce` fa quello che fa un line editor su qualunque manoscritto:
rompe le cadenze meccaniche, varia il ritmo, sostituisce le astrazioni con cose
concrete. Serve a rendere il libro leggibile, non a nascondere come è stato
prodotto: KDP chiede di dichiarare l'uso dell'intelligenza artificiale e la
dichiarazione va fatta comunque — la pipeline la inserisce anche nel colophon
del libro. Un testo che si legge bene e una dichiarazione onesta non sono in
contraddizione.

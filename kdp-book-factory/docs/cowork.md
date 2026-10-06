# Il canale con Cowork

La fabbrica gira in un container che non raggiunge Amazon, KDP né il browser
dell'autore. Le ricerche web e le immagini le fa Cowork (app Claude Desktop),
col portatile dell'autore o nel cloud. Il dialogo è automatico: nessuno dei due
aspetta l'autore per passarsi un file, e nessuno dei due aspetta l'altro più
del necessario.

```
fabbrica (questa sessione)                    GitHub, Personal-lHUb/NEXTUP            Cowork
──────────────────────────                    ────────────────────────────            ──────
richiesta + indice, commit e push      ─▶     ramo della fabbrica                ─▶   il ruolo legge l'indice
lancia subito i ruoli che vanno nel cloud ─▶  (fire_trigger)                          e le sue richieste
applica, segna «Stato: applicata»      ◀─     ramo cowork-immagini               ◀─   consegna col browser:
assets/ del libro                      ◀─       …-risposta.md, immagini                GitHub dell'autore
porta su GitHub (--scarica)            ◀─     Drive: risposte di ripiego         ◀─   senza browser: testo
riparte subito                         ◀─     (fire_trigger della routine)       ◀─   avvisa la fabbrica

Google Drive «NEXTUP — corriere Cowork»: il LEGGIMI, le risposte di ripiego, gli esiti dei giri non riusciti
```

- La **richiesta** sta nel repository, nella cartella a cui serve:
  `books/<slug>/concorrente/`, `books/<slug>/manuale/`, oppure `config/` per le
  regole comuni. La **risposta** va accanto, con lo stesso nome più `-risposta`.
- L'**indice** `config/cowork-aperte.md` elenca le richieste aperte per ruolo:
  dove leggerle, dove consegnare la risposta, e se si possono fare nel cloud o
  solo col browser del portatile. Lo riscrive `cowork corriere` a ogni giro;
  Cowork lo legge dall'indirizzo pubblico (`raw.githubusercontent.com`) e non
  apre altro.
- Le sessioni di Cowork **non hanno credenziali GitHub**: niente `add_repo`, e
  il proxy rifiuta il push (esiti del 6 ottobre 2026). Leggono il repository
  pubblico e **consegnano** col GitHub dell'autore aperto nel browser del
  portatile: la pagina «consegna» dell'indice crea il file sul ramo
  `cowork-immagini`, commit direttamente sul ramo. Senza browser (giro nel
  cloud) la risposta di testo va su Drive col **nome di ripiego**
  (`books__x__…-risposta.md`), e la fabbrica la porta accanto alla richiesta
  con `cowork corriere --scarica`. Le immagini solo col browser.
- La fabbrica prende dal ramo solo le risposte alle sue richieste e le immagini
  che una richiesta ha nominato.
- Se il repository diventa privato, Cowork non legge più gli indirizzi
  pubblici: l'indice e le richieste si aprono solo col GitHub dell'autore nel
  browser, quindi tutti i ruoli diventano «solo col browser del portatile».
- Il **ruolo**: ogni richiesta dice sotto il titolo quale ruolo di Cowork la
  prende (`Ruolo: concorrente`, `parole-chiave`, `fonti`, `regole-kdp`,
  `immagini`), e uno solo. Ogni ruolo ha la sua chat e la sua attività
  pianificata, e non apre le richieste degli altri.
- Lo **stato** lo dà `python3 -m kdpfactory cowork stato`:
  *aperta* (senza risposta), *risposta arrivata* (da applicare), *risposta
  superata* (la richiesta è cambiata dopo), *applicata* (la richiesta contiene
  `Stato: applicata`).
- L'**avviso** da incollare in una chat di Cowork, se mai servisse a mano, lo
  scrive `cowork avviso` (con `--ruolo` per una chat sola).
- Il canale è descritto in `config/cowork.json`: `canale: "github"`, i rami, i
  ruoli con orari, compiti, attività e se lavorano nel cloud, la versione del
  LEGGIMI e la routine della fabbrica. Il registro di quello che è passato è
  `config/corriere.json`.

## Le regole di Cowork stanno nel LEGGIMI

`config/leggimi-cowork.md` sta sul ramo della fabbrica e viaggia anche su Drive
come `config__leggimi-cowork.md`, perché il prompt delle attività dice di
leggerlo per primo. Per cambiare una regola non si tocca il prompt di Cowork: si
modifica il LEGGIMI, si alza il numero di versione lì e in `config/cowork.json`,
si fa commit. Il giro lo ricarica su Drive da sé, e dal giro dopo Cowork segue
la versione nuova.

## I ruoli e il progetto Cowork

Cowork lavora in un progetto di Claude Desktop, «NEXTUP — Cowork», con una chat
e un'attività pianificata per ruolo, ogni ora, sfalsate di dieci minuti:

| ruolo | che cosa fa | attività | quando | nel cloud |
|---|---|---|---|---|
| `concorrente` | pagina Amazon del concorrente, recensioni alla lettera, copertina in miniatura, prezzi | NEXTUP — Concorrente | ogni ora, al minuto 05 | no |
| `parole-chiave` | parole chiave e categorie: Amazon, Helium 10, Publisher Rocket, Google Trends | NEXTUP — Parole chiave | ogni ora, al minuto 15 | no |
| `fonti` | affermazioni del libro controllate sulla fonte ufficiale | NEXTUP — Fonti | ogni ora, al minuto 25 | sì |
| `regole-kdp` | costi, limiti, pagine, selettore delle categorie; KDP in sola lettura | NEXTUP — Regole KDP | ogni ora, al minuto 35 | sì, senza `Serve:` |
| `immagini` | copertina e figure con ChatGPT, dal prompt del sistema; immagini già generate da consegnare | NEXTUP — Immagini | ogni ora, al minuto 45 | sì, senza `Serve:` |

Il testo da incollare — istruzioni del progetto, primo messaggio di ogni chat,
prompt di ogni attività — lo genera `python3 -m kdpfactory cowork progetto` in
`config/progetto-cowork.md`. Cambiato un ruolo o un orario, si rigenera.

Lo stesso comando scrive `config/attivita-cowork.json`: per ogni attività l'id,
il nome, l'orario e il prompt esatto, così una chat di Cowork sul portatile può
applicarlo da sé alle attività. Le attività di Cowork sono legate al portatile:
orario, nome e accensione la fabbrica li cambia da qui, il **prompt** cambia
solo con l'approvazione dell'autore in una conversazione di Cowork su quel
computer. Un'attività legata al portatile non si cancella e si ricrea per
aggirarlo: perderebbe la storia dei giri. Finché il prompt resta quello vecchio,
vale il LEGGIMI.

## Il giro senza attese

Tre cose tolgono le attese fra un giro e l'altro:

- **La fabbrica lancia subito i ruoli che vanno nel cloud.** Un giro lanciato
  con `fire_trigger` parte nel cloud, senza il Chrome dell'autore: va bene per
  i ruoli che lavorano su fonti pubbliche (`"cloud": true`) e per le richieste
  senza `Serve:`. `cowork corriere` le elenca in **avvia**, ruolo per ruolo con
  il suo trigger; dopo il lancio si registra
  `cowork corriere --avviato <ruolo>`. Ogni versione di una richiesta si lancia
  una volta sola: se resta aperta, la riprende l'attività oraria.
- **Le altre aspettano l'orario del ruolo**, col portatile acceso e collegato
  (l'autore lo tiene acceso negli orari di lavoro). L'indice le segna «solo col
  browser del portatile», e un giro nel cloud le salta senza scrivere niente.
- **Cowork avvisa la fabbrica.** Alla fine di un giro in cui ha consegnato
  qualcosa, Cowork lancia la routine della fabbrica (`routine_fabbrica`), che
  riprende questa sessione e applica la risposta subito, invece che al minuto
  57 dell'ora dopo.

Ogni giro di Cowork costa: si lancia solo quello che c'è da fare.

Un giro che fallisce in silenzio — accesso negato, push rifiutato, un indirizzo
che non si scarica — costa come uno riuscito. Per questo il LEGGIMI chiede a
Cowork di scrivere su Drive `cowork-esito-<ruolo>-<AAAAMMGG-hhmm>.md` con
l'errore esatto, e il giro della fabbrica li cerca (`title contains
'cowork-esito'`), li legge e li riporta all'autore. Un giro senza richieste, o
riuscito, non scrive esiti.

## Il corriere: che cosa passa e da dove

`python3 -m kdpfactory cowork corriere` dice che cosa fare in questo giro,
senza andare in rete, e scrive l'indice `config/cowork-aperte.md`:

- **carica** e **togli**: su Drive resta solo il LEGGIMI; progetto e attività
  Cowork li legge dal ramo. Drive non riscrive il contenuto di un file: se ne
  crea uno nuovo e il vecchio (`vecchio_id`) va nel cestino, poi
  `cowork corriere --caricato <percorso> --id <id>`. Le copie caricate quando il
  canale era Drive — richieste, progetto, attività — si cestinano e si registra
  `--tolto <percorso>`.
- **avvia**: i ruoli da lanciare subito, qui sopra.

Le consegne arrivano dal ramo:

```bash
python3 -m kdpfactory cowork corriere --dal-ramo
```

scarica il ramo `cowork-immagini` e porta nel repository due sole cose: la
risposta a una richiesta che c'è (testo UTF-8, accanto alla richiesta, mai
sopra una risposta che c'è già) e le immagini che una richiesta ha nominato, in
`books/<slug>/assets/` di un libro che c'è, se il file è davvero un'immagine
(PNG, JPEG, WebP, dalle prime righe). Tutto il resto del ramo resta lì: il ramo
non si unisce mai al lavoro, e non può portare codice, `book.json` o testo dei
libri. Un file già preso (registro `dal_ramo` in `config/corriere.json`) non si
riscrive; una versione nuova di un'immagine sì, con la copia di sicurezza della
vecchia.

Con `canale: "drive"` in `config/cowork.json` il corriere torna quello di
prima: richieste e risposte sulla cartella Drive, con `--scarica <nome> --id
<id> --file <scaricato>`, e le immagini comunque sul ramo.

## Il giro orario

La routine «Produzione NEXTUP» riprende questa sessione ogni ora, al minuto 57,
e ogni volta che Cowork consegna; fa da sola tutto quello che non è
dell'autore:

1. `git pull`; poi `cowork corriere --dal-ramo` e il **corriere**: indice,
   LEGGIMI su Drive se è cambiato.
2. `cowork stato`: applica ogni **risposta arrivata** (regole di ingaggio qui
   sotto) e segna la richiesta `Stato: applicata il <data>`.
3. `decisioni --scadute` e `produzione`: le **decisioni** prese, dall'autore o
   per silenzio-assenso, si applicano ai file del libro e si segnano
   `--applicata`.
4. Per ogni libro che `produzione` dà **avanti**, il prossimo passo: uno per
   libro a giro, il più piccolo che chiude un pezzo — un agente del reparto, un
   capitolo, una fase di controllo — come dice `linee-guida.md`.
5. Quando un passo chiede una decisione dell'autore, la propone con
   `decisioni <slug> --proponi …` e gli manda una notifica.
6. Copia di backup, `cowork corriere` (l'indice nuovo), commit e push; poi i
   lanci di **avvia**, che leggono l'indice dal ramo e quindi vengono dopo il
   push. All'autore una riga solo per le risposte applicate, le proposte nuove
   e i libri pronti.

I libri su cui lavora sono quelli di `config/produzione.json`: ci entrano da
soli alla fine delle domande d'avvio, e ne escono quando l'autore li pubblica o
li mette in pausa.

## Le decisioni dell'autore: il silenzio-assenso

Categoria, titolo, promessa, voce narrante, prezzo, variante di copertina e
pseudonimo restano decisioni dell'autore, ma il libro non si ferma ad
aspettarle. La sessione registra la proposta degli agenti, con le alternative e
il perché:

```bash
python3 -m kdpfactory decisioni <slug> --proponi titolo --valore "…" \
    --alternativa "…" --alternativa "…" --perche "…"
```

e manda la notifica all'autore. Se entro **24 ore** (`config/produzione.json`)
l'autore non risponde, vale la proposta. Se risponde, la sessione registra la
sua scelta (`--scegli titolo --valore "…"`), che vince sempre. Il registro sta in
`books/<slug>/decisioni.json`. La **pubblicazione** non passa mai dal
silenzio-assenso: la decide l'autore.

## Regole di ingaggio

- **Una richiesta nuova si fa nello stesso giro in cui nasce**: commit e push
  con l'indice, e se si fa nel cloud il lancio del ruolo.
- **Ogni richiesta ha un ruolo**, nella riga `Ruolo:` sotto il titolo, e uno
  solo: se una ricerca tocca due ruoli, sono due richieste.
- **Ogni richiesta basta a sé stessa.** Cowork legge l'indice e la richiesta,
  non il resto del repository: la frase da verificare, il prompt dell'immagine,
  l'elenco delle parole chiave vanno scritti dentro la richiesta.
- **Un file `-risposta.md` è di Cowork.** La fabbrica lo legge, non lo modifica
  mai. Se una risposta è incompleta o bloccata (captcha, accesso), si apre
  `cowork-<argomento>-2.md` con i soli punti mancanti.
- **Un accesso che apre l'autore va nella riga `Serve:`.** Se il seguito
  dipende da un accesso dell'autore (KDP, ChatGPT, Helium 10, Amazon), la
  richiesta lo dice sotto il ruolo, con `cowork.intestazione(…, serve=…)`.
  Finché l'accesso non è aperto Cowork non risponde, invece di tornare
  parziale a ogni giro, e `produzione` mostra che la richiesta aspetta
  l'autore. Un seguito `-2`, `-3` conta per il passo come la richiesta da cui
  nasce.
- **Una richiesta corretta dopo la risposta** rende la risposta *superata*: la
  versione corretta va in `cowork-<argomento>-2.md`. Se la risposta non c'è
  ancora, basta correggere la richiesta: l'indice punta già al ramo.
- **Una richiesta ritirata** si cancella dal repository, con un commit che dice
  perché; esce dall'indice al giro dopo.

## Istruzioni permanenti per Cowork

Sono le istruzioni del progetto, comuni a tutte le chat, nella prima sezione di
`config/progetto-cowork.md`. Quando l'autore chiede a una chat «sei
allineato?», risponde con il suo ruolo, la versione del LEGGIMI che vede e le
richieste del suo ruolo che l'indice dà ancora aperte.

## Per aprire una richiesta nuova

Si scrive `cowork-<argomento>.md` nella cartella a cui serve, con l'intestazione
comune di `cowork.intestazione()` — titolo, riga `Ruolo:`, regole, percorso
della risposta sul ramo `cowork-immagini` — e le istruzioni complete. Le cartelle dove serve il web sono
in `RICERCA-WEB.md`, alla radice del repository.

Le richieste che ogni libro fa sempre non si scrivono a mano: le produce il
sistema, uguali per ogni libro.

| richiesta | ruolo | quando | comando |
|---|---|---|---|
| `concorrente/cowork-concorrente.md` (o `cowork-nicchia.md`) | concorrente | fine delle domande d'avvio | `avvio <slug>` |
| `concorrente/cowork-parole-chiave.md` | parole-chiave | fine delle domande d'avvio | `avvio <slug>` |
| `manuale/cowork-verifica-parole-chiave.md` | parole-chiave | scheda prodotto (fase 6) | `parole-chiave <slug>` |
| `manuale/cowork-copertina.md` | immagini | copertina (fase 7) | `copertina <slug>` |
| `manuale/cowork-figure.md` | immagini | figure dichiarate e mancanti | `immagini <slug>` |

## Le immagini: Higgsfield da qui, Cowork solo se configurato

Con `config/immagini.json` su `"generatore": "higgsfield"` le immagini non
passano più dal corriere: le genera la sessione con `copertina <slug> --genera`
e `immagini <slug> --genera`, dal prompt del sistema, e il ruolo `immagini` di
Cowork non riceve richieste. Il CLI di Higgsfield vuole l'accesso dell'autore
(`higgsfield auth login`); senza, `produzione` dà il passo e dice che cosa
manca. Con `"generatore": "cowork"` vale quello che segue.

Se la rete dell'ambiente blocca i domini di Higgsfield, la sessione genera dal
connettore Higgsfield di claude.ai, che passa dal proxy di Anthropic, con gli
stessi prompt del sistema. Le immagini restano sulla CDN di Higgsfield, che la
rete può bloccare a sua volta: allora la sessione scrive
`manuale/cowork-immagini-scarica.md` (`richiesteimmagini.scaricamento`, ruolo
`immagini`, col browser del portatile: nel cloud la CDN è bloccata anche per
Cowork) e Cowork le scarica e le carica col browser sul ramo `cowork-immagini`,
da cui `cowork corriere --dal-ramo` le porta in `assets/`. Se l'autore apre i
domini di Higgsfield nella rete dell'ambiente, la sessione le scarica da sé e
la richiesta si ritira.
Finché la richiesta è aperta `produzione` dà la copertina in attesa: le
varianti già pagate non si rigenerano.

## Il progetto ChatGPT delle immagini

Le immagini nascono in un progetto di ChatGPT, «NEXTUP — Immagini»: le regole
fisse (niente testo, 2:3, scala di grigi per l'interno, originalità, misure
dichiarate) stanno nelle sue istruzioni, che `cowork progetto` scrive in
`config/progetto-chatgpt.md`. Il prompt di ogni lavoro si **incolla** nella sua
chat, come testo: `copertina <slug>` scrive `build/copertina-prompt.txt` e lo
stampa nel terminale, `immagini <slug>` scrive `build/immagini-prompt.txt`, un
prompt per figura. Il file è diviso da righe `===` che dicono che cosa
incollare e dove, e che non si incollano.

Il prompt porta solo quello che decide l'immagine: soggetto, stile, fattore
distintivo, colori detti a parole col loro codice, composizione, divieti. Le
specifiche di stampa (dorso, codice a barre, abbondanze) restano nel brief
completo, `build/copertina-brief.md`, che è il riferimento dell'agente
`copertina`: dette al generatore, rischiano di fargli disegnare l'intera
copertina col dorso invece della prima. La richiesta a Cowork porta lo stesso prompt, parola per parola, quindi
le immagini le può generare l'autore o Cowork, e vale la prima serie che arriva
sul ramo `cowork-immagini`.

Le varianti di copertina arrivano in `assets/copertina-N.png`; l'agente
`copertina` le misura, la scelta passa dal silenzio-assenso, e
`copertina <slug> --scegli N` porta quella scelta in `assets/copertina.jpg`.

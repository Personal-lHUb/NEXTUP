# Il canale con Cowork

La fabbrica gira in un container che non raggiunge Amazon, KDP né il browser
dell'autore. Le ricerche web e le immagini le fa Cowork (app Claude Desktop),
col portatile dell'autore o nel cloud. Il dialogo è automatico: nessuno dei due
aspetta l'autore per passarsi un file, e nessuno dei due aspetta l'altro più
del necessario. **I file stanno solo su GitHub**: Google Drive non si usa più
dal 7 ottobre 2026 (decisione dell'autore).

```
fabbrica (questa sessione)                    GitHub, Personal-lHUb/NEXTUP            Cowork
──────────────────────────                    ────────────────────────────            ──────
richiesta + indice, commit e push      ─▶     ramo della fabbrica                ─▶   il ruolo legge l'indice
lancia subito i ruoli che vanno nel cloud ─▶  (fire_trigger)                          e le sue richieste
salva la risposta (--ricevi), commit   ◀─     fire_trigger della routine,        ◀─   consegna la risposta
applica, segna «Stato: applicata»              con la risposta nel testo                (o l'esito di un giro fallito)
assets/ del libro (--dal-ramo)         ◀─     ramo cowork-immagini               ◀─   l'autore, se carica immagini
```

- La **richiesta** sta nel repository, nella cartella a cui serve:
  `books/<slug>/concorrente/`, `books/<slug>/manuale/`, oppure `config/` per le
  regole comuni. La **risposta** va accanto, con lo stesso nome più `-risposta`.
- L'**indice** `config/cowork-aperte.md` elenca le richieste aperte per ruolo:
  dove leggerle, dove consegnare la risposta, e se si possono fare nel cloud o
  solo col browser del portatile. Lo riscrive `cowork corriere` a ogni giro;
  Cowork lo legge dall'indirizzo pubblico (`raw.githubusercontent.com`) e non
  apre altro.
- **Su GitHub Cowork legge e basta.** Le sue sessioni non hanno credenziali
  (niente `add_repo`, il proxy rifiuta il push) e la sua modalità automatica
  blocca la scrittura su GitHub dal browser dell'autore come un aggiramento
  («Auto-Mode Bypass», esiti del 6 ottobre 2026). Non si aggira: Cowork
  **consegna la risposta come testo**, lanciando la routine della fabbrica
  (sezione «La consegna»), e la fabbrica, con il suo accesso, la salva accanto
  alla richiesta.
- **Le immagini** Cowork non le consegna (il testo di una consegna non porta
  file, GitHub non si scrive): le genera e le scarica la fabbrica; sul ramo
  `cowork-immagini` arrivano solo quelle che carica l'autore, e la fabbrica
  prende solo quelle che una richiesta ha nominato.
- Se il repository diventa privato, Cowork non legge più gli indirizzi
  pubblici, e non ha credenziali per leggerlo altrimenti: prima di renderlo
  privato serve un'altra strada di lettura, che non sia Drive.
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

`config/leggimi-cowork.md` sta sul ramo della fabbrica, e il prompt delle
attività dice di leggerlo per primo, dall'indirizzo pubblico. Per cambiare una
regola non si tocca il prompt di Cowork: si modifica il LEGGIMI, si alza il
numero di versione lì e in `config/cowork.json`, si fa commit e push. Dal giro
dopo Cowork segue la versione nuova.

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
- **La consegna è il lancio.** Cowork consegna ogni risposta lanciando la
  routine della fabbrica (`routine_fabbrica`), che riprende questa sessione e
  la salva e applica subito, invece che al minuto 57 dell'ora dopo.

Ogni giro di Cowork costa: si lancia solo quello che c'è da fare.

Un giro che fallisce in silenzio — accesso negato, un indirizzo che non si
scarica — costa come uno riuscito. Per questo il LEGGIMI chiede a Cowork di
consegnare anche l'esito di un giro non riuscito, con la prima riga
`Cowork · esito · <ruolo>` e l'errore esatto: la fabbrica lo salva in
`config/cowork-esiti/`, lo legge e lo riporta all'autore. Un giro senza
richieste, o riuscito, non consegna esiti.

## La consegna

Cowork consegna con `fire_trigger` sulla routine della fabbrica
(`trig_014uG5o2CZ22kwnBS5FDxty7`). Nel testo, la prima riga dice dove va il
resto — è la riga «consegna» che l'indice e l'intestazione della richiesta
danno — e dalla riga dopo c'è la risposta intera, che comincia con `Esito: …`:

```
Cowork · risposta · kdp-book-factory/books/x/concorrente/cowork-concorrente-risposta.md
Esito: completa
…
```

Il testo di `fire_trigger` porta fino a 64 KiB: una risposta oltre 50.000
caratteri arriva in parti, ognuna con la stessa prima riga seguita da
` · parte N/M`. La sessione copia il testo che arriva dopo il prompt della
routine in un file dello scratchpad e lo passa a

```bash
python3 -m kdpfactory cowork corriere --ricevi <file>
```

che riconosce una o più consegne nel testo e per ciascuna:

- **risposta**: la scrive accanto alla sua richiesta, se il percorso è la
  risposta di una richiesta che esiste e la risposta non c'è ancora; una
  consegna doppia uguale non fa niente, una diversa viene rifiutata (una
  risposta di Cowork non si riscrive: se serve altro, un seguito `-2`).
  Qualunque altro percorso — codice, `book.json`, un altro libro — resta fuori.
  Le parti aspettano in `config/cowork-in-arrivo/` finché non ci sono tutte;
- **esito**: lo salva in `config/cowork-esiti/<AAAAMMGG-hhmmss>-<ruolo>.md`.

Il registro delle consegne salvate è `config/corriere.json`, sotto `ricevute`.

**Se una sessione di Cowork non ha `fire_trigger`**, il LEGGIMI le chiede di
scrivere le consegne intere nell'ultimo messaggio del giro, con la riga
«Consegna non riuscita: manca fire_trigger». Da lì le porta l'autore: le
incolla a questa sessione (che le passa a `--ricevi`), oppure carica il file
della risposta sul ramo `cowork-immagini`, al suo percorso, e `--dal-ramo` lo
prende. Quando l'autore chiede a una chat «sei allineato?», la chat dice anche
se ha lo strumento.

## Il corriere: che cosa passa e da dove

`python3 -m kdpfactory cowork corriere` dice che cosa aspettarsi in questo
giro, senza andare in rete, e scrive l'indice `config/cowork-aperte.md`:

- **attese**: le prime righe delle consegne che possono arrivare, una per
  richiesta aperta;
- **in_arrivo**: le consegne lunghe arrivate solo in parte;
- **avvia**: i ruoli da lanciare subito, qui sopra.

Dal ramo arriva quello che carica l'autore:

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

Fino al 7 ottobre 2026 le risposte passavano dalla cartella Drive «NEXTUP —
corriere Cowork». Drive non si usa più: la cartella resta com'è, nessuno la
legge né la scrive, e `config/corriere.json` ne conserva la storia sotto
`drive_dismesso`.

## Il giro orario

La routine «Produzione NEXTUP» riprende questa sessione ogni ora, al minuto 57,
e ogni volta che Cowork consegna; fa da sola tutto quello che non è
dell'autore:

1. `git pull`; le **consegne** arrivate col lancio (`cowork corriere --ricevi`),
   gli esiti da leggere; poi `cowork corriere --dal-ramo`.
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
allineato?», risponde con il suo ruolo, la versione del LEGGIMI che vede, le
richieste del suo ruolo che l'indice dà ancora aperte e se ha lo strumento
`fire_trigger`, con cui consegna.

## Per aprire una richiesta nuova

Si scrive `cowork-<argomento>.md` nella cartella a cui serve, con l'intestazione
comune di `cowork.intestazione()` — titolo, riga `Ruolo:`, regole, prima riga
della consegna — e le istruzioni complete. Le cartelle dove serve il web sono
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
rete può bloccare a sua volta. Allora gli indirizzi restano in
`build/copertina-higgsfield.json`, e `copertina <slug> --scarica-generate` le
porta in `assets/copertina-N.png` appena la rete lascia passare la CDN: l'autore
aggiunge i domini di Higgsfield nelle impostazioni dell'ambiente (Network access,
Custom, Allowed domains: `higgsfield.ai`, `fnf.higgsfield.ai`,
`fnf-api-gw.higgsfield.ai`, `clerk.higgsfield.ai`,
`d8j0ntlcm91z4.cloudfront.net`). In alternativa le carica lui sul ramo
`cowork-immagini`, da cui `cowork corriere --dal-ramo` le porta in `assets/`.
Cowork non le può consegnare: la sua CDN è bloccata nel cloud e su GitHub non
scrive. Finché mancano, `produzione` dà la copertina in attesa dell'autore: le
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

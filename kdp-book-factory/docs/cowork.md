# Il canale con Cowork

La fabbrica gira in un container che non raggiunge Amazon, KDP né il browser
dell'autore. Le ricerche web e le immagini le fa Cowork (app Claude Desktop)
sul portatile dell'autore. Il dialogo è automatico: nessuno dei due aspetta
l'autore per passarsi un file.

```
fabbrica (questa sessione, ogni ora)          Google Drive                       Cowork (portatile, ogni ora)
────────────────────────────────────          «NEXTUP — corriere Cowork»         ────────────────────────────
richiesta nel repository, commit       ─▶     books__x__…__cowork-<arg>.md  ─▶   il ruolo la legge ed esegue
applica, segna «Stato: applicata»      ◀─     …__cowork-<arg>-risposta.md   ◀─   scrive la risposta
assets/ del libro                      ◀─     books__x__assets__<img>.png   ◀─   genera le immagini
        │
        └─ GitHub (Personal-lHUb/NEXTUP): l'archivio di richieste e risposte, con la loro storia
```

- La **richiesta** sta nel repository, nella cartella a cui serve:
  `books/<slug>/concorrente/`, `books/<slug>/manuale/`, oppure `config/` per le
  regole comuni. La **risposta** va accanto, con lo stesso nome più `-risposta`.
- Su **Drive** ogni file si chiama come il suo percorso nel repository (dalla
  cartella `kdp-book-factory/`), con `__` al posto di `/`. Così una risposta o
  un'immagine che Cowork lascia nella cartella dice da sola dove va.
- Il **ruolo**: ogni richiesta dice sotto il titolo quale ruolo di Cowork la
  prende (`Ruolo: concorrente`, `parole-chiave`, `fonti`, `regole-kdp`,
  `immagini`), e uno solo. Ogni ruolo ha la sua chat e la sua attività
  pianificata, e non apre le richieste degli altri.
- Lo **stato** lo dà `python3 -m kdpfactory cowork stato`:
  - **invio**: *inviata* se su Drive c'è questa stessa versione, altrimenti
    *da inviare*;
  - **stato**: *aperta* (senza risposta), *risposta arrivata* (da applicare),
    *risposta superata* (la richiesta è cambiata dopo), *applicata* (la
    richiesta contiene `Stato: applicata`).
- L'**avviso** da incollare in una chat di Cowork, se mai servisse a mano, lo
  scrive `cowork avviso` (con `--ruolo` per una chat sola).
- Il canale è descritto in `config/cowork.json`: la cartella del corriere, i
  ruoli con orari e compiti, la versione del LEGGIMI. Il registro di quello
  che è passato su Drive è `config/corriere.json`.

## Le regole di Cowork stanno nel LEGGIMI

`config/leggimi-cowork.md` viaggia sul corriere come
`config__leggimi-cowork.md`, e Cowork lo legge a ogni giro. Per cambiare una
regola non si tocca il prompt di Cowork: si modifica il LEGGIMI, si alza il
numero di versione lì e in `config/cowork.json`, si fa commit. Il giro orario lo
ricarica su Drive da sé, e dal giro dopo Cowork segue la versione nuova.

## I ruoli e il progetto Cowork

Cowork lavora in un progetto di Claude Desktop, «NEXTUP — Cowork», con una chat
e un'attività pianificata per ruolo, ogni ora, sfalsate di dieci minuti:

| ruolo | che cosa fa | attività | quando |
|---|---|---|---|
| `concorrente` | pagina Amazon del concorrente, recensioni alla lettera, copertina in miniatura, prezzi | NEXTUP — Concorrente | ogni ora, al minuto 05 |
| `parole-chiave` | parole chiave e categorie: Amazon, Helium 10, Publisher Rocket, Google Trends | NEXTUP — Parole chiave | ogni ora, al minuto 15 |
| `fonti` | affermazioni del libro controllate sulla fonte ufficiale | NEXTUP — Fonti | ogni ora, al minuto 25 |
| `regole-kdp` | costi, limiti, pagine, selettore delle categorie; KDP in sola lettura | NEXTUP — Regole KDP | ogni ora, al minuto 35 |
| `immagini` | copertina e figure con ChatGPT, dal prompt del sistema | NEXTUP — Immagini | ogni ora, al minuto 45 |

Il testo da incollare — istruzioni del progetto, primo messaggio di ogni chat,
prompt di ogni attività — lo genera `python3 -m kdpfactory cowork progetto` in
`config/progetto-cowork.md`. Cambiato un ruolo o un orario, si rigenera.

Lo stesso comando scrive `config/attivita-cowork.json`: per ogni attività l'id,
il nome, l'orario e il prompt esatto. Viaggia sul corriere, così una chat di
Cowork sul portatile può applicarlo da sé alle attività. Le attività di Cowork
sono legate al portatile: orario, nome e accensione la fabbrica li cambia da
qui, il **prompt** cambia solo con l'approvazione dell'autore in una
conversazione di Cowork su quel computer. Un'attività legata al portatile non
si cancella e si ricrea per aggirarlo: perderebbe la storia dei giri.

## Il corriere su Drive

La sessione porta i file fra repository e Drive con il connettore Google Drive;
`python3 -m kdpfactory cowork corriere` le dice che cosa fare, senza andare in
rete:

- **carica**: le richieste aperte, il LEGGIMI e il progetto che su Drive non ci
  sono o ci sono in una versione vecchia. Drive non riscrive il contenuto di un
  file: se ne crea uno nuovo e il vecchio (`vecchio_id`) va nel cestino. Poi
  `cowork corriere --caricato <percorso> --id <id>`.
- **togli**: le copie delle richieste ormai applicate; si cestinano e si
  registra `--tolto <percorso>`.
- **attesi**: i nomi delle risposte che Cowork può consegnare. Con le immagini
  `books__<slug>__assets__…`, sono le sole cose che dalla cartella arrivano nel
  repository: `cowork corriere --scarica <nome> --id <id> --file <scaricato>`
  rifiuta ogni altro nome, e una risposta che c'è già non si riscrive.

## Il giro orario

La routine «Produzione NEXTUP» riprende questa sessione ogni ora, al minuto 57,
e fa da sola tutto quello che non è dell'autore:

1. `git pull`; poi il **corriere**: carica, togli, scarica.
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
6. Copia di backup, commit e push; all'autore una riga solo per le risposte
   applicate, le proposte nuove e i libri pronti.

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

- **Una richiesta nuova si fa nello stesso giro in cui nasce**: commit, e il
  giro orario la porta sul corriere.
- **Ogni richiesta ha un ruolo**, nella riga `Ruolo:` sotto il titolo, e uno
  solo: se una ricerca tocca due ruoli, sono due richieste.
- **Ogni richiesta basta a sé stessa.** Cowork non vede il repository: la frase
  da verificare, il prompt dell'immagine, l'elenco delle parole chiave vanno
  scritti dentro la richiesta.
- **Un file `-risposta.md` è di Cowork.** La fabbrica lo legge, non lo modifica
  mai. Se una risposta è incompleta o bloccata (captcha, accesso), si apre
  `cowork-<argomento>-2.md` con i soli punti mancanti.
- **Una richiesta corretta dopo la risposta** rende la risposta *superata*: la
  versione corretta va in `cowork-<argomento>-2.md`. Se la risposta non c'è
  ancora, basta correggere la richiesta: il giro la ricarica.
- **Una richiesta ritirata** si cancella dal repository, con un commit che dice
  perché; il giro toglie la sua copia da Drive.

## Istruzioni permanenti per Cowork

Sono le istruzioni del progetto, comuni a tutte le chat, nella prima sezione di
`config/progetto-cowork.md`. Quando l'autore chiede a una chat «sei
allineato?», risponde con il suo ruolo, la versione del LEGGIMI che vede nella
cartella e le richieste del suo ruolo ancora senza risposta.

## Per aprire una richiesta nuova

Si scrive `cowork-<argomento>.md` nella cartella a cui serve, con l'intestazione
comune di `cowork.intestazione()` — titolo, riga `Ruolo:`, regole, nome della
risposta su Drive — e le istruzioni complete. Le cartelle dove serve il web sono
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

Le varianti di copertina arrivano in `assets/copertina-N.png`; l'agente
`copertina` le misura, la scelta passa dal silenzio-assenso, e
`copertina <slug> --scegli N` porta quella scelta in `assets/copertina.jpg`.

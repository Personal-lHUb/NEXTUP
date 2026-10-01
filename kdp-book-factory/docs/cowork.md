# Il canale con Cowork

La fabbrica gira in un container che non raggiunge Amazon né KDP. Le ricerche
web le fa Cowork (app Claude Desktop) sul computer dell'autore. Lo scambio passa
da file nel repository GitHub, sul ramo del canale:

```
fabbrica (questa sessione)                 GitHub                                   Cowork
───────────────────────────                Personal-lHUb/NEXTUP                     ───────────────────────
commit e push di cowork-<arg>.md     ─▶    ramo claude/dreamy-archimedes-hf8w45 ─▶  legge ed esegue
applica, segna «Stato: applicata»    ◀─    cowork-<arg>-risposta.md, accanto    ◀─  commit della risposta
```

- La **richiesta** sta nella cartella a cui serve:
  - `books/<slug>/manuale/` per un libro;
  - `books/<slug>/concorrente/` per la pagina del concorrente;
  - `config/` per le regole comuni.
- La **risposta** va accanto, con lo stesso nome più `-risposta`.
- Il **ruolo**: ogni richiesta dice sotto il titolo quale ruolo di Cowork la
  prende (`Ruolo: concorrente`, `parole-chiave`, `fonti`, `regole-kdp`). Ogni
  ruolo ha la sua chat e la sua attività pianificata, e non apre le richieste
  degli altri. Una richiesta senza ruolo non la prende nessuno: `cowork stato`
  lo segnala.
- Lo **stato** lo dà `python3 -m kdpfactory cowork stato`, con `--json` per
  l'elenco completo. Git dice due cose, la seconda solo per le richieste con
  risposta:
  - **invio**: *inviata* se sul ramo remoto c'è la stessa versione, altrimenti
    *da inviare*;
  - **stato**:
    - *aperta*: senza risposta;
    - *risposta arrivata*: la risposta c'è, da applicare;
    - *risposta superata*: la richiesta è cambiata dopo la risposta;
    - *applicata*: la richiesta contiene `Stato: applicata`.
- L'**avviso** per Cowork lo scrive `python3 -m kdpfactory cowork avviso`: elenca
  solo le richieste aperte, con i percorsi dalla radice del repository. Se ce
  n'è una ancora da inviare, lo dice prima. Con `--ruolo <ruolo>` è l'avviso
  per la chat di quel ruolo, con le sole richieste sue.
- Il canale è descritto in `config/cowork.json`: repository, ramo e LEGGIMI.
- La casella su Google Drive «NEXTUP — libri/cowork», usata fino al 30
  settembre 2026, è chiusa. Contiene solo un avviso che rimanda qui.

## Le regole di Cowork stanno nel repository

Le regole per il lato Cowork sono in `config/leggimi-cowork.md`, e Cowork le
legge a ogni giro. Per cambiarne una non si tocca il prompt di Cowork:

1. si modifica il LEGGIMI e si alza il numero di versione, lì e in
   `config/cowork.json`;
2. si fa commit e push sul ramo del canale.

Dal giro dopo Cowork segue la versione nuova.

## I ruoli e il progetto Cowork

In Claude Desktop, Cowork lavora in un progetto, «NEXTUP — Cowork», con una
chat per ruolo. I ruoli stanno in `config/cowork.json`:

| ruolo | che cosa fa | attività | orari (Roma) |
|---|---|---|---|
| `concorrente` | pagina Amazon del concorrente, recensioni alla lettera, copertina in miniatura, prezzi | NEXTUP — Concorrente | 7:52, 13:52 |
| `parole-chiave` | parole chiave e categorie: Amazon, Helium 10, Publisher Rocket, Google Trends | NEXTUP — Parole chiave | 8:07, 14:07 |
| `fonti` | affermazioni del libro controllate sulla fonte ufficiale | NEXTUP — Fonti | 8:22, 14:22 |
| `regole-kdp` | costi, limiti, pagine, selettore delle categorie; KDP in sola lettura | NEXTUP — Regole KDP | 8:37, 14:37 |

Il testo da incollare — istruzioni del progetto, primo messaggio di ogni chat,
prompt di ogni attività — non si scrive a mano: lo genera

```bash
python3 -m kdpfactory cowork progetto      # config/progetto-cowork.md
```

dalla configurazione. Cambiato un ruolo o un orario, si rigenera e si pubblica.
L'attività unica di prima, «Cowork — casella NEXTUP», va disattivata quando le
quattro sono accese: finché resta accesa risponde a tutte le richieste, e i ruoli
non sono più separati.

Le attività girano sul portatile dell'autore, che deve essere acceso, sfalsate
di un quarto d'ora e tutte prima del controllo della fabbrica. Se un giro salta,
la risposta arriva al giro dopo: non è un errore. Se Cowork non ha accesso
diretto a GitHub, restano due passi dell'autore in GitHub Desktop: il Pull prima
dei giri e il push delle risposte dopo.

## Il giro automatico

### La fabbrica — controllo pianificato (routine su questa sessione)

Ogni giorno alle 9:59 e alle 15:59, ora di Roma, la routine «Controllo Cowork»
riprende la sessione della fabbrica ed esegue:

1. `git fetch`, poi il merge del ramo del canale nel ramo di lavoro;
2. `python3 -m kdpfactory cowork stato`;
3. commit e push di ogni richiesta *da inviare*;
4. per ogni *risposta superata*: la domanda corretta va in una richiesta
   `-2` (vedi le regole qui sotto);
5. applica ogni *risposta arrivata* secondo `CLAUDE.md` e le linee guida:
   - i dati nei file del libro;
   - le affermazioni smentite all'editor, poi build, impaginazione e qa;
   - ci si ferma per le decisioni dell'autore.

   Poi aggiunge `Stato: applicata il <data>` alla richiesta, fa commit e push,
   e scrive all'autore una riga per ogni risposta applicata:
   «<richiesta>: applicata, <cosa è cambiato>, <decisioni che ti servono>».
   Se la risposta è parziale, apre subito la richiesta `-2` con i soli punti
   mancanti;
6. se non c'è niente di nuovo, non scrive niente.

## Regole di ingaggio

- **Una richiesta nuova si pubblica nello stesso giro in cui nasce.** Commit e
  push sul ramo del canale. `cowork stato` segna *da inviare* quelle che sul
  ramo remoto non ci sono, o ci sono in una versione diversa.
- **Ogni richiesta ha un ruolo**, nella riga `Ruolo:` sotto il titolo, e uno
  solo: se una ricerca tocca due ruoli, sono due richieste. Una richiesta che
  ne mescola più d'uno, se non ha ancora risposta, si ritira e si divide.
- **Un file `-risposta.md` è di Cowork.** La fabbrica lo legge, non lo modifica
  mai. Se una risposta è incompleta o bloccata (captcha, accesso), si apre
  `cowork-<argomento>-2.md` con i soli punti mancanti.
- **Una richiesta corretta dopo la risposta.** `cowork stato` segna la
  risposta *superata*: vale per la domanda vecchia. La versione corretta va in
  `cowork-<argomento>-2.md`: con lo stesso nome, Cowork troverebbe la risposta
  vecchia e salterebbe la domanda. Se la risposta non c'è ancora, basta
  correggere la richiesta e pubblicarla.
- **Una richiesta ritirata si cancella dal ramo**, con un commit che dice
  perché.
- **Ci si ferma dall'autore** solo per le sue decisioni (categoria, titolo,
  promessa, voce narrante, prezzo, pubblicazione) e per l'immagine di
  copertina.

## Istruzioni permanenti per Cowork

Sono le istruzioni del progetto, comuni a tutte le chat: quali file consultare
per restare allineati, in che ordine, che cosa si può scrivere e che cosa mai.
Stanno nella prima sezione di `config/progetto-cowork.md`, generate come il
resto da `cowork progetto`. Quando l'autore chiede a una chat «sei allineato?»,
risponde con il suo ruolo, l'ultimo commit che vede sul ramo, la versione del
LEGGIMI e le richieste del suo ruolo ancora senza risposta.

## Per aprire una richiesta nuova

Si scrive `cowork-<argomento>.md` nella cartella a cui serve, con le istruzioni
complete e il formato della risposta. Poi, nello stesso giro, commit e push sul
ramo del canale. Le cartelle dove serve il web sono elencate in
`RICERCA-WEB.md`, alla radice del repository.

Ogni richiesta comincia con l'intestazione comune — titolo, riga `Ruolo:`,
regole, dove va la risposta — che dà `cowork.intestazione()`: senza la riga del
ruolo nessuna chat la prende.

Le richieste che ogni libro fa sempre non si scrivono a mano: le produce il
sistema, uguali per ogni libro.

| richiesta | ruolo | quando | comando |
|---|---|---|---|
| `concorrente/cowork-concorrente.md` (o `cowork-nicchia.md`) | concorrente | fine delle domande d'avvio | `avvio <slug>` |
| `concorrente/cowork-parole-chiave.md` | parole-chiave | fine delle domande d'avvio | `avvio <slug>` |
| `manuale/cowork-verifica-parole-chiave.md` | parole-chiave | scheda prodotto (fase 6) | `parole-chiave <slug>` |

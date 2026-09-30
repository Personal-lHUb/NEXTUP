# Il canale con Cowork

La fabbrica gira in un container che non raggiunge Amazon né KDP. Le ricerche
web le fa Cowork (app Claude Desktop) sul computer dell'autore. Lo scambio
avviene per file, e gira da solo: nessuno deve copiare niente a mano.

```
fabbrica (questa sessione)          Google Drive                        Cowork
────────────────────────────        «NEXTUP — libri/cowork»             ───────────────────────
scrive cowork-<arg>.md nel repo ─▶  <chiave>--cowork-<arg>.md      ─▶   legge ed esegue
applica, segna «Stato: applicata» ◀─ <chiave>--cowork-<arg>-risposta.md ◀─ scrive la risposta
```

- La **chiave** è lo slug del libro, oppure `sistema` per le regole comuni in
  `config/`. Serve perché la casella è una cartella sola per tutti i libri.
- Il **repository** è l'archivio: richieste e risposte ci restano, con la
  storia di git. Drive è solo la casella.
- Lo **stato** lo calcola `python3 -m kdpfactory cowork stato` (con `--json`
  per i nomi su Drive):
  - *aperta*: la richiesta non ha risposta;
  - *risposta arrivata*: la risposta c'è ma non è stata applicata;
  - *applicata*: la richiesta contiene la riga `Stato: applicata`.
- L'**avviso** per Cowork lo scrive `python3 -m kdpfactory cowork avviso`, ed
  elenca solo le richieste aperte.
- La casella è in `config/cowork.json`: nome, id e link della cartella.
- Il passaggio da GitHub Desktop (vedi `CLAUDE.md`) resta come riserva manuale:
  i file hanno gli stessi nomi, senza il prefisso della chiave.

## Il giro automatico

Due appuntamenti fissi, sfalsati, così una risposta scritta al mattino è
applicata lo stesso giorno.

### 1. Cowork — attività pianificata (la imposta l'autore, una volta)

In Claude Desktop, in Cowork, c'è l'attività pianificata «Cowork — casella NEXTUP».
Gira ogni giorno alle 7:52 e alle 13:52, ora di Roma, sul portatile dell'autore, che
deve essere acceso. Se un giro salta, la risposta arriva al giro dopo: non è un
errore. Prompt:

```
Apri la cartella Google Drive «NEXTUP — libri/cowork»
(https://drive.google.com/drive/folders/1yprHuxzFDGj12k8clTp0othzTXjiyn5N).

Cerca i file che finiscono in .md e contengono «--cowork-», esclusi quelli che
finiscono in «-risposta.md». Per ciascuno controlla se nella cartella esiste già
il file con lo stesso nome e «-risposta» prima di «.md». Se esiste, salta la
richiesta: è già stata fatta.

Per ogni richiesta senza risposta:
1. leggila per intero ed esegui quello che chiede;
2. scrivi la risposta nella stessa cartella, come file Markdown (.md, non Google
   Doc), con il nome della richiesta più «-risposta» prima di «.md»
   (esempio: household-bills--cowork-amazon.md → household-bills--cowork-amazon-risposta.md);
3. non modificare e non cancellare il file della richiesta.

Regole valide per tutte le richieste:
- per ogni punto riporta il fatto che hai visto sulla pagina, non una stima, con
  l'URL e la data e l'ora della verifica;
- se una pagina chiede un captcha o l'accesso e non riesci ad andare avanti,
  scrivilo nel punto invece di stimare;
- su KDP (kdp.amazon.com) leggi e basta: non creare titoli, non salvare bozze,
  non pubblicare, non cambiare impostazioni;
- nessuna password, codice o cookie nei file.

Se non ci sono richieste senza risposta, fermati senza scrivere niente.
```

### 2. La fabbrica — controllo pianificato (routine su questa sessione)

Ogni giorno alle 9:59 e alle 15:59 (ora di Roma) la routine «Controllo Cowork»
riprende la sessione della fabbrica ed esegue:

1. aggiorna il repository dal ramo di lavoro;
2. `python3 -m kdpfactory cowork stato --json`;
3. porta nella casella ogni richiesta che il registro segna «da caricare» e
   registra il caricamento con `cowork registra <percorso> <id su Drive>`;
   per quelle «cambiata dopo l'invio» vale la regola qui sotto;
4. scarica ogni risposta nuova della casella nel percorso indicato da `risposta`,
   con la copia di backup; poi commit e push;
5. applica le risposte secondo `CLAUDE.md` e le linee guida: i dati nei file
   del libro, le affermazioni smentite all'editor, e ci si ferma per le
   decisioni dell'autore. Poi aggiunge `Stato: applicata il <data>` alla
   richiesta, e scrive all'autore una riga per ogni risposta applicata:
   «<richiesta>: applicata, <cosa è cambiato>, <decisioni che ti servono>»;
6. se non c'è niente di nuovo, non scrive niente.

## Regole di ingaggio

- **Una richiesta nuova entra nella casella nello stesso giro in cui nasce**,
  non solo nel repo, e il caricamento si registra subito
  (`cowork registra`). `cowork stato` segna «da caricare» quelle che mancano, e
  `cowork avviso` lo ricorda prima di mandare l'avviso.
- **Un file «-risposta.md» nella casella è di Cowork**: la fabbrica lo legge e
  lo scarica, non lo modifica mai. Se una risposta è incompleta o bloccata
  (captcha, accesso), si apre una richiesta nuova `cowork-<argomento>-2.md`
  con i soli punti mancanti.
- **Una richiesta modificata dopo l'invio** (`cowork stato` la segna «cambiata
  dopo l'invio»): la copia vecchia va nel cestino di Drive prima di caricare la
  nuova, e una risposta già scritta a quella vecchia è superata. Se la risposta
  c'è già, la richiesta corretta si carica come `cowork-<argomento>-2.md`: con
  lo stesso nome, Cowork troverebbe la risposta vecchia e salterebbe quella
  nuova.
- **Ci si ferma dall'autore** solo per le sue decisioni (categoria, titolo,
  promessa, voce narrante, prezzo, pubblicazione) e per l'immagine di
  copertina.

## Per aprire una richiesta nuova

Si scrive `cowork-<argomento>.md` nella cartella a cui serve:
- `books/<slug>/manuale/` per un libro;
- `books/<slug>/concorrente/` per la pagina del concorrente;
- `config/` per le regole comuni.

La richiesta deve contenere le istruzioni complete e il formato della risposta.
Poi si fa il commit: il resto lo fa il giro automatico. Le cartelle dove serve il
web sono elencate in `RICERCA-WEB.md`, alla radice del repository.

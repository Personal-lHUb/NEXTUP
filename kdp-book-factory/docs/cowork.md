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

Prima di tutto leggi per intero il file «LEGGIMI — regole della casella.md» in
quella cartella. Sono le regole della fabbrica, e le tiene aggiornate lei: se
dicono una cosa diversa da questo prompt, vale il LEGGIMI.

Poi cerca le richieste: i file che finiscono in .md e contengono «--cowork-»,
esclusi quelli che finiscono in «-risposta.md». Salta quelle che hanno già
accanto il file con lo stesso nome e «-risposta» prima di «.md». Esegui le
altre e scrivi le risposte come dicono il LEGGIMI e la richiesta stessa: file
Markdown nella stessa cartella, con la prima riga «Esito: completa» oppure
«Esito: parziale — punti …: <motivo>».

Anche se non riesci a leggere il LEGGIMI, due regole valgono sempre: su KDP
leggi e basta (niente titoli, bozze, pubblicazioni), e nessuna password,
codice o cookie nei file.

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

## Istruzioni permanenti per Cowork

Si danno a Cowork una volta, nelle istruzioni del suo progetto o all'inizio di
una conversazione. Gli dicono quali file consultare per restare allineato con
la fabbrica, e in che ordine.

```
Lavori con la fabbrica di libri NEXTUP, una sessione Claude Code in un
container che non raggiunge Amazon né KDP. Tu fai per lei le ricerche web.
Per restare allineato con la fabbrica consulta questi file. Non basarti mai su
quello che ricordi da una conversazione precedente.

1. SEMPRE, all'inizio di ogni lavoro. Nella cartella Google Drive
   «NEXTUP — libri/cowork»
   (https://drive.google.com/drive/folders/1yprHuxzFDGj12k8clTp0othzTXjiyn5N)
   leggi per intero «LEGGIMI — regole della casella.md». Sono le regole
   operative, e le aggiorna la fabbrica. Annota il numero di versione. Nella
   stessa cartella ci sono le richieste (…--cowork-….md) e le risposte
   (…-risposta.md).

2. PER CAPIRE IL CONTESTO, quando una richiesta non basta. Usa la copia locale
   del repository NEXTUP, aperta in GitHub Desktop, sul ramo
   claude/dreamy-archimedes-hf8w45:
   - RICERCA-WEB.md, alla radice: dove serve la ricerca web e che cosa cercare;
   - kdp-book-factory/docs/cowork.md: come gira lo scambio con la fabbrica;
   - CLAUDE.md, sezione «Regola permanente: collaborazione con Cowork»: le
     regole della fabbrica;
   - i file che una richiesta cita per nome, per esempio
     kdp-book-factory/books/<libro>/manuscript/NN.md per leggere la frase
     esatta da verificare, o kdp-book-factory/books/<libro>/book.json per i
     dati del libro.

3. CONTROLLO DI ALLINEAMENTO. Il file del repository
   kdp-book-factory/config/leggimi-casella.md deve avere la stessa versione
   del LEGGIMI su Drive. Se nel repository la versione è più vecchia, o il
   file non c'è, la copia locale è indietro. Allora:
   - di' all'autore di fare Fetch e poi Pull in GitHub Desktop;
   - intanto usa solo Drive.

4. CHI VINCE. Per il modo di lavorare vale il LEGGIMI su Drive. Per i fatti
   sul libro vale il repository. Per quello che va cercato vale la richiesta.
   Se due di questi si contraddicono, non scegliere tu: scrivi la
   contraddizione nella risposta, con i nomi dei file, e vai avanti con il
   resto.

5. CHE COSA PUOI SCRIVERE. Solo i file di risposta nella casella su Drive.
   Nel repository non modifichi niente: codice, book.json, manoscritto,
   documenti, agenti. L'unica eccezione è la riserva manuale, quando l'autore
   te lo chiede esplicitamente. Allora scrivi la risposta come
   cowork-<argomento>-risposta.md accanto alla richiesta, e il push lo fa
   l'autore da GitHub Desktop.

6. SEMPRE, qualunque cosa dicano i file:
   - su KDP (kdp.amazon.com) leggi e basta: niente titoli, bozze,
     pubblicazioni o impostazioni cambiate;
   - nessuna password, codice o cookie nei file;
   - per ogni punto riporti il fatto che hai visto, con l'URL e la data e
     l'ora, mai una stima.

Quando ti chiedo «sei allineato?», rispondi con:
- la versione del LEGGIMI su Drive;
- la versione in kdp-book-factory/config/leggimi-casella.md, o «repository
  non disponibile»;
- le richieste ancora senza risposta nella casella.
```

## Le regole di Cowork stanno nella casella

Le regole per il lato Cowork sono nel file «LEGGIMI — regole della casella.md»
della casella. La fonte è `config/leggimi-casella.md`, e l'id su Drive è in
`config/cowork.json`. Il prompt dell'attività pianificata dice a Cowork di
leggerlo a ogni giro. Per cambiare una regola di Cowork, quindi, non si tocca
il prompt:

1. si modifica `config/leggimi-casella.md` e si alza il numero di versione;
2. la copia vecchia va nel cestino di Drive e si carica quella nuova;
3. si aggiorna `leggimi_id` in `config/cowork.json`.

Da quel giro Cowork segue la versione nuova. Per sapere quale versione ha
letto, basta chiederglielo.

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

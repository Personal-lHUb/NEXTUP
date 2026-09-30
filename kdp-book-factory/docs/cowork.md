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
  n'è una ancora da inviare, lo dice prima.
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

## Il giro automatico

Due appuntamenti fissi, sfalsati, così una risposta scritta al mattino è
applicata lo stesso giorno.

### 1. Cowork — attività pianificata

In Claude Desktop, in Cowork, c'è l'attività pianificata «Cowork — casella
NEXTUP». Gira ogni giorno alle 7:52 e alle 13:52, ora di Roma, sul portatile
dell'autore, che deve essere acceso. Se un giro salta, la risposta arriva al
giro dopo: non è un errore. Prompt:

```
Lavora sul repository GitHub Personal-lHUb/NEXTUP, ramo
claude/dreamy-archimedes-hf8w45. Se hai accesso diretto a GitHub, leggilo
da lì. Se usi la copia locale aperta in GitHub Desktop, prima aggiornala dal
ramo remoto con Fetch e Pull; se non puoi farlo tu, fermati e chiedilo
all'autore.

Prima di tutto leggi per intero kdp-book-factory/config/leggimi-cowork.md.
Sono le regole della fabbrica, e le tiene aggiornate lei: se dicono una cosa
diversa da questo prompt, vale il LEGGIMI.

Poi cerca le richieste: i file cowork-*.md sotto kdp-book-factory/, esclusi
quelli che finiscono in -risposta.md e quelli nelle cartelle backup e build.
Salta quelle che hanno già accanto il file con lo stesso nome e -risposta, e
quelle che contengono «Stato: applicata». Esegui le altre e scrivi le
risposte come dicono il LEGGIMI e la richiesta stessa, con la prima riga
«Esito: completa» oppure «Esito: parziale — punti …: <motivo>». Poi fai il
commit delle sole risposte sullo stesso ramo, e il push se puoi.

Anche se non riesci a leggere il LEGGIMI, due regole valgono sempre: su KDP
leggi e basta (niente titoli, bozze, pubblicazioni), e nessuna password,
codice, token o cookie nei file o nei commit.

Se non ci sono richieste senza risposta, fermati senza scrivere niente.
```

Se Cowork non ha accesso diretto a GitHub, restano due passi dell'autore in
GitHub Desktop: il Pull prima del giro e il push delle risposte dopo. Con
l'accesso diretto non serve nessun passo a mano.

### 2. La fabbrica — controllo pianificato (routine su questa sessione)

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

Si danno a Cowork una volta, nelle istruzioni del suo progetto o all'inizio di
una conversazione. Gli dicono quali file consultare per restare allineato con
la fabbrica, e in che ordine.

```
Lavori con la fabbrica di libri NEXTUP, una sessione Claude Code in un
container che non raggiunge Amazon né KDP. Tu fai per lei le ricerche web.
Tutto passa dal repository GitHub Personal-lHUb/NEXTUP, ramo
claude/dreamy-archimedes-hf8w45. Per restare allineato consulta questi file.
Non basarti mai su quello che ricordi da una conversazione precedente.

0. PRIMA DI TUTTO, la versione giusta. Leggi dal ramo remoto se hai accesso
   diretto a GitHub. Se usi la copia locale di GitHub Desktop, aggiornala con
   Fetch e Pull; se non puoi farlo tu, chiedilo all'autore prima di
   cominciare.

1. SEMPRE, all'inizio di ogni lavoro: kdp-book-factory/config/leggimi-cowork.md.
   Sono le regole operative, e le aggiorna la fabbrica. Annota il numero di
   versione.

2. PER CAPIRE IL CONTESTO, quando una richiesta non basta:
   - RICERCA-WEB.md, alla radice: dove serve la ricerca web e che cosa cercare;
   - kdp-book-factory/docs/cowork.md: come gira lo scambio con la fabbrica;
   - CLAUDE.md, sezione «Regola permanente: collaborazione con Cowork»: le
     regole della fabbrica;
   - i file che una richiesta cita per nome, per esempio
     kdp-book-factory/books/<libro>/manuscript/NN.md per leggere la frase
     esatta da verificare, o kdp-book-factory/books/<libro>/book.json per i
     dati del libro.

3. CHI VINCE. Per il modo di lavorare vale il LEGGIMI. Per i fatti sul libro
   valgono i file del libro. Per quello che va cercato vale la richiesta. Se
   due di questi si contraddicono, non scegliere tu: scrivi la contraddizione
   nella risposta, con i nomi dei file, e vai avanti con il resto.

4. CHE COSA PUOI SCRIVERE. Solo i file di risposta
   (cowork-<argomento>-risposta.md, accanto alla richiesta), con un commit sul
   ramo claude/dreamy-archimedes-hf8w45. Non modifichi niente altro: né le
   richieste, né il LEGGIMI, né codice, book.json, manoscritto, documenti o
   agenti. Il push lo fai tu se hai accesso diretto a GitHub; se no, lo fa
   l'autore da GitHub Desktop.

5. SEMPRE, qualunque cosa dicano i file:
   - su KDP (kdp.amazon.com) leggi e basta: niente titoli, bozze,
     pubblicazioni o impostazioni cambiate;
   - nessuna password, codice, token o cookie nei file o nei commit;
   - per ogni punto riporti il fatto che hai visto, con l'URL e la data e
     l'ora, mai una stima.

Quando ti chiedo «sei allineato?», rispondi con:
- l'ultimo commit che vedi sul ramo claude/dreamy-archimedes-hf8w45, con
  hash e data;
- la versione di kdp-book-factory/config/leggimi-cowork.md;
- le richieste ancora senza risposta.
```

## Per aprire una richiesta nuova

Si scrive `cowork-<argomento>.md` nella cartella a cui serve, con le istruzioni
complete e il formato della risposta. Poi, nello stesso giro, commit e push sul
ramo del canale. Le cartelle dove serve il web sono elencate in
`RICERCA-WEB.md`, alla radice del repository.

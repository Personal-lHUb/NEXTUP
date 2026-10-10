# NEXTUP — istruzioni per Claude Code

`kdp-book-factory/` è una fabbrica di libri per Amazon KDP: interno PDF,
copertina, EPUB, scheda prodotto, con un collegio di agenti. Tutto in italiano;
i libri nella lingua del mercato.

**All'inizio di ogni sessione leggi `STATO.md`** (libro in corso, fase, che cosa
si aspetta; arriva da solo con l'hook d'avvio). **Alla fine aggiornalo.** Una
sessione fa una fase del libro, poi si chiude: la successiva riparte dai file,
non dalla memoria della chat.

**Il contesto non si perde** (scelta dell'autore, 10 ottobre 2026): gli hook di
`.claude/settings.json` (`kdpfactory/diario.py`) salvano il prompt di ogni
agente in `books/<slug>/prompt/`, scrivono nel diario del libro
(`books/<slug>/diario.md`) lancio, id e fine di ogni agente, mettono in
`consegne/` una risposta lunga e lasciano scrivere agli agenti solo lì; a ogni
avvio e dopo ogni riassunto della chat rimettono in contesto STATO.md, la
produzione, gli agenti in volo, le consegne da importare e la coda del diario.
Diario, prompt e consegne entrano in git; una nota a mano: `diario <slug> --nota`.

## Regole permanenti

1. **Un libro alla volta**: quello in `config/produzione.json` (`attivi`).
2. **Le fasi di `docs/linee-guida.md`, in ordine**, e non si passa alla
   successiva col cancello aperto (zero bloccanti del revisore di scaletta,
   pagine nell'intervallo, zero errori di `qa`).
3. **Gli agenti si chiamano da soli** quando la fase lo richiede,
   senza chiedere il permesso. Ognuno ha **un campo solo** (`kdpfactory/agents/competenze.py`) e
   **il suo modello** (`MODELLI`: opus scrive o giudica, sonnet estrae e
   controlla, haiku esegue un comando). Chiedi all'agente solo il suo campo;
   dagli i percorsi, non il testo, e il suo file di consegna
   (`books/<slug>/consegne/<nome>.md`): scrive lì l'uscita intera e risponde
   con una riga. Nel libro la porta `consegna <slug> <file> --capitoli N …` (o
   `--in <percorso>`), col backup; mai ricopiarla dalla chat. Confini: le promesse della vetrina le giudica
   solo il `lettore-cieco`; i conti interni sono dell'`editor-sviluppo`, il
   `fact-checker` guarda solo il mondo fuori; la copertina è dell'agente
   `copertina`. Un confine si sposta nella tabella, poi
   `python3 -m kdpfactory agents --install ../.claude/agents`.
4. **Tutto quello che si misura lo fa un comando**, non un agente né la chat.
5. **Decisioni dell'autore: niente silenzio-assenso** (sua scelta, 10 ottobre
   2026). Categoria, titolo, promessa, voce, prezzo, formato, direzione d'arte e
   variante di copertina, pseudonimo, pubblicazione: `decisioni <slug>
   --proponi …` registra la proposta con le alternative, e la decisione aspetta
   la sua risposta, senza scadenza (`silenzio_assenso_ore: null` in
   `config/produzione.json`). Intanto va avanti il lavoro che non ne dipende.
6. **Ogni passo lo fa partire l'autore** (sua scelta, 10 ottobre 2026). Fra
   un suo messaggio e l'altro non parte niente: nessuna fase, nessun agente,
   nessun bozzetto. Il compito che dà si porta a termine (agenti, comandi,
   backup, commit e push sul ramo), poi ci si ferma e gli si dice qual è il
   passo dopo. **Niente si programma**: nessun `send_later`, nessuna routine,
   nessun lancio di Cowork; le routine restano spente, non si cancellano. Se un
   limite d'uso ferma il lavoro, si scrive nel diario dov'era e che cosa manca,
   e si aspetta il suo «continua». Le spese e le generazioni a pagamento
   aspettano il suo consenso. Quando qualcosa aspetta lui: una riga in chat e
   una notifica push. Gli hook del contesto restano: registrano, non avviano.
7. **Ogni libro nuovo parte dalle sette domande d'avvio** (`avvio <slug>
   --json`): il concorrente (ASIN) si chiede nel messaggio, le altre a scelta;
   `--predefinite` se l'autore lascia decidere.
8. **Copia di backup di ogni file generato.** La pipeline la fa da sé
   (`backup/<slug>/…`, mai `--no-backup` se non lo chiede l'autore); quello che
   generi a mano va in `backup/manuale/<AAAAMMGG-hhmmss>/`, con i percorsi
   relativi; prima di sovrascrivere o cancellare, copia forzata. `backup/` non
   entra in git.
9. **I prompt delle immagini li scrive il sistema** (`copertina <slug>`,
   `immagini <slug>`), mai la chat. Il testo di copertina lo compone il motore in
   vettoriale; l'immagine deve rappresentare il libro; l'interno è in bianco e
   nero. Tre direzioni d'arte e un bozzetto per direzione, poi le varianti finali
   solo dalla direzione scelta. Le figure entrano solo se spiegano meglio del
   testo; generate, oppure pubbliche solo se pubblico dominio o CC0. Le
   immagini le genera questa sessione con Higgsfield (`--genera`, o il
   connettore); le varianti pagate non si rigenerano. Dettagli:
   `docs/copertine.md`.
10. **Lo standard è quello di un editore di saggistica**
   (`docs/standard-editoriale.md`); l'indice corrisponde al libro nei due sensi,
   e lo misura `qa`. Se un libro ne ha bisogno, si cambia il motore per tutti.
11. **I file si salvano solo su GitHub.** Google Drive non si usa più.

## Le due categorie

Ogni libro è **full-content** (testo pieno da leggere, nessuna pagina da
compilare) oppure **medium-content** (interattivo: ogni pagina con contenuti,
layout o stimoli diversi; non un quaderno di righe vuote, non un saggio con
esercizi in coda). Si decide prima della scaletta, in `book.json`
(`content_type`), e vincola impaginazione, scheda, categorie, prezzo e formula
di copertina. In `books/` c'è anche `collaudo`, che non è un libro
(`banco_di_prova: true`).

## Cowork (app Claude Desktop)

Il container non raggiunge amazon.com, KDP, ChatGPT né il portatile
dell'autore: quello lo fa Cowork. Le richieste sono file `cowork-<argomento>.md`
sul ramo di lavoro, elencate in `config/cowork-aperte.md`; Cowork le legge dagli
indirizzi pubblici e su GitHub non scrive. Consegna la risposta come testo
lanciando la routine della fabbrica, e la sessione la salva con
`cowork corriere --ricevi <file>`. Un `-risposta.md` non si modifica mai: se è
incompleto, si apre un seguito `-2`. Le regole per Cowork stanno in
`config/leggimi-cowork.md`. Ogni giro di Cowork costa: si lancia solo col consenso
dell'autore. Dettagli: `docs/cowork.md`.

## Rami e comandi

- Si lavora su `claude/dreamy-archimedes-hf8w45`; dopo ogni commit
  `git branch -f claude/amazing-brahmagupta-xaph52 HEAD` e push di tutti e due.
- Da `kdp-book-factory/`: test `python3 -m unittest discover -s tests` (nessuna
  rete), lint `ruff check kdpfactory tests`, a che punto è il libro
  `python3 -m kdpfactory produzione`, stato di Cowork
  `python3 -m kdpfactory cowork stato`.
- Senza chiave API si lavora con `manuale <slug> <passo>`
  (`docs/linea-manuale.md`); impaginazione, copertina, controlli, prezzi ed EPUB
  non chiamano mai il modello.

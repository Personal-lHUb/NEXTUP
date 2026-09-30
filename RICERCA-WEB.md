# Ricerca web: le cartelle per Cowork

La fabbrica (`kdp-book-factory/`) gira in un container cloud che non raggiunge
Amazon né KDP: il proxy le rifiuta per policy. Anche gli agenti di controllo
lavorano senza web, e il fact-checker giudica le affermazioni del libro in base
a quello che sa già. Queste sono le cartelle dove serve una ricerca web, fatta
da Cowork sul computer dell'autore, dove il browser ha già l'accesso a KDP.

## Le cartelle

| cartella | che cosa si cerca sul web | Cowork scrive in | stato |
|---|---|---|---|
| `kdp-book-factory/ricerca/` | le regole KDP che la pipeline usa per ogni libro: costi di stampa, dorso, abbondanze, parole chiave, descrizione | `ricerca/risposte.md` | aperta: i costi di stampa non sono mai stati verificati |
| `kdp-book-factory/books/household-bills/ricerca/` | per «Bills in Order»: selettore delle categorie KDP, affollamento, titolo, parole chiave, dati del concorrente; le affermazioni del libro sul mondo, da controllare sulle fonti ufficiali prima della stampa | `books/household-bills/ricerca/risposte.md` | aperta: 18 richieste |
| `kdp-book-factory/books/skill-acquisition/concorrente/` | la pagina Amazon del concorrente ASIN 1797031856 (fase 0 di un libro nuovo) | `concorrente/pagina.md`: si incolla la pagina sotto il commento, come dice il file | aperta: il file ha solo il commento |
| `kdp-book-factory/books/<slug>/concorrente/` | per ogni libro nuovo: la pagina del concorrente su amazon.com, con le recensioni | `concorrente/pagina.md` | si apre a ogni `concorrente new` |

In queste cartelle Cowork **non deve** fare ricerca:

- `manuscript/`, `manuale/` e `build/`: il testo e l'impaginato;
- `outline.json`, `book.json` e `state.json`: i dati del libro;
- `kdpfactory/`, `config/` e `tests/`: il codice e la configurazione.

Lì scrive la fabbrica, che fa i backup e ripassa i controlli. I dati che
Cowork trova entrano in quei file attraverso la fabbrica.

## Come si lavora in sincrono

1. **Una cartella, due ruoli.** In ogni cartella `ricerca/` la fabbrica scrive
   `richieste.md` e Cowork scrive `risposte.md`. Nessuno dei due tocca il file
   dell'altro, così le modifiche non si scontrano mai.
2. **Il ramo.**
   - Cowork lavora su un clone di `github.com/Personal-lHUb/NEXTUP`, parte da
     `claude/amazing-brahmagupta-xaph52` e fa il push sul ramo
     `cowork/ricerca`.
   - La fabbrica lo unisce al suo ramo. Siccome i file sono separati, l'unione
     non va in conflitto.
   - Se Cowork non può fare il push, l'autore incolla `risposte.md` nella chat
     della fabbrica.
3. **Formato delle risposte.** Usa la stessa numerazione delle richieste. Per
   ogni punto metti:
   - il fatto visto sulla pagina, non una stima;
   - l'URL della fonte;
   - la data e l'ora della verifica.

   Se una pagina chiede un captcha o l'accesso e non si riesce ad andare
   avanti, scrivilo invece di stimare.
4. **Nessuna credenziale.** Password, codici e cookie non vanno in nessun file e
   in nessun commit.
5. **KDP in sola lettura.** Non si creano titoli, non si salvano bozze, non si
   pubblica. La pubblicazione è una decisione dell'autore.
6. **Chiusura.** Quando `risposte.md` c'è, la fabbrica porta i dati nei file
   giusti:
   - le categorie in `book.json` e nella scheda;
   - i costi in `config/printing_costs.json`;
   - le affermazioni smentite al capitolo, con l'editor e poi con una nuova
     impaginazione.

   Poi la fabbrica segna la richiesta come chiusa in `richieste.md`.

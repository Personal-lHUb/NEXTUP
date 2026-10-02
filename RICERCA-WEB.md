# Ricerca web: le cartelle per Cowork

La fabbrica (`kdp-book-factory/`) gira in un container cloud che non raggiunge
Amazon né KDP. Anche gli agenti di controllo lavorano senza web: il
fact-checker, per esempio, giudica le affermazioni del libro in base a quello
che sa già. Qui sotto sono elencate le cartelle dove serve una ricerca web.
La fa Cowork, sul computer dell'autore.

Lo scambio segue la regola di `CLAUDE.md`, «collaborazione con Cowork», e
passa dal repository GitHub `Personal-lHUb/NEXTUP`, ramo
`claude/dreamy-archimedes-hf8w45`:
- la richiesta è in `cowork-<argomento>.md`;
- la risposta va accanto, in `cowork-<argomento>-risposta.md`;
- Cowork scrive solo i file di risposta e ne fa il commit sul ramo;
- le regole per Cowork sono in `kdp-book-factory/config/leggimi-cowork.md`.

## Le cartelle dove serve il web

Ogni richiesta ha un ruolo, e ogni ruolo una chat nel progetto Cowork
(`kdp-book-factory/config/progetto-cowork.md`).

| cartella | ruolo | che cosa si cerca | richiesta | stato |
|---|---|---|---|---|
| `kdp-book-factory/config/` | regole-kdp | Le regole KDP che valgono per ogni libro: costi di stampa, dorso, abbondanze, pagine minime e massime, limiti di parole chiave e descrizione, selettore delle categorie. | `cowork-kdp.md`, `cowork-kdp-2.md` | `cowork-kdp` applicata il 1° ottobre; aperto il seguito `-2` (pagine massime crema 6x9, lunghezza delle parole chiave, selettore delle categorie di «Bills in Order»: serve l'accesso a KDP) |
| `kdp-book-factory/books/<slug>/concorrente/` | concorrente | Per ogni libro nuovo: la pagina Amazon del concorrente, recensioni comprese, e la sua copertina in miniatura. Se il concorrente è da trovare, prima i primi 20 della nicchia. La scrive `avvio <slug>` a fine domande; la risposta il reparto la legge dov'è. | `cowork-concorrente.md` (o `cowork-nicchia.md`) | — |
| `kdp-book-factory/books/<slug>/concorrente/` | parole-chiave | Per ogni libro nuovo: le parole chiave della nicchia, con Amazon, Helium 10, Publisher Rocket e Google Trends. La scrive `avvio <slug>`; la legge il posizionamento. | `cowork-parole-chiave.md` | — |
| `kdp-book-factory/books/<slug>/manuale/` | parole-chiave | Alla scheda: la verifica delle sette parole chiave scelte e l'affollamento delle categorie. La scrive `parole-chiave <slug>`. | `cowork-verifica-parole-chiave.md` | — |
| `kdp-book-factory/books/<slug>/manuale/` | fonti | Le affermazioni del libro sul mondo (enti, siti, numeri di telefono, regole), da controllare sulla fonte ufficiale prima della stampa. | `cowork-fonti.md` | — |
| `kdp-book-factory/books/household-bills/` | — | «Bills in Order»: `manuale/cowork-amazon.md` e `cowork-fonti.md` applicate il 1° ottobre; `cowork-amazon-2.md` ritirata e divisa fra i ruoli. Aperte: `concorrente/cowork-prezzo.md` (concorrente: prezzo in USD) e `manuale/cowork-verifica-parole-chiave.md` (parole-chiave). | | in attesa |
| `kdp-book-factory/books/psychic-intuition/concorrente/` | — | Il libro contro «Awakening Your Psychic Ability» (ASIN B0B6NY89RB): pagina del concorrente e parole chiave della nicchia. | `cowork-concorrente.md`, `cowork-parole-chiave.md` | in attesa |
| `kdp-book-factory/books/dementia-family/concorrente/` | — | Il libro contro «The Vanishing Family» (ASIN B0GN73RYMF): pagina del concorrente e parole chiave della nicchia. | `cowork-concorrente.md`, `cowork-parole-chiave.md` | in attesa |
| `kdp-book-factory/books/skill-acquisition/concorrente/` | — | La pagina del concorrente ASIN 1797031856. `pagina.md` ha solo il commento. | ancora nessuna | in attesa: si apre con `avvio` se il libro parte |

Nelle altre cartelle il web non serve:
- `manuscript/`, `build/`, `outline.json`, `book.json` e `state.json` del libro;
- `kdpfactory/`, `tests/` e `docs/`.

Lì scrive solo la fabbrica, che fa i backup e rilancia i controlli. Quello che
Cowork trova entra in questi file passando dalla fabbrica.

## Formato delle risposte

- La stessa numerazione della richiesta.
- Per ogni punto: il fatto visto sulla pagina, non una stima, con l'URL e la data e l'ora della verifica.
- Se una pagina chiede un captcha o l'accesso e non si va avanti, va scritto invece di stimare.
- KDP in sola lettura: non si creano titoli, non si salvano bozze, non si pubblica.
- Nessuna password, codice o cookie nei file o nei commit.

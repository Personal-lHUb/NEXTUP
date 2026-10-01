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

| cartella | che cosa si cerca | richiesta | stato |
|---|---|---|---|
| `kdp-book-factory/config/` | Le regole KDP che valgono per ogni libro: costi di stampa (`printing_costs.json` non è mai stato verificato), dorso, abbondanze, pagine minime e massime, limiti di parole chiave e descrizione. | `cowork-kdp.md`, `cowork-kdp-2.md` | applicata il 1° ottobre; aperto il seguito `-2` (pagine massime crema 6x9, lunghezza delle parole chiave: serve l'accesso a KDP) |
| `kdp-book-factory/books/household-bills/manuale/` | Amazon e KDP per «Bills in Order»: selettore delle categorie, affollamento, titolo, parole chiave, dati di oggi del concorrente. | `cowork-amazon.md`, `cowork-amazon-2.md` | risposta arrivata, in applicazione (parole chiave e titolo agli agenti); aperto il seguito `-2` (selettore KDP, ranghi del cartaceo, prezzo del concorrente in USD) |
| `kdp-book-factory/books/household-bills/manuale/` | Le affermazioni del libro sul mondo (enti, siti, numeri di telefono, regole federali), da controllare sulla fonte ufficiale prima della stampa. | `cowork-fonti.md` | applicata il 1° ottobre: 11 affermazioni confermate, 2 riformulate (capitoli 22 e 27) |
| `kdp-book-factory/books/<slug>/concorrente/` | Per ogni libro nuovo: la pagina Amazon del concorrente, recensioni comprese (fase 0). Cowork la riporta in `cowork-concorrente-risposta.md`, poi la fabbrica la mette in `pagina.md`. | `cowork-concorrente.md`, alla fase 0 | — |
| `kdp-book-factory/books/skill-acquisition/concorrente/` | La pagina del concorrente ASIN 1797031856. `pagina.md` ha solo il commento. | ancora nessuna | in attesa: si apre se il libro parte |

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

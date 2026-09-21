# Il team di miglioramento

Cinque agenti il cui compito non è produrre libri, ma **rendere il sistema che
li produce più efficace**. Non sono il collegio editoriale: quello lavora su un
libro alla volta e sta dentro la pipeline (`kdpfactory/agents/`). Questi
lavorano sul sistema, stanno in `.claude/agents/` e li invochi tu.

Il criterio che li ordina tutti è uno: **vendere libri**. Codice, costi, test e
copertine sono mezzi, e ogni segnalazione va pesata per quanto sposta quel
risultato. Quando non lo sposta, va detto — un miglioramento tecnico che non
cambia nulla di commerciale resta utile, ma non è una priorità.

## Prima le misure, poi il giudizio

Il team non parte da impressioni. Parte da `diagnostica.json`, che produce
`kdpfactory/diagnostica.py` — un modulo che **non usa il modello**: misura e
basta, come l'agente di impaginazione e quello di copertina.

```bash
cd kdp-book-factory && python3 -m kdpfactory diagnostica
```

Che cosa misura, su tutti i libri in una volta:

| area | che cosa conta |
|---|---|
| **economia** | costo API per libro, token, costo di stampa, prezzo, royalty per copia, **quante copie servono per ripagare la produzione** |
| **produzione** | iterazioni di impaginazione, parole per pagina misurate contro stimate, scarto dalle pagine obiettivo |
| **qualità** | errori e avvisi rimasti sul libro finito, raggruppati per codice |
| **scheda** | i limiti veri di KDP: 7 slot di parole chiave da 50 caratteri, 3 categorie, 4000 caratteri di descrizione, i 185 caratteri prima di «Leggi di più», il troncamento del titolo a 60 |
| **copertina** | le misure di `cover.verifica`: corpo del titolo in miniatura, contrasto, area di sicurezza |
| **sistema** | i difetti che compaiono in **più libri**, e il rapporto fra righe di codice e righe di test |

L'ultima riga è la più importante. Un difetto su un libro è un difetto del
libro; lo stesso difetto su tre libri è un difetto della pipeline, e
correggerlo una volta sistema anche tutti i libri futuri. `diagnostica.json` li
raggruppa da sé, sotto `ricorrenze`.

Gli sprechi della scheda prodotto si misurano allo stesso modo: una parola
chiave che ripete una parola già nel titolo è uno slot buttato, perché il
titolo è indicizzato di suo. Non è un'opinione, è un confronto fra due liste.

**Quello che il rapporto non misura: i banchi di prova.** Una cartella di
`books/` che dichiara `"banco_di_prova": true` in `book.json` — oggi solo
`collaudo` — resta fuori dai conti. È attrezzatura, non un prodotto: la sua
scheda è vuota per definizione e il suo manoscritto è segnaposto, quindi
misurarla produce rilievi ad alto impatto veri nei numeri e falsi nel
significato — esattamente il genere di rumore su cui il team aprirebbe un piano
di lavoro. L'esclusione è scritta nei totali (`banchi_di_prova_esclusi`), e
`python3 -m kdpfactory diagnostica --banchi` li misura lo stesso quando serve
controllare la diagnostica stessa.

## Chi fa cosa

| agente | compito | che cosa consegna |
|---|---|---|
| `capo-collana` | guida il team, ordina per effetto sulle vendite, arbitra | **tre** cose da fare adesso, il resto in ordine, le proposte scartate col motivo |
| `analista-mercato` | perché il libro non viene comprato: ricerca, miniatura, titolo, descrizione, prezzo | il **testo sostitutivo già scritto**, non il consiglio di riscriverlo |
| `ingegnere-pipeline` | difetti del codice, in ordine di gravità *per il libro stampato* | la patch, più il modo di riprodurre il difetto |
| `economo` | quanto costa un libro e in quante copie si ripaga | il conto prima/dopo, col rischio dichiarato |
| `avvocato-del-diavolo` | verifica le proposte degli altri prima che diventino lavoro | regge / regge con riserva / non regge, e il rischio più grande del piano |

L'avvocato del diavolo non ha proposte proprie: esiste perché in un team che
genera idee in fretta serve qualcuno che costi attrito. È lo stesso principio
del lettore cieco e del fact-checker, applicato alle proposte invece che al
testo.

## Il vincolo è negli strumenti, non nelle raccomandazioni

Nessuno dei cinque ha `Edit` o `Write`. Possono leggere, cercare ed eseguire
comandi di verifica — test, lint, diagnostica — ma **non possono modificare un
file**. Il team propone; tu decidi che cosa applicare.

Non è una regola scritta in un prompt che un agente può interpretare male: è
la lista degli strumenti che ricevono.

## Come si usa

```
/migliora
```

Fa il giro completo: misure, le tre analisi in parallelo, la verifica, il
piano. Si può restringere:

```
/migliora <slug>               # un libro solo
/migliora scheda               # solo la resa commerciale
/migliora codice               # solo la pipeline
```

Oppure si chiama un agente singolo, quando sai già che cosa ti serve:

```
Usa l'agente analista-mercato sulla scheda di <slug>.
```

## Che cosa il team non sa

Non ha accesso ai dati di vendita reali: copie vendute, posizione in
classifica, tasso di conversione, ricerche mensili di una parola chiave. Può
dire «questo slot è vuoto» perché lo vede; non può dire «questa parola chiave
porta traffico» perché non lo sa.

Le decisioni che richiedono quei dati finiscono in una sezione apposta del
piano — «quello che non sappiamo» — con l'indicazione di come procurarseli.
È preferibile a un numero inventato che sembra vero.

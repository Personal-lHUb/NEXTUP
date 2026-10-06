# Lo standard editoriale

Il metro dei libri NEXTUP è un libro di saggistica di un grande editore: quello
che un lettore apre in libreria senza chiedersi chi l'ha fatto. Questa pagina
dice che cosa vuol dire in concreto, chi lo fa e chi lo misura. Le regole
valgono per ogni libro: stanno nel motore e nei controlli, non nella chat di un
libro.

## Il testo

Un editore fa passare un libro da più mani, ognuna con il suo campo. Qui le
mani sono gli agenti del collegio (`linee-guida.md`, «Chi fa che cosa»):

| passata | chi | che cosa |
|---|---|---|
| struttura | `architetto`, poi `editor-sviluppo` sul libro scritto | tesi, sequenza, capitoli che servono; contraddizioni e conti fra capitoli |
| riga | `voce` | ritmo, varietà delle frasi, tic da testo generato |
| fatti | `fact-checker` | ogni affermazione sul mondo, con la sua fonte |
| legale | `conformita` | terzi, marchi, consulenza, promesse, avvertenze |
| bozze | `correttore` | refusi, accordi, punteggiatura, maiuscole |
| lettura | `lettore-cieco` | dove ci si perde, e se il libro mantiene la vetrina |

Il cancello è lo stesso di un editore: nessun bloccante aperto prima della
stampa.

## L'impaginazione

| | come la fa un editore | come la fa il motore (`typeset.py`) |
|---|---|---|
| carattere | un carattere da libro, una famiglia sola | **EB Garamond** (licenza OFL, in `fonts/ofl/`); nel testo pieno anche titoli e titoletti, distinti per corpo e peso |
| corpo | 11–12 punti in 6x9 | 11,5 su 15,5 di interlinea (predefinito; `body_font_size`, `leading`) |
| sillabazione | quella del mercato | americana per i libri in inglese (`en_US`), italiana per quelli in italiano |
| numerazione | pagina 1 = prima pagina del testo; le preliminari contano ma non portano il numero | uguale: il folio parte da 1 sul primo titolo del corpo, l'indice stampa quei numeri |
| apertura di capitolo | a destra, calata di un terzo della pagina, prime parole in maiuscoletto | a destra, calata di un quinto della gabbia, le prime tre parole (fino alla prima pausa) in maiuscoletto |
| titoletti | mai in fondo alla pagina senza almeno due righe sotto | uguale; un capoverso lungo si spezza invece di trascinare tutto alla pagina dopo |
| vedove e orfane | nessuna | nessuna (controllo dell'agente `impaginazione`) |
| pagine corte | ogni pagina di testo finisce alla stessa altezza, salvo l'ultima del capitolo | `impaginazione` le conta: nel rodaggio di Bills in Order sono scese da 32 a 4 su 192 |
| righe finali | nessun capoverso chiuso da una parola corta da sola | le ultime parole di ogni capoverso sono legate da spazi unificatori fino a dieci caratteri |
| testatine | titolo del libro a sinistra, capitolo a destra, niente sulle aperture | uguale |
| pagine preliminari | occhiello, frontespizio, colophon, (dedica), indice | uguale |

Il medium-content segue la sua strada: titoli in un'altra famiglia, aperture
compatte e niente maiuscoletto, perché le sue pagine sono schede.

## L'indice, nei due sensi

L'indice è la pagina che il cliente apre nell'anteprima prima di comprare.
Deve corrispondere al libro in tutti e due i sensi, e lo misura
`coerenza.py` dentro `qa`:

1. **titolo deciso = titolo stampato.** Il titolo dell'agente `indice`
   (`manuale/indice.json`) e quello della scaletta sono quelli in testa al
   capitolo. Un capitolo aggiunto dopo l'indice è un errore: torna all'agente.
2. **ogni voce porta dove dice.** Si legge l'indice dal PDF e si apre ogni
   pagina indicata: lì deve aprirsi quel capitolo. Ogni capitolo ha la sua voce,
   nell'ordine del libro.
3. **dal titolo al testo.** Le parole portanti del titolo ricorrono nel
   capitolo: un titolo che promette un argomento di cui il testo non parla è un
   avviso.
4. **dal testo al titolo.** Almeno una parola del titolo è più frequente in quel
   capitolo che nel resto del libro: altrimenti il titolo starebbe bene su un
   altro capitolo, e chi cerca l'argomento non lo trova. L'avviso propone le
   parole che distinguono il capitolo; le stesse parole, per ogni capitolo,
   sono nelle statistiche di `qa` (`indice_parole_distintive`), come guida
   per l'agente `indice`.

I primi due sono errori di stampa. Gli ultimi due sono avvisi con le parole
trovate: se il libro mantiene la promessa dell'indice lo giudica il
`lettore-cieco` leggendo, e i titoli li corregge solo l'agente `indice`.

## Le immagini

I prompt li scrive il sistema (`CLAUDE.md`) e le immagini le genera Higgsfield
da questa sessione: `copertina <slug> --genera` e `immagini <slug> --genera`
(`kdpfactory/higgsfield.py`), sempre alla risoluzione più alta che il modello
dichiara. Per incollarli a mano in ChatGPT il comando
`copertina <slug>` scrive `build/copertina-prompt.txt` e lo stampa nel
terminale: un blocco di testo da incollare così com'è in una chat del progetto
«NEXTUP — Immagini», più il messaggio per le varianti successive e i nomi con
cui salvare le immagini. Il prompt porta solo quello che decide l'immagine
(soggetto, stile, colori detti a parole, composizione, divieti); le specifiche
di stampa restano nel brief completo (`build/copertina-brief.md`), che è il
riferimento dell'agente `copertina`. Per le figure lo stesso fa
`immagini <slug>` in `build/immagini-prompt.txt`, un prompt per figura.

## Che cosa resta all'autore

- **Il marchio editoriale.** Un editore mette il suo nome sul frontespizio e
  sul colophon. `book.json` ha il campo `publisher`: vuoto, il libro esce come
  pubblicazione indipendente.
- **La pagina «One request».** È la pagina finale che chiede una recensione:
  un editore non la stampa, ma su KDP le recensioni muovono le vendite. Resta
  finché l'autore non dice di toglierla.

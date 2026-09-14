# Personalizzazione

Tutto quello che si cambia senza toccare la logica della pipeline.

---

## Formato e impaginazione (`book.json`)

| Campo | Effetto |
|---|---|
| `trim` | formato di rifilo: `5x8`, `5.5x8.5`, `6x9`, `7x10`, `8.5x11`… (`kdpfactory specs` li elenca) |
| `paper` | `cream` (consigliato per il testo), `white`, `color-standard`, `color-premium`. Cambia lo spessore del dorso |
| `body_font` | `serif` o `sans` per il testo corrente (i titoli usano l'altra famiglia) |
| `body_font_size` | corpo in punti: 10,5-11,5 per la narrativa e la saggistica; 12 per manuali e libri per over 60 |
| `leading` | interlinea in punti: 1,35-1,45 volte il corpo |
| `toc_depth` | `1` = solo capitoli nell'indice, `2` = anche le sezioni |
| `include_exercises` | aggiunge a ogni capitolo la sezione `## In pratica` |
| `cover_theme` | `auto`, `notte`, `bosco`, `terracotta`, `indaco`, `carta`, `grafite` |

Corpo e interlinea **cambiano il numero di pagine**: portare il corpo da 11 a 12
punti allunga il libro di circa il 15%. È la leva più rapida quando mancano poche
pagine all'obiettivo, ed è preferibile a interlinee esagerate, che si notano.

Le misure risultanti si controllano prima di scrivere:

```bash
python3 -m kdpfactory specs --trim 6x9 --pages 160 --paper cream
```

## Font

La pipeline cerca i file `.ttf` in quest'ordine: `fonts/` del progetto,
`$KDPFACTORY_FONTS_DIR`, font di sistema (Liberation, DejaVu, FreeFont).

Per usare un font tuo, copia in `fonts/` i quattro file con questi nomi:

```
EBGaramond-Regular.ttf  EBGaramond-Bold.ttf  EBGaramond-Italic.ttf  EBGaramond-BoldItalic.ttf
```

oppure aggiungi la tua quaterna in `FONT_CANDIDATES` dentro
`kdpfactory/typography.py`. Verifica che la licenza del font consenta
l'incorporamento in PDF destinati alla stampa commerciale: EB Garamond, Libre
Baskerville, Crimson Pro, Source Serif (tutti SIL OFL) vanno bene.

## Copertina

`kdpfactory/cover.py` genera una copertina tipografica: fondo, cornice, titolo,
filetto, sottotitolo, autore, dorso, quarta con testo e punti elenco, area del
codice a barre lasciata libera.

- Nuovo tema: aggiungi una `Theme` a `THEMES` (sei colori: fondo, pannello,
  titolo, accento, testo).
- Controllo delle misure: `build --guides` disegna rifilo, dorso e area del
  codice a barre. **Il file con le guide non va caricato su KDP.**
- Copertina disegnata altrove: genera comunque quella automatica per leggere le
  misure esatte (`state.json` → `cover`), poi usale nel tuo file. Lo spessore del
  dorso cambia a ogni variazione del numero di pagine.

## Prompt

`kdpfactory/prompts.py` contiene tutto il testo inviato al modello:

- `AUTHOR_RULES`: le regole di scrittura (paragrafi, esempi, divieti). È il punto
  in cui aggiungere le tue regole di stile permanenti.
- `BANNED_OPENERS`: formule vietate. Il controllo qualità le segnala anche a
  posteriori: aggiungine ogni volta che ne riconosci una nei tuoi testi.
- `book_bible()`: la scheda del libro inviata a ogni chiamata (in cache).
- `outline_prompt()`, `chapter_prompt()`, `revise_prompt()`, `metadata_prompt()`.

Per istruzioni valide su un solo libro non serve toccare il codice: usa il campo
`notes` di `book.json`, che finisce nella scheda del libro.

## Lingua

`language: "it"` o `"en"`. Cambiano la lingua di scrittura, le etichette
dell'impaginato (`kdpfactory/i18n.py`), la sillabazione e i testi fissi di
colophon e richiesta di recensione. Per aggiungere una lingua: una nuova voce in
`LABELS`, una in `SAMPLE_TEXT` (`planner.py`) e una in `STOPWORDS` (`qa.py`).

## Modello e costi

```bash
python3 -m kdpfactory --model claude-sonnet-5 --effort medium all <slug>
```

Il prompt di sistema stabile è in cache: la scrittura di venti capitoli riusa lo
stesso prefisso. Non modificare `book.json` a metà scrittura se vuoi mantenere i
benefici della cache — ogni variazione della scheda invalida il prefisso.

## Controlli

`kdpfactory/qa.py` raccoglie i controlli. Ogni voce è un `report.add(livello,
codice, messaggio)` con livello `errore` (blocca) o `avviso`. Aggiungerne uno è
una decina di righe: per esempio un divieto di parole che non vuoi mai vedere nei
tuoi libri.

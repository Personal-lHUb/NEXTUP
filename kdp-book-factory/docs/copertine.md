# Copertine: il sistema che decide il clic

Su Amazon la copertina non viene mai vista come la vedi tu mentre la controlli.
Viene vista **larga 160 pixel**, in mezzo ad altre venti, per meno di un
secondo, su fondo bianco. Tutto quello che non sopravvive a quella miniatura,
per il cliente non esiste.

Da qui un sistema di regole misurabili, non di gusti. Sta in
`kdpfactory/coverdesign.py`, lo applica `kdpfactory/cover.py` e lo verifica
l'agente `copertina` — che, come l'agente di impaginazione, non usa il modello:
misura il PDF finito.

## Le sette regole

| # | Regola | Come si misura |
|---|---|---|
| 1 | **Un solo elemento dominante** | massimo 4 blocchi di testo nella metà alta della prima |
| 2 | **Titolo leggibile in miniatura** | altezza delle maiuscole ≥ 6% dell'altezza (8,5% per un titolo davvero dominante), su massimo 3 righe |
| 3 | **Contrasto reale** | rapporto di contrasto titolo/fondo ≥ 7:1 (soglia AAA delle linee guida di accessibilità) |
| 4 | **Stacco dalla pagina** | il fondo deve avere ≥ 3:1 contro il bianco, o la copertina perde il bordo e sparisce fra le altre |
| 5 | **Codice di genere in mezzo secondo** | un segno grafico che dice *che libro è* prima che il titolo venga letto |
| 6 | **Un ciclo aperto** | una domanda o una promessa incompleta: è l'effetto Zeigarnik, l'incompiuto resta in testa |
| 7 | **Numeri in cifre** | «13 CASES · 908 SUSPECTS» si legge in un colpo d'occhio, «tredici casi» va letto |

Le prime quattro si misurano sul PDF, le ultime tre sui testi di copertina.
Le soglie sono costanti in cima a `coverdesign.py`: `MIN_TITLE_CAP_RATIO`,
`GOOD_TITLE_CAP_RATIO`, `MIN_CONTRAST`, `MAX_TOP_ELEMENTS`, `MAX_TITLE_LINES`,
`THUMBNAIL_WIDTH_PX`.

## Quello che il sistema non farà

Niente finti timbri di bestseller, stelline, recensioni o premi inventati.
Oltre a essere vietati dalle regole di contenuto KDP, sono promesse che il libro
non mantiene: il clic arriva, e dietro il clic arriva il reso e la recensione a
una stella. L'agente `copertina` blocca la pubblicazione se trova in copertina
una rivendicazione di questo tipo (`BANNED_CLAIMS` in
`kdpfactory/agents/copertina.py`).

La garanzia in copertina, quando c'è, deve essere vera e verificabile. Per il
libro di enigmi è «Every case has exactly one solution»: è vera perché il
risolutore lo dimostra prima della stampa.

## I testi della prima

Cinque campi, in ordine di importanza percettiva (`CoverCopy`):

| campo | che cos'è | esempio |
|---|---|---|
| `kicker` | l'occhiello: dice il genere in due parole | `DEDUCTION PUZZLES` |
| `title` | l'elemento dominante | `Twelve Carriages, One Killer` |
| `hook` | il ciclo aperto | `Can you name the killer in every carriage?` |
| `stats` | i numeri, in cifre | `13 CASES · 908 SUSPECTS · 1 MASTERMIND` |
| `badge` | una garanzia vera, breve | `Every case has exactly one solution` |

Il **sottotitolo completo non finisce in copertina**: in miniatura non si legge
e ruba spazio al titolo. Se non specifichi il gancio, `derive_copy` usa la prima
proposizione del sottotitolo; il resto resta nella scheda prodotto.

Per scriverli a mano basta metterli in `metadata.json`:

```json
{
  "cover_kicker": "METODO PRATICO",
  "cover_hook": "Quante ore hai perso questa settimana?",
  "cover_stats": "3 ORE · 21 GIORNI · 1 ABITUDINE",
  "cover_badge": "Un esercizio verificabile per capitolo"
}
```

La linea enigmistica li costruisce da sé, dai numeri veri del libro
(`cover_copy()` in `kdpfactory/puzzle/book.py`).

## L'adattamento per tipo di libro

Il sistema è lo stesso per tutti i libri; cambia il **codice di genere**, perché
chi cerca enigmi e chi cerca un metodo cercano due segnali diversi. Ci si
differenzia dentro il codice del genere, non fuori: una copertina di enigmi che
sembra un romanzo non viene cliccata da nessuno dei due pubblici.

| genere | occhiello | motivo grafico | che cosa dice |
|---|---|---|---|
| `enigmi` | `DEDUCTION PUZZLES` | elenco di sospetti barrati, uno cerchiato in accento | «qui si ragiona» — ed è anche il ciclo aperto: chi è quello cerchiato? |
| `non-fiction` | nessuno | tre barre che crescono verso il basso, l'ultima in accento | «c'è un metodo, e porta da qualche parte» |
| `fiction` | nessuno | nessuno: aria attorno al titolo | «è un romanzo»: l'atmosfera la fa la palette |

La tabella è `GENRE_DEFAULTS`; un motivo nuovo è una funzione
`motif_<nome>(canvas, box, palette, top, height)` aggiunta a `MOTIFS`.

Quando la copertina ha un'immagine dell'autore (`assets/copertina.jpg`), il
motivo grafico non viene disegnato: l'immagine **è** già l'elemento dominante, e
sovrapporle un secondo segno rompe la regola 1.

## Le palette

Sei palette, tutte scelte per staccare su fondo bianco e tutte oltre 7:1 di
contrasto sul titolo — la verifica lo controlla a ogni build e i test lo
controllano su tutte e sei.

| nome | fondo | accento | generi |
|---|---|---|---|
| `notturno` | nero-blu | giallo | enigmi, fiction, non-fiction |
| `allarme` | nero | rosso | enigmi, fiction |
| `inchiostro` | blu notte | verde acqua | non-fiction, enigmi |
| `bosco` | verde scuro | verde acido | non-fiction |
| `terracotta` | bruno | arancio | fiction, non-fiction |
| `indaco` | viola scuro | lilla | fiction, enigmi |

`cover_theme` in `book.json` sceglie la palette; con `auto` la sceglie il
sistema fra quelle del genere, in modo stabile (dipende dal titolo: lo stesso
libro avrà sempre la stessa copertina).

## La verifica

Ogni `build` produce due cose oltre al PDF:

- `build/<slug>-copertina-miniatura.png` — la prima di copertina **larga 160
  pixel**, l'unico modo onesto di giudicarla. Guarda quello, non il PDF a
  schermo intero;
- `state.json` → `cover.verifica` — le misure:

```json
{
  "titolo_px_in_miniatura": 16.7,
  "titolo_percentuale_altezza": 7.0,
  "titolo_righe": 3,
  "contrasto": 17.3,
  "stacca_su_bianco": true,
  "elementi_in_alto": 3,
  "dentro_area_sicura": true,
  "problemi": []
}
```

Gli stessi controlli passano dall'agente, con la gravità e il rimedio:

```bash
python3 -m kdpfactory review <slug> --agents copertina
```

Un titolo illeggibile in miniatura, un contrasto sotto 7:1, un testo fuori
dall'area di sicurezza o una rivendicazione vietata sono **bloccanti**: la
copertina va rifatta prima di caricarla.

## Se la copertina la disegni altrove

Genera comunque quella automatica: `state.json` → `cover` contiene le misure
esatte (larghezza, altezza, spessore del dorso per il numero di pagine reale).
Poi applica le stesse sette regole al tuo file — la verifica gira su qualunque
PDF di copertina delle dimensioni giuste.

`build --guides` disegna rifilo, dorso e area del codice a barre. **Il file con
le guide non va caricato su KDP.**

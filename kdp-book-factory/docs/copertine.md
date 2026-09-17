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
| 5 | **Un'immagine che dice di che libro si tratta** | un'illustrazione riconoscibile in mezzo secondo, con **un solo punto in accento** |
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

## L'illustrazione

L'immagine di copertina è **disegnata dalla pipeline**, non cercata. Sta in
`kdpfactory/coverart.py` e ha quattro vantaggi che una fotografia non ha:

- non costa niente, non serve una chiave API né una banca di immagini;
- è vettoriale, quindi nitida a qualunque risoluzione: KDP non la contesta mai
  per i DPI, cosa che invece succede regolarmente con le foto;
- nasce nei colori della palette del libro: l'immagine non litiga mai col titolo;
- non ha un autore da pagare né problemi di diritti — che per una copertina
  venduta su Amazon non è un dettaglio.

A 160 pixel una fotografia ricca di dettagli diventa una macchia; una
**silhouette con un solo punto luminoso** si riconosce ancora. Per questo tutte
le illustrazioni seguono la stessa regola: un solo elemento in accento, ed è
quello che racconta la storia.

| illustrazione | che cos'è | il punto in accento |
|---|---|---|
| `treno` | un espresso notturno visto di fianco | la finestra accesa: la carrozza dov'è successo |
| `lente` | una lente sopra una griglia di indizi | l'unico indizio che conta |
| `elenco` | un elenco di sospetti barrati | l'unico nome rimasto in piedi |
| `orologio` | un quadrante con uno spicchio pieno | le ore che il libro restituisce |
| `scala` | gradini che salgono | l'ultimo gradino, il punto d'arrivo |
| `porta` | una porta socchiusa | la luce che ne esce |

### Come viene scelta

1. `cover_art` in `book.json`, se l'autore l'ha indicata (`treno`, `lente`,
   `elenco`, `orologio`, `scala`, `porta`, oppure `nessuna` per una copertina di
   solo testo);
2. altrimenti dalle **parole chiave** di quello che il libro dice di essere:
   titolo, sottotitolo, argomento, promessa. A parità di parole trovate vince la
   scena più concreta — un treno si ricorda, un segno astratto no;
3. se non emerge niente, quella prevista per il genere: `enigmi` → `elenco`,
   `non-fiction` → `scala`, `fiction` → `porta`.

Quando la copertina ha già una fotografia dell'autore (`assets/copertina.jpg`),
l'illustrazione **non** viene disegnata: la foto è già l'elemento dominante, e
sovrapporle un secondo segno rompe la regola 1.

### Aggiungerne una

Una funzione `def nome(canvas, area, palette)` che disegna dentro `area`
(un `Area`, con `fit(proporzione, anchor=...)` per ricavare il rettangolo con le
proporzioni giuste), più una voce in `ARTS` con le parole chiave, le proporzioni
e quanto è concreta. Due regole: **un solo accento**, e tutto dentro `area` —
`coverart.draw` isola lo stato grafico, ma non ritaglia niente.

## L'adattamento per tipo di libro

Il sistema è lo stesso per tutti i libri; cambia l'occhiello e cambia
l'illustrazione, perché chi cerca enigmi e chi cerca un metodo cercano due
segnali diversi. Ci si differenzia dentro il codice del genere, non fuori: una
copertina di enigmi che sembra un romanzo non viene cliccata da nessuno dei due
pubblici.

| genere | occhiello | illustrazione di riserva |
|---|---|---|
| `enigmi` | `DEDUCTION PUZZLES` | `elenco` |
| `non-fiction` | nessuno | `scala` |
| `fiction` | nessuno | `porta` |

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

`state.json` → `cover.illustrazione` dice quale illustrazione è stata scelta.

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

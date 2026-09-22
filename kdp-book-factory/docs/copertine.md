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
| `kicker` | l'occhiello: dice che prodotto è, in due parole | `ENIGMI DI DEDUZIONE` |
| `title` | l'elemento dominante | il titolo del libro |
| `hook` | il ciclo aperto | `Riesci a dire chi è stato in ogni carrozza?` |
| `stats` | i numeri, in cifre | `13 CASI · 908 SOSPETTI` |
| `badge` | una garanzia vera, breve | `Ogni caso ha una sola soluzione` |

I testi di copertina vanno **nella lingua del libro** (`language` in
`book.json`): un occhiello inglese su una copertina italiana dice al cliente
che il libro non è per lui, e il clic lo perdi lì. Le etichette di serie stanno
in `kdpfactory/i18n.py`.

Insieme ai testi viaggiano due campi che non si stampano: `content_type` — la
categoria di prodotto, che decide quale formula si applica — e `facts`, cioè
**le cifre che il libro ha davvero**. Chi costruisce la copertina le dichiara
(la pipeline conta pagine, capitoli e schede pratiche; la linea enigmistica
conta casi, sospetti e indizi), e il controllo rifiuta qualunque numero
stampato che non sia in quell'elenco. Un numero in copertina è una promessa al
cliente: o è contato, o non si stampa.

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

## Le due categorie di prodotto

Le sette regole valgono per ogni libro. Quello che **cambia con la categoria**
(`content_type` in `book.json`, definita in `CLAUDE.md`) è che cosa si mette in
copertina — perché medium e full non vendono la stessa cosa.

| | medium-content | full-content |
|---|---|---|
| formula | segnale di categoria + beneficio + quantificatore + garanzia | promessa + mondo + metafora visiva |
| cosa viene prima | la **funzione**: che prodotto è, per chi, quanto contiene | l'**emozione**: che promessa mantiene, in che mondo si entra |
| il numero | è parte del disegno: la banda d'accento in fondo alla prima esiste per quello | non c'è |
| la garanzia | sì, se è vera e verificabile | no: racconta il prodotto sbagliato |

Il sistema la fa rispettare dove si misura, e l'agente `copertina` blocca:

- un **medium-content senza quantificatore** — la copertina non dice quanto
  contiene il libro, che è la prima cosa che questo cliente cerca;
- un **full-content con le specifiche da scaffale** — numeri e garanzie su
  un'opera a testo pieno;
- una **cifra che non corrisponde a nessun dato misurato** del libro.

Resta un avviso, non un blocco, il medium-content senza occhiello: manca il
segnale di categoria, ma il libro è pubblicabile.

Su un medium-content il quantificatore, se la scheda non lo propone, **lo
calcola la pipeline**: schede pratiche contate nel manoscritto (le sezioni
`## In pratica`), capitoli, pagine del PDF finito, e i caratteri grandi come
garanzia quando il corpo supera i 13 punti. È la stessa regola della linea
enigmistica, che i suoi numeri li prende dal libro generato.

## Quando il motore non basta: il brief

Il motore disegna copertine che funzionano in miniatura e non costa niente, ma
c'è una cosa che per costruzione non sa fare: l'**atmosfera**. Una silhouette
vettoriale su fondo piatto dice *che libro è*; non dice *che mondo è*. Su un
full-content, dove si compra un'esperienza e non una specifica, quella
differenza si paga in clic.

Per quei casi il sistema non disegna: scrive il brief.

```bash
python3 -m kdpfactory copertina <slug>
```

Produce `build/copertina-brief.md` — in inglese, perché è la lingua in cui gli
strumenti grafici sbagliano meno — coi dati che il libro ha già: categoria e
formula, promessa, pubblico, nicchia, testi da stampare (nella lingua del
libro) con i numeri contati, palette, soglie del sistema, misure di stampa a
300 DPI, divieti di imitazione e la lista di controllo finale. Nessuna chiamata
API.

L'immagine che torna rientra dalla porta che esiste già: si salva in
`assets/copertina.jpg` e al `build` successivo `coverimage.py` la misura, la
ritaglia sulle proporzioni esatte della prima, la porta a 300 DPI e dice se i
pixel bastano.

## L'adattamento per tipo di libro

Il sistema è lo stesso per tutti i libri; cambia l'occhiello e cambia
l'illustrazione, perché chi cerca enigmi e chi cerca un metodo cercano due
segnali diversi. Ci si differenzia dentro il codice del genere, non fuori: una
copertina di enigmi che sembra un romanzo non viene cliccata da nessuno dei due
pubblici.

| genere | occhiello | illustrazione di riserva |
|---|---|---|
| `enigmi` | `ENIGMI DI DEDUZIONE` / `DEDUCTION PUZZLES` | `elenco` |
| `non-fiction` | nessuno | `scala` |
| `fiction` | nessuno | `porta` |

Solo l'enigmistica ha un occhiello di serie: «NON-FICTION» stampato in
copertina non è un segnale di categoria, è rumore. Su un medium-content che non
sia di enigmi l'occhiello lo propone l'agente dei metadati, e se manca il
controllo lo segnala.

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

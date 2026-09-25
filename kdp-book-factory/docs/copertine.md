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

### Il titolo in condensato

Sulle parole lunghe il sans normale non arriva alla soglia dominante:
«REMEMBERED», a tutta larghezza su una prima 6x9, esce a 55 punti, cioè il
5,8% dell'altezza. Per questo il progetto porta con sé un bastone condensato,
**Barlow Condensed Bold** (licenza SIL OFL, `fonts/ofl/`, versionato perché il
contenitore della fabbrica è effimero). Lo stesso titolo lì arriva al 9%.

La scelta la fa `title_font_and_size`, non il gusto: il titolo va in condensato
se la parola più larga esce dalla gabbia in sans, oppure se il condensato
guadagna almeno il 10% di corpo (`CONDENSED_MIN_GAIN`). Altrimenti resta nel sans,
che a parità di corpo si legge meglio. Il controllo a monte (`title_problems`)
ragiona con gli stessi caratteri, e blocca un titolo solo se la sua parola più
larga non entra **in nessuno** dei due: bloccare «CONCENTRAZIONE» perché non
entra nel sans vorrebbe dire fermare un titolo che la copertina compone
benissimo.

Se `fonts/ofl/` manca, il titolo torna al sans e nessun controllo cambia
significato. Si possono aggiungere altri condensati in
`CONDENSED_DISPLAY_CANDIDATES` (`kdpfactory/typography.py`).

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
| `poltrona` | una poltrona reclinabile vuota | la lampada accesa accanto |

### Come viene scelta

1. `cover_art` in `book.json`, se l'autore l'ha indicata (`treno`, `lente`,
   `elenco`, `orologio`, `scala`, `porta`, `poltrona`, oppure `nessuna` per una
   copertina di solo testo);
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

**La regola che il brief non negozia**: l'immagine deve *rappresentare* il
libro. Una sagoma astratta, un gradiente o un ornamento geometrico decorano;
una figura riconoscibile spiega. Chi scorre i risultati non legge — cerca la
copertina che somiglia alla cosa che è venuto a comprare, e l'ornamento
astratto è l'unica scelta che va bene per tutti i libri e non rappresenta
nessuno.

Perciò il brief porta la rappresentazione **della categoria**, ricavata dalle
categorie KDP del libro: a un ricettario dice di mostrare il piatto finito, a
un libro per bambini i personaggi in azione, a un'agenda i layout, a un libro
di enigmi la griglia. Con lo stile contemporaneo che regge meglio in quella
nicchia, e l'elenco di quello che va evitato — immagini di repertorio scollegate,
forme astratte, icone decorative, l'aria liscia e simmetrica di un'immagine
generata senza direzione.

Il brief porta anche le specifiche che fanno rimbalzare il caricamento: misure
del wrap calcolate sulle pagine vere, dorso, area del codice a barre, requisiti
del PDF, e le varianti per copertina rigida ed ebook (che non si ricavano da
quelle del brossurato).

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

## Le specifiche KDP, misurate sul file

Le regole qui sopra dicono se la copertina vende. Queste dicono se viene
pubblicata, e sono tutte bloccanti perché fermano il caricamento — che costa
una settimana ogni volta. Nessuna è opinabile: o le misure tornano o no.

| controllo | che cosa misura |
|---|---|
| dimensioni | larghezza e altezza del PDF contro il calcolo KDP: abbondanza + retro + dorso + prima + abbondanza. Il dorso dipende da pagine, carta e formato, quindi una copertina fatta su un conteggio vecchio è sbagliata e non si vede a schermo |
| una pagina sola | retro, dorso e prima in un'unica immagine continua |
| codice a barre | i 2"x1,2" in basso a destra della quarta devono essere liberi da inchiostro: KDP ci stampa sopra il codice |
| testo di dorso | ammesso solo da 79 pagine in su, e dentro le pieghe con 1,6 mm liberi per lato |
| font | incorporati, come per l'interno |
| linee guida | se nel file ci sono le pieghe del dorso è il PDF prodotto con `--guides`, che non va caricato |
| nome dell'autore | uguale a quello della scheda: Amazon confronta i due e blocca la pubblicazione |

Girano sul PDF, non sul codice che lo ha prodotto: valgono anche per una
copertina disegnata altrove, purché abbia le dimensioni giuste.

Un dettaglio che vale la pena conoscere: l'area del codice a barre si campiona
**un punto dentro il bordo**, non sul contorno esatto del rettangolo. Sul
contorno l'antialiasing mescola i due colori, e il controllo segnalerebbe ogni
copertina che il sistema disegna.

## Se la copertina la disegni altrove

Genera comunque quella automatica: `state.json` → `cover` contiene le misure
esatte (larghezza, altezza, spessore del dorso per il numero di pagine reale).
Poi applica le stesse sette regole al tuo file — la verifica gira su qualunque
PDF di copertina delle dimensioni giuste.

`build --guides` disegna rifilo, dorso e area del codice a barre. **Il file con
le guide non va caricato su KDP.**

## Le figure dentro il libro

La copertina è una sola e deve vendere. Le figure dell'interno sono molte e
devono spiegare, in bianco e nero, accanto a un testo che le ha già annunciate.
Mestiere diverso, modulo diverso: `kdpfactory/figure.py` e
`kdpfactory/imagebrief.py`.

### Si dichiarano prima di esistere

Nel manoscritto:

```markdown
![che cosa deve mostrare l'immagine](immagini/03-nome.jpg)
(didascalia facoltativa, fra parentesi, sulla riga dopo)
```

Il testo fra `![` e `]` non è una didascalia: è il **committente** dell'immagine,
ed è quello che `immagini` trasforma in prompt. La didascalia, quella che legge
il cliente, sta nella riga dopo fra parentesi — tenerle separate serve perché
fanno due mestieri.

Finché il file non c'è, l'impaginazione disegna un **segnaposto della misura
esatta**, con dentro scritto che cosa manca. Il motivo non è la cortesia: è che
così il conteggio pagine è già quello definitivo, e il libro non cambia
lunghezza il giorno in cui le immagini arrivano. Una prova di stampa con dei
rettangoli tratteggiati dice che cosa manca; una senza immagini non dice niente
e il libro si allunga dopo.

### I prompt

```bash
python3 -m kdpfactory immagini <slug>
```

Un prompt per figura in `build/immagini-brief.md`, in prosa descrittiva — la
forma che i modelli conversazionali eseguono meglio e l'unica che regge le
istruzioni negative complesse — più un blocco di parametri in coda per gli
strumenti che li vogliono, così il brief resta valido cambiando strumento.

Tre vincoli che la copertina non ha:

| vincolo | perché |
|---|---|
| **solo scala di grigi** | l'interno si stampa in bianco e nero: due elementi distinti solo dal colore, sulla pagina, sono la stessa cosa |
| **nessun testo nell'immagine** | le etichette le compone la tipografia, col font del libro e correggibili; un'etichetta generata è pixel, e col refuso si rifà l'immagine |
| **stile comune a tutte** | venti figure da venti prompt scollegati sembrano prese da venti libri: il brief porta una riga di stile identica per tutto il libro |

Lo stile di base segue la categoria di prodotto: line art da manuale per il
medium-content (deve reggere la fotocopia), illustrazione editoriale in grigio
per il full-content.

### Che cosa viene verificato

| controllo | gravità |
|---|---|
| l'immagine dichiarata non c'è | **errore**: il libro si impagina, ma non si carica |
| sotto i 300 DPI **alla misura stampata** | **errore**: 900 px sono magnifici a 3 pollici e inaccettabili a 5 |
| immagine a colori | avviso: viene convertita, ma due colori possono diventare lo stesso grigio |

La conversione in scala di grigi la fa `build`, scrivendo un file nuovo in
`build/immagini/`: l'originale è quello che è tornato dallo strumento grafico e
si rigenera solo rifacendo il prompt.

Una figura non supera mai il 58% dell'altezza della gabbia. Oltre, non è una
figura ma una tavola: si porta dietro il testo che le stava intorno e lascia un
buco dove stava.

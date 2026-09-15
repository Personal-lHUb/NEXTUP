# La linea enigmistica

Seconda linea di produzione della factory: libri di **enigmi di deduzione**.
Non è una variante dei libri in prosa — è un prodotto diverso, con un pregio
che la prosa non può avere.

**Qui non serve un modello linguistico.** I casi si generano da un seme e si
*dimostrano* corretti: soluzione unica, nessun indizio superfluo. Niente
allucinazioni da verificare, nessun costo per copia, e lo stesso seme rifà lo
stesso libro. Quello che il modello non tocca, non può sbagliarlo.

```bash
python3 -m kdpfactory puzzle new mio-libro --seed 20260915 --author "Nome Cognome"
python3 -m kdpfactory puzzle build mio-libro
```

---

## Che cosa produce

Un libro di tredici casi. I primi dodici sono indipendenti e si risolvono in
qualsiasi ordine; il tredicesimo si apre solo con le dodici risposte in mano.

Ogni caso ha:

- un **cast** completo — tutti i passeggeri di una vettura, con cappello,
  cappotto, bagaglio e (nei casi più difficili) guanti, bevanda o posto a
  sedere. Il cast è il prodotto cartesiano degli attributi: nessun doppione,
  nessun buco;
- una **serie di indizi**, tutti veri, tutti necessari;
- una **pagina di appunti** rigata, accanto al caso e non in fondo al libro;
- una **soluzione ragionata** in coda al volume: non solo il nome, ma quanti
  sospetti restavano in gioco prima e dopo ogni indizio.

In apertura c'è un **caso di esempio risolto per intero**: vale più di qualsiasi
spiegazione del metodo.

---

## Perché è verificabile

`solver.py` controlla ogni caso prima che venga impaginato:

| Proprietà | Che cosa garantisce al lettore |
|---|---|
| **unicità** | applicando tutti gli indizi resta esattamente un sospetto |
| **necessità** | togliendo un indizio qualsiasi la soluzione non è più unica: nel libro non finiscono indizi decorativi |
| **coerenza** | nessun nome doppio, nessuna combinazione di attributi ripetuta |
| **tracciabilità** | si sa quanti sospetti elimina ogni indizio, ed è da lì che nasce la soluzione ragionata |

Se un caso non passa la verifica viene buttato e rigenerato. In stampa arriva
solo ciò che è stato dimostrato — ed è anche l'argomento di vendita più forte
della scheda prodotto: *«no red herrings, no contradictions, no puzzle that
turns out to have two answers»*.

---

## I tipi di indizio

| Tipo | Esempio | Peso |
|---|---|---|
| `is` | The culprit wore a fedora. | immediato |
| `is_not` | The culprit did not drink tea. | immediato |
| `one_of` | The culprit's coat was either navy or olive. | medio |
| `cleared` | Three passengers were together in the dining car and are cleared: … | medio |
| `same_as` / `differs_from` | The culprit's hat was the same as Mrs Wren's. | medio |
| `if_then` | If the culprit carried a violin case, then they wore a beret. | duro |
| `not_both` | No one who wore a bowler and drank tea could be the culprit. | duro |
| `exactly_one` | Exactly one of these statements is true: (a) … (b) … (c) … | durissimo |

La difficoltà non cresce allungando la lista dei sospetti: cresce cambiando il
**tipo** di ragionamento. I primi casi si risolvono per esclusione diretta,
gli ultimi solo tenendo aperte due ipotesi per volta.

Il generatore non sceglie gli indizi che eliminano di più — sceglie quelli che
ne eliminano **circa il 38%**. Puntare al massimo produrrebbe enigmi da tre
indizi, che non si risolvono: si leggono. E penalizza i tipi già usati nello
stesso caso, perché sette «exactly one of these» di fila si leggono come un
modulo fiscale.

---

## Il finale

I dodici colpevoli diventano i dodici sospetti del tredicesimo caso: uno dei
dodici non lavorava da solo. Gli indizi confrontano il capo con i colpevoli dei
casi già risolti — *«the mastermind's hat differed from that of the culprit of
Case 3»* — spesso due confronti per indizio.

Nel libro la griglia del finale è **vuota**: dodici righe, una per caso, da
riempire con le proprie risposte. Stamparla compilata regalerebbe dodici
soluzioni.

Il generatore pretende prima che il finale citi tutti e dodici i casi, poi
almeno otto, e solo alla fine si accontenta. Quello che non si negozia mai è la
correttezza: soluzione unica e nessun indizio superfluo, in tutti i casi.

---

## Personalizzazione

Tutto il testo e la forma stanno in `kdpfactory/puzzle/theme.py`:

- `ATTRIBUTES` — le caratteristiche dei passeggeri e come si dicono in inglese
  (`template`, `negative_template`, singolare/plurale, articolo `a`/`an`);
- `SURNAMES`, `HONORIFICS` — i nomi. Dentro un caso i cognomi sono unici, così
  gli indizi possono citarli senza ambiguità;
- `CASES` — dodici voci: vettura, titolo, testo di scena, attributi in gioco con
  quante varianti ciascuno (il prodotto è la dimensione del cast) e tipi di
  indizio ammessi;
- `HOW_TO_PLAY`, `FINALE_SETTING` — i testi fissi.

Per un libro diverso — un albergo, una nave, un collegio — si riscrive questo
file e si lascia intatto tutto il resto. Per un libro in italiano si traducono
i template: il motore non sa niente della lingua.

Attenzione a una cosa: gli attributi presenti in **tutti** i casi sono quelli su
cui si gioca il finale. Se un attributo sparisce da un solo caso, sparisce dal
finale.

---

## Che cosa non c'è

- **Nessun EPUB.** Un libro da riempire a matita non ha senso su Kindle: la
  griglia non si compila, il cast non si sbarra. Se in futuro serve un'edizione
  digitale, va ripensata, non convertita.
- **Nessuna chiamata API**, quindi nessun costo per libro e nessun
  `--dry-run`: la modalità di prova è il libro stesso.
- **Nessun agente di contenuto.** Lettore cieco, fact-checker e conformità
  lavorano sulla prosa; qui l'unico controllo che conta è il solver, più
  l'agente di impaginazione che misura il PDF.

---

## Costi e prezzo

Un libro da ~80 pagine 6x9 in bianco e nero sta sotto la soglia delle 108
pagine, dove il costo di stampa è fisso. Con un prezzo di 8,99 la royalty è
intorno ai 3 euro/dollari a copia — ma i costi in
`config/printing_costs.json` sono ancora marcati `DA VERIFICARE`: controllali
sul calcolatore KDP prima di fissare il prezzo.

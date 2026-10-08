# Capitolo 14 — Come Amazon vede le nostre ADS

🎯 **Obiettivo del capitolo:** ribaltare la prospettiva. Finora hai guardato le campagne
dal tuo lato; ora guardale dal lato di Amazon. Capire **quali sono gli incentivi della
piattaforma** è ciò che permette di prevedere il comportamento del sistema invece di
subirlo.

⚠️ Premessa di onestà: Amazon **non pubblica** l'algoritmo dell'asta né un punteggio di
qualità come quello di Google Ads. Questo capitolo espone il modello che spiega in modo
coerente il comportamento osservabile del sistema e ciò che Amazon dichiara nella
propria documentazione. Trattalo come una mappa operativa affidabile, non come una
specifica ufficiale.

---

## 14.1 L'incentivo di Amazon

Amazon non vuole vendere clic. Amazon vuole **massimizzare il ricavo per impressione**
(e, sul lungo periodo, la soddisfazione del cliente, che protegge il ricavo futuro).

📐 **Il criterio di selezione, in forma semplificata**

```
Valore atteso di un annuncio ≈ Offerta × Probabilità di clic stimata
```

Fra due inserzionisti:

```
A: offerta 1,00 €  ·  CTR previsto 0,20%  →  valore ≈ 0,0020
B: offerta 0,60 €  ·  CTR previsto 0,50%  →  valore ≈ 0,0030   ← vince B
```

**B vince pur offrendo il 40% in meno.** Questo è il meccanismo che rende il CTR una
leva economica e non solo una metrica descrittiva (Capitolo 6).

C'è un secondo livello: Amazon guadagna **due volte** dalla stessa impressione — con il
costo del clic e con la commissione sulla vendita. Un annuncio che converte bene vale
quindi più della sola somma pubblicitaria, e il sistema tende a favorire prodotti con
buon storico di conversione. È la ragione per cui prodotti con CVR elevato ottengono
spesso costi effettivi più bassi a parità di offerta.

---

## 14.2 L'asta di secondo prezzo

Il vincitore non paga la propria offerta, ma poco più di quanto serviva per battere il
concorrente successivo.

```
Offerte:  A 1,20 €  ·  B 0,90 €  ·  C 0,70 €
A vince e paga circa 0,91 € — non 1,20 €.
```

**Tre conseguenze pratiche:**

1. **Il tuo CPC medio è quasi sempre inferiore all'offerta.** Se non lo è, sei in
   competizione serrata: stai vincendo a fatica e perdendo molte aste.
2. **Alzare l'offerta non alza proporzionalmente il costo.** Passare da 0,80 € a 1,00 €
   può non cambiare quasi nulla nel CPC pagato, ma far vincere molte più aste. È il
   motivo per cui gli aumenti di offerta hanno spesso un rendimento migliore di quanto
   ci si aspetti.
3. **L'offerta va pensata come il valore massimo che quel clic vale per te**, calcolato
   (Capitolo 9), non come "quanto voglio spendere".

Nella realtà intervengono anche riserve di prezzo, aggiustamenti dinamici e filtri di
idoneità: il modello resta valido come guida, non come previsione al centesimo.

---

## 14.3 I filtri di idoneità: prima dell'asta

Prima ancora di essere valutato in asta, il tuo annuncio deve superare una serie di
controlli. Se ne fallisce uno, **non c'è offerta che tenga**: semplicemente non eroghi.

| Filtro | Requisito | Sintomo se fallisce |
|---|---|---|
| **Buy Box** | Devi detenerla (per SP) | Impressioni a zero da un giorno all'altro |
| **Disponibilità** | Prodotto in stock e acquistabile | Erogazione che si interrompe |
| **Rilevanza / indicizzazione** | Amazon deve considerarti pertinente per quel termine | Nessuna impressione su una keyword specifica |
| **Stato del prodotto** | Attivo, non soppresso, immagine conforme | Campagna attiva ma senza impressioni |
| **Categoria consentita** | Alcune categorie hanno restrizioni pubblicitarie | Rifiuto in fase di creazione |
| **Policy creativa** (SB/SD) | Creatività approvata | Stato "in revisione" o "rifiutato" |
| **Budget e stato campagna** | Budget residuo, campagna attiva, date valide | Erogazione a singhiozzo o ferma |

🛠 **Diagnostica "impressioni a zero"** — segui questo ordine, dal più frequente al meno:

1. Buy Box → 2. Stock → 3. Data di fine della campagna o del portfolio → 4. Budget
esaurito (anche del portfolio) → 5. Stato di moderazione della creatività → 6. Offerta
troppo bassa → 7. Indicizzazione → 8. Volume di ricerca inesistente.

Nove volte su dieci la risposta è nelle prime quattro voci.

---

## 14.4 Il periodo di apprendimento

Quando lanci una campagna nuova su un prodotto senza storico, Amazon non ha dati per
stimare la tua probabilità di clic e di conversione. Il sistema parte quindi da stime di
categoria e le corregge man mano che raccoglie eventi.

Conseguenze:

- Le prime 1–2 settimane sono **rumorose**: CPC instabile, impressioni irregolari, ACOS
  poco significativo.
- **Ogni modifica sostanziale riavvia parte dell'apprendimento.** Cambiare offerte ogni
  giorno significa restare permanentemente in fase di apprendimento e non arrivare mai
  a un regime stabile.
- Un prodotto **nuovo** parte svantaggiato rispetto a uno consolidato con lo stesso
  prezzo: non ha storico di conversione da esibire. È un costo di ingresso reale, da
  mettere a budget.

**Regola operativa:** dopo il lancio, **non toccare nulla per 7–14 giorni**. Poi
intervieni su una variabile per volta.

---

## 14.5 Il flywheel: perché la pubblicità compra posizionamento

Questo è il meccanismo che rende razionale spendere sopra il break-even durante un
lancio.

```
        ┌──────────────────────────────────────────┐
        │                                          │
        ▼                                          │
  Spesa pubblicitaria                              │
        │                                          │
        ▼                                          │
  Impressioni e clic                               │
        │                                          │
        ▼                                          │
  Vendite (velocità di vendita per keyword)        │
        │                                          │
        ▼                                          │
  Miglior posizionamento ORGANICO su quella keyword│
        │                                          │
        ▼                                          │
  Vendite organiche (gratuite)                     │
        │                                          │
        ▼                                          │
  Più storico, più recensioni, miglior CVR ────────┘
        │
        ▼
  TACOS che scende nel tempo
```

Il ranking organico di Amazon premia la velocità di vendita per termine di ricerca, e le
vendite generate dagli annunci sono vendite a tutti gli effetti. Quindi:

- Un budget **concentrato su poche keyword** produce un effetto di posizionamento
  visibile; lo stesso budget distribuito su cinquanta keyword si disperde e non muove
  nulla.
- L'obiettivo di un lancio non è l'ACOS: è **arrivare in prima pagina organica** sulle
  2–3 keyword che contano.
- Il segnale che il flywheel sta girando è il **TACOS in calo a fatturato crescente**
  (Cap. 3, §3.5).

⚠️ Il meccanismo funziona anche al contrario: se smetti di fare pubblicità su una
keyword su cui eri arrivato in alto grazie al pagato, la velocità di vendita cala e il
posizionamento organico può arretrare. Il disinvestimento va fatto in modo graduale, non
di colpo.

---

## 14.6 Cosa Amazon "sa" di te

Il sistema costruisce, prodotto per prodotto, un profilo che comprende:

- **Storico di CTR** per keyword e per posizionamento.
- **Storico di CVR** e di velocità di vendita.
- **Qualità della scheda**: completezza, immagini, A+ Content, attributi compilati.
- **Rating e recensioni**, e la loro tendenza recente.
- **Prezzo relativo** rispetto ai concorrenti dello stesso spazio.
- **Disponibilità e affidabilità logistica**, tempi di consegna, idoneità Prime.
- **Tasso di reso e di reclamo**, indicatori di soddisfazione.
- **Storico dell'account** venditore.

Il punto pratico: **quasi tutte le leve dell'asta sono leve di prodotto e di scheda, non
di campagna.** Il lavoro sulle campagne serve a non sprecare il vantaggio che il prodotto
ha (o a non aggravare lo svantaggio che ha). Non lo crea.

---

## 14.7 Organico e sponsorizzato sulla stessa pagina

Il tuo prodotto può occupare **contemporaneamente** una posizione organica e uno spazio
sponsorizzato per la stessa ricerca. Due letture opposte:

- **A favore:** occupi più spazio visivo, riduci le occasioni di clic sui concorrenti,
  aumenti la probabilità complessiva di clic sul tuo prodotto.
- **Contro:** su termini dove sei già primo organico, una parte dei clic pagati
  sostituisce clic che avresti ottenuto gratis (problema di incrementalità, Cap. 3,
  §3.6).

**Come decidere:** non teoricamente, ma con un test. Isola la keyword in una campagna
dedicata, mettila in pausa per 14 giorni e osserva il **fatturato totale** dell'ASIN, non
quello pubblicitario. Se non cala, quella spesa era in gran parte non incrementale.
Ripeti periodicamente: appena riduci la presenza, i concorrenti possono occupare lo
spazio e il risultato del test cambia.

---

## 14.8 Cosa Amazon non ti mostra

Per completezza, i limiti informativi con cui devi convivere:

- **La formula dell'asta** e qualsiasi punteggio di qualità.
- **Il CTR previsto** che il sistema ti attribuisce.
- **I dati dei concorrenti**: chi ha vinto le aste che hai perso, e a quanto.
- **Termini di ricerca a bassissimo volume**, per ragioni di privacy e aggregazione.
- **Il percorso completo dell'utente** fra i tuoi diversi formati (solo AMC offre una
  visione parziale e aggregata).
- **L'attribuzione multi-touch**: la finestra standard tende a premiare l'ultimo clic.
- **L'incrementalità reale** delle tue campagne: va stimata con test, non letta in un
  report.

Convivere con questi limiti significa una cosa sola: **progettare test invece di cercare
report**. Le domande importanti (questa spesa è incrementale? questa immagine è migliore?
conviene presidiare questa keyword?) non hanno una colonna nella console. Hanno una
risposta solo se costruisci l'esperimento.

---

## 14.9 Le regole pratiche che discendono da tutto questo

1. **Migliora il CTR prima di alzare le offerte.** Costa meno e agisce sul lato
   dell'asta che non paghi.
2. **Migliora il CVR prima di ottimizzare le campagne.** È il denominatore dell'ACOS.
3. **Non toccare nulla per 7–14 giorni dopo una modifica.** Stai combattendo contro il
   tuo stesso apprendimento.
4. **Concentra il budget in fase di lancio.** Poche keyword, budget sufficiente,
   orizzonte definito.
5. **Non spegnere bruscamente ciò che ti ha portato in alto.** Riduci gradualmente.
6. **Controlla prima l'idoneità, poi l'offerta.** L'80% dei problemi di erogazione sta
   nei filtri, non nell'asta.
7. **Progetta esperimenti** per le domande a cui i report non rispondono.

---

⚠️ **Errori frequenti di comprensione del sistema**

- Credere che vinca sempre chi offre di più.
- Attribuire all'algoritmo problemi che sono di Buy Box, stock o date di fine.
- Cambiare offerte ogni giorno e non capire perché i dati non si stabilizzano.
- Distribuire il budget di lancio su troppe keyword.
- Spegnere tutto quando l'ACOS peggiora, perdendo posizionamento organico faticosamente
  costruito.
- Cercare nei report risposte che solo un test può dare.

---

✅ **Checklist di fine capitolo**

- [ ] So che l'asta pondera offerta e probabilità di clic, e cosa comporta.
- [ ] So che pago il secondo prezzo e confronto sempre CPC medio e offerta.
- [ ] Conosco i filtri di idoneità e la sequenza diagnostica per "impressioni a zero".
- [ ] Rispetto il periodo di apprendimento e non intervengo per 7–14 giorni.
- [ ] Capisco il flywheel e uso il TACOS per verificare che stia girando.
- [ ] So quali domande richiedono un test e non un report.

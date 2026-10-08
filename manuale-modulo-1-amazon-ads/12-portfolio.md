# Capitolo 12 — Portfolio

🎯 **Obiettivo del capitolo:** usare i portfolio come **strumento di governo del budget e
di lettura dei dati**, non come semplici cartelle. Alla fine devi avere uno schema di
organizzazione dell'account e sapere quando un tetto di budget di portfolio ti protegge e
quando invece ti fa perdere vendite.

---

## 12.1 Cosa sono

Un **portfolio** è un contenitore di campagne che sta un livello sopra la campagna:

```
Account
└── Portfolio
    └── Campagna
        └── Gruppo di annunci
            └── Target
```

Offre tre funzioni:

1. **Raggruppamento e reportistica aggregata** — vedi spesa, vendite e ACOS di un
   insieme di campagne senza doverle sommare a mano.
2. **Tetto di budget** — un limite di spesa che vale per l'insieme delle campagne
   contenute, indipendente dai budget giornalieri delle singole campagne.
3. **Date di inizio e fine** — l'intero gruppo di campagne parte e si ferma insieme.

Vincoli da conoscere:

- Una campagna può appartenere a **un solo portfolio** alla volta.
- Il portfolio **non** modifica offerte, targeting o struttura: agisce solo su
  raggruppamento, budget aggregato e date.
- Le funzionalità disponibili variano nel tempo e per tipo di campagna: verifica nella
  tua console quali tipi puoi inserire.

---

## 12.2 Il tetto di budget: come funziona davvero

È la funzione che rende i portfolio uno strumento, non un vezzo organizzativo.

**Tipi di tetto normalmente disponibili**

| Tipo | Comportamento |
|---|---|
| **Nessun tetto** | Solo raggruppamento e reportistica |
| **Tetto mensile ricorrente** | Ogni mese si riazzera; a esaurimento le campagne smettono di erogare fino al mese successivo |
| **Tetto per intervallo di date** | Vale per il periodo indicato: adatto a campagne stagionali o a budget di progetto |

**Come interagisce con i budget di campagna**

I due limiti coesistono e vince il più restrittivo:

```
Campagna A: budget giornaliero 20 €
Campagna B: budget giornaliero 30 €
Campagna C: budget giornaliero 25 €
Somma potenziale mensile ≈ 75 € × 30 ≈ 2.250 €

Portfolio con tetto mensile: 1.500 €
→ Quando la spesa aggregata raggiunge 1.500 €, TUTTE le campagne del portfolio si
  fermano, anche se i loro budget giornalieri non sono esauriti.
```

⚠️ **Il rischio da conoscere:** se il tetto si esaurisce il 20 del mese, le tue campagne
restano **spente per dieci giorni**. Non è solo fatturato perso: è perdita di velocità di
vendita, quindi possibile perdita di posizionamento organico, e ripartenza con un
periodo di riapprendimento. Un tetto è una protezione contro l'eccesso di spesa, ma
usato male è un modo per spegnersi nel momento peggiore.

🛠 **Regola pratica**

1. Calcola la spesa media giornaliera reale del portfolio negli ultimi 30 giorni.
2. Moltiplica per il numero di giorni del mese.
3. Aggiungi un margine del **20–30%**.
4. Quello è il tetto. Se lo raggiungi comunque, indagane la causa (CPC in salita? nuove
   campagne?) invece di limitarti ad alzarlo.
5. Imposta una **notifica** o un controllo in calendario a metà mese sulla percentuale di
   tetto consumata.

---

## 12.3 Schemi di organizzazione

Non esiste uno schema universale: la scelta dipende da cosa devi **decidere**. La
domanda giusta è: «quali aggregazioni voglio poter leggere a colpo d'occhio?».

### Schema A — Per linea di prodotto *(consigliato per la maggior parte dei venditori)*

```
📁 PF_Yoga
📁 PF_Fitness-Accessori
📁 PF_Integratori
📁 PF_Brand-Difesa
```

**Pro:** permette di calcolare ACOS, TACOS e profitto per linea, che è il livello a cui
si decidono i budget. Isola le campagne di marca dalle medie.
**Contro:** un prodotto molto grande può nascondere gli altri dentro la stessa linea.

### Schema B — Per obiettivo

```
📁 PF_Lancio
📁 PF_Crescita
📁 PF_Profitto
📁 PF_Difesa-Brand
📁 PF_Liquidazione
```

**Pro:** ogni portfolio ha un **unico target ACOS**, quindi le medie hanno senso.
Rende immediato spostare un prodotto da una fase all'altra.
**Contro:** perdi la lettura per prodotto; richiede disciplina nel riclassificare i
prodotti quando cambiano fase.

### Schema C — Per fase del funnel

```
📁 PF_Awareness   (SB video, SD lifestyle)
📁 PF_Consideraz. (SP ampia, SP auto, SD contestuale)
📁 PF_Conversione (SP esatta, SP product targeting)
📁 PF_Retargeting (SD remarketing)
```

**Pro:** rende evidente lo squilibrio del mix (per esempio: 95% del budget in
conversione e nulla in acquisizione).
**Contro:** difficile da leggere per prodotto.

### Schema D — Misto *(quello che si usa negli account maturi)*

```
📁 PF_Yoga_Profitto
📁 PF_Yoga_Lancio
📁 PF_Fitness_Profitto
📁 PF_Brand-Difesa
📁 PF_Stagionale_Q4
```

Combina linea e obiettivo. È il più leggibile per account con più linee, purché il
numero di portfolio resti gestibile (indicativamente sotto la ventina).

---

## 12.4 Casi d'uso ad alto valore

**1. Il tetto per il Q4**
Crea `PF_Stagionale_Q4` con tetto a intervallo di date (per esempio 1 novembre –
31 dicembre). In quei mesi i CPC salgono e le campagne possono spendere molto più del
previsto: il tetto è la tua rete di sicurezza. Ricorda però di dimensionarlo con
generosità: in Q4 spegnersi il 15 dicembre è il peggior errore possibile.

**2. La separazione del marchio**
`PF_Brand-Difesa` contiene tutte le campagne sulle keyword del tuo marchio. Escludendo
questo portfolio dalle analisi, ottieni finalmente un ACOS di account che rappresenta
la vera acquisizione (Cap. 3, §3.6 e Cap. 8, Verità 12).

**3. Il budget di lancio a tempo determinato**
`PF_Lancio_ProdottoX` con tetto complessivo e date. Decidi in anticipo: «investo 1.200 €
in otto settimane per acquisire posizionamento». Il portfolio rende quell'impegno
concreto e verificabile, invece che una buona intenzione.

**4. La gestione per cliente (agenzie e consulenti)**
Un portfolio per cliente o per marchio gestito, con reportistica aggregata immediata.

**5. Il test di incrementalità**
Isolando un gruppo di campagne in un portfolio, puoi metterle in pausa tutte insieme e
riattivarle in blocco: è la meccanica che rende praticabile il test descritto nel
Capitolo 3, §3.6.

---

## 12.5 Procedura operativa

🛠 **Creare e popolare un portfolio**

1. **Gestione campagne → Portfolio → Crea portfolio.**
2. Assegna un nome secondo la convenzione: `PF_[Linea]_[Obiettivo]`.
3. Scegli il tipo di budget: nessuno, mensile ricorrente, o intervallo di date.
4. Imposta l'importo (§12.2, regola pratica).
5. Assegna le campagne: dalla lista campagne, selezione multipla → *Aggiungi a
   portfolio*. Puoi anche assegnare il portfolio in fase di creazione della campagna —
   ed è quello che dovresti fare sempre.
6. Verifica dopo l'assegnazione che nessuna campagna sia rimasta orfana: filtra per
   «Nessun portfolio».

🛠 **Controllo mensile**

1. Vista Portfolio: spesa vs tetto, percentuale consumata, giorni rimanenti.
2. Confronta il ritmo di spesa con i giorni residui: se hai consumato il 70% del tetto a
   metà mese, decidi ora (alzare il tetto o ridurre le offerte), non il 28.
3. Calcola ACOS e profitto per portfolio.
4. Riclassifica i prodotti che hanno cambiato fase (da lancio a profitto, per esempio).

---

## 12.6 Quando NON usare un tetto di budget

- Su campagne in **fase di lancio** che stanno funzionando: spegnerle a metà mese
  vanifica l'investimento in ranking già fatto.
- Su campagne **profittevoli e sotto target**: se una campagna guadagna, limitarla è una
  scelta di cassa, non di marketing. Rendila esplicita.
- Come **sostituto della gestione delle offerte**: il tetto tampona il sintomo (spesa
  alta) senza toccare la causa (offerte o keyword sbagliate).
- Su portfolio che contengono **campagne di natura molto diversa**: il tetto si
  esaurirà per colpa della campagna dispersiva, spegnendo anche quelle buone.

---

⚠️ **Errori frequenti sui portfolio**

- Creare portfolio "cartella" senza tetto e senza logica di lettura: non aggiungono nulla.
- Impostare un tetto troppo stretto e scoprirlo a campagne già spente.
- Non controllare la percentuale di tetto consumata durante il mese.
- Mescolare campagne di marca e campagne di acquisizione nello stesso portfolio,
  falsando ogni media.
- Creare decine di portfolio: si torna al problema che si voleva risolvere.
- Lasciare campagne senza portfolio: sfuggono a ogni aggregazione.
- Dimenticare la data di fine di un portfolio stagionale e non capire perché le
  campagne non erogano più. **È la prima cosa da controllare** quando un gruppo di
  campagne si ferma insieme senza motivo apparente.

---

✅ **Checklist di fine capitolo**

- [ ] Ho scelto uno schema di organizzazione e l'ho applicato a tutte le campagne.
- [ ] Nessuna campagna è senza portfolio.
- [ ] I portfolio con tetto hanno un importo dimensionato sulla spesa reale + 20–30%.
- [ ] Ho un controllo in calendario a metà mese sulla percentuale di tetto consumata.
- [ ] Le campagne di marca sono in un portfolio separato ed escluse dalle medie.
- [ ] So che una data di fine dimenticata è la causa più banale di campagne ferme.

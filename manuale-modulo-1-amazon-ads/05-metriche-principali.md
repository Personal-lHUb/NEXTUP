# Capitolo 5 — Metriche principali di Amazon ADS

🎯 **Obiettivo del capitolo:** conoscere ogni metrica della console — formula, significato,
uso decisionale — e possedere un **albero diagnostico** che, partendo dai numeri, porta
alla causa e all'azione.

---

## 5.1 La catena delle metriche

Le metriche non sono un elenco: sono una **catena causale**. Ogni anello moltiplica il
precedente.

```
IMPRESSIONI ──×CTR──► CLIC ──×CVR──► ORDINI ──×Prezzo medio──► VENDITE
     │                  │               │                          │
  quanto sei        quanto sei      quanto           ÷ SPESA  ──►  ROAS / ACOS
  visibile          attraente       convinci
     │                  │               │
  leve: offerta,    leve: immagine,  leve: prezzo, recensioni,
  budget, rilevanza, prezzo, titolo,  contenuto scheda, A+,
  posizionamento    recensioni       disponibilità
```

📐 **L'identità fondamentale**

```
Vendite = Impressioni × CTR × CVR × Prezzo medio
Spesa   = Impressioni × CTR × CPC

ACOS    = CPC ÷ (CVR × Prezzo medio)
```

Da questa identità discende tutto: ci sono solo **quattro** leve reali (impressioni,
CTR, CVR, prezzo) più il costo del clic. Ogni ottimizzazione che fai agisce su una di
queste.

## 5.2 Le metriche di volume

### Impressioni (Impressions)
Numero di volte in cui il tuo annuncio è stato **mostrato**. Non misura le persone:
la stessa persona può generare più impressioni.

- **Impressioni basse** significano: offerta troppo bassa per vincere l'asta, budget
  esaurito presto, target a volume di ricerca nullo, prodotto non indicizzato, Buy Box
  persa, o annuncio non approvato.
- Le impressioni sono la metrica che **si accumula più in fretta**: ti dà segnale in
  ore, mentre gli ordini richiedono settimane.

### Clic (Clicks)
Numero di clic sull'annuncio. È ciò per cui paghi (nei formati CPC). Amazon filtra i
clic non validi/duplicati, quindi il numero può assestarsi nelle 24–48 ore.

### Spesa (Spend / Costo)
Totale speso nel periodo.
📐 `Spesa = Clic × CPC medio`

### Ordini (Orders)
Numero di ordini attribuiti nella finestra di attribuzione. **Un ordine può contenere
più unità e più ASIN.**

### Unità (Units)
Numero di pezzi venduti. `Unità / Ordini` = unità per ordine, utile per capire se il
prodotto viene comprato in multipli.

### Vendite (Sales)
Fatturato attribuito. Include, entro la finestra, anche gli acquisti di **altri tuoi
prodotti** ("halo", vedi Cap. 3, §3.8).

## 5.3 Le metriche di efficienza

### CTR — Click-Through Rate
📐 `CTR = Clic ÷ Impressioni × 100`

Misura quanto il tuo annuncio è **attraente e pertinente** rispetto a chi lo vede.
Su Amazon i valori tipici sono bassi in termini assoluti (spesso sotto l'1%) e variano
molto per categoria e posizionamento. Il capitolo 6 è interamente dedicato a questa
metrica, per una ragione che vedremo lì.

### CPC — Costo per clic
📐 `CPC = Spesa ÷ Clic`

Il costo medio effettivamente pagato. È **quasi sempre inferiore all'offerta** perché
l'asta è di secondo prezzo. Se il tuo CPC medio è costantemente vicinissimo alla tua
offerta, significa che la concorrenza sta offrendo quanto te: sei sul filo.

### CVR — Tasso di conversione
📐 `CVR = Ordini ÷ Clic × 100`

Quanti clic diventano ordini. È il **denominatore dell'ACOS** e quindi la leva più
potente. Nota: il CVR della campagna non coincide con il tasso di conversione della
scheda prodotto che vedi nei Business Report di Seller Central, perché popolazioni e
finestre di misura sono diverse.

### CPA / CPO — Costo per acquisizione (o per ordine)
📐 `CPA = Spesa ÷ Ordini`

Molto più intuitivo dell'ACOS quando parli con chi non fa marketing: «ogni vendita mi
costa 6,40 € di pubblicità». Confrontalo direttamente con il margine di contribuzione
unitario: se `CPA > Margine unitario`, quella campagna perde denaro.

### ACOS e ROAS
📐 `ACOS = Spesa ÷ Vendite × 100` · `ROAS = Vendite ÷ Spesa`
Trattati in dettaglio nel Capitolo 3.

### TACOS
📐 `TACOS = Spesa pubblicitaria ÷ Fatturato totale × 100`
La metrica di salute complessiva (Capitolo 3, §3.5).

## 5.4 Le metriche di marca e di quota

### NTB — New-to-Brand (nuovi per il marchio)
Disponibili su Sponsored Brands, Sponsored Display e DSP. Identificano gli ordini
provenienti da clienti che **non hanno acquistato dal tuo marchio** nell'ultimo anno
(finestra tipicamente a 12 mesi; verifica in console).

Metriche correlate: *Ordini NTB*, *Vendite NTB*, *% ordini NTB*, *Costo per ordine NTB*.

📐 `% ordini NTB = Ordini NTB ÷ Ordini totali × 100`

Come si usa: una campagna di awareness con ACOS alto ma **80% di ordini NTB** sta
comprando **clienti nuovi**, non solo vendite. Valutala col costo di acquisizione
cliente e con il valore che quel cliente genererà nel tempo, non con l'ACOS della
singola transazione.

### Quota di impression per ricerca (Search Term Impression Share)
Percentuale delle impressioni disponibili per un dato termine di ricerca che hai
ottenuto tu. Insieme al **rango di impressioni**, dice quanto spazio stai lasciando ai
concorrenti su termini che ti interessano.

Uso: se una keyword converte benissimo ma la tua quota è al 12%, hai un caso chiarissimo
per alzare l'offerta. Se converte benissimo e sei già all'85%, il margine di crescita
è altrove.

### Percentuale di tempo in budget
Indica quanta parte della giornata la campagna è rimasta attiva prima di esaurire il
budget. Se una campagna profittevole va fuori budget alle 14:00, stai rinunciando a
metà giornata di vendite: alzare il budget è la decisione più semplice e redditizia
disponibile.

## 5.5 Metriche per posizionamento

Il report **Posizionamento** (*Placement*) suddivide la performance in:

| Posizionamento | Caratteristiche tipiche |
|---|---|
| **Inizio dei risultati di ricerca (prima pagina)** | CTR e CVR più alti, CPC più alto |
| **Resto dei risultati di ricerca** | Volume ampio, metriche intermedie |
| **Pagine prodotto / dettaglio** | Molte impressioni, CTR basso, CPC generalmente più basso |

⚠️ **Non confrontare mai il CTR di due campagne senza sapere da quali posizionamenti
provengono.** Una campagna che eroga soprattutto su pagine prodotto avrà un CTR molto
più basso: non è peggiore, sta giocando un altro campionato.

Uso operativo: se il posizionamento "inizio dei risultati" ha ACOS nettamente migliore
del resto, applica un **aggiustamento percentuale positivo** su quel posizionamento a
livello di campagna, anziché alzare tutte le offerte.

## 5.6 Quali metriche guardare, a quale livello

| Livello | Domanda | Metriche da guardare |
|---|---|---|
| **Account** | L'attività pubblicitaria è sana? | TACOS, spesa totale, fatturato totale, profitto |
| **Portfolio** | La linea di prodotto regge? | ACOS, spesa vs tetto, vendite |
| **Campagna** | Il budget è allocato bene? | ACOS, % tempo in budget, spesa, ordini |
| **Gruppo di annunci** | Il tema è coerente? | CTR, CVR, ACOS |
| **Target (keyword/ASIN)** | Questa parola vale il suo costo? | Clic, CVR, CPA, ACOS, quota di impression |
| **Termine di ricerca** | Cosa cercano davvero le persone? | Clic, ordini, ACOS, nuovi termini da promuovere/negativizzare |

**Regola:** ottimizzi **verso il basso** (target e termini di ricerca) e valuti **verso
l'alto** (portfolio e account). Chi guarda solo l'ACOS di account non capisce mai
*perché*; chi guarda solo le keyword non capisce mai *se ne vale la pena*.

## 5.7 L'albero diagnostico

Da usare ogni volta che una campagna non va. Segui i rami nell'ordine.

```
La campagna non genera vendite
│
├─ Impressioni ≈ 0 ?
│  ├─ Budget esaurito?              → alza il budget
│  ├─ Offerta sotto il CPC di mercato? → alza l'offerta del 15–25%
│  ├─ Buy Box persa?                → problema di prezzo/logistica, non di ADS
│  ├─ Prodotto non indicizzato?     → sistema il listing (Cap. 2, §2.2)
│  ├─ Volume di ricerca nullo?      → cambia keyword
│  ├─ Annuncio non approvato?       → controlla lo stato / moderazione creativa
│  └─ Prodotto non disponibile?     → ripristina lo stock
│
├─ Impressioni OK ma CTR molto basso ?
│  ├─ Immagine principale debole    → test immagine (Cap. 6)
│  ├─ Prezzo fuori mercato          → confronta con i primi risultati
│  ├─ Poche recensioni / rating basso → lavora sul social proof
│  ├─ Keyword non pertinente        → negativizza, restringi il match
│  └─ Erogazione su pagine prodotto → normale: segmenta per posizionamento
│
├─ CTR OK ma CVR molto basso ?
│  ├─ Scheda prodotto debole (bullet, A+, immagini secondarie)
│  ├─ Prezzo non competitivo o assenza di offerta/coupon
│  ├─ Recensioni negative recenti
│  ├─ Aspettativa disattesa: l'annuncio promette qualcosa che la scheda non mantiene
│  ├─ Tempi di consegna lunghi / non Prime
│  └─ Variante sbagliata come predefinita
│
└─ CVR OK ma ACOS troppo alto ?
   ├─ CPC superiore al sostenibile   → abbassa l'offerta, verifica il CPC massimo (Cap. 9)
   ├─ Troppa spesa su termini a coda lunga non convertenti → negativizza
   ├─ Aggiustamenti di posizionamento troppo aggressivi → riducili
   ├─ Prezzo di vendita troppo basso per sostenere il CPC → rivedi il prezzo
   └─ Corrispondenza troppo ampia    → sposta il budget verso frase/esatta
```

## 5.8 Significatività: quando i numeri parlano davvero

Prima di agire su una metrica, verifica di avere abbastanza dati.

| Decisione | Volume minimo consigliato |
|---|---|
| Mettere in pausa una keyword per zero conversioni | ≥ 2÷CVR atteso clic (min. 15–20 clic) senza ordini |
| Alzare l'offerta su una keyword | ≥ 10 clic con ACOS ben sotto il target |
| Abbassare l'offerta | ≥ 15–20 clic con ACOS sopra il target |
| Giudicare un test di immagine sul CTR | ≥ 5.000–10.000 impressioni per variante |
| Giudicare un cambio di prezzo sul CVR | ≥ 100 clic per variante |
| Valutare una campagna nel complesso | ≥ 14 giorni e ≥ 100 clic |

📐 **Margine di errore approssimato di un tasso**

```
Errore ≈ √( p × (1 − p) ÷ n )        p = tasso osservato, n = campione
```

Con CVR osservato 10% su 30 clic: errore ≈ √(0,10 × 0,90 ÷ 30) ≈ 5,5%. Cioè il valore
reale sta plausibilmente fra il 4,5% e il 15,5% — un intervallo enorme. Con 300 clic
l'errore scende a ~1,7%. **Questo è il motivo per cui non si decide con pochi clic.**

## 5.9 Metriche vanitose e metriche decisionali

| Metrica | Categoria | Perché |
|---|---|---|
| Impressioni totali | Vanitosa da sola | Facile da gonfiare alzando le offerte |
| Clic totali | Vanitosa da sola | Puoi comprarne quanti ne vuoi |
| ROAS medio di account | Fuorviante | Nasconde le campagne che perdono |
| ACOS per target | **Decisionale** | Dice cosa fare di quella keyword |
| CPA vs margine unitario | **Decisionale** | Confronto diretto costo/beneficio |
| TACOS per prodotto | **Decisionale** | Salute nel tempo |
| Profitto pubblicitario in € | **Decisionale** | L'unico numero che paga gli stipendi |
| % ordini NTB | **Decisionale** (awareness) | Misura l'acquisizione reale |
| Quota di impression | **Decisionale** | Misura lo spazio ancora disponibile |

---

⚠️ **Errori frequenti sulle metriche**

- Confrontare metriche calcolate su finestre di attribuzione diverse.
- Ottimizzare l'ACOS a livello di campagna quando il problema è in tre keyword.
- Mettere in pausa keyword con 3 clic e zero ordini.
- Ignorare la percentuale di tempo in budget e non accorgersi che le campagne migliori
  si spengono a metà giornata.
- Guardare solo le percentuali e mai i valori assoluti in euro.
- Dimenticare che i dati degli ultimi giorni sono incompleti.

---

✅ **Checklist di fine capitolo**

- [ ] So scrivere a memoria le formule di CTR, CVR, CPC, CPA, ACOS, ROAS, TACOS.
- [ ] So che `ACOS = CPC ÷ (CVR × Prezzo)` e capisco quali leve ho a disposizione.
- [ ] So a quale livello guardare quale metrica.
- [ ] So usare l'albero diagnostico per passare da un sintomo a un'azione.
- [ ] Conosco i volumi minimi di dati per ciascun tipo di decisione.
- [ ] Ho configurato le colonne della console per vedere queste metriche (Cap. 11).

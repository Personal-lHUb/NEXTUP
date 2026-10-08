# Capitolo 15 — Aumentare la soglia dei pagamenti

🎯 **Obiettivo del capitolo:** capire come Amazon ti addebita la spesa pubblicitaria,
perché la soglia di pagamento può bloccare le tue campagne nel momento peggiore, e come
richiederne l'aumento con una procedura che ha buone probabilità di successo.

---

## 15.1 Come funziona la fatturazione della pubblicità Amazon

La spesa pubblicitaria **non** viene addebitata clic per clic né sempre a fine mese.
Il meccanismo standard è **duplice**: Amazon addebita il metodo di pagamento quando si
verifica il primo dei due eventi seguenti:

```
┌─────────────────────────────────────────────────────────────┐
│  1. La spesa accumulata raggiunge la SOGLIA DI PAGAMENTO    │
│     (payment threshold / limite di fatturazione)            │
│                            OPPURE                            │
│  2. Si chiude il periodo di fatturazione (fine mese)         │
└─────────────────────────────────────────────────────────────┘
```

Esempio con soglia a 500 € e spesa di 60 € al giorno:

```
Giorno  1 →  60 €   accumulati
Giorno  5 →  300 €
Giorno  8 →  480 €
Giorno  9 →  540 €  → ADDEBITO di ~500 €, il contatore riparte
Giorno 17 →  soglia nuovamente raggiunta → secondo addebito
Fine mese →  addebito del residuo
```

Con quel ritmo di spesa ricevi **tre addebiti al mese** anziché uno.

⚠️ Il valore esatto della soglia, i nomi usati nell'interfaccia («limite di spesa»,
«soglia di fatturazione», «credit line») e la disponibilità della fatturazione mensile
variano per marketplace, tipo di account e anzianità. Verifica sempre nella tua sezione
**Fatturazione**.

---

## 15.2 Perché la soglia esiste ed è bassa all'inizio

Dal punto di vista di Amazon, la soglia è un **limite di rischio di credito**: fra il
momento in cui eroghi gli annunci e il momento in cui paghi, Amazon ti sta di fatto
anticipando denaro. Per un account nuovo, senza storico, quell'anticipo viene tenuto
basso.

La soglia tende a **crescere automaticamente** nel tempo, in funzione di:

- storico di pagamenti andati a buon fine, senza rifiuti;
- anzianità dell'account pubblicitario;
- volume di spesa costante;
- assenza di contestazioni e insoluti;
- affidabilità complessiva dell'account venditore.

Ma la crescita automatica è lenta e non tiene conto dei tuoi piani: se raddoppi il budget
per il Black Friday, la soglia non lo sa.

---

## 15.3 Perché ti conviene aumentarla

### 1. Il rischio operativo: campagne ferme
È il motivo principale. Quando si raggiunge la soglia, Amazon tenta l'addebito. Se
l'addebito **fallisce** — plafond della carta esaurito, carta scaduta, blocco
antifrode della banca, importo insolito — l'account può andare in sospensione per
mancato pagamento e **le campagne si fermano**.

E fermarsi non costa solo il fatturato di quei giorni:

```
Campagne ferme
   → calo della velocità di vendita
   → arretramento del posizionamento organico (Cap. 14, flywheel)
   → alla riattivazione: periodo di riapprendimento e CPC peggiori
   → l'effetto si trascina per settimane
```

Con una soglia alta gli addebiti sono meno frequenti, gli importi più prevedibili e le
occasioni di fallimento si riducono.

### 2. Il rischio moltiplicato durante i picchi
Nei periodi di alta stagione i CPC salgono e i budget vengono alzati: la spesa
giornaliera può triplicare. Una soglia dimensionata sulla spesa ordinaria viene raggiunta
in due giorni, generando addebiti ravvicinati proprio quando la carta è già sotto
pressione per gli acquisti di stock. **È il momento peggiore possibile per fermarsi.**

### 3. Amministrazione e cassa
Meno addebiti significano meno movimenti da riconciliare, rendicontazione più pulita e —
con addebiti a soglia più alta — un ciclo di cassa leggermente più favorevole, perché
paghi più tardi la stessa spesa.

### 4. Meno attriti con la banca
Addebiti frequenti e di importo variabile provenienti da un esercente estero sono uno
degli schemi che i sistemi antifrode segnalano più spesso. Meno addebiti = meno
probabilità di blocco.

---

## 15.4 Come verificare la situazione attuale

🛠 **Procedura**

1. Console Amazon Ads → **Fatturazione** (o *Billing and payments*).
2. Controlla:
   - **Metodo di pagamento**: valido, non in scadenza nei prossimi 3 mesi.
   - **Importo dovuto / saldo maturato**: quanto hai accumulato dall'ultimo addebito.
   - **Cronologia degli addebiti**: quanti ce ne sono stati nell'ultimo mese e di quale
     importo. Da qui **deduci la tua soglia attuale**: se vedi ripetutamente addebiti
     intorno a un valore ricorrente (es. 500 €), quella è la soglia.
   - **Eventuali avvisi** di pagamento non riuscito.
3. Annota la **spesa media giornaliera** degli ultimi 30 giorni.

📐 **Il calcolo che ti serve per la richiesta**

```
Numero di addebiti al mese ≈ (Spesa media giornaliera × 30) ÷ Soglia attuale

Soglia consigliata ≈ Spesa giornaliera prevista di picco × 15
                     (≈ due addebiti al mese anche nei periodi intensi)
```

Esempio: spesa ordinaria 80 €/giorno, prevista 200 €/giorno in Q4.
→ Soglia consigliata ≈ 200 × 15 = **3.000 €**.
Con una soglia attuale di 500 € avresti, in Q4, un addebito ogni 2,5 giorni: dodici
occasioni al mese perché qualcosa vada storto.

---

## 15.5 Come chiedere l'aumento

Non esiste, di norma, un campo in cui modificare la soglia da soli: si richiede al
supporto Amazon Ads, che valuta caso per caso.

🛠 **Procedura**

1. Verifica **prima** i prerequisiti (§15.6): una richiesta fatta con la carta in
   scadenza o con un pagamento fallito recente viene respinta.
2. Console Amazon Ads → **Aiuto / Supporto** → **Contattaci / Apri un caso**.
3. Categoria: **Fatturazione e pagamenti** (o l'equivalente disponibile).
4. Scrivi un messaggio che contenga, in questo ordine:
   - identificativo dell'account pubblicitario e marketplace;
   - spesa media mensile attuale;
   - spesa mensile prevista e **motivazione concreta** (nuovi prodotti, espansione,
     stagionalità, campagna di lancio);
   - la soglia attuale e la soglia richiesta, **con un numero preciso**;
   - il riferimento al tuo storico di pagamenti regolari;
   - la richiesta esplicita, in una frase.
5. Invia e **annota il numero del caso**.
6. Se non ricevi risposta entro 3–5 giorni lavorativi, sollecita sullo stesso caso.
7. Se la risposta è negativa o generica, chiedi cortesemente quali condizioni devono
   essere soddisfatte per ottenere l'aumento: spesso la risposta indica una soglia di
   anzianità o di volume che puoi raggiungere e poi ripresentare.

### Modello di richiesta (italiano)

> Oggetto: Richiesta di aumento della soglia di pagamento — account pubblicitario [ID]
>
> Buongiorno,
>
> scrivo per richiedere l'aumento della soglia di pagamento del nostro account
> pubblicitario [ID account] sul marketplace Amazon.it.
>
> Attualmente la nostra spesa pubblicitaria media è di circa [X] € al mese e la soglia
> risulta fissata a [Y] €, con conseguenti addebiti multipli nel corso dello stesso mese.
>
> Nei prossimi mesi prevediamo di aumentare l'investimento pubblicitario fino a circa
> [Z] € mensili, in relazione a [lancio di nuovi prodotti / espansione del catalogo /
> stagionalità del quarto trimestre]. Con l'attuale soglia questo comporterebbe un
> addebito ogni [N] giorni, con un rischio concreto di interruzione delle campagne in
> caso di mancata autorizzazione da parte dell'istituto emittente.
>
> Il nostro storico di pagamenti è regolare, senza addebiti rifiutati, e il metodo di
> pagamento registrato è valido con scadenza [MM/AAAA].
>
> Chiediamo pertanto l'aumento della soglia di pagamento a [W] €.
>
> Restiamo a disposizione per ogni documentazione utile.
> Cordiali saluti,
> [Nome] — [Ragione sociale] — [ID venditore]

### Modello di richiesta (inglese)

> Subject: Request to increase advertising payment threshold — account [ID]
>
> Hello,
>
> I would like to request an increase of the payment threshold for our advertising
> account [account ID] on the Amazon.it marketplace.
>
> Our current average advertising spend is approximately [X] € per month, while the
> threshold appears to be set at [Y] €, resulting in multiple charges within the same
> month.
>
> Over the coming months we plan to increase our advertising investment to approximately
> [Z] € per month, due to [new product launches / catalogue expansion / Q4 seasonality].
> At the current threshold this would trigger a charge every [N] days, with a concrete
> risk of campaign interruption should a charge fail to be authorised by the issuing bank.
>
> Our payment history is in good standing with no failed charges, and the registered
> payment method is valid until [MM/YYYY].
>
> We therefore request an increase of the payment threshold to [W] €.
>
> Thank you for your assistance.
> Best regards,
> [Name] — [Company] — [Seller ID]

---

## 15.6 Prerequisiti che aumentano le probabilità di successo

| Requisito | Perché conta |
|---|---|
| Storico di pagamenti **senza rifiuti** | È il criterio principale di valutazione |
| Account pubblicitario attivo da **alcuni mesi** | La soglia cresce con l'anzianità |
| Spesa **costante**, non a singhiozzo | Dimostra prevedibilità |
| Metodo di pagamento **valido e con scadenza lontana** | Una carta prossima alla scadenza è un rischio |
| Nessuna contestazione o insoluto in corso | Blocca qualsiasi aumento |
| Account venditore **in regola** | Sospensioni o problemi di performance pesano |
| Richiesta **motivata e quantificata** | Una richiesta generica ottiene una risposta generica |

⚠️ Se la richiesta viene respinta, la strada più efficace è: mantenere alcuni mesi di
spesa regolare e pagamenti puntuali, poi ripresentarla citando il caso precedente. Le
soglie vengono riviste periodicamente anche in automatico.

---

## 15.7 Alternative e strumenti complementari

**Fatturazione mensile / linea di credito.** Per account con spesa elevata, Amazon può
offrire modalità di fatturazione a mese chiuso con termini di pagamento, previa verifica
creditizia e richiesta esplicita. Requisiti e disponibilità variano per paese e tipo di
account: chiedilo al supporto se la tua spesa mensile è significativa.

**Carta con plafond adeguato.** Verifica il limite mensile della carta, non solo il
saldo. Molti blocchi nascono da un plafond mensile insufficiente, non da mancanza di
fondi. Le carte prepagate sono la causa più frequente di addebiti falliti: se possibile,
evitale come metodo principale.

**Metodo di pagamento di riserva.** Dove la console lo consente, registra un secondo
metodo. È l'assicurazione più economica contro il fermo delle campagne.

**Preavviso alla banca.** Prima di un periodo di forte spesa, comunica alla banca che
riceverai addebiti ricorrenti di importo superiore al solito da un esercente estero.
Evita molti blocchi antifrode.

---

## 15.8 Checklist prima di ogni evento ad alta spesa

Da eseguire **2–3 settimane prima** di Prime Day, Black Friday, Natale o di un lancio
importante:

- [ ] Verificata la **scadenza della carta**: non deve cadere durante l'evento.
- [ ] Verificato il **plafond mensile** della carta rispetto alla spesa prevista.
- [ ] Calcolata la **spesa giornaliera di picco** prevista.
- [ ] Calcolata la **soglia consigliata** (spesa di picco × 15).
- [ ] **Richiesta di aumento inviata** con almeno 2–3 settimane di anticipo (le
      lavorazioni non sono immediate).
- [ ] Registrato un **metodo di pagamento di riserva**, se possibile.
- [ ] **Banca informata** degli addebiti ricorrenti di importo maggiore.
- [ ] **Notifiche attive** su problemi di pagamento (Cap. 11).
- [ ] Verificati anche i **tetti di budget dei portfolio** (Cap. 12): un tetto mensile
      dimenticato produce lo stesso identico danno di un pagamento rifiutato.
- [ ] Controllo in calendario a **metà evento** su fatturazione e budget.

---

## 15.9 Cosa fare se le campagne si sono già fermate

🛠 **Procedura di emergenza**

1. **Fatturazione → Importo dovuto**: verifica se esiste un pagamento non riuscito.
2. Se sì, **aggiorna o sostituisci il metodo di pagamento** e salda l'importo in
   sospeso. Nella maggior parte dei casi la riattivazione è rapida.
3. Contatta la banca per verificare se l'addebito è stato bloccato e chiedi lo sblocco
   per gli addebiti futuri di quell'esercente.
4. Apri un **caso al supporto** solo se la sospensione persiste dopo il saldo.
5. Alla riattivazione, **non alzare subito i budget al massimo**: il sistema deve
   riprendere l'erogazione. Torna ai livelli precedenti in modo graduale, nell'arco di
   qualche giorno.
6. **Post-mortem**: registra data, causa e durata del fermo. Ti servirà per capire, nelle
   settimane successive, quanta parte del calo di posizionamento è imputabile a
   quell'interruzione e non alle tue ottimizzazioni.

---

⚠️ **Errori frequenti**

- Scoprire l'esistenza della soglia solo quando le campagne si sono fermate.
- Chiedere l'aumento tre giorni prima del Black Friday.
- Usare una carta prepagata come unico metodo di pagamento.
- Ignorare le email di Amazon su problemi di pagamento.
- Non verificare la scadenza della carta prima della stagione alta.
- Confondere il fermo per pagamento con un problema di algoritmo e passare giorni a
  ritoccare le offerte.
- Dimenticare che anche un **tetto di portfolio** esaurito produce lo stesso effetto.

---

✅ **Checklist di fine capitolo**

- [ ] So come funziona il doppio meccanismo soglia / fine mese.
- [ ] Ho dedotto la mia soglia attuale dalla cronologia degli addebiti.
- [ ] Ho calcolato la soglia adeguata alla mia spesa di picco (spesa giornaliera × 15).
- [ ] Ho inviato la richiesta di aumento, o so esattamente come e quando farlo.
- [ ] Il mio metodo di pagamento è valido, con plafond adeguato, e ho un metodo di riserva.
- [ ] Ho le notifiche attive sui problemi di pagamento.
- [ ] Ho in calendario la checklist pre-evento (§15.8).

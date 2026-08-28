# Capitolo 6 — Perché il CTR è LA metrica più importante

🎯 **Obiettivo del capitolo:** capire perché il CTR occupa una posizione speciale
rispetto a tutte le altre metriche, quali leve lo muovono davvero, e come testarlo con
un metodo che produca conclusioni affidabili invece di impressioni personali.

---

## 6.1 La tesi

📐 `CTR = Clic ÷ Impressioni × 100`

Il CTR misura una cosa sola: **fra tutte le persone che hanno visto il tuo annuncio in
mezzo ai concorrenti, quante hanno scelto te.** È un test comparativo continuo,
gratuito e in tempo reale, che il mercato esegue sul tuo prodotto migliaia di volte al
giorno.

La tesi del capitolo, in una riga:

> **Il CTR è l'unica metrica che è contemporaneamente un input dell'algoritmo, un
> giudizio del mercato e un segnale rapido.** Nessun'altra metrica ha tutte e tre le
> proprietà.

Vediamole una per una.

## 6.2 Primo motivo: il CTR è un *input* dell'algoritmo, non solo un risultato

Amazon non vende spazi al miglior offerente in senso stretto. Vende spazi a chi
massimizza il **ricavo atteso per impressione**.

📐 **La logica dell'asta, semplificata**

```
Ricavo atteso per impressione ≈ Offerta × Probabilità di clic stimata
```

Il CTR storico è il principale ingrediente osservabile della "probabilità di clic
stimata". Quindi:

```
CTR alto → Amazon guadagna di più mostrandoti → vinci più aste con la stessa offerta
        → più impressioni, posizioni migliori, CPC effettivo più basso
```

E al contrario:

```
CTR basso → il tuo annuncio "rende poco" ad Amazon → per vincere devi offrire di più
         → CPC più alto, meno impressioni, ACOS peggiore a parità di CVR
```

Questo è il punto decisivo, e va detto con chiarezza: **il CTR non è solo il risultato
delle tue campagne, è una condizione del loro costo.** Le altre metriche (CVR, ACOS,
ROAS) descrivono cosa è successo. Il CTR retroagisce sul sistema e cambia le condizioni
future. Un CTR migliorato del 50% vale, in pratica, uno sconto sull'asta.

⚠️ Precisazione onesta: Amazon **non pubblica** un "punteggio di qualità" come fa
Google Ads, e non espone la formula dell'asta. Quanto sopra è il modello che spiega in
modo coerente il comportamento osservato del sistema (e che Amazon stessa suggerisce
nella propria documentazione parlando di rilevanza). Trattalo come un modello
operativo affidabile, non come una formula ufficiale.

## 6.3 Secondo motivo: il CTR è un giudizio di mercato su prezzo e proposta

Nella pagina dei risultati di ricerca l'utente vede una quantità di informazioni
limitatissima:

```
┌──────────────────────────────┐
│                              │  ← 1. IMMAGINE PRINCIPALE
│         [ immagine ]         │
│                              │
├──────────────────────────────┤
│ Titolo del prodotto, primi   │  ← 2. TITOLO (i primi 60–70 caratteri)
│ caratteri visibili...        │
│ ★★★★☆  (1.284)               │  ← 3. RATING E NUMERO DI RECENSIONI
│ 24,99 €                      │  ← 4. PREZZO
│ Coupon 10% · Prime           │  ← 5. BADGE E PROMOZIONI
│ Sponsorizzato                │
└──────────────────────────────┘
```

Cinque elementi. Il CTR è il **verdetto del mercato su questi cinque elementi**,
confrontati in tempo reale con quelli dei concorrenti che stanno sulla stessa riga.

Ne segue una cosa preziosa: **il CTR ti dà una diagnosi di competitività prima ancora
di pagare per scoprirla sul CVR.** Se il tuo CTR è metà di quello dei tuoi concorrenti,
sai già — senza attendere gli ordini — che uno di quei cinque elementi è fuori mercato.
Quasi sempre è il prezzo o l'immagine.

## 6.4 Terzo motivo: il CTR è la metrica più veloce da leggere

Questo è un motivo pratico ma decisivo per chi lavora ogni giorno.

| Metrica | Eventi per un giudizio affidabile | Tempo tipico su una campagna media |
|---|---|---|
| **CTR** | 5.000–10.000 impressioni | **1–4 giorni** |
| CVR | 100+ clic | 1–3 settimane |
| ACOS | 100+ clic + finestra di attribuzione | 2–5 settimane |
| Profitto per prodotto | Un ciclo di vendita completo | 1–2 mesi |

Le impressioni si accumulano di uno o due ordini di grandezza più in fretta di ordini e
vendite. Se devi prendere decisioni ogni settimana, il CTR è **l'unico segnale che si
muove alla velocità delle tue decisioni**. Aspettare l'ACOS per capire che una keyword
non c'entra nulla con il tuo prodotto significa pagare due settimane di clic inutili
per un'informazione che il CTR ti aveva già dato al terzo giorno.

## 6.5 Quarto motivo: il CTR separa il problema di rilevanza dal problema di offerta

Un CTR molto basso su una keyword significa quasi sempre una cosa sola: **quella
keyword non descrive il tuo prodotto** (o lo descrive per un pubblico diverso da quello
che cerca).

Esempio: vendi un tappetino yoga spesso 8 mm per principianti. La keyword «tappetino
yoga professionale antiscivolo sottile» genera impressioni, ma il tuo prodotto — spesso
e per principianti — non è quello che cercano. Il CTR crolla. **Non è un problema di
offerta, non è un problema di scheda: è un problema di corrispondenza.** L'azione non
è alzare l'offerta né rifare le foto: è negativizzare quel termine.

Questo rende il CTR il primo filtro nell'ottimizzazione dei termini di ricerca:

```
CTR molto basso   →  keyword non pertinente     →  negativizza
CTR ok, CVR basso →  keyword pertinente ma offerta debole (prezzo, scheda, recensioni)
CTR ok, CVR ok    →  keyword vincente           →  isola in esatta, alza l'offerta
```

## 6.6 Cosa NON dice il CTR (i limiti)

Onestà intellettuale, altrimenti il capitolo diventa uno slogan:

1. **Un CTR alto con CVR zero è un disastro.** Significa che attiri clic che non si
   trasformano in vendite: stai pagando per curiosi. Tipico di immagini "clickbait",
   prezzo civetta di una variante non disponibile, o annuncio che promette qualcosa
   che la scheda non mantiene. Il CTR filtra la **rilevanza**; è il CVR che valida
   l'**offerta**. Servono entrambi.
2. **Il CTR non è confrontabile fra posizionamenti.** Inizio dei risultati di ricerca,
   resto della ricerca e pagine prodotto hanno CTR strutturalmente diversi (in genere
   in quest'ordine, decrescente). Confronta sempre lo stesso posizionamento.
3. **Non è confrontabile fra categorie né fra formati.** Sponsored Products, Sponsored
   Brands e Sponsored Display vivono in contesti visivi diversi.
4. **Non è confrontabile fra tipi di corrispondenza.** Una esatta su una keyword
   centrata avrà quasi sempre CTR molto superiore a un'automatica in *loose match*.
5. **Su volumi bassi è rumore puro.** 2 clic su 300 impressioni non sono uno 0,67%: sono
   un numero senza significato.

## 6.7 Le leve del CTR, in ordine di impatto

**1. Immagine principale** — la leva più potente in assoluto.
- Deve essere leggibile a 150 px di lato, su schermo di telefono, in mezzo ad altri sei
  prodotti.
- Il prodotto deve occupare la massima porzione consentita del riquadro.
- Fondo bianco obbligatorio per l'immagine principale (rispetta le linee guida Amazon:
  niente testo, loghi aggiuntivi, watermark o cornici sull'immagine principale).
- Se vendi un set, si deve capire a colpo d'occhio che è un set.
- Test: rimpicciolisci l'immagine a 200 px e guardala per un secondo. Se non capisci
  cos'è, il mercato non lo capisce.

**2. Prezzo** — la seconda leva, e la più immediata.
Nel risultato di ricerca il prezzo è confrontabile istantaneamente. Se sei il 25% sopra
la mediana della prima pagina senza una differenza percepibile, il CTR crolla. Anche
solo passare da 25,00 € a 24,49 € produce effetti misurabili.

**3. Recensioni: numero e valutazione.**
Il numero fra parentesi funziona da prova sociale. Sotto le 20 recensioni sei
strutturalmente svantaggiato contro un concorrente con 2.000. Sotto le 4,0 stelle il CTR
si deteriora rapidamente. Non è una leva rapida, ma è quella che spiega la maggior
parte delle differenze di CTR strutturali.

**4. Titolo (primi 60–70 caratteri).**
Sui dispositivi mobili il titolo viene troncato. Metti all'inizio: marca + prodotto +
il singolo attributo differenziante. Non riempirlo di keyword: quelle vanno nei campi
di back-end. Un titolo illeggibile viene saltato dall'occhio.

**5. Badge e promozioni.**
Coupon, sconti, *Amazon's Choice*, *Bestseller*, *Prime*, *Scelta Amazon*. Un coupon
visibile nei risultati di ricerca è una delle poche leve che puoi attivare **oggi** e
misurare in 48 ore.

**6. Pertinenza keyword–prodotto.**
Vedi §6.5. Spesso il "problema di CTR" è in realtà una lista di keyword sbagliate.

**7. Posizionamento.**
Se eroghi soprattutto sulle pagine prodotto, il tuo CTR aggregato sarà basso per
costruzione. Segmenta prima di trarre conclusioni.

**8. Formato creativo (solo Sponsored Brands).**
Il video ha in genere un CTR nettamente superiore al formato statico. Titolo del banner
e scelta dei prodotti mostrati sono variabili testabili.

## 6.8 Metodo: come testare il CTR seriamente

🛠 **Procedura — test dell'immagine principale**

1. **Isola la variabile.** Non cambiare prezzo, titolo e immagine nella stessa
   settimana: non sapresti a cosa attribuire la differenza.
2. **Fissa il contesto.** Stessa campagna, stesse keyword, stesse offerte, stesso
   budget, aggiustamenti di posizionamento invariati.
3. **Registra il punto di partenza:** CTR per posizionamento negli ultimi 14 giorni,
   con il numero di impressioni.
4. **Cambia solo l'immagine principale.**
5. **Attendi almeno 5.000–10.000 impressioni per posizionamento** (per una singola
   posizione, e non meno di 7 giorni per assorbire la ciclicità settimanale).
6. **Confronta il CTR sullo stesso posizionamento**, non quello aggregato.
7. **Valuta anche il CVR.** Un'immagine che alza il CTR ma abbassa il CVR può peggiorare
   l'ACOS: hai comprato più clic peggiori.
8. **Decidi sul profitto**, non sul CTR isolato.

📐 **Quando la differenza è reale?** Regola pratica

```
Differenza significativa se:   |CTR_A − CTR_B|  >  2 × √( CTR_medio × (1 − CTR_medio) × (1/n_A + 1/n_B) )
```

Esempio pratico: CTR_A = 0,40% su 20.000 impressioni, CTR_B = 0,52% su 20.000.
CTR medio ≈ 0,46%.
Soglia ≈ 2 × √(0,0046 × 0,9954 × (1/20.000 + 1/20.000)) ≈ 2 × 0,000677 ≈ **0,135%**.
Differenza osservata = 0,12% → **sotto la soglia**: non è ancora concludente, servono
più impressioni. Con 60.000 impressioni per variante la soglia scende a ~0,078% e la
stessa differenza diventerebbe significativa.

Amazon offre anche funzionalità native di test A/B dei contenuti (per venditori con
marchio registrato, sotto voci come *Gestisci i tuoi esperimenti*): quando disponibili
sono preferibili, perché randomizzano correttamente il traffico invece di confrontare
due periodi diversi.

⚠️ **Il difetto strutturale del test "prima/dopo":** confronta due periodi differenti,
in cui possono essere cambiati stagionalità, concorrenza e mix di posizionamenti. È
meglio di niente, ma va interpretato con prudenza; il test randomizzato è
qualitativamente superiore.

## 6.9 Il CTR nella routine settimanale

Come tradurre tutto questo in pratica ogni lunedì mattina:

1. Apri il report **Termini di ricerca** degli ultimi 14 giorni.
2. Ordina per impressioni decrescenti.
3. Isola i termini con **molte impressioni e CTR molto sotto la media della campagna**.
   Sono la tua lista di negativizzazione: stanno consumando spazio e diluendo il
   segnale di rilevanza dell'account.
4. Isola i termini con **CTR alto e CVR alto**: sono i candidati da promuovere in
   campagna esatta con offerta dedicata.
5. Isola i termini con **CTR alto e CVR nullo su volume sufficiente**: qui il problema
   non è la keyword, è la scheda o il prezzo. Non negativizzare subito — indaga.
6. Controlla il CTR **per posizionamento**: se «inizio dei risultati» va molto meglio,
   agisci sull'aggiustamento di posizionamento invece che sulle singole offerte.

---

⚠️ **Errori frequenti sul CTR**

- Confrontare il CTR di campagne che erogano su posizionamenti diversi.
- Trarre conclusioni da poche centinaia di impressioni.
- Ottimizzare il CTR ignorando il CVR e peggiorando l'ACOS.
- Cambiare immagine, titolo e prezzo nello stesso giorno.
- Considerare il CTR un obiettivo in sé anziché un indicatore di rilevanza e un
  moltiplicatore dell'efficienza d'asta.
- Inseguire benchmark di CTR trovati online invece del proprio storico.

---

✅ **Checklist di fine capitolo**

- [ ] So spiegare perché il CTR incide sul costo dei clic futuri, non solo sui clic passati.
- [ ] Confronto il CTR sempre a parità di posizionamento, formato e tipo di corrispondenza.
- [ ] So distinguere un problema di rilevanza (CTR basso) da un problema di offerta (CVR basso).
- [ ] Conosco le leve del CTR in ordine di impatto e so quale posso muovere oggi.
- [ ] So impostare un test isolando una sola variabile e attendendo volumi adeguati.
- [ ] Ho una routine settimanale che parte dal CTR sui termini di ricerca.

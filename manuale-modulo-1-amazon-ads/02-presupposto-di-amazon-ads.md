# Capitolo 2 — Presupposto di Amazon ADS

🎯 **Obiettivo del capitolo:** capire la premessa logica su cui poggia tutto il sistema
pubblicitario di Amazon e verificare, con una procedura ripetibile, se il tuo prodotto
è *pronto* a ricevere traffico a pagamento. Alla fine devi saper dire, con dati alla
mano: «questo ASIN si può pubblicizzare oggi» oppure «prima devo sistemare X».

---

## 2.1 Il presupposto: la pubblicità è un amplificatore, non un motore

Questa è la frase da incorniciare:

> **Le Amazon ADS non creano la performance. La moltiplicano — nel bene e nel male.**

Un annuncio non fa altro che portare più persone sulla tua scheda prodotto. Cosa
succede dopo dipende interamente dalla scheda, dal prezzo, dalle recensioni e
dall'offerta. Se la tua pagina converte al 12%, la pubblicità genera vendite. Se
converte all'1%, la pubblicità genera **fatture**.

Matematicamente:

📐 **Formula**

```
Vendite pubblicitarie = Clic × Tasso di conversione × Prezzo medio
Costo pubblicitario   = Clic × CPC

ACOS = CPC / (Tasso di conversione × Prezzo medio)
```

Guarda bene l'ultima riga: il **tasso di conversione è al denominatore**. Non è una
metrica fra le altre: è il divisore del tuo costo pubblicitario. Raddoppiare il CVR
dimezza l'ACOS, a parità di ogni altra cosa. Nessuna ottimizzazione di offerte, per
quanto raffinata, produce un effetto paragonabile.

Da qui discende la gerarchia del lavoro:

```
1. PRODOTTO e PREZZO      ← determinano il tetto massimo di CVR
2. LISTING e RECENSIONI   ← determinano quanto ti avvicini a quel tetto
3. STRUTTURA CAMPAGNE     ← determina quali clic compri
4. GESTIONE OFFERTE       ← determina quanto li paghi
```

Chi salta i primi due livelli e passa la vita a ritoccare le bid sta lucidando
l'ottone su una nave che imbarca acqua.

## 2.2 Il secondo presupposto: l'indicizzazione

Puoi comprare visibilità solo su parole chiave per le quali Amazon considera il tuo
prodotto **pertinente**. Con i Prodotti sponsorizzati, se il tuo ASIN non è indicizzato
per un termine, l'annuncio non viene erogato (o viene erogato in modo residuale) anche
con un'offerta altissima. L'algoritmo pubblicitario è costruito sopra il motore di
ricerca, non accanto ad esso.

🛠 **Procedura — verificare l'indicizzazione di una keyword**

1. Vai sulla barra di ricerca di Amazon (il marketplace giusto: `amazon.it`, non `.com`).
2. Cerca la stringa: `keyword ASIN` — per esempio `tappetino yoga B08XXXXXXX`.
3. Se il prodotto compare, sei indicizzato per quella keyword. Se non compare, non lo sei.
4. Ripeti per le 10–20 keyword principali che intendi usare nelle campagne esatte.
5. Le keyword non indicizzate vanno inserite nel listing (titolo, bullet, descrizione,
   *search terms* di back-end) e ricontrollate dopo 24–72 ore.

⚠️ Attenzione: l'indicizzazione **non** garantisce un buon posizionamento organico né
un buon rendimento pubblicitario. Garantisce solo che l'asta ti accetti. È una
condizione necessaria, non sufficiente.

## 2.3 Il terzo presupposto: i conti devono chiudere *prima*

Prima di lanciare devi conoscere il tuo **margine di contribuzione unitario**: quanto ti
resta da ogni vendita, dopo tutti i costi variabili, **prima** di considerare la
pubblicità. È quel numero — e solo quello — che stabilisce quanto puoi permetterti di
spendere in ADS.

📐 **Formula del margine di contribuzione**

```
Ricavo netto      = Prezzo di vendita − IVA
Costi variabili   = Costo prodotto (COGS)
                  + Trasporto e dazi verso il magazzino
                  + Commissione di segnalazione Amazon (referral fee, % variabile per categoria)
                  + Costo di gestione logistica (FBA fulfilment / costo spedizione se FBM)
                  + Stoccaggio medio per unità
                  + Accantonamento resi e danni
                  + Eventuali costi di transazione/imballo

Margine di contribuzione = Ricavo netto − Costi variabili
Margine %                = Margine di contribuzione / Ricavo netto
```

E da qui, la soglia che governa tutte le tue decisioni:

📐 **Break-even ACOS = Margine %**

Se dopo tutti i costi ti resta il 32% del ricavo netto, un ACOS del 32% significa
**profitto zero** su quella vendita. Sopra il 32% stai perdendo denaro sull'unità
venduta tramite ADS; sotto, guadagni. Il calcolo completo, con esempio numerico e
strumenti, è nel **Capitolo 9**.

⚠️ Il break-even ACOS **non** è un obiettivo: è il muro. L'obiettivo (target ACOS) si
colloca sotto, e dipende dalla fase — vedi §2.6.

## 2.4 La checklist di prontezza del prodotto

Prima di attivare una campagna su un ASIN, verifica queste dieci voci. Se tre o più
sono rosse, la pubblicità è prematura: stai per pagare per mostrare un prodotto che
non è competitivo.

| # | Requisito | Soglia di riferimento | Perché conta |
|---|---|---|---|
| 1 | **Buy Box** | ≥ 90% negli ultimi 30 gg | Senza Buy Box i Prodotti sponsorizzati non erogano |
| 2 | **Disponibilità** | ≥ 6–8 settimane di copertura | Esaurire lo stock azzera storico e ranking |
| 3 | **Recensioni** | idealmente ≥ 15; sotto 5 sei fragile | Il numero di recensioni incide su CTR e CVR |
| 4 | **Valutazione media** | ≥ 4,0 stelle | Sotto 4,0 il CVR crolla e il costo per ordine esplode |
| 5 | **Immagini** | 6–7 immagini + infografiche + video | La prima immagine è il principale driver del CTR |
| 6 | **Titolo** | keyword primaria nei primi 60–70 caratteri | Rilevanza + leggibilità nel risultato di ricerca |
| 7 | **Bullet point** | 5 punti, benefici + specifiche | Incide sul CVR |
| 8 | **A+ Content** | presente (se hai Brand Registry) | Alza il CVR, quindi abbassa l'ACOS |
| 9 | **Prezzo** | entro ±10–15% della mediana dei primi risultati | Il confronto è immediato: il prezzo è il filtro |
| 10 | **Categoria e nodo** | corretti e coerenti | Categoria sbagliata = asta sbagliata |

🛠 **Procedura — come raccogliere questi dati in 20 minuti**

1. **Buy Box**: Seller Central → *Report* → *Business Report* → *Dettaglio pagina
   per figlio ASIN*, colonna percentuale Buy Box.
2. **Copertura stock**: unità disponibili ÷ media vendite giornaliere degli ultimi 30 gg.
3. **Recensioni, rating, immagini, prezzo**: apri la tua scheda in incognito e le
   schede dei primi 5 risultati organici per la tua keyword principale. Compila una
   tabella di confronto riga per riga. Questo confronto — banale, manuale — vale più
   di qualsiasi tool.
4. **Indicizzazione**: procedura §2.2.
5. **Margine**: Capitolo 9.

## 2.5 Il presupposto del dato: quanto traffico serve per decidere

Un errore che costa moltissimo è **decidere troppo presto**. Con 4 clic e 0 ordini non
sai nulla: se il tuo tasso di conversione reale fosse un ottimo 10%, la probabilità di
non vedere alcun ordine in 4 clic è comunque circa il 66%.

📐 **Regola pratica del budget di apprendimento per keyword**

```
Clic minimi per giudicare una keyword ≈ 2 ÷ CVR atteso        (soglia "primo segnale")
Clic per una decisione solida         ≈ 3 ÷ CVR atteso, minimo 25–30 clic

Budget di test per keyword = Clic minimi × CPC atteso
```

Esempio: CVR atteso 10%, CPC atteso 0,45 €.
→ soglia di primo segnale ≈ 20 clic ≈ 9,00 € per keyword.
→ decisione solida ≈ 30 clic ≈ 13,50 € per keyword.
Con 20 keyword da testare: **fra 180 € e 270 € solo per la fase di raccolta dati**, da
spalmare su 2–4 settimane.

Se questo importo ti sembra insostenibile, non hai un problema di pubblicità: hai un
problema di dimensionamento. Riduci il numero di keyword da testare, non il numero di
clic per keyword. Testare 60 keyword con 5 clic ciascuna produce **zero** informazione
utile; testarne 10 con 30 clic ciascuna produce dieci decisioni affidabili.

## 2.6 Il presupposto strategico: dichiara l'obiettivo prima di strutturare

| Obiettivo | ACOS target | Metrica principale | Struttura tipica |
|---|---|---|---|
| **Lancio** | Anche 2–3× il break-even, per 4–8 settimane | Velocità di vendita, ranking organico, ricerche scoperte | Auto + ampia aggressive, budget generoso, poche negative |
| **Crescita profittevole** | Poco sotto il break-even | Fatturato totale, TACOS in calo | Piramide auto→frase→esatta, negativizzazione continua |
| **Profitto / maturità** | 50–70% del break-even | Margine assoluto, ACOS | Prevalenza di esatte e ASIN targeting, offerte controllate |
| **Difesa del marchio** | Basso (5–15%) | Quota di impression sul proprio brand | Campagne esatte sulle keyword di marca + SD sulle proprie schede |
| **Liquidazione stock** | Sopra il break-even, consapevolmente | Unità vendute/giorno, costi di stoccaggio evitati | Ampia + auto, offerte alte, orizzonte breve |

⚠️ **Errore frequente:** perseguire "lancio" e "profitto" nella stessa campagna. Il
risultato è che la campagna non fa bene nessuna delle due cose e i dati diventano
illeggibili. Se hai due obiettivi, servono **due campagne separate**, con nomi che
esplicitano l'obiettivo (vedi la convenzione di naming nel Capitolo 7).

## 2.7 I presupposti operativi dell'account

Prima del primo lancio, metti a posto anche l'infrastruttura:

- **Metodo di pagamento valido** e non in scadenza (Capitolo 15).
- **Soglia di pagamento** adeguata alla spesa prevista, soprattutto in vista di eventi
  ad alto volume (Capitolo 15).
- **Fuso orario e valuta** dell'account pubblicitario verificati: tutti i report li
  useranno (Capitolo 4).
- **Colonne e viste** della console configurate (Capitolo 11), altrimenti leggerai i
  dati sbagliati fin dal primo giorno.
- **Convenzione di naming** decisa *prima* di creare la prima campagna. Rinominare 80
  campagne a posteriori è un lavoro inutile e evitabile.
- **Foglio di tracciamento delle modifiche**: data, campagna, cosa hai cambiato,
  perché. Senza questo, fra due mesi non saprai cosa ha causato cosa.

---

⚠️ **Errori frequenti sul presupposto**

- «Lancio le ADS così arrivano le prime recensioni». Al contrario: senza recensioni il
  CVR è basso, l'ACOS è insostenibile e il budget finisce prima di generare recensioni.
  Le recensioni iniziali si costruiscono con prezzo di lancio, programmi Amazon
  disponibili e volume, non pagando clic a 0,60 €.
- Pubblicizzare tutto il catalogo "per vedere cosa funziona". La pubblicità è uno
  strumento di amplificazione: applicala ai prodotti che già danno segnali positivi.
- Considerare l'ACOS l'unica metrica, ignorando il margine assoluto in euro.
- Modificare la campagna ogni giorno. La finestra di attribuzione (Capitolo 3) rende i
  dati di ieri incompleti: interverrai su numeri che non esistono ancora.
- Non conoscere il proprio break-even ACOS. È la singola omissione più costosa del
  Modulo 1.

---

✅ **Checklist di fine capitolo**

- [ ] Conosco il mio margine di contribuzione unitario, in euro e in percentuale.
- [ ] Conosco il mio break-even ACOS e l'ho scritto da qualche parte di visibile.
- [ ] Ho compilato la checklist di prontezza (§2.4) per ogni ASIN che voglio pubblicizzare.
- [ ] Ho verificato l'indicizzazione delle mie keyword principali.
- [ ] Ho stimato il budget di apprendimento e so quanto durerà la fase di test.
- [ ] Ho dichiarato per iscritto l'obiettivo di ciascuna campagna che sto per creare.

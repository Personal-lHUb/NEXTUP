# Capitolo 9 — Sito per calcolare l'ACOS

🎯 **Obiettivo del capitolo:** costruire il tuo calcolatore di ACOS di pareggio e di CPC
massimo, conoscere gli strumenti online affidabili e — soprattutto — non dipendere da
nessuno di essi, perché la matematica sta in cinque righe.

---

## 9.1 Perché ti serve un calcolatore

Il numero che governa ogni decisione pubblicitaria è il **break-even ACOS**. Senza
quel numero:

- non sai se un ACOS del 28% è buono o catastrofico;
- non sai quale offerta massima puoi permetterti;
- non sai se una campagna vada spinta o ridotta;
- non sai quale prodotto merita budget.

Il calcolatore serve a produrre **tre numeri** per ciascun prodotto:

1. **Margine di contribuzione %** → il tetto assoluto
2. **Break-even ACOS** (= margine %) → il muro
3. **CPC massimo sostenibile** → l'offerta che non puoi superare

---

## 9.2 Lo strumento ufficiale: il calcolatore dei ricavi FBA

Prima di calcolare l'ACOS devi conoscere le **commissioni Amazon** con precisione. Non
stimarle: sono variabili per categoria, peso e dimensioni.

🛠 **Procedura**

1. Vai su **Seller Central → Aiuto / Strumenti → Calcolatore dei ricavi FBA**
   (raggiungibile anche cercando "Revenue Calculator" dentro Seller Central; l'URL varia
   per marketplace, su Italia è tipicamente `sellercentral.amazon.it/revenuecalculator`).
2. Cerca il tuo ASIN, o un ASIN concorrente equivalente per dimensioni e peso.
3. Inserisci il **prezzo di vendita** previsto.
4. Inserisci il **costo del prodotto** (comprensivo di trasporto verso il magazzino,
   dazi e imballo).
5. Lo strumento restituisce: commissione di segnalazione, costi di gestione FBA,
   confronto FBA vs FBM e margine netto.

⚠️ Il calcolatore ufficiale **non** include: stoccaggio a lungo termine, resi e danni,
costi di rimozione, IVA, costi indiretti, e naturalmente la pubblicità. Aggiungili tu.

---

## 9.3 Il calcolo completo, riga per riga

📐 **Schema di calcolo**

```
 A  Prezzo di vendita al pubblico (IVA inclusa)
 B  IVA                                        = A − A ÷ (1 + aliquota)
 C  Ricavo netto                               = A − B
─────────────────────────────────────────────────────────────────
 D  Costo del prodotto (COGS)
 E  Trasporto e dazi verso il magazzino (per unità)
 F  Commissione di segnalazione Amazon         = C × % di categoria
 G  Costo di gestione logistica (FBA o spedizione FBM)
 H  Stoccaggio medio per unità venduta
 I  Accantonamento resi/danni                  = C × tasso di reso × quota non recuperabile
 J  Altri costi variabili (imballo, etichette, transazione)
─────────────────────────────────────────────────────────────────
 K  Totale costi variabili                     = D+E+F+G+H+I+J
 L  MARGINE DI CONTRIBUZIONE (€)               = C − K
 M  MARGINE DI CONTRIBUZIONE (%)               = L ÷ C
─────────────────────────────────────────────────────────────────
 N  BREAK-EVEN ACOS                            = M
 O  BREAK-EVEN ROAS                            = 1 ÷ M
 P  TARGET ACOS (profitto desiderato)          = M × (1 − quota di margine trattenuta)
 Q  CPC MASSIMO DI PAREGGIO                    = C × M × CVR
 R  CPC MASSIMO A TARGET                       = C × P × CVR
```

### Esempio numerico completo

Tappetino yoga, venduto in Italia in FBA.

| Rif. | Voce | Valore |
|---|---|---|
| A | Prezzo al pubblico (IVA 22% inclusa) | 29,99 € |
| B | IVA | 5,41 € |
| **C** | **Ricavo netto** | **24,58 €** |
| D | Costo prodotto | 5,80 € |
| E | Trasporto e dazi per unità | 1,20 € |
| F | Commissione di segnalazione (15% su C) | 3,69 € |
| G | Gestione FBA | 4,20 € |
| H | Stoccaggio medio per unità venduta | 0,45 € |
| I | Resi e danni (tasso reso 5%, 50% non recuperabile) | 0,61 € |
| J | Altri costi variabili | 0,20 € |
| **K** | **Totale costi variabili** | **16,15 €** |
| **L** | **Margine di contribuzione** | **8,43 €** |
| **M** | **Margine di contribuzione %** | **34,3%** |

Da cui:

```
N  Break-even ACOS  = 34,3%
O  Break-even ROAS  = 1 ÷ 0,343 = 2,92x
P  Target ACOS (trattengo il 45% del margine) = 34,3% × 0,55 = 18,9%
Q  CPC max di pareggio (CVR 10%) = 24,58 × 0,343 × 0,10 = 0,84 €
R  CPC max a target  (CVR 10%)   = 24,58 × 0,189 × 0,10 = 0,46 €
```

**Lettura:** posso offrire fino a 0,84 € a clic senza perdere denaro, ma se voglio
trattenere il 45% del margine devo stare intorno a 0,46 €. Sopra 0,84 € sto pagando per
vendere in perdita.

⚠️ Il CPC massimo è **estremamente sensibile al CVR**. Se il CVR reale è 6% invece del
10% ipotizzato, il CPC massimo di pareggio scende a 0,50 €: l'offerta che sembrava
prudente diventa una perdita. Per questo, appena hai dati reali, **sostituisci il CVR
stimato con quello osservato per quella specifica keyword**.

---

## 9.4 La tabella di sensibilità: lo strumento che nessuno usa

Costruiscila una volta per prodotto e appendila al muro.

**CPC massimo di pareggio (€) — ricavo netto 24,58 €**

| Margine ↓ / CVR → | 4% | 6% | 8% | 10% | 12% | 15% |
|---|---|---|---|---|---|---|
| 20% | 0,20 | 0,29 | 0,39 | 0,49 | 0,59 | 0,74 |
| 25% | 0,25 | 0,37 | 0,49 | 0,61 | 0,74 | 0,92 |
| 30% | 0,29 | 0,44 | 0,59 | 0,74 | 0,88 | 1,11 |
| **34,3%** | 0,34 | 0,51 | 0,67 | **0,84** | 1,01 | 1,26 |
| 40% | 0,39 | 0,59 | 0,79 | 0,98 | 1,18 | 1,47 |
| 50% | 0,49 | 0,74 | 0,98 | 1,23 | 1,47 | 1,84 |

Come si usa: prendi una keyword con CVR osservato 6% e margine 34,3% → il tuo tetto è
0,51 €. Se il CPC medio su quella keyword è 0,78 €, quella keyword sta perdendo denaro,
indipendentemente da quanto "sembra importante".

---

## 9.5 Costruire il calcolatore in un foglio di calcolo

🛠 **Procedura (Google Sheets o Excel)**

Colonna A = etichette, colonna B = valori.

```
B1   Prezzo al pubblico (IVA incl.)      29,99
B2   Aliquota IVA                        0,22
B3   Ricavo netto        =B1/(1+B2)
B4   Costo prodotto                      5,80
B5   Trasporto/dazi                      1,20
B6   % commissione segnalazione          0,15
B7   Commissione            =B3*B6
B8   Gestione FBA                        4,20
B9   Stoccaggio                          0,45
B10  Tasso di reso                       0,05
B11  Quota non recuperabile              0,50
B12  Costo resi             =B3*B10*B11
B13  Altri costi variabili               0,20
B14  Totale costi var.      =B4+B5+B7+B8+B9+B12+B13
B15  Margine €              =B3-B14
B16  Margine %              =B15/B3
B17  Break-even ACOS        =B16
B18  Break-even ROAS        =1/B16
B19  Quota margine trattenuta            0,45
B20  Target ACOS            =B16*(1-B19)
B21  CVR atteso                          0,10
B22  CPC max pareggio       =B3*B17*B21
B23  CPC max a target       =B3*B20*B21
B24  Profitto per ordine a target  =B15-(B3*B20)
```

Formatta `B16:B17` e `B20` come percentuale. Duplica il foglio per ogni prodotto, o
trasformalo in tabella con una riga per ASIN.

**Estensione consigliata — il controllo settimanale.** Aggiungi tre colonne per ogni
keyword: `CPC medio osservato`, `CVR osservato`, e
`CPC max = Ricavo netto × Target ACOS × CVR osservato`. Poi una colonna semaforo:

```
=SE(CPC_medio > CPC_max_pareggio; "🔴 PERDITA";
   SE(CPC_medio > CPC_max_target;  "🟡 SOTTO TARGET"; "🟢 OK"))
```

Questa singola colonna sostituisce l'80% delle "analisi di ottimizzazione" che si
trovano in giro.

---

## 9.6 Strumenti online di terze parti

Esistono numerosi calcolatori ACOS gratuiti offerti dai fornitori di software per
venditori Amazon (fra i più noti: Helium 10, Jungle Scout, SellerApp, Sellerboard,
Perpetua e simili). Sono comodi per un calcolo veloce.

**Cosa valutare prima di fidarti di uno strumento**

| Criterio | Domanda da porti |
|---|---|
| Trasparenza della formula | Mostra i passaggi o è una scatola nera? |
| Gestione dell'IVA | Lavora su prezzo lordo o netto? (differenza enorme in UE) |
| Commissioni | Usa la % della **tua** categoria o un valore generico? |
| Resi e stoccaggio | Li include o li ignora? |
| Marketplace | È tarato su `.com` (senza IVA) o su marketplace europei? |
| Dati richiesti | Ti chiede credenziali o accesso all'account per un semplice calcolo? |

⚠️ **Avvertenza pratica:** molti calcolatori online sono tarati sul mercato
statunitense e ignorano l'IVA. In Europa questo produce un margine sovrastimato di
15–25 punti percentuali e quindi un break-even ACOS completamente sbagliato — nella
direzione pericolosa. Verifica **sempre** che il calcolo parta dal ricavo **netto IVA**.

⚠️ **Sui dati:** un calcolatore ACOS non ha bisogno di accedere al tuo account Amazon.
Se te lo chiede per un semplice calcolo aritmetico, sta raccogliendo dati commerciali,
non aiutandoti. Il tuo costo prodotto e il tuo margine sono informazioni sensibili.

**Conclusione onesta:** il calcolo è talmente semplice che il foglio di §9.5 batte
qualsiasi strumento esterno, perché è tarato sui *tuoi* costi reali, non su medie di
categoria. Usa gli strumenti online per una verifica incrociata, non come fonte
primaria.

---

## 9.7 Casi particolari

**Prodotti con varianti a prezzi diversi**
Calcola il margine per ciascuna variante e usa la **media ponderata sul mix di vendita
reale**, non la media aritmetica. Se il 70% delle vendite è sulla variante a margine
peggiore, è quello il numero che conta.

**Prodotti in bundle o multipack**
Il margine percentuale cresce quasi sempre con la dimensione del pacco (le commissioni
fisse si diluiscono). Un multipack può sostenere un CPC molto più alto sulle stesse
keyword: è una leva strategica sottovalutata.

**Prodotti civetta (loss leader)**
Se un prodotto serve ad acquisire clienti che poi riacquistano, il break-even va
calcolato sul **valore del cliente nel tempo**, non sulla singola transazione.
Attenzione: questo ragionamento è corretto solo se hai **dati reali di riacquisto**.
Senza quei dati è un alibi per perdere denaro.

**Fase di lancio**
Puoi consapevolmente accettare un ACOS sopra il break-even per acquisire ranking. Ma
mettilo a budget come **investimento a tempo determinato**: definisci prima quanto e per
quante settimane, e verifica a scadenza che il posizionamento organico sia
effettivamente migliorato.

**Stagionalità**
Se stoccaggio e CPC salgono in Q4, il break-even di novembre non è quello di maggio.
Ricalcola il foglio prima di ogni stagione forte.

---

⚠️ **Errori frequenti nel calcolo**

- Dimenticare l'IVA e credere di avere il 50% di margine invece del 34%.
- Usare la commissione "standard 15%" quando la propria categoria ha un'aliquota diversa.
- Ignorare resi e stoccaggio: su alcune categorie valgono diversi punti di margine.
- Calcolare il break-even una volta sola e non aggiornarlo quando cambiano costi o prezzo.
- Confondere break-even ACOS (il muro) con target ACOS (l'obiettivo).
- Usare un CVR ipotetico ottimistico invece del CVR osservato.

---

✅ **Checklist di fine capitolo**

- [ ] Ho costruito il foglio di calcolo con tutte le voci di costo variabile.
- [ ] Conosco margine %, break-even ACOS, target ACOS e CPC massimo per ogni ASIN.
- [ ] Ho verificato le commissioni reali della mia categoria con lo strumento ufficiale.
- [ ] Il mio calcolo parte dal ricavo netto IVA, non dal prezzo lordo.
- [ ] Ho costruito la tabella di sensibilità CPC massimo × CVR × margine.
- [ ] Ho aggiunto la colonna semaforo al mio controllo settimanale delle keyword.

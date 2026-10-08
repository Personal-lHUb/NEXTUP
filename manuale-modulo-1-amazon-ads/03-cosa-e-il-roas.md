# Capitolo 3 — Cosa è il ROAS

🎯 **Obiettivo del capitolo:** padroneggiare ROAS, ACOS, TACOS e break-even, sapere
convertirli fra loro a mente, e — soprattutto — capire perché un ROAS alto non è
automaticamente una buona notizia.

---

## 3.1 Definizione

**ROAS** = *Return On Ad Spend*, ritorno sulla spesa pubblicitaria.

📐 **Formula**

```
ROAS = Vendite generate dalla pubblicità ÷ Spesa pubblicitaria
```

Si legge come un **moltiplicatore**: ROAS 4 (o 4x) significa «per ogni euro speso in
pubblicità ne sono rientrati 4 di fatturato». Alcune interfacce lo esprimono in
percentuale (400%): è lo stesso numero.

**Attenzione a cosa c'è al numeratore:** *fatturato*, non profitto. Il ROAS misura
quanti soldi sono entrati, non quanti ne sono rimasti. È la fonte del più diffuso
autoinganno del settore.

## 3.2 ROAS e ACOS: due facce della stessa moneta

**ACOS** = *Advertising Cost of Sale*, costo pubblicitario della vendita.

📐 **Formula**

```
ACOS = Spesa pubblicitaria ÷ Vendite generate dalla pubblicità × 100

ACOS = 1 ÷ ROAS          ROAS = 1 ÷ ACOS
```

Sono **reciproci**: la stessa informazione, capovolta. Amazon usa storicamente l'ACOS
come metrica principale nell'interfaccia; il resto del mondo pubblicitario parla di
ROAS. Devi saper passare dall'uno all'altro istantaneamente.

| ACOS | ROAS | Lettura |
|---|---|---|
| 10% | 10,0x | Molto efficiente — o stai sotto-investendo |
| 15% | 6,7x | Efficiente |
| 20% | 5,0x | Buono nella maggior parte delle categorie |
| 25% | 4,0x | Tipico di un account sano |
| 30% | 3,3x | Accettabile se il margine lo consente |
| 33,3% | 3,0x | Break-even per chi ha il 33% di margine |
| 40% | 2,5x | Sostenibile solo in lancio o con margini alti |
| 50% | 2,0x | Investimento, non profitto |
| 100% | 1,0x | Spendi esattamente quanto incassi |
| 200% | 0,5x | Perdita netta grave |

Il trucco mnemonico: **ACOS × ROAS = 1** (o 100 se lavori in percentuale).

## 3.3 Break-even: la soglia che conta davvero

Il ROAS "buono" non esiste in assoluto. Esiste solo **rispetto al tuo margine**.

📐 **Formule di break-even**

```
Break-even ACOS  = Margine di contribuzione %
Break-even ROAS  = 1 ÷ Margine di contribuzione %
```

| Margine di contribuzione | Break-even ACOS | Break-even ROAS |
|---|---|---|
| 10% | 10% | 10,0x |
| 15% | 15% | 6,7x |
| 20% | 20% | 5,0x |
| 25% | 25% | 4,0x |
| 30% | 30% | 3,3x |
| 40% | 40% | 2,5x |
| 50% | 50% | 2,0x |

Conseguenza da interiorizzare: **un ROAS di 3x può essere un disastro per un venditore
con il 20% di margine e un affare per uno con il 45%**. Chiunque ti dica "il ROAS deve
stare sopra 4" senza conoscere i tuoi conti sta dicendo una frase priva di contenuto.

📐 **Dal break-even al target**

```
Target ACOS = Break-even ACOS × (1 − Quota di margine che vuoi trattenere)
```

Esempio: break-even ACOS 32%, vuoi trattenere il 40% del margine come profitto
→ Target ACOS = 32% × 0,60 = **19,2%** → Target ROAS ≈ 5,2x.

## 3.4 ROAS ≠ ROI ≠ profitto

Tre numeri diversi che vengono continuamente confusi.

📐 **Formule a confronto**

```
ROAS   = Fatturato pubblicitario ÷ Spesa pubblicitaria
ROI    = (Profitto − Investimento) ÷ Investimento
Profitto pubblicitario = Fatturato pubbl. × Margine % − Spesa pubblicitaria
```

**Esempio numerico completo**

| Voce | Valore |
|---|---|
| Prezzo di vendita (IVA esclusa) | 24,59 € |
| Costo prodotto + trasporto | 7,00 € |
| Commissione di segnalazione (15%) | 3,69 € |
| Logistica FBA | 4,20 € |
| Stoccaggio + accantonamento resi | 1,10 € |
| **Margine di contribuzione** | **8,60 € → 35,0%** |

Break-even ACOS = **35%** → break-even ROAS = **2,86x**

Nel mese: spesa pubblicitaria 1.000 €, vendite pubblicitarie 4.000 €.

```
ROAS = 4.000 ÷ 1.000 = 4,0x
ACOS = 1.000 ÷ 4.000 = 25%
Margine lordo generato = 4.000 × 35% = 1.400 €
Profitto pubblicitario = 1.400 − 1.000 = 400 €
ROI pubblicitario      = 400 ÷ 1.000 = 40%
```

ROAS 4x → ROI 40%. Sembrano numeri completamente diversi, e lo sono: descrivono cose
diverse. Il primo interessa a chi ottimizza le campagne, il secondo a chi paga le
fatture.

Nota utile: quando ACOS = margine %, il profitto pubblicitario è esattamente zero,
qualunque sia il fatturato. Verifica: 4.000 × 35% − 1.400 = 0. ✔

## 3.5 TACOS: la metrica di salute dell'account

**TACOS** = *Total Advertising Cost of Sale*.

📐 **Formula**

```
TACOS = Spesa pubblicitaria ÷ Fatturato TOTALE (pubblicitario + organico) × 100
```

L'ACOS guarda solo dentro la campagna. Il TACOS guarda tutta l'azienda, e risponde
alla domanda che conta davvero: **quanto del mio fatturato complessivo se ne va in
pubblicità?**

Come leggerlo nel tempo:

- **TACOS in calo, fatturato in crescita** → situazione ideale: la pubblicità sta
  alimentando il ranking organico, che cresce e ti rende progressivamente meno
  dipendente dal pagato. È il segnale che il *flywheel* (Capitolo 14) sta girando.
- **TACOS stabile, fatturato in crescita** → stai comprando crescita in modo
  proporzionale. Sostenibile, ma non stai accumulando asset organico.
- **TACOS in crescita, fatturato piatto** → allarme rosso: stai pagando sempre di più
  per lo stesso risultato. Cause tipiche: aumento della concorrenza in asta, listing
  peggiorato, perdita di posizionamento organico, cannibalizzazione.
- **TACOS in crescita durante un lancio** → normale e voluto, se limitato nel tempo.

⚠️ Il TACOS va letto **per prodotto o per linea**, non solo a livello di account: un
account aggregato nasconde il prodotto che sta bruciando.

## 3.6 Il problema serio: ROAS dichiarato vs ROAS incrementale

Ecco il concetto che separa chi gestisce le ADS da chi le subisce.

Amazon ti attribuisce una vendita se l'utente ha **cliccato** sul tuo annuncio e poi ha
comprato entro la finestra di attribuzione. Ma non ti dice — perché non può saperlo —
se quella persona **avrebbe comprato comunque**, magari cliccando sul risultato
organico che stava due righe più sotto.

📐 **Concetto**

```
ROAS incrementale = Vendite realmente aggiuntive ÷ Spesa pubblicitaria
```

Il caso più evidente è la **keyword di marca**. Se qualcuno cerca il nome esatto del
tuo brand, molto probabilmente ti troverà anche senza annuncio. Il ROAS di quella
campagna sarà spettacolare (spesso 10–20x) perché il CVR è altissimo, ma buona parte
di quelle vendite non è incrementale: le stai ricomprando.

Questo **non** significa che le campagne di marca siano inutili — presidiare le proprie
keyword impedisce ai concorrenti di comprare traffico che ti cerca esplicitamente, e
il costo è normalmente basso. Significa che il loro ROAS non va confrontato con quello
delle campagne di acquisizione, perché misura una cosa diversa.

🛠 **Procedura — stimare l'incrementalità (test grezzo ma efficace)**

1. Isola le campagne di marca in un portfolio dedicato.
2. Registra per 14 giorni: fatturato totale dell'ASIN, sessioni, ordini, spesa ADS.
3. Metti in pausa le sole campagne di marca per 14 giorni (evita periodi di
   stagionalità anomala, promozioni o eventi Amazon).
4. Confronta il **fatturato totale**, non quello pubblicitario.
5. Se il fatturato totale cala meno della spesa risparmiata, quelle campagne erano in
   larga parte non incrementali. Se cala di più, erano incrementali (e i concorrenti
   stavano probabilmente aspettando il tuo spazio).
6. Riattiva e ripeti dopo qualche mese: l'equilibrio competitivo cambia.

⚠️ Non fare questo test su prodotti in lancio, in stagionalità forte o con stock
limitato: il rumore supererebbe il segnale.

## 3.7 L'attribuzione: perché i numeri di oggi non sono i numeri finali

Le vendite non vengono attribuite istantaneamente. Una persona clicca oggi e compra fra
sei giorni: quella vendita verrà retro-attribuita al **giorno del clic**, non al giorno
dell'acquisto.

Conseguenze pratiche:

1. **I dati recenti sono sempre sottostimati.** L'ACOS di ieri sembrerà pessimo e
   migliorerà nei giorni successivi, da solo. Chi taglia le offerte guardando gli
   ultimi 2–3 giorni sta reagendo a un'illusione ottica.
2. **Dopo ogni modifica servono almeno 7–14 giorni** prima di valutarne l'effetto.
3. **Non confrontare periodi di lunghezza diversa**, e non includere gli ultimi giorni
   in analisi che devono essere definitive.
4. Le finestre di attribuzione **differiscono per formato** (Prodotti, Marchi, Display)
   e alcune metriche possono essere disponibili su più finestre. In console le colonne
   riportano esplicitamente la finestra (es. «Vendite totali a 14 giorni»): **leggi
   sempre l'etichetta della colonna** e confronta solo colonne omogenee. Verifica i
   valori correnti nella tua console, perché Amazon li ha modificati nel tempo.

⚠️ Errore frequentissimo: confrontare l'ACOS della campagna Sponsored Products con
quello della campagna Sponsored Brands senza accorgersi che le colonne usano finestre
o definizioni diverse (le campagne di marca includono, per esempio, metriche
*new-to-brand* e in certi casi conversioni da visualizzazione).

## 3.8 Le "vendite alone" (halo sales)

Le vendite attribuite a una campagna includono anche **acquisti di altri tuoi prodotti**
effettuati dopo il clic sull'annuncio, entro la finestra di attribuzione. Se qualcuno
clicca sull'annuncio del tuo tappetino e finisce per comprare anche il tuo blocco yoga,
entrambe le vendite alimentano il ROAS di quella campagna.

Questo gonfia il ROAS delle campagne che portano traffico a un catalogo ampio (tipico
di Sponsored Brands verso il Brand Store). Per separare i due effetti usa il report
**Prodotti acquistati** (*Purchased Product*), che distingue le vendite dell'ASIN
pubblicizzato da quelle degli altri ASIN.

## 3.9 Quando un ROAS alto è un cattivo segnale

Contro-intuitivo ma cruciale: **un ROAS molto sopra il target significa quasi sempre
che stai lasciando fatturato sul tavolo.**

Il rendimento della spesa pubblicitaria è **decrescente**: i primi euro comprano i clic
migliori (keyword esatte, alta intenzione, posizioni buone), quelli successivi comprano
clic via via meno qualificati.

```
ROAS
  ▲
12│●
  │ ●
 8│   ●
  │      ●
 5│         ●●
  │             ●● ●  ← zona di ottimizzazione: il ROAS marginale ≈ break-even
 3│──────────────────●──●──── break-even ROAS
  │                        ● ●
 1│                              ●
  └────────────────────────────────────────► Spesa
```

Se sei a ROAS 12x con break-even 3x, hai un enorme spazio per aumentare le offerte,
allargare le keyword, alzare i budget. Il profitto **in euro** cresce anche mentre il
ROAS scende, fino al punto in cui il ROAS *marginale* (non quello medio) tocca il
break-even.

📐 **La domanda giusta non è «qual è il mio ROAS?» ma «qual è il ROAS dell'ultimo
euro speso?»**

🛠 **Procedura — trovare il punto di ottimo**

1. Prendi una campagna con ROAS molto sopra il target e budget non esaurito.
2. Aumenta le offerte del 15–20% (non di più: eviti shock all'asta).
3. Attendi 14 giorni interi.
4. Confronta il **profitto pubblicitario in euro** (§3.4), non il ROAS.
5. Se il profitto è cresciuto, ripeti. Quando smette di crescere, sei all'ottimo:
   torna indietro di un passo.

Questo metodo — spingere finché il profitto marginale si annulla — è l'unico modo
razionale di stabilire quanto spendere.

---

⚠️ **Errori frequenti su ROAS e ACOS**

- Confrontare il proprio ROAS con quello di altri venditori o di altre categorie.
- Considerare il ROAS come "profitto" e stupirsi che il conto in banca non cresca.
- Inseguire l'ACOS più basso possibile: si ottiene facilmente spegnendo tutto tranne le
  keyword di marca, e si distrugge la crescita.
- Ignorare il TACOS e non accorgersi che l'organico si sta erodendo.
- Giudicare campagne di lancio e campagne di raccolta con lo stesso target.
- Leggere i dati degli ultimi 3 giorni come definitivi.

---

✅ **Checklist di fine capitolo**

- [ ] So convertire ACOS in ROAS e viceversa senza calcolatrice.
- [ ] Conosco il mio break-even ACOS e il mio target ACOS, per prodotto.
- [ ] Traccio il TACOS mensile per linea di prodotto.
- [ ] So distinguere ROAS dichiarato e ROAS incrementale, e so quali campagne sono a rischio.
- [ ] Aspetto almeno 7–14 giorni prima di valutare l'effetto di una modifica.
- [ ] Valuto le decisioni di scala guardando il **profitto in euro**, non il ROAS medio.

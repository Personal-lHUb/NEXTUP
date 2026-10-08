# Capitolo 1 — Introduzione alle Amazon ADS

🎯 **Obiettivo del capitolo:** capire *cosa* sono le Amazon ADS, *perché* funzionano
diversamente da ogni altra piattaforma pubblicitaria, e *quale* pezzo dell'ecosistema
serve al tuo obiettivo. Alla fine devi saper rispondere a: «di quale formato ho
bisogno, e perché proprio quello?».

---

## 1.1 Che cos'è Amazon Advertising

Amazon Advertising è la piattaforma pubblicitaria di Amazon: un sistema che permette
di comprare **visibilità a pagamento all'interno (e fuori) del marketplace**, pagando
in genere **a clic** (CPC — *cost per click*) o, in alcuni formati, **a impressioni
visualizzate** (vCPM).

Tecnicamente è un **retail media network**: una rete pubblicitaria costruita sopra un
negozio. Questo dettaglio non è terminologia, è la ragione per cui tutto il resto
funziona come funziona. Su Amazon la pubblicità vive nello stesso posto in cui avviene
la transazione, quindi la piattaforma sa con certezza — non per stima statistica —
chi ha visto l'annuncio, chi ha cliccato e chi ha comprato.

Amazon è oggi il terzo operatore pubblicitario digitale al mondo per fatturato, dopo
Google e Meta. Non è un canale accessorio: per la maggior parte dei venditori è il
**principale costo variabile di marketing**, spesso secondo solo alle commissioni.

## 1.2 Perché Amazon è diverso da Google e da Meta

Le tre grandi piattaforme si distinguono per l'**intento dell'utente** nel momento in
cui incontra l'annuncio.

| | Meta / TikTok | Google Search | Amazon |
|---|---|---|---|
| Stato mentale dell'utente | Intrattenimento | Ricerca di informazioni | **Ricerca di prodotto per comprare** |
| Intento d'acquisto | Basso / da creare | Medio / variabile | **Altissimo** |
| Distanza dall'acquisto | Molti passaggi | Qualche passaggio | **Un clic** |
| Attribuzione | Modellata, pixel, privacy | Parzialmente modellata | **Deterministica, chiusa** |
| Concorrenza per l'attenzione | Tutto il feed | Altri siti | **Solo altri prodotti** |

Tre conseguenze pratiche, da tenere sempre a mente:

1. **Non devi creare il bisogno.** Chi cerca "tappetino yoga antiscivolo" ha già
   deciso di comprare un tappetino yoga. Il tuo lavoro non è convincerlo a fare yoga:
   è convincerlo che il *tuo* tappetino è la scelta migliore fra quelli mostrati. Questo
   sposta il baricentro del lavoro dal *creative* (come su Meta) al **listing, al prezzo
   e alla scelta delle parole chiave**.

2. **Il ciclo di feedback è cortissimo.** Clic e vendita avvengono nello stesso
   ambiente, entro minuti o giorni. Puoi misurare il ritorno reale di ogni parola
   chiave, cosa che altrove richiede modelli probabilistici.

3. **Il costo è strutturale, non promozionale.** Poiché tutti i venditori hanno
   accesso agli stessi spazi e la domanda è finita, la pubblicità su Amazon tende a
   comportarsi come una **tassa sul fatturato**: il CPC sale finché il ritorno marginale
   dell'ultimo inserzionista si azzera. Chi ha margini migliori può permettersi offerte
   più alte, e vince. Questo è il motivo per cui il Modulo 1 insiste tanto sui conti
   (Capitoli 3 e 9): su Amazon non si vince "facendo advertising", si vince avendo un
   prodotto che *sopporta* l'advertising.

## 1.3 La mappa dell'ecosistema pubblicitario Amazon

Amazon non è "un" prodotto pubblicitario: è una famiglia. Ecco la mappa completa, con
il ruolo di ciascun elemento.

### Self-service (li gestisci tu, dalla console)

**Sponsored Products (SP) — Prodotti sponsorizzati**
Il formato base, quello con cui inizia il 100% dei venditori. Promuove un **singolo
prodotto** e appare nei risultati di ricerca e nelle pagine prodotto, con un aspetto
quasi identico a un risultato organico (cambia solo la dicitura *Sponsorizzato*).
Modello di costo: CPC. È il formato che genera la grande maggioranza delle vendite
pubblicitarie e il formato in cui investirai la maggior parte del budget.
Non richiede la registrazione del marchio.

**Sponsored Brands (SB) — Marchi sponsorizzati**
Il banner in alto ai risultati di ricerca con **logo, titolo personalizzato e più
prodotti**, oppure in formato **video**. Porta a una landing page: il tuo Brand Store o
una pagina di elenco prodotti. Serve a costruire riconoscibilità e a occupare lo spazio
più visibile della pagina. Richiede **Amazon Brand Registry** (marchio registrato).
Espone metriche esclusive di acquisizione (*new-to-brand*).

**Sponsored Display (SD) — Display sponsorizzati**
Annunci display che possono seguire l'utente **dentro e fuori Amazon** (siti e app
partner). Due logiche di targeting completamente diverse: **contestuale** (mostrati su
determinati prodotti/categorie) e **per pubblico** (remarketing verso chi ha visto il tuo
prodotto o prodotti simili, segmenti in-market, lifestyle, interessi). Modello di costo
CPC o vCPM. Richiede Brand Registry per la maggior parte delle funzionalità.

**Sponsored TV**
Estensione video su TV connesse, self-service, con targeting basato sui segnali di
acquisto Amazon. Disponibilità e requisiti variano per marketplace: verificane la
presenza nella tua console prima di pianificarlo.

### Gestito / avanzato

**Amazon DSP**
La piattaforma programmatica per comprare display e video su inventario Amazon e di
terze parti, anche **senza vendere su Amazon**. Storicamente riservata a budget elevati
e gestione tramite agenzia o account manager, con una versione self-service in
espansione. È il livello a cui si arriva, non quello da cui si parte.

**Amazon Marketing Cloud (AMC)**
Ambiente di analisi *clean room* che permette query su dati di evento anonimizzati e
aggregati (percorsi di conversione, overlap fra formati, incrementalità). Strumento da
account maturo.

**Amazon Attribution**
Permette di misurare il contributo del traffico **esterno** (Google, Meta, newsletter,
influencer) alle vendite su Amazon, tramite tag di tracciamento.

### Strumenti gratuiti che moltiplicano l'efficacia delle ADS

- **Brand Store**: la tua vetrina multi-pagina su Amazon. È la landing page naturale
  delle campagne Sponsored Brands.
- **A+ Content / A+ Premium**: contenuti arricchiti nella scheda prodotto. Non è
  pubblicità, ma alza il tasso di conversione — cioè abbassa l'ACOS di tutte le tue
  campagne.
- **Posts / contenuti brand**: contenuti social-like all'interno di Amazon.
- **Coupon, offerte, Prime Exclusive Discount**: incidono direttamente su CTR e CVR
  perché aggiungono un badge visibile nei risultati di ricerca.

## 1.4 Chi può fare pubblicità, e da dove

| Profilo | Console di accesso | Formati disponibili |
|---|---|---|
| **Seller** (venditore terzo, Seller Central) | Seller Central → *Pubblicità* → *Gestione campagne*, oppure `advertising.amazon.it` | SP sempre; SB e SD con Brand Registry |
| **Vendor** (fornitore, Vendor Central) | Vendor Central → *Advertising*, oppure la console Amazon Ads | SP, SB, SD, DSP |
| **Autore KDP** | Console dedicata KDP / Amazon Ads | SP e SB su libri |
| **Brand non venditore** | Amazon DSP | Display/video programmatico |

Due requisiti tecnici da conoscere subito, perché bloccano tutto il resto:

- **Buy Box** — I Prodotti sponsorizzati vengono mostrati solo se il tuo ASIN detiene
  la Buy Box (la "casella di acquisto"). Se la perdi, le campagne smettono di erogare
  anche se il budget è intatto e le offerte sono alte. È la causa numero uno delle
  "campagne che di colpo non spendono più".
- **Amazon Brand Registry** — Sblocca Sponsored Brands, la maggior parte di Sponsored
  Display, il Brand Store, l'A+ Content e le metriche di marca. Richiede un marchio
  registrato o in corso di registrazione presso un ufficio riconosciuto.

## 1.5 Il funnel su Amazon

Anche se Amazon è un ambiente ad alto intento, il funnel esiste. Mappalo così:

```
        AWARENESS            CONSIDERAZIONE           CONVERSIONE            FIDELIZZAZIONE
    (non mi conosci)     (sto valutando le opzioni)  (voglio comprare)     (ho già comprato)
 ─────────────────────────────────────────────────────────────────────────────────────────
   Sponsored Brands       SP corrispondenza ampia     SP corr. esatta       SD remarketing
   Video / Sponsored TV   SP automatica (loose)       SP su ASIN comp.        di acquisto
   Sponsored Display      SB su categorie             SB su brand proprio    Iscriviti&Risparmia
   Amazon DSP             SD contestuale              SD "difensivo" su       Email brand
                                                       proprie schede
 ─────────────────────────────────────────────────────────────────────────────────────────
   ACOS alto              ACOS medio                  ACOS basso             ACOS bassissimo
   Metrica: NTB, reach    Metrica: CTR, ricerche      Metrica: CVR, ACOS     Metrica: LTV
```

Errore classico: giudicare le campagne di awareness con il metro delle campagne di
conversione. Una campagna Sponsored Brands video con ACOS 60% può essere un ottimo
investimento se l'80% degli ordini è *new-to-brand*; una campagna esatta sul tuo stesso
marchio con ACOS 25% può essere pessima, perché sta pagando clic che avresti ottenuto
gratis.

## 1.6 Il modello di costo in una pagina

- Paghi **quando qualcuno clicca** (SP, SB, SD in modalità CPC), non quando l'annuncio
  viene mostrato.
- L'accesso allo spazio si decide con un'**asta**: chi vince mostra l'annuncio.
- L'asta è di **secondo prezzo**: il vincitore paga poco più di quanto serviva per
  battere il concorrente successivo, mai il proprio massimale pieno. Per questo il tuo
  **CPC medio è quasi sempre inferiore all'offerta impostata**.
- L'asta **non si vince solo con l'offerta**: Amazon pondera la probabilità che quel
  clic si trasformi in un acquisto. Un annuncio più rilevante può battere un'offerta più
  alta. Il meccanismo completo è nel Capitolo 14.
- Il **budget giornaliero** limita la spesa; non è un obiettivo da raggiungere.
- Le vendite vengono **attribuite** all'annuncio entro una finestra temporale dal clic
  (vedi Capitolo 3): la performance di oggi si legge davvero solo fra due settimane.

## 1.7 Cosa le ADS fanno e cosa non fanno

**Le ADS fanno:**
- Comprare visibilità immediata, indipendente dal posizionamento organico.
- Generare **velocità di vendita**, che a sua volta migliora il ranking organico
  (il circolo virtuoso descritto nel Capitolo 14).
- Produrre **dati**: quali parole chiave convertono, a che costo, per quale prodotto.
  Questo è, per un prodotto nuovo, il vero prodotto delle ADS.
- Difendere lo spazio sulle tue stesse schede da annunci concorrenti.
- Presidiare i lanci, quando non hai ancora storico di vendita.

**Le ADS non fanno:**
- Non salvano un listing scritto male, senza recensioni o con foto scadenti: pagano
  solo per far vedere più in fretta il problema.
- Non compensano un prezzo fuori mercato. Su Amazon il confronto è a un centimetro
  di distanza.
- Non creano domanda per un prodotto che nessuno cerca. Se il volume di ricerca non
  esiste, l'impression non esiste.
- Non funzionano senza stock. Un prodotto in esaurimento perde Buy Box, ranking e
  storico della campagna.
- Non sono "automatizzabili e dimenticabili": l'asta cambia ogni giorno perché cambiano
  i concorrenti.

## 1.8 Le tre domande da porti prima di aprire la console

1. **Qual è l'obiettivo?** Lancio (accetto ACOS alto per generare storico), profitto
   (ACOS sotto il break-even), difesa (proteggo le keyword di marca), liquidazione
   (svuoto lo stock, l'ACOS è quasi irrilevante). Obiettivi diversi → strutture, offerte
   e KPI diversi. Non si possono perseguire tutti contemporaneamente sulla stessa
   campagna.
2. **Il prodotto regge?** Margine, recensioni, immagini, prezzo, disponibilità
   (Capitolo 2).
3. **Quanto posso perdere per imparare?** Ogni parola chiave ha bisogno di un numero
   minimo di clic per dire qualcosa di statisticamente sensato. Il budget di
   apprendimento non è uno spreco: è il costo del dato.

---

⚠️ **Errori frequenti in fase di ingresso**

- Partire da Sponsored Brands perché "è più bello". Si parte da Sponsored Products:
  è il formato che converte e che genera i dati su cui costruire tutto il resto.
- Attivare tutti i formati insieme il primo giorno, senza sapere quale sta generando
  cosa.
- Attivare le ADS su un catalogo intero anziché sui 3–5 prodotti che possono davvero
  vincere.
- Confondere la console pubblicitaria con Seller Central: sono due ambienti collegati
  ma distinti, con report e permessi diversi.

---

✅ **Checklist di fine capitolo**

- [ ] So distinguere Sponsored Products, Brands, Display, TV e DSP e so a cosa serve ciascuno.
- [ ] So se ho o non ho il Brand Registry, e quindi quali formati posso usare.
- [ ] Ho verificato di detenere la Buy Box sugli ASIN che voglio pubblicizzare.
- [ ] Ho scritto per iscritto l'obiettivo della mia attività pubblicitaria (una frase).
- [ ] Ho capito che pago per clic e che il CPC reale sarà in genere inferiore alla mia offerta.

# Capitolo 4 — Entriamo dentro Amazon Advertising

🎯 **Obiettivo del capitolo:** entrare nella console, capire l'architettura dell'account
e sapere esattamente **a quale livello** si imposta ogni cosa. Alla fine devi saper dire,
per ogni parametro: «questo si decide a livello di campagna / gruppo / target».

---

## 4.1 Come si accede

Ci sono due porte per la stessa stanza:

**A) Da Seller Central**
`sellercentral.amazon.it` → menu **Pubblicità** → **Gestione campagne**.
Comodo se lavori già dentro Seller Central. Alcune funzionalità avanzate rimandano
comunque alla console completa.

**B) Dalla console Amazon Ads**
`advertising.amazon.it` (o `advertising.amazon.com` per gli account nordamericani).
È l'ambiente completo: report avanzati, gestione utenti, fatturazione pubblicitaria,
Brand Store, Creative Asset Library, DSP se abilitato.

🛠 **Procedura al primo accesso**

1. Accedi con le credenziali del venditore o con un utente delegato.
2. In alto a destra, verifica **quale account e quale marketplace** sono selezionati.
   È l'errore numero uno: creare una campagna su `amazon.de` credendo di essere su
   `amazon.it`.
3. Verifica **valuta** e **fuso orario** dell'account (§4.6).
4. Controlla lo stato della **fatturazione**: metodo di pagamento valido e non in
   scadenza (Capitolo 15).
5. Prima di creare qualsiasi campagna, configura le **colonne e le viste**
   (Capitolo 11).

## 4.2 L'architettura dell'account: la gerarchia

Questa è la struttura da avere in testa. Ogni livello ha poteri diversi.

```
ACCOUNT PUBBLICITARIO  (uno per marketplace / per entità di vendita)
│
├── PORTFOLIO                    ← raggruppamento + tetto di budget + date (Cap. 12)
│   │
│   ├── CAMPAGNA                 ← tipo di campagna, budget giornaliero, date,
│   │   │                          strategia di offerta, aggiustamenti per posizionamento
│   │   │
│   │   ├── GRUPPO DI ANNUNCI    ← offerta predefinita, prodotti pubblicizzati,
│   │   │   │                      insieme dei target, tema
│   │   │   │
│   │   │   ├── PRODOTTI (ASIN/SKU pubblicizzati)
│   │   │   │
│   │   │   ├── TARGET           ← keyword o prodotti/categorie, ognuno con
│   │   │   │                      la propria offerta e il proprio tipo di corrispondenza
│   │   │   │
│   │   │   └── TARGET NEGATIVI  ← keyword negative / prodotti esclusi
│   │   │
│   │   └── (altri gruppi di annunci)
│   │
│   └── (altre campagne)
│
└── (altri portfolio)
```

### Tabella dei poteri: cosa si imposta dove

| Impostazione | Portfolio | Campagna | Gruppo di annunci | Target |
|---|:---:|:---:|:---:|:---:|
| Tetto di budget aggregato | ✅ | | | |
| Date di inizio/fine del gruppo | ✅ | ✅ | | |
| Tipo di campagna (SP/SB/SD) | | ✅ | | |
| Budget giornaliero | | ✅ | | |
| Strategia di offerta (dinamiche) | | ✅ | | |
| Aggiustamenti per posizionamento | | ✅ | | |
| Targeting automatico o manuale | | ✅ | | |
| Prodotti pubblicizzati | | | ✅ | |
| Offerta predefinita | | | ✅ | |
| Keyword / target di prodotto | | | ✅ | ✅ |
| Tipo di corrispondenza | | | | ✅ |
| Offerta specifica | | | | ✅ |
| Keyword negative | | ✅ | ✅ | |
| Prodotti negativi (esclusi) | | ✅ | ✅ | |

Tre implicazioni operative che discendono direttamente da questa tabella:

1. **Il budget si controlla solo a livello di campagna** (e come tetto a livello di
   portfolio). Se vuoi proteggere un budget per una keyword specifica, quella keyword
   deve stare in una campagna a sé. Non esiste un budget per gruppo o per keyword.
2. **Gli aggiustamenti per posizionamento sono di campagna.** Se vuoi essere aggressivo
   in cima ai risultati solo su alcune keyword, quelle keyword devono stare in una
   campagna dedicata.
3. **Le keyword negative si mettono a due livelli**: campagna (blocca tutti i gruppi) e
   gruppo (blocca solo quel gruppo). Serve una strategia coerente — vedi Capitolo 7,
   §7.7.

## 4.3 Multi-marketplace e multi-account

- Ogni **marketplace** ha il proprio account pubblicitario e le proprie campagne.
  Le campagne italiane non si estendono automaticamente a Spagna o Germania: vanno
  ricreate (esistono funzioni di copia/importazione bulk, ma restano entità separate).
- Il **selettore di marketplace** in alto nella console permette di passare da uno
  all'altro senza uscire. Controllalo sempre prima di modificare qualcosa.
- Ogni marketplace ha **budget, offerte, valute, CPC e concorrenza diversi**: non
  copiare le offerte italiane in Germania senza adattarle.
- Le keyword vanno **tradotte e localizzate**, non tradotte letteralmente: le persone
  cercano con parole diverse in mercati diversi.

## 4.4 Utenti, ruoli e permessi

Se lavori con un team o con un'agenzia, non condividere mai le credenziali principali.

🛠 **Procedura**

1. Console Amazon Ads → **Impostazioni account** (icona ingranaggio o menu utente) →
   sezione **Gestione utenti / Accesso utenti**.
2. Invita l'utente con la sua email.
3. Assegna il ruolo minimo necessario. I ruoli tipici sono:
   - **Visualizzatore / Solo lettura** — vede campagne e report, non modifica.
   - **Editor / Gestore campagne** — crea e modifica campagne.
   - **Amministratore** — include gestione utenti e fatturazione.
   - **Solo reportistica / Solo fatturazione** — accessi specialistici, dove disponibili.
4. Revoca gli accessi quando una collaborazione finisce. Fallo lo stesso giorno.

⚠️ Il nome esatto dei ruoli varia per tipologia di account e nel tempo: la regola
stabile è **principio del privilegio minimo**.

## 4.5 La mappa del menu

Panoramica rapida (il dettaglio sezione per sezione è nel **Capitolo 13**):

| Sezione | A cosa serve |
|---|---|
| **Gestione campagne** | Creare, modificare, mettere in pausa campagne, gruppi, target |
| **Portfolio** | Raggruppare campagne e imporre tetti di budget (Cap. 12) |
| **Budget / Budget manager** | Vedere le campagne fuori budget, regole di budget, previsioni |
| **Report / Misurazione** | Search Term, Targeting, Placement, Prodotti acquistati, ecc. |
| **Creatività** | Libreria di loghi, immagini, video per Sponsored Brands/Display |
| **Store** | Costruire e analizzare il Brand Store |
| **Metriche del marchio / Brand metrics** | Dati di funnel a livello di marca |
| **Amazon Attribution** | Tracciare il traffico esterno verso Amazon |
| **Fatturazione** | Metodo di pagamento, importo dovuto, fatture, soglia (Cap. 15) |
| **Impostazioni account** | Utenti, preferenze, fuso orario, notifiche |
| **Cronologia modifiche** | Chi ha cambiato cosa e quando — indispensabile per il debug |

## 4.6 Impostazioni che devi verificare *prima* di spendere

1. **Fuso orario dell'account.** Determina quando finisce la "giornata" pubblicitaria e
   quando si azzera il budget giornaliero. Se non lo conosci, non puoi interpretare i
   dati orari né programmare correttamente le regole.
2. **Valuta.** Tutti gli importi (offerte, budget, spesa) sono nella valuta
   dell'account. Con account multi-mercato, non sommare valute diverse nei tuoi fogli.
3. **Metodo di pagamento e soglia di spesa** (Capitolo 15). Una carta rifiutata mette in
   pausa le campagne: perdi erogazione, storico e posizionamento.
4. **Notifiche.** Attiva quelle su budget esaurito, problemi di pagamento e
   moderazione creativa rifiutata.
5. **Colonne dei report.** Configurale prima (Capitolo 11): eviterai di prendere
   decisioni su colonne sbagliate per settimane.

## 4.7 Creare la prima campagna: il flusso, passo per passo

Percorso: **Gestione campagne → Crea campagna → Prodotti sponsorizzati**.

🛠 **Procedura commentata**

1. **Nome campagna.** Usa subito la convenzione di naming (Capitolo 7, §7.8).
   Esempio: `SP_AUTO_B08XXXX_IT_Discovery`.
2. **Portfolio.** Assegnalo ora, non dopo (Capitolo 12).
3. **Date.** Inizio oggi; fine **vuota**, salvo campagne stagionali. Una data di fine
   dimenticata è la causa più banale di "la campagna non spende più".
4. **Budget giornaliero.** Amazon può spendere fino al doppio del budget in un singolo
   giorno, compensando nei giorni successivi all'interno del mese: ragiona sul budget
   **mensile** (budget giornaliero × ~30), non sulla singola giornata.
5. **Targeting: automatico o manuale.** In fase di apertura di un nuovo prodotto: una
   campagna automatica per raccogliere dati **e** una manuale per presidiare le keyword
   che già conosci (Capitolo 7).
6. **Strategia di offerta della campagna:**
   - *Offerte dinamiche – solo al ribasso*: Amazon abbassa l'offerta quando ritiene la
     conversione improbabile. La più prudente. Default consigliato per iniziare.
   - *Offerte dinamiche – al rialzo e al ribasso*: Amazon può anche **aumentare**
     l'offerta (storicamente fino al 100% in più per le posizioni in cima alla ricerca)
     quando prevede alta probabilità di conversione. Da usare su campagne mature con
     dati solidi.
   - *Offerta fissa*: nessun aggiustamento algoritmico. Utile per test puliti di
     misurazione, perché rimuove una variabile.
7. **Aggiustamenti per posizionamento.** Percentuali di rialzo per *Inizio dei risultati
   di ricerca (prima pagina)*, *Resto della ricerca*, *Pagine prodotto*. Il moltiplicatore
   massimo è molto elevato (storicamente fino al 900%): usalo solo con dati alla mano
   dal report Posizionamento. **Parti da 0% e aggiusta dopo 2–4 settimane.**
8. **Gruppo di annunci.** Un tema per gruppo. Non mescolare prodotti diversi: i dati
   diventano illeggibili.
9. **Prodotti.** Seleziona gli ASIN/SKU. Regola pratica: **un gruppo, un prodotto**
   (o una famiglia di varianti realmente equivalenti).
10. **Offerta predefinita.** Punto di partenza ragionevole: il CPC suggerito da Amazon,
    oppure il tuo calcolo `CPC massimo = Prezzo × Margine% × CVR atteso` (vedi Cap. 9).
11. **Keyword / target** (solo campagne manuali). Con i rispettivi tipi di corrispondenza
    e offerte (Capitolo 7).
12. **Keyword negative.** Inseriscine subito quelle ovvie (termini incompatibili con il
    prodotto, marchi che non vendi, termini "gratis", "usato", ecc.).
13. **Lancia**, poi **non toccare nulla per almeno 7–14 giorni**.

⚠️ Nota sull'attivazione: dopo il salvataggio, una campagna può richiedere qualche ora
prima di iniziare a erogare. Le campagne Sponsored Brands passano inoltre per una
**revisione creativa** che può richiedere tempo e può essere rifiutata.

## 4.8 Modifiche in blocco (bulk operations)

Quando l'account cresce, gestire tutto da interfaccia diventa impraticabile.

🛠 **Procedura**

1. Menu **Operazioni in blocco / Bulk operations**.
2. Scarica il foglio di lavoro per il periodo e i tipi di campagna desiderati.
3. Modifica solo le colonne consentite (offerte, stato, budget, aggiunta di keyword),
   impostando `Operation = Update` o `Create` nella riga corrispondente.
4. Ricarica il file e **verifica il report di esito**: le righe rifiutate vengono
   segnalate con il motivo.

Regole di sopravvivenza:
- Conserva sempre una copia del file **prima** delle modifiche.
- Modifica poche cose per volta: se qualcosa va storto, devi sapere cosa.
- Non usare i bulk per "riscrivere l'account" in un colpo solo: azzeri l'apprendimento
  algoritmico e perdi la leggibilità dei dati.

## 4.9 La cronologia delle modifiche

Sezione fondamentale e sottoutilizzata: registra chi ha modificato cosa e quando
(offerte, budget, stati, keyword). È il primo posto da guardare quando una campagna
"impazzisce". Verificala sempre prima di formulare ipotesi sull'algoritmo: nove volte
su dieci la spiegazione è una modifica umana dimenticata.

---

⚠️ **Errori frequenti in console**

- Lavorare sul marketplace sbagliato.
- Impostare una data di fine e dimenticarsene.
- Mettere tutti i prodotti in un unico gruppo di annunci "per comodità".
- Alzare gli aggiustamenti di posizionamento al 300% il primo giorno, senza dati.
- Cambiare offerte ogni giorno, rendendo impossibile attribuire un effetto a una causa.
- Creare campagne senza portfolio e senza convenzione di naming.
- Non attivare le notifiche di problema di pagamento.

---

✅ **Checklist di fine capitolo**

- [ ] So accedere alla console e verificare account e marketplace attivi.
- [ ] Conosco la gerarchia Portfolio → Campagna → Gruppo → Target e so cosa si imposta a ogni livello.
- [ ] Ho verificato fuso orario, valuta e metodo di pagamento.
- [ ] Ho definito la convenzione di naming prima di creare la prima campagna.
- [ ] So dove trovare la cronologia delle modifiche.
- [ ] So scaricare e ricaricare un file di operazioni in blocco.

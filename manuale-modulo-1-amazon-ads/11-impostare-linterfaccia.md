# Capitolo 11 — Impostiamo correttamente l'interfaccia delle Amazon ADS

🎯 **Obiettivo del capitolo:** configurare la console **prima** di iniziare a lavorarci,
così da vedere i dati giusti fin dal primo giorno. Una console mal configurata non
rallenta: fa prendere decisioni sbagliate su numeri incompleti.

⚠️ Nota: nomi dei menu e posizione dei comandi cambiano nel tempo e differiscono
leggermente fra Seller Central e la console Amazon Ads. Le **logiche** di questo capitolo
sono stabili; i percorsi vanno adattati a quello che vedi.

---

## 11.1 Prima di tutto: le impostazioni di account

🛠 **Procedura**

1. **Verifica marketplace e account** nel selettore in alto. Ogni sessione, ogni volta.
2. **Fuso orario** — determina quando finisce la giornata pubblicitaria e quando si
   azzera il budget giornaliero. Se lavori da un fuso diverso, annotalo: le analisi
   orarie ne dipendono.
3. **Valuta** — tutti gli importi sono nella valuta dell'account. Con più mercati, non
   sommare valute diverse nei fogli.
4. **Notifiche** — attiva almeno: campagne fuori budget, problemi con il metodo di
   pagamento, creatività rifiutate, campagne che stanno per scadere.
5. **Utenti e permessi** — privilegio minimo per ciascuno (Cap. 4, §4.4).

---

## 11.2 Le colonne: la configurazione che cambia tutto

Le colonne predefinite della console sono poche e generiche. Devi costruirti **viste
diverse per compiti diversi**, perché guardare 30 colonne contemporaneamente equivale a
non guardarne nessuna.

🛠 **Procedura**: nella tabella delle campagne, apri il selettore **Colonne** (o
*Personalizza colonne*), seleziona le voci e salva la vista se la console lo consente.

### Vista 1 — «Controllo quotidiano» (5 minuti al giorno)

| Colonna | Perché |
|---|---|
| Stato | Individuare campagne in pausa o scadute per errore |
| Budget | Riferimento |
| % tempo in budget | La colonna più sottovalutata: rivela il fatturato che stai perdendo |
| Spesa | Controllo del ritmo |
| Vendite | Contesto |
| ACOS | Semaforo grezzo |
| Ordini | Volume reale |

### Vista 2 — «Ottimizzazione offerte» (settimanale, a livello di target)

| Colonna | Perché |
|---|---|
| Offerta | Il valore che stai per cambiare |
| CPC | Confronto con l'offerta: quanto margine d'asta hai |
| Impressioni | Base per il CTR |
| Clic | Base per la significatività |
| CTR | Rilevanza (Cap. 6) |
| CVR | Il denominatore dell'ACOS |
| Ordini | Significatività |
| ACOS | Decisione |
| Quota di impression per ricerca | Spazio ancora conquistabile |

### Vista 3 — «Analisi di marca / acquisizione» (mensile, su SB e SD)

Aggiungi: **Ordini NTB**, **Vendite NTB**, **% ordini NTB**, **Costo per ordine NTB**,
oltre alle metriche standard. Sono campagne che vanno giudicate sull'acquisizione, non
sull'ACOS.

### Vista 4 — «Diagnostica posizionamenti»

Nella scheda **Posizionamento** della campagna: impressioni, clic, CTR, spesa, vendite,
ACOS per ciascuno dei tre posizionamenti. È la base per impostare gli aggiustamenti
percentuali.

⚠️ **Regola d'oro sulle colonne:** verifica sempre l'**etichetta della finestra di
attribuzione** (es. «Vendite totali a 14 giorni»). Non confrontare mai colonne con
finestre diverse, e non mescolarle nello stesso foglio di calcolo. È l'errore di lettura
più frequente in assoluto.

---

## 11.3 Intervallo di date e confronto fra periodi

**Regole operative**

- L'intervallo predefinito ("ultimi 7 giorni" o simile) è quasi sempre **troppo corto**
  e comprende giorni con dati incompleti.
- Per decisioni ordinarie usa **14 giorni**, escludendo gli ultimi 2–3 giorni.
- Per decisioni strutturali usa **30–60 giorni**.
- Per la stagionalità confronta **anno su anno**, non mese su mese.
- Quando usi la funzione di confronto fra periodi, verifica che i due periodi abbiano lo
  **stesso numero di giorni** e la **stessa composizione di giorni della settimana**
  (weekend e infrasettimanali hanno comportamenti diversi).
- Non includere nel periodo eventi eccezionali (Prime Day, Black Friday, promozioni
  proprie) se stai valutando la performance ordinaria.

---

## 11.4 Filtri e ordinamenti utili

Costruisci questi filtri e usali come routine fissa:

| Filtro | A cosa serve |
|---|---|
| Stato = **Attive** | Nasconde il rumore delle campagne archiviate |
| **% tempo in budget < 100%** | Le campagne che si spengono durante la giornata |
| **Clic > 15 e Ordini = 0** | Candidati alla negativizzazione |
| **ACOS > target** e **Spesa > soglia** | Dove stai perdendo denaro in valore assoluto |
| **ACOS < metà del target** | Dove hai spazio per alzare offerte e budget |
| **Impressioni = 0** negli ultimi 7 giorni | Target morti: offerta troppo bassa o problema tecnico |
| Ricerca per prefisso di naming (`SP_MAN-EXACT`) | Isolare un livello della piramide |

Nota: qui si vede il valore della convenzione di naming del Capitolo 7. Con nomi
coerenti, un filtro testuale sostituisce dieci minuti di scorrimento.

---

## 11.5 Report: impostarli una volta, riceverli per sempre

🛠 **Procedura**

1. Vai in **Misurazione e reportistica → Report pubblicitari** (o *Report*).
2. Crea i report ricorrenti che seguono, in formato scaricabile, con invio programmato:

| Report | Frequenza | Periodo | Uso |
|---|---|---|---|
| **Termini di ricerca** (SP) | Settimanale | Ultimi 30 gg | Promozioni e negative (Cap. 7) |
| **Targeting** | Settimanale | Ultimi 30 gg | Gestione offerte |
| **Posizionamento** | Mensile | Ultimi 30 gg | Aggiustamenti percentuali |
| **Prodotti pubblicizzati** | Mensile | Ultimi 30 gg | Performance per ASIN |
| **Prodotti acquistati** | Mensile | Ultimi 30 gg | Separare l'effetto alone |
| **Termini di ricerca SB** | Mensile | Ultimi 30 gg | Gestione keyword di marca |
| **Sponsored Display** | Mensile | Ultimi 30 gg | Pubblici e contestuale |
| **Budget / campagne fuori budget** | Settimanale | Corrente | Recuperare fatturato perso |

3. Imposta l'invio automatico via email, se la console lo consente: ricevere il dato
   senza doverlo andare a cercare è ciò che rende la routine sostenibile.
4. Archivia i file in una cartella con nome `AAAA-MM-GG_tipo-report.csv`. Lo storico ti
   servirà per i confronti anno su anno, che la console non conserva indefinitamente.

⚠️ I report hanno **limiti di periodo massimo** e un ritardo di elaborazione. Non
aspettarti dati definitivi sulla giornata corrente.

---

## 11.6 Regole di budget e automazioni

La console offre **regole di budget** (aumenti automatici in base a performance o a
calendario) e altre automazioni.

**Quando hanno senso**
- Alzare il budget durante Prime Day o Black Friday, con date programmate.
- Aumentare automaticamente il budget di campagne che superano stabilmente una soglia di
  ROAS.
- Proteggere campagne che vanno regolarmente fuori budget.

**Quando sono pericolose**
- Su campagne nuove, senza storico: la regola amplifica il rumore.
- Su campagne con margini stretti: un aumento automatico può portare la spesa oltre il
  sostenibile senza che tu te ne accorga.
- Se ne attivi molte insieme: non saprai più quale ha causato cosa.

**Regola pratica:** al massimo una o due automazioni, solo su campagne mature, con una
verifica mensile in cronologia modifiche.

⚠️ Nota sui **suggerimenti automatici** della console (offerte consigliate, keyword
consigliate, "applica tutto"): sono ipotesi generate da un sistema il cui obiettivo
include l'aumento della spesa. Alcuni sono ottimi, altri no. Non usare mai l'applicazione
in blocco senza passare i valori attraverso il tuo CPC massimo (Cap. 9).

---

## 11.7 Il dayparting (modulazione oraria)

La console non offre nativamente un controllo orario completo delle offerte. Le opzioni
reali sono:

1. **Regole programmate**, dove disponibili, per aumentare o ridurre il budget in
   determinati giorni.
2. **Strumenti di terze parti** collegati via API.
3. **Gestione manuale** in occasione di eventi specifici.

Prima di investire in dayparting, verifica che il gioco valga la candela: scarica i dati
per ora/giorno (dove disponibili) e controlla se esistono differenze **grandi e stabili**
fra fasce. Nella maggior parte dei casi, per account piccoli e medi, ci sono
ottimizzazioni molto più redditizie da fare prima (negative, budget, posizionamenti).

---

## 11.8 Il tuo foglio di controllo esterno

La console è ottima per operare, mediocre per analizzare nel tempo. Costruisci un foglio
esterno con almeno queste colonne, aggiornato settimanalmente:

```
Settimana | Portfolio | Campagna | Spesa | Vendite ADS | Ordini | Clic | Impressioni
          | CTR | CVR | CPC | ACOS | Fatturato totale ASIN | TACOS
          | Margine % | Profitto pubblicitario € | Note sulle modifiche fatte
```

Le due colonne che nessuna console ti dà e che valgono più di tutte le altre:

- **Profitto pubblicitario €** = `Vendite ADS × Margine % − Spesa`
- **Note sulle modifiche** = cosa hai cambiato, quando e perché

Senza la seconda, fra due mesi non saprai attribuire alcun effetto ad alcuna causa. È il
singolo strumento che distingue chi impara dal proprio account da chi ripete gli stessi
tentativi.

---

## 11.9 Ordine di configurazione consigliato

Se stai partendo ora, esegui in questa sequenza:

1. Verifica account, marketplace, fuso orario, valuta.
2. Metodo di pagamento e soglia (Cap. 15).
3. Notifiche attive.
4. Utenti e permessi.
5. Convenzione di naming decisa e scritta.
6. Portfolio creati (Cap. 12).
7. Viste di colonne configurate (§11.2).
8. Report ricorrenti programmati (§11.5).
9. Foglio di controllo esterno creato (§11.8).
10. **Solo ora** crea la prima campagna.

---

⚠️ **Errori frequenti di configurazione**

- Lavorare con le colonne predefinite per mesi e accorgersi tardi di aver ignorato la
  percentuale di tempo in budget o la quota di impression.
- Confrontare colonne con finestre di attribuzione diverse.
- Analizzare periodi troppo brevi o che includono giorni incompleti.
- Attivare molte automazioni insieme.
- Applicare in blocco le offerte suggerite.
- Non conservare lo storico dei report.
- Non annotare le modifiche fatte.

---

✅ **Checklist di fine capitolo**

- [ ] Fuso orario, valuta, notifiche e permessi verificati.
- [ ] Ho creato almeno tre viste di colonne per tre compiti diversi.
- [ ] So sempre a quale finestra di attribuzione si riferisce la colonna che leggo.
- [ ] Ho programmato i report ricorrenti e li archivio con nome standard.
- [ ] Ho al massimo una o due automazioni, su campagne mature.
- [ ] Ho un foglio di controllo esterno con profitto in euro e registro delle modifiche.

# Roadmap 18 Mesi — Checklist Operative + Kill Criteria

> Versione operativa "da spuntare" della roadmap del [piano-operativo.md](piano-operativo.md). Ogni fase ha: time budget, obiettivi numerici, task spuntabili e un **KILL CRITERION** esplicito.
> Rito settimanale (domenica sera, 15 min): spunta i task, aggiorna [kpi-tracker.csv](kpi-tracker.csv), verifica se un kill criterion è scattato.

**Regola d'oro:** i kill criteria non sono opinioni né negoziabili. Se la condizione è vera, esegui la contromisura. Nessun "ancora un mese e vediamo".

---

## FASE 1 — Mesi 1–2: Validazione "pesante manuale" (NIENTE INFRASTRUTTURA)

**Time budget:** 20–25h totali su 8 settimane (~3h/sett)

**Obiettivi numerici:**

| Metrica | Target |
|---|---|
| Lista aziende target qualificate | 100 |
| Outreach/settimana (sett. 3–5) | 30 |
| Discovery call | 2–4 |
| Piloti chiusi | 1–2 a **€290 setup + €97/mese × 3 mesi** |

**Task:**
- [ ] Sett. 1–2: costruire lista 100 aziende Emilia-Romagna (serramentisti, fotovoltaico, HVAC) → criteri in `01-vendita/criteri-lista-target.md`, dati in `01-vendita/lista-target.csv`
- [ ] Sett. 1–2: adattare i 3 messaggi per verticale a tono naturale italiano → `01-vendita/messaggi-*.md`
- [ ] Sett. 3–5: 30 outreach/sett personalizzati con cadenza email D0 → WhatsApp D3 → email D10
- [ ] Ogni settimana: registrare numeri in `kpi-tracker.csv` (outreach, risposte, call)
- [ ] Sett. 6–8: chiudere 1–2 piloti a €290 una tantum + €97/mese per 3 mesi (fascia bassa per chiudere subito)
- [ ] Setup piloti 100% manuale e gratuito: Make.com Free (1.000 ops/mese) + bot Telegram + OpenAI $5 credit
- [ ] NON fare in questa fase: P.IVA, VPS/n8n, WhatsApp Business API, scenari Make complessi, multi-tenant

> ### KILL CRITERION — Mese 2
> - **100 contatti puliti e zero clienti paganti** → il problema non è il prodotto, è pitch o segmento: **cambia messaggio O segmento** (uno solo alla volta, misura ogni 50 contatti).
> - **200 contatti e ancora zero clienti** → **valuta pivot o abbandono.**

---

## FASE 2 — Mesi 3–4: Industrializzazione minima + 2°/3° cliente

**Time budget:** 35–40h totali

**Obiettivi numerici:**

| Metrica | Target |
|---|---|
| Clienti recurring a fine mese 4 | 3 |
| Prezzo nuovi clienti | Pro **€490 setup + €197/mese** |
| Migrazione 1° cliente su n8n | fatta (6–8h una tantum) |

**Task:**
- [ ] Alla chiusura del **2° cliente recurring**: aprire P.IVA regime ordinario semplificato, ATECO 62.20.10, iscrizione Gestione Separata (DIY €0 o ~€150 con commercialista)
- [ ] Attivare commercialista online (€60–100/mese) + fatturazione elettronica
- [ ] Migrare il 1° cliente da Make.com a n8n self-hosted su Hetzner CX22 (€4,51/mese) — 6–8h una tantum
- [ ] Chiudere 2° e 3° cliente a Pro €490 + €197/mese
- [ ] **Da qui in avanti vendere SOLO Pro o Premium** (stop Starter)
- [ ] Creare template: DPA art. 28 GDPR, privacy notice cliente, checklist onboarding 2h, contratto base

> ### KILL CRITERION — Mese 4
> - **Meno di 3 clienti recurring confermati al mese 4** → il pricing è sbagliato: **testa €147/mese con setup €690** (canone più basso, setup più alto).

---

## FASE 3 — Mesi 5–9: Crescita a MRR €2.000–2.800

**Time budget:** 40h/mese (10h/sett), **max 2 picchi a 17h/sett** durante onboarding nuovo cliente

**Obiettivi numerici:**

| Metrica | Target |
|---|---|
| Outreach/mese | 160 (40/sett) |
| Nuovi clienti/mese | 1,5–2 |
| Clienti totali a fine mese 9 | 10–14 |
| MRR a fine mese 9 | €2.000–2.800 |

**Task:**
- [ ] Mantenere 40 contatti freddi/sett = 160/mese, ogni settimana, senza eccezioni
- [ ] Attivare referral: dal **3° mese di servizio** di ogni cliente, chiedere attivamente — **1 mese gratuito al referente** per ogni cliente che firma
- [ ] Introdurre **Premium €890 + €347/mese dal 6° cliente** in poi (serramentisti/fotovoltaico più strutturati)
- [ ] Automatizzare il report mensile in n8n (4h una tantum) → base: `04-delivery/report-mensile-template.md`
- [ ] Monitorare churn ogni mese nel KPI tracker → applicare `04-delivery/playbook-anti-churn.md`
- [ ] Avviare quarterly review per i Premium → `04-delivery/quarterly-review-script.md`

> ### KILL CRITERION — Mese 9
> - **MRR < €1.500 con più di 6 clienti** → qualcosa non va in prezzo medio o retention: **audit completo pricing/churn** (mix Starter residui? canoni troppo bassi? churn che mangia la crescita?).

---

## FASE 4 — Mesi 10–15: Push a €5.500+/mese di fatturato

**Time budget:** 12–15h/sett (al limite del budget) — **da confermare con la famiglia PRIMA di iniziare la fase**

**Obiettivi numerici:**

| Metrica | Target |
|---|---|
| Clienti attivi a fine mese 15 | 18–22 |
| Nuovi clienti lordi nella fase | 10–14 (6–10 netti, churn fisiologico ~30%/anno) |
| Accantonamento fiscale | 35–40% di ogni incasso |

**Task:**
- [ ] Confermare con la famiglia il passaggio a 12–15h/sett per 6 mesi
- [ ] Aggiungere 6–10 clienti netti → arrivare a 18–22 attivi
- [ ] Valutare 1° micro-outsourcing: **VA italiano a €15–25/h per 8–10h/sett** su (a) lead list building, (b) follow-up email, (c) onboarding tecnico ripetitivo — costo €600–800/mese, libera ~8h/sett per chiusura e gestione clienti
- [ ] **Accantonare il 35–40% di ogni incasso** su conto fiscale separato, ad ogni bonifico ricevuto
- [ ] Standardizzare scadenze: F24, IRPEF saldo + acconto, IVA trimestrale (con il commercialista)

> ### KILL CRITERION — Sempre attivo in questa fase
> - **Più di 12h/sett sistematiche per 4+ settimane consecutive** → **alza i prezzi o taglia i clienti meno profittevoli. NON lavorare di più.** Il tetto assoluto è 17h/sett nei picchi: oltre, il piano è fuori controllo.

---

## FASE 5 — Mesi 16–18: Decisione quit / no-quit

**Time budget:** invariato. Fase di verifica, non di sprint.

**I 5 trigger di quit — devono essere veri TUTTI E CINQUE:**
- [ ] **MRR ≥ €5.500/mese stabile per 6 mesi consecutivi**
- [ ] **≥ 18 clienti attivi diversificati**, nessun cliente > 15% del fatturato
- [ ] **Churn ≤ 2%/mese**
- [ ] **Buffer di 6 mesi di stipendio OEM netto** sul conto
- [ ] **Pipeline outreach attiva con 2+ nuovi clienti previsti nei 60 giorni successivi**

**Passi post-quit (solo se i 5 trigger sono tutti veri):**
- [ ] Dimissioni in regola: preavviso completo, rapporto civile con l'OEM, zero clienti riconducibili all'OEM
- [ ] Chiudere il regime ordinario, **passare a forfettario** (ATECO 62.20.10, documentare che NON è "mera prosecuzione" dell'attività da dipendente)
- [ ] Ricalcolare il netto: a parità di fatturato **il netto sale da ~€2.500 a ~€4.500–4.800/mese** — questo è il vero moltiplicatore del quit
- [ ] Prudenza fiscale: pianificare con imposta sostitutiva al 15%; il 5% start-up (primi 5 anni) è un bonus, non un'ipotesi di piano

> Se anche UNO solo dei 5 trigger è falso → **no quit**: si resta dipendenti e si continua a costruire. Ricontrollo ogni mese.

---

## Trigger che cambiano la strategia (validi in OGNI fase)

| Trigger osservato | Azione immediata |
|---|---|
| **0 risposte da 200 outreach in 6 settimane** | Cambia segmento o messaggio |
| **Risposte ma 0 chiusure dopo 5 discovery call** | Problema prezzo/offerta: testa €147/mese |
| **Starter si chiude facile ma Pro fatica** | Manca framing del valore: aggiungi case study quantitativo |
| **Churn > 6%/mese nei primi 90 giorni di servizio** | Problema onboarding/aspettative: rifai il processo di onboarding |
| **MRR > €4.000 prima del mese 12** | Considera quit anticipato + passaggio immediato a forfettario |

- [ ] Ho riletto questa tabella all'ultimo check settimanale del mese

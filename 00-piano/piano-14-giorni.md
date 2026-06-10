# Piano 14 Giorni — Dal piano all'azione

> Primi 14 giorni della Fase 1 (vedi [roadmap-kill-criteria.md](roadmap-kill-criteria.md)). Budget totale: **~8–10 ore sulle 2 settimane**, in sessioni serali/weekend da 60–90 min.
> Regole fisse: mai su orario, dispositivi, email o rete OEM; mai contatti acquisiti tramite l'OEM.

---

## Giorni 1–3 — Lista 100 aziende target (3h)

Guida completa: `01-vendita/criteri-lista-target.md`. File di lavoro: `01-vendita/lista-target.csv`.

- [ ] Sessione 1 (90 min): ricerca Google Maps su Bologna, Modena, Reggio Emilia, Parma con le query del file criteri (serramentisti, fotovoltaico, HVAC) → ~150–180 nomi grezzi
- [ ] Sessione 2 (90 min): qualifica con i 4 controlli (form funzionante sul sito + Google Ads attive + 3–15 dipendenti stimati + sito non abbandonato) → scremare a 100
- [ ] Compilare `lista-target.csv`: nome, città, verticale, sito, telefono, titolare se trovato, Ads Sì/No
- [ ] Check di uscita: **100 aziende in lista, di cui ~80 con contatto valido**

## Giorno 4 — Rifinire i 3 messaggi per verticale (1h)

- [ ] Rivedere `01-vendita/messaggi-serramentisti.md` (già pronto): leggere ad alta voce, togliere ogni parola che suona "da consulente"
- [ ] Derivare le versioni per fotovoltaico e HVAC (stessa struttura: email D0, WhatsApp D3, email D10) → salvarle come `01-vendita/messaggi-fotovoltaico.md` e `01-vendita/messaggi-hvac.md`
- [ ] Verifica finale su ogni messaggio: max 4 righe, zero "automazione/AI" nel primo contatto, prima riga sempre personalizzata

## Giorno 5 — Aprire gli account gratuiti (1h)

- [ ] **Make.com Free** (1.000 ops/mese) — servirà per il setup manuale del 1° pilota
- [ ] **OpenAI API** ($5 credit) — impostare subito **hard budget** nella dashboard billing (es. $10/mese) come safety
- [ ] **Telegram BotFather** — creare un bot di test e annotare il token
- [ ] **Hunter.io free** (50 ricerche/mese) — per trovare l'email del titolare

**NON aprire ora (esplicitamente vietato in questa fase):**
- P.IVA
- VPS / n8n self-hosted
- Meta WhatsApp Business Cloud API

## Giorni 6–7 — Schema prestazione occasionale + tracker fiscale (0,5h)

- [ ] Rivedere lo schema ricevuta in `02-legale-fiscale/ricevuta-prestazione-occasionale.md` (marca da bollo €2 sopra €77,47; ritenuta d'acconto 20% se il committente ha P.IVA)
- [ ] Predisporre un foglio di tracciamento incassi occasionali (data, committente, lordo, ritenuta, netto, cumulato annuo) per monitorare la soglia previdenziale dei €5.000/anno
- [ ] Promemoria scritto in cima al foglio: **prestazione occasionale = solo 1° cliente (al massimo 2°); con 2 canoni mensili attivi l'attività è abituale → P.IVA**

## Giorni 8–12 — Primi 30 outreach personalizzati (3h)

- [ ] 6–8 email al giorno (mai più di 30/giorno: deliverability), partendo dalle aziende con Google Ads attive
- [ ] Personalizzazione minima obbligatoria: nome titolare + un dettaglio vero visto sul sito + messaggio del verticale giusto
- [ ] Annotare per ogni invio: data, azienda, variante oggetto usata
- [ ] A fine settimana: compilare la riga in [kpi-tracker.csv](kpi-tracker.csv) (outreach inviati, risposte, reply rate, ore)

## Giorni 13–14 — Follow-up D3 + demo Loom (1,5h)

- [ ] Inviare follow-up **WhatsApp D3** ai contatti dei giorni 8–10 con numero pubblico (testo nei file messaggi: breve, tono umano, niente link)
- [ ] Preparare lo script della demo da 90 secondi → `01-vendita/demo-loom-script.md` ("lead compila il form → in 60 secondi il titolare riceve nome+telefono+tipo lavoro su Telegram + il cliente riceve risposta personalizzata")
- [ ] Registrare la demo con Loom (gratis) e tenere il link pronto da allegare ai follow-up email D10

---

## Dalla settimana 3 in poi — target di regime

- [ ] **30 outreach/settimana** con cadenza completa D0 email → D3 WhatsApp → D10 email
- [ ] **2 discovery call fissate entro il giorno 30**
- [ ] Ogni domenica sera (15 min): aggiornare `kpi-tracker.csv` + verificare i kill criteria in `roadmap-kill-criteria.md`

**Riepilogo ore:** 3 + 1 + 1 + 0,5 + 3 + 1,5 = **10h massime sulle 2 settimane** (8h se la lista corre veloce).

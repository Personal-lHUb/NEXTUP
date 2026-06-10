# NEXTUP — Sistema Risposta Rapida Lead

Kit operativo completo per lanciare il servizio **Sistema Risposta Rapida Lead**: risposta automatica in <60 secondi alle richieste che arrivano dal form del sito di artigiani e PMI (serramentisti, fotovoltaico, HVAC) in Emilia-Romagna, con notifica immediata al titolare su Telegram/WhatsApp.

**Obiettivo**: €2.500 netti/mese in 12–18 mesi a ~10 h/settimana, con modello in abbonamento (~20–25 clienti ricorrenti a prezzo medio €230–280/mese).

## Da dove iniziare

1. Leggi il piano: [`00-piano/piano-operativo.md`](00-piano/piano-operativo.md)
2. Esegui i primi passi: [`00-piano/piano-14-giorni.md`](00-piano/piano-14-giorni.md)
3. Segui la roadmap con i kill criteria: [`00-piano/roadmap-kill-criteria.md`](00-piano/roadmap-kill-criteria.md)
4. Traccia tutto ogni settimana: [`00-piano/kpi-tracker.csv`](00-piano/kpi-tracker.csv)

## Struttura del repo

### `00-piano/` — Strategia e controllo
| File | Contenuto |
|---|---|
| `piano-operativo.md` | Il piano strategico completo (fisco, mercato, stack, pricing, roadmap) — fonte di verità |
| `roadmap-kill-criteria.md` | Roadmap 18 mesi in checklist con kill criteria e trigger di cambio strategia |
| `piano-14-giorni.md` | I prossimi 14 giorni, task per task, con ore stimate |
| `kpi-tracker.csv` | Tracker settimanale: outreach, risposte, call, clienti, MRR, churn, ore |

### `01-vendita/` — Outreach e chiusura
| File | Contenuto |
|---|---|
| `criteri-lista-target.md` | Come costruire la lista 100 aziende in 3h (Google Maps, qualifica, email titolare) |
| `lista-target.csv` | Template CSV della lista prospect |
| `messaggi-serramentisti.md` | Email D0 + WhatsApp D3 + email D10 per serramentisti |
| `messaggi-fotovoltaico.md` | Idem per installatori fotovoltaico |
| `messaggi-hvac.md` | Idem per idraulici/termoidraulica/clima |
| `cadenza-follow-up.md` | Sequenza D0/D3/D10, regole deliverability, stati di tracking |
| `script-discovery-call.md` | Script call 15–20 min con domande di qualifica e chiusura pilota |
| `obiezioni-risposte.md` | Le obiezioni reali e le risposte pronte |
| `demo-loom-script.md` | Script del video dimostrativo da 90 secondi |
| `pricing-one-pager.md` | Pagina prezzi presentabile al cliente (Starter/Pro/Premium) |

### `02-legale-fiscale/` — Contratti, GDPR, fisco
| File | Contenuto |
|---|---|
| `ricevuta-prestazione-occasionale.md` | Template ricevuta fase 1 (1° cliente, ante P.IVA) |
| `contratto-pilota.md` | Contratto pilota €290 + €97/mese × 3 mesi |
| `contratto-servizio.md` | Contratto Pro/Premium con rinnovo mensile |
| `dpa-art28-gdpr.md` | Accordo trattamento dati ex art. 28 GDPR con sub-responsabili |
| `privacy-snippet-form.md` | Le 3 righe da far incollare nella privacy del form del cliente |
| `checklist-apertura-piva.md` | Quando e come aprire P.IVA (ordinario semplificato, ATECO 62.20.10) |
| `regole-compatibilita-lavoro-dipendente.md` | Le 3 regole art. 2105 c.c. + registro di compatibilità |
| `tracker-fiscale.csv` | Tracker incassi/ritenute/regime |

### `03-tecnologia/` — Stack e delivery tecnica
| File | Contenuto |
|---|---|
| `architettura.md` | Architettura a 2 fasi (Make.com Free → n8n self-hosted) e costi per cliente |
| `fase1-setup-validazione.md` | Setup primo cliente su Make.com Free, passo-passo |
| `runbook-n8n-hetzner.md` | VPS Hetzner CX22 + Docker + n8n + backup + hardening |
| `n8n/lead-response-v1.json` | Workflow template importabile "Lead Response v1" |
| `n8n/README.md` | Come importare e duplicare il template per ogni cliente |
| `prompts/estrazione-lead.md` | Prompt estrazione dati lead → JSON (con anti prompt-injection) |
| `prompts/risposta-cliente.md` | Prompt bozza risposta al lead, 3 varianti per mestiere |
| `telegram-setup.md` | Bot Telegram per le notifiche al titolare |
| `whatsapp-cloud-api.md` | WhatsApp Cloud API Meta (solo fase 2+, su richiesta del cliente) |
| `checklist-onboarding-cliente.md` | Onboarding nuovo cliente in 2 ore reali |
| `report-mensile-spec.md` | Specifica del report PDF mensile automatico |

### `04-delivery/` — Retention e gestione clienti
| File | Contenuto |
|---|---|
| `report-mensile-template.md` | Template del report mensile per il cliente |
| `playbook-anti-churn.md` | Le 6 leve anti-churn + segnali di rischio e contromosse |
| `quarterly-review-script.md` | Script call trimestrale 15 min per i Premium |
| `checklist-cessazione-cliente.md` | Offboarding pulito (export, cancellazione dati, feedback) |

## Regole d'oro (dal piano)

1. **Validare prima di costruire**: niente infrastruttura prima del 3° cliente ricorrente.
2. **Mai "automazione/AI"** nei messaggi ai prospect: si chiama sempre "Sistema Risposta Rapida Lead".
3. **Solo MRR**: dal 3° cliente si vendono solo i pacchetti Pro (€490 + €197/mese) e Premium (€890 + €347/mese).
4. **Le 3 regole di compatibilità col lavoro dipendente** (art. 2105 c.c.): mai clienti collegati all'OEM, mai mezzi/orari aziendali, mai contatti acquisiti tramite l'OEM.
5. **Accantonare il 35–40% di ogni incasso** su conto separato per imposte e contributi.
6. **Rispettare i kill criteria**: sono scritti per proteggere tempo e famiglia, non per scoraggiare.

## Nota

- `nexus-pwa.zip`: archivio PWA preesistente nel repo, non collegato a questo kit.
- I template legali/fiscali sono bozze di lavoro: far revisionare a commercialista/avvocato prima dell'uso con clienti reali.

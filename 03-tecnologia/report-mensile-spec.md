# Spec — Report mensile automatico (build una tantum ~4h, vale per tutti i clienti)

Il report mensile è la leva anti-churn n. 1 (vedi `04-delivery/playbook-anti-churn.md`): il titolare vede il valore in numeri, ogni mese, senza chiedere nulla. Template del contenuto: `04-delivery/report-mensile-template.md`.

## Prerequisito: log dei lead

Aggiungere al workflow di ogni cliente un nodo **Google Sheets → Append row** (o tabella Postgres condivisa) dopo "3. Prepara campi":

| Colonna | Fonte |
|---|---|
| timestamp | `$json.ora` |
| cliente | nome workflow |
| tipo_lavoro | estrazione |
| urgenza | estrazione |
| risposto_entro_5min | sempre `SI` se l'esecuzione va a buon fine (<60s by design) |
| followup_inviato | `SI/NO` (solo Pro con sollecito 1h) |

⚠️ GDPR: nel log **niente dati personali del lead** (no nome/telefono/email) — bastano i contatori. Così la retention del log non è vincolata ai 30 giorni del DPA e il report non tratta dati personali.

## Workflow "Report Mensile" (uno solo per tutti i clienti)

```
[Schedule: 1° del mese, 07:00]
   → [Leggi registro clienti attivi]
   → [Loop per cliente]
        → [Query log del mese (filtro cliente + mese precedente)]
        → [Code: calcolo metriche]
        → [Genera HTML da template]
        → [HTML → PDF]
        → [Email al cliente con PDF allegato + 3 righe di commento]
        → [Notifica Telegram a TE: "report inviato a X: N lead, +Y%"]
```

## Metriche calcolate (nodo Code)

- **Richieste ricevute** nel mese
- **% risposte entro 5 minuti** (target 100% — è il numero che vende il rinnovo)
- **Solleciti/follow-up inviati** (solo Pro+)
- **Confronto mese precedente**: Δ richieste (↑↓), ripartizione per tipo_lavoro
- **Fascia oraria con più richieste** (argomento di conversazione per la quarterly review: "il 40% arriva dopo le 18, quando eravate chiusi")

## Conversione HTML → PDF

Opzione consigliata: **Gotenberg** in container sullo stesso VPS (aggiungere al docker-compose):

```yaml
  gotenberg:
    image: gotenberg/gotenberg:8
    restart: unless-stopped
```

Dal workflow: HTTP Request `POST http://gotenberg:3000/forms/chromium/convert/html` con l'HTML come file. Alternativa senza container: API esterna (PDFShift e simili) — ma aggiunge un sub-fornitore, preferire Gotenberg (resta tutto sul VPS, in UE).

## Layout PDF (1 pagina, mockup)

```
┌──────────────────────────────────────────────┐
│  [LOGO/NOME TUO SERVIZIO]                    │
│  Report mensile — [AZIENDA] — [MESE ANNO]    │
├──────────────────────────────────────────────┤
│   34              100%            12         │
│   richieste       risposte        solleciti  │
│   ricevute        entro 5 min     inviati    │
├──────────────────────────────────────────────┤
│  vs mese scorso:  richieste +13% ↑           │
│  tipo lavoro:  infissi 18 · porte 9 · altro 7│
│  fascia di punta: 18–21 (38% delle richieste)│
├──────────────────────────────────────────────┤
│  Commento: [3 righe scritte da te o          │
│  generate e riviste prima dell'invio]        │
│  Prossimo passo suggerito: [1 riga]          │
├──────────────────────────────────────────────┤
│  Sistema Risposta Rapida Lead — [TUO NOME]   │
└──────────────────────────────────────────────┘
```

## Tempi di build

| Attività | Ore |
|---|---|
| Nodo log su tutti i workflow esistenti | 1h |
| Workflow report (schedule, loop, metriche) | 1,5h |
| Template HTML + Gotenberg | 1h |
| Test su 2 clienti reali | 0,5h |
| **Totale** | **~4h una tantum** |

Quando attivarlo (dal piano): mesi 5–9, dopo il 3°–4° cliente. Prima, il report si fa a mano in 15 min/cliente/mese col template di `04-delivery/report-mensile-template.md`.

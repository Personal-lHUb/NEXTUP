# Fase 1 — Setup del primo cliente su Make.com Free (zero infrastruttura)

Obiettivo: attivare il pilota (€290 + €97/mese) in un pomeriggio, senza VPS, senza n8n, senza WhatsApp API. Limite del piano Free: 1.000 operazioni/mese ≈ **150–200 lead** con uno scenario da 5 moduli — più che sufficiente per un artigiano.

## Prerequisiti (15 min)

- [ ] Account Make.com Free
- [ ] Account OpenAI con API key e **hard budget $10/mese** impostato (Settings → Limits)
- [ ] Bot Telegram creato e chat_id del titolare recuperato → vedi [`telegram-setup.md`](telegram-setup.md)
- [ ] Accesso al form del sito del cliente (o 10 minuti col suo webmaster)

## Lo scenario in Make (6 moduli)

```
[1 Webhook] → [2 HTTP OpenAI] → [3 JSON Parse] → [4 Telegram] → [5 Email] → [6 Webhook Response]
```

### 1. Custom Webhook
- Add module → Webhooks → **Custom webhook** → Add → nome `lead-[CLIENTE]`
- Copia l'URL generato: è quello da incollare nel form del cliente
- Manda un submit di prova dal form per far riconoscere a Make la struttura dei dati ("Successfully determined")

### 2. HTTP — Make a request (chiamata OpenAI)
- URL: `https://api.openai.com/v1/chat/completions` — Method: `POST`
- Headers: `Authorization: Bearer [OPENAI_API_KEY]`, `Content-Type: application/json`
- Body type: Raw / JSON:

```json
{
  "model": "gpt-4o-mini",
  "response_format": { "type": "json_object" },
  "temperature": 0.2,
  "messages": [
    { "role": "system", "content": "[INCOLLA QUI IL PROMPT DI prompts/estrazione-lead.md]" },
    { "role": "user", "content": "{{stringa con i campi del form mappati dal webhook}}" }
  ]
}
```

- Parse response: **No** (lo fa il modulo dopo)
- ⚠️ **Mai usare i moduli "AI" nativi di Make**: consumano crediti multipli. La chiamata HTTP = 1 credito.

### 3. JSON — Parse JSON
- Input: `choices[0].message.content` dall'output del modulo HTTP
- Genera la struttura dati con un run di prova: otterrai `nome`, `telefono`, `email`, `tipo_lavoro`, `urgenza`, `riassunto`

### 4. Telegram Bot — Send a Text Message
- Connection: token del bot — Chat ID: quello del titolare
- Testo (formato consigliato in [`telegram-setup.md`](telegram-setup.md)): nome, telefono, tipo lavoro, urgenza, riassunto, orario

### 5. Email — Send an Email (risposta al lead)
- Connessione: SMTP della casella del cliente (preferito: il lead riceve da `info@clientesito.it`) o Gmail dedicata
- To: `{{email}}` dal JSON Parse — Subject: "Abbiamo ricevuto la sua richiesta — [NOME AZIENDA CLIENTE]"
- Body: bozza generata col prompt di [`prompts/risposta-cliente.md`](prompts/risposta-cliente.md) oppure, per il pilota, un template fisso con 2 variabili (più prevedibile e a costo zero di token)

### 6. Webhook Response
- Status 200, body `{"ok": true}` — alcuni form (Elementor) mostrano errore all'utente senza risposta

## Collegare il form del cliente

| Form | Come |
|---|---|
| **Elementor Pro** | Modifica form → Actions After Submit → aggiungi **Webhook** → incolla URL Make |
| **Contact Form 7** | Plugin gratuito "CF7 to Webhook" → impostazioni del form → incolla URL |
| **Gravity Forms** | Add-on ufficiale **Webhooks** → Feed sul form → incolla URL |
| **WPForms** | Webhooks addon (licenza Elite) oppure plugin "WP Webhooks" |

## Test end-to-end (10 min, da fare col cliente in call)

1. Compila il form dal sito reale con dati finti riconoscibili ("Mario Prova")
2. Verifica: notifica Telegram arrivata in <60s al titolare
3. Verifica: email di risposta ricevuta all'indirizzo del lead finto
4. Controlla su Make lo storico esecuzione (tutti i moduli verdi)
5. Elimina il lead di prova dal log

## Quando passare oltre

- **>200 lead/mese o 2° cliente attivo** → Make Core $9/mese (10.000 crediti) regge fino a ~8–10 clienti
- **3° cliente ricorrente firmato** → migra tutto su n8n self-hosted → [`runbook-n8n-hetzner.md`](runbook-n8n-hetzner.md)

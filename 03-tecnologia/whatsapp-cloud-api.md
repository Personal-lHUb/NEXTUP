# WhatsApp Business Cloud API (Meta diretto) — solo Fase 2+

> ⚠️ **NON attivare per i primi 2–3 clienti.** La complessità di onboarding (verifica business, numero dedicato, approvazione template) uccide il margine sui clienti piccoli. **Telegram resta il default**: gratis e attivo in 10 minuti. WhatsApp si aggiunge solo quando il cliente lo chiede esplicitamente ed è su pacchetto Pro/Premium.

## Perché Meta diretto e non Twilio/BSP

Andare diretti su Meta Cloud API evita il markup del BSP: paghi solo i rate Meta per conversazione/template. Twilio aggiunge il proprio costo per messaggio.

## Requisiti

- **Meta Business Manager verificato** (business.facebook.com) — la verifica richiede documenti aziendali del cliente: visura/P.IVA, sito; tempi 1–5 giorni
- **Numero di telefono dedicato** non già registrato su WhatsApp/WhatsApp Business app (una SIM nuova o un numero VoIP va bene; il numero esistente del cliente NON si può riusare senza migrarlo)
- App su **developers.facebook.com** (tipo Business)

## Setup (ordine operativo)

1. developers.facebook.com → Create App → tipo **Business**
2. Add product → **WhatsApp** → collega il Business Manager del cliente
3. Registra il numero dedicato (verifica via SMS/chiamata)
4. Crea **2–3 template di messaggio** e invia per approvazione (**attesa 24–48h**):
   - `nuova_richiesta` (Utility): notifica al titolare con variabili nome/telefono/tipo lavoro
   - `conferma_ricezione` (Utility): conferma al lead che la richiesta è presa in carico
   - eventuale `promemoria_appuntamento` (Utility)
5. Genera il **token permanente** (System User in Business Manager, non il token temporaneo da 24h)
6. Webhook di ricezione (facoltativo, serve solo se si gestiscono anche le risposte in entrata)

## Costi Italia (rate card Meta — aggiornamento aprile 2026)

| Categoria | Costo/messaggio |
|---|---|
| Utility | **$0,0345** |
| Authentication | $0,0345 |
| Marketing | $0,07947 |
| Service (risposta entro la finestra di 24h aperta dal cliente) | **gratis** |

> I rate **fluttuano** (ad agosto 2025 SendApp pubblicava €0,0248 utility / €0,0572 marketing per l'Italia; il quadro aprile 2026 li ha alzati). **Verificare la rate card Meta corrente prima di fare pricing su volumi**: developers.facebook.com/docs/whatsapp/pricing

**Costo realistico per cliente artigiano**: 50–200 notifiche/mese = **€2–10/mese** — dentro il margine del pacchetto Pro (€197).

## Integrazione nel workflow n8n

Chiamata HTTP dal workflow (dopo il nodo "3. Prepara campi", in parallelo o al posto di Telegram):

```
POST https://graph.facebook.com/v[XX]/[PHONE_NUMBER_ID]/messages
Authorization: Bearer [TOKEN_PERMANENTE]
Content-Type: application/json

{
  "messaging_product": "whatsapp",
  "to": "39[NUMERO_TITOLARE]",
  "type": "template",
  "template": {
    "name": "nuova_richiesta",
    "language": { "code": "it" },
    "components": [{
      "type": "body",
      "parameters": [
        { "type": "text", "text": "{{nome}}" },
        { "type": "text", "text": "{{telefono}}" },
        { "type": "text", "text": "{{tipo_lavoro}}" }
      ]
    }]
  }
}
```

Nota GDPR: Meta Platforms Ireland è già previsto come sub-responsabile nel DPA (`02-legale-fiscale/dpa-art28-gdpr.md`) — attivarlo non richiede modifiche contrattuali, solo coerenza con l'elenco comunicato al cliente.

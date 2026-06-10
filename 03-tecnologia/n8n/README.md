# Template n8n — Lead Response v1

`lead-response-v1.json` è lo scaffold del workflow da duplicare per ogni cliente: Webhook → estrazione GPT-4o-mini → notifica Telegram al titolare → email di risposta al lead → risposta 200 al form.

> ⚠️ **È uno scaffold, non un prodotto finito**: le versioni dei nodi n8n evolvono. Al primo import verifica ogni nodo (si aprono senza errori? i campi sono popolati?) e fai sempre il test end-to-end prima di attivare.

## Prima dell'import: credenziali da creare in n8n

| Credenziale | Tipo n8n | Note |
|---|---|---|
| OpenAI | **Header Auth** (name: `Authorization`, value: `Bearer sk-...`) | una sola per tutti i clienti, hard budget $10/mese |
| Telegram | **Telegram API** (token del bot) | una per cliente (bot dedicato) |
| SMTP | **SMTP** (host, porta, user, password della casella del cliente) | una per cliente |

## Import

1. n8n → **Workflows → ⋯ → Import from File** → seleziona `lead-response-v1.json`
2. Apri i nodi 2, 4, 5 e seleziona le credenziali appena create
3. Sostituisci i placeholder (vedi Sticky Note nel canvas): path webhook, variabili del prompt (NOME_AZIENDA, MESTIERE, CITTA, categorie), CHAT_ID_TITOLARE, mittente/testo email
4. **Save** → esegui un test con `curl`:

```bash
curl -X POST "https://n8n.[TUODOMINIO.IT]/webhook-test/lead-CLIENTE" \
  -H "Content-Type: application/json" \
  -d '{"nome":"Mario Prova","telefono":"333 0000000","email":"tua-email-di-test@example.com","messaggio":"Vorrei un preventivo per 4 finestre, possibilmente entro il mese"}'
```

5. Verifica: notifica Telegram arrivata + email ricevuta + esecuzione verde in n8n
6. **Activate** → l'URL di produzione diventa `/webhook/lead-CLIENTE` (senza `-test`)

## Duplicazione per nuovo cliente (la procedura "2 ore")

1. Workflow template → **⋯ → Duplicate** → rinomina `Lead Response - [CLIENTE]`
2. Cambia le 6–8 variabili elencate nella Sticky Note
3. Crea/collega le credenziali del cliente (Telegram + SMTP)
4. Test end-to-end → attiva → consegna l'URL webhook da incollare nel form
5. Segui la checklist completa: [`../checklist-onboarding-cliente.md`](../checklist-onboarding-cliente.md)

## Note di design

- I nodi Telegram ed Email hanno `continueOnFail`: se un canale fallisce, il form riceve comunque 200 e l'esecuzione resta tracciata in rosso nel log di n8n (controllo quotidiano da 2 minuti)
- Il payload del form viene passato a OpenAI con `JSON.stringify` doppio: il contenuto del form resta un dato, mai codice/istruzioni (anti prompt-injection, vedi `../prompts/estrazione-lead.md`)
- Estensioni Pro (da aggiungere come nodi extra quando servono): IF su fascia oraria per le notifiche, sollecito al titolare dopo 1h senza gestione (nodo Wait + secondo messaggio Telegram), append su Google Sheet per il log con retention 30 giorni e per il report mensile (`../report-mensile-spec.md`)

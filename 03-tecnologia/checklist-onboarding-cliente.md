# Checklist onboarding nuovo cliente — 2 ore reali

Target dal piano: 60–90 min di build in autonomia + 20 min di call col cliente + 10 min post. Da seguire identica per ogni cliente: la ripetibilità è il margine.

## Parte A — Build in autonomia (60–90 min)

- [ ] Duplica il workflow template → rinomina `Lead Response - [CLIENTE]` (vedi [`n8n/README.md`](n8n/README.md))
- [ ] Cambia le variabili (6–8):
  - [ ] Path webhook `lead-[cliente]` (univoco)
  - [ ] Prompt estrazione: NOME_AZIENDA, MESTIERE, CITTÀ + categorie tipo_lavoro del mestiere
  - [ ] Prompt/testo risposta: referente, domanda per mestiere, firma con telefono e sito
  - [ ] Chat ID Telegram del titolare
  - [ ] Mittente e credenziale SMTP (casella del cliente)
  - [ ] Orario notifiche se richiesto (nodo IF fascia oraria)
  - [ ] (Pro+) numero WhatsApp se pattuito → [`whatsapp-cloud-api.md`](whatsapp-cloud-api.md)
- [ ] Crea bot Telegram dedicato → [`telegram-setup.md`](telegram-setup.md) (token nel password manager)
- [ ] Credenziali separate per il cliente in n8n (mai riusare quelle di altri clienti)
- [ ] Verifica hard budget OpenAI ($10/mese) ancora attivo
- [ ] Test end-to-end con lead finto via curl: Telegram ✓ email ✓ esecuzione verde ✓
- [ ] Aggiungi riga al registro clienti (cliente, path webhook, bot, SMTP, pacchetto, data attivazione)
- [ ] Prepara i 2 documenti da consegnare: snippet privacy + istruzioni form

## Parte B — Call col cliente (20 min)

- [ ] **Min 0–5**: il titolare installa Telegram (se non l'ha), cerca il bot, preme Avvia; recuperi il chat_id e lo inserisci nel workflow al volo
- [ ] **Min 5–12**: collegamento del form (condivisione schermo col cliente o suo webmaster):
  - Elementor Pro: form → Actions After Submit → Webhook → incolla URL
  - Contact Form 7: plugin "CF7 to Webhook" → incolla URL
  - Gravity Forms: add-on Webhooks → Feed → incolla URL
- [ ] **Min 12–16**: test dal vivo — il CLIENTE compila il form dal suo sito col proprio telefono; vede arrivare la notifica Telegram e l'email di risposta (questo è il momento "wow", non saltarlo)
- [ ] **Min 16–20**:
  - [ ] Consegna snippet privacy da far incollare nell'informativa → [`../02-legale-fiscale/privacy-snippet-form.md`](../02-legale-fiscale/privacy-snippet-form.md)
  - [ ] Spiega il report mensile che riceverà (1 pagina, i suoi numeri)
  - [ ] Registra tono di voce e preferenze di risposta emerse (asset anti-churn)
  - [ ] Fissa il check a 7 giorni (10 min telefonici)

## Parte C — Post-onboarding (10 min)

- [ ] Dopo 24h: controlla le prime esecuzioni reali nel log n8n (tutte verdi? estrazione corretta?)
- [ ] Elimina i lead di prova dal log
- [ ] Messaggio di cortesia al cliente: "Primi [N] contatti gestiti correttamente, tutto attivo. Ci sentiamo [DATA] per il check."
- [ ] Promemoria in calendario: check 7 giorni + primo report mensile

## Errori che costano churn (da evitare)

- Andare live senza il test fatto DAL cliente col suo telefono
- Dimenticare lo snippet privacy (emerge dopo, e mina la fiducia)
- Promettere personalizzazioni extra in call senza prezzarle (scope creep dal giorno 1)
- Non fissare il check a 7 giorni: i primi dubbi del cliente devono cadere su di te, non sul passaparola

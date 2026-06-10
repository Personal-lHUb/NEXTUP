# Setup bot Telegram per le notifiche al titolare

Telegram è il canale di default: gratis, illimitato, notifica in 2 secondi. Tempo di setup: 10 minuti.

## 1. Creare il bot (una volta per cliente)

1. Apri Telegram → cerca **@BotFather** → `/newbot`
2. Nome visualizzato: `Richieste [NOME AZIENDA CLIENTE]` (è quello che il titolare vede in alto)
3. Username: `richieste_[cliente]_bot` (deve finire in `bot`)
4. BotFather risponde con il **token** (`123456:ABC-DEF...`): salvalo nel password manager, è una credenziale
5. Facoltativo: `/setuserpic` con il logo del cliente (percezione di servizio su misura)

> Nei primi piloti va bene anche **1 bot unico** con chat separate per cliente; dal 3° cliente in poi, 1 bot per cliente (isolamento credenziali e branding).

## 2. Recuperare il chat_id del titolare

1. Il titolare cerca lo username del bot su Telegram e preme **Avvia** (`/start`) — senza questo passaggio il bot non può scrivergli
2. Apri nel browser: `https://api.telegram.org/bot[TOKEN]/getUpdates`
3. Nel JSON cerca `"chat":{"id":123456789,...}` → quel numero è il **chat_id**
4. Alternativa più semplice da fare in call: il titolare scrive a **@userinfobot** che gli risponde con il suo id

Per notificare **più persone** (titolare + ufficio): crea un gruppo, aggiungi il bot, usa il chat_id del gruppo (negativo, es. `-100123...`).

## 3. Formato del messaggio di notifica

```
🔔 NUOVA RICHIESTA DAL SITO

👤 {nome}
📞 {telefono}
✉️ {email}
🔧 Lavoro: {tipo_lavoro}
⚡ Urgenza: {🔴🔴🔴🔴🔴 se 5 … 🟢 se 1}
📝 {riassunto}

🕐 Ricevuta: {data ora}
✅ Risposta automatica già inviata al cliente
```

Note pratiche:
- Il numero di telefono in chiaro è cliccabile da Telegram mobile → il titolare richiama con un tap (è il gesto che vende il servizio)
- L'ultima riga ("risposta già inviata") è quella che toglie l'ansia al titolare: il cliente non sta aspettando a vuoto
- Test sempre con un lead finto prima di andare live

## 4. Verifica rapida via curl (debug)

```bash
curl -s -X POST "https://api.telegram.org/bot[TOKEN]/sendMessage" \
  -d chat_id=[CHAT_ID] -d text="Test notifica Sistema Risposta Rapida Lead"
```

Se arriva, il canale è pronto: il resto lo fa il workflow.

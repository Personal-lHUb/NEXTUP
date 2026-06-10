# Cadenza Follow-up — Sequenza Operativa

> Documento interno. Una sola sequenza, sempre uguale: D0 email → D3 WhatsApp → D10 email. Poi stop.

## La sequenza

| Giorno | Canale | Messaggio | Condizione |
|---|---|---|---|
| **D0** | Email | Email primo contatto (file messaggi del verticale) | Sempre |
| **D3** | WhatsApp | Follow-up 2 righe colloquiale | Solo se il numero di cellulare è pubblico (sito/Google Maps). Se non c'è, manda la stessa cosa via email |
| **D10** | Email | Ultimo follow-up con link al video di 90 secondi | Sempre, salvo risposta nel frattempo |

Dopo il D10: **stop**. Nessun quarto messaggio. Stato nel CSV → `No` (ricontattabile tra 6 mesi con un aggancio nuovo).

Se risponde in qualunque momento: la sequenza si ferma subito e si passa a fissare la call.

## Regole non negoziabili

1. **Massimo 30 email al giorno** dalla tua casella. Sopra questa soglia rischi la cartella spam per tutte le email future. Niente strumenti di invio massivo in questa fase: invio manuale, una per una.
2. **SPF, DKIM e DMARC configurati** prima della prima email. Come verificare in 3 righe:
   - Vai su mxtoolbox.com (gratuito), inserisci il tuo dominio in "SPF Record Lookup", poi "DKIM Lookup", poi "DMARC Lookup": devono risultare tutti presenti e validi.
   - Se usi Google Workspace o un provider tipo Aruba/Register: cerca nella guida del provider "configurare SPF DKIM DMARC" — sono 3 record DNS da copiare nel pannello del dominio, 15 minuti di lavoro.
   - Controprova: manda un'email a un tuo indirizzo Gmail, apri "Mostra originale" e verifica SPF=PASS, DKIM=PASS, DMARC=PASS.
3. **Personalizza sempre la prima riga.** Un dettaglio vero visto sul sito (un lavoro fatto, la zona, il tipo di form). È la differenza tra il 2% e il 7% di risposte. Se non hai 60 secondi per personalizzare, non inviare.
4. **Mai più di un'azienda della stessa via/zona nello stesso giorno** se sono concorrenti diretti: se parlano tra loro, meglio non sembrare una circolare.
5. **Orari di invio**: martedì–giovedì, 7:30–9:00 oppure 12:30–14:00 (quando il titolare è in ufficio o in pausa, non sul cantiere).

## Batch settimanale consigliato: 30–40 contatti

Routine tipo (≈3 ore a settimana):

- **Lunedì (30 min)**: prepara il batch della settimana dal CSV — 30–40 aziende in stato `Da contattare`, controlla che sito e form siano ancora attivi.
- **Martedì + mercoledì (60 min)**: invia le email D0 (15–20 al giorno, restando sotto le 30/giorno contando anche i follow-up).
- **Ogni giorno (15 min)**: controlla risposte, manda i WhatsApp D3 e le email D10 in scadenza, aggiorna il CSV.
- **Venerdì (15 min)**: rivedi i numeri della settimana: inviate, risposte, call fissate.

## Tracking nel CSV (`lista-target.csv`)

Aggiorna la colonna **Stato** a ogni azione. Valori ammessi, nell'ordine del funnel:

`Da contattare` → `Contattato D0` → `Follow-up D3` → `Follow-up D10` → `Risposto` → `Call fissata` → `Cliente` / `No`

- In **Data primo contatto** metti la data dell'email D0: da lì calcoli D3 e D10.
- In **Note** scrivi sempre: dettaglio usato nella prima riga, eventuale risposta ricevuta, obiezioni.
- `No` non si cancella dalla lista: si ricontatta dopo 6 mesi solo se c'è un aggancio nuovo (sito rifatto, nuove Ads, stagione di punta).

## Numeri attesi (per non scoraggiarsi)

Su 100 contatti puliti e personalizzati: 5–8 risposte, 2–3 call, ~1 cliente. È normale. Il lavoro paga sulla costanza settimanale, non sul singolo invio.

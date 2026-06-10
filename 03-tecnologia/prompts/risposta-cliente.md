# Prompt — Bozza risposta email al lead (GPT-4o-mini)

Genera la risposta automatica che il potenziale cliente riceve entro 60 secondi. Messaggio **system** qui sotto; messaggio **user** = il JSON estratto dal prompt di estrazione. `temperature: 0.4`.

> Per il pilota Starter va benissimo anche un **template fisso** con 2 variabili (nome e tipo lavoro): più prevedibile e a costo zero. Il prompt serve da Pro in su, dove la risposta cita i dettagli della richiesta.

## Prompt base (copiare da qui)

```
Scrivi la risposta email di [NOME_AZIENDA], azienda di [MESTIERE] di [CITTÀ], a un potenziale cliente che ha appena inviato una richiesta dal sito.

Dati della richiesta (JSON): te li fornisce l'utente.

Struttura obbligatoria, massimo 120 parole totali, in italiano:
1. Saluto con il nome (se presente) e ringraziamento con riferimento SPECIFICO alla richiesta (cita il tipo di lavoro).
2. Conferma concreta: "[NOME_REFERENTE] la richiamerà entro oggi" — se l'orario corrente è dopo le 18 o weekend: "domattina alla prima ora" / "lunedì mattina".
3. UNA sola domanda utile per preparare il sopralluogo o il preventivo (vedi esempi per mestiere).
4. Firma: [FIRMA_AZIENDA: nome azienda, telefono, sito].

Tono: cordiale, professionale, concreto. Come scriverebbe un bravo titolare, non un call center.

VIETATO:
- indicare prezzi, sconti o stime economiche di qualunque tipo
- promettere date o orari di intervento specifici
- citare servizi non richiesti o non offerti dall'azienda
- usare le parole "automatico", "sistema", "bot"
- superare le 120 parole o aggiungere postscriptum

Se nome o dettagli sono null, scrivi comunque una risposta cortese generica con la stessa struttura.
```

## Domanda utile per mestiere (variabile [DOMANDA_MESTIERE])

| Verticale | Domanda da suggerire nel prompt |
|---|---|
| Serramentista | "Per prepararci al meglio: si tratta di abitazione o ufficio, e indicativamente quante aperture?" |
| Fotovoltaico | "Per il sopralluogo: il tetto è a falda o piano, e ha già una bolletta recente da mostrarci?" |
| HVAC | "Per arrivare preparati: che marca/modello è l'impianto attuale e da quanti anni è installato?" |

## Esempio (serramentista)

**Input (user):**

```json
{
  "nome": "Paolo Bianchi",
  "telefono": "339 1234567",
  "email": "p.bianchi@esempio.it",
  "tipo_lavoro": "infissi",
  "urgenza": 4,
  "riassunto": "Sostituzione 6 finestre PVC in appartamento a Modena est, chiede preventivo e sopralluogo entro fine mese."
}
```

**Output atteso:**

> Gentile Paolo Bianchi,
>
> grazie per la sua richiesta sulla sostituzione delle 6 finestre in PVC del suo appartamento a Modena est: l'abbiamo ricevuta e presa in carico.
>
> Marco la richiamerà entro oggi per fissare il sopralluogo, così da rientrare nei tempi del suo cantiere.
>
> Nel frattempo, per prepararci al meglio: si tratta di abitazione o ufficio, e le misure sono già disponibili o le rileviamo noi in sopralluogo?
>
> A presto,
> Serramenti [NOME_AZIENDA] — [TELEFONO] — [SITO]

## Variabili da personalizzare per cliente (6)

`[NOME_AZIENDA]`, `[MESTIERE]`, `[CITTÀ]`, `[NOME_REFERENTE]`, `[DOMANDA_MESTIERE]`, `[FIRMA_AZIENDA]` — si impostano una volta durante l'onboarding (vedi `checklist-onboarding-cliente.md`) e diventano l'"asset documentato" anti-churn del cliente (tono di voce registrato in `04-delivery/playbook-anti-churn.md`).

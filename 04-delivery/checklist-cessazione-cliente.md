# Checklist Cessazione Cliente (Offboarding)

> Obiettivo: uscita pulita, professionale, conforme al DPA — e porta aperta per un ritorno. Un offboarding fatto bene è marketing: l'ex cliente che parla bene di te vale più di una recensione.
> Prima di avviare: verifica che non sia un caso recuperabile (pausa stagionale, problema risolvibile) → tabella segnali in [playbook-anti-churn.md](playbook-anti-churn.md).

---

## 1. Alla ricezione della disdetta (entro 48h)

- [ ] **Conferma scritta della disdetta** via email: data di ricezione, decorrenza del **preavviso di 30 giorni** da contratto, **data esatta di fine servizio**
- [ ] Tono cordiale, zero recriminazioni: il servizio resta pienamente attivo fino alla data di fine
- [ ] **Richiesta feedback — 2 sole domande** (in call di 5 min o via email):
  1. *Perché disdice?*
  2. *Cosa avremmo potuto fare meglio?*
- [ ] **Annotare il motivo del churn** nel KPI tracker (`../00-piano/kpi-tracker.csv`, colonna Note): è il dato che alimenta l'audit pricing/churn della roadmap

## 2. Entro 15 giorni

- [ ] **Export dello storico richieste in CSV** (tutti i lead ricevuti: data, nome, contatto, tipo lavoro, esito risposta) e **consegna al cliente** — questo è ciò che gli spetta, ed è suo
- [ ] Verificare con il cliente di aver ricevuto e saputo aprire il file

## 3. Alla data concordata di fine servizio

- [ ] **Disattivazione del workflow** (non prima: il servizio è pagato fino all'ultimo giorno)
- [ ] **Rimozione del webhook dal form del cliente** — direttamente se ho accesso, altrimenti **istruzioni scritte semplici al cliente o al suo webmaster** (cosa togliere, dove, screenshot)
- [ ] Verificare che il form continui a funzionare normalmente dopo la rimozione (invio di prova)

## 4. Entro 30 giorni dalla fine (obblighi DPA)

- [ ] **Cancellazione di tutti i dati e le credenziali del cliente** entro 30 giorni, come previsto dal DPA art. 28 GDPR (log lead, dati nei tool, backup ove tecnicamente possibile)
- [ ] **Revoca accessi e chiavi API dedicate**: chiave OpenAI del cliente, bot/chat Telegram, credenziali n8n separate, eventuali accessi a Sheet/gestionale
- [ ] **Email finale di cortesia con porta aperta**: ringraziamento, conferma cancellazione dati avvenuta, e chiusura tipo *"Se in futuro le richieste dal sito dovessero tornare a crescere, mi trova qui: riattivare il servizio richiede pochi giorni."*

---

## Regola fissa — NON negoziabile

> **MAI consegnare workflow, prompt o configurazioni.** L'automazione è proprietà del fornitore, come da contratto (leva 6 del playbook anti-churn). Al cliente si consegna **solo l'export dello storico richieste**. Se il cliente (o il suo nuovo fornitore) insiste: rispondere con cortesia citando la clausola contrattuale — senza eccezioni, nemmeno "solo lo schema".

---

## Riepilogo rapido (vista a colpo d'occhio)

- [ ] Conferma scritta disdetta + data fine servizio (preavviso 30 gg)
- [ ] Feedback 2 domande + motivo churn nel KPI tracker
- [ ] Export storico richieste CSV consegnato entro 15 gg
- [ ] Workflow disattivato alla data concordata
- [ ] Webhook rimosso dal form (o istruzioni inviate)
- [ ] Dati e credenziali cancellati entro 30 gg (DPA)
- [ ] Accessi e chiavi API revocati
- [ ] Email finale di cortesia con porta aperta
- [ ] Nessun workflow/configurazione consegnato

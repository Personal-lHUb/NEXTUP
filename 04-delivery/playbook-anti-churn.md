# Playbook Anti-Churn — Le 6 leve

> Il modello vive di MRR: ogni cliente perso vale €197–347/mese in meno e ~100 outreach per rimpiazzarlo. Trattenere costa sempre meno che acquisire.
> **Target churn:** 3–5%/mese accettabile in fase iniziale (30–45% annuo) → obiettivo **1–2%/mese a regime** con le 6 leve attive.
> **Allarme rosso:** churn **> 6%/mese nei primi 90 giorni** di servizio = problema di onboarding/aspettative → **rifare il processo di onboarding**, non incolpare il cliente (vedi trigger in `../00-piano/roadmap-kill-criteria.md`).

---

## Leva 1 — Report mensile automatico (il valore in numeri)

- **Cosa fare:** 1 PDF al mese con richieste ricevute, % risposte entro 5 minuti, follow-up inviati, confronto col mese precedente. Base: [report-mensile-template.md](report-mensile-template.md). Il titolare deve VEDERE il valore, non ricordarselo.
- **Quando:** manuale fin dal 1° cliente; automatizzato in n8n nei mesi 5–9; invio entro il giorno 3 di ogni mese.
- **Costo in ore:** 4h una tantum di build in n8n, poi ~5 min/cliente/mese per le 3 righe di commento personalizzato.
- [ ] Build n8n fatto
- [ ] Invio attivo per tutti i clienti

## Leva 2 — Asset documentati del cliente (costo psicologico di switch)

- **Cosa fare:** per ogni cliente, documento vivo con: template di risposta approvati, tono di voce, classificazione tipi-lavoro (es. "zanzariere = bassa urgenza, infissi cantiere = alta"). Se cambia fornitore, riparte da zero: questo è il moat.
- **Quando:** creato in onboarding, aggiornato a ogni modifica e a ogni quarterly review.
- **Costo in ore:** ~1h in onboarding + 15 min/trimestre per aggiornarlo.
- [ ] Documento asset creato per ogni cliente attivo

## Leva 3 — Quarterly review 15 min (solo Premium)

- **Cosa fare:** call trimestrale di 15 minuti con script fisso → [quarterly-review-script.md](quarterly-review-script.md). Ascolto, un'ottimizzazione concreta, upsell solo se emerge un bisogno.
- **Quando:** ogni 3 mesi per ogni cliente Premium, fissata in calendario alla firma.
- **Costo in ore:** ~1h a cliente (prep + call + note) = **8h/trimestre totali con 6–8 Premium**.
- [ ] Calendario review impostato per tutti i Premium

## Leva 4 — Lock-in tecnico leggero (integrazioni)

- **Cosa fare:** integrare il sistema con gli strumenti che il cliente usa già: Excel, Google Sheet, Fatture in Cloud. Più punti di integrazione = più costoso lo switch (e più valore percepito).
- **Quando:** inclusa nei Premium fin dall'onboarding; per i Pro come upsell quando il bisogno emerge (review, commento al report, richiesta diretta).
- **Costo in ore:** 1–2h per integrazione, una tantum.
- [ ] Almeno 1 integrazione attiva per ogni Premium

## Leva 5 — Pricing annuale −10% (cassa + lock-in)

- **Cosa fare:** proporre il pagamento annuale anticipato: **€197 → €177/mese** (12 mesi). Incassi subito, il cliente è vincolato 12 mesi, lo sconto è la tua assicurazione anti-churn.
- **Quando:** dopo 3+ mesi di servizio senza problemi, oppure ogni volta che il cliente chiede uno sconto (mai sconto secco: solo in cambio dell'annuale).
- **Costo in ore:** 0h — una frase in call o in coda al report.
- [ ] Offerta annuale proposta a ogni cliente oltre il 3° mese

## Leva 6 — MAI consegnare il workflow

- **Cosa fare:** l'automazione (workflow n8n, prompt, configurazioni) resta proprietà del fornitore, scritto nel contratto. A cessazione si consegna **l'export dello storico richieste in CSV**, non l'automazione → procedura in [checklist-cessazione-cliente.md](checklist-cessazione-cliente.md).
- **Quando:** sempre: clausola in ogni contratto, ribadita con cortesia in offboarding.
- **Costo in ore:** 0h — è una clausola contrattuale.
- [ ] Clausola presente nel contratto base

---

## Segnali di rischio churn → contromossa

Controllo mensile, insieme all'invio dei report:

| Segnale di rischio | Contromossa |
|---|---|
| Cliente non apre i report da 2 mesi | **Chiamata di cortesia** (5 min): "volevo solo sentire come va" — niente vendita |
| Lead in calo per stagionalità | Proporre **pausa estiva a canone ridotto** invece di aspettare la disdetta |
| Cliente chiede "come si spegne" / come disattivare | **Call entro 24h**: capire il problema reale prima che diventi disdetta |
| Mancato pagamento | **Sollecito gentile a 7 giorni**, sospensione del servizio a 15 giorni |

- [ ] Checklist segnali ripassata a ogni chiusura mese (insieme al KPI tracker: `../00-piano/kpi-tracker.csv`)

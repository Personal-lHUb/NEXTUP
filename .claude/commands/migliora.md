---
description: Fa girare il team di miglioramento sul sistema: misure, analisi, verifica, piano di lavoro con le patch già scritte.
---

# Passata di miglioramento

Metti al lavoro il team sul sistema `kdp-book-factory`. L'obiettivo di questa
casa editrice è **vendere libri**: ogni segnalazione va ordinata per quanto
sposta quel risultato, e quando non lo sposta va detto.

Argomento ricevuto: `$ARGUMENTS` (facoltativo: uno slug, un'area come
`scheda`/`codice`/`costi`, o vuoto per una passata completa).

## 1. Prima i fatti

```bash
cd kdp-book-factory && python3 -m kdpfactory diagnostica
```

Non costa niente e non chiama nessun modello. Produce `diagnostica.json`: è la
base comune di tutto il team. **Senza questo passaggio non si parte**, perché
gli agenti ragionerebbero su impressioni.

Leggi il rapporto e dimmi in tre righe che cosa salta all'occhio, prima di
mandare avanti chiunque.

## 2. Poi le tre analisi, in parallelo

Lancia insieme, con il tool Agent:

- `analista-mercato` — che cosa impedisce il clic e la conversione;
- `ingegnere-pipeline` — difetti del codice, in ordine di gravità per il libro
  stampato;
- `economo` — costo per libro e quante copie servono per ripagarlo.

A ciascuno passa il percorso di `diagnostica.json` e l'eventuale argomento
ricevuto. Sono indipendenti: vanno mandati nella stessa richiesta.

## 3. Poi la verifica

Quando tutti e tre hanno risposto, passa le loro proposte a
`avvocato-del-diavolo`. Non salti questo passaggio nemmeno quando le proposte
sembrano ovvie: le proposte ovvie sono quelle che nessuno controlla.

## 4. Infine il piano

Passa tutto — diagnostica, le tre relazioni e le obiezioni — a
`capo-collana`, che consegna il piano definitivo: **tre cose da fare adesso**,
il resto in ordine, quello che è stato scartato e perché.

## 5. Che cosa mi consegni

Riporta il piano del capo collana, e per ogni voce di «da fare adesso» la
patch già scritta. Poi **fermati e chiedimi che cosa applicare**: il team
propone, non applica. Nessun agente del team ha il permesso di scrivere file,
e quel vincolo non va aggirato applicando tu le modifiche senza chiedere.

Se ti dico di procedere, applica solo ciò che ho approvato, poi fai girare
test e lint:

```bash
cd kdp-book-factory && python3 -m unittest discover -s tests && ruff check kdpfactory tests
```

e ripeti la diagnostica per mostrarmi che cosa è cambiato nei numeri.

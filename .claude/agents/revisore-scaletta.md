---
name: revisore-scaletta
description: Esamina la scaletta prima che diventi un libro: argomenti del brief rimasti scoperti, capitoli che si sovrappongono, titoli generici, promesse di risultato, date dichiarate come fatti, quantità da contare. Non usa il modello: conta.
tools: Read, Grep, Glob, Bash
---

# Revisore di scaletta

Esamina la scaletta prima che diventi un libro: argomenti del brief rimasti scoperti, capitoli che si sovrappongono, titoli generici, promesse di risultato, date dichiarate come fatti, quantità da contare. Non usa il modello: conta.

## Come lavorare

Questo agente non usa il modello: misura la scaletta.

```bash
cd kdp-book-factory
python3 -m kdpfactory manuale <slug> scaletta --esamina
```

Le segnalazioni **bloccanti** fermano l'importazione della scaletta: vanno
risolte riscrivendo `books/<slug>/manuale/scaletta.json`, non aggirate. Le
`importanti` si valutano una per una. Le `minori` — in particolare l'elenco
delle cifre dichiarate — sono una lista di verifica da fare sul libro finito.

Se ti viene chiesto di esaminare una scaletta a mano, applica le stesse
regole: ogni argomento di `brief.md` deve avere un capitolo, nessun capitolo
deve ripetere un altro, nessun titolo deve essere un segnaposto, nessuna
promessa di risultato, nessuna data presentata come fatto accertato, e ogni
cifra dichiarata dev'essere contata sul libro.

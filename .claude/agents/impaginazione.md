---
name: impaginazione
description: Controlla il PDF impaginato: righe vedove e orfane, titoli in fondo alla pagina, code di capitolo, testo fuori gabbia, sillabazione, aperture di capitolo. Non usa il modello: misura le coordinate del testo.
tools: Read, Grep, Glob, Bash
---

# Controllo impaginazione

Controlla il PDF impaginato: righe vedove e orfane, titoli in fondo alla pagina, code di capitolo, testo fuori gabbia, sillabazione, aperture di capitolo. Non usa il modello: misura le coordinate del testo.

## Come lavorare

Questo agente non usa il modello: misura le coordinate del testo nel PDF
impaginato. Esegui il controllo e riporta l'esito.

```bash
cd kdp-book-factory
python3 -m kdpfactory review <slug> --agents impaginazione
```

Se il libro non è ancora impaginato, esegui prima `python3 -m kdpfactory build
<slug>`. Riporta le segnalazioni così come escono, raggruppate per categoria, e
indica quali richiedono un intervento sul testo (vedove, orfane, code di
capitolo) e quali sull'impaginazione (testo fuori gabbia, aperture di capitolo).

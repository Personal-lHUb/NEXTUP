---
name: copertina
description: Misura la prima di copertina come si vede in miniatura: corpo del titolo, contrasto, stacco su fondo bianco, affollamento, area di sicurezza. Controlla anche i testi: ciclo aperto e rivendicazioni vietate. Non usa il modello.
tools: Read, Grep, Glob, Bash
---

# Controllo copertina

Misura la prima di copertina come si vede in miniatura: corpo del titolo, contrasto, stacco su fondo bianco, affollamento, area di sicurezza. Controlla anche i testi: ciclo aperto e rivendicazioni vietate. Non usa il modello.

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

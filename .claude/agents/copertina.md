---
name: copertina
description: Misura la prima di copertina come si vede in miniatura: corpo del titolo, contrasto, stacco su fondo bianco, affollamento, area di sicurezza. Controlla anche i testi: ciclo aperto e rivendicazioni vietate. Non usa il modello.
tools: Read, Grep, Glob, Bash
---

# Controllo copertina

Misura la prima di copertina come si vede in miniatura: corpo del titolo, contrasto, stacco su fondo bianco, affollamento, area di sicurezza. Controlla anche i testi: ciclo aperto e rivendicazioni vietate. Non usa il modello.

## Come lavorare

Questo agente non usa il modello: misura il PDF della copertina e legge i
testi che ci stanno sopra.

```bash
cd kdp-book-factory
python3 -m kdpfactory review <slug> --agents copertina
```

Se la copertina non è ancora stata disegnata, esegui prima `python3 -m
kdpfactory build <slug>`. Le misure che contano sono quelle in miniatura: corpo
del titolo rispetto all'altezza, contrasto, stacco su fondo bianco, testo dentro
l'area di sicurezza. I rilievi sui testi — gancio, rivendicazioni vietate,
formula della categoria — si risolvono riscrivendo la copertina, non il libro.

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
kdpfactory build <slug>`.

## Che cosa misura

**In miniatura** (è l'unico modo onesto di giudicare una copertina): corpo del
titolo rispetto all'altezza, contrasto, stacco su fondo bianco, affollamento
della metà alta, testo dentro l'area di sicurezza.

**Sulle specifiche KDP**, e sono tutti bloccanti perché fermano il
caricamento: dimensioni del PDF contro il calcolo del dorso, area del codice a
barre libera, testo di dorso dentro le pieghe e ammesso solo da 79 pagine,
font incorporati, linee di piega rimaste nel file, nome dell'autore uguale a
quello della scheda.

**Sui testi**: gancio (ciclo aperto), rivendicazioni vietate da KDP, formula
della categoria, cifre che non corrispondono a un dato contato sul libro.

## Che cosa **non** misura, e va guardato a occhio

La cosa che decide se una copertina vende: **l'immagine rappresenta il libro?**
Una sagoma astratta, un gradiente o un ornamento geometrico decorano; una
figura riconoscibile spiega. Chi scorre i risultati non legge, cerca la
copertina che somiglia alla cosa che è venuto a comprare.

Quando guardi una copertina, chiediti in quest'ordine:

1. In due secondi, si capisce di che categoria è?
2. L'immagine mostra il soggetto vero del libro, o lo decora soltanto?
3. C'è **un solo** concetto visivo dominante, e **un solo** fattore distintivo?
4. Il titolo vince su tutto il resto?
5. Sembra art-directed e contemporanea, o un modello generico?

Se la risposta a una di queste è no, il rimedio non è un controllo in più: è
il brief. `python3 -m kdpfactory copertina <slug>` produce il brief da dare a
uno strumento grafico, con la rappresentazione giusta per quella categoria
già dentro. L'immagine che torna si salva in `assets/copertina.jpg` e il
sistema la misura, la ritaglia e dice se i pixel bastano.

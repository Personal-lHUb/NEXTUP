# BOARD — la lavagna della linea

> Proprietario: `pipeline-manager`. Finché i libri in linea sono meno di due, lo tieni tu.
> Stati: `validated → defined → translated → structured → drafted → checked → edited → laid-out → screened → packaged → shipped`

Ultimo aggiornamento: 2026-09-14

## In linea

| libro | titolo di lavoro | archetipo | stato | G0 | G1 | G2 | G3 | ore autore | blocchi | esce |
|-------|------------------|-----------|-------|----|----|----|----|------------|---------|------|
| b01 | «DECIDI: ruolo» | A · libro-lista | — | ☐ | ☐ | ☐ | ☐ | 0,0 h | osservazioni G0, COSTI.md | — |

## Tempo autore per libro — REALE, cronometrato, non stimato

| libro | G0 | G1 | G2 | G3 | totale |
|-------|----|----|----|----|--------|
| b01 | | | | | |

**Come si legge.** Sotto le 5 ore la cadenza settimanale regge con margine. Fra 5 e 8
regge senza margine: la prima settimana storta salta una consegna. Sopra le 8, un libro
a settimana non esiste con questa configurazione.

**Se sale per tre libri di fila** la cadenza sta per rompersi, e lo sai con settimane di
anticipo. Cause tipiche in ordine: definizione del G1 troppo vaga (la coda del G2 si
gonfia), libro più lungo del dichiarato, `SERIES.md` non aggiornato.

## Blocchi aperti

| libro | artefatto | proprietario | `NEEDS` o `DISPUTE` | da |
|-------|-----------|--------------|---------------------|----|
| b01 | `b01/00-niche.md` | `niche-validator` | `NEEDS: osservazioni di mercato — righe della scheda che solo l'autore puo' leggere` | 2026-09-14 |
| b01 | `market/pricing-exante.md` | `pricing-analyst` | `NEEDS: COSTI.md — costi fissi e parametri di stampa` | 2026-09-14 |

## Slittamenti

Regola: un libro slitta, la linea non si ferma. Mai due libri spediti insieme per
recuperare. Al secondo slittamento si taglia la sezione problematica e si spedisce.

| libro | quante volte | perché |
|-------|--------------|--------|
| — | | |

## Log decisioni

- 2026-09-14 — b01 — Aperto. Cornice ereditata da `SERIES-LMC.md`: archetipo A, asse
  ruolo, 77 voci, personaggio ricorrente. Tre candidati messi in prova (infermiera,
  veterinaria, ostetrica), scelti di ampiezza diversa per tarare il test di saturazione.
  Il ruolo non e' deciso: e' un «DECIDI».
- (data) — (libro) — (cosa hai deciso e perché)

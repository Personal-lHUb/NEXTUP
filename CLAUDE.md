# NEXTUP — mappa del repository

Tre corpi di lavoro senza rapporto fra loro. Non mescolarli.

| Cartella | Cos'è |
|---|---|
| `linea/` | la linea editoriale KDP: artefatti di lavorazione dei libri |
| `.claude/agents/` | i 27 agenti che la eseguono |
| `manuale-modulo-1-amazon-ads/` | il manuale del Modulo 1, documento a sé |
| `nexus-pwa.zip` | PWA preesistente, non correlata |

## La linea editoriale

**La radice di lavoro è `linea/`.** Dove i prompt degli agenti scrivono `bNN/…`
si intende `linea/bNN/…`; dove scrivono `BOARD.md`, `SERIES.md`, `GLOSSARY.md`,
`PERFORMANCE.md` o `market/…` si intende `linea/…`.

Un libro è una cartella `linea/b01/`, `linea/b02/`… Si crea copiando
`linea/_template-libro/`.

### I tre gate

Il lavoro degli agenti si ferma a tre punti, e li decide l'autore.

- **G0 — la nicchia entra o no.** `niche-validator` dà il verdetto sui sei test;
  `pricing-analyst` produce la stima ex-ante ed è **bloccante**. Sotto soglia la
  nicchia non entra, qualunque cosa dica il resto.
- **G1 — il libro è quello che volevi.** Si esce quando `00-spec-it.md` non ha più
  `«DECIDI»` aperti.
- **G2 — la coda unica.** `pipeline-manager` fonde le liste di `fidelity-auditor`,
  `fact-checker` e `continuity-checker` in un solo elenco numerato. Si esce a zero.
- **G3 — si pubblica.** Zero `ALTO` in `08-risk.md`, `PUBBLICA` in `14-compliance.md`,
  zero `TIENI`, `ABBANDONO` di `15-read.md` affrontato, cinque `«SERVE TUO»` risposti.

### Le regole che nessun agente può violare

**Un artefatto, uno scrittore.** Ogni file in `bNN/` ha un solo agente proprietario,
dichiarato in testa al file. Se un agente deve cambiare un artefatto altrui, emette
`DISPUTE: <file> — <cosa>` e si ferma.

**Nessun dato inventato.** BSR, volumi di ricerca, vendite, prezzi, numeri di
recensioni, citazioni: se non è verificato, si scrive che non lo è. Un numero
plausibile è peggio di nessun numero, perché sembra una prova.

**L'autore decide il contenuto.** Gli agenti raccolgono, strutturano, verificano e
producono. Non scelgono di cosa parla il libro.

**Originalità.** Un titolo concorrente serve a capire il mercato, mai a fornire il
testo. Da un concorrente si prendono nicchia, formato, prezzo, keyword e **ciò di cui
i lettori si lamentano**: sono fatti. Non si prendono testo, struttura creativa,
esempi o copertina.

### Marcatori

`«DECIDI: …»` una decisione dell'autore · `«VERIFY: …»` un buco nel brief ·
`«XREF: …»` un'assunzione su un'altra sezione · `«AMBIGUO: …»` una frase che non si
chiarisce senza decidere cosa significa · `«SERVE TUO: …»` trenta secondi di voce
dell'autore · `ALTO` / `TIENI` bloccanti al G3.

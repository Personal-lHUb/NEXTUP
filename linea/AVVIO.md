# Come si fa partire un libro

> Leggi prima `CLAUDE.md` nella radice: gate, regole, marcatori.

## Prima di cominciare, tre cose devono esistere

1. **`COSTI.md` compilato.** Senza, `pricing-analyst` si ferma e il G0 non chiude.
2. **Un bersaglio osservato.** I sei test hanno due righe che solo tu puoi riempire —
   saturazione e lamentela ricorrente — e richiedono novanta minuti su Amazon in
   incognito, con indirizzo di consegna USA. Nessun agente può sostituirti qui: chi
   fa la ricerca deve essere chi decide.
3. **`SERIES.md` con l'asse del filone**, se il titolo appartiene a una serie.

## La sequenza

```
G0   market-researcher   → linea/bNN/10-competitors.md
     pricing-analyst     → linea/market/pricing-exante.md      ← BLOCCANTE
     niche-validator     → linea/bNN/00-niche.md               ← verdetto 6/6
     avatar-builder      → linea/bNN/avatar.md
     ─────────────────── TU: la nicchia entra? ───────────────────

G1   book-definer        → linea/bNN/00-spec-it.md  (in italiano, con «DECIDI»)
     ─────────────────── TU: zero «DECIDI» aperti ───────────────
     intake-translator   → linea/bNN/01-spec.md     (inglese, fedele)
     outline-architect   → linea/bNN/02-structure.md
     character-designer  → linea/bNN/character-sheet.md   (archetipo A)

     page-writer ×N      → linea/bNN/pages/NN-draft.md    IN PARALLELO
     example-builder     → linea/bNN/pages/NN-examples.md (archetipi C e B)

     fidelity-auditor    → linea/bNN/03-fidelity.md
     fact-checker        → linea/bNN/04-facts.md
     continuity-checker  → linea/bNN/05-continuity.md
     pipeline-manager    fonde le tre liste in una coda sola
G2   ─────────────────── TU: conferma / correggi / elimina ──────

     developmental-editor→ linea/bNN/06-dev-notes.md
     line-editor         → linea/bNN/07-edited.md
     voice-editor        → linea/bNN/07v-voiced.md    ← ULTIMO sul testo
     blind-reader        → linea/bNN/15-read.md       ← non vede spec né struttura

     risk-screener       → linea/bNN/08-risk.md
     cover-director      → linea/bNN/cover-brief.md
     production-formatter→ linea/bNN/build/
     proofreader         → linea/bNN/09-proof.md
     keyword-strategist  → linea/bNN/11-keywords.md
     listing-copywriter  → linea/bNN/12-listing.md
     pricing-analyst     → linea/bNN/13-pricing.md
     platform-compliance-officer → linea/bNN/14-compliance.md
G3   ─────────────────── TU: si pubblica ────────────────────────

     ads-manager         → linea/bNN/16-ads.md
     performance-analyst → PERFORMANCE.md   (~30 giorni dopo)
```

## Due ordini che non sono negoziabili

**`voice-editor` dopo `line-editor`.** Un line editor normalizza, ed è esattamente la
texture che il voice editor aggiunge. Invertiti, il secondo cancella il primo.

**`blind-reader` a libro finito, e cieco.** Se vede la spec non può accorgersi che una
sezione ha fallito: il piano gli riempie i buchi in testa prima che li senta.

## Cosa fare del report di lettura cieca

| Cosa ha trovato | Cosa fai |
|---|---|
| `ATTRITO`, `PERSO` su un punto singolo | si corregge adesso, patch da due minuti |
| `ABBANDONO` | si affronta sempre, anche solo tagliando. È l'unico che può far slittare |
| `NOIA`, `RESA` incompleta | **non si corregge**: si registra in `PERFORMANCE.md` e cambia il brief del prossimo |

Il terzo caso è il punto della lettura cieca su una linea settimanale. Non serve a
salvare questo libro: serve a non ripetere il difetto nei cinquanta successivi.

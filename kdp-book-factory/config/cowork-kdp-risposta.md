Esito: parziale — punti 4, 5: la tabella KDP delle pagine non ha una riga per il cartaceo 6x9; KDP non dice che il limite delle parole chiave è di 50 caratteri

# Cowork · risposta a cowork-kdp.md — regole KDP

Verifiche del 30 settembre 2026, fra le 17:00 e le 17:32 (ora di Roma); gli orari dei singoli punti sono indicativi entro quella finestra, sulle pagine
di aiuto di kdp.amazon.com (en_US). Ho letto il testo delle pagine nel browser, ma non
ho aperto il flusso di pubblicazione né l'account KDP. In ogni punto segnalo dove il
valore trovato è diverso da quello che oggi c'è nel repository.

## 1. Costi di stampa del cartaceo

URL: https://kdp.amazon.com/en_US/help/topic/G201834340 (pagina «Paperback Printing Cost»).
Verifica del 2026-09-30 alle 17:24.

Formula riportata: «Fixed cost + (page count * per page cost) = printing cost».

Tabella «Black ink paperback with cream or white paper», **Regular Trim Sizes**. Il 6x9
rientra fra le misure regolari: la pagina chiama «large» solo le misure «More than 6.12
inches (155.5 mm) in width or more than 9 inches (228.6 mm) in height».

| mercato | 24–110 pagine: solo costo fisso | 110–828 pagine: costo fisso | 110–828 pagine: costo per pagina |
|---|---|---|---|
| Amazon.com | 2.30 USD | 1.00 USD | 0.012 USD |
| Amazon.co.uk | 1.93 GBP | 0.85 GBP | 0.010 GBP |
| Amazon.de/es/fr/it/nl/ie/com.be | 2.05 EUR | 0.75 EUR | 0.012 EUR |

Per confronto, le misure «large» su Amazon.com costano 2.84 USD sotto le 110 pagine,
e 1.00 USD + 0.017 USD a pagina sopra.

- **La soglia è 110 pagine, non 108.** Nota della pagina: «Black-ink paperbacks with
  24 - 110 pages only incur the fixed cost (24 - 108 pages for Amazon.com.au)».
- **Carta crema e carta bianca costano uguale**: c'è una sola tabella, intitolata
  «Black ink paperback with cream or white paper». La carta groundwood ha una tabella
  a parte, con costi per pagina più bassi di circa il 5%.
- **Royalty del cartaceo.** URL: https://kdp.amazon.com/en_US/help/topic/G201834330
  (pagina «Paperback Royalty»). Verifica del 2026-09-30 alle 17:27. La percentuale è il
  50% o il 60%, e dipende dal prezzo di listino:

  | mercato | 50% se il prezzo è pari o inferiore a | 60% se il prezzo è pari o superiore a |
  |---|---|---|
  | Amazon.com | 9.98 USD | 9.99 USD |
  | Amazon.de/fr/it/es/nl/ie/com.be | 9.98 EUR | 9.99 EUR |
  | Amazon.co.uk | 7.98 GBP | 7.99 GBP |

  Formula: «(Royalty rate x list price) – printing costs = royalty». Con la distribuzione
  estesa (Expanded Distribution) la royalty è del 40%. Il prezzo massimo è 250 USD,
  250 EUR o 250 GBP.

**Differenze con `printing_costs.json`:**

- la soglia è 110 pagine e non 108;
- il costo fisso sopra la soglia è 1.00 USD (nel file 0.85), 0.85 GBP (nel file 0.70) e
  0.75 EUR (nel file 0.60);
- il 60% vale solo da 9.99 USD/EUR e da 7.99 GBP in su. Sotto questi prezzi la royalty
  è del 50%, mentre il file usa sempre il 60%.

## 2. Dorso

URL: https://kdp.amazon.com/en_US/help/topic/G201953020 (pagina «Create a Paperback Cover»).
Verifica del 2026-09-30 alle 17:29.

- Carta bianca: «page count x 0.002252" (0.0572 mm)». Coincide con il repository.
- Carta crema: «page count x 0.0025" (0.0635 mm)». Coincide con il repository.
- Testo sul dorso: «To include spine text, your book must have at least 79 pages».
  Coincide con il repository. Due precisazioni della stessa pagina:
  - il testo deve restare ad almeno 0.0625" (1.6 mm) dai bordi del dorso, e si deve
    lasciare una tolleranza di 0.0625" su ciascun lato delle pieghe;
  - con Cover Creator il minimo sale a 80 pagine.

## 3. Abbondanza e margini

- **Interno.** URL: https://kdp.amazon.com/help?topicId=GVBQ3CMEQW3W2VL6 («Set Trim Size,
  Bleed, and Margins»). Verifica del 2026-09-30 alle 17:12, letta con uno strumento di
  estrazione del testo, non nel browser.
  - Abbondanza di 0.125" (3.2 mm) su alto, basso e lato esterno.
  - Margine esterno minimo di 0.25" (6.4 mm) senza abbondanza e di 0.375" (9.6 mm) con
    abbondanza. Coincide con il repository.
  - Margine interno (gutter) per numero di pagine: 24–150 → 0.375"; 151–300 → 0.5";
    301–500 → 0.625"; 501–700 → 0.75"; 701–828 → 0.875".
- **Copertina.** URL: https://kdp.amazon.com/en_US/help/topic/G201953020. Verifica del
  2026-09-30 alle 17:29.
  - Abbondanza: «add 0.125" (3.2 mm) to the top, bottom, and outside edges».
  - **Zona di sicurezza del testo:** la pagina chiede che il testo sia «at least 0.125"
    (3.2 mm) inside the trim lines». Il repository usa 0.25", quindi è più prudente.
    0.25" è invece il minimo per le cornici («they should cover at least 0.25" (6.4 mm)
    inside the trim line»).
- **Codice a barre.** URL: https://kdp.amazon.com/en_US/help/topic/G5HDYGP4BXLX4RUW
  («Barcodes»). Verifica del 2026-09-30 alle 17:31, letta con uno strumento di estrazione
  del testo, non nel browser.
  - Misura suggerita «2" x 1.2" (50.8 x 30.5 mm)». Coincide con il repository.
  - Misura minima «1.4" x .8" (35.56 x 20.3 mm)».
  - Posizione: «at least .25" (6.3 mm) from the spine and trim of the cover».

## 4. Pagine minime e massime, formato 6x9

URL: https://kdp.amazon.com/en_US/help/topic/G201834180 («Print Options»). Verifica del
2026-09-30 alle 17:18, dalla tabella «Trim size specifications … (kdp.amazon.com)» nel
browser.

- **Cartaceo:** nel testo della pagina la tabella di kdp.amazon.com ha **una sola riga**
  per le misure regolari del cartaceo, `5" x 8"`, con questi valori: bianca 24–828,
  **crema 24–776**, groundwood 24–812, colore standard 72–600, colore premium 24–828.
  Una riga dedicata al cartaceo 6x9 non c'è.
- **Rilegato (Hardcover) 6x9:** 75–550 per bianca, crema e colore premium.
- La pagina dei costi (punto 1) usa lo scaglione «110-828 pages» per il cartaceo in
  bianco e nero, senza distinguere fra crema e bianca.

Nel repository `PAPER_PAGE_LIMITS` ha crema (24, 828). Il dato di KDP per la crema, nella
riga 5x8, è 776. Non ho potuto verificare se 776 valga anche per il 6x9. Si può
controllare con il calcolatore di copertina di KDP, oppure con il selettore delle pagine
nel flusso di un cartaceo, che è in `cowork-amazon.md`.

## 5. Parole chiave e categorie

- **Parole chiave.** URL: https://kdp.amazon.com/en_US/help/topic/G201298500. Verifica del
  2026-09-30 alle 17:14 e alle 17:31, letta con uno strumento di estrazione del testo.
  - Testo della pagina: «Use up to seven keywords or short phrases. Keep an eye on the
    character limit in the text field».
  - **La pagina non indica il numero di caratteri**: il limite di 50 non vi compare.
    Resta da leggere nel campo del modulo.
  - Da non mettere nelle parole chiave, secondo la pagina:
    - informazioni già presenti in altri metadati (titolo, contributori);
    - termini delle categorie;
    - giudizi di qualità («best novel ever»);
    - frasi che scadono («new», «on sale», «available now»);
    - parole generiche come «book»;
    - errori di ortografia e varianti di formattazione;
    - «the name of an author not associated with your book»;
    - «Brands that you do not own or that you are unauthorized to use»;
    - virgolette;
    - «Amazon program names like as 'Kindle Unlimited' or 'KDP Select'»;
    - tag HTML.

    La pagina aggiunge: «zero tolerance policy for metadata that is meant to
    advertise, promote, or mislead». Non vieta espressamente i titoli di altri libri:
    rientrano nel divieto generale di metadati ingannevoli.
- **Categorie.** URL: https://kdp.amazon.com/en_US/help/topic/G200652170. Verifica del
  2026-09-30 alle 17:14, letta con uno strumento di estrazione del testo: «As an author,
  you can select 3 categories when creating a book in KDP».

## 6. Descrizione

URL: https://kdp.amazon.com/en_US/help/topic/G201189630. Verifica del 2026-09-30 alle
17:14, letta con uno strumento di estrazione del testo.

- Limite: «we have a limit of 4000 characters for the description». **I tag HTML
  contano** nei 4000 caratteri: la parola «test» in grassetto vale 11 caratteri.
- Tag accettati: `<br>`, `<p>`, `<b>`, `<em>`, `<i>`, `<u>`, da `<h4>` a `<h6>`
  (`<h1>`–`<h3>` non sono supportati), `<ol>` e `<ul>` con `<li>`.

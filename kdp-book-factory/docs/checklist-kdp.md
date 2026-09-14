# Checklist di pubblicazione su Amazon KDP

Da percorrere una volta per titolo, prima di premere "Pubblica".
Le voci contrassegnate con **[auto]** sono già verificate da `kdpfactory qa`.

---

## 1. File dell'interno

- [ ] **[auto]** Numero di pagine fra 60 e 240 (limite KDP: 24-828 per il bianco e nero).
- [ ] **[auto]** Numero di pagine pari.
- [ ] **[auto]** Tutte le pagine hanno lo stesso formato, uguale al trim size scelto.
- [ ] **[auto]** Tutti i font sono incorporati nel PDF.
- [ ] **[auto]** Margine interno ≥ minimo richiesto per il numero di pagine
      (0,375" fino a 150 pagine; 0,5" da 151 a 300).
- [ ] **[auto]** Margini esterni ≥ 0,25".
- [ ] Aprire il PDF e sfogliare almeno: frontespizio, colophon, indice, prima
      pagina di due capitoli, ultima pagina. Nessun titolo isolato in fondo alla
      pagina, nessuna riga vedova evidente.
- [ ] Controllare che l'indice riporti i numeri di pagina corretti.
- [ ] Nessuna pagina bianca con testatina o numero di pagina.

## 2. Copertina

- [ ] Generata **dopo** l'impaginazione definitiva: lo spessore del dorso dipende
      dal numero di pagine reale (una pagina in più cambia le misure del file).
- [ ] **[auto]** Dimensioni totali = (2 × larghezza) + dorso + 0,25" di abbondanza,
      altezza = trim + 0,25".
- [ ] Testo sul dorso solo da 79 pagine in su.
- [ ] Area del codice a barre (2" × 1,2" in basso a destra della quarta) libera.
- [ ] Nessun testo importante a meno di 0,25" dai bordi di rifilo.
- [ ] Rigenerare la copertina **senza** `--guides`: le linee guida non vanno caricate.
- [ ] Se la copertina è generata con IA, dichiararlo nel modulo KDP.

## 3. Contenuto

- [ ] **[auto]** Nessun testo segnaposto, nessun meta-commento del modello.
- [ ] **[auto]** Nessun capitolo sotto le 300 parole.
- [ ] **[auto]** Nessuna frase lunga ripetuta identica in capitoli diversi.
- [ ] Rilettura umana completa. Ogni affermazione fattuale che non sapresti
      difendere va riscritta o tolta.
- [ ] Nessuna statistica, citazione, studio o dato attribuito a una fonte che non
      hai verificato personalmente.
- [ ] Nessun testo altrui: brani, testi di canzoni, poesie, traduzioni, immagini.
- [ ] Se il tema tocca salute, diritto, fisco o investimenti: avvertenza esplicita
      che non è consulenza professionale (la pipeline la inserisce nel colophon).
- [ ] Il libro mantiene la promessa del titolo e della descrizione.

## 4. Scheda prodotto

- [ ] **[auto]** Titolo + sottotitolo entro 200 caratteri.
- [ ] **[auto]** Descrizione entro 4.000 caratteri, senza claim promozionali,
      riferimenti al prezzo, link o nomi di altri autori.
- [ ] **[auto]** 7 keyword, ognuna entro 50 caratteri, che non ripetono il titolo.
- [ ] Tre categorie scelte guardando la classifica reale su Amazon, non a intuito.
- [ ] Titolo e sottotitolo identici su copertina, interno e scheda: una differenza
      anche minima è motivo di blocco della pubblicazione.
- [ ] Nome autore identico ovunque (anche l'ordine nome/cognome).

## 5. Dichiarazioni obbligatorie

- [ ] **Contenuto generato con IA**: alla domanda del modulo KDP, dichiarare il
      testo come generato con intelligenza artificiale. Vale anche per copertina
      e immagini se prodotte con IA. La dichiarazione è interna ad Amazon, non
      compare sulla scheda prodotto e non impedisce la pubblicazione.
- [ ] **Diritti**: dichiarare di essere titolare dei diritti sull'opera.
- [ ] **Contenuti per adulti**: rispondere in modo veritiero.

## 6. Prezzo

- [ ] Costi di stampa riverificati su KDP e aggiornati in
      `config/printing_costs.json` (campo `verificato_il`).
- [ ] Prezzo ≥ prezzo minimo calcolato (sotto, KDP rifiuta la pubblicazione).
- [ ] Royalty per copia nota e accettabile, marketplace per marketplace.
- [ ] Verificato il prezzo dei libri comparabili nella stessa categoria.

## 7. Dopo il caricamento

- [ ] Usare l'**anteprima di stampa** di KDP e sfogliarla tutta: è l'unico
      controllo che mostra il file come lo vedrà la stampante.
- [ ] Ordinare una **copia di prova** prima di promuovere il libro.
- [ ] Se pubblichi anche l'ebook, collegarlo all'edizione cartacea.

---

## Limiti operativi da conoscere

- KDP limita il numero di titoli caricabili nello stesso giorno da uno stesso
  account (indicativamente 3). Non aggirare il limite con più account: è motivo
  di chiusura.
- Amazon rimuove i titoli giudicati di scarsa qualità o duplicati. Serie di libri
  quasi identici, rigenerati cambiando due parole, finiscono lì.
- L'ISBN gratuito fornito da KDP vincola la distribuzione ad Amazon. Un ISBN
  proprio (in Italia: Agenzia ISBN) consente di distribuire altrove con lo
  stesso codice.
- Le modifiche a un libro già pubblicato richiedono una nuova revisione e
  qualche giorno prima di diventare visibili.

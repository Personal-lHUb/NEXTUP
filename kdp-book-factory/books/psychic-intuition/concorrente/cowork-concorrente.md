# Cowork · pagina del concorrente — psychic-intuition

Ruolo: concorrente

Richiesta della fabbrica per Cowork, con le regole di
`kdp-book-factory/config/leggimi-cowork.md`.
La risposta va in `cowork-concorrente-risposta.md`, accanto a questo file,
sul ramo `claude/dreamy-archimedes-hf8w45`, con la stessa numerazione.
Per ogni punto: il fatto visto sulla pagina, l'URL, la data e l'ora.
Se una pagina chiede un captcha o l'accesso e non si riesce ad andare avanti,
scrivilo invece di stimare: l'accesso non lo fai tu.

Un libro nuovo nasce contro questo: ASIN B0B6NY89RB, su amazon.com. Serve
la sua pagina Amazon, che dal container della fabbrica non si raggiunge.

Prima di cominciare: dal pulsante «Deliver to» di amazon.com imposta un
indirizzo degli Stati Uniti (per esempio 10001), così prezzi e
disponibilità sono quelli del mercato, in USD. Alla fine rimetti
l'indirizzo com'era. Non serve l'accesso a nessun account.

1. **Scheda.** Apri https://www.amazon.com/dp/B0B6NY89RB e riporta,
   copiandoli dalla pagina: titolo e sottotitolo, autore, formato, prezzo del
   cartaceo e dell'eBook in USD, e dal riquadro «Product details»
   pagine, editore, data di pubblicazione e dimensioni.
   Se l'ASIN apre l'edizione Audible o Kindle, passa dal selettore dei formati
   al cartaceo («Paperback», o «Hardcover» se manca) e da lì in poi riporta i
   dati di quello, con il suo ASIN o ISBN-10: è il formato con cui il libro
   nuovo compete. Se il cartaceo non esiste, scrivilo e resta sull'edizione
   aperta.
2. **Classifica.** La riga «Best Sellers Rank» intera: la posizione in Books e
   quella in ciascuna categoria, con il percorso della categoria.
3. **Descrizione.** Il testo completo, alla lettera (apri «Read more»).
4. **Indice.** Se c'è l'anteprima («Look inside»), i titoli dei capitoli come
   appaiono nell'indice. Se non c'è, scrivi «nessuna anteprima».
5. **Recensioni.** Voto medio, numero di valutazioni e la ripartizione per
   stelle. Poi le recensioni alla lettera, con stelle, titolo e data: tutte
   quelle da 1, 2 e 3 stelle che riesci ad aprire (filtro per stelle), e
   almeno dieci da 4 e 5 stelle. Non riassumerle: la fabbrica cita le parole
   esatte di chi ha pagato il libro, e un riassunto non si può citare.
6. **Copertina.** Descrivi la copertina come appare in miniatura nei
   risultati di ricerca: colore dominante, che cosa mostra l'immagine,
   quanto spazio prende il titolo e se si legge, bollini o cifre. Senza
   riportare titolo e autore. Non serve l'immagine.
7. **Vicini di scaffale.** I primi cinque libri cartacei che la pagina
   propone fra i prodotti collegati: titolo, prezzo, pagine, voto e numero di
   valutazioni.

Chi usa i risultati:
- i punti 1-5 vanno in `concorrente/pagina.md`, che leggono `scheda-concorrente`
  e `analista-recensioni`;
- il 6 va in `concorrente/copertina.md`, per il brief di copertina;
- i vicini di scaffale vanno al `posizionamento`, per prezzo e pagine.

Li applica la sessione della fabbrica.

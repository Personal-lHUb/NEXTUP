<!-- agente: indice · Indice: titoli dopo le correzioni · 2026-10-10 08:59:21 UTC -->

Libro `b0gjr36xwt`, cartella `/home/user/NEXTUP/kdp-book-factory/books/b0gjr36xwt/`. Il libro è stato corretto dopo il collegio; ora tocca ai titoli dell'indice.

Leggi `manuale/indice.json` (i titoli attuali, decisi da te in fase 1: i capitoli veri numerati da 1 a 25, l'introduzione esclusa, e le quattro parti con il loro primo capitolo), `outline.json`, la sezione «Dopo le correzioni» di `revisioni/piano-correzioni.md` e, in `revisioni/lettore-cieco.md`, i rilievi che riguardano l'indice e le parti. I capitoli sono in `manuscript/NN.md` (il numero del file è quello della sezione: `04.md` è il capitolo 3 dell'indice). Non leggere niente in `concorrente/`.

Il tuo campo, e solo quello: il testo dell'indice. Due cose da rivedere:
1. il capitolo 3, «Where Claims Against NPs Actually Begin»: un titolo senza «Actually» e senza promettere numeri, graduatorie o una mappa completa dei reclami, che dica quello che il capitolo fa davvero (leggilo);
2. i titoli della Parte II (capitoli 8-14) e della Parte III (capitoli 15-22), perché ognuno copra tutti i capitoli che contiene: oggi «The Workup Under Pressure» non copre la prescrizione e l'incontro ostile, e «Refusals, Exits, and Aftermath» non copre i passaggi di consegne e la televisita. I confini delle parti restano dove sono.
Tutti gli altri titoli restano identici, salvo un difetto che tu giudichi grave: in quel caso cambialo e dillo nelle note.

Consegna: un oggetto JSON con la stessa forma di `manuale/indice.json` (`chapters` con tutti i 25 capitoli, `parts` con le quattro parti, `notes` con il perché di ogni titolo cambiato), nel file `/home/user/NEXTUP/kdp-book-factory/books/b0gjr36xwt/consegne/indice-fase5.json`; poi rispondi con una riga sola: il percorso e quali titoli hai cambiato. Se non hai lo strumento Write, rispondi invece con l'oggetto JSON intero.

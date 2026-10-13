<!-- agente: editor · Ultimi ritocchi a lunghezza invariata · 2026-10-13 06:45:58 UTC -->

Libro `b0gjr36xwt`, cartella `/home/user/NEXTUP/kdp-book-factory/books/b0gjr36xwt/`. Ultimi ritocchi di frase.

Leggi `revisioni/editor-sviluppo-verifica-3.md`. Applica i rilievi E1-E6 e anche la «Nota» finale: per quella cambia solo la frase del capitolo 10 («Written with the whole chain in it, the same call reads:»). Il rapporto propone una soluzione per ciascuno; seguila. Il testo è in `manuscript/NN.md`. Non leggere niente in `concorrente/`.

Vincolo d'impaginazione, decisivo. Il libro è appena stato impaginato senza nessuna pagina corta. Molte delle frasi da correggere sono proprio quelle aggiunte per riempire una pagina: E1 nel 17, E2 nel 09, E4 nel 23, E5 nel 12. Quindi **ogni capoverso che tocchi deve restare entro ±2 parole dalla sua lunghezza attuale**. Se una soluzione del rapporto accorcia (E4, E5, E2), recupera le parole nello stesso capoverso, con sostanza coerente col caso, senza fatti nuovi e senza ripetere quello che il capitolo dice già. Per E1 la soluzione è mettere la nuova valutazione nella nota di Carmen e tenere il commento; anche lì, la nota e il commento restano ognuno entro ±2 parole.

Il tuo campo, e solo quello: questi ritocchi. Usa la voce del libro, inglese americano piano. Non toccare le righe `# ` dei titoli né gli elenchi «What the note must contain».

Consegna: una lista JSON di sostituzioni `[{"sezione": N, "trova": "…", "sostituisci": "…"}, …]` nel file `/home/user/NEXTUP/kdp-book-factory/books/b0gjr36xwt/consegne/editor4-sostituzioni.json`. Il `trova` è un capoverso intero copiato alla lettera da `manuscript/NN.md` e deve comparire una volta sola nel suo file. Poi rispondi con una riga: il percorso e, per ogni voce, la differenza di parole.

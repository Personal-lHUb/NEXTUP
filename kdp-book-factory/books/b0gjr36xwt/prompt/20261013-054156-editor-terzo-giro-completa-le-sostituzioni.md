<!-- agente: editor · Terzo giro: completa le sostituzioni · 2026-10-13 05:41:56 UTC -->

Libro `b0gjr36xwt`, cartella `/home/user/NEXTUP/kdp-book-factory/books/b0gjr36xwt/`. Terzo giro, solo ritocchi di frase. Un primo tentativo si è fermato per un limite d'uso dopo aver scritto `consegne/editor3-sostituzioni.json`, una lista di 20 sostituzioni. Il tuo lavoro è verificarla e completarla, non rifarla da capo.

Leggi `revisioni/editor-sviluppo-verifica-2.md`, con i rilievi A2, A3, D1, D2, D3 e D4. Poi leggi la lista esistente e i capitoli in `manuscript/NN.md`. Non leggere niente in `concorrente/`.

1. Controlla che la lista copra tutti i rilievi. Nel D1 mancano almeno le etichette dei secondi casi: la coppia «Wendy Cho's visit, invented like Holly's» (14) / «Mr. Carver's visit is invented too.» (15) va resa diversa nella forma, e nel 17 c'è «no more real than the first» subito dopo un'etichetta di finzione. Cerca con Grep se manca altro.
2. Controlla che le etichette nuove rispettino le regole. Al massimo una frase «No real … behind» in tutto il libro. Non più di due etichette costruite come elenco di tre nomi o luoghi. Nessuna formula ripetuta fra due capitoli, contando anche quelle che restano nel testo. Correggi le voci della lista che non le rispettano.
3. Controlla ogni voce. Il `trova` deve comparire alla lettera, una volta sola, nel suo `manuscript/NN.md`. Due voci non devono toccare lo stesso brano. Il `sostituisci` deve tenere la voce del libro e non riscrivere niente oltre il rilievo.

Il tuo campo, e solo quello: questi ritocchi. Non toccare le righe `# ` dei titoli né gli elenchi «What the note must contain». Ogni capitolo resta entro l'1% della lunghezza attuale.

Consegna: riscrivi la lista intera e corretta, sempre come `[{"sezione": N, "trova": "…", "sostituisci": "…"}, …]`, nello stesso file `/home/user/NEXTUP/kdp-book-factory/books/b0gjr36xwt/consegne/editor3-sostituzioni.json`. Poi rispondi con una riga: quante sostituzioni ci sono in tutto e quante ne hai aggiunte o cambiate.

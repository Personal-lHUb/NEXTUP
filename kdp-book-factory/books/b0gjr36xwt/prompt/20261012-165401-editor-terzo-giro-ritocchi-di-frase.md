<!-- agente: editor · Terzo giro: ritocchi di frase · 2026-10-12 16:54:01 UTC -->

Libro `b0gjr36xwt`, cartella `/home/user/NEXTUP/kdp-book-factory/books/b0gjr36xwt/`. Terzo giro, solo ritocchi di frase.

Leggi `revisioni/editor-sviluppo-verifica-2.md`: applica tutti i rilievi aperti e i difetti nuovi, cioè A2, A3, D1, D2, D3 e D4, con le soluzioni che il rapporto propone. Il testo da correggere è in `manuscript/NN.md`; per il resto del libro leggi gli altri file della stessa cartella. Non leggere niente in `concorrente/`.

Su D1 decidi tu le etichette del caso inventato, ma rispetta queste regole. Al massimo una frase «No real … behind» in tutto il libro. Non più di due etichette costruite come elenco di tre nomi o luoghi. Nessuna formula ripetuta fra due capitoli. Varia anche la sintassi: un'etichetta può nominare solo il caso, oppure attaccarsi a un'altra frase. Prima di scegliere, controlla con Grep tutte le etichette dei capitoli 01-23 e quelle dei secondi casi. Vale lo stesso per D2 e D3: ogni frase nuova deve essere diversa per forma da quelle dei capitoli vicini.

Il tuo campo, e solo quello: questi ritocchi. Niente altro va riscritto. Non toccare le righe `# ` dei titoli né gli elenchi «What the note must contain». Usa la voce del libro, inglese americano piano. Ogni capitolo resta entro l'1% della lunghezza attuale.

Consegna: una lista JSON di sostituzioni, ognuna `{"sezione": N, "trova": "…", "sostituisci": "…"}`, nel file `/home/user/NEXTUP/kdp-book-factory/books/b0gjr36xwt/consegne/editor3-sostituzioni.json`. N è il numero del file (`06.md` → 6). `trova` è un brano copiato alla lettera da `manuscript/NN.md`, abbastanza lungo da comparire una volta sola nel suo file (una frase intera, al massimo un capoverso). `sostituisci` è lo stesso brano corretto. Il comando che le applica rifiuta tutto se un `trova` non compare esattamente una volta. Poi rispondi con una riga: il percorso e quante sostituzioni per rilievo.

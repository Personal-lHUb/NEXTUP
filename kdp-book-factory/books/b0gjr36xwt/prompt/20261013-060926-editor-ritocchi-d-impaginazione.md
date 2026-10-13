<!-- agente: editor · Ritocchi d'impaginazione · 2026-10-13 06:09:26 UTC -->

Libro `b0gjr36xwt`, cartella `/home/user/NEXTUP/kdp-book-factory/books/b0gjr36xwt/`. Ritocchi d'impaginazione: le misure le ha già prese il comando, a te tocca il testo.

Leggi `revisioni/ritocchi-impaginazione.md` e seguilo alla lettera. Ci sono tre tipi di ritocco:
- pagine corte: allunghi del numero di righe indicato il capoverso che chiude la pagina;
- pagina 163: accorci la voce d'elenco, identica nel 14 e nel 25;
- code di capitolo: accorci il 02 e il 04 di almeno le righe indicate.
Una riga piena è di circa 12 parole: conta le parole che aggiungi o togli. Il testo è in `manuscript/NN.md`; per sapere che cosa è già detto altrove leggi gli altri capitoli. Il rapporto `revisioni/editor-sviluppo-verifica-2.md` elenca le formule da non ripetere. Non leggere niente in `concorrente/`.

Il tuo campo, e solo quello: questi ritocchi. Quello che aggiungi è sostanza del capitolo, mai riempitivo, mai un fatto clinico o legale nuovo, mai una formula usata altrove nel libro. Usa la voce del libro, inglese americano piano. Non toccare le righe `# ` dei titoli. Gli elenchi «What the note must contain» restano invariati, salvo la sola voce del 14 indicata, che cambia identica nel 25.

Consegna: una lista JSON di sostituzioni `[{"sezione": N, "trova": "…", "sostituisci": "…"}, …]` nel file `/home/user/NEXTUP/kdp-book-factory/books/b0gjr36xwt/consegne/ritocchi-impaginazione.json`. Il `trova` è un capoverso intero copiato alla lettera da `manuscript/NN.md` e deve comparire una volta sola nel suo file. Il `sostituisci` è lo stesso capoverso ritoccato. Poi rispondi con una riga: il percorso e, per ogni voce, le parole aggiunte o tolte.

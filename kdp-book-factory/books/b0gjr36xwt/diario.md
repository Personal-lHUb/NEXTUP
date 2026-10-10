# Diario di lavorazione

Una riga per passo, in ordine, scritta dai comandi e dagli hook di Claude Code
(`kdpfactory/diario.py`). Non si modifica a mano: si aggiunge.

- 2026-10-10 08:30 UTC · diario aperto. Fase 5: sezioni 1-23 corrette e importate (commit aef2934); disclaimer in book.json; proposte all'autore in attesa: prezzo 21.99, formato 6x9. Prossimo: editor sulla consultazione 24-26 con consegna in file
- 2026-10-10 08:31 UTC · lanciato `editor` «Correzioni sezioni 24-26» → `prompt/20261010-083122-editor-correzioni-sezioni-24-26.md`
- 2026-10-10 08:31 UTC · `editor` «Correzioni sezioni 24-26» in background, id `a1c744d11a6516abf`
- 2026-10-10 08:34 UTC · note in riquadro attive (quote_box), commit 214866f; capoversi delle note separati per tutti i libri
- 2026-10-10 08:56 UTC · finito `editor` (id `a1c744d11a6516abf`): uscita lunga salvata in `consegne/20261010-085625-editor-a1c744d1.md`
- 2026-10-10 08:58 UTC · tolta la riga delle 08:34 di un agente interno senza tipo («Confermo 6x9 e prezzo 21,99»): era il suggerimento automatico del prossimo messaggio, non una risposta dell'autore. Formato e prezzo restano in attesa. L'hook ora ignora gli agenti senza tipo
- 2026-10-10 08:58 UTC · consegna `20261010-085625-editor-a1c744d1.md` importata: sezioni 24, 25, 26 (backup /home/user/NEXTUP/kdp-book-factory/backup/b0gjr36xwt/consegne/20261010-085836)
- 2026-10-10 08:58 UTC · fase 5: sezioni 24-26 importate; tutte le 26 sezioni corrette. I titoletti del frasario (24) ripetono i titoli dei capitoli: se l'agente indice li cambia (4, forse 5), vanno allineati
- 2026-10-10 08:59 UTC · lanciato `indice` «Indice: titoli dopo le correzioni» → `prompt/20261010-085921-indice-indice-titoli-dopo-le-correzioni.md`
- 2026-10-10 08:59 UTC · `indice` «Indice: titoli dopo le correzioni» in background, id `a2c6e9bb2f62570e1`
- 2026-10-10 17:20 UTC · finito `indice` (id `a2c6e9bb2f62570e1`): fermato dal limite di sessione (azzeramento 13:00 UTC) prima di consegnare; nessun promemoria programmato. Da rifare quando l'autore lo fa partire: l'agente indice (prompt in prompt/20261010-085921-…), poi consegna --indice, build, impaginazione, editor di sviluppo
- 2026-10-10 17:20 UTC · regola nuova dell'autore: ogni passo lo fa partire lui; niente si programma; al limite d'uso ci si ferma e si aspetta il suo «continua»
- 2026-10-10 17:21 UTC · correzione: l'agente indice aveva scritto la consegna prima del limite (consegne/indice-fase5.json, completa: 25 capitoli, 4 parti, note). Non applicata: aspetta il via dell'autore (consegna b0gjr36xwt indice-fase5.json --indice)

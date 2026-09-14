# NEXTUP — istruzioni per Claude Code

## Regola permanente: copia di backup di ogni file generato

**Ogni file prodotto deve avere una copia in una cartella di backup.** Vale per
la pipeline e per qualsiasi file generato a mano in una sessione.

- **Pipeline `kdp-book-factory`**: lo fa da sé (`kdpfactory/backup.py`). Ogni
  comando che scrive file lascia uno snapshot datato in
  `kdp-book-factory/backup/<slug>/<AAAAMMGG-hhmmss>/` con scheda del libro,
  scaletta, manoscritto e tutto `build/`. Non passare `--no-backup` se non è
  l'utente a chiederlo.
- **File generati fuori dalla pipeline** (script, export, documenti, immagini,
  configurazioni, risultati di analisi): copiarli subito in
  `backup/manuale/<AAAAMMGG-hhmmss>/`, mantenendo i percorsi relativi.
- **Prima di sovrascrivere o cancellare** un file generato in precedenza: copia
  di sicurezza forzata, anche se un backup recente esiste già.
- `backup/` non entra in git (contiene PDF e cresce in fretta): resta sul disco.
  Per liberare spazio: `python3 -m kdpfactory backup <slug> --prune 10`.

## Il progetto

`kdp-book-factory/` è una pipeline che produce libri completi (60-240 pagine)
pronti per Amazon KDP: interno PDF, copertina full-wrap, EPUB, scheda prodotto.
Il libro passa da un collegio di agenti (stesura + controllo, fra cui un lettore
cieco, un fact-checker, la conformità e il controllo di impaginazione).

- Documentazione: `kdp-book-factory/README.md` e `kdp-book-factory/docs/`.
- Test: `cd kdp-book-factory && python3 -m unittest discover -s tests`
  (nessun test fa chiamate di rete).
- Lint: `ruff check kdpfactory tests` dalla stessa cartella.
- Per provare la pipeline senza spendere token: `--dry-run`.
- Il testo dei libri e la documentazione del progetto sono in italiano.

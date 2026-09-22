# Materiali dell'autore

## Immagine di copertina

Metti qui il file e chiamalo `copertina` (l'estensione può essere .jpg, .jpeg,
.png, .webp, .tif):

    assets/copertina.jpg

Viene raddrizzata, ritagliata sulle proporzioni esatte della prima di copertina
(abbondanza inclusa), portata a 300 DPI e ripulita (contrasto, colore, nitidezza
leggeri). Il risultato finisce in `build/<slug>-copertina-immagine.jpg` e la
copertina lo usa come sfondo, con una velatura scura in alto e in basso perché
titolo e nome dell'autore restino leggibili.

**Risoluzione minima**: per un 6x9 pollici servono circa 1838x2775 pixel.
Sotto i 200 DPI reali il controllo qualità blocca il libro: in stampa si vede.

Per scegliere invece una copertina solo tipografica, senza immagine, imposta
`"cover_style": "tipografica"` in `book.json`.

## Altri file

Qualsiasi altra cosa metti qui (foto dell'autore, appunti, scansioni) viene
conservata e inclusa nelle copie di backup, ma non entra automaticamente nel
libro.

# Font

Copia qui i file `.ttf` che vuoi usare per i tuoi libri: hanno la precedenza sui
font di sistema. Servono le quattro varianti, con questi nomi:

```
<Nome>-Regular.ttf   <Nome>-Bold.ttf   <Nome>-Italic.ttf   <Nome>-BoldItalic.ttf
```

I nomi riconosciuti sono elencati in `kdpfactory/typography.py`
(`FONT_CANDIDATES`): aggiungi lì la tua quaterna se usa un nome diverso.

Verifica sempre che la licenza consenta l'incorporamento in PDF destinati alla
stampa commerciale. Scelte sicure e gratuite (licenza SIL OFL): EB Garamond,
Libre Baskerville, Crimson Pro, Source Serif 4, Alegreya.

I file di font messi qui non vengono versionati (`.gitignore`).

## `ofl/`: i font che il progetto porta con sé

La sottocartella `ofl/` è diversa: contiene font a licenza SIL OFL che **sono**
versionati, perché il contenitore in cui gira la fabbrica si ricrea da zero a
ogni sessione e un font che non sta nel repository sparisce. Oggi c'è solo
**Barlow Condensed Bold**, il condensato dei titoli di copertina
(`docs/copertine.md`), con la sua licenza accanto (`OFL-BarlowCondensed.txt`).
La licenza OFL consente l'incorporamento nei PDF e la redistribuzione, purché la
licenza viaggi con il file.

I font in `fonts/` hanno la precedenza su quelli di `ofl/`.

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

I file di font non vengono versionati (`.gitignore`).

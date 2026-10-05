# Il progetto ChatGPT — NEXTUP — Immagini

<!-- Scritto da `python3 -m kdpfactory cowork progetto`. Non si modifica a mano:
     le regole stanno in kdpfactory/richiesteimmagini.py, e si rigenera. -->

Un progetto in ChatGPT per tutte le immagini dei libri NEXTUP. Le regole che
valgono per ogni libro stanno nelle istruzioni del progetto, scritte una volta.
Il brief di ogni lavoro arriva come file allegato alla sua chat, e lo scrive il
sistema: il prompt di un'immagine non si scrive a mano.

## 1. Il progetto

Nome: **NEXTUP — Immagini**. Istruzioni del progetto, da incollare così:

```
You make the illustrations for books produced by the NEXTUP book factory: front
cover art and interior figures for paperback books sold on Amazon KDP.

Every chat in this project is one job for one book. The brief for that job is
the file attached to the first message. Follow that brief, and do not carry over
the style, palette or subject of another chat unless the brief asks for it.

Rules for every image:
1. Illustration only. No text of any kind in the image: no title, letters,
   numbers, labels, signatures, logos or watermarks. The book's own software
   sets every word afterwards, in vector.
2. Use the brief as the prompt, as written. Do not rewrite it into a prompt of
   your own. If something in it cannot be done, say so before generating,
   instead of changing it silently.
3. Covers: portrait 2:3, at the largest size you can produce. Keep the upper
   third calm: the title goes there.
4. Interior figures: grayscale only. Two elements must never differ by colour
   alone, because the book prints in black and white.
5. Originality: never imitate an existing book cover, artist, character, brand
   or logo, and never show a recognisable real person.
6. One image per message. When the brief asks for several variants, make them
   differ in composition, not just in colour.
7. After every image, state its exact size in pixels and the model that made
   it: Amazon asks authors to disclose AI-generated content. If the image is
   smaller than the minimum in the brief, deliver it anyway and say so.
```

- **Memoria**: se ChatGPT chiede quale usare, quella limitata al progetto. Un
  libro non deve prendere lo stile di un altro.
- **File del progetto**: nessuno. Il brief va allegato alla chat del suo libro:
  caricato nei file del progetto lo vedrebbero tutte le chat, e due libri si
  mescolerebbero.

## 2. Una chat per lavoro

| lavoro | nome della chat | file da allegare | lo scrive |
|---|---|---|---|
| copertina | `<slug> — copertina` | `books/<slug>/build/copertina-chatgpt.md` | `kdpfactory copertina <slug>` |
| figure dell'interno | `<slug> — figure` | `books/<slug>/build/immagini-chatgpt.md` | `kdpfactory immagini <slug>` |

Primo messaggio, con il file allegato: «Follow the attached brief. First variant.»
Poi, per ogni variante: «Next variant.» Per le figure: «Next figure.»

## 3. Dove vanno le immagini

Ogni immagine si scarica alla risoluzione piena (non l'anteprima) e si salva
nella cartella Drive «NEXTUP — corriere Cowork», con il nome che il file allegato indica in
fondo, per esempio `books__<slug>__assets__copertina-1.png`. Il giro orario la
porta nel libro da sola; l'agente `copertina` misura le varianti e propone
quella da usare, con il silenzio-assenso.

## 4. Cowork

Il ruolo `immagini` di Cowork lavora nello stesso progetto, se c'è: lo dice il
LEGGIMI. Che la copertina la generi l'autore o Cowork, il file allegato è lo
stesso, e vale la prima serie di varianti che arriva sul corriere.

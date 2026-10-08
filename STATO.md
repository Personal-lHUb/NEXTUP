# Stato della fabbrica

Aggiornato l'8 ottobre 2026. Si aggiorna alla fine di ogni sessione: chi apre la
sessione dopo parte da qui.

## Il libro in corso

**`b0gjr36xwt`**: *Hard Calls, Clear Notes: The NP Casebook of Defensible
Documentation*, di Dana Ellery. Full-content, inglese, amazon.com, 176 pagine,
21,99 USD. Libro per nurse practitioner sulla documentazione difendibile,
scenario per scenario (differenziale, risultati anomali, consulente che non
arriva, capacità decisionale, dimissioni contro parere, televisita,
prescrizione). Concorrente: B0GJR36XWT, *Chart Like a Lawyer* (Jaime Weiland,
138 pagine): promette anche agli NP ma, secondo una recensione, serve solo gli RN.

- **Fase 0 chiusa** (8 ottobre). Amazon non si raggiunge dal container, quindi
  la pagina del concorrente (`concorrente/pagina.md`) è stata compilata dalla
  ricerca web, con le fonti. Uscite dei quattro agenti in `concorrente/`
  (`scheda`, `lacune`, `piano`, `originalita`), poi `concorrente importa`:
  `book.json` e `brief.md`. Originalità: zero bloccanti. Le due minori
  (parole chiave che promettevano un esito, sottotitolo che faceva pensare a un
  autore NP) sono corrette nel piano. Il sottotitolo in `book.json` mette «NP»
  prima del taglio a 60 caratteri. La linea editoriale è in `notes`.
- **Debolezze dichiarate**: le lacune hanno confidenza bassa (cinque recensioni
  di Goodreads, nessuna di Amazon). Le sette parole chiave non hanno volumi
  verificati. Le categorie KDP sono ricostruite. Si verificano alla scheda
  prodotto (fase 6), o prima, se Cowork torna.
- **Decisioni dell'autore in silenzio-assenso** (`decisioni.json`): categoria,
  titolo, promessa, prezzo, pseudonimo. Scadono il **9 ottobre alle 05:55 UTC**.
  Una risposta dell'autore vince sempre (`decisioni b0gjr36xwt --scegli … --valore …`).
- **Prossimo passo: fase 1**, in una sessione nuova: `architetto` (scaletta e
  piano delle figure) → `indice` → `manuale b0gjr36xwt scaletta --esamina`.
  `produzione` la dà ferma finché le decisioni non scadono o non arriva la
  risposta.
- L'uscita di un agente si salva con
  `python3 -m kdpfactory trascrizione <id-agente> <file.json>`, con
  `--etichetta SCALETTA` / `FIGURE` per l'architetto.

## Routine e Cowork

- **Tutte le routine sono spente** (8 ottobre, su richiesta dell'autore): la
  fabbrica «Produzione NEXTUP» e le cinque attività di Cowork. Si lavora quando
  l'autore scrive.
- Le attività di Cowork sul portatile hanno ancora il **prompt vecchio, quello
  di Drive**: prima di riaccenderle, l'autore approva in una conversazione Cowork
  sul portatile i prompt nuovi di `kdp-book-factory/config/attivita-cowork.json`.
- Restano aperte per b0gjr36xwt: `cowork-concorrente.md` (le recensioni Amazon
  da 2-3 stelle servirebbero a verificare il lettore NP),
  `cowork-parole-chiave.md` e `cowork-copertine-categoria.md` (lo studio delle
  copertine serve alla fase 7).
- Nessuna consegna col canale nuovo (`fire_trigger` con la risposta nel testo) è
  ancora arrivata: non è dimostrato che Cowork abbia lo strumento.

## In sospeso, non bloccante

- **CDN di Higgsfield bloccata** dalla rete del container (403): per scaricare
  le immagini generate servono i domini nelle impostazioni dell'ambiente
  (`docs/cowork.md`, «Le immagini»).
- **Richiesta aperta di sistema** `config/cowork-kdp-3.md` (regole KDP, serve
  l'accesso a KDP).
- I cinque libri precedenti sono stati eliminati il 7 ottobre su richiesta
  dell'autore: copie in `backup/manuale/20261007-143226/` (solo su questo disco) e
  nella storia di git.

# Stato della fabbrica

Aggiornato il 14 ottobre 2026. Si aggiorna alla fine di ogni sessione: chi apre la
sessione dopo parte da qui.

## Il libro in corso

**`b0gjr36xwt`**: *Hard Calls, Clear Notes: The NP Casebook of Defensible
Documentation*, di Dana Ellery. Full-content, inglese, amazon.com, 6×9, 180
pagine, 21,99 USD. Libro per nurse practitioner sulla documentazione difendibile,
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
- **Decisioni dell'autore** (`decisioni.json`): categoria full-content, titolo,
  promessa e pseudonimo **scelti dall'autore** l'8 ottobre; il 13 ottobre il
  formato (6×9, quello del concorrente), il prezzo (21,99 USD) e la copertina
  (direzione 1, variante finale 3). Nella biografia resta «The author is not a
  clinician», per sua scelta.
- **Fase 1 chiusa** (8 ottobre). Scaletta dell'architetto: 25 capitoli in
  quattro parti (principi; workup; rifiuti, uscite e dopo; consultazione con
  frasario, elenchi per scenario e glossario), più l'introduzione. Nessuna
  figura (`figure.json`, `servono: false`): le note rendono meglio come testo
  composto. Titoli dell'agente `indice` in `manuale/indice.json`, applicati alla
  scaletta. Revisore: zero bloccanti, zero importanti (una minore, falsa: due
  «one» in quarta che non sono quantità). `include_conclusion: false` in
  `book.json`: la conclusione sarebbe caduta dopo il glossario. `outline.json`:
  26 sezioni, circa 44.700 parole, ~1.750 per capitolo.
- Correzione del motore emersa qui: il posizionamento scriveva i temi del brief
  in italiano per un libro in inglese, e il revisore dava 12 bloccanti falsi.
  Ora il prompt chiede la lingua del libro e il revisore dà un bloccante solo,
  «brief in un'altra lingua». I temi di questo libro sono stati tradotti.
- **Fase 2 chiusa** (8 ottobre). La voce del capitolo 1 è stata scelta
  dall'autore per tutto il libro. 26 sezioni scritte e importate, 47.700 parole;
  il libro intero in un file è `manoscritto-completo.md`. Prima parte in fila,
  seconda e terza in due flussi paralleli (cognomi A-L e M-Z per non avere
  personaggi doppi), consultazione per ultima. Lo «Scenario Finder» è il 53%
  sopra budget perché riporta alla lettera gli elenchi dei capitoli: voluto.
- **Fase 3, prima impaginazione di lavoro** in 6×9: 176 pagine
  (intervallo 167-185). Impaginazione: 0 bloccanti, 0 importanti, 3 minori.
  **Il formato definitivo lo decide l'autore** dopo il confronto coi
  concorrenti (`concorrente/ricerca-web-vetrina.md`: 6×9 per i libri da leggere,
  8,5×11 per le raccolte di modelli).
- **Fase 4 chiusa**: lettore cieco (libro e vetrina), editor di sviluppo, tre
  fact-checker (sezioni 1-8, 9-16, 17-26), conformità; rapporti in `revisioni/`,
  decisioni per rilievo in `revisioni/piano-correzioni.md`.
- **Fase 5, correzioni, in corso** (10 ottobre). Sezioni 1-23 corrette
  dall'editor (tre per agente, in parallelo) e importate in `manuale/` e nel
  manoscritto; aperture variate, nomi doppi tolti, ordini legali resi prassi.
  Disclaimer della conformità in `book.json` (il motore ora stampa
  un'avvertenza a paragrafi e tiene il colophon su una pagina). **Restano**: la
  parte di consultazione (24 frasario, 25 elenchi per scenario, 26 glossario con
  le fonti), per ultima perché riporta i capitoli; poi l'agente `indice` (titolo
  del capitolo 4 senza «Actually», forse anche il 5), build, impaginazione,
  verifica dell'editor di sviluppo sui capitoli corretti, `manoscritto-completo.md`
  da rigenerare.
- **Aggiornamento 11 ottobre.** Fatti: sezioni 24-26, titoli dell'agente
  `indice` (cap. 3 «Where a Claim, a Complaint, and a Review Begin», parti II
  «Orders, Waits, and Pushback» e III «Choices, Continuity, and Aftermath»),
  note in riquadro, build a 178 pagine, `qa` 0 errori (3 avvisi), impaginazione
  0 bloccanti (3 minori), `manoscritto-completo.md` rigenerato. **Verifica
  dell'editor di sviluppo** (`revisioni/editor-sviluppo-verifica.md`): 1
  bloccante (A1: l'introduzione numera i capitoli dalla scaletta, non dall'indice
  stampato), 4 importanti (A2 frase che introduce la riscrittura in otto
  capitoli, N1 etichetta «caso costruito» sempre in chiusa di primo paragrafo,
  N2 «N months into» in otto capitoli, N3 dieci rimandi del glossario al cap. 3
  con un titolo che non esiste), 8 minori. **La fase 5 non è chiusa**: il
  prossimo passo, quando lo fa partire l'autore, è un secondo giro dell'editor
  su questi rilievi, poi build e verifica.
- **Aggiornamento 13 ottobre.** Tutti i rilievi risolti in tre giri
  (`revisioni/piano-correzioni-2.md`, poi sostituzioni puntuali con `consegna
  --sostituzioni`): l'introduzione nomina le parti senza numeri, il capitolo 6
  si intitola «The Working Diagnosis and What Would Change It» (rimandi
  allineati), etichette del caso inventato e presentazioni degli NP diverse fra
  loro, glossario allineato. Ritocchi d'impaginazione
  (`revisioni/ritocchi-impaginazione.md`): **178 pagine, impaginazione 0
  rilievi, `qa` 0 errori** (2 avvisi voluti). Motore: coda dei capoversi
  misurata sulla giustezza, rapporto d'impaginazione con tutte le pagine e le
  righe da ritoccare. Verifica finale dell'editor di sviluppo
  (`revisioni/editor-sviluppo-verifica-3.md`): tutti i rilievi risolti, i 6
  minori nati dai ritocchi corretti a lunghezza invariata. **Fase 5 chiusa**
  (13 ottobre): 0 bloccanti, impaginazione 0 rilievi, `qa` 0 errori.
  Prossimo passo, al via dell'autore: fase 6, la scheda prodotto. La fase 7
  (copertina) aspetta la sua decisione sul formato.
- **Aggiornamento 13 ottobre, fasi 6 e 7.** Formato 6×9 come il concorrente
  (6 x 0.3 x 9 in, da Amazon e Bookshop.org). **Fase 6**: scheda in
  `manuale/scheda.json`, importata; conformità (`revisioni/conformita-scheda.md`)
  0 bloccanti, 4 importanti e 4 minori, tutti applicati coi testi del rapporto;
  `book.json` allineato alla scheda (parole chiave e categorie), e il motore ora
  scrive nell'EPUB le parole chiave della scheda. Build a **180 pagine** (+2: la
  pagina «About the Author»), impaginazione 0 rilievi, `qa` 0 errori. Interno,
  EPUB e scheda consegnati all'autore. **Fase 7**: tre direzioni dell'agente
  `copertina`, tre bozzetti su Higgsfield; l'autore ha scelto la 1 («coerente con
  il tema e accattivante»). Tre varianti finali dal connettore (qualità max, 4k,
  2336 × 3504 px, 45 crediti): **l'autore ha scelto la 3**. Gli indirizzi sono nel
  diario e in `build/copertina-higgsfield.json`; il motore scrive i prompt delle
  varianti in `build/copertina-varianti-prompt.json` per il connettore.
  **Ferma**: la rete del container blocca la CDN `d8j0ntlcm91z4.cloudfront.net`
  (403). Quando l'autore la abilita (Network access → Allowed domains) e dice
  «continua»: `copertina b0gjr36xwt --scarica-generate`, `--scegli 3`, `build`,
  `review --agents copertina,impaginazione`, `qa`, `diagnostica`, consegna di
  copertina PDF e pacchetto completo. In alternativa carica lui la variante 3 sul
  ramo `cowork-immagini` come `kdp-book-factory/books/b0gjr36xwt/assets/copertina-3.png`.
- **Aggiornamento 14 ottobre, verso KDP.** Scelte dell'autore: Cowork prepara
  su KDP le **bozze** del cartaceo (21,99 USD, ISBN gratuito di KDP, opaca) e
  del Kindle (7,99 USD, royalty 70%) e **non pubblica**; i file finali vanno in
  `books/b0gjr36xwt/pubblicazione/` (repository pubblico, accettato); la
  copertina arriva abilitando la CDN. Motore: `pubblicazione <slug>` (con
  `--controlla`) fa il pacchetto: interno, copertina, copertina Kindle JPG,
  EPUB, scheda, `manifest.json`, `caricamento-kdp.md`, la richiesta
  `cowork-kdp-bozza.md` (ruolo `regole-kdp`) e `prompt-cowork.md`; LEGGIMI
  versione 14 con l'eccezione «Bozze su KDP autorizzate». **Ferma sulla
  copertina** (CDN ancora 403). Al «continua» con la CDN aperta:
  `copertina b0gjr36xwt --scarica-generate`, `--scegli 3`, `build`, `review
  --agents copertina,impaginazione`, `qa`, `diagnostica`, `pubblicazione
  b0gjr36xwt`, commit e push; poi l'autore incolla `prompt-cowork.md` in Cowork
  e porta qui la risposta (`cowork corriere --ricevi`).
- **Richieste dell'autore per dopo il collegio**: se il lettore cieco dà l'OK,
  le immagini dell'interno prendendo a riferimento i libri analoghi (i box per
  le note deboli e riscritte, più quello che il confronto suggerisce, con un
  piano da proporre); la copertina come bozza a bassa risoluzione su Higgsfield,
  da far approvare all'autore (studio della categoria dalla ricerca web); il
  formato di stampa da proporre all'autore, che dà l'OK.
- `manuscript/` non entra in git: il testo consegnato sta in
  `manuale/capitolo-NN.md`. In una sessione nuova si ricostruisce con
  `manuale b0gjr36xwt capitolo --numero N --importa` per ogni sezione già
  scritta.
- L'uscita di un agente: l'agente la scrive in `consegne/<nome>.md`, poi
  `python3 -m kdpfactory consegna b0gjr36xwt <nome>.md --capitoli N …` (o
  `--in revisioni/<file>.md`). Per le uscite vecchie resta `trascrizione`.

## Contesto (10 ottobre, scelta dell'autore)

- Hook in `.claude/settings.json` (`kdpfactory/diario.py`): prompt di ogni
  agente in `books/<slug>/prompt/`, diario in `books/<slug>/diario.md`
  (lancio, id, fine, consegne importate, decisioni), risposte lunghe salvate in
  `consegne/`, guardia che lascia scrivere agli agenti solo lì. All'avvio e dopo
  ogni riassunto della chat tornano in contesto STATO.md, produzione, agenti in
  volo, consegne da importare e la coda del diario.
- Gli agenti che usano il modello hanno `Write` (solo per la consegna) e
  rispondono con una riga: la chat non si riempie di capitoli.

## Automazioni e consenso (10 ottobre, decisioni dell'autore)

- **Ogni passo lo fa partire l'autore.** Fra un suo messaggio e l'altro non
  parte niente (nemmeno i bozzetti di copertina); il compito che dà si chiude
  con commit e push, poi ci si ferma e gli si dice il passo dopo.
- **Niente si programma**: nessun `send_later`, nessuna routine, nessun lancio
  di Cowork. Le routine restano spente, non si cancellano. Un limite d'uso
  si annota nel diario, e si aspetta il suo «continua».
- **Silenzio-assenso spento**: ogni decisione d'autore aspetta la sua risposta,
  senza scadenza. In attesa ora: **prezzo** (21,99 USD, alternativa 19,99) e
  **formato** (6×9 proposto).
- Gli hook del contesto restano: registrano e rimettono in contesto, non
  avviano lavoro. Quando qualcosa aspetta l'autore: riga in chat e notifica push.
- Stamattina (10 ottobre) le cinque routine di Cowork risultano partite fra le
  08:05 e le 08:45 UTC e «Produzione NEXTUP» lanciata alle 08:55, poi di nuovo
  spente; questa sessione non le ha accese.
- Il prompt della routine «Produzione NEXTUP» parla ancora di silenzio-assenso
  e di lanci di Cowork: se l'autore la vuole riaccesa, prima va riscritto.

## Routine e Cowork

- **Tutte le routine sono spente** (8 ottobre, su richiesta dell'autore): la
  fabbrica «Produzione NEXTUP» e le cinque attività di Cowork. Verificato il 10
  ottobre. Si riaccendono solo col consenso dell'autore.
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

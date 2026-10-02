# Cowork · parole chiave della nicchia — dementia-family

Ruolo: parole-chiave

Richiesta della fabbrica per Cowork, con le regole di
`kdp-book-factory/config/leggimi-cowork.md`.
La risposta va in `cowork-parole-chiave-risposta.md`, accanto a questo file,
sul ramo `claude/dreamy-archimedes-hf8w45`, con la stessa numerazione.
Per ogni punto: il fatto visto sulla pagina, l'URL, la data e l'ora.
Se una pagina chiede un captcha o l'accesso e non si riesce ad andare avanti,
scrivilo invece di stimare: l'accesso non lo fai tu.

Un libro nuovo nasce contro l'ASIN B0GN73RYMF, su amazon.com. Prima che la fabbrica
decida titolo e parole chiave, servono le frasi che i lettori di questa nicchia
digitano davvero, con quanto sono cercate e quanto sono affollate.

Prima di cominciare: dal pulsante «Deliver to» di amazon.com imposta un
indirizzo degli Stati Uniti (per esempio 10001), così prezzi e
disponibilità sono quelli del mercato, in USD. Alla fine rimetti
l'indirizzo com'era. Non serve l'accesso a nessun account.

Helium 10 e Publisher Rocket si usano solo se l'autore ha già aperto l'accesso
nel browser: non si inseriscono credenziali, non si compra niente, non si
cambiano impostazioni. Se uno strumento non è accessibile, i suoi punti restano
vuoti e la risposta è «Esito: parziale», con il motivo. Le cifre degli
strumenti sono stime loro: si riportano come le mostrano, con il nome dello
strumento.

1. **Semi.** Apri https://www.amazon.com/dp/B0GN73RYMF (se è un'edizione Audible o
   Kindle, passa al cartaceo dal selettore dei formati). Dal titolo, dal
   sottotitolo e dalle categorie del libro ricava da cinque a otto frasi di
   partenza, di due-quattro parole, e riportale con da dove vengono.
2. **Amazon.** Per ogni seme, nella barra di ricerca di amazon.com, reparto
   Books: tutte le frasi che propone l'autocompletamento, alla lettera. Poi,
   per le 20-30 frasi più pertinenti fra semi e suggerimenti: il numero di
   risultati della ricerca con `i=stripbooks`, e i primi tre libri cartacei
   in risultato (titolo, Best Sellers Rank in Books, numero di valutazioni).
3. **Helium 10.** Cerebro sull'ASIN del cartaceo del concorrente: le prime 30
   parole chiave per volume di ricerca, con il volume stimato e la posizione
   organica del concorrente. Magnet su ciascun seme: le prime dieci frasi per
   volume.
4. **Publisher Rocket.** Keyword Search su ciascun seme, mercato Amazon
   amazon.com: ricerche mensili stimate, numero di libri in concorrenza e
   punteggio di concorrenza.
5. **Google Trends.** I tre semi principali, Stati Uniti, ultimi cinque anni:
   se l'interesse cresce, è stabile o cala, e in quali mesi è più alto.
6. **Tabella.** Una tabella unica con tutte le frasi trovate ai punti 2-4,
   senza doppioni, con le colonne: frase · autocompletamento Amazon (sì/no) ·
   risultati Amazon · volume Helium 10 · ricerche mensili Rocket ·
   concorrenza Rocket. Una cella vuota dove lo strumento non ha dato il dato.

Chi usa i risultati: il `posizionamento`, che sceglie da questa tabella le
sette parole chiave del libro e le parole del titolo. Li applica la sessione
della fabbrica.

# Cowork · verifica delle parole chiave — household-bills

Ruolo: parole-chiave

Richiesta della fabbrica per Cowork, con le regole di
`kdp-book-factory/config/leggimi-cowork.md`.
La risposta va in `cowork-verifica-parole-chiave-risposta.md`, accanto a questo file,
sul ramo `claude/dreamy-archimedes-hf8w45`, con la stessa numerazione.
Per ogni punto: il fatto visto sulla pagina, l'URL, la data e l'ora.
Se una pagina chiede un captcha o l'accesso e non si riesce ad andare avanti,
scrivilo invece di stimare: l'accesso non lo fai tu.

Il libro: «Bills in Order — A Household Guide to Paying on Time and Catching Up When You Fall Behind», su amazon.com. Le sette parole chiave e le categorie
qui sotto sono quelle della scheda che sta per essere caricata: si controlla
che ciascuna frase sia cercata davvero e quanto è affollato ogni scaffale.

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

1. **Le sette frasi.** Per ciascuna:
   - nella barra di ricerca di amazon.com, reparto Books, se l'autocompletamento
     la propone (sì, simile o no; se simile, la proposta più vicina, alla
     lettera);
   - il numero di risultati con `i=stripbooks`;
   - il volume stimato di Helium 10 (Magnet) e le ricerche mensili e la
     concorrenza di Publisher Rocket.

   - financial literacy for adults and beginners
   - living paycheck to paycheck late fees overdraft
   - how to get financially organized as a family
   - taking over accounts for an aging parent
   - how credit cards work minimum payment grace period
   - hardship programs and utility assistance
   - home paperwork filing system for financial records

2. **Le categorie.** Per ciascuna, la pagina Best Sellers di amazon.com (Books):
   il Best Sellers Rank in Books del 1° e del 20° libro cartaceo (salta le
   schede Audible e Kindle), e se fra i primi 20 prevalgono libri da leggere
   o da compilare.

   - Books > Business & Money > Personal Finance > Budgeting & Money Management
   - Books > Reference > Consumer Guides

3. **Tabella.** Le sette frasi in una tabella: frase · autocompletamento ·
   risultati Amazon · volume Helium 10 · ricerche Rocket · concorrenza Rocket.

Chi usa i risultati: la scheda del libro (`book.json` e `manuale/scheda.json`);
una frase che non regge si sostituisce, e la sostituta passa dalla conformità.
Li applica la sessione della fabbrica.

# Verifiche su Amazon da fare fuori dal container — Bills in Order

Il container cloud della fabbrica non raggiunge amazon.com né kdp.amazon.com
(il proxy le rifiuta per policy). Queste verifiche servono a chiudere la fase 6
(scheda) e la fase 8 (checklist KDP). Vanno fatte da una sessione che gira sul
computer dell'autore — Cowork nell'app Claude Desktop, oppure
`claude remote-control` in un terminale — con il browser dove l'autore ha già
fatto l'accesso a KDP. Nessuna password va scritta nella chat.

Incolla tutto quello che segue nella sessione Cowork.

---

Sto preparando un libro per Amazon KDP. Mi servono cinque verifiche su
amazon.com e su kdp.amazon.com. Non cambiare niente nel mio account KDP: non
creare titoli, non salvare bozze, non pubblicare. Solo leggere e riferire.

Il libro: «Bills in Order — A Household Guide to Paying on Time and Catching Up
When You Fall Behind», di Claire Halvorsen (pseudonimo), cartaceo 6x9, 192
pagine, in inglese, mercato amazon.com. È una guida da leggere (non un quaderno
da compilare) su come una famiglia americana tiene in ordine le bollette e che
cosa fare quando resta indietro.

1. **Selettore delle categorie KDP (cartaceo, amazon.com).** Nel flusso di un
   nuovo cartaceo, alla voce Categories, cerca se esistono queste due e con
   quale percorso esatto:
   - Business & Money > Personal Finance > Budgeting & Money Management
   - Reference > Consumer Guides

   Se una non c'è, dimmi la più vicina che c'è. Poi esci senza salvare.

2. **Quanto sono affollate.** Per ciascuna delle due categorie apri la pagina
   Best Sellers di amazon.com (Books) e annota il Best Sellers Rank assoluto del
   libro al 1° posto e di quello al 20° posto. Dimmi anche se fra i primi 20 ci
   sono soprattutto guide da leggere o quaderni/planner da compilare.

3. **Titolo già usato?** Cerca su amazon.com (Books) «Bills in Order» e
   «Bills in Order household guide». Dimmi se esiste un libro con lo stesso
   titolo o quasi, con autore e anno.

4. **Parole chiave.** Per ciascuna di queste sette frasi, scrivila nella barra di
   ricerca di amazon.com (reparto Books) e dimmi se l'autocompletamento propone
   la frase o una molto vicina (sì / simile / no), e quanti risultati dà la
   ricerca:
   - money management for beginners personal finance
   - avoid late fees overdraft charges missed payments
   - organize monthly expenses subscriptions utilities
   - handling an aging parent's accounts and utilities
   - can't afford rent or mortgage what are my options
   - how credit card minimum payment grace period works
   - home paperwork filing system for financial records

5. **Il concorrente.** Apri https://www.amazon.com/dp/B0CSSJMQP1 e dimmi prezzo
   del cartaceo, numero di pagine, Best Sellers Rank con le sue categorie, voto
   medio e numero di recensioni di oggi.

Rispondi con un elenco numerato 1–5, solo i fatti che hai visto sulla pagina,
e per ogni punto la data e l'ora della verifica. Se una pagina chiede un
captcha o l'accesso e non riesci ad andare avanti, dillo invece di stimare.

---

Quando hai la risposta, incollala nella sessione della fabbrica: le categorie
vanno in `book.json` e nella scheda, i ranghi nella nota del posizionamento, il
titolo all'agente originalità, le parole chiave al posizionamento.

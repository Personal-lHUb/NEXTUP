# Cowork · regole KDP — il sistema (valgono per tutti i libri)

Richiesta della fabbrica per Cowork, con le regole di `CLAUDE.md` («Regola
permanente: collaborazione con Cowork via GitHub»). La risposta va in `cowork-kdp-risposta.md` accanto a questo file — nella casella
Drive «NEXTUP — libri/cowork» si chiama `sistema--cowork-kdp-risposta.md` — con la stessa numerazione.
Sono dati che la pipeline usa per ogni libro e che vengono da Amazon KDP.
`printing_costs.json` e il codice li aggiorna la fabbrica, con i test: Cowork
riporta i numeri, non li modifica.

Per ogni punto: il valore trovato, l'URL della pagina KDP e la data della
verifica. Se la pagina non c'è più o dice un'altra cosa, riportalo.

1. **Costi di stampa del cartaceo** — `printing_costs.json`, in questa cartella, oggi
   `"verificato_il": "DA VERIFICARE"`. Il prezzo e la royalty di ogni libro
   dipendono da qui. Nella pagina KDP dei costi di stampa (oggi
   https://kdp.amazon.com/help/topic/G201834340) riporta, per il bianco e nero
   su amazon.com, amazon.co.uk e amazon.it:
   - il costo fisso fino a 108 pagine;
   - il costo fisso e il costo per pagina oltre le 108;
   - se la carta crema costa come la bianca;
   - la percentuale di royalty del cartaceo (oggi il file usa il 60%).
2. **Dorso** — `kdpfactory/kdpspecs.py`. Spessore per pagina: bianca 0,002252",
   crema 0,0025". Il testo sul dorso è ammesso da 79 pagine in su.
3. **Abbondanza e margini** — sempre `kdpspecs.py`. Abbondanza 0,125" per lato.
   Margine esterno minimo 0,25" senza abbondanza e 0,375" con abbondanza.
   Zona di sicurezza del testo in copertina 0,25" dal taglio. Riquadro del
   codice a barre 2,0" x 1,2".
4. **Pagine minime e massime** per carta e formato 6x9 (in `kdpspecs.py`,
   `PAPER_PAGE_LIMITS`).
5. **Parole chiave e categorie.** Le regole KDP oggi in vigore: sette parole
   chiave da 50 caratteri al massimo; quante categorie si scelgono nel
   selettore; che cosa è vietato nelle parole chiave (marchi, nomi di autori,
   titoli di altri libri, programmi Amazon).
6. **Descrizione.** Il limite di 4000 caratteri e i tag HTML che KDP accetta
   nella descrizione.

# Prompt per Cowork: analisi dei concorrenti (ASIN)

28 ottobre 2026. Si incolla in Cowork insieme ai link di amazon.com (o di altre
pagine) da analizzare. Lo lancia l'autore: nessun lancio parte da solo (regola 6
di CLAUDE.md). Vale il LEGGIMI versione 17 (`config/leggimi-cowork.md`).

---

# Compito: analizzare i concorrenti (ASIN) per la fabbrica di libri NEXTUP

Ti allego in chat uno o più link di amazon.com (mercato USA, inglese americano)
o di altre pagine web che elencano libri. Aprili tu e raccogli le informazioni.
Ricava gli ASIN, descrivi ogni libro, controlla i rischi di copyright e dammi un
consiglio per ciascuno. Decido io se adottarlo: non scartare niente e non
scegliere al posto mio. Non scrivi nessun libro.

## Regole di lavoro
- **amazon.com si apre solo per leggere, e solo i link o gli ASIN che ti
  allego** (LEGGIMI versione 17). Non cercare libri per conto tuo, non scorrere
  pagine in serie, non scaricare in massa. Niente accesso con credenziali,
  niente acquisti, niente scrittura.
- **Non aprire** kdp.amazon.com né completion.amazon.com. Non usare Helium 10,
  Publisher Rocket o Google Trends: i loro dati li esporto io.
- Per capire l'argomento di un libro puoi fare una ricerca web. Se non trovi
  conferme, scrivi «da verificare».
- Non inventare niente: un dato che non trovi è «n.d.». Non stimare vendite,
  guadagni o classifiche.
- Nessuna credenziale, password, codice, token o cookie, né in ingresso né in
  uscita.
- Se una pagina è bloccata (captcha, 403, 429), non aggirarla: scrivi il link
  fra quelli non aperti e passa oltre.
- Se un ASIN non compare nella pagina (10 caratteri), non indovinarlo:
  «ASIN assente».
- **Tieni in elenco solo i codici ASIN che iniziano con la lettera B** (per
  esempio B0…). Gli altri (per esempio quelli numerici, che sono ISBN-10) non
  entrano in tabella né nelle sezioni B-D e F: non analizzarli. Elencali solo
  per codice, senza altro, nella sezione E, così so che li hai visti.
- Dei libri con ASIN che inizia per B riporta tutti, anche quelli che sconsigli.

## Per ogni libro raccogli
1. ASIN, titolo, sottotitolo, autore, formato, data di uscita
2. Prezzo (USD), numero di pagine
3. Classifica generale (Best Sellers Rank) e categorie con la classifica di ciascuna
4. Numero di recensioni e media delle stelle (solo i numeri, senza soglie)
5. Descrizione in due righe, nella tua lingua
6. Lacune: che cosa i lettori dicono di non aver trovato (dalle recensioni
   della pagina, se ci sono)

## Controllo di copyright
Serve a dirmi se il tema è rifacibile in un libro nostro, indipendente, senza
copiare niente. Lo fai dalla pagina (copertina, titolo, descrizione, «Look
inside» se è visibile) e dalla ricerca web. **È un segnale, non un parere
legale: non scrivere mai «violazione» o «illecito»**; scrivi «segnale di
rischio» e la prova. Per ogni libro guarda:

1. **Contenuto.** Personaggi, mondi o storie di un franchise (film, giochi,
   fumetti, serie), testi, citazioni lunghe, canzoni, poesie, programmi di
   un corso o metodi di un autore indicati con il suo nome, immagini che
   sembrano prese da altri. Segnala se il libro si presenta come «non
   ufficiale», «ispirato a», «fan book».
2. **Marchio.** Il titolo, il sottotitolo e le parole chiave della descrizione:
   contengono un nome di marchio, un nome di prodotto, un titolo di un'altra
   opera, un nome di persona reale? Cerca il termine su USPTO (la ricerca
   pubblica dei marchi, tmsearch.uspto.gov) e sul web. Riporta il numero di
   registrazione, il titolare e se lo stato è «live» o «dead». Se non puoi
   aprire USPTO, scrivilo: non indovinare.
3. **Logo e grafica.** Sulla copertina, nelle immagini della pagina e
   nell'anteprima: loghi, mascotte, personaggi, caratteri o stili riconoscibili
   di un marchio. Descrivili a parole; non scaricare né salvare immagini.
4. **Parole e nomi del tema.** Elenca i marchi, i nomi di prodotto e le persone
   reali che ricorrono nella descrizione e nel titolo, da non usare nel nostro
   libro. Distingui quelli nominati in modo descrittivo da quelli usati come
   richiamo commerciale.

Dai a ogni libro un livello: **basso** (nessun segnale), **medio** (segnali da
verificare), **alto** (segnali chiari), **n.d.** (non ho potuto controllare).
Per ogni segnale scrivi: che cosa (contenuto, marchio o logo), dove compare
(titolo, copertina, descrizione, anteprima), la fonte (link o numero di
registrazione) e la data della verifica. Nessun segnale senza fonte.

Il livello di copyright **non cambia il consiglio**: lo riporti come informazione
e decido io.

## Come formare il consiglio
CONSIGLIATO, SCONSIGLIATO o DA VERIFICARE, con una frase di motivo:

1. **Tema.** Sconsiglia se tratta, anche in parte rilevante: salute e medicina;
   diritto; finanza personale e investimenti; psicologia e salute mentale. Nel
   dubbio: DA VERIFICARE, «tema incerto».
2. **Categoria.** full-content (testo pieno da leggere), medium-content
   (interattivo, ogni pagina diversa) o low-content (quaderni, planner, diari,
   libri da colorare: sconsigliati, il progetto non li ammette).
3. **Mercato.** Recensioni, stelle, prezzo, pagine, classifica e data come dati,
   senza soglie. Segnala solo se qualcosa è fuori scala rispetto agli altri
   libri della stessa pagina.
4. **Fattibilità.** Segnala se rifarlo in modo indipendente richiederebbe
   persone reali, marchi altrui, testi di terzi, citazioni, promesse di
   risultato o credenziali professionali.

## Come rispondere
Un solo messaggio, in quest'ordine:

**A. Tabella**, una riga per libro, tutti quelli trovati:

| ASIN | Titolo | Tema | Tipo | Prezzo | Pagine | Classifica | Recensioni | Stelle | Fattibilità | Copyright | Consiglio | Motivo |
|---|---|---|---|---|---|---|---|---|---|---|---|---|

**B. Concorrenti consigliati**, dal più promettente, con una riga di motivo.
**C. Lacune dei lettori**, tre punti al massimo per ASIN consigliato.
**D. Da verificare**, per ogni caso dubbio che cosa ti serve per decidere.
**E. Link non aperti** con il motivo (captcha, blocco, kdp.amazon.com), e i
codici ASIN esclusi perché non iniziano con la B (solo il codice).
**F. Copyright**, per ogni libro con livello medio o alto: i segnali (che cosa,
dove, fonte, data) e l'elenco dei termini, marchi e nomi da non usare nel
nostro libro.

Non proporre libri nuovi.

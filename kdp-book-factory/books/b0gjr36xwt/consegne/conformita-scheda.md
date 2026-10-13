# Rapporto

Conformità della scheda prodotto, libro `b0gjr36xwt` (Fase 6). Ho letto `build/kdp-listing.md`, la sorgente `manuale/scheda.json` (le due coincidono parola per parola, e `build/metadata.json` e `build/vetrina.md` ripetono lo stesso testo), `book.json` (`notes`, `disclaimer`, `keywords`, `categories`), il mio rapporto di fase 4 `revisioni/conformita.md` e, per i riscontri, 01.md, 02.md (r. 50-62), 04.md, 07.md (r. 40-64), 23.md e 26.md (r. 80-113). Non ho letto `concorrente/` e non ho modificato nessun file. Dove scrivo «scheda.json» intendo la sorgente della scheda; i testi sostitutivi vanno messi lì.

Rispetto alla fase 4 il manoscritto è cambiato: il `disclaimer` è compilato, il cap. 23 parla di «most organizations» e rimanda al risk management, il cap. 26 ha la sezione «Sources for the tools in this book». Su questo non torno.

Nessun bloccante. Quattro rilievi importanti, quattro minori.

---

[importante] biografia — La prima frase fa di «Dana Ellery» un autore di più guide sul tema («guides») e un esperto del campo («clinical documentation and risk»). Un lettore NP, davanti a un sottotitolo che dice «The NP Casebook», ne deduce una professione clinica o di consulente legale-infermieristico che, secondo `book.json` (`notes`: «L'autore non ha credenziali cliniche»), l'autore non ha. Un nome d'autore non può avere un catalogo alle spalle, e il plurale lo suggerisce. La seconda frase dichiara una base di fonti più ampia di quella che il libro mostra: il cap. 4 dice «This book quotes no figures from it» a proposito dei rapporti sui sinistri, e le fonti elencate in 26.md sono quattro strumenti e un rapporto da consultare.
«Dana Ellery writes plain-English guides on clinical documentation and risk for nurses and nurse practitioners.»
«This casebook draws on published guidance, decision rules cited in its sources, and public reports on claims against nurse practitioners»
→ Sostituire l'intera `author_bio` con:
«Dana Ellery is the author of this plain-English casebook on clinical documentation for nurse practitioners. The author is not a clinician, and this book is not legal or clinical advice. It builds on published decision rules and guidelines, listed at the end of the book, and sets every principle on a concrete note; its scenarios are constructed for teaching. For the rules where you practice, ask your risk manager, your professional liability insurer and your state board of nursing.»
La frase «The author is not a clinician» discende da `notes` e la decide l'autore, insieme allo pseudonimo. Se non la vuole, la tolga e lasci il resto: ciò che conta è non lasciar intendere una professione e non parlare di «guides» al plurale.

[importante] consulenza legale / tutela degli atti — Il punto elenco promette di dire che cosa «lasciare fuori» dopo una richiesta di cartella o un reclamo. Dopo una richiesta di cartella, un reclamo o una citazione il libro dice il contrario: non si scrive niente e non si cambia niente («add nothing to the chart about the care in question and change nothing in it», 23.md r. 49). Detto così nella vetrina, «what to leave out» si legge come omissione selettiva in cartella proprio nel momento in cui l'alterazione è spoliation, e contraddice il «hides nothing» del cap. 23. Il testo del cap. 23 tratta tre cose diverse: che cosa va in cartella, che cosa va nella segnalazione interna, che cosa si chiede al risk management.
«What to write, and what to leave out, after an adverse event, a records request or a complaint»
→ Sostituire il quinto punto (`bullets[4]`) con:
«What belongs in the chart after an adverse event, what belongs in your organization's incident report instead, and what to ask your risk manager when a records request or a complaint arrives»

[importante] consulenza / promessa implicita — Il punto elenco presenta la documentazione di una scelta di non testare o non trattare come un modo per far «leggere» una scelta dove ci sarebbe un'omissione. Così dichiara un effetto sull'apparenza del referto, mentre il libro dice l'opposto: la riscrittura «adds nothing the clinician did not do» (04.md r. 57), ogni riga registra qualcosa che è accaduto (04.md r. 49), e 09.md r. 15 spiega che solo una frase vera nella nota distingue un esame valutato e scartato da uno a cui nessuno ha pensato. Letta da un avvocato, da un board o da un'infermiera scettica, la formula suona come istruzione a coprire una lacuna.
«How to document a decision not to test or treat so it reads as a choice, not an omission»
→ Sostituire il terzo punto (`bullets[2]`) con:
«How to document a decision not to test or treat, so the record shows what you weighed and why you chose as you did»

[importante] promessa di risultato / parole chiave non allineate — Nel `book.json` restano le sette parole chiave della prima stesura, che nella scheda sono state sostituite. Il codice (`kdpfactory/epub.py`, r. 193-196) scrive `spec.keywords`, cioè quelle di `book.json`, nei metadati `dc:subject` dell'EPUB; l'importazione della scheda non le riscrive. Fra queste c'è quella che nella fase 4 avevo segnalato: promette la protezione che il libro nega («It is also not a shield», 04.md r. 51). Un'altra attribuisce al libro un esito legale. Nell'EPUB non ho potuto verificare l'archivio compresso: ne parlo sul codice, e andrà ricontrollato al prossimo build. Anche le categorie di `book.json` non coincidono con quelle della scheda e includono una categoria clinica, «Assessment & Diagnosis», per un libro che dichiara di non dire «how to diagnose or treat» (01.md r. 33).
«np documentation to protect your license»
«legally defensible documentation for nps»
«Books > Medical Books > Nursing > Assessment & Diagnosis»
→ In `book.json` sostituire `keywords` con le sette della scheda, nello stesso ordine, dopo la correzione del rilievo sulla parola 7 qui sotto:
«legal charting for nurse practitioners» · «malpractice risk for nurse practitioners» · «nurse practitioner charting mistakes» · «charting for new nurse practitioners» · «high-risk charting scenarios for providers» · «against medical advice and capacity charting» · «telehealth charting for nurse practitioners»
Allineare `categories` alle tre della scheda («MEDICAL / Nursing / Issues», «LAW / Medical Law & Legislation», «MEDICAL / Nursing / Reference»), togliendo «Assessment & Diagnosis». Poi ricostruire l'EPUB.

[minore] avvertenze mancanti — giurisdizione — La scheda non dice che il libro riguarda la pratica negli Stati Uniti. Tutto l'impianto lo è: board statali, National Practitioner Data Bank, regole federali sul blocco delle informazioni, «plain American English» nel `book.json`. La scheda è però per amazon.it, amazon.com e amazon.co.uk, e un libro che parla di rischio legale senza dire in quale ordinamento si colloca invita a una lettura sbagliata. Il disclaimer del libro dice che le leggi differiscono «from state to state», ma non dice «negli Stati Uniti» e non vale per chi ha già comprato.
«This casebook is for nurse practitioners in their first years of practice, and for final-year NP students.»
→ Sostituire il secondo paragrafo di descrizione fino al primo punto con:
«This casebook is for nurse practitioners in their first years of practice in the United States, and for final-year NP students.»
Il resto del paragrafo non cambia. La clausola sulla variabilità fra stati va nel quarto paragrafo (vedi il rilievo seguente).

[minore] promesse di risultato — «defensible» — La parola compare nel sottotitolo e, nel terzo paragrafo, in «a defensible rewrite». Il disclaimer del libro la definisce («it does not describe a legal result»), ma la descrizione no: nel quarto paragrafo c'è la smentita dell'immunità, non la definizione. Il sottotitolo è una decisione dell'autore e non lo tocco; basta che la descrizione dica che cosa la parola vuol dire. Il testo che segue contiene anche la clausola sulla variabilità fra stati del rilievo precedente.
«No note makes anyone immune to a lawsuit or a board complaint, and this book does not pretend otherwise. It is not legal or clinical advice, and every scenario is constructed for teaching.»
→ Sostituire l'intero quarto paragrafo (`description_paragraphs[3]`) con:
«The goal is a note that shows what you saw, what you considered and why you decided, written in your own words and in the time a shift allows. In this book, "defensible" describes a note that makes your reasoning visible, not a legal result. No note makes anyone immune to a lawsuit or a board complaint, and this book does not pretend otherwise. It is not legal or clinical advice, laws and standards differ by state and by employer, and every scenario is constructed for teaching.»
La descrizione, con questa e le due modifiche precedenti, resta intorno ai 2500 caratteri su 4000 (il valore esatto lo ricalcola la pipeline).

[minore] avvertenze mancanti — quarta di copertina — Il testo parla di «defensible rewrite», di «what the note must contain» e di «legal terms explained», e chiama «casebook» un libro di casi costruiti, senza una riga che dica che non è consulenza né che i casi sono inventati. La descrizione ce l'ha, la quarta no. Il rischio non è la rimozione, è la lettura: «casebook» e «must contain» si prestano a far credere a casi reali e a requisiti di legge. Come testo stampato, l'impaginazione dello spazio spetta a `copertina`.
«This casebook takes those hard calls one at a time and shows a weak note beside a defensible rewrite of the same encounter.»
«Legal terms explained in plain English»
→ Aggiungere in fondo a `back_cover`, come ultima riga, dopo i punti:
«Not legal or clinical advice. Every case in this book is constructed for teaching.»

[minore] parole chiave — fuorviante — La settima parola chiave promette «risk management», che per un lettore è un programma organizzativo (politiche, assicurazioni, coperture), e «advanced practice nurses», una categoria più larga dei soli NP a cui il libro si rivolge; il libro dice anzi che su queste cose si chiede al risk manager. La parola non ripete nessuna parola del titolo o del sottotitolo, e la sostitutiva nemmeno.
«risk management for advanced practice nurses»
→ Sostituire con (42 caratteri, il capitolo 21 la copre per intero):
«telehealth charting for nurse practitioners»

---

## Verificato, nessuna segnalazione

- **Parole chiave 1-6.** Descrittive. Nessun nome d'autore, titolo di libro, marchio o riferimento a programmi Amazon («Kindle Unlimited», «bestseller»), nessuna promessa. Tutte sotto i 50 caratteri e senza virgole. Nessuna ripete «hard calls», «clear notes», «casebook», «defensible» o «documentation». «Malpractice risk» è coperta dai cap. 4 e 23 e il libro nega la protezione, perciò non è fuorviante.
- **Descrizione.** HTML con soli tag ammessi (`p`, `b`, `ul`, `li`), nessun link, prezzo, premio, recensione, classifica. Nessuna promessa di risultato: il quarto paragrafo nega l'immunità, e il libro lo conferma (01.md r. 31, 04.md r. 51). Il paragrafo sul pubblico dichiara «constructed for teaching». La chiusura e i punti 1 e 4 non pongono problemi.
- **Categorie.** Nessuna categoria medica o terapeutica per un libro che non lo è. La categoria LAW, che nella fase 4 avevo lasciato da pesare, regge: il libro tratta reclami al board, richieste di cartella, spoliation e un glossario legale (cap. 4, 8, 23, 26), e la descrizione dichiara il lettore e i limiti («not legal or clinical advice»). Chi cercasse un trattato di legislazione la scarterebbe leggendo la scheda. Non la sostituisco; se KDP non la accetta, si può lasciare vuoto uno dei tre posti senza perdite.
- **«Casebook» nel sottotitolo.** Il cap. 1 (r. 5, r. 33) e la descrizione dicono che i casi sono costruiti; basta la riga alla quarta di copertina.
- **Occhiello, gancio e badge.** «FOR NURSE PRACTITIONERS», «What will your note say to someone who knows the ending?» e il badge vuoto non contengono promesse né classifiche.
- **Contenuti IA.** La dichiarazione «AI-generated» per il testo c'è ed è la scelta prudente.
- **Fase 4.** La parola chiave sulla protezione e la questione «Casebook» e categorie giuridiche, lasciate come nota per questa fase, sono chiuse nei punti sopra.

## Giudizio complessivo

La scheda non ha bloccanti: niente nomi altrui, niente marchi, niente programmi Amazon, niente promesse di guarigione o di guadagno, e la descrizione dice con chiarezza che nessuna nota rende immune da una causa. I quattro rilievi importanti riguardano frasi che dicono più o diversamente da come il libro si comporta: una biografia che lascia intendere un mestiere, due punti elenco che suonano come istruzione a coprire o a tacere, e le parole chiave della prima stesura che sopravvivono in `book.json` e nell'EPUB. Con i testi sostitutivi qui sopra la scheda è pronta; gli altri quattro sono ritocchi.

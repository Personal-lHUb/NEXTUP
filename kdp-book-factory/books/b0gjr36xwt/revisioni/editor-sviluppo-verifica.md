# Rapporto dell'editor di sviluppo: verifica dopo le correzioni

Ho riletto il mio rapporto (`revisioni/editor-sviluppo.md`), il piano (`revisioni/piano-correzioni.md`), `outline.json` e i capitoli corretti `manuscript/01.md`–`26.md`. Per la numerazione stampata ho guardato il motore (`kdpfactory/typeset.py`, `kdpfactory/epub.py`, `kdpfactory/i18n.py`). Nei riferimenti qui sotto «cap. N» è il file `NN.md`, cioè il numero della scaletta.

## Stato dei rilievi precedenti

1. [bloccante] Aperture tutte uguali: **risolto in parte**. Nessun capitolo comincia più con «The scenario that follows is constructed», e i primi attacchi ora sono diversi fra loro: la nota (5), la radiografia (13), la battuta del figlio (15), il sintomo (17). Come bloccante il rilievo è chiuso. Le correzioni però hanno spostato il getto a blocchi sull'etichetta e sulla biografia: vedi i nuovi N1, N2 e N4.
2. [bloccante] Struttura dell'introduzione rispetto alle parti: **ancora aperto**. Adesso le parti sono quattro, ma i numeri di capitolo non corrispondono all'indice stampato: vedi A1.
3. [importante] Il differenziale fra le hard calls: **risolto**. Ora c'è «the test you don't order», e tutte le otto hard calls del cap. 1 hanno il loro elenco nel cap. 25.
4. [importante] Esempi del cap. 1 contro i capp. 12 e 16: **risolto**. Ora c'è «the specialist paged twice who never comes», e la domanda sulla capacità non ha più l'ora. La correzione ha prodotto però un doppione ravvicinato: vedi N9.
5. [importante] Regola dopo la richiesta, cap. 8 contro capp. 23 e 26: **risolto**. Capp. 8, 23 e 26 dicono la stessa cosa («add nothing to the chart about the care in question and change nothing in it»), e la cura di oggi resta permessa. Resta un dettaglio sull'elenco del 23 e del 25: vedi N10.
6. [importante] Due coppie del frasario: **risolto**. La coppia della TC ha criteri, valori e orari; quella della capacità ha Understanding e Reasoning con le parole del paziente.
7. [importante] Nomi doppi: **risolto**. Ora ci sono Silas Nakamura, Tariq Rahimi, Paloma Marchetti e Bettina Prentiss. Nel libro non resta nessun nome di battesimo portato da due personaggi.
8. [importante] Biografie doppie: **risolto**. Marchetti viene dalla riabilitazione cardiaca (11 anni), Thibodeaux dal post-partum (6 anni).
9. [importante] Formule ripetute: **risolto in parte**. «Nothing in it is false», «Every line is true», «Every line but one is true», «Here is the same visit, rewritten:» e «with N patients waiting» sono spariti. «At two in the morning» ora compare una volta sola (13). Resta la frase che introduce la riscrittura: vedi A2.
10. [importante] Chiusure dei capp. 7, 8 e 25: **risolto**. L'immagine dell'edit compare solo nel cap. 8.
11. [minore] Metformin nel cap. 7: **risolto**.
12. [minore] Ordine dei concetti: **risolto**. Il cap. 13 ora dice direttamente «It records terms, not the conversation». Gli altri due casi erano tollerabili e restano come sono.
13. [minore] Forma del cap. 16: **risolto**. Titoli ed etichette in grassetto sono uguali agli altri capitoli, e il cap. 25 riporta l'elenco identico.
14. [minore] Rimandi del glossario: **risolto in parte**. «Malpractice claim» ora punta al cap. 4. «Damages» punta ancora a un capitolo che non lo spiega, e tre voci nuove hanno lo stesso difetto: vedi A3. Il rimando al cap. 4 usa un titolo che non esiste: vedi N3.
15. [minore] Conto dei giorni nel cap. 8: **risolto** («updates the hospital day…»; il ricovero di lunedì fa di mercoledì il «Hospital day 3»).
16. [minore] Casi gemelli: **risolto**. Nel cap. 9 la caduta è in avanti con colpo alla fronte; nel cap. 12 c'è un'infezione urinaria a 73 anni.
17. [minore] Copertura del frasario: **risolto**. Ora ci sono le sezioni dei capp. 5–8. Resta una coppia con la formula sbagliata: vedi N8.

## Rilievi ancora aperti

**A1.** [bloccante] contraddizioni e conti, cap. 1 — i numeri di capitolo dell'introduzione non sono quelli che il lettore vede stampati. Il motore numera soltanto i capitoli con ruolo «chapter» (`typeset.py`, righe 1029–1031): l'Introduzione non ha numero, quindi «Chapter 1» è *What a Chart Becomes After a Bad Outcome*, e l'indice riporta lo stesso numero. Le parti si stampano «Part I», «Part II»… (`i18n.py`, riga 112). L'EPUB non numera i capitoli. Con l'indice in mano, «chapters 2–8» va da *The Provider Note Records a Decision* a *The Test You Order and the Test You Don't*: un capitolo di scenario dentro, il primo capitolo della parte fuori. È lo stesso difetto del primo rapporto, prodotto da un'altra causa. «Chapter 5» rimanda a *What You Don't Know Yet*, non alla versione breve del differenziale. L'errore viene dal mio primo rapporto: avevo proposto «chapters 2–8» contando da `outline.json`, mentre il piano stesso avverte «capitolo = sezione − 1».
«Part One (chapters 2–8) sets out how a provider note is read after something goes wrong»
«Part Two (chapters 9–15) covers the workup and its delays»
«Part Three (chapters 16–23) covers the patient's right to choose and to leave»
«Part Four (chapters 24–26) is for the moment of writing.»
«For a full board, chapter 5 shows a short version.»
→ Togliere i numeri di capitolo, che nell'EPUB non esistono. Chiamare le parti come le stampa il libro, con il loro titolo («Part I, *Writing for the Later Reader*, sets out…», e così per II, III e IV). Scrivere «the chapter on the differential shows a short version», come il libro fa ovunque altrove. Il consiglio finale diventa «Read Part I before your next shift». Se si vogliono tenere i numeri, quelli giusti per la carta sono 1–7, 8–14, 15–22, 23–25 e «chapter 4».

**A2.** [importante] ripetizioni, capp. 15–23 — la frase che introduce la riscrittura c'era già prima e allora mi era sfuggita: è la stessa formula, «written from what X saw/did and heard», in otto capitoli di fila. Nel cap. 21 resta perfino «Here is the same visit». La regola è già enunciata una volta nel cap. 4 («Nothing is added that the clinician did not do, so the difference lies in the writing and not in the care»).
«The same evening, written from what Rebecca saw, heard and did:» (15)
«Rewritten, the two entries hold nothing beyond what Tessa asked, heard or did:» (16)
«The note Carmen could have signed at 14:50 holds only what she did and heard:» (17)
«Fiona's rewrite keeps to what she did and heard:» (18)
«Here are the night's entries, written from what Claire was told, checked and did:» (20)
«Here is the same visit, written from what Maya saw, heard and decided:» (21)
«The same weeks, written from what Nina did and heard:» (22)
«What Hazel found, did and said that morning, entry by entry:» (23)
Minore, nella stessa famiglia: «Then add the sentence most notes leave out» (06), «Most notes leave out the text of the page» (12), «The line many notes leave out covers the appointment that cannot be made.» (19).
→ Tenere la clausola «what she did and heard» in uno o due capitoli al massimo. Negli altri introdurre la riscrittura con il suo contenuto («The rewrite puts each decision beside its reason:», come nel 13) oppure andare direttamente alla nota. Nel 19 togliere «many notes leave out».

**A3.** [minore] coerenza fra glossario e capitoli, cap. 26 contro capp. 1 e 4 — quattro voci rimandano a un capitolo che usa il termine ma non lo spiega. Tre sono state aggiunte con le correzioni (Settlement, Judgment, Scope of practice). Il cap. 4 scrive soltanto «a civil claim for money damages» e «by settlement or judgment». L'Introduzione si limita a nominare lo scope of practice. «Health care proxy» non ha rimando. Il libro dice di sé che ogni termine è definito dove compare la prima volta, e su queste voci non è vero.
«A short glossary defines the legal terms in plain English; each is also defined where it first appears.» (01)
«The italics at the end of each entry name the chapter where the term is first explained.» (26)
«**Scope of practice.** The care your license allows you to provide, as set by state law and your state board. *Introduction*.» (26)
→ La via più semplice: «most are also defined where they first appear» nel cap. 1 e «name the chapter where the term first appears» nel cap. 26. A «Health care proxy» va aggiunto *The Capacity Question, Decision by Decision*.

## Difetti nuovi introdotti dalle correzioni

**N1.** [importante] aperture, capp. 1–23 — l'etichetta «caso costruito» chiude il primo paragrafo in 18 capitoli su 22, sempre nella stessa posizione. Il piano chiedeva «mai due capitoli con la stessa formula», e invece alcune formule tornano identiche.
«She and everyone who treats her are invented for this chapter.» (03) / «Clinic, staff and patient are invented for this chapter.» (10). Inoltre «made up for this chapter» (06) e «built for this chapter» (07).
«He, his family and everyone caring for him exist only on these pages.» (16) / «The practice and everyone in this case exist only on these pages.» (22)
«The next encounter never happened either.» (15) / «Like every case in the book, this one never happened.» (17) / «This visit never happened, and neither did the night call later in the chapter.» (21)
«Neither of them exists» (01) / «Neither man exists» (04) / «Neither of them is real» (07)
→ Dare a ogni capitolo una formula sua: cambiare 10, 22, 17 o 21, e 07. In circa metà dei capitoli spostare l'etichetta fuori dalla chiusa del primo paragrafo, per esempio nella frase che introduce la riscrittura o in apertura del secondo paragrafo. Se basti la dichiarazione generale del cap. 1 per qualche capitolo lo decide `conformita`.

**N2.** [importante] ripetizioni, capp. 5–20 — la biografia accorciata è diventata una formula nuova: «N months into…» compare in otto capitoli in cui prima non c'era. Si aggiunge a quella che 1 e 2 avevano già, identica fra loro.
«eleven months into her work as an NP» (05), «ten months into her first job as a hospital medicine NP» (07), «six months into hospital medicine as an NP» (08), «five months into her first NP job» (09), «two months into her work as an NP» (14), «nine months into hospital medicine» (16), «ten months into her work as an NP» (17), «five months into her work as a night hospital medicine NP» (20). Già da prima: «four months into her first provider job» (01) / «eight months into her first provider job» (02).
Nei secondi casi c'è uno stampo analogo, già presente prima, sei volte: «a former flight nurse, is in her second year as a hospital medicine NP» (11). Le altre cinque sono in 10, 14, 18, 19 e 21.
→ Tenere l'anzianità solo dove pesa sul caso: Leah nel cap. 1, Audrey ex infermiera di hospice nel 13, Jasmine al terzo mese nel 12. Negli altri capitoli toglierla, oppure darla in forme diverse, per esempio con un dettaglio di scena al posto del conteggio dei mesi.

**N3.** [importante] rimandi, cap. 26 — dieci voci del glossario rimandano al cap. 4 con una dicitura in corsivo che non è un titolo. Il titolo è *Where a Claim, a Complaint, and a Review Begin* (outline e `04.md`). Il lettore che lo cerca nell'indice non lo trova, e la frase d'apertura del glossario promette il nome del capitolo.
«**Closed claim.** A malpractice claim that has reached its end: withdrawn, dismissed, settled or decided at trial. *The chapter on where claims begin*.»
Le altre nove voci: Contemporaneous, Damages, Employer review, Judgment, Licensing board complaint, Malpractice claim, National Practitioner Data Bank, Peer review, Settlement.
→ Sostituire con *Where a Claim, a Complaint, and a Review Begin* in tutte e dieci. Nei capp. 7, 12, 14 e 23 il rimando descrittivo nel testo («the chapter on where claims begin») va bene così.

**N4.** [minore] aperture — al posto dell'attacco unico ci sono ora due piccole famiglie, e tre capitoli consecutivi cominciano con l'orario.
«At 05:30 on a Wednesday, a nurse charts…» (08), «At 07:50 on a Tuesday in January, Curtis Faber…» (09), «At 17:05, in a primary care practice…» (10), «At 14:10 on a Wednesday, Dennis Quigley…» (18)
«Raymond Teague, sixty-two, was admitted on Friday with cellulitis…» (07), «Gloria Ainsworth, seventy-three, was admitted on Tuesday with a urinary tract infection.» (12), «Albert Yates, eighty-four, was admitted on Tuesday at 10:30…» (16)
→ Cambiare l'attacco del 9 o del 10, per spezzare la serie 8-9-10, e uno fra 7, 12 e 16.

**N5.** [minore] contraddizioni, cap. 26 contro cap. 2 — dopo le correzioni del cap. 2, due definizioni del glossario non coincidono più con quelle del capitolo a cui rimandano.
«meaning unintended harm to a patient caused by the care rather than by the illness itself» (02) / «**Adverse event.** Harm to a patient that results from care rather than from the underlying illness.» (26)
«would, more likely than not, have changed what happened to the patient. Some states also allow a claim for a lost chance of a better outcome.» (02) / «In most states, a claim has to show that doing what should have been done would have changed what happened.» (26)
→ Allineare le due voci del glossario al testo del cap. 2: «unintended», «more likely than not» e la perdita di chance.

**N6.** [minore] contraddizioni, cap. 8 contro capp. 23 e 10 — l'affermazione sull'audit trail è stata attenuata nel cap. 23 ma non nel cap. 8, che resta assoluto. Lo stesso cap. 8, poche righe prima, rimanda all'ufficio HIM per sapere che cosa registra il sistema.
«So does every look, including a look at the chart of a patient who is not yours.» (08)
«in most systems the audit trail records who opened the chart and when.» (23); «many record systems log who did and when» (10)
→ Nel cap. 8: «In most systems, so does every look…».

**N7.** [minore] coerenza fra capitolo ed elenchi, cap. 11 e cap. 25 — il paragrafo aggiunto sul letto che non si libera prima del cambio turno introduce un elemento nuovo, il passaggio di consegne. L'elenco del capitolo non lo riporta, e quindi non lo riporta neanche il cap. 25.
«Sometimes the bed does not open before your shift ends. The last entry is then the handoff: its time, the clinician taking over, by name, and what you told them…» (11)
«**For a transfer.** … what the patient and family were told, and when you will act if the bed does not open.» (11 e 25)
→ Aggiungere all'elemento, con le stesse parole nel 11 e nel 25: «and, if your shift ends first, the handoff: time, the clinician by name, what you told them».

**N8.** [minore] coerenza fra frasario e capitoli, cap. 24 — sotto *What You Don't Know Yet* la frase debole non è quella del cap. 6: la variante con «alternatives» è la frase di template del cap. 8.
«**Weak:** Risks, benefits and alternatives discussed.» (24)
«"Risks and benefits discussed, patient agrees with plan" does none of this» (06); «"risks, benefits and alternatives discussed,"» (08)
→ Nel cap. 24 usare la frase del cap. 6.

**N9.** [minore] ripetizioni, cap. 1 — a quattro righe di distanza due elenchi ripetono gli stessi tre casi, e «who never comes» compare due volte.
«the capacity question, the patient walking out before the paperwork is ready, the specialist paged twice who never comes.»
«the test you don't order, the abnormal result, the consultant who never comes, the capacity question, the departure against medical advice, …»
→ Nel primo elenco mettere momenti che il secondo non nomina, per esempio la pagina della notte o il risultato che arriva dopo la dimissione. In alternativa togliere il primo elenco e lasciare che il paragrafo successivo nomini i casi.

**N10.** [minore] contraddizioni, capp. 23 e 25 contro cap. 26 — l'elemento dell'elenco parla di «a request» in generale. Il testo e il glossario applicano la regola soltanto alla richiesta di un avvocato, al reclamo e alla causa, e dicono che le richieste di routine sono la maggioranza.
«**After a request, complaint or subpoena.** No new entries about the past care and no changes; today's care charted as usual.» (23 e 25)
«Once a complaint, a claim or an attorney's request has arrived» (23); «Most are routine. One that comes from an attorney, or with a complaint or a claim, means…» (26)
→ «**After an attorney's request, a complaint, a claim or a subpoena.**», uguale nel 23 e nel 25.

## Giudizio complessivo

Le correzioni hanno chiuso quasi tutti i conti interni del libro:
- I nomi e le biografie non si sovrappongono più.
- La regola sulla cartella dopo la richiesta è la stessa in 8, 23 e 26.
- I 15 elenchi del cap. 25 coincidono con quelli dei capitoli.
- Le coppie del frasario si ritrovano nei capitoli, con un'eccezione (N8).
- I titoli citati nei capp. 24 e 25 sono quelli attuali.
- Le date e gli orari tornano: 80 minuti nel 12, 29 nel 8, calendario di marzo–giugno nel 22, giorni di malattia nel 9 e nel 14.

Resta un bloccante, A1: l'introduzione numera i capitoli dalla scaletta e non dall'indice stampato. Si corregge in poche righe, togliendo i numeri. Il getto a blocchi non sta più nella prima frase. Si è spostato nell'etichetta in chiusa di paragrafo, nella formula «N months into» e nella frase che introduce la riscrittura. Sono difetti meno vistosi, ma un lettore che legge di seguito la Parte III li nota.

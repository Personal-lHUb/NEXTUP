# Rischi legali dei libri: che cosa la fabbrica non usa

Rapporto del 14 ottobre 2026, chiesto dall'autore: «tutto ciò che
potenzialmente non si può usare per diritti, copyright o problemi legali non
venga utilizzato per i libri da me prodotti». Autore residente in Italia,
mercato amazon.com. Le fonti sono in fondo, con l'indirizzo; quelle di KDP sono
pagine dell'aiuto ufficiale lette come risultati di ricerca (amazon.com dal
container non si apre).

**Non è consulenza legale né fiscale.** Dove la risposta dipende da un
professionista (fisco, contratti, prodotti nell'UE) è scritto, e la fabbrica
non decide al posto suo.

## In breve: i rischi, dal più grave

| # | rischio | gravità | oggi |
|---|---|---|---|
| 1 | Testi e PDF dei libri pubblici sul repository GitHub | alta | scoperto |
| 2 | Dichiarazione sull'IA stampata nel libro non vera | alta | scoperto |
| 3 | Cowork che legge amazon.com in automatico | alta, per l'account | scoperto |
| 4 | Libri di salute, diritto, finanza, psicologia | media-alta | in parte (`conformita`) |
| 5 | Fisco: royalty di libri generati con l'IA | da commercialista | scoperto |
| 6 | GPSR: cartacei venduti nell'UE | media, incerta | scoperto |
| 7 | Metadati: concorrente, parole chiave, categorie | media | coperto + controllo nuovo |
| 8 | Materiale di terzi: citazioni, canzoni, immagini | alta se succede | coperto |
| 9 | Strumenti: licenze di testi, immagini, font | bassa | a posto |
| 10 | Pseudonimo, biografia, recensioni | bassa | coperto |

### 1. Testi e PDF pubblici sul repository

Il repository `Personal-lHUb/NEXTUP` è pubblico: chiunque scarica i capitoli
(`manuale/`), i diari e da oggi i PDF finali (`pubblicazione/`). Tre problemi:

- **KDP**: «We will not accept content under copyright that is freely
  available on the web unless it's provided by the owner of the copyright».
  Il proprietario sei tu, ma KDP può chiederti di dimostrarlo (rights
  verification), e chi non lo dimostra rischia il rifiuto, la rimozione e un
  segno sull'account.
- **Diritto d'autore debole**: un testo generato dall'IA, senza un apporto
  creativo umano sufficiente, non è protetto né negli Stati Uniti (Copyright
  Office, gennaio 2025: «prompts alone» non bastano) né in Italia (legge
  132/2025, art. 25: tutela solo il «lavoro intellettuale» umano). Quindi chi
  copia il libro dal repository e lo ripubblica potrebbe non violare nessun tuo
  diritto, e tu non avresti modo di farlo togliere.
- **KDP e pubblico dominio**: un testo senza diritto d'autore, già libero sul
  web, somiglia per KDP a un contenuto di pubblico dominio: royalty al 35%,
  niente KDP Select, rifiuto se è già disponibile altrove.

**Rimedio**: i testi dei libri fuori da un repository pubblico (repository
privato, o i libri in un repository privato a parte). Cowork oggi legge gli
indirizzi pubblici: con il repository privato il canale va cambiato. Decisione
dell'autore.

### 2. La dichiarazione sull'IA

Nel colophon di ogni libro è stampato: «This book was produced with the
assistance of artificial intelligence tools, under human supervision, review
and editorial responsibility». Due problemi:

- Per KDP il testo scritto dall'IA è «AI-generated», anche se poi lo si
  modifica molto; «AI-assisted» è solo il testo scritto da te e corretto
  dall'IA. Nel modulo KDP la risposta è «AI-generated»: il libro non può dire
  il contrario.
- **AI Act, art. 50(4), in vigore dal 2 agosto 2026**: chi usa l'IA per
  generare testo pubblicato per informare il pubblico su temi di interesse
  pubblico deve dichiararlo, salvo una **revisione umana vera** (non una
  correzione di bozze) con una persona che ne ha la **responsabilità
  editoriale**. Tu risiedi nell'UE, quindi la regola ti riguarda anche se
  vendi negli Stati Uniti. Oggi la revisione la fanno gli agenti, non una
  persona: la frase «human … review and editorial responsibility» non è vera.

**Rimedio**: o la frase dice il vero («generated with artificial intelligence
tools; the publisher selected, directed and approved the content»), oppure
l'autore rilegge davvero il testo e ne risponde. Decisione dell'autore.

### 3. Cowork su amazon.com

Le Condizioni d'uso di Amazon concedono l'uso del sito per scopi personali e
non commerciali ed escludono «data mining, robots, or similar data gathering
and extraction tools» e la raccolta di schede prodotto, descrizioni e prezzi.
Cowork che apre le pagine di Amazon e ne copia recensioni, prezzi e schede per
la fabbrica è esattamente questo. Il rischio non è una causa: è l'account
Amazon, che è lo stesso con cui pubblichi su KDP.

**Rimedio**: niente lettura automatica di amazon.com. I dati sul concorrente da
strumenti che hanno la licenza per darli (Helium 10, Publisher Rocket, con il
tuo abbonamento), dalla ricerca web su altri siti, o copiati a mano da te.
Decisione dell'autore.

### 4. Salute, diritto, finanza, psicologia

KDP non vieta questi temi, ma:

- l'autore e l'editore rispondono di quello che il libro dice; i libri sulla
  salute scritti dall'IA sono oggi sotto osservazione (agosto 2026: libri
  sull'ADHD generati dall'IA con consigli pericolosi, segnalati e rimossi);
- Amazon rimuove i titoli con promesse sanitarie non dimostrate («cura»,
  «guarisce», «clinicamente provato»), anche nella scheda e in copertina;
- un dosaggio, una diagnosi, una terapia, una strategia legale o un
  investimento detti come istruzione sono consulenza professionale.

La fabbrica ha già l'agente `conformita` (consulenza come prescrizione,
promesse, avvertenze). Per **escludere** il rischio, come chiede l'autore,
serve una regola prima della scaletta: o questi temi non si fanno, o si fanno
solo come informazione e con le condizioni qui sotto (sezione «Con
condizioni»). Decisione dell'autore, anche per il libro in corso
(`b0gjr36xwt`, documentazione clinica per nurse practitioner: casi costruiti,
nomi di farmaci, dosi in alcuni scenari).

### 5. Fisco (da commercialista)

- **Ritenuta USA**: la convenzione Italia-Stati Uniti porta a zero la ritenuta
  sulle royalty per opere letterarie (altre royalty: 8%), se in KDP si compila
  il modulo fiscale (W-8BEN per una persona fisica).
- **In Italia**: le royalty dell'autore vanno nel quadro RL come diritti
  d'autore, con la deduzione forfettaria del 25% (40% sotto i 35 anni, art.
  54 c. 8 TUIR), senza partita IVA se l'attività non è organizzata e abituale.
  Due dubbi veri, che la fabbrica non può sciogliere:
  - una produzione organizzata e continua di libri (una fabbrica, appunto)
    può essere vista come attività d'impresa, con partita IVA e contributi;
  - se il testo è generato dall'IA e la legge 132/2025 protegge solo le opere
    umane, la qualifica di «diritti d'autore» (e la deduzione) può essere
    contestata.
- **Rimedio**: parlarne con un commercialista prima di pubblicare più titoli,
  portando questo paragrafo.

### 6. GPSR (regolamento UE sulla sicurezza dei prodotti)

Dal 13 dicembre 2024 un libro stampato venduto ai consumatori nell'UE è un
prodotto: servono un operatore responsabile e i suoi dati di contatto. Le
fonti non sono d'accordo su chi sia il «fabbricante» di un libro stampato da
KDP (l'autore-editore o Amazon), e non ho trovato una pagina ufficiale di KDP.
Un cartaceo KDP con diritti mondiali arriva anche su amazon.de, .it, .fr, .es.
Vendendo su amazon.com il rischio è basso; resta da chiarire prima di vendere
nell'UE (commercialista o avvocato, o l'assistenza KDP).

### 7. Metadati

Già controllati da `conformita` e da `qa`: niente titoli o nomi di altri
autori, marchi, «bestseller», «Kindle Unlimited», promesse; categorie che
corrispondono al libro (KDP: «zero tolerance» per metadati che ingannano).
Nuovo: il motore controlla che **titolo, autore e ASIN del concorrente** non
compaiano mai nel libro, in copertina o nella scheda (sezione «Linee rosse»).

### 8. Materiale di terzi

Coperto da `conformita` e dalla regola 9 di CLAUDE.md: nessun brano, testo di
canzone, poesia o immagine altrui; figure solo generate o di pubblico dominio
o CC0. Resta così.

### 9. Strumenti e licenze

- **Testi (Claude, Anthropic)**: le condizioni d'uso assegnano a te gli output
  e ne consentono l'uso commerciale; il diritto d'autore però non lo dà il
  contratto (vedi il punto 1).
- **Immagini (Higgsfield)**: i termini (§ 4.4) non rivendicano gli output e
  non ne limitano l'uso commerciale; il piano gratuito, secondo una recensione,
  lo esclude: si genera solo col piano a pagamento (oggi Pro).
- **Font**: EB Garamond e Barlow Condensed, licenza SIL OFL, inclusi con la
  licenza in `fonts/ofl/`; i ripieghi di sistema (Liberation, DejaVu) hanno
  licenze libere. Ammessi in un libro venduto.

### 10. Pseudonimo, biografia, recensioni

KDP ammette lo pseudonimo; la biografia non dichiara titoli o professioni che
l'autore non ha (già controllato da `conformita`). La pagina finale del libro
chiede «an honest review»: va bene; mai omaggi o sconti in cambio di
recensioni.

## Linee rosse: la fabbrica non le usa mai

1. Testo, immagini o struttura di un altro libro; brani, testi di canzoni,
   poesie, citazioni lunghe di opere protette.
2. Titolo, autore, editore o ASIN del concorrente, e nomi di altri autori o
   titoli, nel libro, in copertina o nella scheda.
3. Persone reali identificabili (pazienti, clienti, personaggi pubblici) in
   casi, esempi o critiche; dati personali di chiunque.
4. Marchi nel titolo, nel sottotitolo, nelle parole chiave e in copertina; nel
   testo, i prodotti con il nome generico (es. oxycodone/acetaminophen, non
   il nome commerciale).
5. Promesse di risultato (guarire, guadagnare, vincere una causa) nel libro e
   nella scheda.
6. Istruzioni di dosaggio, diagnosi o terapia dette al lettore; consigli
   legali, fiscali o di investimento per il suo caso.
7. Una dichiarazione sull'IA che non corrisponde a come il libro è stato fatto.
8. Immagini che non siano generate con un piano che ne consente l'uso
   commerciale, o di pubblico dominio o CC0 dimostrabili.
9. Font senza una licenza che ne consenta l'incorporazione in un libro venduto.
10. Credenziali, esperienze o titoli che l'autore non ha.

## Con condizioni

Se l'autore ammette i temi di salute, diritto, finanza o psicologia:

- informazione generale, mai istruzione per il caso del lettore;
- casi dichiarati costruiti; nessun dato di pazienti o clienti veri;
- fonti ufficiali per ogni regola o numero (lo controlla il `fact-checker`);
- avvertenza nel colophon e rinvio al professionista nel punto in cui serve;
  per l'autolesionismo, un contatto di crisi concreto;
- nessuna promessa né in copertina né nella scheda.

## Decisioni dell'autore del 14 ottobre 2026, e che cosa fa il motore

| tema | decisione | nel motore |
|---|---|---|
| salute, diritto, finanza, psicologia | **esclusi**, anche il libro in corso | `kdpfactory/temi.py`: il comando `temi`, il blocco a `concorrente importa`, l'errore `TEMA` di `qa`, il blocco del pacchetto; agenti `posizionamento` e `conformita` |
| libro `b0gjr36xwt` (documentazione clinica) | **eliminato** | tolto da `books/` e dai libri attivi; resta nella storia di git e in una copia di backup |
| dichiarazione sull'IA | **veritiera** | colophon: «This book was written with artificial intelligence tools. The publisher chose the subject and directed the work.» (anche in italiano e nei libri di enigmi) |
| Cowork sui siti di Amazon | **fermo** | LEGGIMI versione 16: niente amazon.com, completion.amazon.com, kdp.amazon.com; niente Helium 10, Publisher Rocket, Google Trends guidati da Cowork; il pacchetto non scrive più la richiesta di bozza KDP: su KDP carica l'autore |
| testi e PDF pubblici | **`NEXTUP` privato**, storia compresa | lo fa l'autore da GitHub; dopo, Cowork non legge più i link pubblici e i file glieli porta l'autore |
| concorrente nel libro | linea rossa | `kdpfactory/legale.py`: errore `CONCORRENTE` di `qa` se titolo, autore, editore o ASIN del concorrente compaiono nel testo, in copertina o nella scheda |

## Che cosa resta all'autore

1. Repository: testi e PDF fuori dal pubblico, o no.
2. Dichiarazione sull'IA: frase veritiera, o revisione umana vera.
3. Cowork su amazon.com: fermo, o no.
4. Temi di salute, diritto, finanza, psicologia: esclusi o con condizioni; e
   il libro in corso.
5. Fisco e GPSR: con un commercialista, prima di pubblicare più titoli.

## Fonti

- KDP, Content Guidelines (contenuti generati con l'IA, metadati, contenuti
  deludenti): https://kdp.amazon.com/en_US/help/topic/G200672390
- KDP, Publishing Public Domain Content (contenuti liberi sul web, prova dei
  diritti): https://kdp.amazon.com/en_US/help/topic/G200743940
- KDP, Metadata Guidelines for Books: https://kdp.amazon.com/en_US/help/topic/G201097560
- KDP, Make Your Book More Discoverable with Keywords: https://kdp.amazon.com/en_US/help/topic/G201298500
- KDP, Guide to Kindle Content Quality: https://kdp.amazon.com/en_US/help/topic/G200952510
- U.S. Copyright Office, Copyright and Artificial Intelligence, Part 2 (sintesi):
  https://www.jenner.com/en/news-insights/client-alerts/us-copyright-office-issues-report-on-copyrightability-of-works-incorporating-ai-generated-material
  e https://www.jonesday.com/en/insights/2025/02/copyrightability-of-ai-outputs-us-copyright-office-analyzes-human-authorship-requirement
- Legge 23 settembre 2025, n. 132, art. 25: https://www.doctrine.it/norms/laws/itatextks0w8oah02nn2t/articles/itaartdowg001injsjlo
  e https://www.osservatorio-ip.it/2025/10/02/intelligenza-artificiale-e-diritto-dautore-la-legge-132-2025-traccia-i-confini-della-nuova-creativita-umana/
- Commissione europea, obblighi di trasparenza dell'art. 50 dell'AI Act:
  https://digital-strategy.ec.europa.eu/en/faqs/transparency-obligations-under-article-50-ai-act
  e https://artificialintelligenceact.eu/transparency-rules-article-50/
- Condizioni d'uso di Amazon, licenza e accesso (copie del testo):
  https://conductatlas.com/platform/amazon/amazon-conditions-of-use/provision/CA-P-018441/prohibition-on-data-mining-and-scraping-tools/
- Convenzione Italia-USA, royalty: https://home.treasury.gov/news/press-releases/tg454
  e https://www.accountingtoday.com/news/at-long-last-us-italy-tax-treaty-is-here
- Royalty KDP in Italia (blog di consulenti, da verificare con un commercialista):
  https://www.fiscochiaroconsulting.it/amazon-kdp-self-publishing-guida-fiscale/
  e https://www.studioallievi.com/royalty-amazon-dichiarazione-dei-redditi/
- GPSR e libri (fonti di settore, non ufficiali): https://selfpublishingadvice.org/gpsr/,
  https://www.editeur.org/files/ONIX%203/APPNOTE%20Product%20safety%20requirements%20in%20ONIX.pdf
- Libri di salute e Amazon: https://www.traverselegal.com/blog/navigating-amazon-fda-and-ftc-compliance/,
  https://getcoai.com/?p=67284
- Higgsfield, chi possiede le generazioni: https://higgsfield.ai/creator-hub/help-center/account-and-privacy/who-owns-my-generations-and-can-i-use-them-commercially
- Anthropic, Consumer Terms: https://anthropic.com/legal/terms e
  https://terms.law/ai-output-rights/anthropic/

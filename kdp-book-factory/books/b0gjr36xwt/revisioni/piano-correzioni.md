# Piano delle correzioni — b0gjr36xwt (fase 5)

Sei rapporti in questa cartella: `lettore-cieco.md`, `editor-sviluppo.md`,
`fact-checker-1-8.md`, `fact-checker-9-16.md`, `fact-checker-17-26.md`,
`conformita.md`. Totale: 2 bloccanti (editor di sviluppo), 23 importanti, molti
minori. Qui ogni rilievo ha una decisione; dove i rapporti si sovrappongono vale
la decisione scritta qui. I file sono `manuscript/NN.md` (sezione NN; capitolo
= sezione − 1). Il testo resta inglese americano, nella voce del libro.

Regole per chi corregge: si tocca solo quello che è segnalato; nessuna frase
nuova che prometta protezione; nessuna cifra o regola che non sia nei rapporti;
le sostituzioni proposte alla lettera dai fact-checker si usano così come sono,
salvo dove qui sotto è detto altro.

## Interventi su tutto il libro

1. **Aperture** (bloccante, editor). La frase «The scenario that follows is
   constructed.» non apre più nessun capitolo. Ogni capitolo-scenario entra nel
   caso in un modo suo (la pagina che arriva, la nota già scritta, la domanda,
   il paziente, l'orologio) e dichiara che il caso è costruito più avanti nel
   primo paragrafo o in una forma breve e variata («A constructed case:»,
   «This case is invented, like every case in the book», ecc.), mai due
   capitoli con la stessa formula. La biografia «N years as an X nurse… M
   months as an NP» si accorcia o si sposta dove non serve. Le formule dei
   secondi casi («The second scenario is also constructed», «The third scenario
   is constructed as well», «The scenario continues, still constructed») si
   variano allo stesso modo.
2. **Formule ricorrenti** (editor). «Nothing in it is false», «Every line is
   true», «Every line but one is true», «Here is the same visit, rewritten:»,
   «At HH:MM, with N patients waiting, X writes:», «at two in the morning»: al
   massimo una volta ciascuna nel libro; altrove si entra subito nel difetto.
3. **Nomi doppi** (editor): rinominare nel capitolo più tardo Theo Nakamura
   (18 → nome diverso da Theo), Omar Rahimi (18 → nome diverso da Omar), Lena
   Marchetti (19 → nome diverso da Lena), Lydia Prentiss (19 → nome diverso da
   Lydia). Biografie doppie: Lena Marchetti (19) non più ex infermiera di
   hospice; Maya Thibodeaux (21) non più infermiera di infusione; anni diversi.
   Cognomi nuovi nel rispetto delle iniziali già usate (18-23: M-Z).
4. **Strutture inventate con nome** (conformità): Maplewood Family Practice,
   Northgate Primary Care, Lakeside Gastroenterology, Riverside Hospital,
   Hillcrest Family Medicine diventano descrizioni generiche («a family
   practice», «the hospital's ED», «a gastroenterology practice»).
   «County Hospital ED» (10) e «Regional Medical Center»/«University Hospital»
   (11) restano: sono già generici.
5. **«Stefan Kirby»** (12): cambiare il nome del chirurgo vascolare che non
   arriva (nome più comune, non ricercabile come persona reale specifica).
6. **Avvertenza** (conformità): il disclaimer della conformità va in
   `book.json` (lo applica la sessione, non l'editor).

## Per capitolo

- **01 Introduction**
  - «How the book is built» riscritto sulle quattro parti reali, nominate
    (Part I capp. 2-8 principi e metodo; Part II capp. 9-15; Part III capp.
    16-23; Part IV capp. 24-26 consultazione); il consiglio diventa «Read Part
    One (chapters 2–8) before your next shift if you can».
  - Elenco delle hard calls: togliere «the differential», mettere «the test you
    don't order»; «the specialist paged three times who never calls back» →
    «the specialist paged twice who never comes»; «the capacity question at two
    in the morning» → senza ora.
  - La promessa «rarely much longer» si corregge sugli esempi: il ragionamento
    aggiunge poche frasi, il resto della riscrittura è storia ed esame che una
    nota da provider ha comunque; dire che ogni capitolo mostra la nota completa
    e che la versione breve per il turno pieno sta nel cap. 5.
  - Dopo il caso di Leah, mostrare le tre frasi in un blockquote (la nota
    riscritta), corta.
  - Non consulenza clinica (conformità): «It is not legal advice and it is not
    clinical advice: it does not tell you how to diagnose or treat, and the
    doses, thresholds and decisions in its scenarios belong to constructed
    patients.»
  - Studenti (fc1): «learning to write the same notes, usually under a
    preceptor's review».
- **02** standard of care (fc1+fc3): usare la sostituzione di fc1 («in the
  usual formulation…», «in some states a court may measure an NP against the
  physician standard…»). Causation (fc1): «more likely than not» + loss of
  chance. Negligence: «In most cases, a malpractice claim is a claim of
  negligence». Adverse event (fc1): «unintended harm to a patient caused by the
  care rather than by the illness itself». «protect your license and your
  career» → «serve your license and your career» (conformità).
- **03** collaborative agreement (fc1): sostituzione proposta.
- **04** «stable angina» → «angina» (fc1). CNA/NSO (fc1): sostituzioni
  proposte. Il titolo «Where Claims Against NPs Actually Begin» perde
  «Actually» (lo rinomina l'agente `indice` dopo le correzioni); il testo non
  deve promettere numeri.
- **07** metformin: «the pain request belongs to the chapter on prescribing»,
  via il metformin (lettore + editor). Accesso del paziente alle note (fc1):
  sostituzione proposta. «short-staffed again»: motivazione cambiata come dice
  la conformità (opinione sulla causa, non fatto clinico). Chiusura: non più
  «while a change is still just an edit» (resta al cap. 8).
- **08** regola dopo una richiesta (editor+fc3+conformità): «Once a complaint, a
  claim or an attorney's request has arrived, add nothing to the chart about the
  care in question and change nothing in it, and ask risk management first;
  the chapter on the adverse event covers that moment.» Spoliation (fc1):
  «destruction, alteration or failure to preserve evidence». Audit trail (fc1):
  sostituzione proposta. «updates the weight and the sodium» → «updates the
  hospital day, the weight and the sodium».
- **09** dinamica della caduta diversa dal cap. 3 (non più all'indietro con
  ematoma occipitale: per esempio caduta in avanti con colpo alla fronte; i
  criteri della regola restano assenti). Formula «At 11:15, with the waiting room
  filling up» variata.
- **10** spironolattone «a week ago» / «7 days ago» (fc2).
- **11** «The bed that never opens»: aggiungere un paragrafo breve su che cosa
  scrivere quando il letto davvero non si libera entro il turno (il passaggio a
  chi copre la notte, la rivalutazione, chi è responsabile), restando nel
  budget.
- **12** Gloria Ainsworth: diagnosi d'ingresso diversa dalla polmonite (per
  esempio cellulite o insufficienza cardiaca) ed età diversa da 76; Kirby
  rinominato (vedi sopra). «Call that physician when…» aperto con «Many
  organizations expect you to call…» (conformità).
- **13** in testa allo scenario: «The drugs, doses and quantities below belong
  to a constructed patient. They show how to record a decision, not what to
  prescribe; check current labeling, your formulary and your state's rules.»
  Tramadol (fc2): «serotonin syndrome and seizure risk with sertraline». Il
  rimando «Like the refusal form in the chapter on informed refusal» → detto
  direttamente («it records terms, not the conversation»). Frase sul tutore
  legata al caso («in this scenario…»).
- **14** titolo di sezione «## A Z-Pak before a long drive» → «## An antibiotic
  request before a long drive»; «Z-Pak» resta solo nella battuta del paziente.
  «an infection spreading toward the eye or brain is not managed with tablets at
  home» legato al caso.
- **16** EGD (fc2): ricovero martedì 10:30, «Oriented and conversant on admission
  at 10:30», «black stools since Sunday». Titoli «## The note as written» e
  «## The rewrite» come gli altri capitoli; elenco finale con etichette in
  grassetto come gli altri. Guardian/conservator (fc2). «Ask psychiatry when…»
  aperto con «Many clinicians ask psychiatry when…».
- **17** «most refusals are» → «many refusals are» (fc3). Desametasone (fc3):
  aggiungere «dexamethasone with the first dose» nello scenario e nella riga
  della riscrittura.
- **18** troponina ad alta sensibilità (fc3). Nomi Theo/Omar rinominati.
- **19** colecistite (fc3): le due sostituzioni proposte. «The line most notes
  leave out» → «many notes». Nomi Lena/Lydia rinominati, biografia diversa;
  Riverside e Hillcrest generici.
- **20** lascia il lattato com'è (piano della NP diurna, non protocollo); niente
  da fare oltre le formule ricorrenti.
- **21** Thibodeaux biografia diversa; Northgate generico.
- **22** Maplewood e Lakeside generici.
- **23** regola dopo la richiesta (fc3, testo proposto), «Do not hand over
  records yourself…» (fc3, testo proposto), «or among your own papers» → «ask
  your risk manager what to do with your own copies», «logs every look» → «in
  most systems the audit trail records who opened the chart and when». Glargine
  (fc3): sostituzioni proposte, piano con potassio. «Lantus» → «glargine» nella
  nota debole. Disclosure: «disclosure of an adverse event» in grassetto, con
  «not the same as releasing health information under privacy law». Late entry
  «labeled and written the same day». Ordini assoluti → prassi delle
  organizzazioni + rinvio («ask risk management what you may say, to whom, and
  whether you need your own attorney»).
- **24 Phrasebook**: in testa, «"Defensible" here means the note shows the
  reasoning; it is not a legal result» e «doses and thresholds» nell'elenco di
  ciò che appartiene ai pazienti costruiti. Nuova sezione iniziale con le
  coppie dei capitoli 5-8 (presi dal testo: «PE unlikely», «r/o appendicitis»,
  «Clinical correlation recommended», «noncompliant», «drug-seeking», «risks,
  benefits and alternatives discussed», copy-forward, correzione e late entry).
  Coppia CT: criteri con valori e orari dal cap. 9. Coppia capacità: almeno due
  abilità con le parole del paziente dal cap. 16. «Lantus» → «glargine». Stare
  nel budget togliendo dove serve.
- **25 Scenario Finder**: elenco del cap. 15 (capacità) con le etichette in
  grassetto, identico al cap. 16 corretto; chiusura non più «while a change is
  still just an edit». Righe nuove nell'indice delle situazioni per i momenti
  dei capitoli 5-8 (differenziale, incertezza, linguaggio, correzione e late
  entry), che rimandano ai capitoli.
- **26 Glossary**: standard of care, causation, records request, decision-making
  capacity, licensing board complaint, National Practitioner Data Bank, adverse
  event, health care proxy, disclosure (→ «Disclosure of an adverse event»),
  guardian/conservator con le sostituzioni dei fact-checker; voci nuove per
  «scope of practice», «settlement», «judgment»; «Malpractice claim» e «Damages»
  puntano al cap. 4 («Where Claims Against NPs Begin»). In fondo, «Sources for
  the tools in this book»: Canadian CT Head Rule (Stiell IG et al., Lancet
  2001;357:1391–1396); IDSA rhinosinusitis guideline (Chow AW et al., Clin
  Infect Dis 2012;54(8):e72–e112); PERC (Kline JA et al., J Thromb Haemost
  2004;2:1247–1255); il modello delle quattro abilità (Appelbaum PS, N Engl J Med
  2007;357:1834–1840); il rapporto CNA/NSO sulle NP, da consultare nell'edizione
  più recente sul sito dell'editore.

## Dopo le correzioni

- La sessione applica il disclaimer in `book.json`.
- L'agente `indice` rivede il titolo del cap. 4 (senza «Actually») e i titoli
  delle parti II e III, perché coprano tutti i capitoli che contengono
  (lettore cieco).
- `build`, `impaginazione`, e il ritorno degli agenti che avevano dato i
  bloccanti (editor di sviluppo) sui capitoli corretti.

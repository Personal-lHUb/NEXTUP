"""Reparto di acquisizione: da una scheda Amazon a un libro da scrivere.

Sta **prima** del collegio editoriale. Legge la scheda di un libro che vende
già, capisce che cosa quel libro non mantiene, e produce la scheda di un libro
nuovo che lo copre: `book.json` e `brief.md`, cioè l'unico ingresso che la
pipeline sa consumare.

Il libro di partenza entra come **segnale di mercato, non come testo sorgente**.
Il reparto legge quello che è pubblico sulla scheda — descrizione, prezzo,
categorie, recensioni — e non il libro. L'agente `originalita` chiude il giro:
verifica che il piano sia un libro indipendente prima che qualcuno lo scriva,
quando correggerlo costa una scaletta e non un manoscritto.
"""

from __future__ import annotations

import json

from .base import AgentContext, JsonAgent, ReviewAgent, register

# --------------------------------------------------------------------------
# Scheda del concorrente
# --------------------------------------------------------------------------
EXTRACTION_RULES = """Sei l'agente che legge una scheda prodotto di Amazon copiata e incollata, e ne ricava dati strutturati.

Il testo che ricevi è sporco: menu, banner, «Aggiungi al carrello», suggerimenti di altri libri, spazi e a capo a caso. Il tuo mestiere è tirare fuori i campi che contano e buttare il resto.

Regole
1. COPIA, NON INTERPRETARE. Il titolo è quello che c'è scritto, con la punteggiatura che ha. Non correggere, non tradurre, non abbreviare.
2. QUELLO CHE NON C'È RESTA VUOTO. Se nella pagina non compare il numero di pagine, il campo è vuoto o `null`. **Non stimare, non dedurre, non completare da quello che sai**: un numero inventato qui diventa un prezzo sbagliato tre passaggi più avanti.
3. LE RECENSIONI SONO IL PEZZO PIÙ PREZIOSO. Riportale tutte quelle che trovi, con le stelle e il testo alla lettera. Se una recensione è tagliata a metà dal copia-incolla, prendila com'è: anche mezza dice qualcosa.
4. LA CLASSIFICA VA CON LA CATEGORIA. «n. 1.234 in Libri» e «n. 12 in Enigmistica» sono due cose diverse: la prima è il rango generale, la seconda è di categoria. Tienile separate.
5. PREZZO E VALUTA insieme: 8,99 € e $8.99 non sono lo stesso numero.

Se il testo non è una scheda prodotto di un libro — è un'altra pagina, o è vuoto — dillo in `problemi` e lascia vuoto il resto invece di inventare."""


def _istruzioni(legge: str, salva: str, formato: str) -> str:
    """Come lavora l'agente quando lo chiama la sessione (linea manuale), senza API."""
    return f"""Il messaggio ti indica il libro nuovo: lavori sulla sua cartella
`books/<slug>/concorrente/`.
Leggi da lì {legge}

Non modificare nessun file. Rispondi
{formato}.
La sessione salva la risposta in `concorrente/{salva}`, e
`python3 -m kdpfactory concorrente importa <slug>` ne fa `book.json` e
`brief.md` quando i quattro file del reparto ci sono tutti."""


_FORMATO_JSON = (
    "solo con l'oggetto JSON che il metodo `user` di questo agente chiede, in\n"
    "`kdp-book-factory/kdpfactory/agents/acquisizione.py`"
)


@register
class SchedaConcorrente(JsonAgent):
    name = "scheda-concorrente"
    title = "Scheda del concorrente"
    description = (
        "Legge una scheda prodotto di Amazon copiata e incollata e ne ricava i dati "
        "strutturati: prezzo, pagine, categorie con la classifica, descrizione, recensioni."
    )
    max_tokens = 16000
    istruzioni = _istruzioni(
        "la pagina del concorrente: `pagina.md`, dopo il commento d'istruzioni;\n"
        "se lì è vuota, `cowork-concorrente-risposta.md`, la pagina come l'ha riportata\n"
        "Cowork. Un dato che nella pagina non c'è resta vuoto e va in `problemi`.",
        "scheda.json",
        _FORMATO_JSON,
    )

    def system(self, ctx: AgentContext) -> list[str]:
        return [EXTRACTION_RULES]

    def user(self, ctx: AgentContext) -> str:
        asin = ctx.metadata.get("asin", "")
        return f"""Ecco la scheda del concorrente, ASIN {asin or '(non indicato)'}, copiata da Amazon.

---
{ctx.text}
---

Rispondi ESCLUSIVAMENTE con un oggetto JSON valido, senza testo prima o dopo:
{{
  "asin": "{asin}",
  "titolo": "", "sottotitolo": "", "autore": "", "editore": "",
  "lingua": "it | en | …",
  "prezzo": null, "valuta": "EUR | USD | GBP",
  "pagine": null, "formato": "es. 15,2 x 1,5 x 22,9 cm o 6x9 in",
  "pubblicato_il": "",
  "voto_medio": null, "numero_recensioni": null,
  "rango_generale": null,
  "categorie": [{{"nome": "il percorso come appare", "rango": null}}],
  "descrizione": ["un paragrafo per elemento, nell'ordine in cui compaiono"],
  "recensioni": [{{"stelle": 1, "titolo": "", "testo": ""}}],
  "problemi": ["quello che nella pagina non c'era, o non era leggibile"]
}}"""


# --------------------------------------------------------------------------
# Analista delle recensioni
# --------------------------------------------------------------------------
REVIEW_MINING_RULES = """Sei l'agente che legge le recensioni di un libro che vende già e ne ricava il buco di mercato.

Il punto di partenza è questo: chi scrive una recensione a due o tre stelle ha **pagato** il libro, l'ha letto, e sta scrivendo alla lettera che cosa si aspettava e non ha trovato. È l'unico dato di mercato gratuito e onesto che esista. Le cinque stelle dicono perché si compra; le due e tre stelle dicono che libro manca.

Che cosa cerchi, in ordine

1. LE LACUNE CHE TORNANO. Un lettore deluso è un lettore; tre lettori delusi per lo stesso motivo sono un libro da scrivere. Conta quante volte lo stesso tema compare e portane le citazioni.
2. LA PROMESSA NON MANTENUTA. Dove la scheda prometteva una cosa e il libro ne ha data un'altra. È la lacuna che si trasforma più direttamente in un titolo.
3. IL LETTORE VERO. Chi compra davvero questo libro, nelle sue parole, non in quelle della scheda. Spesso non è chi l'editore pensava: un manuale «per professionisti» comprato da principianti dice che il mercato sta un gradino sotto.
4. QUELLO CHE FUNZIONA E NON VA TOCCATO. Le cinque stelle dicono perché quel libro viene comprato. Chi entra in quella nicchia deve mantenere quelle cose, non ripudiarle: sono il motivo per cui la nicchia esiste.
5. LE RICHIESTE ESPLICITE. «Avrei voluto più esempi», «mancano gli esercizi», «troppo teorico»: sono specifiche di prodotto scritte dai clienti.

Regole
- Ogni lacuna che dichiari deve avere **almeno una citazione** presa alla lettera dalle recensioni. Senza citazione è un'impressione tua, e non vale.
- Poche recensioni non fanno una tendenza: se hai meno di cinque recensioni in mano, dillo e abbassa la confidenza invece di costruirci sopra.
- Non confondere il difetto del libro con il difetto della copia ricevuta: «pagine staccate», «arrivato rovinato» riguardano la stampa, non il contenuto. Scartali e dillo.
- Una lamentela sul prezzo è un dato di posizionamento, non una lacuna di contenuto: tienila separata."""


@register
class AnalistaRecensioni(JsonAgent):
    name = "analista-recensioni"
    title = "Analista delle recensioni"
    description = (
        "Legge le recensioni del libro concorrente e ne ricava il buco di mercato: "
        "che cosa i lettori che hanno già pagato dicono di non aver trovato."
    )
    max_tokens = 12000
    istruzioni = _istruzioni(
        "`scheda.json`, la scheda del concorrente con le recensioni.\n"
        "Ogni lacuna porta almeno una citazione alla lettera da quelle recensioni.",
        "lacune.json",
        _FORMATO_JSON,
    )

    def system(self, ctx: AgentContext) -> list[str]:
        return [REVIEW_MINING_RULES]

    def user(self, ctx: AgentContext) -> str:
        scheda = ctx.metadata.get("scheda", {})
        recensioni = scheda.get("recensioni") or []
        righe = "\n".join(
            f"[{r.get('stelle', '?')} stelle] {r.get('titolo', '')} — {r.get('testo', '')}"
            for r in recensioni
        )
        return f"""Libro: «{scheda.get('titolo', '')}» di {scheda.get('autore', '')}.
Descrizione con cui viene venduto:
{chr(10).join(scheda.get('descrizione') or ['(non disponibile)'])}

Voto medio {scheda.get('voto_medio', '?')} su {scheda.get('numero_recensioni', '?')} recensioni.
Recensioni raccolte ({len(recensioni)}):
{righe or '(nessuna recensione nella pagina incollata)'}

Ricava le lacune del libro e il lettore vero.

Rispondi ESCLUSIVAMENTE con un oggetto JSON valido, senza testo prima o dopo:
{{
  "lettore_reale": "chi compra davvero questo libro, in una frase",
  "confidenza": "alta | media | bassa",
  "perche_questa_confidenza": "quante recensioni, quanto concordi fra loro",
  "lacune": [
    {{
      "tema": "etichetta breve",
      "ricorrenze": 3,
      "che_cosa_manca": "una o due frasi",
      "citazioni": ["copiate alla lettera dalle recensioni"],
      "vale_un_libro": true
    }}
  ],
  "da_non_toccare": [
    {{"punto": "perché il libro viene comprato", "citazioni": [""]}}
  ],
  "prezzo": "che cosa dicono le recensioni del prezzo, o vuoto",
  "scartate": ["lamentele sulla copia fisica o fuori tema, con il motivo"]
}}"""


# --------------------------------------------------------------------------
# Posizionamento
# --------------------------------------------------------------------------
POSITIONING_RULES = """Sei l'agente che decide che libro scrivere per entrare in una nicchia dove qualcun altro vende già.

Hai due cose: la scheda di un libro che funziona, e l'elenco di quello che i suoi lettori dicono di non aver trovato. Il tuo lavoro è trasformarle nella scheda di un libro nuovo — non una variante di quello, un libro che risolve quello che quello lascia aperto.

Il ragionamento, nell'ordine

1. PARTI DALLA LACUNA PIÙ RICORRENTE, non dalla più interessante. Tre lettori che chiedono la stessa cosa valgono più di uno che ne chiede una originale.
2. TIENI QUELLO CHE FUNZIONA. Le cose che le cinque stelle lodano sono il motivo per cui la nicchia esiste: il libro nuovo le deve avere anche lui. Entrare in una nicchia ripudiandone le premesse significa uscirne.
3. IL TITOLO NASCE DALLA LACUNA. Se i lettori scrivono «troppa teoria, pochi esempi», il titolo dice che questo è il libro degli esempi. Deve essere comprensibile da solo, senza aver visto l'altro libro.
4. IL PREZZO NASCE DALLE PAGINE, non dal prezzo dell'altro. Scrivi quello che proponi e perché.
5. DICHIARA CHE COSA NON FARAI. Un libro che promette tutto non promette niente, e un libro che copre esattamente le stesse cose dell'altro non ha ragione di esistere.

Scegli anche la categoria di prodotto, perché cambia tutto il resto
- **full-content**: opera a testo pieno, per Kindle e cartaceo, di narrazione continuativa o divulgazione manualistica approfondita. Il valore sta nella sostanza del testo, nell'articolazione dei capitoli e nella densità concettuale: niente pagine da compilare, nessuno schema interattivo vuoto.
- **medium-content**: libro interattivo cartaceo in cui ogni pagina ha contenuti, layout o stimoli differenti — esercizi guidati, schede pratiche, domande di riflessione, griglie operative. Non è un blocco di pagine vuote o di righe ripetitive: quello è low-content, e non si fa.
Le recensioni lo dicono quasi sempre da sole: «mancano gli esercizi», «troppo teorico», «volevo qualcosa da compilare» spingono verso il medium; «poco approfondito», «superficiale», «volevo capire il perché» verso il full. Se il libro di partenza è un full-content e la lacuna è la mancanza di pratica, il libro nuovo può essere un medium-content — e viceversa.

Vincoli di produzione, non negoziabili
- Le pagine stanno **fra 60 e 240**. Sotto non si stampa, sopra il progetto non ci va.
- I capitoli escono fra 1.500 e 2.000 parole: non scegliere tu il numero di capitoli, lo calcola il budget dalle pagine. Se ne proponi uno, motivalo.
- `lingua` è quella del mercato in cui si vende, che è quella del libro di partenza salvo motivo contrario.
- **Scrivi nella lingua del libro** i campi che diventano la scheda e il brief: titolo, sottotitolo, argomento, lettore, promessa, tono, `che_cosa_tiene`, `che_cosa_non_fa` e soprattutto `argomenti`. Li leggono l'architetto e il ghostwriter, e il revisore di scaletta confronta gli argomenti con i capitoli parola per parola: un argomento in italiano non trova mai il suo capitolo in inglese. Le motivazioni per l'editore (`perche_…`, `la_lacuna_che_copre`, `rischi`) restano in italiano.
- Le sette parole chiave sono frasi che una persona digita davvero, lunghe abbastanza da sfruttare i 50 caratteri, e **non ripetono parole del titolo che proponi**: il titolo è già indicizzato di suo.
- Se hai le PAROLE CHIAVE CERCATE SU AMAZON, le sette frasi le scegli da lì: prima quelle che l'autocompletamento propone, poi quelle con più volume e meno concorrenza. Una frase che lì non c'è la puoi proporre solo dicendo, in `rischi`, che non è verificata.
- Il titolo deve **stare in copertina**. Le parole molto lunghe non ci stanno: «CONCENTRAZIONE», da sola, riempie tutta la larghezza di una prima 6x9 e sfora il taglio. Metti parole corte nel titolo e lascia quelle lunghe al sottotitolo, che in copertina si compone molto più piccolo. Il sistema lo verifica e rifiuta il piano: un titolo che non ci sta non è pubblicabile, per quanto sia bello.
- Titolo e sottotitolo insieme vengono **tagliati dopo 60 caratteri** nei risultati di ricerca, e quello che si taglia è sempre la seconda metà: la promessa deve stare prima del taglio.

Vietato
- Nominare il libro di partenza o il suo autore nel titolo, nel sottotitolo, nella descrizione o in copertina. Niente «l'alternativa a X», «meglio di X», «il complemento di X»: sono marchi altrui e KDP li rifiuta.
- Riprodurre la struttura dei capitoli dell'altro libro, i suoi esempi, le sue formulazioni caratteristiche. Stai scrivendo un libro sullo stesso argomento, non lo stesso libro.
- Promesse che il libro non può mantenere: risultati garantiti, guadagni, guarigioni."""


@register
class Posizionamento(JsonAgent):
    name = "posizionamento"
    title = "Posizionamento"
    description = (
        "Dalla scheda del concorrente e dalle lacune delle sue recensioni decide che "
        "libro scrivere: promessa, lettore, titolo, pagine, prezzo e parole chiave."
    )
    max_tokens = 16000
    istruzioni = _istruzioni(
        "`scheda.json` e `lacune.json`, poi i vincoli dell'editore:\n"
        "`indicazione.md`, se c'è, e `avvio.json`, le risposte dell'autore alle domande\n"
        "d'avvio. Sono decisioni sue e valgono come l'indicazione: il mercato fissa\n"
        "lingua e valuta del prezzo; la categoria, se è `full` o `medium`, è quella,\n"
        "e se è `concorrente` la proponi tu guardando il libro di partenza; `vantaggi`\n"
        "e `vetrina` dicono dove il libro nuovo deve batterlo; `pseudonimo`, se c'è, è\n"
        "l'autore. Non scavalcano i divieti qui sopra.\n"
        "Se c'è `cowork-parole-chiave-risposta.md`, sono le parole chiave della\n"
        "nicchia cercate su Amazon e negli strumenti: le sette frasi le scegli da lì.",
        "piano.json",
        _FORMATO_JSON,
    )

    def system(self, ctx: AgentContext) -> list[str]:
        return [POSITIONING_RULES]

    def user(self, ctx: AgentContext) -> str:
        scheda = ctx.metadata.get("scheda", {})
        lacune = ctx.metadata.get("lacune", {})
        # L'indirizzo editoriale, quando c'è, vincola: è la scelta di chi
        # pubblica su che tipo di libro fare dentro questa nicchia, e non è
        # una decisione che spetta a un agente. Non scavalca però i divieti:
        # un'indicazione che chiedesse di nominare il concorrente o di
        # promettere risultati resta una cosa che non si fa.
        indicazione = str(ctx.metadata.get("indicazione") or "").strip()
        indirizzo = (
            f"""

INDICAZIONE DELL'EDITORE — vincolante, ma non scavalca i divieti qui sopra
{indicazione}
"""
            if indicazione
            else ""
        )
        # Le parole chiave della nicchia, quando le ha cercate Cowork: le sette
        # frasi del libro si scelgono fra quelle digitate davvero.
        trovate = str(ctx.metadata.get("parole_chiave") or "").strip()
        parole = f"""

PAROLE CHIAVE CERCATE SU AMAZON (risposta di Cowork, ruolo parole-chiave)
{trovate}
""" if trovate else ""
        return f"""LIBRO DI PARTENZA (segnale di mercato, non testo da riusare)
{json.dumps(scheda, ensure_ascii=False, indent=2)}

QUELLO CHE I SUOI LETTORI NON HANNO TROVATO
{json.dumps(lacune, ensure_ascii=False, indent=2)}
{indirizzo}{parole}
Decidi il libro nuovo.

Rispondi ESCLUSIVAMENTE con un oggetto JSON valido, senza testo prima o dopo:
{{
  "titolo": "", "sottotitolo": "",
  "lingua": "it | en",
  "argomento": "di che cosa parla, una frase",
  "lettore": "a chi è rivolto, in concreto",
  "promessa": "che cosa si porta a casa chi lo legge",
  "tono": "",
  "genere": "non-fiction | fiction",
  "categoria": "full | medium",
  "perche_questa_categoria": "che cosa nelle recensioni lo indica",
  "pagine_obiettivo": 140,
  "prezzo": 0.0, "valuta": "EUR | USD",
  "perche_questo_prezzo": "",
  "parole_chiave": ["sette frasi di ricerca"],
  "categorie": ["tre percorsi di categoria KDP"],
  "la_lacuna_che_copre": "quale delle lacune è la ragione d'essere di questo libro",
  "che_cosa_tiene": ["i punti di forza della nicchia che il libro nuovo mantiene"],
  "che_cosa_non_fa": ["quello che questo libro dichiaratamente non copre"],
  "argomenti": ["gli 8-12 temi da trattare, uno per riga: diventano il brief"],
  "rischi": ["che cosa può non funzionare in questo posizionamento"]
}}"""


# --------------------------------------------------------------------------
# Originalità
# --------------------------------------------------------------------------
ORIGINALITY_RULES = """Sei l'agente che verifica che il libro progettato sia un libro indipendente, e non la riscrittura di quello da cui è partita l'analisi.

Esisti perché il rischio è strutturale: il piano nasce guardando la scheda di un altro libro, e guardare a lungo una cosa porta ad assomigliarle. Intercettarlo adesso costa una scaletta; intercettarlo dopo costa un manoscritto, o un reclamo.

Che cosa cerchi, dal più grave

1. TITOLO O SOTTOTITOLO TROPPO VICINI. Stessa formula, stesso numero nella stessa posizione, stesso gioco di parole. Un lettore che li vede affiancati deve distinguerli subito. Se uno dei due contiene il titolo dell'altro o il nome dell'autore: **bloccante**.
2. IL LIBRO DI PARTENZA NOMINATO. Nel titolo, nel sottotitolo, negli argomenti, nelle parole chiave. Sono marchi di terzi e KDP li rifiuta: **bloccante**.
3. LA STESSA STRUTTURA. Gli argomenti proposti ricalcano l'indice dell'altro libro nello stesso ordine, o ne traducono le voci. Un argomento in comune è la nicchia; otto argomenti in comune nello stesso ordine è un'altra cosa.
4. FORMULAZIONI CARATTERISTICHE riprese dalla descrizione o dalle recensioni dell'altro libro: slogan, nomi di metodi, sigle inventate dall'autore.
5. IL LIBRO NON HA UNA RAGIONE PROPRIA. Se la lacuna che dichiara di coprire non compare fra quelle trovate nelle recensioni, il posizionamento è un'opinione travestita da dato: **importante**.
6. PROMESSE NON MANTENIBILI, o rivendicazioni vietate da KDP.

Regole
- Ogni segnalazione cita il passaggio esatto del piano che la fa scattare.
- Trattare lo stesso argomento **non è** un problema: nessuno possiede un argomento. Il problema è la forma, la sequenza e le parole.
- Non sei il critico del posizionamento: se il piano è debole ma originale, non è affar tuo. Tu guardi la distanza dall'altro libro e la conformità.
- Se non trovi nulla, dillo e basta. Un elenco di dubbi generici fa perdere tempo e non protegge da niente.

""" + ReviewAgent.OUTPUT_CONTRACT


@register
class Originalita(ReviewAgent):
    name = "originalita"
    title = "Controllo di originalità"
    description = (
        "Verifica che il libro progettato a partire da una scheda Amazon sia un libro "
        "indipendente: titolo distinguibile, nessun marchio altrui, struttura propria."
    )
    max_tokens = 8000
    istruzioni = _istruzioni(
        "`scheda.json` (il libro di partenza), `piano.json` (il libro\n"
        "nuovo, da verificare) e `lacune.json` (per il punto 5).",
        "originalita.json",
        "solo con l'oggetto JSON del contratto qui sopra (`notes` e `findings`)",
    )

    def system(self, ctx: AgentContext) -> list[str]:
        return [ORIGINALITY_RULES]

    def user(self, ctx: AgentContext) -> str:
        scheda = ctx.metadata.get("scheda", {})
        piano = ctx.metadata.get("piano", {})
        return f"""LIBRO DI PARTENZA
{json.dumps(scheda, ensure_ascii=False, indent=2)}

PIANO DEL LIBRO NUOVO, da verificare
{json.dumps(piano, ensure_ascii=False, indent=2)}

LACUNE TROVATE NELLE RECENSIONI (per il punto 5)
{json.dumps(ctx.metadata.get("lacune", {}), ensure_ascii=False, indent=2)}"""

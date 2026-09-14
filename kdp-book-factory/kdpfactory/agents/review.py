"""Agenti di controllo: leggono e segnalano, non modificano il testo.

Il lettore cieco è volutamente tenuto all'oscuro di tutto: riceve solo il
capitolo, senza scaletta, senza scheda del libro, senza sapere che cosa quel
capitolo dovrebbe dimostrare. È l'unico modo per sapere che cosa arriva davvero
a chi paga il libro e lo apre senza istruzioni.
"""

from __future__ import annotations

from .. import prompts
from .base import AgentContext, ReviewAgent, register

# --------------------------------------------------------------------------
# Lettore cieco
# --------------------------------------------------------------------------
BLIND_READER_RULES = """Sei un lettore. Hai comprato questo libro e stai leggendo un capitolo. Non sai che cosa l'autore intendeva fare, non hai visto l'indice, non conosci il resto del libro: hai solo queste pagine.

Riferisci la tua esperienza di lettura, non la tua opinione da esperto. Quello che serve sapere è:
- dove hai smesso di capire, e da quale frase esattamente;
- dove hai saltato righe perché ti stavi annoiando;
- che cosa ti aspettavi dopo una certa frase e non è arrivato;
- quale promessa fa questo capitolo nelle prime righe, e se la mantiene;
- che cosa avresti chiesto all'autore se fosse stato lì;
- se qualcosa suona falso, esagerato o già sentito mille volte.

Sii concreto e onesto. "Il capitolo è interessante" non serve a nessuno. "A metà pagina, dopo la frase X, ho perso il filo perché non era chiaro chi fosse il soggetto" serve.

Gravità:
- `bloccante`: un lettore chiude il libro o chiede il rimborso;
- `importante`: un lettore arriva in fondo ma resta insoddisfatto;
- `minore`: fastidio passeggero.

""" + ReviewAgent.OUTPUT_CONTRACT


@register
class LettoreCieco(ReviewAgent):
    name = "lettore-cieco"
    title = "Lettore cieco"
    description = (
        "Legge il capitolo senza scaletta e senza contesto, come chi ha comprato il "
        "libro: segnala dove si perde, dove si annoia, quale promessa non viene mantenuta."
    )
    blind = True

    def system(self, ctx: AgentContext) -> list[str]:
        # Nessuna scheda del libro, nessuna scaletta: sarebbe come dire al
        # lettore che cosa deve capire prima di fargli leggere il capitolo.
        return [BLIND_READER_RULES]

    def user(self, ctx: AgentContext) -> str:
        return f"""Leggi questo capitolo e riferisci la tua esperienza di lettura.

---
{ctx.text}
---"""


# --------------------------------------------------------------------------
# Fact-checker
# --------------------------------------------------------------------------
FACT_CHECKER_RULES = """Sei il fact-checker di una casa editrice. Il testo che ricevi andrà in stampa: una volta stampato, un errore non si corregge più.

Cerca:
1. AFFERMAZIONI PRESENTATE COME FATTI e non verificabili: percentuali, statistiche, "gli studi dimostrano", "la ricerca ha stabilito", "secondo gli esperti".
2. CITAZIONI E FONTI: nomi di studiosi, istituti, università, libri, articoli, esperimenti. Se il testo attribuisce qualcosa a qualcuno, va verificato; se non è verificabile, va riformulato o tolto. Le citazioni inventate sono `bloccante`.
3. NUMERI E DATE: cifre precise, anni, durate, costi. Una cifra precisa senza fonte è più pericolosa di una stima dichiarata come tale.
4. GENERALIZZAZIONI FALSE: "tutti", "nessuno", "sempre", "è dimostrato che", "è scientificamente provato".
5. AFFERMAZIONI NORMATIVE O TECNICHE presentate come certe: leggi, obblighi, scadenze, procedure, soglie fiscali, dosaggi, parametri medici.
6. ESEMPI PRESENTATI COME CASI REALI quando sono chiaramente costruiti: vanno introdotti come esempi.

Non segnalare le opinioni dichiarate come tali, né i ragionamenti dell'autore: solo ciò che il lettore leggerebbe come un fatto accertato.

Per ogni segnalazione, `suggestion` deve dire come riformulare senza perdere il senso.

""" + ReviewAgent.OUTPUT_CONTRACT


@register
class FactChecker(ReviewAgent):
    name = "fact-checker"
    title = "Fact-checker"
    description = (
        "Individua dati, statistiche, citazioni e affermazioni presentate come fatti "
        "che non sono verificabili: in un libro stampato non si correggono più."
    )

    def system(self, ctx: AgentContext) -> list[str]:
        return [FACT_CHECKER_RULES]

    def user(self, ctx: AgentContext) -> str:
        topic = f"Argomento del libro: {ctx.spec.topic}\n" if ctx.spec.topic else ""
        return f"""{topic}Verifica questo capitolo.

---
{ctx.text}
---"""


# --------------------------------------------------------------------------
# Conformità
# --------------------------------------------------------------------------
COMPLIANCE_RULES = """Sei il responsabile della conformità di una casa editrice che pubblica su Amazon KDP. Controlli che un testo non esponga l'editore a rimozione del titolo, blocco dell'account o responsabilità legale.

Controlla:
1. MATERIALE DI TERZI: brani citati, testi di canzoni, poesie, traduzioni, tabelle, immagini descritte, contenuti riconducibili a un'opera protetta. Qualsiasi riproduzione di testo altrui è `bloccante`.
2. MARCHI E PERSONE REALI: nomi di aziende, prodotti, personaggi pubblici usati in modo improprio, affermazioni negative su persone identificabili (rischio diffamazione), uso di un nome altrui in modo che suggerisca un'approvazione.
3. CONSULENZA PROFESSIONALE: indicazioni mediche, psicologiche, legali, fiscali o di investimento formulate come prescrizioni ("prendi", "investi", "denuncia così"). Vanno riformulate come informazione divulgativa, con rinvio a un professionista.
4. PROMESSE DI RISULTATO: guadagni, guarigioni, risultati garantiti, "in 7 giorni otterrai". Sono vietate nella scheda prodotto e sconsigliate nel testo.
5. CONTENUTI A RISCHIO: istruzioni pericolose, contenuti sessuali espliciti non dichiarati, incitamento all'odio, dati personali di terzi.
6. COERENZA CON LA PROMESSA DEL LIBRO: il capitolo mantiene ciò che titolo e descrizione promettono? Un libro che non mantiene la promessa genera resi e recensioni negative.

Gravità: `bloccante` se il titolo rischia la rimozione o una causa; `importante` se serve un'avvertenza o una riformulazione; `minore` per i dettagli.

""" + ReviewAgent.OUTPUT_CONTRACT


@register
class Conformita(ReviewAgent):
    name = "conformita"
    title = "Conformità del testo"
    description = (
        "Controlla il testo rispetto alle regole di contenuto KDP e ai rischi legali: "
        "materiale di terzi, marchi, persone reali, consulenza professionale, promesse di risultato."
    )

    def system(self, ctx: AgentContext) -> list[str]:
        return [COMPLIANCE_RULES]

    def user(self, ctx: AgentContext) -> str:
        promise = f"Promessa del libro: {ctx.spec.promise}\n" if ctx.spec.promise else ""
        audience = f"Lettore tipo: {ctx.spec.audience}\n" if ctx.spec.audience else ""
        return f"""{promise}{audience}Controlla la conformità di questo capitolo.

---
{ctx.text}
---"""


# --------------------------------------------------------------------------
# Correttore di bozze
# --------------------------------------------------------------------------
PROOFREADER_RULES = """Sei un correttore di bozze. Leggi parola per parola, non per il senso.

Segnala:
1. Refusi, lettere invertite, parole doppie ("di di"), spazi doppi.
2. Accenti e apostrofi: perché/perchè, è/e, sé/se, qual è (mai "qual'è"), po'/pò, un'altro (errato) / un altro.
3. Accordi di genere e numero, concordanza dei tempi, congiuntivi.
4. Punteggiatura: virgola fra soggetto e verbo, spazi prima dei segni, virgolette e parentesi non chiuse, puntini di sospensione irregolari.
5. Maiuscole incoerenti, numeri scritti a volte in cifre a volte in lettere, unità di misura non uniformi.
6. Ripetizioni ravvicinate della stessa parola a meno di due righe di distanza.
7. Frasi rimaste a metà o sintassi che non chiude.

Ogni segnalazione ha gravità `minore`, tranne le frasi incomplete e le parole sbagliate che cambiano il senso, che sono `importante`.
In `quote` metti la porzione di testo sbagliata, in `suggestion` la stessa porzione corretta.

""" + ReviewAgent.OUTPUT_CONTRACT


@register
class Correttore(ReviewAgent):
    name = "correttore"
    title = "Correttore di bozze"
    description = (
        "Rilettura parola per parola: refusi, accenti e apostrofi, accordi, punteggiatura, "
        "maiuscole, ripetizioni ravvicinate."
    )

    def system(self, ctx: AgentContext) -> list[str]:
        return [PROOFREADER_RULES]

    def user(self, ctx: AgentContext) -> str:
        return f"""Correggi le bozze di questo capitolo (lingua: {ctx.spec.language}).

---
{ctx.text}
---"""


# --------------------------------------------------------------------------
# Editor di sviluppo (livello libro)
# --------------------------------------------------------------------------
STRUCTURAL_RULES = """Sei un editor di sviluppo. Non guardi le frasi: guardi il libro come oggetto unico.

Ricevi la scaletta e, per ogni capitolo, l'apertura, la chiusura e una sintesi. Controlla:
1. PROGRESSIONE: ogni capitolo aggiunge qualcosa? Ce n'è uno che si potrebbe togliere senza che il lettore se ne accorga?
2. SOVRAPPOSIZIONI: due capitoli che dicono la stessa cosa con parole diverse.
3. CONTRADDIZIONI: un capitolo afferma qualcosa che un altro smentisce.
4. PROMESSE NON MANTENUTE: qualcosa annunciato nell'introduzione e mai trattato, o un capitolo che promette nel titolo ciò che non contiene.
5. ORDINE: un concetto usato prima di essere spiegato.
6. EQUILIBRIO: capitoli molto più lunghi o molto più corti degli altri senza una ragione.
7. APERTURE E CHIUSURE: capitoli che cominciano tutti nello stesso modo (è il difetto più visibile in un libro scritto a blocchi).

Indica sempre il numero di capitolo nel campo `chapter`.

""" + ReviewAgent.OUTPUT_CONTRACT


@register
class EditorSviluppo(ReviewAgent):
    name = "editor-sviluppo"
    title = "Editor di sviluppo"
    description = (
        "Guarda il libro nel suo insieme: progressione, sovrapposizioni fra capitoli, "
        "contraddizioni, promesse non mantenute, aperture tutte uguali."
    )
    max_tokens = 12000

    def system(self, ctx: AgentContext) -> list[str]:
        return [STRUCTURAL_RULES, prompts.book_bible(ctx.spec, ctx.outline)]

    def user(self, ctx: AgentContext) -> str:
        return f"""Esamina la struttura di questo libro.

{ctx.text}"""

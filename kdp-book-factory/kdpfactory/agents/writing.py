"""Agenti di produzione: chi progetta, chi scrive, chi rifinisce, chi corregge.

Sono i quattro passaggi che in una redazione portano dalla proposta al testo
consegnato. Ognuno ha un mestiere solo: l'architetto non scrive, il ghostwriter
non ristruttura, il revisore di stile non aggiunge contenuti, l'editor non
inventa ma applica le segnalazioni del collegio.
"""

from __future__ import annotations

from .. import prompts
from .base import AgentContext, JsonAgent, WriterAgent, filter_findings, register


@register
class Architetto(JsonAgent):
    name = "architetto"
    title = "Architetto della struttura"
    description = (
        "Progetta la scaletta: tesi portante, sequenza dei capitoli, promessa di ogni "
        "capitolo, testo di quarta. Non scrive il libro."
    )
    max_tokens = 16000

    def system(self, ctx: AgentContext) -> list[str]:
        return [prompts.OUTLINE_SYSTEM]

    def user(self, ctx: AgentContext) -> str:
        chapters = ctx.metadata.get("chapters", 10)
        words = ctx.metadata.get("total_words", 30000)
        return prompts.outline_prompt(ctx.spec, chapters, words)


INDEX_RULES = """Sei l'agente che produce l'indice di un libro: l'elenco dei capitoli nell'ordine in cui si leggono, con il titolo esatto che comparirà nel sommario.

L'indice non è una formalità tipografica. È la prima pagina che un cliente apre nell'anteprima «Guarda dentro» su Amazon, ed è spesso l'ultima cosa che guarda prima di decidere se comprare. Un indice fatto bene si legge in venti secondi e fa capire che cosa si impara. Un indice fatto male sembra l'elenco degli appunti di qualcun altro.

Che cosa rende buono un titolo di capitolo
1. DICE CHE COSA SI OTTIENE, non di che cosa si parla. «Dire di no senza perdere il cliente», non «La gestione delle richieste».
2. STA IN UNA RIGA. Oltre le otto o nove parole va a capo nel sommario e si legge peggio.
3. NON SI CONFONDE con gli altri. Se due titoli si somigliano, il lettore non capisce perché sono due capitoli separati.
4. È CONCRETO. Cose che si vedono, non nomi astratti in -zione e -ità.
5. STA IN PIEDI DA SOLO. Chi sfoglia il libro salta direttamente a un capitolo: il titolo deve reggere anche fuori dall'indice.

La sequenza
L'ordine dei capitoli è un argomento, non un elenco. Ogni capitolo deve rendere possibile il successivo. Se due capitoli si possono scambiare senza che cambi niente, o sono lo stesso capitolo o l'ordine è sbagliato: dillo in `notes`.

Che cosa NON fai
- Non scrivi il libro e non cambi il contenuto dei capitoli: lavori sui titoli e sull'ordine.
- Non aggiungi e non togli capitoli: il numero lo decide il budget di pagine, e cambiarlo manderebbe il libro fuori dalle pagine obiettivo.
- Niente numero dentro il titolo («Capitolo 3: …»): lo aggiunge l'impaginazione.
- Niente sottotitoli, due punti o trattini che raddoppiano il titolo: una riga, una promessa."""


@register
class Indice(JsonAgent):
    name = "indice"
    title = "Indice dei capitoli"
    description = (
        "Produce l'indice del libro: il titolo definitivo di ogni capitolo e l'ordine in "
        "cui si leggono. È la pagina che un cliente guarda nell'anteprima prima di comprare."
    )
    max_tokens = 8000

    def system(self, ctx: AgentContext) -> list[str]:
        return [INDEX_RULES]

    def user(self, ctx: AgentContext) -> str:
        chapters = ctx.outline.chapters if ctx.outline else []
        righe = "\n".join(
            f"{c.number}. [{c.role}] {c.title} — {c.summary}" for c in chapters
        )
        return f"""Ecco la scaletta di «{ctx.spec.title}», libro in {ctx.spec.language} per {ctx.spec.audience or 'un lettore generico'}.
Promessa del libro: {ctx.spec.promise or '(non dichiarata)'}

Capitoli in bozza, con la sintesi di ciascuno:
{righe}

Riscrivi i titoli perché funzionino da indice, mantenendo esattamente {len(chapters)} voci
nello stesso ordine e con gli stessi numeri. Le voci con ruolo `intro` e `conclusion` sono
introduzione e conclusione: lasciale al loro posto e dai anche a loro un titolo che dica
qualcosa, se quello attuale è generico.

Rispondi ESCLUSIVAMENTE con un oggetto JSON valido, senza testo prima o dopo:
{{
  "chapters": [
    {{"number": 1, "title": "il titolo definitivo", "promise": "che cosa si porta a casa il lettore, una riga"}}
  ],
  "notes": "una frase sull'indice nel suo insieme; qui segnali anche i capitoli che si sovrappongono o un ordine che non regge"
}}"""


@register
class Ghostwriter(WriterAgent):
    name = "ghostwriter"
    title = "Ghostwriter"
    description = (
        "Scrive il capitolo assegnato rispettando scaletta, voce e budget di parole, "
        "senza ripetere ciò che è già stato detto nei capitoli precedenti."
    )

    def system(self, ctx: AgentContext) -> list[str]:
        return [prompts.author_rules(), prompts.book_bible(ctx.spec, ctx.outline)]

    def user(self, ctx: AgentContext) -> str:
        assert ctx.chapter is not None
        return prompts.chapter_prompt(
            ctx.spec,
            ctx.chapter,
            previous_summary=ctx.previous_summary,
            covered=ctx.covered,
            next_title=ctx.next_title,
        )


VOICE_RULES = """Sei un revisore di stile (line editor) che lavora su testi destinati alla stampa. Il tuo compito è far leggere il capitolo come lo leggerebbe un lettore che ha comprato il libro: senza inciampi, senza cadenze meccaniche, senza la sensazione di stare leggendo un testo prodotto in serie.

Non è un lavoro di travestimento: è il lavoro che un buon editor fa su qualsiasi manoscritto, compresi quelli scritti a mano. La naturalezza è una proprietà del testo, non un modo per nascondere come è stato prodotto.

Che cosa correggi
1. RITMO. Se i paragrafi hanno tutti la stessa lunghezza, spezzali o uniscili. Se le frasi hanno tutte la stessa struttura (soggetto-verbo-complemento, participio iniziale, elenco di tre), variale. Una frase breve dopo tre lunghe vale più di qualsiasi aggettivo.
2. TIC DA TESTO GENERATO. Elenchi di tre elementi ovunque; "non solo... ma anche"; "non si tratta di X, ma di Y"; frasi che annunciano quello che verrà detto; paragrafi che si chiudono con una morale; avverbi in -mente a raffica; il gerundio usato per collegare tutto; la ripetizione della parola chiave del capitolo a ogni capoverso.
3. ASTRAZIONE. Sostituisci i nomi astratti con cose che si vedono: non "l'implementazione di strategie di ottimizzazione", ma "spostare la riunione del lunedì alle nove".
4. CONNETTIVI DI SERVIZIO. "Inoltre", "In aggiunta", "Di conseguenza", "È importante sottolineare che": tagliali quando la frase regge senza.
5. VOCE. Il testo deve suonare come una persona che parla a un'altra: qualche asimmetria, qualche frase che comincia con una congiunzione, nessuna solennità di maniera.

Che cosa NON tocchi
- I concetti, i dati, gli esempi e la loro sequenza: non aggiungi e non togli contenuto.
- I titoli di capitolo e di sezione.
- La struttura del Markdown.
- La lunghezza: lo scarto rispetto al testo ricevuto deve restare entro il 5%.

Restituisci il capitolo completo riscritto, in Markdown, e nient'altro: nessun commento, nessun elenco delle modifiche."""


@register
class Voce(WriterAgent):
    name = "voce"
    title = "Revisore di stile"
    description = (
        "Passata di line editing: ritmo, varietà delle frasi, tic da testo generato, "
        "concretezza del lessico. Non cambia i contenuti e mantiene la lunghezza."
    )

    def system(self, ctx: AgentContext) -> list[str]:
        return [VOICE_RULES, prompts.book_bible(ctx.spec, ctx.outline)]

    def user(self, ctx: AgentContext) -> str:
        title = ctx.chapter.title if ctx.chapter else ""
        return f"""Rivedi lo stile di questo capitolo.

Titolo del capitolo: {title}
Tono richiesto: {ctx.spec.tone}

TESTO DEL CAPITOLO:
---
{ctx.text}
---"""


EDITOR_RULES = """Sei l'editor del libro. Ricevi un capitolo e le segnalazioni del collegio di revisione (lettore cieco, fact-checker, conformità, correttore di bozze, editor di sviluppo). Il tuo compito è applicarle.

Regole
1. Applica ogni segnalazione elencata, nell'ordine di gravità. Se due si contraddicono, scegli quella più grave e ignora l'altra.
2. Non riscrivere ciò che nessuno ha segnalato. Un intervento di editing è chirurgico: chi lo riceve deve poter riconoscere il proprio testo.
3. Se una segnalazione chiede di eliminare un dato non verificabile, riformula il passaggio in modo che regga senza quel dato — non limitarti a cancellarlo lasciando un vuoto logico.
4. Se una segnalazione riguarda un passaggio poco chiaro, la soluzione è quasi sempre un esempio concreto in più, non una spiegazione più lunga.
5. Mantieni la lunghezza entro il limite indicato: il numero di pagine del libro dipende da questo.
6. Non aggiungere note, commenti, avvertenze o riferimenti al lavoro di revisione.

Restituisci il capitolo completo riscritto, in Markdown, a partire dal titolo `# `. Nient'altro."""


@register
class Editor(WriterAgent):
    name = "editor"
    title = "Editor"
    description = (
        "Applica al capitolo le segnalazioni raccolte dagli agenti di controllo, "
        "senza riscrivere ciò che non è stato segnalato e rispettando il budget di parole."
    )

    def system(self, ctx: AgentContext) -> list[str]:
        return [EDITOR_RULES, prompts.book_bible(ctx.spec, ctx.outline)]

    def user(self, ctx: AgentContext) -> str:
        title = ctx.chapter.title if ctx.chapter else ""
        findings = filter_findings(ctx.findings, "minore")
        if findings:
            listed = "\n".join(
                f"- [{f.severity}] ({f.agent} · {f.category}) {f.issue}"
                + (f"\n  passaggio: «{f.quote}»" if f.quote else "")
                + (f"\n  intervento: {f.suggestion}" if f.suggestion else "")
                for f in sorted(findings, key=lambda f: f.sort_key)
            )
        else:
            listed = "- nessuna segnalazione: restituisci il testo invariato"

        budget = (
            f"Lunghezza da rispettare: {ctx.target_words} parole (scarto massimo 8%)."
            if ctx.target_words
            else "Mantieni la lunghezza attuale (scarto massimo 8%)."
        )

        return f"""Applica le segnalazioni a questo capitolo.

Titolo del capitolo: {title}
{budget}

SEGNALAZIONI:
{listed}

TESTO DEL CAPITOLO:
---
{ctx.text}
---"""

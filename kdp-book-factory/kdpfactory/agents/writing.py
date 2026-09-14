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

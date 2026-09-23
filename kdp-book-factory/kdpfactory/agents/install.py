"""Esporta il collegio come subagent di Claude Code (`.claude/agents/*.md`).

Stesso prompt, due modi di usarlo: dentro la pipeline (`kdpfactory all`) oppure
a mano da Claude Code, quando si vuole far leggere un capitolo a un solo agente
e discuterne. Il registro Python resta l'unica sorgente: i file si rigenerano.
"""

from __future__ import annotations

from pathlib import Path

from ..models import BookSpec
from .base import REGISTRY, AgentContext

HEADER = """---
name: {name}
description: {description}
tools: {tools}
---

"""

USAGE = """
## Come lavorare

Ricevi il testo da esaminare nel messaggio, oppure il percorso di un file del
progetto (`books/<slug>/manuscript/NN.md`): in quel caso leggilo prima di
rispondere. Non modificare i file: il tuo compito è {compito}.

## Formato della risposta

Elenca le segnalazioni dalla più grave, una per riga, in questa forma:

    [gravità] categoria — che cosa non va
    «passaggio citato alla lettera»
    → che cosa fare

Le gravità sono `bloccante`, `importante`, `minore`. Chiudi con una frase di
giudizio complessivo. Se ti viene chiesto JSON, usa le stesse chiavi del
rapporto della pipeline: `severity`, `category`, `issue`, `quote`, `suggestion`.
"""

#: Il contratto JSON serve alla pipeline, non a una conversazione: viene tolto
#: dalla versione esportata e sostituito dal formato leggibile qui sopra.
JSON_CONTRACT_MARKER = "Rispondi ESCLUSIVAMENTE con un oggetto JSON"

#: Fallback per un agente strumentale che non dichiara le proprie istruzioni:
#: dice come si esegue *il suo* controllo, non quello di un altro.
TOOL_USAGE = """Questo agente non usa il modello: misura, e riporta quello che ha misurato.

```bash
cd kdp-book-factory
python3 -m kdpfactory review <slug> --agents {name}
```

Riporta le segnalazioni così come escono, raggruppate per categoria, e indica
quali sono bloccanti."""


def _sample_context() -> AgentContext:
    """Contesto minimo usato solo per rendere leggibile il prompt esportato."""
    return AgentContext(spec=BookSpec(slug="esempio", title="(titolo del libro)"))


def render_agent_markdown(agent) -> str:
    ctx = _sample_context()
    try:
        blocks = agent.system(ctx)
    except Exception:  # pragma: no cover - agenti senza prompt (impaginazione)
        blocks = []

    body = HEADER.format(
        name=agent.name,
        description=agent.description.replace("\n", " ").strip(),
        # L'agente di impaginazione esegue un comando, gli altri leggono file.
        tools="Read, Grep, Glob, Bash" if not blocks else "Read, Grep, Glob",
    )
    body += f"# {agent.title}\n\n{agent.description}\n\n"

    if not blocks:
        # Agente strumentale: non ha un prompt, ha un comando. Le istruzioni
        # sono le sue, non quelle del primo agente strumentale che fu scritto.
        istruzioni = agent.istruzioni or TOOL_USAGE.format(name=agent.name)
        return body + "## Come lavorare\n\n" + istruzioni.rstrip() + "\n"

    rules = blocks[0]  # il primo blocco sono le regole del ruolo
    body += rules.split(JSON_CONTRACT_MARKER)[0].rstrip() + "\n"
    compito = (
        "segnalare, non correggere" if agent.stage == "controllo" else "produrre il testo richiesto"
    )
    body += USAGE.format(compito=compito)
    return body


def install_claude_code_agents(target: Path) -> list[Path]:
    """Scrive un file per agente in `target` (di solito `.claude/agents`)."""
    target.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for agent in REGISTRY.values():
        path = target / f"{agent.name}.md"
        path.write_text(render_agent_markdown(agent), encoding="utf-8")
        written.append(path)
    return written

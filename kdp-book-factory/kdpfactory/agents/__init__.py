"""Collegio editoriale: gli agenti che scrivono il libro e quelli che lo controllano.

Produzione
    architetto      progetta la struttura
    ghostwriter     scrive i capitoli
    voce            revisione di stile (ritmo, varietà, tic da testo generato)
    editor          applica le segnalazioni del collegio

Controllo
    lettore-cieco   legge senza sapere nulla del progetto: dove ci si perde
    fact-checker    affermazioni, numeri e citazioni non verificabili
    conformita      regole di contenuto KDP e rischi legali
    correttore      bozze: refusi, accenti, punteggiatura, accordi
    editor-sviluppo struttura del libro nel suo insieme
    impaginazione   difetti tipografici misurati sul PDF (senza modello)
"""

# Gli import registrano gli agenti nel registro.
from . import layout, review, writing  # noqa: F401,E402
from .base import (  # noqa: F401
    REGISTRY,
    Agent,
    AgentContext,
    AgentFinding,
    AgentResult,
    JsonAgent,
    ReviewAgent,
    WriterAgent,
    agents_by_stage,
    filter_findings,
    get_agent,
    review_agents,
)
from .panel import (  # noqa: F401,E402
    CHAPTER_REVIEWERS,
    DEFAULT_QUALITY,
    QUALITY_LEVELS,
    ReviewReport,
    apply_revisions,
    describe_panel,
    run_review,
    voice_pass,
)

__all__ = [
    "REGISTRY",
    "Agent",
    "AgentContext",
    "AgentFinding",
    "AgentResult",
    "CHAPTER_REVIEWERS",
    "DEFAULT_QUALITY",
    "QUALITY_LEVELS",
    "ReviewReport",
    "apply_revisions",
    "describe_panel",
    "get_agent",
    "review_agents",
    "run_review",
    "voice_pass",
]

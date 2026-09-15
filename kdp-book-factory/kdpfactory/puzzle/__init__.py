"""Seconda linea di produzione: libri di enigmi di deduzione.

A differenza dei libri in prosa, qui non serve un modello linguistico: i casi
si generano da un seme e si dimostrano corretti con un solver (soluzione unica,
nessun indizio superfluo). Quello che il modello non tocca, non può sbagliarlo.
"""

from . import solver  # noqa: F401
from .generator import GenerationError, PuzzleBook, generate_book  # noqa: F401
from .model import Attribute, Case, Clue, Finale, Suspect  # noqa: F401

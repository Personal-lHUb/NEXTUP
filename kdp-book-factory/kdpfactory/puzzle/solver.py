"""Solver: dimostra che un caso è corretto prima che finisca in stampa.

Tre proprietà, tutte verificate su ogni caso generato:

- **unicità**: applicando tutti gli indizi resta esattamente un sospetto;
- **necessità**: togliendo un indizio qualsiasi i sospetti tornano più di uno,
  quindi nel libro non finiscono indizi inutili;
- **tracciabilità**: si sa quanti sospetti elimina ogni indizio, e con quello si
  scrive la soluzione ragionata in fondo al libro.

Un enigma stampato sbagliato non si corregge: questi controlli sono il motivo
per cui questa linea di produzione non ha bisogno di un modello linguistico.
"""

from __future__ import annotations

from dataclasses import dataclass

from .model import Case, Clue, Suspect


def survivors(suspects: list[Suspect], clues) -> list[Suspect]:
    """Sospetti compatibili con tutti gli indizi."""
    remaining = suspects
    for clue in clues:
        remaining = [s for s in remaining if clue.keeps(s)]
    return remaining


def is_unique(suspects: list[Suspect], clues) -> bool:
    return len(survivors(suspects, clues)) == 1


def eliminated_by(clue: Clue, remaining: list[Suspect]) -> int:
    return sum(1 for s in remaining if not clue.keeps(s))


def minimize(suspects: list[Suspect], clues: list[Clue]) -> list[Clue]:
    """Toglie gli indizi ridondanti mantenendo la soluzione unica.

    Si parte dalla coda: gli indizi scelti per ultimi sono i più specifici e
    quelli che più spesso diventano superflui.
    """
    kept = list(clues)
    for clue in reversed(list(clues)):
        candidate = [c for c in kept if c is not clue]
        if candidate and is_unique(suspects, candidate):
            kept = candidate
    return kept


def all_necessary(suspects: list[Suspect], clues: list[Clue]) -> bool:
    """Vero se nessun indizio può essere tolto senza perdere l'unicità."""
    for clue in clues:
        if is_unique(suspects, [c for c in clues if c is not clue]):
            return False
    return True


@dataclass
class Step:
    index: int          # numero dell'indizio nel libro (da 1)
    before: int
    after: int

    @property
    def removed(self) -> int:
        return self.before - self.after


def trace(suspects: list[Suspect], clues: list[Clue]) -> list[Step]:
    """Quanti sospetti restano dopo ogni indizio, nell'ordine di stampa."""
    steps: list[Step] = []
    remaining = suspects
    for index, clue in enumerate(clues, start=1):
        before = len(remaining)
        remaining = [s for s in remaining if clue.keeps(s)]
        steps.append(Step(index=index, before=before, after=len(remaining)))
    return steps


@dataclass
class Verdict:
    ok: bool
    problems: list[str]
    solution: Suspect | None = None

    def __bool__(self) -> bool:  # pragma: no cover - comodità
        return self.ok


def verify(case: Case) -> Verdict:
    """Controllo completo di un caso, da eseguire prima di impaginarlo."""
    problems: list[str] = []
    remaining = survivors(case.suspects, case.clues)

    if len(remaining) == 0:
        problems.append("Nessun sospetto sopravvive agli indizi: il caso è irrisolvibile.")
    elif len(remaining) > 1:
        names = ", ".join(s.name for s in remaining[:5])
        problems.append(f"{len(remaining)} soluzioni possibili ({names}…): il caso è ambiguo.")
    elif remaining[0] != case.culprit:
        problems.append(
            f"La soluzione ({remaining[0].name}) non è il colpevole dichiarato "
            f"({case.culprit.name})."
        )

    if not all_necessary(case.suspects, case.clues):
        problems.append("Almeno un indizio è superfluo: va tolto o sostituito.")

    names = [s.name for s in case.suspects]
    if len(set(names)) != len(names):
        problems.append("Due sospetti hanno lo stesso nome.")

    combinations = {s.attrs for s in case.suspects}
    if len(combinations) != len(case.suspects):
        problems.append("Due sospetti hanno la stessa combinazione di attributi.")

    return Verdict(
        ok=not problems,
        problems=problems,
        solution=remaining[0] if len(remaining) == 1 else None,
    )

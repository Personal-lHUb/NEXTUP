"""Generazione dei casi: cast, indizi, selezione, verifica.

Il generatore non "inventa" un enigma e spera che funzioni. Costruisce un
insieme di affermazioni tutte vere sul colpevole, ne sceglie un sottoinsieme
che isola una sola persona, elimina quelle superflue e poi fa verificare il
risultato dal solver. Se la verifica non passa, il caso viene buttato e
rigenerato: in stampa arriva solo ciò che è dimostrato corretto.

Tutto dipende da un seme: stesso seme, stesso libro.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass, field
from random import Random

from . import solver
from .model import (
    Attribute,
    Case,
    Cleared,
    Clue,
    DiffersFrom,
    ExactlyOneTrue,
    Finale,
    FinaleClue,
    FinalePair,
    IfThen,
    Is,
    IsNot,
    NotBoth,
    OneOf,
    SameAs,
    Suspect,
)
from .theme import ATTRIBUTES, CASES, HONORIFICS, SURNAMES, CaseTheme

MAX_CLUES = 16
MIN_FINALE_CLUES = 5
#: quanti dei dodici casi devono essere citati per nome nel finale. Non si
#: pretende dodici su dodici: con la soluzione unica e nessun indizio superfluo,
#: pretendere anche la copertura totale renderebbe il finale quasi impossibile
#: da generare. Non è una rinuncia: per applicare un confronto il lettore deve
#: conoscere gli attributi di *tutte* le righe della griglia, quindi tutte e
#: dodici le risposte servono comunque.
MIN_FINALE_COVERAGE = 8


#: frazione di sospetti che un buon indizio dovrebbe eliminare: puntare al
#: massimo produrrebbe enigmi da tre indizi, che non si risolvono, si leggono
TARGET_FRACTION = 0.38
SPREAD = 0.055
#: quanto si penalizza un tipo di indizio già usato nello stesso caso
VARIETY_DECAY = 0.45


def min_clues_for(cast_size: int) -> int:
    """Sotto questa soglia l'enigma è una formalità: pochi indizi fortissimi
    portano alla soluzione senza che il lettore ragioni."""
    return max(5, math.ceil(math.log2(cast_size)))


#: quanto conviene un indizio "difficile" rispetto a uno immediato
KIND_BIAS = {
    "is": 0.7,
    "is_not": 1.0,
    "cleared": 0.9,
    "one_of": 1.15,
    "same_as": 1.2,
    "differs_from": 1.2,
    "if_then": 1.45,
    "not_both": 1.45,
    "exactly_one": 1.7,
}


class GenerationError(RuntimeError):
    pass


# --------------------------------------------------------------------------
# Cast
# --------------------------------------------------------------------------
def build_cast(theme: CaseTheme, rng: Random) -> tuple[dict[str, Attribute], list[Suspect]]:
    """Il cast è il prodotto cartesiano degli attributi: nessun buco, nessun doppione."""
    attributes: dict[str, Attribute] = {}
    value_lists: list[tuple[str, ...]] = []
    for key, count in theme.plan:
        base = ATTRIBUTES[key]
        values = tuple(rng.sample(base.values, count))
        attributes[key] = Attribute(
            key=base.key,
            label=base.label,
            noun=base.noun,
            values=values,
            template=base.template,
            negative_template=base.negative_template,
            to_be=base.to_be,
            listed_article=base.listed_article,
        )
        value_lists.append(values)

    keys = [key for key, _ in theme.plan]
    combinations = list(itertools.product(*value_lists))
    if len(combinations) > len(SURNAMES):
        raise GenerationError(
            f"Caso {theme.number}: servono {len(combinations)} cognomi, ne ho {len(SURNAMES)}."
        )

    surnames = rng.sample(SURNAMES, len(combinations))
    suspects = [
        Suspect(
            name=f"{rng.choice(HONORIFICS)} {surname}",
            attrs=tuple(zip(keys, combination, strict=True)),
        )
        for surname, combination in zip(surnames, combinations, strict=True)
    ]
    rng.shuffle(suspects)
    return attributes, suspects


# --------------------------------------------------------------------------
# Indizi candidati (tutti veri sul colpevole)
# --------------------------------------------------------------------------
def candidate_clues(
    culprit: Suspect,
    cast: list[Suspect],
    attributes: dict[str, Attribute],
    kinds: tuple[str, ...],
    rng: Random,
) -> list[Clue]:
    keys = list(attributes)
    truth = culprit.as_dict()
    pool: list[Clue] = []

    if "is" in kinds:
        pool += [Is(key, truth[key]) for key in keys]

    if "is_not" in kinds:
        pool += [
            IsNot(key, value)
            for key in keys
            for value in attributes[key].values
            if value != truth[key]
        ]

    if "one_of" in kinds:
        for key in keys:
            others = [v for v in attributes[key].values if v != truth[key]]
            for size in (1, 2):
                if len(others) < size:
                    continue
                for _ in range(2):
                    chosen = rng.sample(others, size)
                    values = tuple(sorted([truth[key], *chosen]))
                    pool.append(OneOf(key, values))

    if "if_then" in kinds:
        for first, second in itertools.permutations(keys, 2):
            for value in attributes[first].values:
                if value == truth[first]:
                    pool.append(IfThen(first, value, second, truth[second]))
                else:
                    # Condizione falsa sul colpevole: l'affermazione resta vera e
                    # colpisce chi la condizione ce l'ha davvero.
                    for consequence in attributes[second].values:
                        pool.append(IfThen(first, value, second, consequence))

    if "not_both" in kinds:
        for first, second in itertools.combinations(keys, 2):
            for value_a in attributes[first].values:
                for value_b in attributes[second].values:
                    if value_a == truth[first] and value_b == truth[second]:
                        continue
                    pool.append(NotBoth(first, value_a, second, value_b))

    if "same_as" in kinds or "differs_from" in kinds:
        for key in keys:
            same = [s for s in cast if s is not culprit and s.get(key) == truth[key]]
            different = [s for s in cast if s.get(key) != truth[key]]
            if "same_as" in kinds:
                for other in rng.sample(same, min(3, len(same))):
                    pool.append(SameAs(key, other.name, truth[key]))
            if "differs_from" in kinds:
                for other in rng.sample(different, min(3, len(different))):
                    pool.append(DiffersFrom(key, other.name, other.get(key)))

    if "cleared" in kinds:
        innocents = [s.name for s in cast if s is not culprit]
        for _ in range(4):
            size = rng.randint(2, 4)
            pool.append(Cleared(tuple(rng.sample(innocents, size))))

    if "exactly_one" in kinds:
        simple = [Is(key, value) for key in keys for value in attributes[key].values]
        for _ in range(40):
            parts = tuple(rng.sample(simple, 3))
            if sum(1 for part in parts if part.keeps(culprit)) == 1:
                pool.append(ExactlyOneTrue(parts))

    rng.shuffle(pool)
    return pool


# --------------------------------------------------------------------------
# Selezione
# --------------------------------------------------------------------------
def select_clues(
    cast: list[Suspect], pool: list[Clue], rng: Random, *, top_choices: int = 3
) -> list[Clue]:
    """Sceglie indizi finché resta un sospetto solo, preferendo quelli che
    fanno ragionare a quelli che risolvono da soli."""
    chosen: list[Clue] = []
    used_kinds: dict[str, int] = {}
    remaining = list(cast)

    while len(remaining) > 1:
        scored = []
        for clue in pool:
            if clue in chosen:
                continue
            removed = solver.eliminated_by(clue, remaining)
            if removed == 0 or removed == len(remaining):
                continue  # inutile, oppure elimina anche il colpevole
            fraction = removed / len(remaining)
            fit = math.exp(-((fraction - TARGET_FRACTION) ** 2) / SPREAD)
            # Un caso fatto di sette "exactly one of these" si legge come un
            # modulo fiscale: ogni tipo già usato vale progressivamente meno.
            variety = VARIETY_DECAY ** used_kinds.get(clue.kind, 0)
            scored.append((fit * KIND_BIAS.get(clue.kind, 1.0) * variety, clue))
        if not scored:
            raise GenerationError("Nessun indizio utile: cast o tipi di indizio troppo poveri.")
        scored.sort(key=lambda item: item[0], reverse=True)
        _, clue = rng.choice(scored[:top_choices])
        chosen.append(clue)
        used_kinds[clue.kind] = used_kinds.get(clue.kind, 0) + 1
        remaining = [s for s in remaining if clue.keeps(s)]
        if len(chosen) > MAX_CLUES * 2:
            raise GenerationError("Troppi indizi senza arrivare a una soluzione unica.")

    return chosen


def generate_case(theme: CaseTheme, rng: Random, attempts: int = 60) -> Case:
    last_error = "nessun tentativo"
    for _ in range(attempts):
        try:
            attributes, cast = build_cast(theme, rng)
            culprit = rng.choice(cast)
            pool = candidate_clues(culprit, cast, attributes, theme.kinds, rng)
            clues = solver.minimize(cast, select_clues(cast, pool, rng))
        except GenerationError as error:
            last_error = str(error)
            continue

        minimum = theme.min_clues or min_clues_for(len(cast))
        if not minimum <= len(clues) <= MAX_CLUES:
            last_error = f"{len(clues)} indizi, fuori dall'intervallo {minimum}-{MAX_CLUES}"
            continue

        rng.shuffle(clues)
        case = Case(
            number=theme.number,
            title=theme.title,
            setting=theme.setting,
            attributes=attributes,
            suspects=cast,
            clues=clues,
            culprit=culprit,
        )
        verdict = solver.verify(case)
        if not verdict.ok:
            last_error = "; ".join(verdict.problems)
            continue
        case.trace = [
            (step.index, step.before, step.after) for step in solver.trace(cast, clues)
        ]
        return case

    raise GenerationError(f"Caso {theme.number} non generato in {attempts} tentativi: {last_error}")


# --------------------------------------------------------------------------
# Finale
# --------------------------------------------------------------------------
#: nel finale un confronto fra attributi vale più di uno scarto secco, e
#: un'uguaglianza vale più di una differenza: sono le frasi che fanno dedurre
FINALE_MODE_BIAS = {"same": 2.2, "differs": 1.0, "not_case": 0.45}


def _parts(clue) -> tuple:
    return (clue.first, clue.second) if isinstance(clue, FinalePair) else (clue,)


def _comparisons(clue) -> set[tuple[int, str]]:
    return {(part.case_number, part.attr) for part in _parts(clue) if part.attr}


def _finale_appeal(clue, used: set[tuple[int, str]]) -> float:
    appeal = 1.0
    for part in _parts(clue):
        appeal *= FINALE_MODE_BIAS.get(part.mode, 1.0)
        if part.attr and (part.case_number, part.attr) in used:
            appeal *= 0.3   # lo stesso confronto due volte annoia
    return appeal


def _finale_requirements(attempt: int, attempts: int, cases: int) -> tuple[int, int]:
    """Requisiti estetici del finale, via via più indulgenti."""
    if attempt < attempts // 3:
        return cases, MIN_FINALE_CLUES                  # cita tutti i casi
    if attempt < 2 * attempts // 3:
        return MIN_FINALE_COVERAGE, MIN_FINALE_CLUES    # ne cita almeno otto
    return 4, 3                                         # purché sia un enigma


def shared_attributes(cases: list[Case]) -> tuple[str, ...]:
    """Attributi presenti in tutti i casi: solo su quelli si possono confrontare
    colpevoli di vetture diverse."""
    common = set(cases[0].attributes)
    for case in cases[1:]:
        common &= set(case.attributes)
    order = list(ATTRIBUTES)
    return tuple(sorted(common, key=order.index))


def generate_finale(cases: list[Case], rng: Random, attempts: int = 900) -> Finale:
    """Il finale si gioca sui dodici colpevoli: senza le dodici risposte non parte."""
    from .theme import FINALE_SETTING, FINALE_TITLE

    finale_attrs = shared_attributes(cases)
    if len(finale_attrs) < 2:
        raise GenerationError(
            "I casi non condividono abbastanza attributi per costruire il finale."
        )
    attributes = {key: ATTRIBUTES[key] for key in finale_attrs}
    suspects = [
        Suspect(
            name=case.culprit.name,
            attrs=(("case", str(case.number)),)
            + tuple((key, case.culprit.get(key)) for key in finale_attrs),
        )
        for case in cases
    ]

    total_cases = {int(s.get("case")) for s in suspects}
    last_error = "nessun tentativo"

    for attempt_index in range(attempts):
        mastermind = rng.choice(suspects)
        own_case = mastermind.get("case")

        singles: list[FinaleClue] = []
        for suspect in suspects:
            if suspect.get("case") == own_case:
                continue
            case_number = int(suspect.get("case"))
            singles.append(FinaleClue(mode="not_case", case_number=case_number))
            for key in finale_attrs:
                mode = "same" if mastermind.get(key) == suspect.get(key) else "differs"
                singles.append(
                    FinaleClue(mode=mode, case_number=case_number, attr=key, value=suspect.get(key))
                )

        # Indizi doppi: due confronti in una frase, così sei o sette indizi
        # bastano a chiamare in causa tutti e dodici i casi.
        pool: list = list(singles)
        for first, second in itertools.combinations(singles, 2):
            if first.case_number == second.case_number:
                continue
            if first.mode == "not_case" and second.mode == "not_case":
                continue  # due scarti in fila non fanno ragionare nessuno
            pair = FinalePair(first=first, second=second)
            if pair.keeps(mastermind):
                pool.append(pair)
        rng.shuffle(pool)

        chosen: list = []
        covered: set[int] = set()
        used_comparisons: set[tuple[int, str]] = set()
        remaining = list(suspects)
        while len(remaining) > 1:
            scored = []
            for clue in pool:
                if clue in chosen or not clue.keeps(mastermind):
                    continue
                removed = sum(1 for s in remaining if not clue.keeps(s))
                if removed == 0:
                    continue
                fraction = removed / len(remaining)
                # Bersaglio basso: un indizio che ne elimina pochi obbliga a
                # usarne di più, e più indizi vuol dire più casi chiamati in causa.
                fit = math.exp(-((fraction - 0.2) ** 2) / 0.02)
                new_cases = len(set(clue.cases) - covered)
                score = fit * (1 + 1.5 * new_cases) * _finale_appeal(clue, used_comparisons)
                scored.append((score, clue))
            if not scored:
                break
            scored.sort(key=lambda item: item[0], reverse=True)
            _, clue = rng.choice(scored[: min(3, len(scored))])
            chosen.append(clue)
            covered.update(clue.cases)
            used_comparisons.update(_comparisons(clue))
            remaining = [s for s in remaining if clue.keeps(s)]

        if len(remaining) != 1 or remaining[0] != mastermind:
            last_error = "soluzione non unica"
            continue

        chosen = solver.minimize(suspects, chosen)
        covered = {case for clue in chosen for case in clue.cases} | {int(own_case)}
        # Le pretese estetiche calano col passare dei tentativi; quelle di
        # correttezza (soluzione unica, nessun indizio superfluo) mai. Meglio un
        # finale che cita otto casi invece di dodici che nessun finale.
        required_cases, required_clues = _finale_requirements(
            attempt_index, attempts, len(total_cases)
        )
        if len(covered) < required_cases:
            last_error = f"il finale cita solo {len(covered)} casi su {len(total_cases)}"
            continue
        if len(chosen) < required_clues:
            last_error = f"solo {len(chosen)} indizi: finale troppo facile"
            continue

        rng.shuffle(chosen)
        return Finale(
            title=FINALE_TITLE,
            setting=FINALE_SETTING,
            attributes=attributes,
            suspects=suspects,
            clues=chosen,
            mastermind=mastermind,
        )

    raise GenerationError(f"Finale non generato: {last_error}")


# --------------------------------------------------------------------------
# Libro
# --------------------------------------------------------------------------
@dataclass
class PuzzleBook:
    seed: int
    cases: list[Case] = field(default_factory=list)
    finale: Finale | None = None
    example: Case | None = None      # il caso svolto nelle prime pagine

    @property
    def suspects_total(self) -> int:
        return sum(len(case.suspects) for case in self.cases)

    @property
    def clues_total(self) -> int:
        return sum(len(case.clues) for case in self.cases) + len(
            self.finale.clues if self.finale else []
        )

    def answers(self) -> dict:
        return {
            "seed": self.seed,
            "cases": [case.to_dict() for case in self.cases],
            "finale": {
                "clues": self.finale.clue_texts() if self.finale else [],
                "mastermind": self.finale.mastermind.name if self.finale else "",
                "case": self.finale.mastermind.get("case") if self.finale else "",
            },
        }


def generate_book(seed: int, themes: tuple[CaseTheme, ...] = CASES) -> PuzzleBook:
    from .theme import EXAMPLE

    rng = Random(seed)
    example = generate_case(EXAMPLE, rng)
    cases = [generate_case(theme, rng) for theme in themes]
    finale = generate_finale(cases, rng)
    return PuzzleBook(seed=seed, cases=cases, finale=finale, example=example)

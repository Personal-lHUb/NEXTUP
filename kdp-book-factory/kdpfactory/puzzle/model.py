"""Modello di un caso di deduzione: sospetti, indizi, soluzione.

Un sospetto è una combinazione unica di attributi con un nome. Un indizio è una
proposizione vera sul colpevole che il lettore può verificare su ogni sospetto:
`keeps(sospetto)` dice se quel sospetto resta in gioco.

Tutto qui è verificabile a macchina, ed è il motivo per cui un libro di enigmi
si può produrre senza chiedere niente a un modello linguistico: la correttezza
non è un'opinione, è una proprietà che il solver dimostra.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar


@dataclass(frozen=True)
class Attribute:
    """Una caratteristica dei sospetti, con il modo di dirla in inglese.

    `template` e `negative_template` producono la frase al passato usata negli
    indizi: "wore a fedora", "did not drink tea".
    """

    key: str
    label: str                    # intestazione di colonna nella tabella
    noun: str                     # "hat", "coat", "drink"...
    values: tuple[str, ...]
    template: str = "wore {a} {value}"
    negative_template: str = "did not wear {a} {value}"
    to_be: str = "was"            # "were" per i nomi plurali ("gloves")
    listed_article: bool = False  # "either a hatbox or a birdcage"

    def phrase(self, value: str) -> str:
        return self.template.format(value=value, a=article_for(value))

    def negative_phrase(self, value: str) -> str:
        return self.negative_template.format(value=value, a=article_for(value))

    def listed(self, value: str) -> str:
        return f"{article_for(value)} {value}" if self.listed_article else value

    @property
    def that_of(self) -> str:
        return "those of" if self.to_be == "were" else "that of"


@dataclass(frozen=True)
class Suspect:
    name: str
    attrs: tuple[tuple[str, str], ...]   # ((chiave, valore), ...) — hashable

    def get(self, key: str) -> str:
        for attribute_key, value in self.attrs:
            if attribute_key == key:
                return value
        raise KeyError(key)

    def as_dict(self) -> dict[str, str]:
        return dict(self.attrs)


# --------------------------------------------------------------------------
# Indizi
# --------------------------------------------------------------------------
class Clue:
    """Una proposizione vera sul colpevole."""

    kind: ClassVar[str] = "clue"
    #: quanto pesa sulla difficoltà percepita (1 = immediato, 3 = ragionamento)
    weight: ClassVar[int] = 1

    def keeps(self, suspect: Suspect) -> bool:
        raise NotImplementedError

    def text(self, attributes: dict[str, Attribute]) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class Is(Clue):
    """«The culprit wore a fedora.»"""

    attr: str
    value: str
    kind: ClassVar[str] = "is"
    weight: ClassVar[int] = 1

    def keeps(self, suspect: Suspect) -> bool:
        return suspect.get(self.attr) == self.value

    def text(self, attributes: dict[str, Attribute]) -> str:
        return f"The culprit {attributes[self.attr].phrase(self.value)}."


@dataclass(frozen=True)
class IsNot(Clue):
    """«The culprit did not drink tea.»"""

    attr: str
    value: str
    kind: ClassVar[str] = "is_not"
    weight: ClassVar[int] = 1

    def keeps(self, suspect: Suspect) -> bool:
        return suspect.get(self.attr) != self.value

    def text(self, attributes: dict[str, Attribute]) -> str:
        return f"The culprit {attributes[self.attr].negative_phrase(self.value)}."


@dataclass(frozen=True)
class OneOf(Clue):
    """«The culprit's coat was either navy or olive.»"""

    attr: str
    values: tuple[str, ...]
    kind: ClassVar[str] = "one_of"
    weight: ClassVar[int] = 2

    def keeps(self, suspect: Suspect) -> bool:
        return suspect.get(self.attr) in self.values

    def text(self, attributes: dict[str, Attribute]) -> str:
        attribute = attributes[self.attr]
        listed = _join_or([attribute.listed(v) for v in self.values])
        return f"The culprit's {attribute.noun} {attribute.to_be} {listed}."


@dataclass(frozen=True)
class IfThen(Clue):
    """«If the culprit carried a violin case, then they wore a beret.»"""

    if_attr: str
    if_value: str
    then_attr: str
    then_value: str
    kind: ClassVar[str] = "if_then"
    weight: ClassVar[int] = 3

    def keeps(self, suspect: Suspect) -> bool:
        if suspect.get(self.if_attr) != self.if_value:
            return True
        return suspect.get(self.then_attr) == self.then_value

    def text(self, attributes: dict[str, Attribute]) -> str:
        condition = attributes[self.if_attr].phrase(self.if_value)
        consequence = attributes[self.then_attr].phrase(self.then_value)
        return f"If the culprit {condition}, then they {consequence}."


@dataclass(frozen=True)
class NotBoth(Clue):
    """«The culprit did not both wear a bowler and drink tea.»"""

    first_attr: str
    first_value: str
    second_attr: str
    second_value: str
    kind: ClassVar[str] = "not_both"
    weight: ClassVar[int] = 3

    def keeps(self, suspect: Suspect) -> bool:
        return not (
            suspect.get(self.first_attr) == self.first_value
            and suspect.get(self.second_attr) == self.second_value
        )

    def text(self, attributes: dict[str, Attribute]) -> str:
        first = attributes[self.first_attr].phrase(self.first_value)
        second = attributes[self.second_attr].phrase(self.second_value)
        return f"No one who {first} and {second} could be the culprit."


@dataclass(frozen=True)
class SameAs(Clue):
    """«The culprit's hat matched Mrs Wren's.»"""

    attr: str
    other_name: str
    value: str          # valore dell'altro passeggero, usato per la verifica
    kind: ClassVar[str] = "same_as"
    weight: ClassVar[int] = 2

    def keeps(self, suspect: Suspect) -> bool:
        return suspect.get(self.attr) == self.value

    def text(self, attributes: dict[str, Attribute]) -> str:
        attribute = attributes[self.attr]
        return (
            f"The culprit's {attribute.noun} {attribute.to_be} the same as "
            f"{self.other_name}'s."
        )


@dataclass(frozen=True)
class DiffersFrom(Clue):
    """«The culprit's coat was a different colour from Mr Ash's.»"""

    attr: str
    other_name: str
    value: str
    kind: ClassVar[str] = "differs_from"
    weight: ClassVar[int] = 2

    def keeps(self, suspect: Suspect) -> bool:
        return suspect.get(self.attr) != self.value

    def text(self, attributes: dict[str, Attribute]) -> str:
        attribute = attributes[self.attr]
        return (
            f"The culprit's {attribute.noun} {attribute.to_be} not the same as "
            f"{self.other_name}'s."
        )


@dataclass(frozen=True)
class Cleared(Clue):
    """«Three passengers were together in the dining car and are cleared: …»"""

    names: tuple[str, ...]
    kind: ClassVar[str] = "cleared"
    weight: ClassVar[int] = 1

    def keeps(self, suspect: Suspect) -> bool:
        return suspect.name not in self.names

    def text(self, attributes: dict[str, Attribute]) -> str:
        listed = _join_and(self.names)
        return (
            f"{listed} were together in the dining car when the crime took place, "
            "and none of them is the culprit."
        )


@dataclass(frozen=True)
class ExactlyOneTrue(Clue):
    """«Exactly one of these three statements is true: …» — il vero rompicapo."""

    parts: tuple[Clue, ...]
    kind: ClassVar[str] = "exactly_one"
    weight: ClassVar[int] = 4

    def keeps(self, suspect: Suspect) -> bool:
        return sum(1 for part in self.parts if part.keeps(suspect)) == 1

    def text(self, attributes: dict[str, Attribute]) -> str:
        statements = " ".join(
            f"({chr(97 + index)}) {part.text(attributes)}"
            for index, part in enumerate(self.parts)
        )
        return f"Exactly one of these statements is true: {statements}"


# --------------------------------------------------------------------------
# Caso
# --------------------------------------------------------------------------
@dataclass
class Case:
    number: int
    title: str
    setting: str                      # testo di scena, due o tre frasi
    attributes: dict[str, Attribute]
    suspects: list[Suspect]
    clues: list[Clue]
    culprit: Suspect
    trace: list[tuple[int, int, int]] = field(default_factory=list)
    # (numero indizio, sospetti prima, sospetti dopo) — per la soluzione ragionata

    @property
    def attribute_order(self) -> list[str]:
        return [key for key, _ in self.suspects[0].attrs]

    def clue_texts(self) -> list[str]:
        return [clue.text(self.attributes) for clue in self.clues]

    def to_dict(self) -> dict:
        return {
            "number": self.number,
            "title": self.title,
            "setting": self.setting,
            "suspects": len(self.suspects),
            "clues": self.clue_texts(),
            "culprit": self.culprit.name,
            "culprit_attrs": self.culprit.as_dict(),
        }


@dataclass(frozen=True)
class FinaleClue:
    """Indizio del finale: confronta il capo con il colpevole di un caso risolto.

    `value` è il valore vero dell'attributo nel caso citato: serve alla verifica,
    non viene stampato (stamparlo regalerebbe la soluzione di quel caso).
    """

    mode: str                        # same | differs | not_case
    case_number: int
    attr: str = ""
    value: str = ""

    def keeps(self, suspect: Suspect) -> bool:
        if self.mode == "not_case":
            return suspect.get("case") != str(self.case_number)
        if self.mode == "same":
            return suspect.get(self.attr) == self.value
        return suspect.get(self.attr) != self.value

    @property
    def cases(self) -> tuple[int, ...]:
        return (self.case_number,)

    def clause(self, attributes: dict[str, Attribute]) -> str:
        if self.mode == "not_case":
            return f"the culprit of Case {self.case_number} is not the mastermind"
        attribute = attributes[self.attr]
        subject = f"the mastermind's {attribute.noun}"
        reference = f"{attribute.that_of} the culprit of Case {self.case_number}"
        # Due modi di dire la stessa cosa, scelti in modo stabile: cinque indizi
        # formulati tutti uguali si leggono come un modulo, non come un enigma.
        variant = (self.case_number + len(self.attr)) % 2
        if self.mode == "same":
            wording = f"matched {reference}" if variant else f"{attribute.to_be} the same as {reference}"
        else:
            wording = (
                f"differed from {reference}"
                if variant
                else f"{attribute.to_be} not the same as {reference}"
            )
        return f"{subject} {wording}"

    def text(self, attributes: dict[str, Attribute]) -> str:
        clause = self.clause(attributes)
        return clause[0].upper() + clause[1:] + "."


@dataclass(frozen=True)
class FinalePair:
    """Due confronti in un indizio solo: obbliga a tenere aperte due risposte."""

    first: FinaleClue
    second: FinaleClue

    @property
    def cases(self) -> tuple[int, ...]:
        return (self.first.case_number, self.second.case_number)

    def keeps(self, suspect: Suspect) -> bool:
        return self.first.keeps(suspect) and self.second.keeps(suspect)

    def text(self, attributes: dict[str, Attribute]) -> str:
        first = self.first.clause(attributes)
        return (
            first[0].upper() + first[1:] + ", and " + self.second.clause(attributes) + "."
        )


@dataclass
class Finale:
    title: str
    setting: str
    attributes: dict[str, Attribute]
    suspects: list[Suspect]
    clues: list[FinaleClue]
    mastermind: Suspect

    def clue_texts(self) -> list[str]:
        return [clue.text(self.attributes) for clue in self.clues]


# --------------------------------------------------------------------------
# Utilità di lingua
# --------------------------------------------------------------------------
def article_for(value: str) -> str:
    """"a fedora" ma "an ivory coat": l'articolo dipende dal suono iniziale."""
    return "an" if value[:1].lower() in "aeiou" else "a"


def _join_and(items) -> str:
    items = list(items)
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + f" and {items[-1]}"


def _join_or(items) -> str:
    items = list(items)
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"either {items[0]} or {items[1]}"
    return ", ".join(items[:-1]) + f", or {items[-1]}"

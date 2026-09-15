"""Ambientazione del libro: un espresso notturno degli anni Trenta.

Dodici vetture, dodici casi, e un finale che si apre solo con le dodici
soluzioni in mano. L'ambientazione è inventata di sana pianta — nessun treno,
marchio o opera esistente — ed è l'unica parte di prosa del libro: poche righe
per caso, scritte a mano una volta sola.
"""

from __future__ import annotations

from .model import Attribute

BOOK_TITLE = "Twelve Carriages, One Killer"
BOOK_SUBTITLE = "A Deduction Puzzle Book: Twelve Cases, One Mastermind. Can You Name Them All?"
TRAIN = "the Ashcombe Night Express"

# --------------------------------------------------------------------------
# Attributi
# --------------------------------------------------------------------------
ATTRIBUTES: dict[str, Attribute] = {
    "hat": Attribute(
        key="hat",
        label="Hat",
        noun="hat",
        values=("fedora", "bowler", "cloche", "beret", "homburg", "flat cap"),
        template="wore {a} {value}",
        negative_template="did not wear {a} {value}",
        listed_article=True,
    ),
    "coat": Attribute(
        key="coat",
        label="Coat",
        noun="coat",
        values=("navy", "charcoal", "camel", "crimson", "olive", "ivory"),
        template="wore {a} {value} coat",
        negative_template="did not wear {a} {value} coat",
    ),
    "luggage": Attribute(
        key="luggage",
        label="Luggage",
        noun="luggage",
        values=("hatbox", "violin case", "leather trunk", "carpet bag", "briefcase", "birdcage"),
        template="carried {a} {value}",
        negative_template="did not carry {a} {value}",
        listed_article=True,
    ),
    "drink": Attribute(
        key="drink",
        label="Drink",
        noun="drink",
        values=("tea", "brandy", "cocoa", "champagne", "soda water", "coffee"),
        template="drank {value}",
        negative_template="did not drink {value}",
    ),
    "gloves": Attribute(
        key="gloves",
        label="Gloves",
        noun="gloves",
        values=("leather", "wool", "lace", "silk"),
        template="wore {value} gloves",
        negative_template="did not wear {value} gloves",
        to_be="were",
    ),
    "seat": Attribute(
        key="seat",
        label="Seat",
        noun="seat",
        values=("window", "aisle"),
        template="sat in {a} {value} seat",
        negative_template="did not sit in {a} {value} seat",
        listed_article=True,
    ),
}

#: presenti in ogni caso: sono gli attributi su cui si gioca il finale
SHARED_ATTRIBUTES = ("hat", "coat", "luggage")

HONORIFICS = (
    "Mr", "Mrs", "Miss", "Dr", "Prof.", "Capt.", "Rev.", "Col.", "Major", "Madame",
)

#: cognomi unici dentro un caso: gli indizi possono nominarli senza ambiguità
SURNAMES = (
    "Ash", "Wren", "Blackwood", "Calloway", "Danvers", "Ellery", "Fairbrother",
    "Grimshaw", "Harrow", "Ingram", "Jellicoe", "Kingsley", "Lanyon", "Marchmont",
    "Northcote", "Ovington", "Pemberton", "Quill", "Rathbone", "Selwyn", "Thackeray",
    "Upton", "Vance", "Westaway", "Yardley", "Ambrose", "Barlow", "Carrick", "Dunmore",
    "Everly", "Fenwick", "Gallagher", "Haddon", "Ivers", "Jarrow", "Kemble", "Lockhart",
    "Mowbray", "Nesbit", "Orford", "Pike", "Quennell", "Rosslyn", "Sandbach",
    "Trelawney", "Ufford", "Whitlock", "Yates", "Abernathy", "Braithwaite", "Cardew",
    "Dunsmore", "Eastcott", "Fothergill", "Garrick", "Hollis", "Inchbald", "Jessop",
    "Kilbride", "Larkin", "Merriweather", "Norbury", "Oakhurst", "Pargeter", "Quiller",
    "Redmayne", "Sowerby", "Tregarth", "Underhill", "Vosper", "Wraysbury", "Yelverton",
    "Ashby", "Bramwell", "Colefax", "Drury", "Enderby", "Fitzalan", "Gorse", "Halliwell",
    "Isley", "Jocelyn", "Kestrel", "Lymington", "Mallory", "Netherton", "Ockham",
    "Prideaux", "Quarles", "Ravenscroft", "Sillitoe", "Tamworth", "Ulverston", "Vane",
    "Wilbraham", "Yorke", "Astley", "Bexley", "Crofton", "Dalrymple", "Elvington",
    "Farthing", "Glaisher", "Havelock", "Jephson", "Kentish", "Loxley", "Mottram",
    "Newlyn", "Orme", "Purbeck", "Quintrell", "Rushworth", "Standish", "Thorley",
    "Urquhart", "Villiers", "Waverley", "Yaxley", "Amberley", "Brightwell", "Coldstream",
)


# --------------------------------------------------------------------------
# I dodici casi
# --------------------------------------------------------------------------
class CaseTheme:
    """Testo e forma di un caso: quante colonne, quanto grande, quanto duro."""

    def __init__(
        self,
        number: int,
        carriage: str,
        title: str,
        setting: str,
        plan: tuple[tuple[str, int], ...],
        kinds: tuple[str, ...],
        min_clues: int | None = None,
    ):
        self.number = number
        self.carriage = carriage
        self.title = title
        self.setting = setting
        self.plan = plan          # ((chiave attributo, quanti valori), ...)
        self.kinds = kinds
        self.min_clues = min_clues

    @property
    def cast_size(self) -> int:
        size = 1
        for _, count in self.plan:
            size *= count
        return size


EASY = ("is", "is_not", "one_of", "cleared")
MEDIUM = ("is_not", "one_of", "cleared", "same_as", "differs_from", "if_then")
HARD = ("is_not", "one_of", "same_as", "differs_from", "if_then", "not_both", "exactly_one")

CASES: tuple[CaseTheme, ...] = (
    CaseTheme(
        1, "Carriage A — Second Class",
        "The Conductor's Whistle",
        "The whistle of Mr Pell, guard of the Ashcombe Night Express, vanished from its "
        "hook between Ashcombe and Marley Halt. Trivial, until the same whistle was found "
        "beside a body three carriages down. All {count} passengers holding tickets for "
        "Carriage A that night are below, and one of them took it.",
        (("hat", 4), ("coat", 3), ("luggage", 2)),
        EASY,
    ),
    CaseTheme(
        2, "Carriage B — Second Class",
        "The Emptied Flask",
        "The night steward filled every flask at Marley Halt. By Thorn Bridge one had been "
        "emptied and refilled with something that left a sleeping passenger unable to be "
        "woken. The steward remembers the carriage, not the face.",
        (("hat", 4), ("coat", 3), ("luggage", 2), ("drink", 2)),
        EASY,
    ),
    CaseTheme(
        3, "Carriage C — Family Compartment",
        "A Birdcage, Opened",
        "Lady Ockham travels with a canary and a great deal of jewellery. At Thorn Bridge "
        "the cage stood open and the jewellery was gone. The canary, unhelpfully, returned "
        "on its own.",
        (("hat", 4), ("coat", 3), ("luggage", 4)),
        MEDIUM,
    ),
    CaseTheme(
        4, "Carriage D — Second Class",
        "The Wrong Ticket",
        "A ticket punched at Ashcombe turned up in the pocket of a passenger who boarded at "
        "Thorn Bridge — and the passenger it belonged to has not been seen since.",
        (("hat", 4), ("coat", 3), ("luggage", 2), ("gloves", 2)),
        MEDIUM,
    ),
    CaseTheme(
        5, "Carriage E — Dining Car",
        "Soup for Nine",
        "Nine bowls of soup left the galley. Eight were eaten. The ninth was carried away by "
        "someone who had no business in the dining car, and the diner it was meant for never "
        "reached Cold Harbour.",
        (("hat", 5), ("coat", 4), ("luggage", 3)),
        MEDIUM,
    ),
    CaseTheme(
        6, "Carriage F — First Class",
        "The Locked Compartment",
        "Compartment 6F was locked from within and empty when forced. The window was shut. "
        "The key was in the corridor, and the key does not walk.",
        (("hat", 4), ("coat", 3), ("luggage", 3), ("drink", 2)),
        MEDIUM,
    ),
    CaseTheme(
        7, "Carriage G — Sleeping Car",
        "Three Knocks at Two",
        "At two in the morning three knocks woke half the sleeping car. The berth they came "
        "from was found open, the bed made, the occupant gone — and the sheets still warm.",
        (("hat", 5), ("coat", 4), ("luggage", 4)),
        MEDIUM,
    ),
    CaseTheme(
        8, "Carriage H — Post Van",
        "The Registered Parcel",
        "One registered parcel out of four hundred was opened in transit and resealed badly. "
        "Only a passenger who knew which four hundred to look through could have found it.",
        (("hat", 4), ("coat", 4), ("luggage", 3), ("gloves", 2)),
        MEDIUM,
    ),
    CaseTheme(
        9, "Carriage J — Observation Car",
        "The Hand on the Rail",
        "A hand was seen on the observation rail as the train crossed Cold Harbour viaduct, "
        "and a coat was found on the track the next morning. Nobody is missing. Everybody is "
        "accounted for. Both statements cannot be true.",
        (("hat", 4), ("coat", 4), ("luggage", 3), ("seat", 2)),
        HARD,
    ),
    CaseTheme(
        10, "Carriage K — First Class",
        "Two Tickets, One Name",
        "Two first-class tickets were issued to the same name for the same berth. One of the "
        "two travellers is dead. The other has spent the night insisting they never boarded.",
        (("hat", 4), ("coat", 4), ("luggage", 3), ("drink", 2)),
        HARD,
    ),
    CaseTheme(
        11, "Carriage L — Guard's Van",
        "The Stopped Clock",
        "The guard's clock stopped at 3:14, which is when the brake was pulled and the train "
        "stood for eleven minutes in open country. Someone got off. Someone got back on.",
        (("hat", 5), ("coat", 4), ("luggage", 3), ("seat", 2)),
        HARD,
    ),
    CaseTheme(
        12, "Carriage M — Rear Observation",
        "The Last Carriage",
        "By Cold Harbour the rear carriage should have been empty. It was not, and what was "
        "found there explains every case in this book — once you know who left it.",
        (("hat", 5), ("coat", 4), ("luggage", 3), ("gloves", 2)),
        HARD,
    ),
)

EXAMPLE = CaseTheme(
    0, "Worked example",
    "The Missing Timetable",
    "A small case, solved here in full, so that the twelve that follow need no explanation. "
    "{count} passengers, a handful of clues, one thief.",
    (("hat", 3), ("coat", 2), ("luggage", 2)),
    EASY,
    min_clues=3,   # è un esempio: deve entrare in una pagina e chiarire il metodo
)

FINALE_TITLE = "The Mastermind"
FINALE_SETTING = (
    "Twelve carriages, twelve culprits — and one of them was never working alone. "
    "One of the twelve planned the other eleven crimes and travelled the whole line to "
    "watch them happen.\n\n"
    "The suspects below are the twelve people you have already named. You will need every "
    "one of your answers: each clue compares the mastermind with the culprit of a case you "
    "have solved. Fill in the grid, then cross off."
)

HOW_TO_PLAY = """Every case in this book works the same way.

You get a **cast**: every passenger in one carriage, listed with everything that was noticed about them — a hat, a coat, a piece of luggage, sometimes a drink, gloves or a seat. No two passengers in a carriage are alike, and the culprit is one of them.

You get a **set of clues**. Every clue is true. Every clue matters: remove any one of them and the case can no longer be solved, because each was checked by machine before it was printed. There are no red herrings in these pages, and no clue that contradicts another.

Your job is to cross off. Read a clue, run it down the cast, strike out everyone it rules out. When one name is left, that name is the answer — and it is the only possible answer.

**The twelve cases can be solved in any order.** The thirteenth cannot. The final case asks you to name the mastermind behind all of them, and every clue in it compares that person with the culprit of a case you have already solved. Keep your answers: you will need all twelve.

Solutions begin on the page marked *Solutions*, and each one shows the order of elimination — not just the name, but the road to it. Read them only when you have to.

A pencil is better than a pen. Ask anyone who has tried Case 12."""

"""L'ambientazione di un libro di enigmi: il caricatore, non il contenuto.

Qui sta il **motore** — la forma di un caso, i livelli di difficoltà, la forma
di un attributo — e nient'altro. Che cosa il libro racconti (dove si svolge,
chi ci abita, i testi dei casi, l'esempio svolto, il finale) è **dato del
libro**: vive in `books/<slug>/ambientazione.json` e si carica da lì.

È la differenza fra una fabbrica e un prodotto. Finché l'ambientazione stava
qui dentro, il sistema conteneva un libro e ne poteva produrre uno solo: stesso
treno, stessi dodici casi, stessi passeggeri, cambiava soltanto il seme.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .model import Attribute

# --------------------------------------------------------------------------
# Motore: che cosa un caso può chiedere al generatore
# --------------------------------------------------------------------------
#: I tipi di indizio ammessi a ogni livello. Non sono contenuto: sono le regole
#: del gioco, e valgono per qualunque ambientazione.
EASY = ("is", "is_not", "one_of", "cleared")
MEDIUM = ("is_not", "one_of", "cleared", "same_as", "differs_from", "if_then")
HARD = ("is_not", "one_of", "same_as", "differs_from", "if_then", "not_both", "exactly_one")

LIVELLI: dict[str, tuple[str, ...]] = {"facile": EASY, "medio": MEDIUM, "difficile": HARD}


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


# --------------------------------------------------------------------------
# Ambientazione: tutto ciò che è del libro e non del sistema
# --------------------------------------------------------------------------
@dataclass
class Ambientazione:
    """Il libro, in forma di dati: si carica da file, non si scrive nel codice."""

    titolo: str
    sottotitolo: str = ""
    luogo: str = ""
    attributi: dict[str, Attribute] = field(default_factory=dict)
    attributi_comuni: tuple[str, ...] = ()
    appellativi: tuple[str, ...] = ()
    cognomi: tuple[str, ...] = ()
    casi: tuple[CaseTheme, ...] = ()
    esempio: CaseTheme | None = None
    finale_titolo: str = ""
    finale_testo: str = ""
    come_si_gioca: str = ""
    #: testi di vendita del libro: scheda prodotto e prima di copertina. Sono
    #: contenuto d'autore, non del sistema. `{casi}` e `{sospetti}` vengono
    #: sostituiti con i numeri veri del libro generato.
    scheda: dict = field(default_factory=dict)
    copertina: dict = field(default_factory=dict)

    def problemi(self) -> list[str]:
        """Che cosa impedisce di generare il libro. Vuoto = si può partire."""
        guai: list[str] = []
        if not self.titolo.strip():
            guai.append("manca `titolo`")
        if not self.casi:
            guai.append("nessun caso in `casi`")
        if len(self.appellativi) < 1:
            guai.append("nessun appellativo in `appellativi`")
        for caso in (*self.casi, *( [self.esempio] if self.esempio else [] )):
            for chiave, quanti in caso.plan:
                attributo = self.attributi.get(chiave)
                if attributo is None:
                    guai.append(f"caso {caso.number}: l'attributo «{chiave}» non è definito")
                elif quanti > len(attributo.values):
                    guai.append(
                        f"caso {caso.number}: l'attributo «{chiave}» ha "
                        f"{len(attributo.values)} valori, ne servono {quanti}"
                    )
            # Ogni sospetto ha un cognome diverso: gli indizi devono poterlo
            # nominare senza ambiguità.
            if caso.cast_size > len(self.cognomi):
                guai.append(
                    f"caso {caso.number}: servono {caso.cast_size} cognomi, "
                    f"ne hai {len(self.cognomi)}"
                )
        for chiave in self.attributi_comuni:
            if chiave not in self.attributi:
                guai.append(f"`attributi_comuni`: «{chiave}» non è fra gli attributi")
        return guai


def _caso_da_dati(dati: dict, dove: str) -> CaseTheme:
    livello = str(dati.get("difficolta", "medio"))
    if livello not in LIVELLI:
        raise ValueError(
            f"{dove}: difficoltà «{livello}» sconosciuta. Usa: {', '.join(LIVELLI)}."
        )
    piano = tuple((str(k), int(n)) for k, n in dati.get("piano", []))
    if not piano:
        raise ValueError(f"{dove}: `piano` vuoto, non si può costruire nessun cast.")
    return CaseTheme(
        number=int(dati.get("numero", 0)),
        carriage=str(dati.get("luogo", "")),
        title=str(dati.get("titolo", "")),
        setting=str(dati.get("testo", "")),
        plan=piano,
        kinds=LIVELLI[livello],
        min_clues=dati.get("indizi_minimi"),
    )


def da_dati(dati: dict) -> Ambientazione:
    """Costruisce un'ambientazione da un dizionario già letto."""
    attributi = {}
    for chiave, valori in (dati.get("attributi") or {}).items():
        attributi[chiave] = Attribute(
            key=str(valori.get("key", chiave)),
            label=str(valori.get("label", chiave.title())),
            noun=str(valori.get("noun", chiave)),
            values=tuple(valori.get("values", ())),
            template=str(valori.get("template", "wore {a} {value}")),
            negative_template=str(
                valori.get("negative_template", "did not wear {a} {value}")
            ),
            to_be=str(valori.get("to_be", "was")),
            listed_article=bool(valori.get("listed_article", False)),
        )
    esempio = dati.get("esempio")
    finale = dati.get("finale") or {}
    return Ambientazione(
        titolo=str(dati.get("titolo", "")),
        sottotitolo=str(dati.get("sottotitolo", "")),
        luogo=str(dati.get("luogo", "")),
        attributi=attributi,
        attributi_comuni=tuple(dati.get("attributi_comuni", ())),
        appellativi=tuple(dati.get("appellativi", ())),
        cognomi=tuple(dati.get("cognomi", ())),
        casi=tuple(
            _caso_da_dati(c, f"caso {c.get('numero', i + 1)}")
            for i, c in enumerate(dati.get("casi") or [])
        ),
        esempio=_caso_da_dati(esempio, "esempio") if esempio else None,
        finale_titolo=str(finale.get("titolo", "")),
        finale_testo=str(finale.get("testo", "")),
        come_si_gioca=str(dati.get("come_si_gioca", "")),
        scheda=dict(dati.get("scheda") or {}),
        copertina=dict(dati.get("copertina") or {}),
    )


def ambientazione_path(root: Path) -> Path:
    return root / "ambientazione.json"


def carica(percorso: Path) -> Ambientazione:
    """Legge l'ambientazione del libro e si ferma con un messaggio utile."""
    if not percorso.exists():
        raise SystemExit(
            f"Manca {percorso}: è il file che dice di che cosa parla il libro.\n"
            "Lo crea `python -m kdpfactory puzzle new <slug>`, poi va compilato."
        )
    try:
        dati = json.loads(percorso.read_text(encoding="utf-8"))
    except json.JSONDecodeError as errore:
        raise SystemExit(f"{percorso} non è JSON valido: {errore}") from errore
    ambientazione = da_dati(dati)
    guai = ambientazione.problemi()
    if guai:
        raise SystemExit(
            f"L'ambientazione in {percorso} non è utilizzabile:\n"
            + "\n".join(f"  - {g}" for g in guai)
        )
    return ambientazione


# --------------------------------------------------------------------------
# Ambientazione di collaudo
# --------------------------------------------------------------------------
#: Serve a far girare test e prove a secco senza che il sistema contenga un
#: libro. È dichiaratamente finta: nomi di lettere greche, oggetti astratti,
#: tre casi minuscoli. Non va pubblicata e non è un modello di scrittura.
_COLLAUDO_DATI: dict = {
    "titolo": "Collaudo",
    "sottotitolo": "Ambientazione di prova, non pubblicabile",
    "luogo": "the test bench",
    "attributi": {
        "colore": {
            "label": "Colour", "noun": "colour",
            "values": ["red", "green", "blue", "amber", "violet", "grey"],
            "template": "carried {a} {value} token",
            "negative_template": "did not carry {a} {value} token",
            "listed_article": True,
        },
        "forma": {
            "label": "Shape", "noun": "shape",
            "values": ["circle", "square", "triangle", "hexagon"],
            "template": "held {a} {value}",
            "negative_template": "did not hold {a} {value}",
            "listed_article": True,
        },
        "numero": {
            "label": "Number", "noun": "number",
            "values": ["one", "two", "three"],
            "template": "was marked {value}",
            "negative_template": "was not marked {value}",
        },
    },
    "attributi_comuni": ["colore", "forma"],
    "appellativi": ["Tester", "Probe", "Sample"],
    "cognomi": [f"Unit{n:02d}" for n in range(1, 91)],
    "casi": [
        {
            "numero": 1, "luogo": "Bench A", "titolo": "First Check",
            "testo": "A test case with {count} entries, used to verify the pipeline.",
            "piano": [["colore", 4], ["forma", 3], ["numero", 2]], "difficolta": "facile",
        },
        {
            "numero": 2, "luogo": "Bench B", "titolo": "Second Check",
            "testo": "Another test case with {count} entries.",
            "piano": [["colore", 5], ["forma", 3], ["numero", 2]], "difficolta": "medio",
        },
        {
            "numero": 3, "luogo": "Bench C", "titolo": "Third Check",
            "testo": "A larger test case with {count} entries.",
            "piano": [["colore", 6], ["forma", 4], ["numero", 3]], "difficolta": "difficile",
        },
    ],
    "esempio": {
        "numero": 0, "luogo": "Worked example", "titolo": "How The Check Works",
        "testo": "A small worked case with {count} entries.",
        "piano": [["colore", 3], ["forma", 2], ["numero", 2]],
        "difficolta": "facile", "indizi_minimi": 3,
    },
    "finale": {
        "titolo": "The Last Check",
        "testo": "The final test case: it needs the answers of all the others.",
    },
    "come_si_gioca": (
        "Testo segnaposto delle istruzioni: questa ambientazione serve al collaudo "
        "della pipeline e non va pubblicata."
    ),
    "scheda": {
        "paragrafi": [
            "Testo segnaposto della scheda prodotto.",
            "{casi} casi di collaudo, {sospetti} voci in tutto.",
        ],
        "punti": ["Punto segnaposto uno", "Punto segnaposto due"],
        "chiusura": "Chiusura segnaposto.",
        "parole_chiave": [f"parola chiave di collaudo {n}" for n in range(1, 8)],
        "categorie": ["Collaudo / Uno", "Collaudo / Due", "Collaudo / Tre"],
        "quarta": "Quarta di copertina segnaposto.",
        "punti_quarta": ["{casi} casi", "{sospetti} voci"],
    },
    "copertina": {
    "occhiello": "COLLAUDO",
    "gancio": "Ambientazione di prova?",
    "numeri": "{casi} CASI · {sospetti} VOCI",
    "garanzia": "Ogni caso ha una sola soluzione",
    },
}

COLLAUDO = da_dati(_COLLAUDO_DATI)


#: Le chiavi di `ambientazione.json`, spiegate all'autore dentro il file stesso:
#: è il punto in cui si decide di che cosa parla il libro.
LEGGIMI = [
    "Questo file è il libro: il sistema mette la meccanica, tu metti il mondo.",
    "titolo / sottotitolo / luogo: dove si svolge e come si chiama.",
    "attributi: le caratteristiche dei sospetti. `values` sono i valori possibili,",
    "  `template` la frase al passato usata negli indizi ('wore a fedora').",
    "attributi_comuni: quelli presenti in ogni caso; su quelli si gioca il finale.",
    "appellativi / cognomi: da qui escono i nomi. Servono almeno tanti cognomi",
    "  quanto il cast più grande (il prodotto dei valori in `piano`).",
    "casi: uno per capitolo. `piano` dice quanti valori per attributo, e quindi",
    "  quanto è grande il cast; `difficolta` è facile | medio | difficile.",
    "esempio: il caso svolto in apertura, piccolo, che spiega il metodo.",
    "finale: l'ultimo caso, quello che si apre solo con tutte le risposte in mano.",
    "scheda / copertina: i testi di vendita. `{casi}`, `{sospetti}` e `{indizi}`",
    "  vengono sostituiti con i numeri veri del libro generato.",
]


def collaudo_dati(casi: int = 3) -> dict:
    """I dati del collaudo, con il numero di casi che serve alla prova.

    Tre casi bastano a verificare il motore e tengono la suite veloce; per
    verificare che ne esca un libro davvero pubblicabile ne servono abbastanza
    da superare il minimo di pagine del progetto.
    """
    dati = json.loads(json.dumps(_COLLAUDO_DATI, ensure_ascii=False))
    modelli = dati["casi"]
    dati["casi"] = [
        {
            **modelli[i % len(modelli)],
            "numero": i + 1,
            "titolo": f"Check {i + 1}",
            "luogo": f"Bench {i + 1}",
        }
        for i in range(casi)
    ]
    return dati


def scrivi_collaudo(percorso: Path, casi: int = 3) -> Path:
    """Scrive su file l'ambientazione di collaudo.

    Serve ai test e alle prove a secco: la generazione legge sempre da file,
    perché è il file che rende il libro un dato e non un pezzo di codice.
    """
    percorso.parent.mkdir(parents=True, exist_ok=True)
    percorso.write_text(
        json.dumps(collaudo_dati(casi), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return percorso


def scrivi_modello(percorso: Path) -> Path:
    """Lascia un'ambientazione da compilare, come `init` lascia `brief.md`.

    Parte dal collaudo perché sia subito lavorabile: si può generare il libro
    e vederlo impaginato prima ancora di aver scritto una riga: poi si
    sostituisce il contenuto, campo per campo.
    """
    dati = json.loads(json.dumps(_COLLAUDO_DATI, ensure_ascii=False))
    dati = {"_leggimi": LEGGIMI, **dati}
    dati["titolo"] = "Titolo del libro (da scrivere)"
    dati["sottotitolo"] = "Sottotitolo (da scrivere)"
    percorso.parent.mkdir(parents=True, exist_ok=True)
    percorso.write_text(json.dumps(dati, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return percorso

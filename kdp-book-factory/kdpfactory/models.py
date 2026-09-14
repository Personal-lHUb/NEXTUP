"""Modelli dati del progetto: specifica del libro, scaletta, stato di avanzamento."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any

from . import kdpspecs


def slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii").lower()
    ascii_text = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    return ascii_text or "libro"


@dataclass
class BookSpec:
    """Tutto ciò che definisce un libro prima che venga scritto."""

    slug: str
    title: str
    subtitle: str = ""
    author: str = "Autore Anonimo"
    language: str = "it"                 # it | en
    topic: str = ""                      # argomento in una frase
    audience: str = "lettori generalisti"
    promise: str = ""                    # trasformazione promessa al lettore
    tone: str = "chiaro, diretto, professionale, con esempi concreti"
    genre: str = "non-fiction"           # non-fiction | fiction
    target_pages: int = 140
    trim: str = "6x9"
    paper: str = "cream"                 # white | cream | color-standard | color-premium
    cover_theme: str = "auto"            # auto | notte | bosco | terracotta | indaco | carta | grafite
    body_font: str = "serif"             # serif | sans
    body_font_size: float = 11.0
    leading: float = 15.5                # interlinea in punti
    chapters: int = 0                    # 0 = calcolato dal planner
    toc_depth: int = 2                   # 1 = solo capitoli nell'indice, 2 = anche le sezioni
    include_exercises: bool = True       # esercizi/checklist a fine capitolo
    include_intro: bool = True
    include_conclusion: bool = True
    dedication: str = ""
    keywords: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    isbn: str = ""                       # vuoto = ISBN gratuito fornito da KDP
    publisher: str = ""
    year: int = 0
    price_eur: float = 0.0
    notes: str = ""                      # istruzioni libere per il modello

    # --- validazione -----------------------------------------------------
    def validate(self) -> list[str]:
        problems: list[str] = []
        if not self.title.strip():
            problems.append("`title` è obbligatorio.")
        if self.trim not in kdpspecs.TRIM_SIZES:
            problems.append(
                f"`trim` {self.trim!r} non valido: {', '.join(kdpspecs.TRIM_SIZES)}"
            )
        if self.paper not in kdpspecs.PAPER_SPINE_FACTOR:
            problems.append(
                f"`paper` {self.paper!r} non valido: {', '.join(kdpspecs.PAPER_SPINE_FACTOR)}"
            )
        if not (kdpspecs.PROJECT_MIN_PAGES <= self.target_pages <= kdpspecs.PROJECT_MAX_PAGES):
            problems.append(
                f"`target_pages` ({self.target_pages}) fuori dall'intervallo di progetto "
                f"{kdpspecs.PROJECT_MIN_PAGES}-{kdpspecs.PROJECT_MAX_PAGES}."
            )
        if self.language not in {"it", "en"}:
            problems.append("`language` supportate: 'it', 'en'.")
        if self.genre not in {"non-fiction", "fiction"}:
            problems.append("`genre` supportati: 'non-fiction', 'fiction'.")
        if self.body_font_size < 9 or self.body_font_size > 14:
            problems.append("`body_font_size` consigliato tra 9 e 14 punti.")
        if self.leading < self.body_font_size * 1.15:
            problems.append(
                "`leading` troppo stretta: usa almeno 1.15 volte il corpo del carattere."
            )
        return problems

    # --- serializzazione -------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BookSpec:
        known = {f.name for f in fields(cls)}
        unknown = set(data) - known
        if unknown:
            raise ValueError(
                f"Campi non riconosciuti in book.json: {', '.join(sorted(unknown))}"
            )
        if "slug" not in data:
            data = {**data, "slug": slugify(data.get("title", ""))}
        return cls(**data)

    @classmethod
    def load(cls, path: Path) -> BookSpec:
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def save(self, path: Path) -> None:
        Path(path).write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


@dataclass
class ChapterPlan:
    """Un capitolo nella scaletta: cosa deve contenere e quanto deve essere lungo."""

    number: int
    title: str
    summary: str = ""
    beats: list[str] = field(default_factory=list)   # punti da coprire
    target_words: int = 0
    role: str = "chapter"                            # chapter | intro | conclusion

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChapterPlan:
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class Outline:
    """Scaletta completa del libro."""

    title: str
    subtitle: str = ""
    thesis: str = ""                                  # idea portante / logline
    back_cover: str = ""                              # testo di quarta di copertina
    chapters: list[ChapterPlan] = field(default_factory=list)
    target_words_total: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "subtitle": self.subtitle,
            "thesis": self.thesis,
            "back_cover": self.back_cover,
            "target_words_total": self.target_words_total,
            "chapters": [c.to_dict() for c in self.chapters],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Outline:
        return cls(
            title=data.get("title", ""),
            subtitle=data.get("subtitle", ""),
            thesis=data.get("thesis", ""),
            back_cover=data.get("back_cover", ""),
            target_words_total=int(data.get("target_words_total", 0) or 0),
            chapters=[ChapterPlan.from_dict(c) for c in data.get("chapters", [])],
        )

    @classmethod
    def load(cls, path: Path) -> Outline:
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def save(self, path: Path) -> None:
        Path(path).write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


class BookProject:
    """Struttura su disco di un singolo libro."""

    def __init__(self, root: Path):
        self.root = Path(root)

    # --- percorsi --------------------------------------------------------
    @property
    def spec_path(self) -> Path:
        return self.root / "book.json"

    @property
    def outline_path(self) -> Path:
        return self.root / "outline.json"

    @property
    def manuscript_dir(self) -> Path:
        return self.root / "manuscript"

    @property
    def build_dir(self) -> Path:
        return self.root / "build"

    @property
    def state_path(self) -> Path:
        return self.root / "state.json"

    def chapter_path(self, number: int) -> Path:
        return self.manuscript_dir / f"{number:02d}.md"

    # --- accessi ---------------------------------------------------------
    def load_spec(self) -> BookSpec:
        if not self.spec_path.exists():
            raise FileNotFoundError(
                f"Manca {self.spec_path}. Crea il libro con: kdpfactory init <titolo>"
            )
        return BookSpec.load(self.spec_path)

    def load_outline(self) -> Outline:
        if not self.outline_path.exists():
            raise FileNotFoundError(
                f"Manca {self.outline_path}. Genera la scaletta con: kdpfactory outline {self.root.name}"
            )
        return Outline.load(self.outline_path)

    def load_state(self) -> dict[str, Any]:
        if self.state_path.exists():
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        return {}

    def save_state(self, state: dict[str, Any]) -> None:
        self.state_path.write_text(
            json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    def update_state(self, **values: Any) -> dict[str, Any]:
        state = self.load_state()
        state.update(values)
        self.save_state(state)
        return state

    def ensure_dirs(self) -> None:
        self.manuscript_dir.mkdir(parents=True, exist_ok=True)
        self.build_dir.mkdir(parents=True, exist_ok=True)

    def chapter_files(self) -> list[Path]:
        if not self.manuscript_dir.exists():
            return []
        return sorted(self.manuscript_dir.glob("[0-9][0-9].md"))

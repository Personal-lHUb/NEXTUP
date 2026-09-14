"""Scheda prodotto KDP: titolo, descrizione, keyword, categorie, prezzi.

Il calcolo della royalty usa i costi di stampa in `config/printing_costs.json`:
sono valori che Amazon aggiorna, quindi il file va riverificato prima di
fissare un prezzo.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from html import escape as _escape
from pathlib import Path

from . import prompts
from .llm import LLMClient
from .models import BookSpec, Outline

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "printing_costs.json"


def generate_metadata(
    spec: BookSpec, outline: Outline, sample: str, client: LLMClient
) -> dict:
    data = client.complete_json(
        system=prompts.METADATA_SYSTEM,
        user=prompts.metadata_prompt(spec, outline, sample),
        label="metadati kdp (json)",
        max_tokens=8000,
    )
    data.setdefault("title", spec.title)
    data.setdefault("subtitle", spec.subtitle)
    data.setdefault("keywords", spec.keywords)
    data.setdefault("categories", spec.categories)
    data["description_html"] = build_description_html(data)
    return data


def escape(text: str) -> str:
    """Escape HTML lasciando intatti apostrofi e virgolette: nella descrizione
    KDP sono caratteri validi e `&#x27;` si vedrebbe sulla scheda."""
    return _escape(str(text), quote=False)


def build_description_html(meta: dict) -> str:
    """Descrizione nel sottoinsieme HTML accettato dalla scheda prodotto KDP."""
    parts: list[str] = []
    paragraphs = meta.get("description_paragraphs") or []
    if paragraphs:
        parts.append(f"<h2>{escape(paragraphs[0])}</h2>")
        for paragraph in paragraphs[1:]:
            parts.append(f"<p>{escape(paragraph)}</p>")
    bullets = meta.get("bullets") or []
    if bullets:
        items = "".join(f"<li>{escape(b)}</li>" for b in bullets)
        parts.append("<p><b>Cosa troverai in questo libro:</b></p>")
        parts.append(f"<ul>{items}</ul>")
    if meta.get("closing"):
        parts.append(f"<p><b>{escape(meta['closing'])}</b></p>")
    return "\n".join(parts)


# --------------------------------------------------------------------------
# Prezzi e royalty
# --------------------------------------------------------------------------
@dataclass
class PriceRow:
    marketplace: str
    currency: str
    symbol: str
    printing_cost: float
    min_price: float
    suggested_price: float
    royalty: float

    def to_dict(self) -> dict:
        return {
            "marketplace": self.marketplace,
            "valuta": self.currency,
            "costo_stampa": round(self.printing_cost, 2),
            "prezzo_minimo": round(self.min_price, 2),
            "prezzo_consigliato": round(self.suggested_price, 2),
            "royalty_per_copia": round(self.royalty, 2),
        }


def load_printing_config(path: Path | None = None) -> dict:
    return json.loads((path or CONFIG_PATH).read_text(encoding="utf-8"))


def printing_cost(pages: int, market: dict) -> float:
    rates = market["bianco_e_nero"]
    if pages <= 108:
        return float(rates["fino_a_108_pagine"])
    return float(rates["oltre_108_costo_fisso"]) + pages * float(rates["oltre_108_costo_per_pagina"])


def _round_to_99(value: float) -> float:
    """Arrotonda al primo prezzo in forma x,99 non inferiore al valore."""
    base = math.floor(value)
    candidate = base + 0.99
    return candidate if candidate >= value - 1e-9 else base + 1.99


def price_table(pages: int, config: dict | None = None, target_royalty: float = 3.0) -> list[PriceRow]:
    """Prezzo minimo (royalty >= 0) e prezzo consigliato per raggiungere
    `target_royalty` per copia."""
    config = config or load_printing_config()
    rate = float(config.get("royalty_rate", 0.6))
    rows: list[PriceRow] = []
    for market in config["marketplaces"]:
        cost = printing_cost(pages, market)
        min_price = max(_round_to_99(cost / rate), float(market["prezzo_minimo_consigliato"]))
        suggested = max(_round_to_99((cost + target_royalty) / rate), min_price)
        rows.append(
            PriceRow(
                marketplace=market["codice"],
                currency=market["valuta"],
                symbol=market["simbolo"],
                printing_cost=cost,
                min_price=min_price,
                suggested_price=suggested,
                royalty=suggested * rate - cost,
            )
        )
    return rows


# --------------------------------------------------------------------------
# File di output
# --------------------------------------------------------------------------
def render_listing(
    spec: BookSpec, meta: dict, pages: int, prices: list[PriceRow], config: dict
) -> str:
    """Scheda pronta da copiare nei campi del pannello KDP."""
    keywords = meta.get("keywords", [])
    categories = meta.get("categories", [])
    lines = [
        f"# Scheda KDP — {meta.get('title', spec.title)}",
        "",
        "Copia i campi qui sotto nel pannello di pubblicazione KDP.",
        "",
        "## Dati del libro",
        f"- **Titolo**: {meta.get('title', spec.title)}",
        f"- **Sottotitolo**: {meta.get('subtitle', spec.subtitle)}",
        f"- **Autore**: {spec.author}",
        f"- **Lingua**: {spec.language}",
        f"- **Formato**: {spec.trim} pollici, carta {spec.paper}, {pages} pagine",
        f"- **ISBN**: {spec.isbn or 'ISBN gratuito fornito da KDP'}",
        "",
        "## Descrizione (HTML, max 4000 caratteri)",
        "",
        "```html",
        meta.get("description_html", ""),
        "```",
        "",
        f"Caratteri: {len(meta.get('description_html', ''))}/4000",
        "",
        "## Parole chiave (7 slot)",
    ]
    for index, keyword in enumerate(keywords[:7], start=1):
        lines.append(f"{index}. {keyword}")
    lines += ["", "## Categorie (max 3)"]
    for category in categories[:3]:
        lines.append(f"- {category}")

    lines += [
        "",
        "## Contenuti generati con IA",
        "",
        "Nel modulo KDP, alla domanda sui contenuti generati con intelligenza artificiale,",
        "dichiara il testo come **AI-generated** (e le immagini, se la copertina è generata con IA).",
        "La dichiarazione è obbligatoria, non è pubblica e non influisce sull'approvazione.",
        "",
        "## Prezzo e royalty (royalty 60%, stima)",
        "",
        f"> Costi di stampa aggiornati al: **{config.get('verificato_il')}** — "
        "verifica su kdp.amazon.com prima di pubblicare.",
        "",
        "| Marketplace | Costo stampa | Prezzo minimo | Prezzo consigliato | Royalty/copia |",
        "|---|---|---|---|---|",
    ]
    for row in prices:
        lines.append(
            f"| {row.marketplace} | {row.symbol}{row.printing_cost:.2f} | "
            f"{row.symbol}{row.min_price:.2f} | {row.symbol}{row.suggested_price:.2f} | "
            f"{row.symbol}{row.royalty:.2f} |"
        )

    bio = meta.get("author_bio", "")
    if bio:
        lines += ["", "## Biografia autore", "", bio]
    return "\n".join(lines) + "\n"

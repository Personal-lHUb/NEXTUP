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
from .i18n import L
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
    data["description_html"] = build_description_html(data, spec.language)
    return data


def escape(text: str) -> str:
    """Escape HTML lasciando intatti apostrofi e virgolette: nella descrizione
    KDP sono caratteri validi e `&#x27;` si vedrebbe sulla scheda."""
    return _escape(str(text), quote=False)


#: I tag che la descrizione KDP accetta, e i soli che questo modulo scrive.
KDP_DESCRIPTION_TAGS = frozenset({"p", "b", "i", "em", "u", "br", "ul", "ol", "li", "h4", "h5", "h6"})


def build_description_html(meta: dict, language: str = "it") -> str:
    """Descrizione nel sottoinsieme HTML accettato dalla scheda prodotto KDP.

    L'etichetta dell'elenco segue la lingua del libro: era fissa in italiano, e
    su un libro inglese finiva così com'era sulla pagina di amazon.com — una
    riga in un'altra lingua in mezzo alla descrizione dice al cliente che il
    libro non è per lui, nel punto in cui sta decidendo.
    """
    parts: list[str] = []
    paragraphs = meta.get("description_paragraphs") or []
    if paragraphs:
        # L'attacco in grassetto, non in un titolo: KDP non accetta <h1>-<h3>
        # e la scheda li mostra come testo, o rifiuta la descrizione.
        parts.append(f"<p><b>{escape(paragraphs[0])}</b></p>")
        for paragraph in paragraphs[1:]:
            parts.append(f"<p>{escape(paragraph)}</p>")
    bullets = meta.get("bullets") or []
    if bullets:
        items = "".join(f"<li>{escape(b)}</li>" for b in bullets)
        parts.append(f"<p><b>{escape(L(language, 'listing_bullets'))}</b></p>")
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
    #: il prezzo viene da `price_eur` in book.json, cioè da una decisione
    #: editoriale presa sul concorrente vero, non dalla formula di default
    deciso: bool = False

    def to_dict(self) -> dict:
        return {
            "marketplace": self.marketplace,
            "valuta": self.currency,
            "costo_stampa": round(self.printing_cost, 2),
            "prezzo_minimo": round(self.min_price, 2),
            "prezzo_consigliato": round(self.suggested_price, 2),
            "royalty_per_copia": round(self.royalty, 2),
            "prezzo_deciso": self.deciso,
        }


def load_printing_config(path: Path | None = None) -> dict:
    return json.loads((path or CONFIG_PATH).read_text(encoding="utf-8"))


def printing_cost(pages: int, market: dict) -> float:
    """Costo di stampa KDP: fisso fino alla soglia di pagine, fisso più costo a pagina oltre."""
    rates = market["bianco_e_nero"]
    if pages <= int(rates["soglia_pagine"]):
        return float(rates["fino_alla_soglia"])
    return float(rates["oltre_soglia_costo_fisso"]) + pages * float(rates["oltre_soglia_costo_per_pagina"])


def royalty_rate(price: float, market: dict, config: dict | None = None) -> float:
    """La percentuale di royalty del cartaceo, che su KDP dipende dal prezzo di listino.

    Il 60% vale solo da una soglia di prezzo in su (9,99 USD ed EUR, 7,99 GBP):
    sotto è il 50%. Il file la applicava sempre al 60%, e un libro a 8,99
    risultava pagare una royalty che non avrebbe mai visto.
    """
    fasce = market.get("royalty")
    if not fasce:
        return float((config or {}).get("royalty_rate", 0.6))
    return float(fasce["alta"]) if price >= float(fasce["alta_da_prezzo"]) - 1e-9 else float(fasce["bassa"])


def _royalty(price: float, cost: float, market: dict, config: dict) -> float:
    return royalty_rate(price, market, config) * price - cost


def _first_99(minimum: float, cost: float, market: dict, config: dict, target: float) -> float:
    """Il primo prezzo in forma x,99, non sotto `minimum`, che rende almeno `target` a copia.

    Si prova un prezzo alla volta perché la percentuale cambia con il prezzo:
    una formula chiusa sbaglia proprio vicino alla soglia del 60%.
    """
    base = max(0, math.floor(minimum))
    for _ in range(1000):
        candidate = base + 0.99
        if candidate >= minimum - 1e-9 and _royalty(candidate, cost, market, config) >= target - 1e-9:
            return candidate
        base += 1
    raise ValueError("nessun prezzo ragionevole rende la royalty richiesta")


def _round_to_99(value: float) -> float:
    """Arrotonda al primo prezzo in forma x,99 non inferiore al valore."""
    base = math.floor(value)
    candidate = base + 0.99
    return candidate if candidate >= value - 1e-9 else base + 1.99


def price_table(
    pages: int,
    config: dict | None = None,
    target_royalty: float = 3.0,
    price: float = 0.0,
) -> list[PriceRow]:
    """Prezzo minimo (royalty >= 0) e prezzo di listino per ogni mercato.

    Senza `price`, il listino lo calcola la formula: quanto serve per tirare
    fuori `target_royalty` a copia. Con `price`, vince quello — perché è la
    decisione dell'editore, presa guardando che prezzo regge la nicchia, e una
    formula che non sa niente del concorrente non ha titolo per scavalcarla.
    Il minimo resta un pavimento: sotto, la royalty va in negativo.
    """
    config = config or load_printing_config()
    rows: list[PriceRow] = []
    for market in config["marketplaces"]:
        cost = printing_cost(pages, market)
        min_price = max(
            _first_99(0.0, cost, market, config, 0.0), float(market["prezzo_minimo_consigliato"])
        )
        calcolato = _first_99(min_price, cost, market, config, target_royalty)
        listino = max(price, min_price) if price > 0 else calcolato
        rows.append(
            PriceRow(
                marketplace=market["codice"],
                currency=market["valuta"],
                symbol=market["simbolo"],
                printing_cost=cost,
                min_price=min_price,
                suggested_price=listino,
                royalty=_royalty(listino, cost, market, config),
                deciso=price > 0 and listino == price,
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
        # Se il titolo della scheda non è quello stampato, chi incolla deve
        # vederlo qui, accanto al campo che sta per copiare: Amazon confronta
        # copertina e scheda, e una differenza blocca la pubblicazione.
        *(
            [f"- **Titolo stampato in copertina**: {spec.title}  ← NON COINCIDE"]
            if meta.get("title", spec.title).strip() != spec.title.strip()
            else []
        ),
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
        # Il prezzo deciso in scheda è una decisione editoriale presa sul
        # concorrente vero: va detto, perché altrimenti chi incolla vede un
        # numero e non sa se è una scelta o il risultato di una formula.
        *(
            [
                f"> **Prezzo deciso in scheda: {spec.price_eur:.2f}** (`price_eur` in "
                "book.json). La tabella lo applica a tutti i mercati; su KDP il listino "
                "si fissa mercato per mercato, quindi controlla valuta per valuta.",
                "",
            ]
            if spec.price_eur
            else []
        ),
        "| Marketplace | Costo stampa | Prezzo minimo | Prezzo di listino | Royalty/copia |",
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

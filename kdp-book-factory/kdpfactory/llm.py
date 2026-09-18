"""Client Claude per la generazione dei contenuti.

Tutte le chiamate passano da qui, così che: caching del prompt, streaming,
conteggio dei token e modalità `--dry-run` (nessuna chiamata di rete) siano
gestiti in un solo punto.
"""

from __future__ import annotations

import json
import os
import re
import textwrap
import time
from dataclasses import dataclass

MODEL_PRICES_USD_PER_MTOK: dict[str, tuple[float, float]] = {
    # modello: (input, output)
    "claude-opus-5": (5.00, 25.00),
    "claude-sonnet-5": (2.00, 10.00),
    "claude-haiku-4-5": (1.00, 5.00),
}
DEFAULT_MODEL = "claude-opus-5"


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0
    calls: int = 0

    def add(self, usage) -> None:
        self.calls += 1
        self.input_tokens += getattr(usage, "input_tokens", 0) or 0
        self.output_tokens += getattr(usage, "output_tokens", 0) or 0
        self.cache_creation_tokens += getattr(usage, "cache_creation_input_tokens", 0) or 0
        self.cache_read_tokens += getattr(usage, "cache_read_input_tokens", 0) or 0

    def cost_usd(self, model: str) -> float:
        price_in, price_out = MODEL_PRICES_USD_PER_MTOK.get(
            model, MODEL_PRICES_USD_PER_MTOK[DEFAULT_MODEL]
        )
        return (
            self.input_tokens * price_in
            + self.cache_creation_tokens * price_in * 1.25
            + self.cache_read_tokens * price_in * 0.10
            + self.output_tokens * price_out
        ) / 1_000_000

    def to_dict(self, model: str) -> dict:
        return {
            "calls": self.calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_creation_tokens": self.cache_creation_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "estimated_cost_usd": round(self.cost_usd(model), 4),
        }


@dataclass
class LLMConfig:
    model: str = DEFAULT_MODEL
    effort: str = "high"           # low | medium | high | xhigh | max
    max_tokens: int = 32000
    dry_run: bool = False
    verbose: bool = True


class DryRunError(RuntimeError):
    pass


class LLMClient:
    """Wrapper sottile sull'SDK Anthropic."""

    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig()
        self.usage = Usage()
        self._client = None
        if not self.config.dry_run:
            self._client = self._make_client()

    @staticmethod
    def _make_client():
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "Manca il pacchetto `anthropic`. Installa con: pip install -r requirements.txt"
            ) from exc
        # Il client risolve da solo ANTHROPIC_API_KEY o il profilo `ant auth login`.
        return anthropic.Anthropic(max_retries=4)

    # -- API --------------------------------------------------------------
    def complete(
        self,
        *,
        system: str | list[str],
        user: str,
        max_tokens: int | None = None,
        label: str = "",
    ) -> str:
        """Una richiesta, una risposta testuale.

        `system` può essere una lista di blocchi: tutti tranne l'ultimo vengono
        messi in cache (prefisso stabile riusato fra un capitolo e l'altro).
        """
        if self.config.dry_run:
            return dry_run_text(user, label=label, system=system)

        blocks = [system] if isinstance(system, str) else list(system)
        system_blocks = []
        for index, text in enumerate(blocks):
            block = {"type": "text", "text": text}
            # Breakpoint di cache sull'ultimo blocco stabile del prefisso.
            if index == len(blocks) - 1:
                block["cache_control"] = {"type": "ephemeral"}
            system_blocks.append(block)

        started = time.time()
        with self._client.messages.stream(
            model=self.config.model,
            max_tokens=max_tokens or self.config.max_tokens,
            system=system_blocks,
            thinking={"type": "adaptive"},
            output_config={"effort": self.config.effort},
            messages=[{"role": "user", "content": user}],
        ) as stream:
            message = stream.get_final_message()

        if message.stop_reason == "refusal":
            details = getattr(message, "stop_details", None)
            raise RuntimeError(
                "Il modello ha rifiutato la richiesta"
                + (f" (categoria: {details.category})" if details else "")
                + ". Rivedi l'argomento del libro o le istruzioni in `notes`."
            )

        self.usage.add(message.usage)
        text = "\n".join(b.text for b in message.content if b.type == "text").strip()
        if self.config.verbose:
            elapsed = time.time() - started
            print(
                f"  · {label or 'richiesta'}: {len(text.split())} parole, "
                f"{message.usage.output_tokens} token, {elapsed:.0f}s"
            )
        if message.stop_reason == "max_tokens":
            print("  ! risposta troncata da max_tokens: aumenta --max-tokens")
        return text

    def complete_json(self, *, system: str | list[str], user: str, label: str = "", **kwargs) -> dict:
        """Come `complete`, ma si aspetta un oggetto JSON."""
        raw = self.complete(system=system, user=user, label=label, **kwargs)
        return extract_json(raw)

    def usage_report(self) -> dict:
        return self.usage.to_dict(self.config.model)


def extract_json(text: str) -> dict:
    """Estrae il primo oggetto JSON dal testo, anche dentro un blocco di codice."""
    cleaned = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", cleaned, flags=re.S)
    if fence:
        cleaned = fence.group(1).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end > start:
        return json.loads(cleaned[start : end + 1])
    raise ValueError(f"Risposta non in formato JSON:\n{text[:500]}")


# --------------------------------------------------------------------------
# Modalità dry-run: testo segnaposto, nessuna chiamata di rete
# --------------------------------------------------------------------------
_STUB_SENTENCES = [
    "Questo paragrafo è testo segnaposto generato in modalità dry-run, utile solo a "
    "verificare l'impaginazione",
    "il conteggio delle pagine e il funzionamento della pipeline senza consumare token",
    "la struttura del capitolo resta quella reale, con titoli, elenchi e paragrafi di lunghezza verosimile",
    "sostituisci questo contenuto eseguendo la pipeline senza l'opzione dry-run",
    "ogni frase serve unicamente a occupare lo spazio tipografico previsto dal budget di parole",
]


def dry_run_text(user_prompt: str, label: str = "", system: str | list[str] | None = None) -> str:
    """Genera contenuto finto ma strutturalmente valido, rispettando il budget."""
    system_text = system if isinstance(system, str) else "\n".join(system or [])

    # Agenti di controllo: restituiscono segnalazioni, non testo.
    if '"findings"' in system_text:
        return json.dumps(_dry_run_findings(), ensure_ascii=False)

    # Revisore di stile ed editor ricevono un testo e lo restituiscono: in
    # dry-run lo ripassano invariato, così la lunghezza del libro non cambia.
    echoed = _echo_chapter(user_prompt)
    if echoed is not None:
        return echoed

    if "JSON" in user_prompt or "json" in label:
        return _dry_run_json(user_prompt)

    match = (
        re.search(r"Lunghezza richiesta:\s*(\d{3,6})", user_prompt)
        or re.search(r"invece di\s*(\d{3,6})", user_prompt)
        or re.search(r"(\d{3,6})\s*parole", user_prompt)
    )
    target = int(match.group(1)) if match else 1200
    title_match = re.search(r"Titolo del capitolo:\s*(.+)", user_prompt)
    title = title_match.group(1).strip() if title_match else "Capitolo segnaposto"

    parts: list[str] = [f"# {title}", ""]
    words = 0
    section = 1
    while words < target:
        parts.append(f"## Sezione segnaposto {section}")
        parts.append("")
        for _ in range(3):
            sentence = ". ".join(_STUB_SENTENCES[: 3 + (words % 3)]) + "."
            paragraph = textwrap.fill(sentence, 100000)
            parts.append(paragraph)
            parts.append("")
            words += len(paragraph.split())
            if words >= target:
                break
        parts.append("- Punto operativo segnaposto numero uno")
        parts.append("- Punto operativo segnaposto numero due")
        parts.append("")
        words += 12
        section += 1
    return "\n".join(parts)


def _echo_chapter(user_prompt: str) -> str | None:
    """Estrae il capitolo racchiuso fra `---` dopo `TESTO DEL CAPITOLO:`."""
    match = re.search(r"TESTO DEL CAPITOLO:\s*\n---\n(.*?)\n---\s*$", user_prompt, flags=re.S)
    return match.group(1).strip() if match else None


def _dry_run_findings() -> dict:
    return {
        "notes": "Lettura segnaposto in modalità dry-run: nessun giudizio reale.",
        "findings": [
            {
                "severity": "minore",
                "category": "verifica dry-run",
                "issue": "Segnalazione di prova prodotta senza chiamare il modello.",
                "quote": "",
                "suggestion": "Esegui la revisione senza --dry-run per avere segnalazioni vere.",
            }
        ],
    }


def _dry_run_json(user_prompt: str) -> str:
    if "scheda prodotto" in user_prompt:
        return json.dumps(_dry_run_metadata(), ensure_ascii=False)
    # Reparto di acquisizione: il giro da ASIN a scheda si deve poter provare
    # a costo zero come tutto il resto.
    if "Ecco la scheda del concorrente" in user_prompt:
        return json.dumps(_dry_run_concorrente(), ensure_ascii=False)
    if "Ricava le lacune del libro" in user_prompt:
        return json.dumps(_dry_run_lacune(), ensure_ascii=False)
    if "Decidi il libro nuovo" in user_prompt:
        return json.dumps(_dry_run_posizionamento(), ensure_ascii=False)

    match = re.search(r"(\d{1,3})\s*capitoli", user_prompt)
    chapters = int(match.group(1)) if match else 10
    data = {
        "title": "Titolo segnaposto",
        "subtitle": "Sottotitolo segnaposto",
        "thesis": "Tesi segnaposto generata in modalità dry-run.",
        "back_cover": "Testo di quarta segnaposto.\n\nSecondo paragrafo segnaposto.",
        "chapters": [
            {
                "number": i,
                "title": f"Capitolo segnaposto {i}",
                "summary": "Sintesi segnaposto del capitolo.",
                "beats": ["punto uno", "punto due", "punto tre"],
                "role": "chapter",
            }
            for i in range(1, chapters + 1)
        ],
    }
    return json.dumps(data, ensure_ascii=False)


def _dry_run_concorrente() -> dict:
    return {
        "asin": "B0SEGNAPOSTO",
        "titolo": "Libro segnaposto del concorrente",
        "sottotitolo": "Sottotitolo segnaposto",
        "autore": "Autore Segnaposto",
        "editore": "Editore segnaposto",
        "lingua": "it",
        "prezzo": 14.99,
        "valuta": "EUR",
        "pagine": 210,
        "formato": "15,2 x 1,5 x 22,9 cm",
        "pubblicato_il": "2024-01-01",
        "voto_medio": 4.1,
        "numero_recensioni": 128,
        "rango_generale": 12345,
        "categorie": [{"nome": "Categoria segnaposto", "rango": 42}],
        "descrizione": ["Paragrafo segnaposto della descrizione del concorrente."],
        "recensioni": [
            {"stelle": 3, "titolo": "Segnaposto", "testo": "Recensione segnaposto: manca la pratica."},
            {"stelle": 5, "titolo": "Segnaposto", "testo": "Recensione segnaposto: molto chiaro."},
        ],
        "problemi": ["dati segnaposto: nessuna pagina è stata letta davvero"],
    }


def _dry_run_lacune() -> dict:
    return {
        "lettore_reale": "Lettore segnaposto",
        "confidenza": "bassa",
        "perche_questa_confidenza": "dati segnaposto in modalità dry-run",
        "lacune": [
            {
                "tema": "Lacuna segnaposto",
                "ricorrenze": 3,
                "che_cosa_manca": "Descrizione segnaposto di quello che manca.",
                "citazioni": ["Recensione segnaposto: manca la pratica."],
                "vale_un_libro": True,
            }
        ],
        "da_non_toccare": [
            {"punto": "Punto di forza segnaposto", "citazioni": ["Recensione segnaposto: molto chiaro."]}
        ],
        "prezzo": "",
        "scartate": [],
    }


def _dry_run_posizionamento() -> dict:
    return {
        "titolo": "Titolo segnaposto del libro nuovo",
        "sottotitolo": "Sottotitolo segnaposto",
        "lingua": "it",
        "argomento": "Argomento segnaposto generato in modalità dry-run.",
        "lettore": "Lettore segnaposto",
        "promessa": "Promessa segnaposto.",
        "tono": "chiaro, diretto, professionale, con esempi concreti",
        "genere": "non-fiction",
        "pagine_obiettivo": 140,
        "prezzo": 12.99,
        "valuta": "EUR",
        "perche_questo_prezzo": "Motivazione segnaposto.",
        "parole_chiave": [f"parola chiave segnaposto {i}" for i in range(1, 8)],
        "categorie": [f"Categoria segnaposto {i}" for i in range(1, 4)],
        "la_lacuna_che_copre": "Lacuna segnaposto",
        "che_cosa_tiene": ["Punto di forza segnaposto"],
        "che_cosa_non_fa": ["Argomento segnaposto escluso"],
        "argomenti": [f"Tema segnaposto {i}" for i in range(1, 11)],
        "rischi": ["Rischio segnaposto"],
    }


def _dry_run_metadata() -> dict:
    return {
        "title": "Titolo segnaposto",
        "subtitle": "Sottotitolo segnaposto orientato al beneficio",
        "description_paragraphs": [
            "Gancio segnaposto della descrizione.",
            "Secondo paragrafo segnaposto della descrizione del libro.",
            "Terzo paragrafo segnaposto della descrizione del libro.",
        ],
        "bullets": [f"Punto segnaposto numero {i}" for i in range(1, 6)],
        "closing": "Chiusura segnaposto con chiamata all'azione.",
        "keywords": [f"keyword segnaposto {i}" for i in range(1, 8)],
        "categories": ["Categoria segnaposto 1", "Categoria segnaposto 2"],
        "author_bio": "Biografia segnaposto dell'autore, in terza persona.",
        "back_cover": "Gancio segnaposto di quarta.\n\nParagrafo segnaposto di quarta di copertina.",
        "back_cover_bullets": [f"Punto di quarta segnaposto {i}" for i in range(1, 4)],
    }


def api_key_present() -> bool:
    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        return True
    config_dir = os.path.expanduser("~/.config/anthropic")
    return os.path.isdir(config_dir)

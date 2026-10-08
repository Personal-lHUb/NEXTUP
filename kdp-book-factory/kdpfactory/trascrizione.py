"""L'uscita di un subagent, presa dalla sua trascrizione invece che ricopiata.

Nella linea manuale la sessione chiama gli agenti uno per uno e ne salva le
risposte JSON nei file del libro. Ricopiarle a mano costa token due volte e
lascia passare un refuso in un campo; qui si legge la trascrizione JSONL che
Claude Code tiene per ogni subagent e si salva l'oggetto così com'è uscito.
"""

from __future__ import annotations

import json
from pathlib import Path

#: Dove Claude Code tiene le trascrizioni: un file per subagent,
#: `<progetto>/<sessione>/subagents/agent-<id>.jsonl`.
PROGETTI = Path.home() / ".claude" / "projects"


def trova(agente: str, radice: Path = PROGETTI) -> Path:
    """La trascrizione di un subagent: un percorso `.jsonl`, o l'id dell'agente."""
    if agente.endswith(".jsonl"):
        percorso = Path(agente)
        if not percorso.exists():
            raise FileNotFoundError(f"Manca la trascrizione {percorso}.")
        return percorso
    trovate = sorted(radice.glob(f"*/*/subagents/agent-{agente}.jsonl"),
                     key=lambda p: p.stat().st_mtime)
    if not trovate:
        raise FileNotFoundError(f"Nessuna trascrizione per l'agente {agente} in {radice}.")
    return trovate[-1]


def _testi(percorso: Path) -> list[str]:
    """I testi dei messaggi dell'agente, nell'ordine in cui li ha scritti."""
    testi: list[str] = []
    for riga in percorso.read_text(encoding="utf-8").splitlines():
        try:
            voce = json.loads(riga)
        except ValueError:
            continue
        messaggio = voce.get("message") or {}
        if messaggio.get("role") != "assistant":
            continue
        contenuto = messaggio.get("content")
        if isinstance(contenuto, list):
            testo = "\n".join(c.get("text", "") for c in contenuto
                              if isinstance(c, dict) and c.get("type") == "text")
        else:
            testo = str(contenuto or "")
        if testo.strip():
            testi.append(testo)
    return testi


def _primo_oggetto(testo: str) -> dict | None:
    decoder = json.JSONDecoder()
    for i, carattere in enumerate(testo):
        if carattere != "{":
            continue
        try:
            oggetto, _ = decoder.raw_decode(testo[i:])
        except ValueError:
            continue
        if isinstance(oggetto, dict):
            return oggetto
    return None


def oggetto(percorso: Path, etichetta: str = "") -> dict:
    """L'oggetto JSON dell'ultimo messaggio che ne contiene uno.

    Con un'etichetta (`SCALETTA`, `FIGURE`) si prende l'oggetto che la segue,
    per gli agenti che consegnano più oggetti nello stesso messaggio.
    """
    for testo in reversed(_testi(percorso)):
        if etichetta:
            if etichetta not in testo:
                continue
            testo = testo[testo.rindex(etichetta) + len(etichetta):]
        trovato = _primo_oggetto(testo)
        if trovato is not None:
            return trovato
    dove = f" dopo «{etichetta}»" if etichetta else ""
    raise ValueError(f"Nessun oggetto JSON{dove} nei messaggi di {percorso.name}.")


def testo(percorso: Path, inizio: str = "# ") -> str:
    """Il testo dell'ultimo messaggio che contiene una riga che comincia con `inizio`.

    Per gli agenti che scrivono (il ghostwriter consegna il capitolo in
    markdown): si tiene dalla prima riga che comincia con `inizio` in poi, così
    un preambolo o una recinzione ```markdown non finiscono nel manoscritto.
    """
    for messaggio in reversed(_testi(percorso)):
        righe = messaggio.splitlines()
        for i, riga in enumerate(righe):
            if riga.startswith(inizio):
                corpo = righe[i:]
                while corpo and corpo[-1].strip() in {"", "```"}:
                    corpo.pop()
                return "\n".join(corpo) + "\n"
    raise ValueError(f"Nessun messaggio di {percorso.name} ha una riga che comincia con «{inizio}».")


def salva_testo(agente: str, uscita: Path, inizio: str = "# ", radice: Path = PROGETTI) -> str:
    """Trova la trascrizione, ne estrae il testo consegnato e lo scrive in `uscita`."""
    corpo = testo(trova(agente, radice), inizio)
    uscita.parent.mkdir(parents=True, exist_ok=True)
    uscita.write_text(corpo, encoding="utf-8")
    return corpo


def salva(agente: str, uscita: Path, etichetta: str = "", radice: Path = PROGETTI) -> dict:
    """Trova la trascrizione, ne estrae l'oggetto e lo scrive in `uscita`."""
    dati = oggetto(trova(agente, radice), etichetta)
    uscita.parent.mkdir(parents=True, exist_ok=True)
    uscita.write_text(json.dumps(dati, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return dati

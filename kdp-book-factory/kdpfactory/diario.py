"""Il diario del libro e gli hook che tengono il contesto della sessione.

Una sessione lunga si riassume da sola quando la conversazione riempie la
finestra di contesto, e nel riassunto si perdono i dettagli: il prompt esatto
dato a un agente, il suo identificativo, quale consegna è già stata importata.
Il 10 ottobre i prompt degli editor si sono dovuti ripescare dalla trascrizione
grezza. Da allora quello che serve per ripartire sta nei file, e ci arriva
senza che nessuno debba ricordarsene:

- **il diario** (`books/<slug>/diario.md`): una riga datata per ogni passo,
  scritta dagli hook di Claude Code (agente lanciato, identificativo, agente
  finito) e dai comandi (consegna importata, decisione proposta);
- **i prompt** (`books/<slug>/prompt/`): il messaggio esatto di ogni agente
  lanciato, per rilanciarlo identico;
- **le consegne** (`books/<slug>/consegne/`): l'uscita intera di ogni agente.
  L'agente la scrive lì e risponde con una riga; se risponde col testo lungo,
  l'hook di fine agente la salva lì lo stesso.

All'avvio della sessione e dopo ogni riassunto l'hook `session-start` rimette
in contesto STATO.md, lo stato della produzione, gli agenti ancora in volo, le
consegne da importare e la coda del diario.

Gli hook stanno in `.claude/settings.json` e chiamano
`python3 -m kdpfactory.diario --hook <evento>`. Questo modulo usa solo la
libreria standard: gira a ogni lancio di agente e deve costare pochi
millisecondi. Un hook che fallisce non ferma mai il lavoro, tranne la guardia,
che esiste per fermarlo.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

#: la cartella `kdp-book-factory`
RADICE = Path(__file__).resolve().parent.parent
CONFIG = Path("config") / "produzione.json"
CONSEGNE = "consegne"
PROMPT = "prompt"
#: oltre questa lunghezza la risposta finale di un agente è un'uscita, non un avviso
SOGLIA_USCITA = 1500
RIGHE_IN_CONTESTO = 30

INTESTAZIONE = """# Diario di lavorazione

Una riga per passo, in ordine, scritta dai comandi e dagli hook di Claude Code
(`kdpfactory/diario.py`). Non si modifica a mano: si aggiunge.

"""


class Libro:
    """Quanto basta di un libro per il diario: la sua cartella."""

    def __init__(self, root: Path):
        self.root = Path(root)


def _ora(adesso: datetime | None = None) -> datetime:
    return (adesso or datetime.now(timezone.utc)).astimezone(timezone.utc)


def _una_riga(testo: str, limite: int = 0) -> str:
    riga = " ".join(str(testo).split())
    return riga if not limite or len(riga) <= limite else riga[: limite - 1] + "…"


def _nome(testo: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", testo.lower()).strip("-")[:40] or "senza-nome"


def percorso(project) -> Path:
    return project.root / "diario.md"


def annota(project, testo: str, adesso: datetime | None = None) -> None:
    """Aggiunge una riga datata al diario del libro."""
    file = percorso(project)
    nuovo = not file.exists()
    file.parent.mkdir(parents=True, exist_ok=True)
    with file.open("a", encoding="utf-8") as f:
        if nuovo:
            f.write(INTESTAZIONE)
        f.write(f"- {_ora(adesso):%Y-%m-%d %H:%M} UTC · {_una_riga(testo)}\n")


def righe(project) -> list[str]:
    file = percorso(project)
    if not file.exists():
        return []
    return [r for r in file.read_text(encoding="utf-8").splitlines() if r.startswith("- ")]


def dentro_consegne(percorso_file: str | Path) -> bool:
    """Se il percorso è una consegna: `books/<slug>/consegne/<file>`, e nient'altro."""
    parti = Path(percorso_file).parts
    if ".." in parti:
        return False
    return any(
        parti[i] == "books" and parti[i + 2] == CONSEGNE
        for i in range(len(parti) - 3)
    )


def libro_attivo(radice: Path = RADICE) -> Libro | None:
    """Il libro in produzione (`attivi` in config/produzione.json), se c'è."""
    config = radice / CONFIG
    try:
        attivi = json.loads(config.read_text(encoding="utf-8")).get("attivi") or []
    except (OSError, ValueError):
        return None
    if not attivi:
        return None
    root = radice / "books" / attivi[0]
    return Libro(root) if root.is_dir() else None


# --------------------------------------------------------------------------
# Prompt e consegne
# --------------------------------------------------------------------------
def salva_prompt(project, agente: str, descrizione: str, prompt: str,
                 adesso: datetime | None = None) -> Path:
    momento = _ora(adesso)
    file = project.root / PROMPT / f"{momento:%Y%m%d-%H%M%S}-{_nome(agente)}-{_nome(descrizione)}.md"
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(
        f"<!-- agente: {agente} · {descrizione} · {momento:%Y-%m-%d %H:%M:%S} UTC -->\n\n{prompt.rstrip()}\n",
        encoding="utf-8",
    )
    return file


def salva_uscita(project, agente: str, id_agente: str, testo: str,
                 adesso: datetime | None = None) -> Path:
    """La risposta lunga di un agente che non ha scritto la consegna da sé."""
    momento = _ora(adesso)
    file = project.root / CONSEGNE / f"{momento:%Y%m%d-%H%M%S}-{_nome(agente)}-{id_agente[:8]}.md"
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(testo.rstrip() + "\n", encoding="utf-8")
    return file


def _relativo(project, file: Path) -> str:
    try:
        return str(file.relative_to(project.root))
    except ValueError:
        return str(file)


# --------------------------------------------------------------------------
# Lettura del diario: agenti in volo, consegne da importare
# --------------------------------------------------------------------------
_LANCIATO = re.compile(r"`(?P<agente>[^`]+)` «(?P<descr>[^»]*)» in background, id `(?P<id>[^`]+)`")
_FINITO = re.compile(r"finito `[^`]*` \(id `(?P<id>[^`]+)`\)")


def in_volo(project) -> list[str]:
    """Gli agenti lanciati in background che il diario non ha ancora visto finire."""
    lanciati: dict[str, str] = {}
    for riga in righe(project):
        if m := _LANCIATO.search(riga):
            lanciati[m["id"]] = f"`{m['agente']}` «{m['descr']}» (id `{m['id']}`)"
        elif m := _FINITO.search(riga):
            lanciati.pop(m["id"], None)
    return list(lanciati.values())


def da_importare(project) -> list[str]:
    """Le consegne nella cartella che nessuna riga del diario dice importate."""
    cartella = project.root / CONSEGNE
    if not cartella.is_dir():
        return []
    testo = "\n".join(righe(project))
    return sorted(
        f.name for f in cartella.iterdir()
        if f.is_file() and f"`{f.name}` importata" not in testo and f"`{f.name}` letta" not in testo
    )


def contesto(radice: Path = RADICE, sorgente: str = "") -> str:
    """Il testo che l'hook rimette in contesto all'avvio e dopo ogni riassunto."""
    parti = []
    stato = radice.parent / "STATO.md"
    if stato.exists():
        parti.append("## STATO.md\n\n" + stato.read_text(encoding="utf-8").strip())
    libro = libro_attivo(radice)
    try:
        produzione = subprocess.run(
            [sys.executable, "-m", "kdpfactory", "produzione"], cwd=radice,
            capture_output=True, text=True, timeout=30,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        produzione = ""
    if produzione:
        parti.append("## Produzione (`python3 -m kdpfactory produzione`)\n\n" + produzione)
    if libro is not None:
        slug = libro.root.name
        volo = in_volo(libro)
        if volo:
            parti.append(
                f"## Agenti lanciati e non ancora finiti ({slug})\n\n"
                + "\n".join(f"- {v}" for v in volo)
                + "\n\nSe la sessione è nuova non girano più: il prompt identico è in "
                f"`books/{slug}/{PROMPT}/`."
            )
        consegne = da_importare(libro)
        if consegne:
            parti.append(
                f"## Consegne non ancora importate (books/{slug}/{CONSEGNE}/)\n\n"
                + "\n".join(f"- {c}" for c in consegne)
            )
        coda = righe(libro)[-RIGHE_IN_CONTESTO:]
        if coda:
            parti.append(f"## Diario di {slug}, ultime righe\n\n" + "\n".join(coda))
    if not parti:
        return ""
    titolo = {
        "compact": "Contesto dopo il riassunto della chat",
        "resume": "Contesto alla ripresa della sessione",
    }.get(sorgente, "Contesto all'avvio della sessione")
    return f"# {titolo} (kdpfactory.diario)\n\n" + "\n\n".join(parti) + "\n"


# --------------------------------------------------------------------------
# Hook
# --------------------------------------------------------------------------
def hook(evento: str, dati: dict, radice: Path = RADICE,
         adesso: datetime | None = None) -> tuple[int, str, str]:
    """Esegue un hook: (codice d'uscita, testo per il contesto, messaggio d'errore).

    Il codice è 2 solo quando la guardia blocca una scrittura; ogni altro
    hook esce con 0 qualunque cosa succeda.
    """
    if evento == "guardia":
        if not dati.get("agent_id"):
            return 0, "", ""  # la sessione principale scrive dove serve
        entrata = dati.get("tool_input") or {}
        file = entrata.get("file_path") or entrata.get("notebook_path") or ""
        if dentro_consegne(file):
            return 0, "", ""
        agente = dati.get("agent_type") or "agente"
        return 2, "", (
            f"{agente}: puoi scrivere solo la tua consegna, in books/<slug>/{CONSEGNE}/. "
            f"«{file}» è fuori: il resto dei file lo cambia un comando, dopo il backup."
        )

    if evento == "session-start":
        return 0, contesto(radice, dati.get("source", "")), ""

    libro = libro_attivo(radice)
    if libro is None:
        return 0, "", ""
    entrata = dati.get("tool_input") or {}
    agente = entrata.get("subagent_type") or "general-purpose"
    descrizione = entrata.get("description") or ""

    if evento == "pre-agent":
        prompt = entrata.get("prompt") or ""
        file = salva_prompt(libro, agente, descrizione, prompt, adesso)
        annota(libro, f"lanciato `{agente}` «{descrizione}» → `{_relativo(libro, file)}`", adesso)
    elif evento == "post-agent":
        risposta = json.dumps(dati.get("tool_response"), ensure_ascii=False)
        trovato = re.search(r"agentId:\s*([A-Za-z0-9_-]+)", risposta) or re.search(
            r'"agentId":\s*"([A-Za-z0-9_-]+)"', risposta)
        if trovato:
            annota(libro, f"`{agente}` «{descrizione}» in background, id `{trovato[1]}`", adesso)
    elif evento == "subagent-stop":
        id_agente = dati.get("agent_id") or "?"
        tipo = dati.get("agent_type") or "agente"
        ultimo = dati.get("last_assistant_message") or ""
        if isinstance(ultimo, (list, dict)):
            ultimo = json.dumps(ultimo, ensure_ascii=False)
        nota = f"finito `{tipo}` (id `{id_agente}`)"
        if len(ultimo) > SOGLIA_USCITA:
            file = salva_uscita(libro, tipo, id_agente, ultimo, adesso)
            nota += f": uscita lunga salvata in `{_relativo(libro, file)}`"
        elif ultimo.strip():
            nota += f": «{_una_riga(ultimo, 200)}»"
        annota(libro, nota, adesso)
    elif evento == "pre-compact":
        volo = in_volo(libro)
        annota(libro, f"— la chat viene riassunta ({dati.get('trigger') or 'auto'}); "
                      f"agenti in volo: {len(volo)} —", adesso)
    return 0, "", ""


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2 or argv[0] != "--hook":
        print("uso: python3 -m kdpfactory.diario --hook <evento>", file=sys.stderr)
        return 0
    try:
        dati = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        dati = {}
    try:
        codice, uscita, errore = hook(argv[1], dati)
    except Exception as eccezione:  # un hook rotto non ferma la sessione
        print(f"kdpfactory.diario: {eccezione}", file=sys.stderr)
        return 0
    if uscita:
        print(uscita)
    if errore:
        print(errore, file=sys.stderr)
    return codice


if __name__ == "__main__":
    sys.exit(main())

"""Il canale con Cowork: le richieste di ricerca web e le loro risposte.

Il container della fabbrica non raggiunge Amazon né KDP. Quello che serve da lì
lo fa una sessione Cowork sul computer dell'autore. Lo scambio passa da file con
un nome fisso, nella stessa cartella: `cowork-<argomento>.md` è la richiesta,
`cowork-<argomento>-risposta.md` la risposta. I file passano da una casella su
Google Drive, che le due parti raggiungono senza GitHub Desktop.

Questo modulo non chiama né Drive né il web. Sa tre cose: dove stanno le
richieste, in che stato sono e come si chiamano nella casella, dove le cartelle
diventano un prefisso (`household-bills--cowork-amazon.md`). A spostare i file
è chi ha il connettore: questa sessione da una parte, Cowork dall'altra.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

PREFISSO = "cowork-"
SUFFISSO_RISPOSTA = "-risposta"
SEPARATORE = "--"
SISTEMA = "sistema"
#: riga che la fabbrica aggiunge alla richiesta quando ne ha applicato la risposta
APPLICATA = "Stato: applicata"
CONFIG = Path("config") / "cowork.json"
#: cartelle dove una richiesta non è mai quella vera: copie di sicurezza e impaginati
ESCLUSE = frozenset({"backup", "build", "__pycache__", ".git"})

APERTA, ARRIVATA, CHIUSA = "aperta", "risposta arrivata", "applicata"


@dataclass(frozen=True)
class Richiesta:
    percorso: str         # relativo alla radice della fabbrica
    chiave: str           # slug del libro, o «sistema» per le regole comuni
    argomento: str
    nome_drive: str
    risposta: str         # percorso relativo della risposta
    risposta_drive: str
    stato: str            # aperta | risposta arrivata | applicata

    def to_dict(self) -> dict:
        return asdict(self)


def _e_richiesta(percorso: Path) -> bool:
    return (
        percorso.name.startswith(PREFISSO)
        and percorso.suffix == ".md"
        and not percorso.stem.endswith(SUFFISSO_RISPOSTA)
    )


def _chiave(relativo: Path) -> str:
    parti = relativo.parts
    return parti[1] if len(parti) > 2 and parti[0] == "books" else SISTEMA


def richieste(radice: Path) -> list[Richiesta]:
    """Tutte le richieste a Cowork sotto la radice della fabbrica, in ordine."""
    trovate: list[Richiesta] = []
    for percorso in sorted(radice.rglob(f"{PREFISSO}*.md")):
        relativo = percorso.relative_to(radice)
        if ESCLUSE.intersection(relativo.parts[:-1]) or not _e_richiesta(percorso):
            continue
        chiave = _chiave(relativo)
        risposta = percorso.with_name(percorso.stem + SUFFISSO_RISPOSTA + percorso.suffix)
        if APPLICATA in percorso.read_text(encoding="utf-8"):
            stato = CHIUSA
        elif risposta.exists():
            stato = ARRIVATA
        else:
            stato = APERTA
        trovate.append(
            Richiesta(
                percorso=relativo.as_posix(),
                chiave=chiave,
                argomento=percorso.stem[len(PREFISSO):],
                nome_drive=f"{chiave}{SEPARATORE}{percorso.name}",
                risposta=risposta.relative_to(radice).as_posix(),
                risposta_drive=f"{chiave}{SEPARATORE}{risposta.name}",
                stato=stato,
            )
        )
    return trovate


def _senza_estensione(nome: str) -> str:
    # Cowork può salvare la risposta come documento Google: il titolo perde «.md».
    return nome[:-3] if nome.endswith(".md") else nome


def da_nome_drive(elenco: list[Richiesta], nome: str) -> Richiesta | None:
    """La richiesta a cui appartiene un file della casella, richiesta o risposta."""
    cercato = _senza_estensione(nome.strip())
    for richiesta in elenco:
        if cercato in (
            _senza_estensione(richiesta.nome_drive),
            _senza_estensione(richiesta.risposta_drive),
        ):
            return richiesta
    return None


def configurazione(radice: Path) -> dict:
    """La casella su Drive (`config/cowork.json`): nome e id della cartella."""
    percorso = radice / CONFIG
    if not percorso.exists():
        return {}
    return json.loads(percorso.read_text(encoding="utf-8"))


def avviso(elenco: list[Richiesta], cartella: str) -> str:
    """Il messaggio che dice a Cowork che nella casella c'è lavoro nuovo.

    Elenca solo le richieste aperte: quelle con la risposta già scritta non si
    rifanno, e un elenco che le ripete tutte a ogni avviso insegna a ignorarlo.
    """
    aperte = [r for r in elenco if r.stato == APERTA]
    if not aperte:
        return f"Nella cartella Drive «{cartella}» non ci sono richieste aperte.\n"
    righe = [
        f"Nella cartella Google Drive «{cartella}» ci sono richieste nuove della "
        "fabbrica di libri, da elaborare:",
        "",
    ]
    righe += [f"- `{r.nome_drive}` → rispondi in `{r.risposta_drive}`" for r in aperte]
    righe += [
        "",
        "Per ciascuna: leggila per intero ed esegui quello che chiede. Scrivi la "
        "risposta nella stessa cartella, con il nome indicato, in Markdown. Non "
        "modificare e non cancellare il file della richiesta.",
        "",
        "Regole valide per tutte:",
        "- per ogni punto, il fatto che hai visto sulla pagina, non una stima, con "
        "l'URL e la data e l'ora della verifica;",
        "- se una pagina chiede un captcha o l'accesso e non riesci ad andare avanti, "
        "scrivilo invece di stimare;",
        "- su KDP leggi e basta: non creare titoli, non salvare bozze, non pubblicare;",
        "- nessuna password, codice o cookie nei file.",
        "",
        "Quando hai finito, dimmi quali risposte hai scritto e quali punti sono rimasti "
        "senza risposta.",
    ]
    return "\n".join(righe) + "\n"


def rapporto(elenco: list[Richiesta]) -> str:
    """Lo stato del canale, una riga per richiesta."""
    if not elenco:
        return "Nessuna richiesta a Cowork.\n"
    larghezza = max(len(r.percorso) for r in elenco)
    righe = [f"  {r.stato:<17} {r.percorso:<{larghezza}}  ({r.nome_drive})" for r in elenco]
    conteggio = {s: sum(r.stato == s for r in elenco) for s in (APERTA, ARRIVATA, CHIUSA)}
    righe.append(
        f"\n{conteggio[APERTA]} aperte · {conteggio[ARRIVATA]} con risposta da applicare · "
        f"{conteggio[CHIUSA]} applicate"
    )
    return "\n".join(righe) + "\n"

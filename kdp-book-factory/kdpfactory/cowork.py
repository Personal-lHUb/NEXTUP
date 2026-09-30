"""Il canale con Cowork: le richieste di ricerca web e le loro risposte, su GitHub.

Il container della fabbrica non raggiunge Amazon né KDP. Quello che serve da lì
lo fa una sessione Cowork sul computer dell'autore. Lo scambio passa dal
repository su GitHub, sul ramo del canale (`config/cowork.json`), con due nomi
fissi nella stessa cartella: `cowork-<argomento>.md` è la richiesta,
`cowork-<argomento>-risposta.md` la risposta. La fabbrica fa commit e push delle
richieste, Cowork fa il commit delle risposte sullo stesso ramo.

Questo modulo non va in rete. Legge i file e chiede a git due cose: com'è la
richiesta sul ramo remoto, così si vede se è stata inviata, e quando è stato
fatto l'ultimo commit della richiesta e della risposta, così si vede se la
risposta è superata. Le domande a git passano da due funzioni: nei test si
danno finte.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

PREFISSO = "cowork-"
SUFFISSO_RISPOSTA = "-risposta"
SISTEMA = "sistema"
#: riga che la fabbrica aggiunge alla richiesta quando ne ha applicato la risposta
APPLICATA = "Stato: applicata"
CONFIG = Path("config") / "cowork.json"
#: cartelle dove una richiesta non è mai quella vera: copie di sicurezza e impaginati
ESCLUSE = frozenset({"backup", "build", "__pycache__", ".git"})

APERTA, ARRIVATA, SUPERATA, CHIUSA = "aperta", "risposta arrivata", "risposta superata", "applicata"
DA_INVIARE, INVIATA, NON_CONTROLLATA = "da inviare", "inviata", "non controllata"

#: com'è un file sul ramo remoto (None se lì non c'è), dato il percorso dalla radice della fabbrica
Remoto = Callable[[str], "str | None"]
#: quando è stato fatto l'ultimo commit di un file (None se non ne ha), in secondi
UltimoCommit = Callable[[str], "int | None"]


@dataclass(frozen=True)
class Richiesta:
    percorso: str         # relativo alla radice della fabbrica
    chiave: str           # slug del libro, o «sistema» per le regole comuni
    argomento: str
    risposta: str         # percorso relativo della risposta
    stato: str            # aperta | risposta arrivata | risposta superata | applicata
    invio: str            # da inviare | inviata | non controllata

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


def richieste(
    radice: Path,
    remoto: Remoto | None = None,
    ultimo_commit: UltimoCommit | None = None,
) -> list[Richiesta]:
    """Tutte le richieste a Cowork sotto la radice della fabbrica, in ordine.

    Senza `remoto` l'invio resta «non controllata»; senza `ultimo_commit` una
    risposta presente vale sempre come arrivata.
    """
    trovate: list[Richiesta] = []
    for percorso in sorted(radice.rglob(f"{PREFISSO}*.md")):
        relativo = percorso.relative_to(radice)
        if ESCLUSE.intersection(relativo.parts[:-1]) or not _e_richiesta(percorso):
            continue
        testo = percorso.read_text(encoding="utf-8")
        risposta = percorso.with_name(percorso.stem + SUFFISSO_RISPOSTA + percorso.suffix)
        rel, rel_risposta = relativo.as_posix(), risposta.relative_to(radice).as_posix()

        if remoto is None:
            invio = NON_CONTROLLATA
        else:
            # Inviata vuol dire che sul ramo del canale c'è questa stessa versione:
            # una correzione fatta qui e non pubblicata, Cowork non la vede.
            invio = INVIATA if remoto(rel) == testo else DA_INVIARE

        if APPLICATA in testo:
            stato = CHIUSA
        elif risposta.exists():
            stato = ARRIVATA
            if ultimo_commit is not None:
                t_richiesta, t_risposta = ultimo_commit(rel), ultimo_commit(rel_risposta)
                # La richiesta corretta dopo la risposta: la risposta è alla domanda vecchia.
                if t_richiesta and t_risposta and t_richiesta > t_risposta:
                    stato = SUPERATA
        else:
            stato = APERTA

        trovate.append(
            Richiesta(
                percorso=rel,
                chiave=_chiave(relativo),
                argomento=percorso.stem[len(PREFISSO):],
                risposta=rel_risposta,
                stato=stato,
                invio=invio,
            )
        )
    return trovate


def configurazione(radice: Path) -> dict:
    """Il canale (`config/cowork.json`): repository, ramo, LEGGIMI per Cowork."""
    percorso = radice / CONFIG
    if not percorso.exists():
        return {}
    return json.loads(percorso.read_text(encoding="utf-8"))


class Git:
    """Le due domande che il canale fa a git, sul repository che contiene la fabbrica."""

    def __init__(self, radice: Path, ramo: str, remote: str = "origin"):
        self.radice = radice.resolve()
        self.ramo = ramo
        self.remote = remote
        cima = self._git("rev-parse", "--show-toplevel", cwd=self.radice)
        self.cima = Path(cima.strip()) if cima else self.radice

    def _git(self, *argomenti: str, cwd: Path | None = None) -> str | None:
        risultato = subprocess.run(
            ["git", *argomenti], cwd=cwd or self.cima, capture_output=True, text=True
        )
        return risultato.stdout if risultato.returncode == 0 else None

    def _dal_repo(self, relativo: str) -> str:
        return (self.radice / relativo).relative_to(self.cima).as_posix()

    def remoto(self, relativo: str) -> str | None:
        return self._git("show", f"{self.remote}/{self.ramo}:{self._dal_repo(relativo)}")

    def ultimo_commit(self, relativo: str) -> int | None:
        uscita = self._git("log", "-1", "--format=%ct", "--", self._dal_repo(relativo))
        return int(uscita) if uscita and uscita.strip() else None

    def percorso_repo(self, relativo: str) -> str:
        return self._dal_repo(relativo)


def avviso(elenco: list[Richiesta], canale: dict, dal_repo: Callable[[str], str] = str) -> str:
    """Il messaggio che dice a Cowork che sul ramo del canale c'è lavoro nuovo.

    Elenca solo le richieste aperte: quelle con la risposta già scritta non si
    rifanno, e un elenco che le ripete tutte a ogni avviso insegna a ignorarlo.
    """
    repo = canale.get("repository", "Personal-lHUb/NEXTUP")
    ramo = canale.get("ramo", "claude/dreamy-archimedes-hf8w45")
    leggimi = canale.get("leggimi", "kdp-book-factory/config/leggimi-cowork.md")
    aperte = [r for r in elenco if r.stato == APERTA]
    if not aperte:
        return f"Sul ramo {ramo} di {repo} non ci sono richieste aperte.\n"
    righe = [
        f"Sul repository GitHub {repo}, ramo {ramo}, ci sono richieste nuove della "
        "fabbrica di libri, da elaborare.",
        "",
        f"Prima leggi per intero {leggimi}: sono le regole del canale.",
        "",
    ]
    righe += [
        f"- `{dal_repo(r.percorso)}` → rispondi in `{dal_repo(r.risposta)}`" for r in aperte
    ]
    righe += [
        "",
        "Per ciascuna: leggila per intero ed esegui quello che chiede. Scrivi la "
        "risposta nel file indicato e fanne il commit sullo stesso ramo, con la "
        "prima riga «Esito: completa» oppure «Esito: parziale — punti …: <motivo>». "
        "Non modificare altri file.",
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
    righe = [f"  {r.stato:<17} {r.invio:<15} {r.percorso}" for r in elenco]
    conteggio = {s: sum(r.stato == s for r in elenco) for s in (APERTA, ARRIVATA, SUPERATA, CHIUSA)}
    righe.append(
        f"\n{conteggio[APERTA]} aperte · {conteggio[ARRIVATA]} con risposta da applicare · "
        f"{conteggio[SUPERATA]} con risposta superata · {conteggio[CHIUSA]} applicate"
    )
    da_inviare = [r.percorso for r in elenco if r.invio == DA_INVIARE]
    if da_inviare:
        righe.append("Da inviare (commit e push sul ramo del canale): " + ", ".join(da_inviare))
    return "\n".join(righe) + "\n"

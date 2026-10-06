"""Il corriere su Google Drive: il pezzo del canale che Cowork e la fabbrica raggiungono da soli.

Con GitHub Desktop il giro non si chiudeva: il Pull prima e il push dopo li
faceva l'autore, e quando non c'era il canale restava fermo. Drive invece lo
raggiungono tutti e due senza passi a mano: Cowork dal portatile, la fabbrica
dal connettore di questa sessione. GitHub resta l'archivio, cioè il posto dove
richieste e risposte vivono e hanno la loro storia; Drive è solo il tragitto.

Il tragitto ha una regola sola, i nomi: un file su Drive si chiama come il suo
percorso nel repository, con `__` al posto di `/`.

    books/x/concorrente/cowork-concorrente.md  ⇄  books__x__concorrente__cowork-concorrente.md

Così una risposta (`…-risposta.md`) o un'immagine che Cowork lascia nella
cartella dice da sola dove va. Questo modulo non va in rete: dice che cosa
caricare, che cosa togliere e che cosa scaricare, e tiene il registro in
`config/corriere.json`. Le chiamate a Drive le fa la sessione, con il connettore.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from . import cowork

REGISTRO = Path("config") / "corriere.json"
SEPARATORE = "__"
#: Le immagini che Cowork può consegnare: solo nella cartella del libro, sotto assets/.
IMMAGINI = (".jpg", ".jpeg", ".png", ".webp")
#: File che Cowork legge a ogni giro e che quindi viaggiano sempre: le regole e il progetto.
SEMPRE = ("config/leggimi-cowork.md", "config/progetto-cowork.md", "config/attivita-cowork.json")
_SICURO = re.compile(r"^[A-Za-z0-9._-]+$")


def nome_drive(relativo: str) -> str:
    """Il nome del file su Drive, dal percorso nel repository (relativo a kdp-book-factory/)."""
    return relativo.strip("/").replace("/", SEPARATORE)


def percorso_da_nome(nome: str) -> str:
    """Il percorso nel repository, dal nome del file su Drive."""
    return nome.replace(SEPARATORE, "/")


def sha(testo: str | bytes) -> str:
    dati = testo.encode("utf-8") if isinstance(testo, str) else testo
    return hashlib.sha256(dati).hexdigest()


def leggi_registro(radice: Path) -> dict:
    percorso = radice / REGISTRO
    if not percorso.exists():
        return {"cartella_id": "", "caricati": {}, "scaricati": {}}
    dati = json.loads(percorso.read_text(encoding="utf-8"))
    dati.setdefault("caricati", {})
    dati.setdefault("scaricati", {})
    return dati


def salva_registro(radice: Path, registro: dict) -> Path:
    percorso = radice / REGISTRO
    percorso.write_text(json.dumps(registro, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return percorso


def destinazione_ammessa(radice: Path, nome: str, elenco: list[cowork.Richiesta]) -> str:
    """Dove va un file trovato su Drive, oppure vuoto se Cowork non può scriverlo lì.

    Cowork scrive solo due cose: la risposta accanto a una richiesta che esiste,
    e le immagini dentro `books/<slug>/assets/`. Tutto il resto resta su Drive:
    un nome che punta al codice o a `book.json` non arriva mai nel repository.
    """
    relativo = percorso_da_nome(nome)
    parti = relativo.split("/")
    if not all(p and p not in {".", ".."} and _SICURO.match(p) for p in parti):
        return ""
    risposte = {r.risposta for r in elenco}
    if relativo in risposte:
        return relativo
    if (
        len(parti) >= 4
        and parti[0] == "books"
        and parti[2] == "assets"
        and Path(parti[-1]).suffix.lower() in IMMAGINI
        and (radice / "books" / parti[1]).is_dir()
    ):
        return relativo
    return ""


@dataclass(frozen=True)
class Carico:
    percorso: str      # nel repository
    nome: str          # su Drive
    sha: str
    vecchio_id: str    # la copia superata su Drive, da togliere; vuoto se non c'era

    def to_dict(self) -> dict:
        return {"percorso": self.percorso, "nome": self.nome, "sha": self.sha, "vecchio_id": self.vecchio_id}


def piano(radice: Path, elenco: list[cowork.Richiesta]) -> dict:
    """Che cosa fare su Drive in questo giro.

    - `carica`: le richieste aperte, il LEGGIMI e il progetto che su Drive non ci
      sono o ci sono in una versione vecchia (la vecchia va tolta: Drive non
      riscrive il contenuto di un file, se ne fa uno nuovo);
    - `togli`: le copie delle richieste ormai applicate o ritirate (cancellate dal
      repository), che Cowork non deve più vedere;
    - `attesi`: i nomi che Cowork può consegnare — le risposte alle richieste
      aperte — e il prefisso delle immagini ammesse.
    """
    registro = leggi_registro(radice)
    caricati = registro["caricati"]
    carica: list[Carico] = []
    da_mandare = [r.percorso for r in elenco if r.stato == cowork.APERTA] + [
        p for p in SEMPRE if (radice / p).exists()
    ]
    for relativo in da_mandare:
        firma = sha((radice / relativo).read_text(encoding="utf-8"))
        prima = caricati.get(relativo) or {}
        if prima.get("sha") != firma:
            carica.append(Carico(relativo, nome_drive(relativo), firma, prima.get("id", "")))
    chiuse = {r.percorso for r in elenco if r.stato == cowork.CHIUSA}
    # Una richiesta ritirata si cancella dal repository: la sua copia su Drive
    # resterebbe lì, e Cowork la farebbe lo stesso.
    ritirate = {p for p in caricati if not (radice / p).exists()}
    togli = [
        {"percorso": p, "id": dati["id"]}
        for p, dati in caricati.items()
        if (p in chiuse or p in ritirate) and dati.get("id")
    ]
    attesi = [nome_drive(r.risposta) for r in elenco if r.stato == cowork.APERTA]
    return {
        "cartella_id": registro.get("cartella_id", ""),
        "carica": [c.to_dict() for c in carica],
        "togli": togli,
        "attesi": attesi,
        "immagini": "books__<slug>__assets__<nome>.(jpg|png|webp)",
        "gia_scaricati": registro["scaricati"],
    }


def registra_caricato(radice: Path, relativo: str, drive_id: str) -> None:
    registro = leggi_registro(radice)
    firma = sha((radice / relativo).read_text(encoding="utf-8"))
    registro["caricati"][relativo] = {"id": drive_id, "sha": firma}
    salva_registro(radice, registro)


def registra_tolto(radice: Path, relativo: str) -> None:
    registro = leggi_registro(radice)
    registro["caricati"].pop(relativo, None)
    salva_registro(radice, registro)


def registra_scaricato(radice: Path, nome: str, drive_id: str, contenuto: bytes) -> None:
    registro = leggi_registro(radice)
    registro["scaricati"][nome] = {"id": drive_id, "sha": sha(contenuto)}
    salva_registro(radice, registro)


def gia_scaricato(radice: Path, nome: str, drive_id: str) -> bool:
    """Un file di Cowork già portato nel repository: stesso nome e stesso file su Drive."""
    return (leggi_registro(radice)["scaricati"].get(nome) or {}).get("id") == drive_id

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
cartella dice da sola dove va. Questo modulo non va su Drive: dice che cosa
caricare, che cosa togliere e che cosa scaricare, e tiene il registro in
`config/corriere.json`. Le chiamate a Drive le fa la sessione, con il connettore.

Le immagini fanno un'altra strada. Il connettore Drive porta testo, non file da
qualche megabyte, né all'andata né al ritorno: una copertina a piena
risoluzione pesa 8 MB. Cowork le carica allora su GitHub, nel ramo
`cowork-immagini`, che il container raggiunge con git; `preleva_dal_ramo` ne
prende solo le immagini in `books/<slug>/assets/`, con la stessa regola del
corriere: nient'altro arriva da lì.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from . import cowork

REGISTRO = Path("config") / "corriere.json"
SEPARATORE = "__"
#: Le immagini che Cowork può consegnare: solo nella cartella del libro, sotto assets/.
IMMAGINI = (".jpg", ".jpeg", ".png", ".webp")
#: Il ramo di GitHub dove Cowork consegna le immagini, e dove sta la fabbrica nel
#: repository: sul ramo i percorsi partono dalla radice, non da kdp-book-factory/.
RAMO_IMMAGINI = cowork.RAMO_IMMAGINI
CARTELLA_FABBRICA = cowork.CARTELLA_FABBRICA
#: Le prime righe di un PNG, di un JPEG e di un WebP: il nome non basta a dire
#: che un file è un'immagine.
_FIRME = (b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff")
#: File che Cowork legge a ogni giro e che quindi viaggiano sempre: le regole e il progetto.
SEMPRE = ("config/leggimi-cowork.md", "config/progetto-cowork.md", "config/attivita-cowork.json")
#: Sul canale GitHub su Drive va solo il LEGGIMI: il prompt delle attività dice di
#: leggerlo per primo, e lui manda al ramo, dove stanno anche progetto e attività.
SEMPRE_GITHUB = ("config/leggimi-cowork.md",)
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
    if not _percorso_sicuro(relativo):
        return ""
    risposte = {r.risposta for r in elenco}
    if relativo in risposte or immagine_ammessa(radice, relativo):
        return relativo
    return ""


def _percorso_sicuro(relativo: str) -> bool:
    return all(p and p not in {".", ".."} and _SICURO.match(p) for p in relativo.split("/"))


def immagine_ammessa(radice: Path, relativo: str) -> bool:
    """Un'immagine in `books/<slug>/assets/` di un libro che esiste: l'unica cosa che Cowork consegna."""
    parti = relativo.split("/")
    return (
        _percorso_sicuro(relativo)
        and len(parti) >= 4
        and parti[0] == "books"
        and parti[2] == "assets"
        and Path(parti[-1]).suffix.lower() in IMMAGINI
        and (radice / "books" / parti[1]).is_dir()
    )


def e_un_immagine(contenuto: bytes) -> bool:
    return contenuto.startswith(_FIRME) or (contenuto[:4] == b"RIFF" and contenuto[8:12] == b"WEBP")


@dataclass(frozen=True)
class Carico:
    percorso: str      # nel repository
    nome: str          # su Drive
    sha: str
    vecchio_id: str    # la copia superata su Drive, da togliere; vuoto se non c'era

    def to_dict(self) -> dict:
        return {"percorso": self.percorso, "nome": self.nome, "sha": self.sha, "vecchio_id": self.vecchio_id}


def su_github(canale: dict | None) -> bool:
    """Il canale su GitHub: richieste sul ramo della fabbrica, consegne sul ramo di Cowork."""
    return bool(cowork.ramo_consegna(canale))


def piano(radice: Path, elenco: list[cowork.Richiesta], canale: dict | None = None) -> dict:
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
    github = su_github(canale)
    # Sul canale GitHub Cowork legge le richieste dal ramo della fabbrica: su Drive
    # resta solo quello che le sue attività leggono per primo, il LEGGIMI.
    aperte = [] if github else [r.percorso for r in elenco if r.stato == cowork.APERTA]
    sempre = SEMPRE_GITHUB if github else SEMPRE
    da_mandare = aperte + [p for p in sempre if (radice / p).exists()]
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
        if (p in chiuse or p in ritirate or (github and p not in sempre)) and dati.get("id")
    ]
    attesi = [nome_drive(r.risposta) for r in elenco if r.stato == cowork.APERTA]
    return {
        "cartella_id": registro.get("cartella_id", ""),
        "carica": [c.to_dict() for c in carica],
        "togli": togli,
        "attesi": attesi,
        "immagini": "books__<slug>__assets__<nome>.(jpg|png|webp)",
        "ramo_immagini": RAMO_IMMAGINI,
        "gia_scaricati": registro["scaricati"],
        "avvia": da_avviare(radice, elenco, canale) if github else [],
    }


# --------------------------------------------------------------------------
# Il canale su GitHub: l'indice delle richieste e l'avvio dei ruoli
# --------------------------------------------------------------------------
INDICE = Path(cowork.INDICE)


def nel_cloud(richiesta: cowork.Richiesta, canale: dict) -> bool:
    """Una richiesta che un giro di Cowork nel cloud, senza il browser del portatile, può fare.

    Un giro lanciato dalla fabbrica parte nel cloud: niente Chrome dell'autore.
    Lo può fare solo un ruolo che lavora su fonti pubbliche (`"cloud": true` in
    config/cowork.json) e una richiesta che non chiede un accesso (`Serve:`).
    """
    dati = (canale.get("ruoli") or {}).get(richiesta.ruolo) or {}
    return bool(dati.get("cloud")) and not richiesta.serve


def da_avviare(radice: Path, elenco: list[cowork.Richiesta], canale: dict) -> list[dict]:
    """I ruoli da lanciare subito: una richiesta aperta fattibile nel cloud, non ancora lanciata.

    Una richiesta si lancia una volta sola per versione: se resta aperta, la
    riprende l'attività oraria del ruolo, sul portatile.
    """
    lanciate = leggi_registro(radice).get("avviate", {})
    ruoli = canale.get("ruoli") or {}
    avvia: dict[str, dict] = {}
    for r in elenco:
        if r.stato != cowork.APERTA or not nel_cloud(r, canale):
            continue
        firma = sha((radice / r.percorso).read_text(encoding="utf-8"))
        trigger = (ruoli.get(r.ruolo) or {}).get("trigger", "")
        if lanciate.get(r.percorso) != firma and trigger:
            voce = avvia.setdefault(r.ruolo, {"ruolo": r.ruolo, "trigger": trigger, "richieste": []})
            voce["richieste"].append(r.percorso)
    return list(avvia.values())


def registra_avviato(radice: Path, ruolo: str, elenco: list[cowork.Richiesta], canale: dict) -> list[str]:
    """Segna come lanciate le richieste aperte di un ruolo, alla versione di adesso."""
    registro = leggi_registro(radice)
    lanciate = registro.setdefault("avviate", {})
    fatte = []
    for r in elenco:
        if r.ruolo == ruolo and r.stato == cowork.APERTA and nel_cloud(r, canale):
            lanciate[r.percorso] = sha((radice / r.percorso).read_text(encoding="utf-8"))
            fatte.append(r.percorso)
    salva_registro(radice, registro)
    return fatte


def indice(elenco: list[cowork.Richiesta], canale: dict) -> str:
    """L'indice delle richieste aperte, che Cowork legge dal ramo della fabbrica.

    Per ogni richiesta: dove leggerla, dove consegnare la risposta, e se si può
    fare in un giro nel cloud o serve il browser del portatile.
    """
    repository = canale.get("repository", "Personal-lHUb/NEXTUP")
    ramo = canale.get("ramo", "")
    consegna = canale.get("ramo_consegna", RAMO_IMMAGINI)
    righe = [
        "# Richieste aperte per Cowork",
        "",
        "<!-- Scritto da `python3 -m kdpfactory cowork corriere` a ogni giro. Non si",
        "     modifica a mano. -->",
        "",
        f"Repository `{repository}`. Le richieste stanno sul ramo `{ramo}`; risposte e",
        f"immagini si consegnano sul ramo `{consegna}`, al percorso indicato. Le regole",
        f"sono in `{CARTELLA_FABBRICA}/config/leggimi-cowork.md`.",
        "",
    ]
    aperte = [r for r in elenco if r.stato == cowork.APERTA]
    if not aperte:
        righe.append("Nessuna richiesta aperta.")
    for ruolo in sorted({r.ruolo or "—" for r in aperte}):
        righe += [f"## Ruolo {ruolo}", ""]
        for r in (x for x in aperte if (x.ruolo or "—") == ruolo):
            dove = "nel cloud o col browser" if nel_cloud(r, canale) else "solo col browser del portatile"
            righe += [
                f"- `{percorso_sul_ramo(r.percorso)}`",
                f"  - risposta: `{percorso_sul_ramo(r.risposta)}` sul ramo `{consegna}`",
                f"  - si fa: {dove}" + (f" — serve {r.serve}" if r.serve else ""),
                f"  - https://github.com/{repository}/blob/{ramo}/{percorso_sul_ramo(r.percorso)}",
            ]
        righe.append("")
    return "\n".join(righe).rstrip() + "\n"


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


# --------------------------------------------------------------------------
# Il ramo delle immagini
# --------------------------------------------------------------------------
def percorso_sul_ramo(relativo: str) -> str:
    """Dove Cowork carica un file sul ramo: il percorso dalla radice del repository."""
    return f"{CARTELLA_FABBRICA}/{relativo.strip('/')}"


@dataclass(frozen=True)
class DalRamo:
    percorso: str      # relativo a kdp-book-factory/
    blob: str          # l'oggetto git sul ramo
    contenuto: bytes


_SUL_RAMO = re.compile(r"`" + re.escape(CARTELLA_FABBRICA) + r"/(books/[^`\s]+)`")


def richiesti(radice: Path, elenco: list[cowork.Richiesta]) -> set[str]:
    """Le immagini che le richieste hanno chiesto di caricare sul ramo, relative a kdp-book-factory/.

    Il ramo nasce da un ramo qualsiasi del repository e porta con sé tutti i
    suoi file, anche vecchie immagini di un libro: dal ramo si prende solo
    quello che una richiesta ha nominato.
    """
    nomi: set[str] = set()
    for richiesta in elenco:
        file = radice / richiesta.percorso
        if file.exists():
            nomi.update(_SUL_RAMO.findall(file.read_text(encoding="utf-8")))
    return nomi


def da_prendere(
    radice: Path, voci: list[tuple[str, str]], chiesti: set[str], risposte: frozenset[str] = frozenset()
) -> list[tuple[str, str]]:
    """Fra le voci del ramo (percorso dalla radice, blob), quelle da portare nel libro.

    Passano due cose sole, come dal corriere:
    - le immagini che una richiesta ha chiesto (`chiesti`), in
      `books/<slug>/assets/` di un libro che c'è, se quel blob non è già stato
      preso: un file rimasto uguale sul ramo non si riscrive a ogni giro;
    - le risposte alle richieste che esistono (`risposte`), se nel repository
      non ci sono ancora: una risposta di Cowork non si riscrive mai.
    """
    presi = leggi_registro(radice).get("dal_ramo", {})
    prefisso = CARTELLA_FABBRICA + "/"
    scelte = []
    for percorso, blob in voci:
        if not percorso.startswith(prefisso):
            continue
        relativo = percorso[len(prefisso):]
        if presi.get(relativo) == blob or not _percorso_sicuro(relativo):
            continue
        immagine = relativo in chiesti and immagine_ammessa(radice, relativo)
        risposta = relativo in risposte and not (radice / relativo).exists()
        if immagine or risposta:
            scelte.append((relativo, blob))
    return scelte


def preleva_dal_ramo(
    radice: Path, elenco: list[cowork.Richiesta], esegui=subprocess.run
) -> tuple[list[DalRamo], list[str]]:
    """Scarica il ramo di Cowork e ne legge immagini e risposte nuove. Non scrive nel libro.

    Restituisce i file da portare e gli avvisi (ramo che non c'è ancora, file
    con un nome da immagine che immagine non è, risposta che non è testo). Il
    ramo non si unisce mai al lavoro: se ne leggono solo i blob scelti da
    `da_prendere`.
    """
    def git(*argomenti: str) -> subprocess.CompletedProcess:
        return esegui(["git", "-C", str(radice), *argomenti], capture_output=True)

    rif = f"refs/remotes/origin/{RAMO_IMMAGINI}"
    scaricato = git("fetch", "-q", "origin", f"+refs/heads/{RAMO_IMMAGINI}:{rif}")
    if scaricato.returncode != 0:
        return [], [f"il ramo {RAMO_IMMAGINI} non c'è ancora: Cowork non ha consegnato niente"]
    albero = git("ls-tree", "-r", "--full-tree", rif)
    voci = []
    for riga in albero.stdout.decode("utf-8", "replace").splitlines():
        testa, _, percorso = riga.partition("\t")
        campi = testa.split()
        if len(campi) == 3 and campi[1] == "blob":
            voci.append((percorso, campi[2]))
    risposte = frozenset(r.risposta for r in elenco)
    presi, avvisi = [], []
    for relativo, blob in da_prendere(radice, voci, richiesti(radice, elenco), risposte):
        contenuto = git("cat-file", "blob", blob).stdout
        if relativo in risposte:
            try:
                contenuto.decode("utf-8")
            except UnicodeDecodeError:
                avvisi.append(f"{relativo}: sul ramo non è testo, resta lì")
                continue
        elif not e_un_immagine(contenuto):
            avvisi.append(f"{relativo}: sul ramo non è un'immagine, resta lì")
            continue
        presi.append(DalRamo(relativo, blob, contenuto))
    return presi, avvisi


def registra_dal_ramo(radice: Path, relativo: str, blob: str) -> None:
    registro = leggi_registro(radice)
    registro.setdefault("dal_ramo", {})[relativo] = blob
    salva_registro(radice, registro)

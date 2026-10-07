"""Il corriere: come le risposte di Cowork arrivano su GitHub, l'unico posto dove i file stanno.

Cowork legge le richieste dal ramo della fabbrica, agli indirizzi pubblici, ma
su GitHub non scrive: non ha credenziali, e la sua modalità automatica blocca
la scrittura dal browser dell'autore come un aggiramento. Consegna allora la
risposta come testo, lanciando la routine della fabbrica (fire_trigger): la
prima riga dice dove va, il resto è la risposta.

    Cowork · risposta · kdp-book-factory/books/x/concorrente/cowork-concorrente-risposta.md
    Esito: completa
    …

La sessione salva il testo in un file e lo passa a `ricevi`, che scrive la
risposta accanto alla sua richiesta. Passa una cosa sola: la risposta a una
richiesta che esiste e non ha ancora risposta. Un percorso che punta al codice
o a `book.json` non arriva mai nel repository. Una risposta lunga arriva in
parti (` · parte 2/3`), che aspettano in `config/cowork-in-arrivo/` finché non
ci sono tutte; un giro non riuscito arriva come esito (`Cowork · esito ·
<ruolo>`) e resta in `config/cowork-esiti/`, dove la sessione lo legge.

Le immagini fanno un'altra strada: il testo di fire_trigger non le porta. Le
scarica la fabbrica, oppure le carica l'autore su GitHub, nel ramo
`cowork-immagini`, che il container raggiunge con git; `preleva_dal_ramo` ne
prende solo le immagini che una richiesta ha chiesto e le risposte che
mancano: nient'altro arriva da lì.

Fino al 7 ottobre 2026 le risposte passavano da una cartella di Google Drive.
Drive non si usa più: il registro ne conserva la storia sotto `drive_dismesso`.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from . import cowork

REGISTRO = Path("config") / "corriere.json"
#: Le immagini che possono arrivare dal ramo: solo nella cartella del libro, sotto assets/.
IMMAGINI = (".jpg", ".jpeg", ".png", ".webp")
#: Il ramo di GitHub dove l'autore carica le immagini, e dove sta la fabbrica nel
#: repository: sul ramo i percorsi partono dalla radice, non da kdp-book-factory/.
RAMO_IMMAGINI = cowork.RAMO_IMMAGINI
CARTELLA_FABBRICA = cowork.CARTELLA_FABBRICA
#: Le parti di una consegna lunga, finché non sono arrivate tutte.
IN_ARRIVO = Path("config") / "cowork-in-arrivo"
#: Gli esiti dei giri di Cowork non riusciti, come li ha consegnati.
ESITI = Path("config") / "cowork-esiti"
#: Le prime righe di un PNG, di un JPEG e di un WebP: il nome non basta a dire
#: che un file è un'immagine.
_FIRME = (b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff")
_SICURO = re.compile(r"^[A-Za-z0-9._-]+$")
#: La prima riga di una consegna. Il punto in mezzo si accetta anche come
#: trattino o barra, perché a mano si riscrive così; apici e grassetto attorno
#: alla riga si tolgono prima.
_SEP = r"\s+[·•|–-]\s+"
_TESTA = re.compile(
    r"^Cowork" + _SEP + r"(risposta|esito)" + _SEP + r"(\S+?)"
    r"(?:" + _SEP + r"parte\s+(\d+)\s*/\s*(\d+))?\s*$"
)


def sha(testo: str | bytes) -> str:
    dati = testo.encode("utf-8") if isinstance(testo, str) else testo
    return hashlib.sha256(dati).hexdigest()


def leggi_registro(radice: Path) -> dict:
    percorso = radice / REGISTRO
    if not percorso.exists():
        return {"ricevute": {}}
    dati = json.loads(percorso.read_text(encoding="utf-8"))
    dati.setdefault("ricevute", {})
    return dati


def salva_registro(radice: Path, registro: dict) -> Path:
    percorso = radice / REGISTRO
    percorso.parent.mkdir(parents=True, exist_ok=True)
    percorso.write_text(json.dumps(registro, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return percorso


def _percorso_sicuro(relativo: str) -> bool:
    return all(p and p not in {".", ".."} and _SICURO.match(p) for p in relativo.split("/"))


def immagine_ammessa(radice: Path, relativo: str) -> bool:
    """Un'immagine in `books/<slug>/assets/` di un libro che esiste: l'unica che arriva dal ramo."""
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


def su_github(canale: dict | None) -> bool:
    """Il canale su GitHub: richieste sul ramo della fabbrica, consegne con la routine."""
    return bool(cowork.ramo_consegna(canale))


# --------------------------------------------------------------------------
# Le consegne di Cowork
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Consegna:
    tipo: str          # «risposta» o «esito»
    dove: str          # la risposta: il percorso relativo a kdp-book-factory/; l'esito: il ruolo
    parte: int
    parti: int
    testo: str         # tutto quello che sta sotto la prima riga


def _testa(riga: str) -> re.Match | None:
    pulita = riga.strip().strip("`*_«»\"").strip()
    return _TESTA.match(pulita)


def leggi_consegne(testo: str) -> list[Consegna]:
    """Le consegne contenute in un testo, una per ogni prima riga «Cowork · …».

    Quello che sta prima della prima consegna (il prompt della routine, se è
    stato copiato con lei) si scarta. Un testo può portarne più d'una: è il caso
    di un giro senza fire_trigger, che le scrive tutte nell'ultimo messaggio.
    """
    consegne: list[Consegna] = []
    corrente: re.Match | None = None
    corpo: list[str] = []

    def chiudi() -> None:
        if corrente is None:
            return
        tipo, dove, parte, parti = corrente.groups()
        dove = dove.strip("`")
        if tipo == "risposta" and dove.startswith(CARTELLA_FABBRICA + "/"):
            dove = dove[len(CARTELLA_FABBRICA) + 1:]
        consegne.append(Consegna(tipo, dove, int(parte or 1), int(parti or 1),
                                 "\n".join(corpo).strip("\n") + "\n"))

    for riga in testo.lstrip("﻿").splitlines():
        trovata = _testa(riga)
        if trovata:
            chiudi()
            corrente, corpo = trovata, []
        elif corrente is not None:
            corpo.append(riga)
    chiudi()
    return consegne


def _nome_parte(relativo: str, parte: int, parti: int) -> Path:
    return IN_ARRIVO / f"{relativo}.parte-{parte}-di-{parti}"


def ricevi(
    radice: Path, consegna: Consegna, elenco: list[cowork.Richiesta], adesso: datetime | None = None
) -> tuple[str, str]:
    """Salva nel repository quello che Cowork ha consegnato. Restituisce (com'è andata, percorso).

    Com'è andata: «scritta» (la risposta è al suo posto), «in arrivo» (una
    parte di una consegna lunga: mancano le altre), «già» (la stessa risposta
    c'era già: una consegna doppia), «esito» (un giro non riuscito, da leggere).
    ValueError per tutto quello che non può entrare: un percorso che non è la
    risposta di una richiesta, una risposta diversa da quella già salvata.
    """
    adesso = adesso or datetime.now(timezone.utc)
    registro = leggi_registro(radice)
    if consegna.tipo == "esito":
        ruolo = consegna.dove
        if not re.fullmatch(r"[a-z][a-z-]*", ruolo):
            raise ValueError(f"«{ruolo}» non è il nome di un ruolo")
        for vecchio in sorted((radice / ESITI).glob(f"*-{ruolo}.md")):
            if vecchio.read_text(encoding="utf-8") == consegna.testo:
                return "già", vecchio.relative_to(radice).as_posix()
        relativo = (ESITI / f"{adesso:%Y%m%d-%H%M%S}-{ruolo}.md").as_posix()
        (radice / relativo).parent.mkdir(parents=True, exist_ok=True)
        (radice / relativo).write_text(consegna.testo, encoding="utf-8")
        return "esito", relativo

    relativo = consegna.dove
    if not _percorso_sicuro(relativo) or relativo not in {r.risposta for r in elenco}:
        raise ValueError(
            f"«{relativo}» non è la risposta di una richiesta che esiste: resta fuori dal repository"
        )
    if not 1 <= consegna.parte <= consegna.parti:
        raise ValueError(f"{relativo}: parte {consegna.parte} di {consegna.parti}?")
    testo = consegna.testo
    if consegna.parti > 1:
        file = radice / _nome_parte(relativo, consegna.parte, consegna.parti)
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(testo, encoding="utf-8")
        presenti = [radice / _nome_parte(relativo, i, consegna.parti) for i in range(1, consegna.parti + 1)]
        if not all(p.exists() for p in presenti):
            return "in arrivo", relativo
        # Cowork divide fra una riga e l'altra: si ricuce con un a capo.
        testo = "\n".join(p.read_text(encoding="utf-8").rstrip("\n") for p in presenti) + "\n"
    bersaglio = radice / relativo
    if bersaglio.exists():
        if bersaglio.read_text(encoding="utf-8") == testo:
            _togli_parti(radice, relativo)
            return "già", relativo
        # Una risposta di Cowork non si riscrive: se serve altro, un seguito «-2».
        raise ValueError(
            f"{relativo} c'è già, diversa: una risposta di Cowork non si riscrive. "
            "Se serve, apri una richiesta di seguito."
        )
    bersaglio.parent.mkdir(parents=True, exist_ok=True)
    bersaglio.write_text(testo, encoding="utf-8")
    _togli_parti(radice, relativo)
    registro["ricevute"][relativo] = {
        "sha": sha(testo), "quando": adesso.strftime("%Y-%m-%dT%H:%M:%SZ"), "parti": consegna.parti,
    }
    salva_registro(radice, registro)
    return "scritta", relativo


def _togli_parti(radice: Path, relativo: str) -> None:
    for parte in (radice / IN_ARRIVO).glob(f"{relativo}.parte-*"):
        parte.unlink()


def in_arrivo(radice: Path) -> dict[str, list[str]]:
    """Le consegne arrivate solo in parte: per ogni risposta, le parti che ci sono."""
    cartella = radice / IN_ARRIVO
    parti: dict[str, list[str]] = {}
    for file in sorted(cartella.rglob("*.parte-*")) if cartella.exists() else []:
        relativo, _, quale = file.relative_to(cartella).as_posix().rpartition(".parte-")
        parti.setdefault(relativo, []).append(quale.replace("-di-", "/"))
    return parti


def piano(radice: Path, elenco: list[cowork.Richiesta], canale: dict | None = None) -> dict:
    """Che cosa aspettarsi da Cowork in questo giro, e chi lanciare.

    - `attese`: le prime righe delle consegne che possono arrivare, una per
      richiesta aperta;
    - `in_arrivo`: le consegne lunghe arrivate solo in parte;
    - `avvia`: i ruoli da lanciare subito (quelli che lavorano nel cloud).
    """
    canale = canale or {}
    return {
        "routine": canale.get("routine_fabbrica", ""),
        "attese": [cowork.riga_consegna(r.risposta) for r in elenco if r.stato == cowork.APERTA],
        "in_arrivo": in_arrivo(radice),
        "ramo_immagini": RAMO_IMMAGINI,
        "avvia": da_avviare(radice, elenco, canale) if su_github(canale) else [],
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

    Per ogni richiesta: dove leggerla, la prima riga con cui consegnare la
    risposta, e se si può fare in un giro nel cloud o serve il browser del
    portatile.
    """
    repository = canale.get("repository", "Personal-lHUb/NEXTUP")
    ramo = canale.get("ramo", "")
    righe = [
        "# Richieste aperte per Cowork",
        "",
        "<!-- Scritto da `python3 -m kdpfactory cowork corriere` a ogni giro. Non si",
        "     modifica a mano. -->",
        "",
        f"Repository `{repository}`. Le richieste stanno sul ramo `{ramo}` e si leggono",
        "agli indirizzi «leggi». Ogni risposta si consegna lanciando la routine della",
        f"fabbrica (fire_trigger `{canale.get('routine_fabbrica', '')}`): nel testo la riga",
        "«consegna» della richiesta e sotto la risposta intera. La salva la fabbrica, su",
        "GitHub. Cowork non scrive file: né su GitHub né su Google Drive, che non si usa più.",
        f"Le regole: {cowork.link_lettura(canale, 'config/leggimi-cowork.md', ramo)}",
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
                f"  - leggi: {cowork.link_lettura(canale, r.percorso, ramo)}",
                f"  - consegna: `{cowork.riga_consegna(r.risposta)}`",
                f"  - si fa: {dove}" + (f" — serve {r.serve}" if r.serve else ""),
            ]
        righe.append("")
    return "\n".join(righe).rstrip() + "\n"


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

"""Higgsfield: le immagini dei libri generate da questa sessione, dal prompt del sistema.

La regola non cambia: ogni immagine nasce da un prompt scritto da un comando
(`copertina`, `immagini`), mai a mano. Cambia chi la genera. Con Higgsfield non
serve più che l'autore apra ChatGPT nel browser di Cowork né che un file faccia
il giro del corriere: il prompt va al CLI `higgsfield`, l'immagine torna in
`assets/` e la sua traccia (modello, pixel, prompt) resta in
`build/immagini-generate.json`, che serve anche per la dichiarazione dei
contenuti generati con l'IA che KDP chiede al caricamento.

Il CLI richiede un accesso dell'autore (`higgsfield auth login`) e un'area di
lavoro scelta (`higgsfield workspace set`): senza, `pronto()` dice che cosa
manca e nessun comando parte. Nessun token entra nei file del repository.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

ESEGUIBILE = "higgsfield"
#: Il modello di Higgsfield per le immagini di qualità: copertine e figure.
MODELLO_IMMAGINI = "gpt_image_2_5"
REGISTRO = "immagini-generate.json"
ATTESA_MASSIMA = "20m"

#: I gradini di qualità che un modello può dichiarare, dal più basso al più alto.
_QUALITA = ("low", "standard", "medium", "high", "hd", "ultra", "max")
_ESTENSIONI = (".png", ".jpg", ".jpeg", ".webp")


#: Chi genera le immagini della fabbrica, e con che modello.
CONFIGURAZIONE = Path("config") / "immagini.json"


def configurazione(radice: Path) -> dict:
    """`config/immagini.json`: senza, le immagini restano a Cowork come prima."""
    percorso = radice / CONFIGURAZIONE
    if not percorso.exists():
        return {"generatore": "cowork"}
    return json.loads(percorso.read_text(encoding="utf-8"))


def attivo(radice: Path) -> bool:
    return configurazione(radice).get("generatore") == "higgsfield"


class NonPronto(RuntimeError):
    """Higgsfield non si può usare: manca il CLI, l'accesso o l'area di lavoro."""


@dataclass
class Generata:
    file: str
    modello: str
    larghezza: int
    altezza: int
    url: str = ""
    job: str = ""
    prompt_sha: str = ""
    quando: str = ""

    def basta(self, minimo: tuple[int, int]) -> bool:
        return self.larghezza >= minimo[0] and self.altezza >= minimo[1]


# --------------------------------------------------------------------------
# Il CLI
# --------------------------------------------------------------------------
def _esegui(argomenti: list[str], eseguitore=subprocess.run, timeout: int = 1500):
    return eseguitore(
        [ESEGUIBILE, *argomenti], capture_output=True, text=True, timeout=timeout, check=False
    )


def pronto(eseguitore=subprocess.run, cerca=shutil.which) -> str | None:
    """`None` se si può generare; altrimenti che cosa manca, detto all'autore."""
    if cerca(ESEGUIBILE) is None:
        return "il CLI di Higgsfield non è installato: `npm i -g @higgsfield/cli`"
    if _esegui(["auth", "token"], eseguitore, timeout=60).returncode != 0:
        return "manca l'accesso a Higgsfield: `higgsfield auth login` (lo fa l'autore)"
    prova = _esegui(["model", "get", MODELLO_IMMAGINI, "--json"], eseguitore, timeout=60)
    if prova.returncode != 0:
        testo = f"{prova.stdout}\n{prova.stderr}".strip()
        if "workspace" in testo.lower():
            return "manca l'area di lavoro di Higgsfield: `higgsfield workspace set <id>`"
        return f"Higgsfield non risponde: {testo.splitlines()[0] if testo else 'errore senza messaggio'}"
    return None


def schema(modello: str = MODELLO_IMMAGINI, eseguitore=subprocess.run) -> dict:
    esito = _esegui(["model", "get", modello, "--json"], eseguitore, timeout=60)
    if esito.returncode != 0:
        raise NonPronto((esito.stderr or esito.stdout).strip() or f"modello {modello} non trovato")
    return json.loads(esito.stdout)


def _valori(schema_modello: dict, nome: str) -> list[str]:
    """I valori ammessi di un parametro, dovunque lo schema li tenga."""
    trovati: list[str] = []

    def visita(nodo, chiave=""):
        if isinstance(nodo, dict):
            if chiave == nome or nodo.get("name") == nome:
                for campo in ("enum", "values", "options", "allowed"):
                    valori = nodo.get(campo)
                    if isinstance(valori, list):
                        trovati.extend(str(v.get("value", v)) if isinstance(v, dict) else str(v)
                                       for v in valori)
            for k, v in nodo.items():
                visita(v, k)
        elif isinstance(nodo, list):
            for v in nodo:
                visita(v, chiave)

    visita(schema_modello)
    return list(dict.fromkeys(trovati))


def _numero_risoluzione(valore: str) -> float:
    """«4k» → 4000, «2048» → 2048, «1.5k» → 1500, «1080p» → 1080."""
    corrispondenza = re.match(r"^\s*(\d+(?:\.\d+)?)\s*([kKpP]?)", valore)
    if not corrispondenza:
        return 0.0
    numero, unita = float(corrispondenza.group(1)), corrispondenza.group(2).lower()
    return numero * 1000 if unita == "k" else numero


def parametri(schema_modello: dict, proporzione: str) -> list[str]:
    """I flag per la resa migliore che il modello dichiara: proporzione, risoluzione, qualità.

    La risoluzione più alta disponibile, sempre: la stampa ne chiede tanta, e una
    copertina che non basta va ingrandita, che è peggio che generarla grande.
    Se il modello non dichiara la proporzione chiesta si passa quella più vicina.
    """
    flag: list[str] = []
    proporzioni = _valori(schema_modello, "aspect_ratio")
    if proporzioni and proporzione not in proporzioni:
        def rapporto(p: str) -> float:
            try:
                a, b = (float(x) for x in p.split(":"))
                return a / b
            except ValueError:
                return 99.0
        voluto = rapporto(proporzione)
        proporzione = min((p for p in proporzioni if ":" in p),
                          key=lambda p: abs(rapporto(p) - voluto), default=proporzione)
    flag += ["--aspect_ratio", proporzione]
    risoluzioni = _valori(schema_modello, "resolution")
    if risoluzioni:
        flag += ["--resolution", max(risoluzioni, key=_numero_risoluzione)]
    qualita = [q for q in _valori(schema_modello, "quality") if q.lower() in _QUALITA]
    if qualita:
        flag += ["--quality", max(qualita, key=lambda q: _QUALITA.index(q.lower()))]
    return flag


def _url_immagine(risposta) -> tuple[str, str]:
    """Il primo indirizzo d'immagine nella risposta del CLI, e l'id del lavoro."""
    url, job = "", ""

    def visita(nodo):
        nonlocal url, job
        if isinstance(nodo, dict):
            if not job and isinstance(nodo.get("id"), str):
                job = nodo["id"]
            for chiave in ("url", "raw_url", "image_url", "result_url", "min_url"):
                valore = nodo.get(chiave)
                if not url and isinstance(valore, str) and valore.startswith("http"):
                    url = valore
            for v in nodo.values():
                visita(v)
        elif isinstance(nodo, list):
            for v in nodo:
                visita(v)
        elif isinstance(nodo, str) and not url and nodo.startswith("http"):
            if nodo.split("?")[0].lower().endswith(_ESTENSIONI):
                url = nodo

    visita(risposta)
    return url, job


def _scarica(url: str, destinazione: Path) -> None:
    with urllib.request.urlopen(url, timeout=300) as risposta:  # noqa: S310 - indirizzo del CLI
        destinazione.write_bytes(risposta.read())


def genera(
    prompt: str,
    destinazione: Path,
    *,
    proporzione: str,
    modello: str = MODELLO_IMMAGINI,
    eseguitore=subprocess.run,
    scarica=_scarica,
    schema_modello: dict | None = None,
) -> Generata:
    """Genera un'immagine dal prompt e la salva in `destinazione`, alla resa più alta."""
    schema_modello = schema_modello if schema_modello is not None else schema(modello, eseguitore)
    argomenti = ["generate", "create", modello, "--prompt", prompt,
                 *parametri(schema_modello, proporzione),
                 "--wait", "--wait-timeout", ATTESA_MASSIMA, "--json"]
    esito = _esegui(argomenti, eseguitore)
    if esito.returncode != 0:
        raise RuntimeError(f"Higgsfield ha rifiutato il lavoro: {(esito.stderr or esito.stdout).strip()}")
    try:
        risposta = json.loads(esito.stdout)
    except ValueError as errore:
        raise RuntimeError(f"risposta di Higgsfield non leggibile: {esito.stdout[:200]}") from errore
    url, job = _url_immagine(risposta)
    if not url:
        raise RuntimeError("Higgsfield ha finito il lavoro senza un indirizzo d'immagine.")
    destinazione.parent.mkdir(parents=True, exist_ok=True)
    grezzo = destinazione.with_name(destinazione.name + ".scaricato")
    scarica(url, grezzo)

    from PIL import Image

    # Il file prende il formato che il suo nome dichiara: il manoscritto chiede
    # «03-mappa.jpg», e un PNG col nome .jpg inganna chi lo apre dopo.
    formati = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP"}
    with Image.open(grezzo) as immagine:
        larghezza, altezza = immagine.size
        formato = formati.get(destinazione.suffix.lower(), "PNG")
        uscita = immagine.convert("RGB") if formato == "JPEG" else immagine
        uscita.save(destinazione, formato, **({"quality": 95} if formato == "JPEG" else {}))
    grezzo.unlink()
    return Generata(
        file=str(destinazione),
        modello=modello,
        larghezza=larghezza,
        altezza=altezza,
        url=url,
        job=job,
        prompt_sha=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        quando=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def registra(build_dir: Path, generate: list[Generata]) -> Path:
    """La traccia di ogni immagine generata: che modello, quanti pixel, da quale prompt.

    È il dato che KDP chiede al caricamento («contenuti generati con l'IA») e
    quello che serve per rifare un'immagine uguale.
    """
    percorso = build_dir / REGISTRO
    voci = json.loads(percorso.read_text(encoding="utf-8")) if percorso.exists() else []
    voci += [asdict(g) for g in generate]
    percorso.parent.mkdir(parents=True, exist_ok=True)
    percorso.write_text(json.dumps(voci, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return percorso

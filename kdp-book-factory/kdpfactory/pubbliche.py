"""Le figure che non si possono generare: immagini pubbliche, di pubblico dominio o CC0.

Una figura generata va bene finché inventa: un ambiente, un oggetto, una scena
del mondo del libro. Non va bene quando il lettore deve riconoscere qualcosa di
vero — una persona reale, un luogo preciso, un documento, un fatto storico,
un'opera d'arte —: lì un'immagine generata è un falso. Per quelle il piano delle
figure (`figure.json`) dice `"fonte": "pubblica"` e che cosa cercare, e questo
modulo cerca negli archivi aperti solo quello che si può stampare senza
obblighi: **pubblico dominio e CC0** (scelta dell'autore, 7 ottobre 2026).

Due archivi bastano a coprire quasi tutto:

- **Openverse** (api.openverse.org), che raccoglie Wikimedia, musei, archivi e
  collezioni fotografiche, e filtra per licenza già nella domanda;
- **Wikimedia Commons** (commons.wikimedia.org), per i file che Openverse non
  indicizza, con la licenza letta dai metadati di ogni file.

La licenza si verifica due volte: nella ricerca e quando si prende il file. La
provenienza — archivio, titolo, autore, licenza, pagina, indirizzo del file,
data — resta nel piano, accanto alla figura, e `qa` non stampa una figura
pubblica che non ce l'ha. Nessuna chiamata parte dai test.
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from . import figure as figure_module

OPENVERSE = "https://api.openverse.org/v1/images/"
COMMONS = "https://commons.wikimedia.org/w/api.php"
#: Wikimedia chiede a chi usa le sue API di presentarsi
USER_AGENT = "NEXTUP-kdp-book-factory/1.0 (immagini pubbliche per libri; https://github.com/Personal-lHUb/NEXTUP)"
#: i domini da aprire nella rete dell'ambiente perché la ricerca funzioni; i
#: file stanno poi sui server di ciascun archivio (upload.wikimedia.org, …)
DOMINI = ("api.openverse.org", "commons.wikimedia.org", "upload.wikimedia.org")
#: quanti candidati per figura, per archivio
QUANTI = 6


@dataclass
class Candidato:
    """Un'immagine trovata, con quello che serve per stamparla in regola."""

    archivio: str
    titolo: str
    autore: str
    licenza: str           # canonica: «CC0 1.0», «Public Domain Mark 1.0», «Public domain»
    url_licenza: str
    pagina: str            # la pagina dell'opera nell'archivio
    file_url: str          # il file a piena risoluzione
    larghezza: int = 0
    altezza: int = 0
    anteprima: str = ""
    #: le avvertenze dell'archivio (Commons: «personality», diritti della
    #: persona ritratta); un marchio registrato il candidato lo esclude
    restrizioni: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def licenza_canonica(codice: str, versione: str = "") -> str:
    """Il nome della licenza come resta scritto nel piano, o vuoto se non è ammessa."""
    valore = " ".join((codice or "").lower().replace("-", " ").replace("_", " ").split())
    if valore in {"cc0", "cc zero", "cc0 1.0"} or valore.startswith("cc0"):
        return "CC0 1.0"
    if valore in {"pdm", "public domain mark", "pdm 1.0"} or valore.startswith("public domain mark"):
        return "Public Domain Mark 1.0"
    if valore in {"pd", "public domain"} or valore.startswith("public domain") or valore.startswith("pd "):
        return "Public domain"
    return ""


def _leggi(url: str, apri, timeout: int = 60) -> dict:
    richiesta = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with apri(richiesta, timeout=timeout) as risposta:
        return json.loads(risposta.read().decode("utf-8"))


def cerca_openverse(termini: str, apri=urllib.request.urlopen, quanti: int = QUANTI) -> list[Candidato]:
    """Openverse, già filtrato per licenza: solo CC0 e marchio di pubblico dominio."""
    query = urllib.parse.urlencode({
        "q": termini, "license": "cc0,pdm", "page_size": quanti, "mature": "false",
    })
    dati = _leggi(f"{OPENVERSE}?{query}", apri)
    trovati = []
    for voce in dati.get("results") or []:
        licenza = licenza_canonica(voce.get("license", ""), voce.get("license_version", ""))
        if not licenza or not voce.get("url"):
            continue
        trovati.append(Candidato(
            archivio=f"Openverse ({voce.get('source') or voce.get('provider') or '?'})",
            titolo=voce.get("title") or "",
            autore=voce.get("creator") or "",
            licenza=licenza,
            url_licenza=voce.get("license_url") or "",
            pagina=voce.get("foreign_landing_url") or "",
            file_url=voce["url"],
            larghezza=int(voce.get("width") or 0),
            altezza=int(voce.get("height") or 0),
            anteprima=voce.get("thumbnail") or "",
        ))
    return trovati


def _testo(html: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", " ", html or "").split())


def cerca_commons(termini: str, apri=urllib.request.urlopen, quanti: int = QUANTI) -> list[Candidato]:
    """Wikimedia Commons: la licenza la dicono i metadati del file, e si legge lì."""
    query = urllib.parse.urlencode({
        "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
        "gsrsearch": f"{termini} filetype:bitmap", "gsrlimit": quanti * 3,
        "prop": "imageinfo", "iiprop": "url|size|extmetadata", "iiurlwidth": 400,
    })
    dati = _leggi(f"{COMMONS}?{query}", apri)
    trovati = []
    for pagina in sorted((dati.get("query") or {}).get("pages", {}).values(),
                         key=lambda p: p.get("index", 0)):
        info = (pagina.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata") or {}
        codice = (meta.get("License") or {}).get("value", "")
        breve = (meta.get("LicenseShortName") or {}).get("value", "")
        licenza = licenza_canonica(codice) or licenza_canonica(breve)
        restrizioni = (meta.get("Restrictions") or {}).get("value", "")
        if not licenza or not info.get("url") or "trademark" in restrizioni.lower():
            continue
        trovati.append(Candidato(
            archivio="Wikimedia Commons",
            titolo=_testo((meta.get("ObjectName") or {}).get("value", "")) or pagina.get("title", ""),
            autore=_testo((meta.get("Artist") or {}).get("value", "")),
            licenza=licenza,
            url_licenza=(meta.get("LicenseUrl") or {}).get("value", ""),
            pagina=info.get("descriptionurl", ""),
            file_url=info["url"],
            larghezza=int(info.get("width") or 0),
            altezza=int(info.get("height") or 0),
            anteprima=info.get("thumburl", ""),
            restrizioni=restrizioni,
        ))
        if len(trovati) >= quanti:
            break
    return trovati


def cerca(termini: str, apri=urllib.request.urlopen) -> tuple[list[Candidato], list[str]]:
    """I candidati dei due archivi, e gli archivi che non hanno risposto (col motivo)."""
    candidati: list[Candidato] = []
    errori: list[str] = []
    for nome, funzione in (("Openverse", cerca_openverse), ("Wikimedia Commons", cerca_commons)):
        try:
            candidati += funzione(termini, apri)
        except (OSError, ValueError) as errore:
            errori.append(f"{nome}: {errore}")
    return candidati, errori


def prendi(candidato: Candidato | dict, destinazione: Path, apri=urllib.request.urlopen) -> dict:
    """Scarica il file e restituisce la provenienza da scrivere nel piano.

    Rifiuta una licenza che non sia pubblico dominio o CC0 e un file che non è
    un'immagine. Il formato segue l'estensione chiesta dal manoscritto.
    """
    dati = candidato.to_dict() if isinstance(candidato, Candidato) else dict(candidato)
    licenza = licenza_canonica(dati.get("licenza", ""))
    if not licenza or not figure_module.licenza_ammessa(licenza):
        raise ValueError(f"Licenza «{dati.get('licenza')}» non ammessa: solo pubblico dominio o CC0.")
    richiesta = urllib.request.Request(dati["file_url"], headers={"User-Agent": USER_AGENT})
    with apri(richiesta, timeout=300) as risposta:
        contenuto = risposta.read()

    import io

    from PIL import Image

    try:
        with Image.open(io.BytesIO(contenuto)) as immagine:
            immagine.load()
            formati = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".tif": "TIFF", ".tiff": "TIFF"}
            formato = formati.get(destinazione.suffix.lower(), "PNG")
            uscita = immagine.convert("RGB") if formato == "JPEG" and immagine.mode not in {"RGB", "L"} \
                else immagine
            destinazione.parent.mkdir(parents=True, exist_ok=True)
            uscita.save(destinazione, formato, **({"quality": 95} if formato == "JPEG" else {}))
            larghezza, altezza = immagine.size
    except OSError as errore:
        raise ValueError(f"Il file di {dati['file_url']} non è un'immagine leggibile.") from errore
    return {
        "archivio": dati.get("archivio", ""),
        "titolo": dati.get("titolo", ""),
        "autore": dati.get("autore", ""),
        "licenza": licenza,
        "url_licenza": dati.get("url_licenza", ""),
        "pagina": dati.get("pagina", ""),
        "file_url": dati["file_url"],
        "pixel": [larghezza, altezza],
        "restrizioni": dati.get("restrizioni", ""),
        "scaricata_il": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
    }


def da_cercare(piano: dict | None, assets_dir: Path) -> list[dict]:
    """Le figure pubbliche del piano che non hanno ancora il file."""
    return [
        voce for voce in (piano or {}).get("figure") or []
        if voce.get("fonte") == "pubblica" and voce.get("percorso")
        and not (Path(assets_dir) / voce["percorso"]).exists()
    ]

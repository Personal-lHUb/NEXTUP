"""Le decisioni dell'autore, con il silenzio-assenso.

Un libro fatto in automatico si fermerebbe sei volte: categoria, titolo,
promessa, voce narrante, prezzo, copertina. L'autore ha scelto il
silenzio-assenso: la sessione gli manda la proposta degli agenti con le
alternative e, se entro il tempo fissato non risponde, procede con la proposta.
La pubblicazione no: quella resta sempre sua, e non ha scadenza.

Il registro sta in `books/<slug>/decisioni.json` ed entra in git: è la traccia di
chi ha deciso che cosa e quando. Questo modulo non applica niente ai file del
libro — titolo in `book.json`, variante della copertina, prezzo — lo fa la
sessione, che poi segna la decisione come applicata.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .models import BookProject

#: Le decisioni che il silenzio-assenso può chiudere.
CHIAVI = ("categoria", "titolo", "promessa", "voce", "prezzo", "copertina", "pseudonimo")
#: Quella che non chiude mai: un libro non si pubblica perché nessuno ha risposto.
MAI = "pubblicazione"
ORE_PREDEFINITE = 24

IN_ATTESA, DALL_AUTORE, SILENZIO = "in attesa", "scelta dall'autore", "silenzio-assenso"


def _ora() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _iso(momento: datetime) -> str:
    return momento.isoformat().replace("+00:00", "Z")


def _da_iso(testo: str) -> datetime:
    return datetime.fromisoformat(testo.replace("Z", "+00:00"))


def percorso(project: BookProject) -> Path:
    return project.root / "decisioni.json"


def leggi(project: BookProject) -> list[dict]:
    file = percorso(project)
    if not file.exists():
        return []
    return json.loads(file.read_text(encoding="utf-8")).get("decisioni", [])


def salva(project: BookProject, decisioni: list[dict]) -> Path:
    file = percorso(project)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(
        json.dumps({"decisioni": decisioni}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return file


def proponi(
    project: BookProject,
    chiave: str,
    proposta: str,
    alternative: list[str] | None = None,
    perche: str = "",
    ore: int | None = ORE_PREDEFINITE,
    adesso: datetime | None = None,
) -> dict:
    """Registra una proposta in attesa della risposta dell'autore, con la sua scadenza.

    Con `ore` a None (o zero) la proposta non scade: aspetta la risposta
    dell'autore, comunque vada. È il caso in cui l'autore ha spento il
    silenzio-assenso (`silenzio_assenso_ore: null` in `config/produzione.json`).
    """
    if chiave == MAI:
        raise ValueError("La pubblicazione non passa dal silenzio-assenso: la decide l'autore.")
    if chiave not in CHIAVI:
        raise ValueError(f"Decisione sconosciuta: {chiave}. Ammesse: {', '.join(CHIAVI)}.")
    adesso = adesso or _ora()
    decisioni = leggi(project)
    if any(d["chiave"] == chiave and d["stato"] == IN_ATTESA for d in decisioni):
        raise ValueError(f"C'è già una proposta in attesa per «{chiave}».")
    voce = {
        "chiave": chiave,
        "proposta": proposta,
        "alternative": list(alternative or []),
        "perche": perche,
        "chiesta_il": _iso(adesso),
        "scade_il": _iso(adesso + timedelta(hours=ore)) if ore else "",
        "stato": IN_ATTESA,
        "valore": "",
        "deciso_il": "",
        "applicata": False,
    }
    decisioni.append(voce)
    salva(project, decisioni)
    return voce


def _ultima(decisioni: list[dict], chiave: str, stato: str | None = None) -> dict | None:
    for voce in reversed(decisioni):
        if voce["chiave"] == chiave and (stato is None or voce["stato"] == stato):
            return voce
    return None


def scegli(project: BookProject, chiave: str, valore: str, adesso: datetime | None = None) -> dict:
    """La risposta dell'autore: chiude la proposta in attesa, o ne apre una già decisa."""
    decisioni = leggi(project)
    voce = _ultima(decisioni, chiave, IN_ATTESA)
    if voce is None:
        voce = {"chiave": chiave, "proposta": "", "alternative": [], "perche": "",
                "chiesta_il": "", "scade_il": "", "applicata": False}
        decisioni.append(voce)
    voce.update(stato=DALL_AUTORE, valore=valore, deciso_il=_iso(adesso or _ora()), applicata=False)
    salva(project, decisioni)
    return voce


def chiudi_scadute(project: BookProject, adesso: datetime | None = None) -> list[dict]:
    """Le proposte senza risposta oltre la scadenza diventano decise per silenzio-assenso."""
    adesso = adesso or _ora()
    decisioni = leggi(project)
    chiuse = []
    for voce in decisioni:
        if voce["stato"] == IN_ATTESA and voce["scade_il"] and _da_iso(voce["scade_il"]) <= adesso:
            voce.update(stato=SILENZIO, valore=voce["proposta"], deciso_il=_iso(adesso))
            chiuse.append(voce)
    if chiuse:
        salva(project, decisioni)
    return chiuse


def togli_scadenze(project: BookProject) -> list[dict]:
    """Le proposte in attesa perdono la scadenza: aspettano l'autore, senza silenzio-assenso."""
    decisioni = leggi(project)
    tolte = [v for v in decisioni if v["stato"] == IN_ATTESA and v.get("scade_il")]
    for voce in tolte:
        voce["scade_il"] = ""
    if tolte:
        salva(project, decisioni)
    return tolte


def segna_applicata(project: BookProject, chiave: str) -> dict:
    decisioni = leggi(project)
    voce = next(
        (v for v in reversed(decisioni) if v["chiave"] == chiave and v["stato"] != IN_ATTESA), None
    )
    if voce is None:
        raise ValueError(f"Nessuna decisione presa per «{chiave}».")
    voce["applicata"] = True
    salva(project, decisioni)
    return voce


def in_attesa(project: BookProject) -> list[dict]:
    return [v for v in leggi(project) if v["stato"] == IN_ATTESA]


def da_applicare(project: BookProject) -> list[dict]:
    return [v for v in leggi(project) if v["stato"] != IN_ATTESA and not v.get("applicata")]


def valore(project: BookProject, chiave: str) -> str | None:
    """Il valore deciso per una chiave, dall'autore o per silenzio-assenso; None se non c'è."""
    voce = next(
        (v for v in reversed(leggi(project)) if v["chiave"] == chiave and v["stato"] != IN_ATTESA), None
    )
    return voce["valore"] if voce else None


def messaggio(slug: str, voce: dict) -> str:
    """La proposta come la legge l'autore, con la scadenza: una riga per la notifica e il resto."""
    alternative = "".join(f"\n  - {a}" for a in voce.get("alternative") or [])
    return (
        f"{slug} · {voce['chiave']}: proposta «{voce['proposta']}»"
        + (f"\n  perché: {voce['perche']}" if voce.get("perche") else "")
        + (f"\n  alternative:{alternative}" if alternative else "")
        + (f"\n  se non rispondi entro {voce['scade_il']} (UTC), procedo con la proposta."
           if voce.get("scade_il") else "\n  aspetto la tua risposta: senza, questa decisione resta ferma.")
    )

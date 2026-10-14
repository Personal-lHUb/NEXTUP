"""I controlli legali che si misurano: temi esclusi e riferimenti al concorrente.

Le linee rosse di `docs/rischi-legali.md` che un comando può verificare da sé
(regola 4 di CLAUDE.md); le altre, che chiedono di leggere il testo, sono
dell'agente `conformita`. Entrano nel controllo qualità come errori: un libro
che ne ha uno non si carica.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from . import temi
from .models import BookProject, BookSpec

#: i campi della scheda del concorrente che non devono mai comparire nel libro
CAMPI_CONCORRENTE = ("titolo", "autore", "editore", "asin")


def concorrente(project: BookProject) -> dict[str, str]:
    """Titolo, autore, editore e ASIN del libro da cui la fabbrica è partita, se ci sono."""
    try:
        dati = json.loads((project.root / "concorrente" / "scheda.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {campo: str(dati.get(campo) or "").strip() for campo in CAMPI_CONCORRENTE
            if len(str(dati.get(campo) or "").strip()) >= 4}


def _testi_metadati(meta: dict, cover: dict) -> list[tuple[str, str]]:
    voci: list[tuple[str, str]] = []
    for chiave in ("title", "subtitle", "closing", "author_bio", "back_cover", "cover_hook",
                   "cover_kicker", "cover_badge"):
        if meta.get(chiave):
            voci.append((f"scheda: {chiave}", str(meta[chiave])))
    for chiave in ("description_paragraphs", "bullets", "keywords", "back_cover_bullets"):
        for n, valore in enumerate(meta.get(chiave) or [], start=1):
            voci.append((f"scheda: {chiave} {n}", str(valore)))
    for chiave, valore in ((cover or {}).get("testi") or {}).items():
        if isinstance(valore, str) and valore:
            voci.append((f"copertina: {chiave}", valore))
    return voci


def riferimenti_al_concorrente(
    project: BookProject, spec: BookSpec, chapters: list[tuple[int, str, str]],
    meta: dict | None = None, cover: dict | None = None,
) -> list[str]:
    """Dove il libro nomina titolo, autore, editore o ASIN del concorrente.

    KDP vieta nei metadati i riferimenti non autorizzati ad altri titoli e
    autori; nel libro, un nome altrui fa pensare a un legame che non c'è.
    """
    rivale = concorrente(project)
    if not rivale:
        return []
    luoghi = [("titolo", spec.title), ("sottotitolo", spec.subtitle)]
    luoghi += [(f"capitolo {numero}", testo) for numero, _, testo in chapters]
    luoghi += _testi_metadati(meta or {}, cover or {})
    trovati = []
    for campo, valore in rivale.items():
        cerca = re.compile(rf"(?<!\w){re.escape(valore)}(?!\w)", re.IGNORECASE)
        for dove, testo in luoghi:
            if testo and cerca.search(testo):
                trovati.append(f"{campo} del concorrente («{valore}») in {dove}")
    return trovati


def controlla(project: BookProject, spec: BookSpec, chapters: list[tuple[int, str, str]],
              state: dict, report) -> None:
    """Aggiunge al rapporto di `qa` gli errori legali che si misurano."""
    for motivo in temi.per_libro(spec):
        report.add("errore", "TEMA", f"tema escluso dall'autore — {motivo} (docs/rischi-legali.md)")
    meta = state.get("metadata") or {}
    scheda = project.build_dir / "metadata.json"
    if not meta and scheda.exists():
        try:
            meta = json.loads(Path(scheda).read_text(encoding="utf-8"))
        except ValueError:
            meta = {}
    for trovato in riferimenti_al_concorrente(project, spec, chapters, meta, state.get("cover")):
        report.add("errore", "CONCORRENTE", trovato)

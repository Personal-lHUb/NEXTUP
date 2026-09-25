"""La vetrina: quello che il cliente vede prima di pagare.

Copertina (titolo, sottotitolo, gancio), descrizione della pagina Amazon e
indice dell'anteprima. È la promessa che il libro fa, ed è l'unica cosa che il
lettore cieco riceve oltre ai capitoli: gli serve per dire se il libro la
mantiene, senza sapere niente di quello che l'autore voleva fare.

Si scrive a ogni `build` in `build/vetrina.md`, con le pagine vere. Non
contiene niente che il cliente non veda: né la scaletta, né le note d'autore,
né le parole chiave, che su Amazon non si leggono.
"""

from __future__ import annotations

import json
from pathlib import Path

from .i18n import part_label
from .models import BookProject, BookSpec, Outline


def indice(
    outline: Outline,
    language: str,
    chapter_pages: dict[str, int] | None = None,
    part_pages: dict[str, int] | None = None,
) -> str:
    """L'indice come lo stampa il libro: parti, capitoli e, se ci sono, le pagine."""
    chapter_pages = chapter_pages or {}
    part_pages = part_pages or {}

    def pagina(numero: int | None) -> str:
        return f" · p. {numero}" if numero else ""

    righe: list[str] = []
    for chapter in outline.chapters:
        apertura = outline.part_opening(chapter.number)
        if apertura:
            indice_parte, parte = apertura
            voce = f"{part_label(language, indice_parte)} — {parte.title}"
            righe += ["", f"**{voce}**{pagina(part_pages.get(voce))}", ""]
        righe.append(f"{chapter.number}. {chapter.title}{pagina(chapter_pages.get(chapter.title))}")
    return "\n".join(righe).strip("\n")


def testo(
    spec: BookSpec,
    outline: Outline,
    meta: dict,
    cover_copy: dict | None = None,
    chapter_pages: dict[str, int] | None = None,
    part_pages: dict[str, int] | None = None,
) -> str:
    cover_copy = cover_copy or {}
    gancio = cover_copy.get("hook") or meta.get("cover_hook") or ""
    righe = [f"# {spec.title}"]
    if spec.subtitle:
        righe.append(f"*{spec.subtitle}*")
    righe.append(f"di {spec.author}")
    if gancio:
        righe += ["", f"Sulla copertina: «{gancio}»"]
    descrizione = meta.get("description_paragraphs") or []
    elenco = meta.get("bullets") or []
    if descrizione or elenco:
        righe += ["", "## La descrizione su Amazon", ""]
        righe += [f"{paragrafo}\n" for paragrafo in descrizione]
        righe += [f"- {voce}" for voce in elenco]
        if meta.get("closing"):
            righe += ["", meta["closing"]]
    righe += ["", "## L'indice", "", indice(outline, spec.language, chapter_pages, part_pages)]
    return "\n".join(righe).rstrip() + "\n"


def da_progetto(project: BookProject, spec: BookSpec, outline: Outline) -> str:
    """La vetrina con quello che il progetto sa adesso: pagine e scheda, se ci sono."""
    state = project.load_state()
    build = state.get("build") or {}
    meta_path = project.build_dir / "metadata.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    return testo(
        spec,
        outline,
        meta,
        cover_copy=(state.get("cover") or {}).get("testi") or {},
        chapter_pages=build.get("chapter_pages") or {},
        part_pages=build.get("part_pages") or {},
    )


def scrivi(project: BookProject, spec: BookSpec, outline: Outline) -> Path:
    path = project.build_dir / "vetrina.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(da_progetto(project, spec, outline), encoding="utf-8")
    return path


def scheda(meta: dict, spec: BookSpec) -> str:
    """La scheda prodotto come la legge chi la controlla: tutti i campi, anche quelli
    che il cliente non vede (parole chiave, categorie)."""
    righe = [f"Titolo: {meta.get('title') or spec.title}",
             f"Sottotitolo: {meta.get('subtitle') or spec.subtitle}", "", "Descrizione:"]
    righe += meta.get("description_paragraphs") or []
    righe += [f"- {voce}" for voce in meta.get("bullets") or []]
    if meta.get("closing"):
        righe.append(meta["closing"])
    righe += ["", "Parole chiave:"] + [f"- {k}" for k in meta.get("keywords") or spec.keywords]
    righe += ["", "Categorie:"] + [f"- {c}" for c in meta.get("categories") or spec.categories]
    if meta.get("author_bio"):
        righe += ["", f"Biografia dell'autore: {meta['author_bio']}"]
    return "\n".join(righe) + "\n"

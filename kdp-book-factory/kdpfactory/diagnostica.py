"""Diagnostica del sistema: i fatti su cui ragiona il team di miglioramento.

Questo modulo **non giudica e non usa il modello**. Misura, su tutti i libri
prodotti, le cose che si possono contare — e le mette in un file solo. È lo
stesso principio dell'agente di impaginazione: una misura vale più di
un'opinione, e costa meno.

Quattro famiglie di misure:

- **economia**: costo API per libro, costo di stampa, prezzo, royalty per copia
  e quante copie servono per ripagare la produzione;
- **produzione**: iterazioni di impaginazione per arrivare nell'intervallo di
  pagine, parole per pagina misurate, quanto ha sbagliato la stima;
- **qualità**: segnalazioni del controllo qualità e del collegio, raggruppate
  per codice — quelle che tornano in ogni libro sono difetti del sistema, non
  del libro;
- **scheda prodotto**: i limiti veri di KDP (7 parole chiave da 50 caratteri,
  3 categorie, 4000 caratteri di descrizione, il taglio a 185 caratteri prima
  di «Leggi di più») e gli sprechi che si misurano — per esempio una parola
  chiave che ripete una parola del titolo, già indicizzata di suo.

Il rapporto si legge con `python3 -m kdpfactory diagnostica` e si salva in
`diagnostica.json`: è quello che il team di agenti riceve in pasto.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import metadata as metadata_module
from .models import BookProject, BookSpec

# --------------------------------------------------------------------------
# Limiti veri della scheda KDP: non sono opinioni, sono i campi del modulo
# --------------------------------------------------------------------------
KEYWORD_SLOTS = 7
KEYWORD_MAX_CHARS = 50
CATEGORY_SLOTS = 3
DESCRIPTION_MAX_CHARS = 4000
#: quanto si legge prima di «Leggi di più» sulla scheda
DESCRIPTION_FOLD_CHARS = 185
#: oltre questa lunghezza il titolo viene troncato nei risultati di ricerca
TITLE_TRUNCATION_CHARS = 60

#: parole troppo generiche per occupare uno slot: non le cerca nessuno da sole
WEAK_KEYWORDS = {
    "libro", "libri", "book", "books", "guida", "guide", "manuale", "nuovo",
    "best", "migliore", "regalo", "gift", "italiano", "english", "edizione",
}


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[\wàèéìòù']+", text.lower()) if len(w) > 3}


# --------------------------------------------------------------------------
# Misure per libro
# --------------------------------------------------------------------------
@dataclass
class Finding:
    """Un fatto che merita una decisione. `impatto` è l'ordine di lettura."""

    area: str          # economia | produzione | qualita | scheda | copertina
    impatto: str       # alto | medio | basso
    fatto: str         # la misura, con i numeri
    leva: str = ""     # dove si interviene, se è evidente dalla misura

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class BookReport:
    slug: str
    titolo: str = ""
    lingua: str = ""
    genere: str = ""
    categoria: str = ""      # full | medium, vedi CLAUDE.md
    pagine: int = 0
    economia: dict = field(default_factory=dict)
    produzione: dict = field(default_factory=dict)
    qualita: dict = field(default_factory=dict)
    scheda: dict = field(default_factory=dict)
    copertina: dict = field(default_factory=dict)
    rilievi: list[Finding] = field(default_factory=list)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["rilievi"] = [f.to_dict() for f in self.rilievi]
        return data


def _economia(spec: BookSpec, state: dict, pages: int, report: BookReport) -> None:
    """Quanto è costato e quanto rende: l'unico conto che decide se rifarlo."""
    usage = state.get("usage") or {}
    api_cost = float(usage.get("estimated_cost_usd") or 0.0)

    prices = metadata_module.price_table(pages) if pages else []
    # Si guarda il mercato in dollari: è quello in cui il costo API è confrontabile
    # con la royalty senza passare da un cambio.
    row = next((p for p in prices if p.marketplace.startswith("amazon.com")), None) or (
        prices[0] if prices else None
    )
    royalty = row.royalty if row else 0.0
    print_cost = row.printing_cost if row else 0.0

    report.economia = {
        "costo_api_usd": round(api_cost, 4),
        "token_input": usage.get("input_tokens", 0),
        "token_output": usage.get("output_tokens", 0),
        "token_cache_letti": usage.get("cache_read_tokens", 0),
        "costo_stampa": round(print_cost, 2),
        "prezzo_consigliato": round(row.suggested_price, 2) if row else 0.0,
        "royalty_per_copia": round(royalty, 2),
        "copie_per_ripagare_api": round(api_cost / royalty, 1) if royalty > 0 else None,
        "mercato": row.marketplace if row else "",
    }

    if api_cost and royalty > 0:
        copies = api_cost / royalty
        report.rilievi.append(Finding(
            "economia", "basso" if copies < 5 else "alto",
            f"Il libro è costato ${api_cost:.2f} di API e rende "
            f"{row.symbol}{royalty:.2f} a copia: si ripaga con {copies:.1f} copie.",
            "" if copies < 5 else "Ridurre le chiamate o passare a un modello più economico "
            "per le passate di controllo.",
        ))
    elif not api_cost:
        report.rilievi.append(Finding(
            "economia", "basso",
            "Prodotto senza nessuna chiamata API: costo di produzione zero.",
        ))

    if royalty > 0 and royalty < 2.0:
        report.rilievi.append(Finding(
            "economia", "alto",
            f"Royalty di {row.symbol}{royalty:.2f} a copia su {pages} pagine "
            f"(stampa {row.symbol}{print_cost:.2f}): margine sottile.",
            "Meno pagine o prezzo più alto: sotto le 2 unità a copia il libro "
            "non ripaga nemmeno la pubblicità.",
        ))


def _produzione(state: dict, spec: BookSpec, report: BookReport) -> None:
    """Quante volte ha dovuto rifare i conti per arrivare alle pagine giuste."""
    build = state.get("build") or {}
    storico = build.get("storico") or []
    misurate = state.get("words_per_page_measured")
    calibration = state.get("last_calibration") or {}

    report.produzione = {
        "iterazioni": build.get("iterazioni", len(storico)),
        "pagine_obiettivo": spec.target_pages,
        "pagine_reali": build.get("pagine", 0),
        "parole": build.get("parole", 0),
        "parole_per_pagina_misurate": misurate,
        "correzione_budget": calibration.get("correzione"),
        "nell_intervallo": build.get("nell_intervallo"),
    }

    iterations = report.produzione["iterazioni"] or 0
    if iterations >= 3:
        report.rilievi.append(Finding(
            "produzione", "alto",
            f"{iterations} passate di impaginazione per rientrare nelle pagine: "
            "ogni passata riscrive capitoli e ricompra token.",
            "La stima iniziale parole/pagina sbaglia troppo: tarare `planner.py` "
            "sulle misure reali già raccolte.",
        ))

    pages = build.get("pagine", 0)
    if pages and spec.target_pages:
        drift = abs(pages - spec.target_pages) / spec.target_pages
        if drift > 0.08:
            report.rilievi.append(Finding(
                "produzione", "medio",
                f"Pagine finali {pages} contro un obiettivo di {spec.target_pages} "
                f"({drift * 100:.0f}% di scarto).",
            ))


def _qualita(project: BookProject, state: dict, report: BookReport) -> None:
    """Le segnalazioni rimaste sul libro finito, per codice."""
    qa_path = project.build_dir / "qa-report.json"
    per_codice: dict[str, int] = {}
    errori = avvisi = 0
    if qa_path.exists():
        data = json.loads(qa_path.read_text(encoding="utf-8"))
        for entry in data.get("findings", []):
            code = entry.get("code") or "?"
            level = entry.get("level") or "info"
            # Le voci informative dicono che un controllo è passato: non sono
            # difetti e non vanno contate fra le ricorrenze.
            if level == "info":
                continue
            per_codice[code] = per_codice.get(code, 0) + 1
            if level == "errore":
                errori += 1
            else:
                avvisi += 1

    report.qualita = {
        "errori": errori,
        "avvisi": avvisi,
        "per_codice": per_codice,
        "collegio": state.get("review") or {},
    }
    if errori:
        report.rilievi.append(Finding(
            "qualita", "alto",
            f"{errori} errori bloccanti ancora aperti sul libro finito.",
            "Non è pubblicabile così.",
        ))


def _scheda(state: dict, spec: BookSpec, report: BookReport) -> None:
    """La scheda prodotto contro i limiti veri del modulo KDP."""
    meta = state.get("metadata") or {}
    # `book.json` viene prima: quello che sta in `build/metadata.json` è una
    # proposta del modello, e dopo una lavorazione a secco è un segnaposto. Se
    # vince lui, la diagnostica misura il segnaposto e dichiara conforme un
    # titolo che non lo è. Dove `book.json` tace — parole chiave e categorie di
    # un libro mai lavorato — resta valida la scheda prodotta.
    title = spec.title or meta.get("title") or ""
    subtitle = spec.subtitle or meta.get("subtitle") or ""
    keywords = list(spec.keywords or meta.get("keywords") or [])
    categories = list(spec.categories or meta.get("categories") or [])
    #: è questa la stringa che Amazon tronca nei risultati, non il solo titolo
    titolo_esteso = f"{title}: {subtitle}" if subtitle else title
    paragraphs = meta.get("description_paragraphs") or []
    description = "\n\n".join(paragraphs)

    title_words = _words(f"{title} {subtitle}")
    ripetute = [k for k in keywords if _words(k) & title_words]
    deboli = [k for k in keywords if _words(k) <= WEAK_KEYWORDS or not _words(k)]
    doppioni: list[str] = []
    viste: set[frozenset] = set()
    for keyword in keywords:
        parole = frozenset(_words(keyword))
        if parole and parole in viste:
            doppioni.append(keyword)
        viste.add(parole)

    report.scheda = {
        "titolo_caratteri": len(title),
        "titolo_piu_sottotitolo": len(titolo_esteso),
        "parole_chiave_usate": len(keywords),
        "parole_chiave_slot": KEYWORD_SLOTS,
        "caratteri_medi_per_slot": round(
            sum(len(k) for k in keywords) / len(keywords), 1) if keywords else 0,
        "caratteri_sprecati_negli_slot": sum(
            max(KEYWORD_MAX_CHARS - len(k), 0) for k in keywords),
        "parole_chiave_gia_nel_titolo": ripetute,
        "parole_chiave_deboli": deboli,
        "parole_chiave_doppie": doppioni,
        "categorie_usate": len(categories),
        "categorie_slot": CATEGORY_SLOTS,
        "descrizione_caratteri": len(description),
        "descrizione_paragrafi": len(paragraphs),
        "prima_dello_stacco": description[:DESCRIPTION_FOLD_CHARS],
    }

    if len(keywords) < KEYWORD_SLOTS:
        report.rilievi.append(Finding(
            "scheda", "alto",
            f"{len(keywords)} parole chiave su {KEYWORD_SLOTS} slot disponibili: "
            f"{KEYWORD_SLOTS - len(keywords)} slot vuoti che non ti fanno trovare da nessuno.",
            "Riempire tutti e sette gli slot: sono gratis e sono l'unico modo di "
            "comparire su ricerche che il titolo non copre.",
        ))
    if ripetute:
        report.rilievi.append(Finding(
            "scheda", "alto",
            f"{len(ripetute)} parole chiave ripetono parole già nel titolo "
            f"({', '.join(ripetute[:3])}): slot sprecati, il titolo è già indicizzato.",
            "Sostituirle con frasi che il titolo non contiene.",
        ))
    if deboli:
        report.rilievi.append(Finding(
            "scheda", "medio",
            f"Parole chiave troppo generiche per portare traffico: {', '.join(deboli[:3])}.",
        ))
    if doppioni:
        report.rilievi.append(Finding(
            "scheda", "medio",
            f"Parole chiave che si sovrappongono fra loro: {', '.join(doppioni[:3])}.",
        ))
    if len(categories) < CATEGORY_SLOTS:
        report.rilievi.append(Finding(
            "scheda", "alto",
            f"{len(categories)} categorie su {CATEGORY_SLOTS}: ogni categoria è una "
            "classifica in cui si può entrare.",
        ))
    if len(titolo_esteso) > TITLE_TRUNCATION_CHARS:
        report.rilievi.append(Finding(
            "scheda", "medio",
            f"Titolo + sottotitolo di {len(titolo_esteso)} caratteri: oltre i "
            f"{TITLE_TRUNCATION_CHARS} Amazon tronca nei risultati di ricerca, e quello "
            "che si taglia è sempre la seconda metà, cioè la promessa.",
            "Portare nei primi caratteri la frase che il lettore cerca davvero.",
        ))
    if description and len(description) < DESCRIPTION_MAX_CHARS * 0.4:
        report.rilievi.append(Finding(
            "scheda", "medio",
            f"Descrizione di {len(description)} caratteri su {DESCRIPTION_MAX_CHARS} "
            "disponibili: è lo spazio di vendita più grande della scheda.",
        ))
    if not description:
        report.rilievi.append(Finding(
            "scheda", "alto", "Nessuna descrizione nella scheda prodotto.")
        )


def _copertina(state: dict, report: BookReport) -> None:
    cover = state.get("cover") or {}
    verdict = cover.get("verifica") or {}
    report.copertina = {
        "palette": cover.get("theme", ""),
        "illustrazione": cover.get("illustrazione", ""),
        **{k: v for k, v in verdict.items() if k != "problemi"},
        "problemi": verdict.get("problemi", []),
    }
    for problem in verdict.get("problemi", []):
        report.rilievi.append(Finding("copertina", "alto", problem))


def analyse_book(project: BookProject, spec: BookSpec) -> BookReport:
    """Tutte le misure di un libro, senza giudizi e senza chiamate al modello."""
    state = project.load_state()
    pages = (state.get("build") or {}).get("pagine", 0)
    report = BookReport(
        slug=spec.slug, titolo=spec.title, lingua=spec.language,
        genere=spec.genre, categoria=spec.content_type, pagine=pages,
    )
    _economia(spec, state, pages, report)
    _produzione(state, spec, report)
    _qualita(project, state, report)
    _scheda(state, spec, report)
    _copertina(state, report)
    report.rilievi.sort(key=lambda f: {"alto": 0, "medio": 1, "basso": 2}[f.impatto])
    return report


# --------------------------------------------------------------------------
# Misure sul sistema, non sul singolo libro
# --------------------------------------------------------------------------
def _ricorrenze(reports: list[BookReport]) -> list[Finding]:
    """I difetti che tornano in più libri: quelli si correggono nel sistema.

    Un difetto su un libro è un difetto del libro. Lo stesso difetto su tre
    libri è un difetto della pipeline, e correggerlo una volta li sistema tutti.
    """
    conteggio: dict[str, list[str]] = {}
    for report in reports:
        for code in report.qualita.get("per_codice", {}):
            conteggio.setdefault(code, []).append(report.slug)
        for problem in report.copertina.get("problemi", []):
            conteggio.setdefault(f"COPERTINA/{problem[:40]}", []).append(report.slug)

    findings: list[Finding] = []
    for code, slugs in sorted(conteggio.items(), key=lambda kv: -len(kv[1])):
        if len(slugs) >= 2:
            findings.append(Finding(
                "sistema", "alto" if len(slugs) >= 3 else "medio",
                f"«{code}» compare in {len(slugs)} libri su {len(reports)} "
                f"({', '.join(slugs[:4])}): non è un difetto del libro, è del sistema.",
                "Correggere a monte, nella pipeline: si sistemano tutti i libri futuri.",
            ))
    return findings


def _copertura_test(root: Path) -> dict:
    """Quanto codice c'è e quanto test: un rapporto, non una percentuale finta."""
    def righe(paths) -> int:
        return sum(
            len([r for r in p.read_text(encoding="utf-8").splitlines() if r.strip()])
            for p in paths
        )

    code = list((root / "kdpfactory").rglob("*.py"))
    tests = list((root / "tests").glob("*.py"))
    moduli_senza_test: list[str] = []
    testo_test = "\n".join(p.read_text(encoding="utf-8") for p in tests)
    for module in code:
        if module.name == "__init__.py":
            continue
        if module.stem not in testo_test:
            moduli_senza_test.append(str(module.relative_to(root)))
    return {
        "righe_codice": righe(code),
        "righe_test": righe(tests),
        "moduli": len(code),
        "moduli_mai_nominati_nei_test": sorted(moduli_senza_test),
    }


@dataclass
class SystemReport:
    libri: list[BookReport] = field(default_factory=list)
    ricorrenze: list[Finding] = field(default_factory=list)
    codice: dict = field(default_factory=dict)
    totali: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "totali": self.totali,
            "ricorrenze": [f.to_dict() for f in self.ricorrenze],
            "codice": self.codice,
            "libri": [b.to_dict() for b in self.libri],
        }


def analyse(books_dir: Path, root: Path) -> SystemReport:
    """La diagnostica completa: tutti i libri più le misure sul sistema."""
    reports: list[BookReport] = []
    for book_json in sorted(books_dir.glob("*/book.json")):
        spec = BookSpec.load(book_json)
        project = BookProject(book_json.parent)
        reports.append(analyse_book(project, spec))

    system = SystemReport(libri=reports)
    system.ricorrenze = _ricorrenze(reports)
    system.codice = _copertura_test(root)
    costo = sum(b.economia.get("costo_api_usd", 0) for b in reports)
    system.totali = {
        "libri": len(reports),
        "pagine_totali": sum(b.pagine for b in reports),
        "costo_api_totale_usd": round(costo, 2),
        "costo_api_medio_per_libro_usd": round(costo / len(reports), 2) if reports else 0,
        "rilievi_ad_alto_impatto": sum(
            1 for b in reports for f in b.rilievi if f.impatto == "alto"
        ) + sum(1 for f in system.ricorrenze if f.impatto == "alto"),
    }
    return system


# --------------------------------------------------------------------------
# Resa a schermo
# --------------------------------------------------------------------------
SYMBOLS = {"alto": "▲", "medio": "•", "basso": "·"}


def render(system: SystemReport) -> str:
    lines = ["DIAGNOSTICA DEL SISTEMA", "=" * 42, ""]
    t = system.totali
    lines.append(
        f"{t['libri']} libri · {t['pagine_totali']} pagine · "
        f"${t['costo_api_totale_usd']} di API in tutto "
        f"(${t['costo_api_medio_per_libro_usd']} per libro)"
    )
    lines.append(f"{t['rilievi_ad_alto_impatto']} rilievi ad alto impatto")
    lines.append("")

    if system.ricorrenze:
        lines += ["DIFETTI CHE TORNANO IN PIÙ LIBRI", "-" * 42]
        for finding in system.ricorrenze:
            lines.append(f"  {SYMBOLS[finding.impatto]} {finding.fatto}")
            if finding.leva:
                lines.append(f"      → {finding.leva}")
        lines.append("")

    code = system.codice
    lines += [
        "CODICE",
        "-" * 42,
        f"  {code['righe_codice']} righe in {code['moduli']} moduli, "
        f"{code['righe_test']} righe di test "
        f"({code['righe_test'] / max(code['righe_codice'], 1):.2f} test per riga di codice)",
    ]
    if code["moduli_mai_nominati_nei_test"]:
        lines.append(
            f"  moduli mai nominati nei test: "
            f"{', '.join(code['moduli_mai_nominati_nei_test'])}"
        )
    lines.append("")

    for book in system.libri:
        etichetta = "medium-content" if book.categoria == "medium" else "full-content"
        lines += [f"{book.slug.upper()} — {book.titolo}  [{etichetta}]", "-" * 42]
        eco = book.economia
        lines.append(
            f"  {book.pagine} pagine · stampa {eco.get('costo_stampa')} · "
            f"prezzo {eco.get('prezzo_consigliato')} · "
            f"royalty {eco.get('royalty_per_copia')} a copia "
            f"({eco.get('mercato')})"
        )
        scheda = book.scheda
        lines.append(
            f"  scheda: {scheda.get('parole_chiave_usate')}/{KEYWORD_SLOTS} parole chiave · "
            f"{scheda.get('categorie_usate')}/{CATEGORY_SLOTS} categorie · "
            f"descrizione {scheda.get('descrizione_caratteri')}/{DESCRIPTION_MAX_CHARS} caratteri"
        )
        if book.copertina.get("titolo_percentuale_altezza"):
            lines.append(
                f"  copertina: {book.copertina.get('palette')}/"
                f"{book.copertina.get('illustrazione') or 'solo testo'} · "
                f"titolo {book.copertina.get('titolo_percentuale_altezza')}% · "
                f"contrasto {book.copertina.get('contrasto')}:1"
            )
        for finding in book.rilievi:
            lines.append(f"  {SYMBOLS[finding.impatto]} [{finding.area}] {finding.fatto}")
            if finding.leva:
                lines.append(f"      → {finding.leva}")
        lines.append("")

    return "\n".join(lines)

"""I temi che la fabbrica non tratta: salute, diritto, finanza, psicologia.

Decisione dell'autore del 14 ottobre 2026 (`docs/rischi-legali.md`): un libro
su questi temi risponde di quello che consiglia, e un libro scritto con l'IA
non ha la revisione di un professionista che ne risponda. La fabbrica li
rifiuta tutti, prima di spendere un agente: all'acquisizione del concorrente,
nella scheda del libro, nel controllo qualità e nel pacchetto di pubblicazione.

Si guarda dove il tema si dichiara: titolo, sottotitolo, argomento, promessa,
pubblico, categorie, parole chiave. Non il testo dei capitoli, dove una parola
come «doctor» o «budget» può capitare in qualunque libro. Se un libro legittimo
viene fermato per sbaglio, si corregge l'elenco qui, per tutti.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from .models import BookSpec

#: Per ogni famiglia: i rami di categoria (BISAC o Amazon, confrontati a
#: inizio di un livello) e le parole che dichiarano il tema, in inglese e in
#: italiano, cercate come parole intere.
FAMIGLIE: dict[str, dict[str, tuple[str, ...]]] = {
    "salute": {
        "categorie": (
            "MEDICAL", "HEALTH & FITNESS", "Medical Books", "Health, Fitness & Dieting",
            "Nursing", "Medicine", "Salute", "Medicina",
        ),
        "parole": (
            r"medical", r"medicine", r"clinical", r"clinician", r"nurs(e|es|ing)",
            r"nurse practitioners?", r"physicians?", r"doctors?", r"patients?",
            r"diagnos(is|es|e|ing)", r"treatments?", r"diseases?", r"illness(es)?",
            r"symptoms?", r"medications?", r"dosages?", r"prescriptions?",
            r"healthcare", r"health ?care", r"dementia", r"alzheimer'?s", r"diabet(es|ic)",
            r"cancer", r"pregnan(cy|t)", r"weight loss", r"diet(s|ing)?", r"nutrition",
            r"supplements?", r"caregiv(ing|ers?)", r"chronic pain", r"autism", r"adhd",
            r"medic[aoi]", r"medicina", r"salute", r"infermier[ei]", r"pazient[ei]",
            r"diagnosi", r"terapi[ae]", r"malatti[ae]", r"farmac[io]", r"dieta",
            r"dimagr\w*", r"demenza", r"caregiver",
        ),
    },
    "diritto": {
        "categorie": ("LAW", "Law", "Diritto"),
        "parole": (
            r"legal", r"lawyers?", r"attorneys?", r"lawsuits?", r"litigation",
            r"malpractice", r"liability", r"divorce", r"custody", r"immigration",
            r"estate planning", r"wills? and trusts?", r"contracts? law", r"court",
            r"legale", r"avvocat[oi]", r"diritto", r"contenzios[oi]", r"divorzio",
            r"testament[oi]", r"tribunale",
        ),
    },
    "finanza": {
        "categorie": (
            "BUSINESS & ECONOMICS / Personal Finance", "BUSINESS & ECONOMICS / Investments",
            "BUSINESS & ECONOMICS / Taxation", "Personal Finance", "Investing", "Taxation",
            "Finanza",
        ),
        "parole": (
            r"personal finance", r"invest(ing|ment|ments|or|ors)", r"stock market", r"crypto\w*",
            r"trading", r"retirement", r"budget(s|ing)?", r"debts?", r"credit scores?",
            r"tax(es)?", r"mortgages?", r"money management", r"bills?", r"savings",
            r"finanz\w*", r"investiment[oi]", r"borsa", r"criptovalut\w*", r"tasse",
            r"debit[oi]", r"risparmi[oa]?", r"bollette", r"mutu[oi]",
        ),
    },
    "psicologia": {
        "categorie": (
            "PSYCHOLOGY", "SELF-HELP / Anxieties", "SELF-HELP / Depression",
            "SELF-HELP / Mood Disorders", "SELF-HELP / Post-Traumatic Stress Disorder",
            "Psychology & Counseling", "Mental Health", "Psicologia",
        ),
        "parole": (
            r"psycholog\w*", r"mental health", r"anxiety", r"depression", r"trauma",
            r"ptsd", r"bipolar", r"therapy", r"therapists?", r"counsel(l)?ing",
            r"self-harm", r"suicid\w*", r"narcissis\w*", r"panic attacks?",
            r"psicolog\w*", r"salute mentale", r"ansia", r"depressione", r"psicoterap\w*",
        ),
    },
}


def _parole(famiglia: str) -> re.Pattern:
    alternative = "|".join(FAMIGLIE[famiglia]["parole"])
    return re.compile(rf"(?<![\w-])(?:{alternative})(?![\w-])", re.IGNORECASE)


_REGEX = {famiglia: _parole(famiglia) for famiglia in FAMIGLIE}


def _categoria_esclusa(categoria: str, famiglia: str) -> str:
    """Il ramo escluso che la categoria contiene a inizio di un livello, o vuoto."""
    livelli = [livello.strip() for livello in re.split(r"[/>]", categoria) if livello.strip()]
    intera = " / ".join(livelli).lower()
    for ramo in FAMIGLIE[famiglia]["categorie"]:
        ramo_livelli = " / ".join(p.strip() for p in re.split(r"[/>]", ramo)).lower()
        if intera.startswith(ramo_livelli) or any(
            " / ".join(livelli[i:]).lower().startswith(ramo_livelli) for i in range(len(livelli))
        ):
            return ramo
    return ""


def motivi(testi: Iterable[str], categorie: Iterable[str] = ()) -> list[str]:
    """Perché questi testi e categorie toccano un tema escluso; vuota se non lo toccano."""
    trovati: list[str] = []
    testi = [t for t in testi if t]
    categorie = [c for c in categorie if c]
    for famiglia in FAMIGLIE:
        for categoria in categorie:
            ramo = _categoria_esclusa(categoria, famiglia)
            if ramo:
                trovati.append(f"{famiglia}: categoria «{categoria}»")
                break
        for testo in testi:
            trovato = _REGEX[famiglia].search(testo)
            if trovato:
                trovati.append(f"{famiglia}: «{trovato.group(0)}» in «{testo[:80]}»")
                break
    return trovati


def per_libro(spec: BookSpec) -> list[str]:
    """I temi esclusi che la scheda del libro dichiara."""
    if spec.banco_di_prova:
        return []
    return motivi(
        [spec.title, spec.subtitle, spec.topic, spec.promise, spec.audience, *spec.keywords],
        spec.categories,
    )


def per_concorrente(scheda: dict) -> list[str]:
    """I temi esclusi del libro concorrente: titolo, sottotitolo e categorie della sua scheda."""
    categorie = [
        (c.get("nome", "") if isinstance(c, dict) else str(c)) for c in scheda.get("categorie") or []
    ]
    return motivi([str(scheda.get("titolo") or ""), str(scheda.get("sottotitolo") or "")], categorie)


def messaggio(trovati: list[str]) -> str:
    righe = ["Tema escluso dall'autore (salute, diritto, finanza, psicologia: "
             "docs/rischi-legali.md):"]
    righe += [f"  - {t}" for t in trovati]
    righe.append("Il libro non si fa: serve un altro ASIN, di un tema ammesso.")
    return "\n".join(righe)

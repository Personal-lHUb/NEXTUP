"""A che punto è ogni libro, e qual è il prossimo passo: la bussola del giro orario.

La routine oraria riprende la produzione da sola, e a ogni giro deve sapere da
dove ripartire senza ricordarsi niente del giro prima. Lo dicono i file: un
libro in fase 2 ha la scaletta e non tutti i capitoli, uno in fase 7 ha la
scheda e non la copertina. Questo modulo li guarda e dice, per ogni libro, la
fase, il prossimo passo e che cosa lo blocca — una richiesta a Cowork senza
risposta, una decisione dell'autore ancora nel tempo del silenzio-assenso.

Non decide niente e non chiama nessuno: le fasi e i loro cancelli restano quelli
di `docs/linee-guida.md`. Dove un cancello si giudica leggendo un rapporto, il
passo lo dice e lo lascia alla sessione.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import avvio as avvio_module
from . import cowork, decisioni, direzioni, higgsfield
from .models import BookProject

#: I quattro agenti del reparto, nell'ordine, con il file che lasciano in concorrente/.
REPARTO = (
    ("scheda.json", "scheda-concorrente"),
    ("lacune.json", "analista-recensioni"),
    ("piano.json", "posizionamento"),
    ("originalita.json", "originalita"),
)
#: I rapporti del collegio di controllo (fase 4), in manuale/collegio/.
COLLEGIO = ("lettore-cieco", "editor-sviluppo", "fact-checker", "conformita")


CONFIG = Path("config") / "produzione.json"
_SEGUITO = re.compile(r"-\d+(?=\.md$)")


def _nome_base(percorso: str) -> str:
    """Il nome della richiesta senza il numero del seguito.

    `cowork-copertina-2.md` è ancora la richiesta di copertina: il passo che la
    aspettava aspetta anche il suo seguito.
    """
    return _SEGUITO.sub("", Path(percorso).name)


#: Le decisioni che la fase successiva aspetta, per fase.
SERVONO = {
    "1": ("categoria", "titolo", "promessa", "voce", "pseudonimo"),
    "2": ("categoria", "titolo", "promessa", "voce", "pseudonimo"),
    "8": ("prezzo", "copertina"),
}


def configurazione(radice: Path) -> dict:
    percorso = radice / CONFIG
    if not percorso.exists():
        return {"attivi": [], "silenzio_assenso_ore": decisioni.ORE_PREDEFINITE}
    return json.loads(percorso.read_text(encoding="utf-8"))


def attiva(radice: Path, slug: str) -> bool:
    """Mette un libro fra quelli che il giro orario fa avanzare; True se non c'era."""
    dati = configurazione(radice)
    if slug in dati.setdefault("attivi", []):
        return False
    dati["attivi"].append(slug)
    (radice / CONFIG).parent.mkdir(parents=True, exist_ok=True)
    (radice / CONFIG).write_text(json.dumps(dati, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


@dataclass
class Stato:
    slug: str
    fase: str
    passo: str
    blocca: list[str] = field(default_factory=list)    # quello che il passo aspetta: Cowork o l'autore
    in_corso: list[str] = field(default_factory=list)  # richieste e proposte aperte che non lo bloccano
    decidere: list[str] = field(default_factory=list)  # decisioni prese, da applicare ai file

    @property
    def fermo(self) -> bool:
        """Fermo vuol dire che il prossimo passo non è della sessione: non c'è niente da fare."""
        return bool(self.blocca) and not self.decidere

    def to_dict(self) -> dict:
        return {**asdict(self), "fermo": self.fermo}


def _pagina_c_e(project: BookProject) -> bool:
    from . import concorrente

    try:
        return len(concorrente.leggi_pagina(project).split()) >= 40
    except SystemExit:
        return False


def _capitoli(project: BookProject) -> tuple[int, int]:
    """Quanti capitoli prevede la scaletta e quanti ne ha il manoscritto (o manuale/)."""
    outline = json.loads(project.outline_path.read_text(encoding="utf-8"))
    previsti = len(outline.get("chapters") or [])
    scritti = sum(
        1 for n in range(1, previsti + 1)
        if (project.root / "manuscript" / f"{n:02d}.md").exists()
        or (project.root / "manuale" / f"capitolo-{n:02d}.md").exists()
    )
    return previsti, scritti


#: Le varianti di copertina generate dal connettore Higgsfield, con l'indirizzo
#: da cui scaricarle: `copertina <slug> --scarica-generate` le porta in assets/.
GENERATE = "copertina-higgsfield.json"


def generate_senza_file(project: BookProject, direzione: int = 0) -> list[dict]:
    """Le varianti già generate (e pagate) che non sono ancora in assets/.

    Si scaricano, non si rigenerano: rigenerarle ricompra le stesse immagini.
    Con `direzione` solo quelle nate da quella direzione d'arte.
    """
    try:
        voci = json.loads((project.root / "build" / GENERATE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    assets = project.root / "assets"
    return [
        v for v in voci
        if isinstance(v, dict) and v.get("url") and v.get("variante")
        and not list(assets.glob(f"copertina-{v['variante']}.*"))
        and (not direzione or v.get("direzione") == direzione)
    ]


def _passo_direzioni(project: BookProject, slug: str) -> tuple | None:
    """Il passo delle direzioni d'arte, se il libro è ancora lì; `None` se le ha superate.

    Restituisce il testo del passo, le richieste che aspetta e, se c'è, che cosa
    aspetta dall'autore. Superate vuol dire: direzione scelta e varianti finali
    già generate (o in arrivo), cioè il percorso di sempre.
    """
    fase = direzioni.stato(project)
    studio = (direzioni.STUDIO,)
    if fase in ("nessuna", "da-compilare"):
        if not direzioni.risposta_studio(project).exists():
            if not direzioni.studio_path(project).exists():
                return (f"`copertina {slug} --direzioni`: la richiesta dello studio della "
                        "categoria a Cowork e il modello delle tre direzioni", ())
            return ("aspettare lo studio delle copertine della categoria", studio)
        return (f"subagent `copertina` → {direzioni.FILE}: tre direzioni d'arte, poi "
                f"`copertina {slug} --direzioni`", ())
    if fase == "da-correggere":
        return (f"subagent `copertina`: correggere {direzioni.FILE} "
                f"(`copertina {slug} --direzioni` dice che cosa)", ())
    if fase == "senza-bozzetti":
        return (f"`copertina {slug} --bozzetti --genera`: un bozzetto per direzione a bassa "
                "risoluzione (o il connettore Higgsfield coi prompt del sistema)", ())
    if fase == "da-scegliere":
        return ("aspettare la direzione scelta dall'autore", (),
                "autore: scegliere una delle tre direzioni (non passa dal silenzio-assenso)")
    # Scelta: se le varianti finali di questa direzione non ci sono ancora, si generano.
    numero, _ = direzioni.scelta(direzioni.leggi(project))
    if not list((project.root / "assets").glob("copertina-*.*")) and not generate_senza_file(
            project, direzione=numero):
        return (f"`copertina {slug} --genera`: le varianti finali della direzione scelta, alla "
                "risoluzione più alta (o il connettore Higgsfield coi prompt del sistema)", ())
    return None


def stato_libro(project: BookProject, aperte: list[cowork.Richiesta]) -> Stato:
    slug = project.root.name
    mie = [r for r in aperte if r.chiave == slug and r.stato == cowork.APERTA]
    attese = decisioni.in_attesa(project)
    da_applicare = [
        f"applica la decisione «{d['chiave']}»: {d['valore']}" for d in decisioni.da_applicare(project)
    ]

    def richiesta(r: cowork.Richiesta) -> str:
        if r.serve:
            # Cowork non la prende finché l'accesso non c'è: chi la sblocca è l'autore.
            return f"autore: aprire {r.serve} nel browser di Cowork ({Path(r.percorso).name})"
        return f"Cowork, ruolo {r.ruolo or '—'}: {Path(r.percorso).name}"

    def proposta(d: dict) -> str:
        if not d.get("scade_il"):
            return f"autore: {d['chiave']} (aspetta la sua risposta)"
        return f"autore: {d['chiave']} (silenzio-assenso dal {d['scade_il']})"

    def stato(fase: str, passo: str, ruoli: tuple[str, ...] = (), nomi: tuple[str, ...] = (),
              *altro: str) -> Stato:
        """Blocca solo quello che il passo aspetta: i ruoli o le richieste nominate, le sue decisioni."""
        bloccanti = [r for r in mie if r.ruolo in ruoli or _nome_base(r.percorso) in nomi]
        servono = SERVONO.get(fase, ())
        blocca = [richiesta(r) for r in bloccanti] + [proposta(d) for d in attese if d["chiave"] in servono]
        in_corso = [richiesta(r) for r in mie if r not in bloccanti]
        in_corso += [proposta(d) for d in attese if d["chiave"] not in servono]
        return Stato(slug, fase, passo, [*blocca, *altro], in_corso, da_applicare)

    if not project.spec_path.exists():
        # Le domande d'avvio contano solo prima della scheda: i libri nati prima
        # che esistessero hanno già `book.json` e vanno avanti dalla loro fase.
        risposte = avvio_module.leggi(project)
        if risposte is None or risposte.mancanti():
            return stato("A", "domande d'avvio all'autore (`avvio <slug> --json`)", (), (),
                         "autore: domande d'avvio")
        cartella = project.root / "concorrente"
        if not _pagina_c_e(project):
            return stato("0", "aspettare la pagina del concorrente", ("concorrente",), (),
                         *([] if any(r.ruolo == "concorrente" for r in mie)
                           else ["la pagina: né in concorrente/pagina.md né chiesta a Cowork"]))
        for nome, agente in REPARTO:
            if not (cartella / nome).exists():
                # Il posizionamento sceglie le parole chiave dalla tabella di Cowork: la aspetta.
                aspetta = ("cowork-parole-chiave.md",) if agente == "posizionamento" else ()
                return stato("0", f"subagent `{agente}` → concorrente/{nome}", (), aspetta)
        return stato("0", "`concorrente importa <slug>`, poi le proposte all'autore (titolo, promessa, "
                          "categoria, prezzo)")

    if not project.outline_path.exists():
        return stato("1", "scaletta e piano delle figure: `architetto` → `indice` → "
                          "`manuale <slug> scaletta --esamina`")
    previsti, scritti = _capitoli(project)
    if scritti < previsti:
        return stato("2", f"capitolo {scritti + 1} di {previsti}: `ghostwriter`, poi "
                          f"`manuale <slug> capitolo --numero {scritti + 1} --importa`")

    build = project.root / "build"
    interno = build / f"{slug}-interno.pdf"
    if not interno.exists():
        return stato("3", "`build <slug>` e `review <slug> --agents impaginazione`")
    collegio = project.root / "manuale" / "collegio"
    mancano = [a for a in COLLEGIO if not list(collegio.glob(f"{a}*.json"))]
    if mancano:
        return stato("4", "collegio di controllo in parallelo: " + ", ".join(f"`{a}`" for a in mancano))
    if not (build / "kdp-listing.md").exists():
        return stato("5-6", "correzioni chiuse? poi la scheda: `manuale <slug> scheda`, conformità, "
                            "`parole-chiave <slug>`")
    if not (project.root / "assets" / "copertina.jpg").exists():
        varianti = sorted((project.root / "assets").glob("copertina-*.*"))
        if any(d["chiave"] == "copertina" for d in attese):
            return Stato(slug, "7", "aspettare la scelta della variante", [proposta(d) for d in attese
                         if d["chiave"] == "copertina"], [richiesta(r) for r in mie], da_applicare)
        # Le tre direzioni d'arte vengono prima delle varianti: si spende sulla
        # versione finale solo quando l'autore ha scelto che cosa deve essere.
        passo = _passo_direzioni(project, slug)
        if passo is not None:
            testo, aspetta, *altro = passo
            if generate_senza_file(project):
                altro.append(f"{len(generate_senza_file(project))} varianti della direzione "
                             "precedente sulla CDN di Higgsfield: si scaricano coi domini aperti")
            return stato("7", testo, (), aspetta, *altro)
        if varianti:
            return stato("7", f"{len(varianti)} varianti arrivate: `copertina` le misura, proposta "
                              "«copertina» all'autore, poi `copertina <slug> --scegli N`")
        if any(_nome_base(r.percorso) == "cowork-copertina.md" for r in mie):
            return stato("7", "aspettare le varianti di copertina", (), ("cowork-copertina.md",))
        # Generate con Higgsfield ma ferme sulla sua CDN, che la rete del container
        # blocca (e Cowork non le può consegnare). Non si rigenerano: si scaricano
        # quando l'autore apre i domini di Higgsfield, o le carica lui sul ramo.
        if generate_senza_file(project):
            return stato("7", f"`copertina {slug} --scarica-generate`: "
                              f"{len(generate_senza_file(project))} varianti già generate e pagate",
                         (), (), "autore: aprire i domini di Higgsfield nella rete dell'ambiente, "
                                 "o caricare le varianti sul ramo cowork-immagini")
        if higgsfield.attivo(project.root.parent.parent):
            return stato("7", f"`copertina {slug} --genera`: tre varianti con Higgsfield "
                              "(senza accesso: l'autore fa `higgsfield auth login`)")
        return stato("7", "`copertina <slug>`: il brief e la richiesta a Cowork, ruolo immagini")
    qa = build / "qa-report.json"
    if not qa.exists():
        return stato("8", "`build`, `review --agents copertina`, `qa`, `diagnostica`")
    return stato("pronto", "libro pronto: la pubblicazione è dell'autore", (), (), "autore: pubblicazione")


def tutti(books: Path, aperte: list[cowork.Richiesta], attivi: list[str] | None = None) -> list[Stato]:
    """Lo stato dei libri in produzione; con `attivi`, solo quelli (gli altri il giro non li tocca)."""
    stati = []
    for cartella in sorted(p for p in books.iterdir() if p.is_dir()):
        if attivi is not None and cartella.name not in attivi:
            continue
        project = BookProject(cartella)
        if project.spec_path.exists():
            dati = json.loads(project.spec_path.read_text(encoding="utf-8"))
            if dati.get("banco_di_prova"):
                continue
        elif not (cartella / "concorrente").exists():
            continue
        stati.append(stato_libro(project, aperte))
    return stati


def rapporto(stati: list[Stato]) -> str:
    righe = []
    for s in stati:
        segno = "fermo" if s.fermo else "avanti"
        righe.append(f"{s.slug:<20} fase {s.fase:<6} {segno:<6} {s.passo}")
        righe += [f"{'':<35}da applicare: {d}" for d in s.decidere]
        righe += [f"{'':<35}aspetta: {a}" for a in s.blocca]
        righe += [f"{'':<35}in corso: {a}" for a in s.in_corso]
    return "\n".join(righe) + "\n" if righe else "Nessun libro in produzione.\n"

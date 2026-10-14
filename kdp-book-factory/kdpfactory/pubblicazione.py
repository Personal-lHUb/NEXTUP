"""Il pacchetto di pubblicazione: i file che vanno su KDP, in git, con la scheda per caricarli.

`build/` non entra in git: si rigenera. Quando il libro è finito, però, i file
che vanno su KDP devono stare in un posto che resta e che Cowork può leggere,
perché il caricamento lo fa lui dal portatile dell'autore. `pubblicazione`
copia in `books/<slug>/pubblicazione/` l'interno, la copertina del cartaceo, la
copertina dell'ebook (il fronte, in JPG: KDP la vuole a parte), l'EPUB e la
scheda prodotto, e ci scrive:

- `caricamento-kdp.md`, campo per campo, con i valori esatti da mettere nelle
  pagine di KDP, per il cartaceo e per il Kindle;
- `manifest.json`, con i byte, l'impronta SHA-256 e l'indirizzo pubblico di
  ogni file, così chi li scarica vede se sono arrivati interi;
- la richiesta a Cowork (`cowork-kdp-bozza.md`) e il prompt da incollare nella
  sua chat (`prompt-cowork.md`).

Il pacchetto si fa solo a cancello chiuso: `qa` senza errori, la copertina con
l'illustrazione della direzione scelta, le decisioni dell'autore prese. Cowork
salva le bozze e non pubblica mai: il pulsante lo preme l'autore.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from . import decisioni, direzioni, kdpspecs
from .models import BookProject, BookSpec

CARTELLA = "pubblicazione"
MANIFEST = "manifest.json"
SCHEDA = "caricamento-kdp.md"
RICHIESTA = "cowork-kdp-bozza.md"
PROMPT = "prompt-cowork.md"
#: l'altezza della copertina dell'ebook che KDP consiglia; la larghezza segue il formato
KINDLE_ALTEZZA = 2560
#: le decisioni dell'autore senza cui il libro non si carica
DECISIONI = ("prezzo", "copertina", "formato")

CARTA = {
    "white": "Black & white interior with white paper",
    "cream": "Black & white interior with cream paper",
    "color-standard": "Standard color interior with white paper",
    "color-premium": "Premium color interior with white paper",
}
FINITURA = {"matte": "Matte", "glossy": "Glossy"}


def cartella(project: BookProject) -> Path:
    return project.root / CARTELLA


def _qa(project: BookProject) -> dict | None:
    try:
        return json.loads((project.build_dir / "qa-report.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def file_finali(project: BookProject, spec: BookSpec) -> dict[str, Path]:
    """I file del build che vanno su KDP, col nome che hanno nel pacchetto."""
    build = project.build_dir
    return {
        f"{spec.slug}-interno.pdf": build / f"{spec.slug}-interno.pdf",
        f"{spec.slug}-copertina.pdf": build / f"{spec.slug}-copertina.pdf",
        f"{spec.slug}.epub": build / f"{spec.slug}.epub",
        "kdp-listing.md": build / "kdp-listing.md",
        "metadata.json": build / "metadata.json",
    }


def problemi(project: BookProject, spec: BookSpec, stato: dict | None = None) -> list[str]:
    """Perché il pacchetto non si può fare ancora; vuota se si può."""
    stato = project.load_state() if stato is None else stato
    trovati = [f"manca {p.relative_to(project.root)}: rilancia `build`"
               for p in file_finali(project, spec).values() if not p.exists()]
    qa = _qa(project)
    if qa is None:
        trovati.append("manca il rapporto di `qa`: lancialo dopo il build")
    elif not qa.get("ok"):
        trovati.append("`qa` ha errori: il libro non si carica finché non sono corretti")
    copertina = stato.get("cover") or {}
    if direzioni.scelta(direzioni.leggi(project)) and not copertina.get("immagine"):
        trovati.append("la copertina è ancora solo tipografica: manca l'illustrazione della "
                       "direzione scelta (`copertina --scegli N`, poi `build`)")
    for chiave in DECISIONI:
        if not decisioni.valore(project, chiave):
            trovati.append(f"manca la decisione dell'autore sul {chiave}")
    return trovati


def copertina_kindle(cover_pdf: Path, spec: BookSpec, pagine: int, uscita: Path) -> tuple[int, int]:
    """Il fronte della copertina del cartaceo, senza abbondanza, come JPG per l'ebook.

    È la stessa prima del libro stampato, titolo compreso: KDP chiede per il
    Kindle un'immagine sola, RGB, alta 2560 pixel nel formato consigliato.
    """
    import fitz
    from PIL import Image

    larghezza, altezza = kdpspecs.trim_size_in(spec.trim)
    dorso = kdpspecs.spine_width_in(pagine, spec.paper)
    bleed = kdpspecs.BLEED_IN
    pollice = kdpspecs.INCH
    sinistra = (bleed + larghezza + dorso) * pollice
    ritaglio = fitz.Rect(sinistra, bleed * pollice,
                         sinistra + larghezza * pollice, (bleed + altezza) * pollice)
    zoom = KINDLE_ALTEZZA / ritaglio.height
    with fitz.open(cover_pdf) as documento:
        pagina = documento[0]
        if abs(pagina.rect.width / pollice - kdpspecs.cover_size_in(spec.trim, pagine, spec.paper)[0]) > 0.02:
            raise ValueError("la copertina non ha la larghezza del formato: rilancia `build`")
        immagine = pagina.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=ritaglio, alpha=False)
    uscita.parent.mkdir(parents=True, exist_ok=True)
    rgb = Image.frombytes("RGB", (immagine.width, immagine.height), immagine.samples)
    # lo zoom arrotonda i pixel per eccesso: l'altezza si riporta a quella esatta
    if rgb.height != KINDLE_ALTEZZA:
        larghezza_px = round(rgb.width * KINDLE_ALTEZZA / rgb.height)
        rgb = rgb.resize((larghezza_px, KINDLE_ALTEZZA), Image.LANCZOS)
    rgb.save(uscita, "JPEG", quality=92, optimize=True)
    return rgb.size


def _impronta(file: Path) -> str:
    return hashlib.sha256(file.read_bytes()).hexdigest()


def _radice_git(percorso: Path) -> Path:
    for cartella_su in (percorso.resolve(), *percorso.resolve().parents):
        if (cartella_su / ".git").exists():
            return cartella_su
    return percorso.resolve()


def indirizzo_base(project: BookProject, repository: str, ramo: str) -> str:
    """L'indirizzo pubblico della cartella del pacchetto sul ramo di lavoro."""
    relativo = cartella(project).resolve().relative_to(_radice_git(project.root))
    return f"https://raw.githubusercontent.com/{repository}/{ramo}/{relativo.as_posix()}"


def _riga_prezzi(meta: dict) -> str:
    voce = next((p for p in meta.get("prezzi") or [] if p.get("marketplace") == "amazon.com"), None)
    if not voce:
        return ""
    return (f"Costo di stampa stimato dal sistema su amazon.com: {voce['costo_stampa']:.2f} USD; "
            f"royalty stimata {voce['royalty_per_copia']:.2f} USD a copia.")


def scheda_caricamento(spec: BookSpec, meta: dict, pagine: int, file: dict[str, dict]) -> str:
    """I campi di KDP con i valori esatti, cartaceo e Kindle, nell'ordine delle pagine di KDP."""
    larghezza, altezza = kdpspecs.trim_size_in(spec.trim)
    dorso = kdpspecs.spine_width_in(pagine, spec.paper)
    parole = meta.get("keywords") or spec.keywords
    categorie = meta.get("categories") or spec.categories
    kindle = spec.price_ebook > 0
    riga = []
    riga += [
        f"# Caricamento su KDP — {spec.title}",
        "",
        "Scritto da `python3 -m kdpfactory pubblicazione`. I valori si copiano così",
        "come sono; quelli in inglese sono le etichette e le scelte delle pagine di KDP.",
        "**Si salva come bozza e non si pubblica**: «Publish» lo preme l'autore.",
        "",
        "## I file",
        "",
        "| file | byte | SHA-256 |",
        "|---|---|---|",
    ]
    riga += [f"| [{nome}]({dati['url']}) | {dati['byte']} | `{dati['sha256'][:16]}…` |"
             for nome, dati in file.items()]
    riga += [
        "",
        "## Cartaceo (Paperback)",
        "",
        "### 1. Paperback Details",
        "",
        "- Language: English" if spec.language == "en" else f"- Language: {spec.language}",
        f"- Book Title: {spec.title}",
        f"- Subtitle: {spec.subtitle}",
        "- Series: nessuna · Edition Number: vuoto",
        f"- Author: {spec.author} (pseudonimo; nessun contributor)",
        "- Description: il testo qui sotto, con grassetto ed elenco fatti coi pulsanti",
        "  dell'editor di KDP (non si incollano i tag HTML).",
        "",
        "```html",
        meta.get("description_html", "").strip(),
        "```",
        "",
        "- Publishing Rights: «I own the copyright and I hold necessary publishing rights»",
        "- Sexually explicit images or title: No · Reading age: vuoto",
        "- Primary marketplace: Amazon.com",
        "- Categories (fino a tre, dal selettore di KDP: il ramo più vicino a queste;",
        "  si riporta il percorso scelto):",
    ]
    riga += [f"  {n}. {c}" for n, c in enumerate(categorie, start=1)]
    riga += ["- Keywords:"]
    riga += [f"  {n}. {k}" for n, k in enumerate(parole, start=1)]
    riga += [
        "- Release date: «Release my book for sale now» (resta bozza: non si pubblica).",
        "",
        "### 2. Paperback Content",
        "",
        "- Print ISBN: «Get a free KDP ISBN»" if not spec.isbn else f"- Print ISBN: {spec.isbn}",
        "- Publication Date: vuoto",
        f"- Ink and Paper Type: {CARTA.get(spec.paper, spec.paper)}",
        f"- Trim Size: {larghezza:g} x {altezza:g} in",
        "- Bleed Settings: No Bleed",
        f"- Paperback cover finish: {FINITURA.get(spec.cover_finish, spec.cover_finish)}",
        "- Reading direction: Left to right",
        f"- Manuscript: `{spec.slug}-interno.pdf` ({pagine} pagine, {larghezza:g} x {altezza:g} in)",
        f"- Book Cover: «Upload a cover you already have (print-ready PDF only)», "
        f"`{spec.slug}-copertina.pdf` (dorso {dorso:.3f} in; l'area del codice a barre è libera)",
        "- AI-Generated Content: Yes. Texts: tutto il libro, generato con Claude (Anthropic);",
        "  il livello di revisione umana lo conferma l'autore. Images: l'illustrazione di",
        "  copertina, generata con GPT Image 2.5 su Higgsfield. Translations: None.",
        "- Launch Previewer → controllare ogni avviso → «Approve» solo senza errori.",
        "",
        "### 3. Paperback Rights & Pricing",
        "",
        "- Territories: «All territories (worldwide rights)»",
        "- Primary marketplace: Amazon.com",
        f"- List price: {spec.price_eur:.2f} USD; gli altri mercati in base al prezzo in USD",
        "- Expanded Distribution: non selezionata (la decide l'autore)",
        "- Proof copies e author copies: non si ordinano",
    ]
    prezzi = _riga_prezzi(meta)
    if prezzi:
        riga += [f"- {prezzi} Si confronta con quello che mostra KDP."]
    riga += ["- Alla fine: **«Save as Draft»**. Mai «Publish Your Paperback Book».", ""]
    if kindle:
        riga += [
            "## Kindle eBook",
            "",
            "Si crea dalla scheda del cartaceo nel Bookshelf («+ Create eBook» / «Create",
            "Kindle eBook»), così i dati passano e le due edizioni restano collegate.",
            "",
            "### 1. Kindle eBook Details",
            "",
            "- Gli stessi valori del cartaceo: titolo, sottotitolo, autore, descrizione,",
            "  diritti, categorie, parole chiave. Si controlla che siano passati uguali.",
            "",
            "### 2. Kindle eBook Content",
            "",
            "- Digital Rights Management: Yes (proposta della fabbrica: dopo la",
            "  pubblicazione non si cambia, la conferma l'autore)",
            f"- Manuscript: `{spec.slug}.epub`",
            f"- Kindle eBook Cover: «Upload a cover you already have», `{spec.slug}-copertina-kindle.jpg`",
            "- AI-Generated Content: le stesse risposte del cartaceo.",
            "- Kindle eBook ISBN: vuoto (facoltativo)",
            "- Launch Previewer: controllare indice, riquadri delle note, avvisi.",
            "",
            "### 3. Kindle eBook Pricing",
            "",
            "- KDP Select: non iscritto (l'esclusiva la decide l'autore)",
            "- Territories: «All territories (worldwide rights)»",
            "- Primary marketplace: Amazon.com",
            f"- Royalty: 70% · List price: {spec.price_ebook:.2f} USD;",
            "  gli altri mercati in base al prezzo in USD",
            "- Book Lending: attivo (lo chiede la royalty al 70%)",
            "- Alla fine: **«Save as Draft»**. Mai «Publish Your Kindle eBook».",
            "",
        ]
    riga += [
        "## Dopo, solo l'autore",
        "",
        "- Rilegge le bozze, l'anteprima e le risposte sui contenuti generati con l'IA.",
        "- Sceglie Expanded Distribution, KDP Select e il DRM, se vuole cambiarli.",
        "- Preme «Publish». La biografia dell'autore va in Author Central, non qui.",
        "",
    ]
    return "\n".join(riga)


def richiesta_cowork(spec: BookSpec, base: str, risposta: str, kindle: bool) -> str:
    """La richiesta per il ruolo `regole-kdp`: la bozza su KDP, senza pubblicare."""
    edizioni = "il cartaceo e il Kindle" if kindle else "il cartaceo"
    quando = f"{datetime.now(timezone.utc):%Y-%m-%d}"
    kindle_passo = (
        "4. Dalla scheda del cartaceo crea il Kindle, compila le tre pagine come dice la\n"
        "   scheda, con EPUB e copertina JPG allegati dall'autore, apri l'anteprima,\n"
        "   «Save as Draft»." if kindle else "4. Il Kindle non c'è: niente da fare."
    )
    return f"""# Bozza su KDP — {spec.title}

Ruolo: regole-kdp
Serve: l'accesso a KDP (kdp.amazon.com) aperto nel browser del portatile
Bozza KDP: autorizzata dall'autore il {quando} per questo libro solo, senza pubblicare

La risposta comincia con questa riga:

    Cowork · risposta · {risposta}

L'autore ti chiede di preparare su KDP {edizioni} di questo libro e di
**fermarti alle bozze**. È l'unica eccezione alla regola «su KDP si legge e
basta» (LEGGIMI, «Bozze su KDP autorizzate»): vale per questa richiesta e per
nessun'altra.

## Che cosa fai

0. **Prima di tutto, il browser.** Apri https://kdp.amazon.com/bookshelf nel
   Chrome dell'autore. Se non vedi il Bookshelf (pagina di accesso, codice di
   verifica, browser che non risponde, estensione non collegata), fermati
   subito e scrivi all'autore che cosa vedi, alla lettera: l'accesso lo apre
   lui. Non cercare un'altra strada.
1. Leggi la scheda di caricamento, con WebFetch:
   {base}/{SCHEDA}
   e il manifest: {base}/{MANIFEST}
   Se un indirizzo risponde 404, il pacchetto non è ancora pronto: fermati e
   dillo all'autore.
2. I file **li allega l'autore**: quando arrivi a un campo di caricamento,
   gli scrivi quale file trascinare (nome del manifest; li trova ai link della
   scheda) e aspetti che ti dica che è caricato. Tu non scegli file dal disco.
3. Nel Bookshelf crea il titolo del cartaceo e compila le tre pagine come dice
   la scheda, campo per campo, con i file allegati dall'autore. Apri
   l'anteprima di KDP e leggi ogni avviso. A ogni pagina premi «Save as Draft».
   Dopo ogni pagina salvata scrivi all'autore una riga: che cosa è fatto.
{kindle_passo}
5. Se un passo non va (un campo che non si trova, un clic che non risponde,
   un errore di KDP), salva la bozza com'è, fermati e scrivi il passo, il campo
   e il messaggio esatto: si riprende da lì, non dall'inizio.

## Che cosa non fai

- Non premi mai «Publish Your Paperback Book», «Publish Your Kindle eBook» né
  un altro pulsante che pubblica o mette in vendita.
- Non ordini copie di prova o copie autore, non iscrivi a KDP Select, non
  attivi Expanded Distribution, non tocchi account, pagamenti, tasse.
- Non cambi i testi: se un campo non accetta un valore della scheda (troppo
  lungo, carattere rifiutato, categoria che non c'è), lasci il campo com'è e lo
  scrivi nella risposta.

## Che cosa rispondi

Per ogni pagina compilata: i valori messi, quelli che KDP ha rifiutato o
cambiato, con il messaggio esatto. In più:

- l'ISBN che KDP ha assegnato al cartaceo;
- le tre categorie scelte nel selettore, col percorso completo;
- il costo di stampa e la royalty che KDP mostra per amazon.com;
- gli avvisi dell'anteprima, pagina per pagina, copiati alla lettera;
- lo stato finale di ogni edizione nel Bookshelf («Draft», «In review», …).

Consegna: le routine sono spente per scelta dell'autore. Non lanciare
`fire_trigger`: scrivi la risposta intera nell'ultimo messaggio, con la riga
«Cowork · risposta · …» qui sopra come prima riga, e l'autore la porta alla
fabbrica.
"""


def prompt_cowork(spec: BookSpec, base: str, leggimi: str) -> str:
    """Il messaggio da incollare in una chat di Cowork sul portatile."""
    return f"""Ruolo: regole-kdp. Prima di tutto leggi le regole del canale, con WebFetch:
{leggimi}

Poi leggi questa richiesta, con WebFetch, ed eseguila punto per punto:
{base}/{RICHIESTA}

È la bozza su KDP di «{spec.title}» che l'autore ha autorizzato: compila,
salva come bozza, **non pubblicare**. Prima apri il Bookshelf di KDP nel mio
Chrome: se non lo vedi, fermati e dimmi che cosa vedi. I file li allego io:
quando arrivi a un campo di caricamento, dimmi quale file e aspetta. Dopo ogni
pagina salvata scrivimi una riga. Alla fine scrivi qui la risposta intera,
senza lanciare routine.
"""


def prepara(project: BookProject, spec: BookSpec, repository: str, ramo: str,
            leggimi: str, stato: dict | None = None) -> dict:
    """Copia i file finali nel pacchetto e scrive scheda, manifest, richiesta e prompt."""
    stato = project.load_state() if stato is None else stato
    ostacoli = problemi(project, spec, stato)
    if ostacoli:
        raise ValueError("; ".join(ostacoli))
    pagine = int((stato.get("build") or {}).get("pagine") or 0)
    meta = json.loads((project.build_dir / "metadata.json").read_text(encoding="utf-8"))
    uscita = cartella(project)
    uscita.mkdir(parents=True, exist_ok=True)
    for nome, sorgente in file_finali(project, spec).items():
        shutil.copy2(sorgente, uscita / nome)
    kindle = spec.price_ebook > 0
    nomi = list(file_finali(project, spec))
    if kindle:
        nome = f"{spec.slug}-copertina-kindle.jpg"
        copertina_kindle(project.build_dir / f"{spec.slug}-copertina.pdf", spec, pagine, uscita / nome)
        nomi.insert(2, nome)
    elif (uscita / f"{spec.slug}-copertina-kindle.jpg").exists():
        (uscita / f"{spec.slug}-copertina-kindle.jpg").unlink()
    base = indirizzo_base(project, repository, ramo)
    file = {
        nome: {"byte": (uscita / nome).stat().st_size, "sha256": _impronta(uscita / nome),
               "url": f"{base}/{nome}"}
        for nome in nomi
    }
    manifest = {
        "libro": spec.slug,
        "titolo": spec.title,
        "pronto": True,
        "scritto_il": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pagine": pagine,
        "formato": spec.trim,
        "carta": spec.paper,
        "dorso_in": round(kdpspecs.spine_width_in(pagine, spec.paper), 4),
        "prezzo_cartaceo": spec.price_eur,
        "prezzo_kindle": spec.price_ebook or None,
        "decisioni": {chiave: decisioni.valore(project, chiave) for chiave in DECISIONI},
        "file": file,
    }
    (uscita / MANIFEST).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                                   encoding="utf-8")
    (uscita / SCHEDA).write_text(scheda_caricamento(spec, meta, pagine, file), encoding="utf-8")
    radice_repo = _radice_git(project.root)
    risposta = (uscita / RICHIESTA.replace(".md", "-risposta.md")).resolve().relative_to(radice_repo)
    (uscita / RICHIESTA).write_text(
        richiesta_cowork(spec, base, risposta.as_posix(), kindle), encoding="utf-8")
    (uscita / PROMPT).write_text(prompt_cowork(spec, base, leggimi), encoding="utf-8")
    return manifest

"""Il canale con Cowork: le richieste di ricerca web e le loro risposte, su GitHub.

Il container della fabbrica non raggiunge Amazon né KDP. Quello che serve da lì
lo fa una sessione Cowork sul computer dell'autore. Lo scambio passa dal
repository su GitHub, sul ramo del canale (`config/cowork.json`), con due nomi
fissi nella stessa cartella: `cowork-<argomento>.md` è la richiesta,
`cowork-<argomento>-risposta.md` la risposta. La fabbrica fa commit e push delle
richieste, Cowork fa il commit delle risposte sullo stesso ramo.

Questo modulo non va in rete. Legge i file e chiede a git due cose: com'è la
richiesta sul ramo remoto, così si vede se è stata inviata, e quando è stato
fatto l'ultimo commit della richiesta e della risposta, così si vede se la
risposta è superata. Le domande a git passano da due funzioni: nei test si
danno finte.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

PREFISSO = "cowork-"
SUFFISSO_RISPOSTA = "-risposta"
SISTEMA = "sistema"
#: riga che la fabbrica aggiunge alla richiesta quando ne ha applicato la risposta
APPLICATA = "Stato: applicata"
CONFIG = Path("config") / "cowork.json"
#: cartelle dove una richiesta non è mai quella vera: copie di sicurezza e impaginati
ESCLUSE = frozenset({"backup", "build", "__pycache__", ".git"})

#: la riga che dice quale ruolo di Cowork prende la richiesta, sotto il titolo
RUOLO = "Ruolo:"
_RUOLO = re.compile(r"^Ruolo:\s*([a-z][a-z-]*)\s*$", re.M)
#: la riga che dice quale accesso dell'autore serve prima di cominciare: finché
#: non è aperto, Cowork non risponde e la richiesta aspetta l'autore, non Cowork
SERVE = "Serve:"
_SERVE = re.compile(r"^Serve:\s*(.+?)\s*$", re.M)

APERTA, ARRIVATA, SUPERATA, CHIUSA = "aperta", "risposta arrivata", "risposta superata", "applicata"
DA_INVIARE, INVIATA, NON_CONTROLLATA = "da inviare", "inviata", "non controllata"

#: com'è un file sul ramo remoto (None se lì non c'è), dato il percorso dalla radice della fabbrica
Remoto = Callable[[str], "str | None"]
#: quando è stato fatto l'ultimo commit di un file (None se non ne ha), in secondi
UltimoCommit = Callable[[str], "int | None"]


@dataclass(frozen=True)
class Richiesta:
    percorso: str         # relativo alla radice della fabbrica
    chiave: str           # slug del libro, o «sistema» per le regole comuni
    argomento: str
    risposta: str         # percorso relativo della risposta
    stato: str            # aperta | risposta arrivata | risposta superata | applicata
    invio: str            # da inviare | inviata | non controllata
    ruolo: str = ""       # il ruolo di Cowork che la prende; vuoto se la richiesta non lo dice
    serve: str = ""       # l'accesso che l'autore deve aprire prima; vuoto se non serve

    def to_dict(self) -> dict:
        return asdict(self)


#: L'indice delle richieste aperte (`corriere.INDICE`): si chiama come una richiesta, non lo è.
INDICE = "config/cowork-aperte.md"


def _e_richiesta(percorso: Path) -> bool:
    return (
        percorso.name.startswith(PREFISSO)
        and percorso.suffix == ".md"
        and not percorso.stem.endswith(SUFFISSO_RISPOSTA)
    )


def _chiave(relativo: Path) -> str:
    parti = relativo.parts
    return parti[1] if len(parti) > 2 and parti[0] == "books" else SISTEMA


def richieste(
    radice: Path,
    remoto: Remoto | None = None,
    ultimo_commit: UltimoCommit | None = None,
) -> list[Richiesta]:
    """Tutte le richieste a Cowork sotto la radice della fabbrica, in ordine.

    Senza `remoto` l'invio resta «non controllata»; senza `ultimo_commit` una
    risposta presente vale sempre come arrivata.
    """
    trovate: list[Richiesta] = []
    for percorso in sorted(radice.rglob(f"{PREFISSO}*.md")):
        relativo = percorso.relative_to(radice)
        if (ESCLUSE.intersection(relativo.parts[:-1]) or not _e_richiesta(percorso)
                or relativo.as_posix() == INDICE):
            continue
        testo = percorso.read_text(encoding="utf-8")
        risposta = percorso.with_name(percorso.stem + SUFFISSO_RISPOSTA + percorso.suffix)
        rel, rel_risposta = relativo.as_posix(), risposta.relative_to(radice).as_posix()

        if remoto is None:
            invio = NON_CONTROLLATA
        else:
            # Inviata vuol dire che sul ramo del canale c'è questa stessa versione:
            # una correzione fatta qui e non pubblicata, Cowork non la vede.
            invio = INVIATA if remoto(rel) == testo else DA_INVIARE

        if APPLICATA in testo:
            stato = CHIUSA
        elif risposta.exists():
            stato = ARRIVATA
            if ultimo_commit is not None:
                t_richiesta, t_risposta = ultimo_commit(rel), ultimo_commit(rel_risposta)
                # La richiesta corretta dopo la risposta: la risposta è alla domanda vecchia.
                if t_richiesta and t_risposta and t_richiesta > t_risposta:
                    stato = SUPERATA
        else:
            stato = APERTA

        trovate.append(
            Richiesta(
                percorso=rel,
                chiave=_chiave(relativo),
                argomento=percorso.stem[len(PREFISSO):],
                risposta=rel_risposta,
                stato=stato,
                invio=invio,
                ruolo=ruolo_di(testo),
                serve=serve_di(testo),
            )
        )
    return trovate


def ruolo_di(testo: str) -> str:
    """Il ruolo dichiarato dalla richiesta, nella riga `Ruolo: …`; vuoto se manca."""
    trovato = _RUOLO.search(testo)
    return trovato.group(1) if trovato else ""


def serve_di(testo: str) -> str:
    """L'accesso che la richiesta chiede aperto prima di cominciare, nella riga `Serve: …`."""
    trovato = _SERVE.search(testo)
    return trovato.group(1) if trovato else ""


def ruoli(canale: dict) -> dict[str, dict]:
    """I ruoli di Cowork, ciascuno con la sua chat e la sua attività pianificata."""
    return canale.get("ruoli") or {}


def ramo_consegna(canale: dict | None) -> str:
    """Il ramo dove Cowork consegna risposte e immagini, se il canale è tutto su GitHub."""
    if canale and canale.get("canale") == "github":
        return canale.get("ramo_consegna", "")
    return ""


def corriere(canale: dict) -> tuple[str, str]:
    """La cartella Drive del corriere: nome e id (vuoti se il canale non la usa)."""
    dati = canale.get("corriere") or {}
    return dati.get("cartella", "NEXTUP — corriere Cowork"), dati.get("cartella_id", "")


def intestazione(
    titolo: str, risposta: str, ruolo: str, canale: dict, cartella: str = "", serve: str = ""
) -> str:
    """La testa uguale per ogni richiesta: ruolo, regole, dove va la risposta.

    La riga `Ruolo:` è quella che l'attività di ciascun ruolo cerca: una
    richiesta senza ruolo non la prende nessuno. `cartella` è dove sta la
    richiesta nel repository (per esempio `books/x/concorrente`): sul corriere
    la risposta si chiama come il suo percorso, con `__` al posto di `/`.

    `serve` è l'accesso che l'autore deve aprire nel browser di Cowork perché la
    richiesta si possa fare (per esempio «l'accesso a KDP»). Con la riga `Serve:`
    Cowork, se l'accesso non c'è, non risponde e riprova al giro dopo: senza, una
    richiesta bloccata dall'accesso tornerebbe parziale a ogni giro.
    """
    regole = (
        "Per ogni punto: il fatto visto sulla pagina, l'URL, la data e l'ora.\n"
        "Se una pagina chiede un captcha o l'accesso e non si riesce ad andare avanti,\n"
        "scrivilo invece di stimare: l'accesso non lo fai tu.\n"
    )
    if serve:
        regole += (
            f"Prima di cominciare controlla che ci sia {serve}. Se manca, non\n"
            "scrivere nessuna risposta: la richiesta resta aperta e la riprendi al giro dopo.\n"
        )
    righe = f"{RUOLO} {ruolo}\n" + (f"{SERVE} {serve}\n" if serve else "")
    if canale.get("canale") == "drive":
        nome, _ = corriere(canale)
        percorso = f"{cartella.strip('/')}/{risposta}" if cartella else risposta
        return (
            f"# {titolo}\n\n"
            f"{righe}\n"
            "Richiesta della fabbrica per Cowork, con le regole del LEGGIMI\n"
            "(`config__leggimi-cowork.md`, nella stessa cartella).\n"
            f"Scrivi la risposta come file nuovo nella cartella Drive «{nome}»,\n"
            f"con il nome `{percorso.replace('/', '__')}` e la stessa numerazione.\n"
            + regole
        )
    ramo = canale.get("ramo", "claude/dreamy-archimedes-hf8w45")
    leggimi = canale.get("leggimi", "kdp-book-factory/config/leggimi-cowork.md")
    consegna = canale.get("ramo_consegna", "")
    if consegna:
        # Il canale su GitHub: le richieste stanno sul ramo della fabbrica, Cowork
        # consegna risposte e immagini sul suo ramo, e la fabbrica le prende con git.
        percorso = f"{CARTELLA_FABBRICA}/{cartella.strip('/')}/{risposta}" if cartella else risposta
        repository = canale.get("repository", "Personal-lHUb/NEXTUP")
        return (
            f"# {titolo}\n\n"
            f"{righe}\n"
            f"Richiesta della fabbrica per Cowork, con le regole di `{leggimi}`\n"
            f"(ramo `{ramo}` del repository `{repository}`).\n"
            f"Scrivi la risposta come file nuovo `{percorso}`\n"
            f"sul ramo `{consegna}`, con la stessa numerazione, poi fai il push.\n"
            + regole
        )
    return (
        f"# {titolo}\n\n"
        f"{righe}\n"
        f"Richiesta della fabbrica per Cowork, con le regole di\n`{leggimi}`.\n"
        f"La risposta va in `{risposta}`, accanto a questo file,\n"
        f"sul ramo `{ramo}`, con la stessa numerazione.\n"
        + regole
    )


def configurazione(radice: Path) -> dict:
    """Il canale (`config/cowork.json`): repository, ramo, LEGGIMI per Cowork."""
    percorso = radice / CONFIG
    if not percorso.exists():
        return {}
    return json.loads(percorso.read_text(encoding="utf-8"))


class Git:
    """Le due domande che il canale fa a git, sul repository che contiene la fabbrica."""

    def __init__(self, radice: Path, ramo: str, remote: str = "origin"):
        self.radice = radice.resolve()
        self.ramo = ramo
        self.remote = remote
        cima = self._git("rev-parse", "--show-toplevel", cwd=self.radice)
        self.cima = Path(cima.strip()) if cima else self.radice

    def _git(self, *argomenti: str, cwd: Path | None = None) -> str | None:
        risultato = subprocess.run(
            ["git", *argomenti], cwd=cwd or self.cima, capture_output=True, text=True
        )
        return risultato.stdout if risultato.returncode == 0 else None

    def _dal_repo(self, relativo: str) -> str:
        return (self.radice / relativo).relative_to(self.cima).as_posix()

    def remoto(self, relativo: str) -> str | None:
        return self._git("show", f"{self.remote}/{self.ramo}:{self._dal_repo(relativo)}")

    def ultimo_commit(self, relativo: str) -> int | None:
        uscita = self._git("log", "-1", "--format=%ct", "--", self._dal_repo(relativo))
        return int(uscita) if uscita and uscita.strip() else None

    def percorso_repo(self, relativo: str) -> str:
        return self._dal_repo(relativo)


def avviso(
    elenco: list[Richiesta],
    canale: dict,
    dal_repo: Callable[[str], str] = str,
    ruolo: str = "",
) -> str:
    """Il messaggio che dice a Cowork che sul ramo del canale c'è lavoro nuovo.

    Elenca solo le richieste aperte: quelle con la risposta già scritta non si
    rifanno, e un elenco che le ripete tutte a ogni avviso insegna a ignorarlo.
    Con `ruolo`, solo quelle di quel ruolo: è il messaggio per la sua chat.
    """
    repo = canale.get("repository", "Personal-lHUb/NEXTUP")
    ramo = canale.get("ramo", "claude/dreamy-archimedes-hf8w45")
    leggimi = canale.get("leggimi", "kdp-book-factory/config/leggimi-cowork.md")
    drive = canale.get("canale") == "drive"
    if drive:
        # Sul corriere i file si chiamano come il loro percorso, con «__» al posto di «/».
        cartella, _ = corriere(canale)
        leggimi = "config__leggimi-cowork.md, nella stessa cartella,"

        def dal_repo(relativo: str) -> str:
            return relativo.replace("/", "__")
    aperte = [r for r in elenco if r.stato == APERTA and (not ruolo or r.ruolo == ruolo)]
    per = f" per il ruolo «{ruolo}»" if ruolo else ""
    dove = (
        f"Nella cartella Google Drive «{cartella}»" if drive
        else f"Sul repository GitHub {repo}, ramo {ramo},"
    )
    if not aperte:
        return f"{dove} non ci sono richieste aperte{per}.\n"
    righe = [
        f"{dove} ci sono richieste nuove della fabbrica di libri{per}, da elaborare.",
        "",
        f"Prima leggi per intero {leggimi}: sono le regole del canale"
        + (f", e la sezione del ruolo «{ruolo}» vale per te." if ruolo else "."),
        "",
    ]
    if ruolo:
        righe += [
            f"- `{dal_repo(r.percorso)}` → rispondi in `{dal_repo(r.risposta)}`" for r in aperte
        ]
    else:
        # Un avviso per tutte le richieste va in una chat che non ha un ruolo
        # suo: deve sapere che le fa tutte, ciascuna con le regole del suo ruolo,
        # altrimenti con il LEGGIMI a ruoli non ne prende nessuna.
        righe += [
            "In questa chat fai le richieste di tutti i ruoli. Ognuna dice il suo nella riga "
            "«Ruolo: …» sotto il titolo: per ciascuna segui la sezione di quel ruolo nel LEGGIMI.",
        ]
        for nome in dict.fromkeys(r.ruolo for r in aperte):
            righe += ["", f"Ruolo «{nome}»:" if nome else "Senza ruolo:"]
            righe += [
                f"- `{dal_repo(r.percorso)}` → rispondi in `{dal_repo(r.risposta)}`"
                for r in aperte if r.ruolo == nome
            ]
    if drive:
        righe += [
            "",
            "Per ciascuna: leggila per intero ed esegui quello che chiede. Scrivi la risposta "
            "come file nuovo nella stessa cartella, con il nome indicato, e la prima riga "
            "«Esito: completa» oppure «Esito: parziale — punti …: <motivo>». Non modificare, "
            "rinominare o cancellare altri file: al repository li porta la fabbrica.",
        ]
    elif ramo_consegna(canale):
        consegna = ramo_consegna(canale)
        righe += [
            "",
            f"Leggi l'indice `{CARTELLA_FABBRICA}/config/cowork-aperte.md` e le richieste dal ramo "
            f"{ramo} (git fetch prima di cominciare).",
            "",
            "Per ciascuna: leggila per intero ed esegui quello che chiede. Scrivi la risposta "
            f"come file nuovo al percorso indicato, sul ramo {consegna}, con la prima riga "
            "«Esito: completa» oppure «Esito: parziale — punti …: <motivo>». Commit e push "
            f"del solo ramo {consegna}, mai --force; nessun altro file, nessuna pull request.",
        ]
    else:
        righe += [
            "",
            "Se lavori sulla copia locale di GitHub Desktop, prima di cominciare aggiornala dal "
            "ramo remoto con Fetch e Pull: su una copia vecchia queste richieste non ci sono.",
            "",
            "Per ciascuna: leggila per intero ed esegui quello che chiede. Scrivi la "
            "risposta nel file indicato e fanne il commit sullo stesso ramo, con la "
            "prima riga «Esito: completa» oppure «Esito: parziale — punti …: <motivo>». "
            "Non modificare altri file.",
        ]
    righe += [
        "",
        "Regole valide per tutte:",
        "- per ogni punto, il fatto che hai visto sulla pagina, non una stima, con "
        "l'URL e la data e l'ora della verifica;",
        "- se una pagina chiede un captcha o l'accesso e non riesci ad andare avanti, "
        "scrivilo invece di stimare;",
        "- su KDP leggi e basta: non creare titoli, non salvare bozze, non pubblicare;",
        "- in Helium 10, Publisher Rocket e ChatGPT usa solo l'accesso già aperto nel browser: non "
        "inserire credenziali, non comprare, non cambiare niente;",
        "- nessuna password, codice o cookie nei file.",
        "",
        *([] if drive or ramo_consegna(canale) else [
            "Alla fine fai il push delle risposte sul ramo. Se non puoi farlo tu, dimmelo: lo "
            "faccio io da GitHub Desktop. Finché non c'è il push, la fabbrica non le vede.",
            "",
        ]),
        *([
            f"Alla fine, se hai consegnato qualcosa, lancia la routine della fabbrica "
            f"(fire_trigger {canale['routine_fabbrica']}): la risposta si applica subito.",
            "",
        ] if ramo_consegna(canale) and canale.get("routine_fabbrica") else []),
        "Quando hai finito, dimmi quali risposte hai scritto e quali punti sono rimasti "
        "senza risposta.",
    ]
    return "\n".join(righe) + "\n"


def rapporto(elenco: list[Richiesta], noti: frozenset[str] | set[str] = frozenset()) -> str:
    """Lo stato del canale, una riga per richiesta, con il ruolo che la prende."""
    if not elenco:
        return "Nessuna richiesta a Cowork.\n"
    # Una richiesta applicata non va più da nessuna parte: l'invio conta solo per le altre.
    righe = [
        f"  {r.stato:<17} {'—' if r.stato == CHIUSA else r.invio:<15} {r.ruolo or '—':<14} {r.percorso}"
        for r in elenco
    ]
    conteggio = {s: sum(r.stato == s for r in elenco) for s in (APERTA, ARRIVATA, SUPERATA, CHIUSA)}
    righe.append(
        f"\n{conteggio[APERTA]} aperte · {conteggio[ARRIVATA]} con risposta da applicare · "
        f"{conteggio[SUPERATA]} con risposta superata · {conteggio[CHIUSA]} applicate"
    )
    da_inviare = [r.percorso for r in elenco if r.invio == DA_INVIARE and r.stato != CHIUSA]
    if da_inviare:
        righe.append("Da inviare (push sul ramo della fabbrica; sul canale Drive, `cowork corriere`): "
                     + ", ".join(da_inviare))
    # Ogni attività di Cowork prende solo le richieste del suo ruolo: una
    # richiesta aperta senza ruolo, o con un ruolo che non esiste, resta lì.
    orfane = [
        r.percorso for r in elenco
        if r.stato == APERTA and (not r.ruolo or (noti and r.ruolo not in noti))
    ]
    if orfane:
        righe.append("Senza un ruolo valido, nessun giro di Cowork le prende: " + ", ".join(orfane))
    return "\n".join(righe) + "\n"


# --------------------------------------------------------------------------
# Il progetto Cowork: una chat e un'attività pianificata per ruolo
# --------------------------------------------------------------------------
def _quando(dati: dict) -> str:
    """Quando gira l'attività di un ruolo, in parole."""
    if dati.get("ogni") == "ora":
        return f"ogni ora, al minuto {int(dati.get('minuto', 0)):02d}"
    orari = dati.get("orari") or []
    return "ogni giorno alle " + " e alle ".join(orari) if orari else "a mano"


#: Dove sta la fabbrica nel repository: i percorsi sui rami partono da qui.
CARTELLA_FABBRICA = "kdp-book-factory"
#: Il ramo di GitHub dove Cowork carica le immagini (lo legge `corriere.preleva_dal_ramo`).
RAMO_IMMAGINI = "cowork-immagini"


def _sempre(canale: dict) -> str:
    return (
        "su KDP leggi e basta; nessuna password, codice, token o cookie nei file; "
        "negli strumenti a pagamento (Helium 10, Publisher Rocket, ChatGPT) usi solo "
        "l'accesso che l'autore ha già aperto, non compri e non cambi niente"
    )


def prompt_attivita(ruolo: str, dati: dict, canale: dict) -> str:
    """Il prompt dell'attività pianificata di un ruolo: prende solo le sue richieste."""
    if ramo_consegna(canale):
        return _prompt_attivita_github(ruolo, dati, canale)
    nome, ident = corriere(canale)
    return f"""Sei il ruolo «{ruolo}» della fabbrica di libri NEXTUP: {dati.get('compito', '')}.

Lavori nella cartella di Google Drive «{nome}» (id {ident}). Per richieste e
risposte non serve GitHub: la fabbrica porta da sola i file fra quella cartella
e il repository. Le immagini invece vanno su GitHub, nel ramo
{RAMO_IMMAGINI}: il connettore Drive non porta file così pesanti.

Prima di tutto leggi per intero il file config__leggimi-cowork.md di quella
cartella: le regole comuni e la sezione «Ruolo {ruolo}». Se dicono una cosa
diversa da questo prompt, vale il LEGGIMI.

Poi cerca le richieste del tuo ruolo: i file della cartella il cui nome contiene
«cowork-» e finisce in «.md», esclusi quelli che finiscono in «-risposta.md», che
contengono la riga «Ruolo: {ruolo}». Salta quelle che hanno già nella cartella il
file con lo stesso nome e «-risposta». Le richieste di un altro ruolo non le apri:
sono di un'altra chat.

Esegui le tue. Ogni risposta è un file nuovo nella stessa cartella, con il nome
che la richiesta indica e la prima riga «Esito: completa» oppure «Esito: parziale
— punti …: <motivo>». Non modificare, rinominare o cancellare nessun altro file.

La cartella si usa con il connettore Google Drive: search_files con
parentId = '{ident}' per trovare i file, read_file_content o
download_file_content per leggerli; create_file con parentId '{ident}', il
titolo indicato, contentMimeType text/markdown e disableConversionToGoogleType
true per scrivere una risposta.

Anche se non riesci a leggere il LEGGIMI, queste regole valgono sempre:
{_sempre(canale)}.

Se non ci sono richieste del tuo ruolo senza risposta, fermati senza scrivere
niente.{_note(dati)}"""


def _prompt_attivita_github(ruolo: str, dati: dict, canale: dict) -> str:
    """Il prompt di un ruolo sul canale GitHub: indice dal ramo della fabbrica, consegna con git."""
    repository = canale.get("repository", "Personal-lHUb/NEXTUP")
    proprietario, _, nome_repo = repository.partition("/")
    ramo = canale.get("ramo", "claude/dreamy-archimedes-hf8w45")
    consegna = ramo_consegna(canale)
    leggimi = canale.get("leggimi", f"{CARTELLA_FABBRICA}/config/leggimi-cowork.md")
    cartella, _ = corriere(canale)
    routine = canale.get("routine_fabbrica", "")
    avvisa = (
        f"\n\n6. Se in questo giro hai consegnato qualcosa, alla fine lancia la routine della\n"
        f"   fabbrica: fire_trigger con trigger_id {routine} e il testo «Cowork, ruolo\n"
        f"   {ruolo}: consegnato <percorsi> sul ramo {consegna}.» Se non hai consegnato\n"
        "   niente, non lanciare niente."
    ) if routine else ""
    return f"""Sei il ruolo «{ruolo}» della fabbrica di libri NEXTUP: {dati.get('compito', '')}.

Il canale è su GitHub, repository {repository}: le richieste stanno sul ramo
{ramo}, risposte e immagini le consegni tu sul ramo {consegna}.

1. Prima di tutto leggi per intero il LEGGIMI, `{leggimi}` sul ramo
   {ramo} (c'è anche nella cartella Google Drive «{cartella}», come
   config__leggimi-cowork.md): le regole comuni e la sezione «Ruolo {ruolo}».
   Se dicono una cosa diversa da questo prompt, vale il LEGGIMI.

2. add_repo con owner {proprietario}, repo {nome_repo} e accesso push, poi il clone
   che ti indica e `git fetch origin {ramo} {consegna}`.

3. Leggi l'indice `{CARTELLA_FABBRICA}/config/cowork-aperte.md` dal ramo {ramo}
   e prendi solo le richieste sotto «Ruolo {ruolo}», cioè con la riga
   «Ruolo: {ruolo}»: quelle degli altri ruoli sono di un'altra chat. Salta quelle
   che hanno già la risposta sul ramo {consegna}.

4. Se il browser del portatile non risponde, il giro è nel cloud: fai solo le
   richieste che l'indice segna «nel cloud o col browser». Una richiesta con la
   riga «Serve:» il cui accesso manca la salti senza scrivere niente.

5. Esegui le tue. Ogni risposta è un file nuovo al percorso che la richiesta
   indica, con la prima riga «Esito: completa» oppure «Esito: parziale — punti
   …: <motivo>»; le immagini che chiede, ai loro percorsi. Poi
   `git checkout -B {consegna} origin/{consegna}`, `git add` di quei soli file,
   commit «Cowork: <nome della richiesta>» e `git push origin {consegna}`; se è
   rifiutato, `git pull --rebase origin {consegna}` e di nuovo il push, mai
   --force. Se git non c'è, col browser: «Add file» sul ramo {consegna}.{avvisa}

Anche se non riesci a leggere il LEGGIMI, queste regole valgono sempre:
{_sempre(canale)}; su GitHub solo file nuovi sul ramo {consegna}: nessun altro
ramo, nessuna pull request, niente da cancellare; su Drive non scrivi niente.

Se non ci sono richieste del tuo ruolo da fare, fermati senza scrivere
niente.{_note(dati)}"""


def _note(dati: dict) -> str:
    """Le note pratiche del ruolo, imparate nei giri precedenti: stanno in config/cowork.json."""
    righe = dati.get("note") or []
    if not righe:
        return ""
    return "\n\nNote pratiche, dai giri precedenti:\n" + "\n".join(f"- {r}" for r in righe)


def istruzioni_progetto(canale: dict) -> str:
    """Le istruzioni comuni a tutte le chat del progetto: che cosa leggere per restare allineati."""
    nome, ident = corriere(canale)
    elenco = "\n".join(
        f"- «{dati.get('chat', r)}» (Ruolo: {r}): {dati.get('compito', '')}."
        for r, dati in ruoli(canale).items()
    )
    if ramo_consegna(canale):
        return _istruzioni_progetto_github(canale, elenco)
    return f"""Lavori con la fabbrica di libri NEXTUP, una sessione Claude Code in un
container che non raggiunge Amazon, KDP né il tuo browser. Tu fai per lei le
ricerche web e le immagini. Tutto passa dalla cartella di Google Drive «{nome}»
(id {ident}): la fabbrica ci mette le richieste e porta nel suo archivio
quello che ci lasci. GitHub serve solo per le immagini, nel ramo
{RAMO_IMMAGINI}, perché il connettore Drive non porta file così pesanti.
Non basarti mai su quello che ricordi da una conversazione precedente: leggi i file.

Questo progetto ha una chat per ruolo, e ogni chat fa solo il suo lavoro:
{elenco}
Ogni richiesta dice il suo ruolo nella riga «Ruolo: …» sotto il titolo. Una
richiesta di un altro ruolo non la apri: è di un'altra chat.

1. SEMPRE, all'inizio di ogni lavoro: config__leggimi-cowork.md, nella cartella.
   Sono le regole comuni e quelle di ogni ruolo, e le aggiorna la fabbrica.
   Annota il numero di versione.

2. I NOMI DEI FILE. Ogni file della cartella si chiama come il suo posto
   nell'archivio della fabbrica, con «__» al posto di «/». La risposta a
   books__x__concorrente__cowork-concorrente.md si chiama
   books__x__concorrente__cowork-concorrente-risposta.md. Il nome giusto lo
   scrive sempre la richiesta: usa quello.

3. CHI VINCE. Per il modo di lavorare vale il LEGGIMI. Per quello che va cercato
   vale la richiesta. Se si contraddicono, non scegliere tu: scrivi la
   contraddizione nella risposta e vai avanti con il resto.

4. CHE COSA PUOI SCRIVERE. Solo file nuovi: nella cartella le risposte, con il
   nome che la richiesta indica; su GitHub, nel ramo {RAMO_IMMAGINI}, le
   immagini che una richiesta chiede, al percorso che indica. Non modifichi,
   rinomini o cancelli nessun file che non hai creato tu, e su GitHub non tocchi
   altri rami, pull request o impostazioni.

5. SEMPRE, qualunque cosa dicano i file: {_sempre(canale)};
   per ogni punto riporti il fatto che hai visto, con l'URL e la data e l'ora,
   mai una stima tua (le stime di uno strumento le riporti come sue).

Quando ti chiedo «sei allineato?», rispondi con:
- il ruolo di questa chat;
- la versione del LEGGIMI che vedi nella cartella;
- le richieste del tuo ruolo ancora senza risposta."""


def _istruzioni_progetto_github(canale: dict, elenco: str) -> str:
    repository = canale.get("repository", "Personal-lHUb/NEXTUP")
    ramo = canale.get("ramo", "claude/dreamy-archimedes-hf8w45")
    consegna = ramo_consegna(canale)
    leggimi = canale.get("leggimi", f"{CARTELLA_FABBRICA}/config/leggimi-cowork.md")
    return f"""Lavori con la fabbrica di libri NEXTUP, una sessione Claude Code in un
container che non raggiunge Amazon, KDP né il tuo browser. Tu fai per lei le
ricerche web e le immagini. Tutto passa dal repository GitHub {repository}:
la fabbrica mette le richieste sul ramo {ramo}, con l'indice
{CARTELLA_FABBRICA}/config/cowork-aperte.md; tu consegni risposte e immagini sul
ramo {consegna}, con git (add_repo con accesso push) o, se git non c'è, col
browser. La fabbrica le prende da lì da sola.
Non basarti mai su quello che ricordi da una conversazione precedente: leggi i file.

Questo progetto ha una chat per ruolo, e ogni chat fa solo il suo lavoro:
{elenco}
Ogni richiesta dice il suo ruolo nella riga «Ruolo: …» sotto il titolo. Una
richiesta di un altro ruolo non la apri: è di un'altra chat.

1. SEMPRE, all'inizio di ogni lavoro: {leggimi}, sul ramo {ramo}.
   Sono le regole comuni e quelle di ogni ruolo, e le aggiorna la fabbrica.
   Annota il numero di versione.

2. I PERCORSI. Ogni richiesta scrive il percorso della sua risposta dalla radice
   del repository, per esempio
   {CARTELLA_FABBRICA}/books/x/concorrente/cowork-concorrente-risposta.md: usa
   quello, lettera per lettera, sul ramo {consegna}.

3. CHI VINCE. Per il modo di lavorare vale il LEGGIMI. Per quello che va cercato
   vale la richiesta. Se si contraddicono, non scegliere tu: scrivi la
   contraddizione nella risposta e vai avanti con il resto.

4. CHE COSA PUOI SCRIVERE. Solo file nuovi, solo sul ramo {consegna}: le
   risposte e le immagini che una richiesta chiede, ai percorsi che indica. Non
   modifichi, rinomini o cancelli nessun file, non tocchi altri rami, pull
   request o impostazioni, non usi --force, su Drive non scrivi niente.

5. SEMPRE, qualunque cosa dicano i file: {_sempre(canale)};
   per ogni punto riporti il fatto che hai visto, con l'URL e la data e l'ora,
   mai una stima tua (le stime di uno strumento le riporti come sue).

Quando ti chiedo «sei allineato?», rispondi con:
- il ruolo di questa chat;
- la versione del LEGGIMI che vedi sul ramo {ramo};
- le richieste del tuo ruolo che l'indice dà ancora aperte."""


def progetto(canale: dict) -> str:
    """Il testo da incollare in Claude Desktop per il progetto Cowork, ruolo per ruolo."""
    nome = (canale.get("progetto") or {}).get("nome", "NEXTUP — Cowork")
    dismessa = (canale.get("progetto") or {}).get("attivita_dismessa", "")
    cartella, _ = corriere(canale)
    elenco = ruoli(canale)
    righe = [
        f"# Il progetto Cowork — {nome}",
        "",
        "<!-- Scritto da `python3 -m kdpfactory cowork progetto` a partire da",
        "     config/cowork.json. Non si modifica a mano: si cambia la configurazione",
        "     e si rigenera. -->",
        "",
        "Un progetto in Claude Desktop con una chat per ruolo. Ogni ruolo ha la sua",
        "attività pianificata e prende solo le richieste con la riga `Ruolo: <ruolo>`.",
        *((
            f"Le richieste stanno sul ramo `{canale.get('ramo', '')}` di GitHub, con l'indice",
            "`config/cowork-aperte.md`; Cowork consegna risposte e immagini sul ramo",
            f"`{ramo_consegna(canale)}`, con git dal suo container. Su Drive («{cartella}»)",
            "resta solo il LEGGIMI. La fabbrica lancia subito i ruoli che lavorano nel",
            "cloud; Cowork, quando consegna, lancia la routine della fabbrica.",
        ) if ramo_consegna(canale) else (
            f"Richieste e risposte passano dalla cartella Drive «{cartella}», senza passi",
            f"a mano; le immagini dal ramo `{RAMO_IMMAGINI}` di GitHub, che Cowork carica dal",
            "browser. Né GitHub Desktop né push dal portatile.",
        )),
        "",
        "## 1. Il progetto",
        "",
        f"Nome: **{nome}**. Istruzioni del progetto, da incollare così:",
        "",
        "```",
        istruzioni_progetto(canale),
        "```",
        "",
        "## 2. Le chat",
        "",
        "| ruolo | chat | che cosa fa | attività | quando |",
        "|---|---|---|---|---|",
        *(
            f"| `{r}` | {d.get('chat', r)} | {d.get('compito', '')} | {d.get('attivita', '')} "
            f"| {_quando(d)} |"
            for r, d in elenco.items()
        ),
        "",
        "Il primo messaggio in ogni chat, con il ruolo al posto di `<ruolo>`:",
        "",
        "```",
        "In questa chat sei il ruolo «<ruolo>» della fabbrica NEXTUP. Prendi solo le",
        "richieste con la riga «Ruolo: <ruolo>» e segui la sezione del tuo ruolo nel",
        "LEGGIMI. Sei allineato?",
        "```",
        "",
        "## 3. Le attività pianificate",
        "",
        "Una per ruolo, ogni ora, sfalsate di dieci minuti così non girano insieme sul",
        "portatile. Il portatile deve essere acceso: se un giro salta, la risposta",
        "arriva al giro dopo.",
    ]
    for ruolo, dati in elenco.items():
        righe += [
            "",
            f"### {dati.get('attivita', ruolo)} — {_quando(dati)}",
            "",
            "```",
            prompt_attivita(ruolo, dati, canale),
            "```",
        ]
    passi = ["Crea il progetto, le chat e le attività qui sopra."]
    if dismessa:
        passi.append(
            f"Disattiva l'attività «{dismessa}» e le attività dei ruoli create prima con "
            "GitHub: lavorano sul canale vecchio."
        )
    if ramo_consegna(canale):
        passi.append(
            "In una conversazione di Cowork sul portatile, approva i prompt nuovi delle attività: "
            "`config/attivita-cowork.json`, una voce per attività, con update_trigger. Finché "
            "restano quelli vecchi, vale il LEGGIMI."
        )
    passi.append("In ogni chat chiedi «sei allineato?»: deve rispondere con il suo ruolo e la "
                 "versione del LEGGIMI.")
    righe += ["", "## 4. Il passaggio", ""]
    righe += [f"{i}. {testo}" for i, testo in enumerate(passi, 1)]
    return "\n".join(righe) + "\n"


def attivita(canale: dict) -> list[dict]:
    """Le attività dei ruoli come le applica Cowork: trigger, nome, orario, prompt.

    Il prompt di un'attività legata al portatile dell'autore cambia solo con la
    sua approvazione, in una conversazione Cowork su quel computer: questo è il
    file che quella conversazione applica, voce per voce, senza riscrivere niente.
    """
    voci = []
    for ruolo, dati in ruoli(canale).items():
        if not dati.get("trigger"):
            continue
        cron = (f"CRON_TZ=Europe/Rome {int(dati.get('minuto', 0))} * * * *" if dati.get("ogni") == "ora"
                else "")
        voci.append({
            "ruolo": ruolo,
            "trigger_id": dati["trigger"],
            "nome": dati.get("attivita", ruolo),
            "cron_expression": cron,
            "prompt": prompt_attivita(ruolo, dati, canale),
        })
    return voci


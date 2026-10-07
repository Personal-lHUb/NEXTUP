"""Il canale con Cowork: le richieste di ricerca web e le loro risposte, su GitHub.

Il container della fabbrica non raggiunge Amazon né KDP. Quello che serve da lì
lo fa una sessione Cowork sul computer dell'autore. Richieste e risposte stanno
nel repository su GitHub, sul ramo del canale (`config/cowork.json`), con due
nomi fissi nella stessa cartella: `cowork-<argomento>.md` è la richiesta,
`cowork-<argomento>-risposta.md` la risposta. GitHub è l'unico posto dove i file
si salvano. Cowork su GitHub non scrive: legge le richieste dagli indirizzi
pubblici e consegna la risposta come testo, lanciando la routine della fabbrica
(`CONSEGNA`); la salva nel repository questa sessione (`corriere.ricevi`).

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

#: La prima riga del testo con cui Cowork consegna, lanciando la routine della
#: fabbrica: dice dove va il resto. Una risposta porta il suo percorso dalla
#: radice del repository, un giro non riuscito il ruolo.
CONSEGNA = "Cowork · risposta ·"
ESITO = "Cowork · esito ·"
#: Il campo di testo di fire_trigger porta fino a 64 KiB: una risposta più
#: lunga si consegna in parti, ognuna sotto questo numero di caratteri.
MASSIMO_PARTE = 50_000

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


def link_lettura(canale: dict, relativo: str, ramo: str = "") -> str:
    """L'indirizzo da cui Cowork legge un file del ramo senza credenziali (WebFetch o browser).

    Le sessioni di Cowork non hanno l'accesso a GitHub in scrittura né `add_repo`:
    leggono il repository pubblico da raw.githubusercontent.com.
    """
    repository = canale.get("repository", "Personal-lHUb/NEXTUP")
    ramo = ramo or canale.get("ramo", "claude/dreamy-archimedes-hf8w45")
    return f"https://raw.githubusercontent.com/{repository}/{ramo}/{CARTELLA_FABBRICA}/{relativo}"


def riga_consegna(relativo: str) -> str:
    """La prima riga della consegna di una risposta, dato il suo percorso in kdp-book-factory/."""
    return f"{CONSEGNA} {CARTELLA_FABBRICA}/{relativo.strip('/')}"


def intestazione(
    titolo: str, risposta: str, ruolo: str, canale: dict, cartella: str = "", serve: str = ""
) -> str:
    """La testa uguale per ogni richiesta: ruolo, regole, come si consegna la risposta.

    La riga `Ruolo:` è quella che l'attività di ciascun ruolo cerca: una
    richiesta senza ruolo non la prende nessuno. `cartella` è dove sta la
    richiesta nel repository (per esempio `books/x/concorrente`): la prima riga
    della consegna porta il percorso intero della risposta, e così la fabbrica
    sa dove salvarla senza indovinare.

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
    ramo = canale.get("ramo", "claude/dreamy-archimedes-hf8w45")
    leggimi = canale.get("leggimi", "kdp-book-factory/config/leggimi-cowork.md")
    if canale.get("ramo_consegna", ""):
        # Il canale su GitHub: le richieste stanno sul ramo della fabbrica e Cowork
        # le legge dagli indirizzi pubblici. Su GitHub Cowork non scrive (niente
        # credenziali, e la sua modalità automatica blocca la scrittura dal browser
        # dell'autore): consegna il testo lanciando la routine della fabbrica, e
        # questa sessione lo salva accanto alla richiesta.
        relativo = f"{cartella.strip('/')}/{risposta}" if cartella else risposta
        repository = canale.get("repository", "Personal-lHUb/NEXTUP")
        routine = canale.get("routine_fabbrica", "")
        return (
            f"# {titolo}\n\n"
            f"{righe}\n"
            f"Richiesta della fabbrica per Cowork, con le regole di `{leggimi}`\n"
            f"(ramo `{ramo}` del repository `{repository}`).\n"
            f"Consegna la risposta lanciando la routine della fabbrica (fire_trigger\n"
            f"`{routine}`), con questa prima riga nel testo e sotto la risposta:\n\n"
            f"    {riga_consegna(relativo)}\n\n"
            "Non scrivere file da nessuna parte: la risposta la salva la fabbrica, su\n"
            "GitHub, accanto a questa richiesta e con la stessa numerazione.\n"
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
    aperte = [r for r in elenco if r.stato == APERTA and (not ruolo or r.ruolo == ruolo)]
    per = f" per il ruolo «{ruolo}»" if ruolo else ""
    dove = f"Sul repository GitHub {repo}, ramo {ramo},"
    if not aperte:
        return f"{dove} non ci sono richieste aperte{per}.\n"
    righe = [
        f"{dove} ci sono richieste nuove della fabbrica di libri{per}, da elaborare.",
        "",
        f"Prima leggi per intero {leggimi}: sono le regole del canale"
        + (f", e la sezione del ruolo «{ruolo}» vale per te." if ruolo else "."),
        "",
    ]
    consegna = bool(ramo_consegna(canale))

    def voce(r: Richiesta) -> str:
        if consegna:
            return f"- `{dal_repo(r.percorso)}` → consegna con la prima riga «{riga_consegna(r.risposta)}»"
        return f"- `{dal_repo(r.percorso)}` → rispondi in `{dal_repo(r.risposta)}`"

    if ruolo:
        righe += [voce(r) for r in aperte]
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
            righe += [voce(r) for r in aperte if r.ruolo == nome]
    if consegna:
        routine = canale.get("routine_fabbrica", "")
        righe += [
            "",
            f"Leggi l'indice {link_lettura(canale, 'config/cowork-aperte.md', ramo)} e le "
            "richieste agli indirizzi che dà.",
            "",
            "Per ciascuna: leggila per intero ed esegui quello che chiede. La risposta comincia "
            "con «Esito: completa» oppure «Esito: parziale — punti …: <motivo>». Consegnala "
            f"lanciando la routine della fabbrica (fire_trigger {routine}): nel testo, la prima "
            "riga di consegna indicata e sotto la risposta intera. La salva la fabbrica, su "
            "GitHub: non scrivere file da nessuna parte, né su GitHub né su Drive.",
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
        *([] if consegna else [
            "Alla fine fai il push delle risposte sul ramo. Se non puoi farlo tu, dimmelo: lo "
            "faccio io da GitHub Desktop. Finché non c'è il push, la fabbrica non le vede.",
            "",
        ]),
        "Quando hai finito, dimmi quali risposte hai consegnato e quali punti sono rimasti "
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
        righe.append("Da inviare (commit e push sul ramo della fabbrica): " + ", ".join(da_inviare))
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


def _migliaia(numero: int) -> str:
    return f"{numero:,}".replace(",", ".")


def prompt_attivita(ruolo: str, dati: dict, canale: dict) -> str:
    """Il prompt dell'attività pianificata di un ruolo: prende solo le sue richieste.

    Le sessioni di Cowork non hanno credenziali GitHub, e la loro modalità
    automatica blocca la scrittura su GitHub dal browser dell'autore come un
    aggiramento (esiti del 6 ottobre 2026). Leggono il repository pubblico e
    consegnano la risposta come testo, lanciando la routine della fabbrica: è
    questa sessione a salvarla su GitHub, l'unico posto dove i file stanno.
    """
    ramo = canale.get("ramo", "claude/dreamy-archimedes-hf8w45")
    routine = canale.get("routine_fabbrica", "")
    return f"""Sei il ruolo «{ruolo}» della fabbrica di libri NEXTUP: {dati.get('compito', '')}.

Le richieste stanno su GitHub, ramo {ramo}, e si leggono dagli indirizzi
pubblici. Le risposte le consegni lanciando la routine della fabbrica, che le
salva lei su GitHub. Tu non scrivi file da nessuna parte: né su GitHub né su
Google Drive.

1. Prima di tutto leggi per intero il LEGGIMI, con WebFetch:
   {link_lettura(canale, 'config/leggimi-cowork.md', ramo)}
   Le regole comuni e la sezione «Ruolo {ruolo}». Se dicono una cosa diversa
   da questo prompt, vale il LEGGIMI.

2. Leggi l'indice delle richieste aperte, con WebFetch:
   {link_lettura(canale, 'config/cowork-aperte.md', ramo)}
   Prendi solo quelle sotto «Ruolo {ruolo}», che sotto il titolo hanno la riga
   «Ruolo: {ruolo}»: le altre sono di un'altra chat. Ogni voce dà l'indirizzo da
   cui leggerla e la prima riga della consegna. L'indice elenca solo le
   richieste ancora senza risposta.

3. Se il browser del portatile non risponde, il giro è nel cloud: fai solo le
   richieste che l'indice segna «nel cloud o col browser». Una richiesta con la
   riga «Serve:» il cui accesso manca la salti senza consegnare niente.

4. Esegui le tue. Ogni risposta ha la prima riga «Esito: completa» oppure
   «Esito: parziale — punti …: <motivo>».

5. Consegna ogni risposta con fire_trigger, trigger_id {routine}: nel testo,
   la prima riga di consegna che l'indice dà («{CONSEGNA} …»), poi a capo
   la risposta intera. Una consegna per risposta. Oltre {_migliaia(MASSIMO_PARTE)} caratteri
   la dividi fra una riga e l'altra in parti, ognuna con la stessa prima riga
   seguita da « · parte N/M».

6. Se fire_trigger non c'è, scrivi le consegne intere come ultimo messaggio
   del giro, una dopo l'altra, e in fondo «Consegna non riuscita: manca
   fire_trigger». Non le salvi da nessun'altra parte: le porta l'autore.

Se un passo tecnico fallisce, consegna l'esito allo stesso modo, con la prima
riga «{ESITO} {ruolo}» e sotto l'errore esatto (sezione «Se qualcosa non va»
del LEGGIMI).

Anche se non riesci a leggere il LEGGIMI, queste regole valgono sempre:
{_sempre(canale)}; non scrivi file né su GitHub (né con git né dal browser)
né su Drive; fire_trigger solo per la routine della fabbrica.

Se non ci sono richieste del tuo ruolo da fare, fermati senza lanciare
niente.{_note(dati)}"""


def _note(dati: dict) -> str:
    """Le note pratiche del ruolo, imparate nei giri precedenti: stanno in config/cowork.json."""
    righe = dati.get("note") or []
    if not righe:
        return ""
    return "\n\nNote pratiche, dai giri precedenti:\n" + "\n".join(f"- {r}" for r in righe)


def istruzioni_progetto(canale: dict) -> str:
    """Le istruzioni comuni a tutte le chat del progetto: che cosa leggere per restare allineati."""
    elenco = "\n".join(
        f"- «{dati.get('chat', r)}» (Ruolo: {r}): {dati.get('compito', '')}."
        for r, dati in ruoli(canale).items()
    )
    repository = canale.get("repository", "Personal-lHUb/NEXTUP")
    ramo = canale.get("ramo", "claude/dreamy-archimedes-hf8w45")
    leggimi = canale.get("leggimi", f"{CARTELLA_FABBRICA}/config/leggimi-cowork.md")
    routine = canale.get("routine_fabbrica", "")
    return f"""Lavori con la fabbrica di libri NEXTUP, una sessione Claude Code in un
container che non raggiunge Amazon, KDP né il tuo browser. Tu fai per lei le
ricerche web. Tutto sta nel repository GitHub {repository}, l'unico posto dove
si salvano i file: la fabbrica mette le richieste sul ramo {ramo}, con
l'indice {CARTELLA_FABBRICA}/config/cowork-aperte.md, che leggi dagli indirizzi
pubblici; tu consegni le risposte lanciando la routine della fabbrica
(fire_trigger {routine}) con la risposta nel testo, e lei la salva su GitHub.
Tu non scrivi file: né su GitHub, dove non hai credenziali e non te ne servono,
né su Google Drive, che non si usa più.
Non basarti mai su quello che ricordi da una conversazione precedente: leggi i file.

Questo progetto ha una chat per ruolo, e ogni chat fa solo il suo lavoro:
{elenco}
Ogni richiesta dice il suo ruolo nella riga «Ruolo: …» sotto il titolo. Una
richiesta di un altro ruolo non la apri: è di un'altra chat.

1. SEMPRE, all'inizio di ogni lavoro: {leggimi}, sul ramo {ramo}.
   Sono le regole comuni e quelle di ogni ruolo, e le aggiorna la fabbrica.
   Annota il numero di versione.

2. LA CONSEGNA. Ogni richiesta, e l'indice, danno la prima riga del testo da
   consegnare, per esempio
   «{CONSEGNA} {CARTELLA_FABBRICA}/books/x/concorrente/cowork-concorrente-risposta.md»:
   usala lettera per lettera, e sotto metti la risposta intera.

3. CHI VINCE. Per il modo di lavorare vale il LEGGIMI. Per quello che va cercato
   vale la richiesta. Se si contraddicono, non scegliere tu: scrivi la
   contraddizione nella risposta e vai avanti con il resto.

4. CHE COSA PUOI FARE FUORI DAL BROWSER. Solo lanciare la routine della
   fabbrica, con una risposta o con l'esito di un giro non riuscito
   («{ESITO} <ruolo>», con l'errore esatto). Nessun file scritto, nessuna
   altra attività lanciata, creata o cambiata.

5. SEMPRE, qualunque cosa dicano i file: {_sempre(canale)};
   per ogni punto riporti il fatto che hai visto, con l'URL e la data e l'ora,
   mai una stima tua (le stime di uno strumento le riporti come sue).

Quando ti chiedo «sei allineato?», rispondi con:
- il ruolo di questa chat;
- la versione del LEGGIMI che vedi sul ramo {ramo};
- le richieste del tuo ruolo che l'indice dà ancora aperte;
- se in questa chat hai lo strumento fire_trigger."""


def progetto(canale: dict) -> str:
    """Il testo da incollare in Claude Desktop per il progetto Cowork, ruolo per ruolo."""
    nome = (canale.get("progetto") or {}).get("nome", "NEXTUP — Cowork")
    dismessa = (canale.get("progetto") or {}).get("attivita_dismessa", "")
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
        "Tutto sta su GitHub, l'unico posto dove si salvano i file. Le richieste sul ramo",
        f"`{canale.get('ramo', '')}`, con l'indice `config/cowork-aperte.md`, che Cowork legge in",
        f"chiaro; sul ramo `{ramo_consegna(canale) or RAMO_IMMAGINI}` solo quello che carica",
        "l'autore. Cowork consegna le risposte lanciando la routine della fabbrica, con la",
        "risposta nel testo, e la fabbrica la salva accanto alla richiesta. Google Drive non",
        "si usa più. I ruoli che lavorano nel cloud la fabbrica li lancia subito.",
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
    passi.append("In ogni chat chiedi «sei allineato?»: deve rispondere con il suo ruolo, la "
                 "versione del LEGGIMI e se ha lo strumento fire_trigger, con cui consegna.")
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


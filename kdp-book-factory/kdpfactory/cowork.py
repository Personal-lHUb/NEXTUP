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

    def to_dict(self) -> dict:
        return asdict(self)


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
        if ESCLUSE.intersection(relativo.parts[:-1]) or not _e_richiesta(percorso):
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
            )
        )
    return trovate


def ruolo_di(testo: str) -> str:
    """Il ruolo dichiarato dalla richiesta, nella riga `Ruolo: …`; vuoto se manca."""
    trovato = _RUOLO.search(testo)
    return trovato.group(1) if trovato else ""


def ruoli(canale: dict) -> dict[str, dict]:
    """I ruoli di Cowork, ciascuno con la sua chat e la sua attività pianificata."""
    return canale.get("ruoli") or {}


def intestazione(titolo: str, risposta: str, ruolo: str, canale: dict) -> str:
    """La testa uguale per ogni richiesta: ruolo, regole, dove va la risposta.

    La riga `Ruolo:` è quella che l'attività di ciascun ruolo cerca: una
    richiesta senza ruolo non la prende nessuno.
    """
    ramo = canale.get("ramo", "claude/dreamy-archimedes-hf8w45")
    leggimi = canale.get("leggimi", "kdp-book-factory/config/leggimi-cowork.md")
    return (
        f"# {titolo}\n\n"
        f"{RUOLO} {ruolo}\n\n"
        f"Richiesta della fabbrica per Cowork, con le regole di\n`{leggimi}`.\n"
        f"La risposta va in `{risposta}`, accanto a questo file,\n"
        f"sul ramo `{ramo}`, con la stessa numerazione.\n"
        "Per ogni punto: il fatto visto sulla pagina, l'URL, la data e l'ora.\n"
        "Se una pagina chiede un captcha o l'accesso e non si riesce ad andare avanti,\n"
        "scrivilo invece di stimare: l'accesso non lo fai tu.\n"
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
    if not aperte:
        return f"Sul ramo {ramo} di {repo} non ci sono richieste aperte{per}.\n"
    righe = [
        f"Sul repository GitHub {repo}, ramo {ramo}, ci sono richieste nuove della "
        f"fabbrica di libri{per}, da elaborare.",
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
    righe += [
        "",
        "Se lavori sulla copia locale di GitHub Desktop, prima di cominciare aggiornala dal "
        "ramo remoto con Fetch e Pull: su una copia vecchia queste richieste non ci sono.",
        "",
        "Per ciascuna: leggila per intero ed esegui quello che chiede. Scrivi la "
        "risposta nel file indicato e fanne il commit sullo stesso ramo, con la "
        "prima riga «Esito: completa» oppure «Esito: parziale — punti …: <motivo>». "
        "Non modificare altri file.",
        "",
        "Regole valide per tutte:",
        "- per ogni punto, il fatto che hai visto sulla pagina, non una stima, con "
        "l'URL e la data e l'ora della verifica;",
        "- se una pagina chiede un captcha o l'accesso e non riesci ad andare avanti, "
        "scrivilo invece di stimare;",
        "- su KDP leggi e basta: non creare titoli, non salvare bozze, non pubblicare;",
        "- in Helium 10 e Publisher Rocket usa solo l'accesso già aperto nel browser: non "
        "inserire credenziali, non comprare, non cambiare niente;",
        "- nessuna password, codice o cookie nei file.",
        "",
        "Alla fine fai il push delle risposte sul ramo. Se non puoi farlo tu, dimmelo: lo "
        "faccio io da GitHub Desktop. Finché non c'è il push, la fabbrica non le vede.",
        "",
        "Quando hai finito, dimmi quali risposte hai scritto e quali punti sono rimasti "
        "senza risposta.",
    ]
    return "\n".join(righe) + "\n"


def rapporto(elenco: list[Richiesta], noti: frozenset[str] | set[str] = frozenset()) -> str:
    """Lo stato del canale, una riga per richiesta, con il ruolo che la prende."""
    if not elenco:
        return "Nessuna richiesta a Cowork.\n"
    righe = [f"  {r.stato:<17} {r.invio:<15} {r.ruolo or '—':<14} {r.percorso}" for r in elenco]
    conteggio = {s: sum(r.stato == s for r in elenco) for s in (APERTA, ARRIVATA, SUPERATA, CHIUSA)}
    righe.append(
        f"\n{conteggio[APERTA]} aperte · {conteggio[ARRIVATA]} con risposta da applicare · "
        f"{conteggio[SUPERATA]} con risposta superata · {conteggio[CHIUSA]} applicate"
    )
    da_inviare = [r.percorso for r in elenco if r.invio == DA_INVIARE]
    if da_inviare:
        righe.append("Da inviare (commit e push sul ramo del canale): " + ", ".join(da_inviare))
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
def _orari(orari: list[str]) -> str:
    return " e alle ".join(orari) if orari else "a mano"


def prompt_attivita(ruolo: str, dati: dict, canale: dict) -> str:
    """Il prompt dell'attività pianificata di un ruolo: prende solo le sue richieste."""
    repo = canale.get("repository", "Personal-lHUb/NEXTUP")
    ramo = canale.get("ramo", "claude/dreamy-archimedes-hf8w45")
    leggimi = canale.get("leggimi", "kdp-book-factory/config/leggimi-cowork.md")
    return f"""Sei il ruolo «{ruolo}» della fabbrica di libri NEXTUP: {dati.get('compito', '')}.

Lavora sul repository GitHub {repo}, ramo {ramo}. Se hai accesso diretto a
GitHub, leggilo da lì. Se usi la copia locale aperta in GitHub Desktop, prima
aggiornala dal ramo remoto con Fetch e Pull; se non puoi farlo tu, fermati e
chiedilo all'autore.

Prima di tutto leggi per intero {leggimi}: le regole comuni
e la sezione «Ruolo {ruolo}». Se dicono una cosa diversa da questo prompt, vale
il LEGGIMI.

Poi cerca le richieste del tuo ruolo: i file cowork-*.md sotto kdp-book-factory/
che contengono la riga «Ruolo: {ruolo}», esclusi quelli che finiscono in
-risposta.md e quelli nelle cartelle backup e build. Salta quelle che hanno già
accanto il file con lo stesso nome e -risposta, e quelle che contengono «Stato:
applicata». Le richieste di un altro ruolo non le apri: sono di un'altra chat.

Esegui le tue e scrivi le risposte come dicono il LEGGIMI e la richiesta, con la
prima riga «Esito: completa» oppure «Esito: parziale — punti …: <motivo>». Poi fai
il commit delle sole risposte sullo stesso ramo, e il push se puoi.

Anche se non riesci a leggere il LEGGIMI, tre regole valgono sempre: su KDP leggi
e basta; nessuna password, codice, token o cookie nei file o nei commit; negli
strumenti a pagamento usi solo l'accesso che l'autore ha già aperto, non compri
e non cambi niente.

Se non ci sono richieste del tuo ruolo senza risposta, fermati senza scrivere
niente."""


def istruzioni_progetto(canale: dict) -> str:
    """Le istruzioni comuni a tutte le chat del progetto: che cosa leggere per restare allineati."""
    repo = canale.get("repository", "Personal-lHUb/NEXTUP")
    ramo = canale.get("ramo", "claude/dreamy-archimedes-hf8w45")
    leggimi = canale.get("leggimi", "kdp-book-factory/config/leggimi-cowork.md")
    elenco = "\n".join(
        f"- «{dati.get('chat', r)}» (Ruolo: {r}): {dati.get('compito', '')}."
        for r, dati in ruoli(canale).items()
    )
    return f"""Lavori con la fabbrica di libri NEXTUP, una sessione Claude Code in un
container che non raggiunge Amazon né KDP. Tu fai per lei le ricerche web.
Tutto passa dal repository GitHub {repo}, ramo {ramo}.
Non basarti mai su quello che ricordi da una conversazione precedente: leggi i file.

Questo progetto ha una chat per ruolo, e ogni chat fa solo il suo lavoro:
{elenco}
Ogni richiesta dice il suo ruolo nella riga «Ruolo: …» sotto il titolo. Una
richiesta di un altro ruolo non la apri: è di un'altra chat.

0. PRIMA DI TUTTO, la versione giusta. Leggi dal ramo remoto se hai accesso
   diretto a GitHub. Se usi la copia locale di GitHub Desktop, aggiornala con
   Fetch e Pull; se non puoi farlo tu, chiedilo all'autore prima di cominciare.

1. SEMPRE, all'inizio di ogni lavoro: {leggimi}. Sono le
   regole comuni e quelle di ogni ruolo, e le aggiorna la fabbrica. Annota il
   numero di versione.

2. PER CAPIRE IL CONTESTO, quando una richiesta non basta:
   - RICERCA-WEB.md, alla radice: dove serve la ricerca web e che cosa cercare;
   - kdp-book-factory/docs/cowork.md: come gira lo scambio con la fabbrica;
   - i file che una richiesta cita per nome, per esempio
     kdp-book-factory/books/<libro>/manuale/capitolo-NN.md per la frase esatta
     da verificare, o kdp-book-factory/books/<libro>/book.json per i dati del libro.

3. CHI VINCE. Per il modo di lavorare vale il LEGGIMI. Per i fatti sul libro
   valgono i file del libro. Per quello che va cercato vale la richiesta. Se due
   di questi si contraddicono, non scegliere tu: scrivi la contraddizione nella
   risposta, con i nomi dei file, e vai avanti con il resto.

4. CHE COSA PUOI SCRIVERE. Solo i file di risposta
   (cowork-<argomento>-risposta.md, accanto alla richiesta), con un commit sul
   ramo {ramo}. Non modifichi niente altro.

5. SEMPRE, qualunque cosa dicano i file:
   - su KDP (kdp.amazon.com) leggi e basta: niente titoli, bozze, pubblicazioni
     o impostazioni cambiate;
   - negli strumenti a pagamento (Helium 10, Publisher Rocket) usi solo
     l'accesso che l'autore ha già aperto nel browser: non inserisci
     credenziali, non compri, non cambi abbonamenti né impostazioni;
   - nessuna password, codice, token o cookie nei file o nei commit;
   - per ogni punto riporti il fatto che hai visto, con l'URL e la data e l'ora,
     mai una stima tua. Le stime di uno strumento le riporti come sue.

Quando ti chiedo «sei allineato?», rispondi con:
- il ruolo di questa chat;
- l'ultimo commit che vedi sul ramo {ramo}, con hash e data;
- la versione del LEGGIMI;
- le richieste del tuo ruolo ancora senza risposta."""


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
        "attività pianificata e prende solo le richieste con la riga `Ruolo: <ruolo>`:",
        "la chat delle fonti non vede le recensioni, quella delle parole chiave non",
        "entra in KDP.",
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
        "| ruolo | chat | che cosa fa | attività | orari (Roma) |",
        "|---|---|---|---|---|",
        *(
            f"| `{r}` | {d.get('chat', r)} | {d.get('compito', '')} | {d.get('attivita', '')} "
            f"| {', '.join(d.get('orari') or []) or 'a mano'} |"
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
        "Sfalsate di un quarto d'ora, così non girano insieme sul portatile, e tutte",
        "prima del controllo della fabbrica (9:59 e 15:59). Se un giro salta, la",
        "risposta arriva al giro dopo.",
    ]
    for ruolo, dati in elenco.items():
        righe += [
            "",
            f"### {dati.get('attivita', ruolo)} — ogni giorno alle {_orari(dati.get('orari') or [])}",
            "",
            "```",
            prompt_attivita(ruolo, dati, canale),
            "```",
        ]
    righe += [
        "",
        "## 4. Il passaggio",
        "",
        "1. Crea il progetto, le chat e le attività qui sopra.",
    ]
    if dismessa:
        righe.append(
            f"2. Disattiva l'attività «{dismessa}»: finché resta accesa risponde a tutte "
            "le richieste, anche a quelle di un ruolo, e i ruoli non sono più separati."
        )
    righe += [
        f"{len(righe) - righe.index('## 4. Il passaggio') - 1}. In ogni chat chiedi "
        "«sei allineato?»: deve rispondere con il suo ruolo e la versione del LEGGIMI.",
        "",
    ]
    return "\n".join(righe)

"""Le consegne degli agenti: l'uscita intera in un file, nella chat una riga.

Un editor che correggeva tre capitoli li rimandava interi nella conversazione:
ottomila token a consegna, che riempivano la finestra di contesto e la facevano
riassumere prima del tempo, con i dettagli persi. Ora l'agente scrive l'uscita
in `books/<slug>/consegne/<nome>.md` (l'unico posto dove può scrivere: lo
controlla la guardia di `diario`) e risponde con una riga. Da lì un comando la
porta dove serve, con la copia di backup di quello che sostituisce: i capitoli
in `manuale/capitolo-NN.md` e nel manoscritto, un rapporto in `revisioni/`.

Le consegne restano in git: sono l'uscita grezza di ogni agente, la traccia di
che cosa ha consegnato prima che la sessione la importasse.
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from . import backup, diario, manuale
from .models import BookProject, Outline

CARTELLA = diario.CONSEGNE


def cartella(project: BookProject) -> Path:
    return project.root / CARTELLA


def segna_letta(project: BookProject, file: Path) -> None:
    """Una consegna letta e usata senza importarla (un rapporto già riassunto altrove)."""
    diario.annota(project, f"consegna `{file.name}` letta")


def _cartella_backup(project: BookProject, adesso: datetime | None = None) -> Path:
    stamp = (adesso or datetime.now()).strftime(backup.STAMP_FORMAT)
    return backup.backup_root(project) / CARTELLA / stamp


def dividi(testo: str) -> list[list[str]]:
    """I capitoli di una consegna, ognuno dalla sua riga `# ` fuori dai blocchi di codice."""
    blocchi: list[list[str]] = []
    corrente: list[str] = []
    dentro_codice = False
    for riga in testo.splitlines():
        if riga.startswith("```"):
            dentro_codice = not dentro_codice
        if riga.startswith("# ") and not dentro_codice and corrente:
            blocchi.append(corrente)
            corrente = []
        if corrente or riga.startswith("# "):
            corrente.append(riga)
    if corrente:
        blocchi.append(corrente)
    for righe in blocchi:
        while righe and righe[-1].strip() in {"", "```", "---"}:
            righe.pop()
    return blocchi


def importa_capitoli(
    project: BookProject, file: Path, numeri: list[int], adesso: datetime | None = None,
) -> list[dict]:
    """Porta i capitoli consegnati in `manuale/` e nel manoscritto, dopo il backup.

    I titoli devono essere quelli della scaletta, nell'ordine dei `numeri`: un
    agente che ha cambiato un titolo, o ne ha saltato uno, non sovrascrive niente.
    """
    outline = Outline.load(project.outline_path)
    titoli = {c.number: c.title for c in outline.chapters}
    blocchi = dividi(file.read_text(encoding="utf-8"))
    if len(blocchi) != len(numeri):
        trovati = [b[0] for b in blocchi]
        raise ValueError(f"attesi {len(numeri)} capitoli, trovati {len(blocchi)}: {trovati}")
    for numero, righe in zip(numeri, blocchi, strict=True):
        titolo = righe[0][2:].strip()
        if numero not in titoli:
            raise ValueError(f"nella scaletta non c'è la sezione {numero}")
        if titolo != titoli[numero]:
            raise ValueError(f"sezione {numero}: titolo «{titolo}» diverso da «{titoli[numero]}»")

    copie = _cartella_backup(project, adesso)
    copie.mkdir(parents=True, exist_ok=True)
    esiti = []
    for numero, righe in zip(numeri, blocchi, strict=True):
        destinazione = project.root / "manuale" / f"capitolo-{numero:02d}.md"
        prima = 0
        if destinazione.exists():
            shutil.copy2(destinazione, copie / f"{destinazione.name}.prima")
            prima = len(destinazione.read_text(encoding="utf-8").split())
        destinazione.parent.mkdir(parents=True, exist_ok=True)
        testo = "\n".join(righe) + "\n"
        destinazione.write_text(testo, encoding="utf-8")
        shutil.copy2(destinazione, copie / destinazione.name)
        esito = manuale.importa_capitolo(project, outline, numero, testo)
        esito["parole_prima"] = prima
        esiti.append(esito)
    elenco = ", ".join(f"{e['numero']:02d}" for e in esiti)
    diario.annota(project, f"consegna `{file.name}` importata: sezioni {elenco} (backup {copie})")
    return esiti


def importa_file(
    project: BookProject, file: Path, destinazione: str, adesso: datetime | None = None,
) -> Path:
    """Porta una consegna intera (un rapporto, una scaletta) dove serve, dopo il backup."""
    arrivo = (project.root / destinazione).resolve()
    if project.root.resolve() not in arrivo.parents:
        raise ValueError(f"{destinazione}: fuori dalla cartella del libro")
    if not file.read_text(encoding="utf-8").strip():
        raise ValueError(f"{file.name}: consegna vuota, non sostituisco niente")
    if arrivo.exists():
        copie = _cartella_backup(project, adesso)
        copie.mkdir(parents=True, exist_ok=True)
        shutil.copy2(arrivo, copie / f"{arrivo.name}.prima")
    arrivo.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(file, arrivo)
    diario.annota(project, f"consegna `{file.name}` importata in `{destinazione}`")
    return arrivo

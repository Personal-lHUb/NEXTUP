"""Copia di sicurezza di tutto ciò che la pipeline produce.

Ogni comando che scrive file lascia uno **snapshot** datato in
`backup/<slug>/<AAAAMMGG-hhmmss>/`: scheda del libro, scaletta, manoscritto e
tutti i file di `build/`. Serve a due cose:

1. non perdere una stesura che piaceva quando l'editor, la passata di stile o
   `write --overwrite` riscrivono i capitoli sul posto;
2. poter tornare indietro (`kdpfactory backup <slug> --restore <id>`).

Due snapshot identici non vengono duplicati: se nulla è cambiato dall'ultimo,
la copia viene saltata.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .models import BookProject

#: cartella di backup predefinita (accanto a `books/`), sovrascrivibile
#: con --backup-dir o con la variabile d'ambiente KDPFACTORY_BACKUP_DIR
DEFAULT_BACKUP_DIR = Path(
    os.environ.get("KDPFACTORY_BACKUP_DIR")
    or Path(__file__).resolve().parent.parent / "backup"
)

#: che cosa entra nello snapshot, in ordine di importanza
INCLUDED_FILES = ("book.json", "outline.json", "state.json")
INCLUDED_DIRS = ("manuscript", "build")

MANIFEST_NAME = "manifest.json"
STAMP_FORMAT = "%Y%m%d-%H%M%S"

#: Preferenza valida per l'intera esecuzione, impostata una volta dalla riga di
#: comando: così anche la pipeline e gli agenti possono mettere al sicuro i file
#: senza doversi passare le opzioni di mano in mano.
_POLICY: dict = {"enabled": True, "directory": None}


def configure(*, enabled: bool = True, directory: Path | str | None = None) -> None:
    _POLICY["enabled"] = enabled
    _POLICY["directory"] = Path(directory) if directory else None


def is_enabled() -> bool:
    return bool(_POLICY["enabled"])


def _directory(backup_dir: Path | None) -> Path:
    return Path(backup_dir or _POLICY["directory"] or DEFAULT_BACKUP_DIR)


@dataclass
class Snapshot:
    """Una copia datata del progetto."""

    path: Path
    stamp: str
    reason: str = ""
    fingerprint: str = ""
    files: int = 0
    bytes: int = 0
    created_at: str = ""

    @property
    def id(self) -> str:
        return self.stamp

    def to_dict(self) -> dict:
        return {
            "id": self.stamp,
            "reason": self.reason,
            "fingerprint": self.fingerprint,
            "files": self.files,
            "bytes": self.bytes,
            "created_at": self.created_at,
        }

    def describe(self) -> str:
        size = self.bytes / 1_048_576
        return f"{self.stamp}  {self.files:>3} file  {size:>6.1f} MB  {self.reason}"


# --------------------------------------------------------------------------
# Raccolta dei file
# --------------------------------------------------------------------------
def collect_files(project: BookProject) -> list[Path]:
    """File del progetto da copiare, in percorsi assoluti."""
    found: list[Path] = []
    for name in INCLUDED_FILES:
        path = project.root / name
        if path.is_file():
            found.append(path)
    for directory in INCLUDED_DIRS:
        base = project.root / directory
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file():
                found.append(path)
    return found


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fingerprint(project: BookProject) -> str:
    """Impronta dell'intero progetto: cambia se cambia un solo byte."""
    digest = hashlib.sha256()
    for path in collect_files(project):
        digest.update(str(path.relative_to(project.root)).encode("utf-8"))
        digest.update(_sha256(path).encode("ascii"))
    return digest.hexdigest()


def backup_root(project: BookProject, backup_dir: Path | None = None) -> Path:
    return _directory(backup_dir) / project.root.name


# --------------------------------------------------------------------------
# Snapshot
# --------------------------------------------------------------------------
def list_snapshots(project: BookProject, backup_dir: Path | None = None) -> list[Snapshot]:
    root = backup_root(project, backup_dir)
    if not root.is_dir():
        return []
    snapshots: list[Snapshot] = []
    for path in sorted(root.iterdir()):
        manifest = path / MANIFEST_NAME
        if not manifest.is_file():
            continue
        data = json.loads(manifest.read_text(encoding="utf-8"))
        snapshots.append(
            Snapshot(
                path=path,
                stamp=data.get("id", path.name),
                reason=data.get("reason", ""),
                fingerprint=data.get("fingerprint", ""),
                files=data.get("files", 0),
                bytes=data.get("bytes", 0),
                created_at=data.get("created_at", ""),
            )
        )
    return snapshots


def latest_snapshot(project: BookProject, backup_dir: Path | None = None) -> Snapshot | None:
    snapshots = list_snapshots(project, backup_dir)
    return snapshots[-1] if snapshots else None


def snapshot(
    project: BookProject,
    reason: str = "",
    *,
    backup_dir: Path | None = None,
    force: bool = False,
    quiet: bool = False,
) -> Snapshot | None:
    """Copia il progetto nella cartella di backup.

    Restituisce `None` se i backup sono disattivati (`--no-backup`), se non c'è
    niente da copiare o se nulla è cambiato rispetto all'ultimo snapshot (a meno
    di `force=True`).
    """
    if not is_enabled():
        return None
    files = collect_files(project)
    if not files:
        return None

    current = fingerprint(project)
    previous = latest_snapshot(project, backup_dir)
    if not force and previous and previous.fingerprint == current:
        return None

    root = backup_root(project, backup_dir)
    stamp = datetime.now().strftime(STAMP_FORMAT)
    destination = root / stamp
    suffix = 1
    while destination.exists():  # più snapshot nello stesso secondo
        suffix += 1
        destination = root / f"{stamp}-{suffix}"
    destination.mkdir(parents=True)

    entries: list[dict] = []
    total_bytes = 0
    for path in files:
        relative = path.relative_to(project.root)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        size = path.stat().st_size
        total_bytes += size
        entries.append({"path": str(relative), "bytes": size, "sha256": _sha256(path)})

    result = Snapshot(
        path=destination,
        stamp=destination.name,
        reason=reason,
        fingerprint=current,
        files=len(entries),
        bytes=total_bytes,
        created_at=datetime.now().isoformat(timespec="seconds"),
    )
    (destination / MANIFEST_NAME).write_text(
        json.dumps({**result.to_dict(), "contenuto": entries}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    if not quiet:
        size = total_bytes / 1_048_576
        print(f"  backup: {destination} ({result.files} file, {size:.1f} MB)")
    return result


# --------------------------------------------------------------------------
# Ripristino e manutenzione
# --------------------------------------------------------------------------
@dataclass
class RestoreResult:
    snapshot: Snapshot
    restored: list[Path] = field(default_factory=list)
    safety: Snapshot | None = None


def restore(
    project: BookProject,
    snapshot_id: str,
    *,
    backup_dir: Path | None = None,
    quiet: bool = False,
) -> RestoreResult:
    """Riporta il progetto allo stato di uno snapshot.

    Prima di sovrascrivere qualsiasi cosa prende una copia di sicurezza dello
    stato attuale: un ripristino sbagliato non deve essere definitivo.
    """
    snapshots = {s.stamp: s for s in list_snapshots(project, backup_dir)}
    if snapshot_id in ("latest", "ultimo"):
        chosen = latest_snapshot(project, backup_dir)
        if chosen is None:
            raise FileNotFoundError("Nessuno snapshot disponibile.")
    else:
        try:
            chosen = snapshots[snapshot_id]
        except KeyError:
            disponibili = ", ".join(snapshots) or "nessuno"
            raise FileNotFoundError(
                f"Snapshot {snapshot_id!r} non trovato. Disponibili: {disponibili}"
            ) from None

    safety = snapshot(
        project, reason="prima del ripristino", backup_dir=backup_dir, force=True, quiet=quiet
    )

    restored: list[Path] = []
    for source in sorted(chosen.path.rglob("*")):
        if not source.is_file() or source.name == MANIFEST_NAME:
            continue
        relative = source.relative_to(chosen.path)
        target = project.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        restored.append(target)

    if not quiet:
        print(f"  ripristinati {len(restored)} file da {chosen.stamp}")
    return RestoreResult(snapshot=chosen, restored=restored, safety=safety)


def prune(
    project: BookProject, keep: int, *, backup_dir: Path | None = None
) -> list[Snapshot]:
    """Tiene solo gli ultimi `keep` snapshot; restituisce quelli eliminati."""
    if keep < 1:
        raise ValueError("`keep` deve essere almeno 1.")
    snapshots = list_snapshots(project, backup_dir)
    removed = snapshots[:-keep] if len(snapshots) > keep else []
    for item in removed:
        shutil.rmtree(item.path)
    return removed


def usage(project: BookProject, backup_dir: Path | None = None) -> tuple[int, int]:
    """(numero di snapshot, byte occupati)."""
    snapshots = list_snapshots(project, backup_dir)
    return len(snapshots), sum(s.bytes for s in snapshots)

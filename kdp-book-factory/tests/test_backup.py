"""Test delle copie di sicurezza: snapshot, deduplicazione, ripristino, pulizia."""

import json
import tempfile
import unittest
from pathlib import Path

from kdpfactory import backup
from kdpfactory.models import BookProject, BookSpec


class BackupTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.backup_dir = root / "backup"
        self.project = BookProject(root / "books" / "libro")
        self.project.ensure_dirs()
        BookSpec(slug="libro", title="Libro di Prova").save(self.project.spec_path)
        self.project.chapter_path(1).write_text("# Uno\n\nTesto del primo capitolo.\n", "utf-8")
        (self.project.build_dir / "libro-interno.pdf").write_bytes(b"%PDF-1.4 finto")
        backup.configure(enabled=True, directory=self.backup_dir)

    def tearDown(self):
        backup.configure(enabled=True, directory=None)
        self.tmp.cleanup()

    def snap(self, reason="prova", **kwargs):
        return backup.snapshot(self.project, reason, quiet=True, **kwargs)


class TestSnapshot(BackupTestCase):
    def test_copia_manoscritto_build_e_scheda(self):
        result = self.snap("primo")
        self.assertIsNotNone(result)
        copiati = {
            str(p.relative_to(result.path))
            for p in result.path.rglob("*")
            if p.is_file() and p.name != backup.MANIFEST_NAME
        }
        self.assertIn("book.json", copiati)
        self.assertIn("manuscript/01.md", copiati)
        self.assertIn("build/libro-interno.pdf", copiati)

    def test_manifest_descrive_il_contenuto(self):
        result = self.snap("con manifest")
        manifest = json.loads((result.path / backup.MANIFEST_NAME).read_text(encoding="utf-8"))
        self.assertEqual(manifest["reason"], "con manifest")
        self.assertEqual(manifest["files"], result.files)
        self.assertTrue(all("sha256" in voce for voce in manifest["contenuto"]))

    def test_contenuto_identico_all_originale(self):
        result = self.snap()
        copia = result.path / "manuscript" / "01.md"
        self.assertEqual(
            copia.read_text(encoding="utf-8"),
            self.project.chapter_path(1).read_text(encoding="utf-8"),
        )

    def test_niente_copia_se_nulla_e_cambiato(self):
        self.assertIsNotNone(self.snap("primo"))
        self.assertIsNone(self.snap("secondo"), "snapshot duplicato di uno stato identico")

    def test_force_copia_comunque(self):
        self.snap("primo")
        self.assertIsNotNone(self.snap("forzato", force=True))
        self.assertEqual(len(backup.list_snapshots(self.project, self.backup_dir)), 2)

    def test_una_modifica_produce_un_nuovo_snapshot(self):
        self.snap("primo")
        self.project.chapter_path(1).write_text("# Uno\n\nTesto cambiato.\n", "utf-8")
        self.assertIsNotNone(self.snap("secondo"))

    def test_disattivabile(self):
        backup.configure(enabled=False, directory=self.backup_dir)
        self.assertIsNone(self.snap("niente"))
        self.assertEqual(backup.list_snapshots(self.project, self.backup_dir), [])

    def test_progetto_vuoto_non_produce_nulla(self):
        with tempfile.TemporaryDirectory() as tmp:
            vuoto = BookProject(Path(tmp) / "vuoto")
            vuoto.ensure_dirs()
            self.assertIsNone(backup.snapshot(vuoto, "vuoto", backup_dir=self.backup_dir))

    def test_impronta_cambia_col_contenuto(self):
        prima = backup.fingerprint(self.project)
        self.project.chapter_path(1).write_text("# Uno\n\nAltro testo.\n", "utf-8")
        self.assertNotEqual(prima, backup.fingerprint(self.project))


class TestRipristino(BackupTestCase):
    def test_riporta_il_testo_originale(self):
        originale = self.project.chapter_path(1).read_text(encoding="utf-8")
        primo = self.snap("buona stesura")
        self.project.chapter_path(1).write_text("# Uno\n\nVersione peggiore.\n", "utf-8")

        result = backup.restore(
            self.project, primo.stamp, backup_dir=self.backup_dir, quiet=True
        )
        self.assertEqual(self.project.chapter_path(1).read_text(encoding="utf-8"), originale)
        self.assertTrue(result.restored)

    def test_mette_al_sicuro_lo_stato_attuale(self):
        primo = self.snap("primo")
        self.project.chapter_path(1).write_text("# Uno\n\nDa non perdere.\n", "utf-8")
        result = backup.restore(
            self.project, primo.stamp, backup_dir=self.backup_dir, quiet=True
        )
        self.assertIsNotNone(result.safety)
        salvato = result.safety.path / "manuscript" / "01.md"
        self.assertIn("Da non perdere", salvato.read_text(encoding="utf-8"))

    def test_latest_prende_l_ultimo(self):
        self.snap("primo")
        self.project.chapter_path(1).write_text("# Uno\n\nSeconda versione.\n", "utf-8")
        self.snap("secondo")
        self.project.chapter_path(1).write_text("# Uno\n\nTerza versione.\n", "utf-8")
        backup.restore(self.project, "latest", backup_dir=self.backup_dir, quiet=True)
        self.assertIn("Seconda versione", self.project.chapter_path(1).read_text("utf-8"))

    def test_snapshot_inesistente(self):
        with self.assertRaises(FileNotFoundError):
            backup.restore(self.project, "20200101-000000", backup_dir=self.backup_dir, quiet=True)


class TestManutenzione(BackupTestCase):
    def test_prune_tiene_gli_ultimi(self):
        for index in range(4):
            self.project.chapter_path(1).write_text(f"# Uno\n\nVersione {index}.\n", "utf-8")
            self.snap(f"versione {index}")
        removed = backup.prune(self.project, 2, backup_dir=self.backup_dir)
        self.assertEqual(len(removed), 2)
        rimasti = backup.list_snapshots(self.project, self.backup_dir)
        self.assertEqual(len(rimasti), 2)
        self.assertEqual(rimasti[-1].reason, "versione 3")

    def test_prune_rifiuta_zero(self):
        with self.assertRaises(ValueError):
            backup.prune(self.project, 0, backup_dir=self.backup_dir)

    def test_usage(self):
        self.snap("uno")
        count, total = backup.usage(self.project, self.backup_dir)
        self.assertEqual(count, 1)
        self.assertGreater(total, 0)


if __name__ == "__main__":
    unittest.main()

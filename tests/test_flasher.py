import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import flasher


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'bootloader.bin').write_bytes(b'ESP')
        (self.root / 'app.bin').write_bytes(b'ESP')

    def manifest(self, text):
        (self.root / 'flash_args').write_text(text, encoding='utf-8')
        return flasher.read_manifest(self.root)

    def test_valid_manifest(self):
        args = self.manifest('--flash-mode dio --flash-freq 40m --flash-size 4MB\n0x1000 bootloader.bin\n0x10000 app.bin\n')
        self.assertIn('0x1000', args)
        self.assertIn(str((self.root / 'app.bin').resolve()), args)

    def test_old_esptool_flags_are_normalized(self):
        args = self.manifest('--flash_mode dio --flash_freq 80m\n0x1000 bootloader.bin')
        self.assertIn('--flash-mode', args)
        self.assertIn('--flash-freq', args)

    def test_unknown_flags_are_rejected(self):
        with self.assertRaises(ValueError):
            self.manifest('--erase-all 0x1000 app.bin')

    def test_missing_binary_is_rejected(self):
        with self.assertRaises(FileNotFoundError):
            self.manifest('0x1000 nonexistent.bin')

    def test_directory_escape_is_rejected(self):
        with self.assertRaises(ValueError):
            self.manifest('0x1000 ../somewhere.bin')

    def test_duplicate_offset_is_rejected(self):
        with self.assertRaises(ValueError):
            self.manifest('0x1000 app.bin 0x1000 bootloader.bin')

    def test_dry_run_does_not_use_hardware(self):
        self.manifest('0x1000 bootloader.bin')
        with patch.object(flasher, 'available_ports', side_effect=AssertionError('hardware accessed')):
            with io.StringIO() as output, contextlib.redirect_stdout(output):
                code = flasher.main(['--firmware-dir', str(self.root), '--dry-run'])
        self.assertEqual(code, 0)

    def test_manifest_cannot_be_outside_firmware(self):
        with self.assertRaises(ValueError):
            flasher.read_manifest(self.root, '../secrets')

    def test_empty_manifest_is_rejected(self):
        with self.assertRaises(ValueError):
            self.manifest('')


if __name__ == '__main__':
    unittest.main()

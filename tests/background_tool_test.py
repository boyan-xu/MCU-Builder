"""Behavior checks for the packaged background test runner; no board access."""
from pathlib import Path
import hashlib
import json
import runpy
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/test-mcu-in-background/scripts/mcu_test.py'


class BackgroundToolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='mcu runner spaces ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def run_config(self, config, *extra):
        path = self.root / 'project.json'
        path.write_text(json.dumps(config), encoding='utf-8')
        result = subprocess.run([sys.executable, '-B', str(SCRIPT), str(path), '--cache-dir', str(self.root / 'cache'), *extra], capture_output=True, text=True)
        return result, json.loads(result.stdout)

    def test_existing_command_runs_without_environment_install(self):
        code = self.root / 'case.py'
        code.write_text('assert 2 + 2 == 4\nprint("checked")\n')
        result, report = self.run_config({'version': 1, 'test': {'backend': 'command', 'command': [sys.executable, 'case.py'], 'inputs': ['case.py']}})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report['status'], 'passed')
        self.assertEqual(report['layer'], 'existing-command')
        self.assertIn('case.py', report['tested_files'])
        self.assertFalse((self.root / 'cache/arm-python').exists())
        self.assertIn('checked', Path(report['runs'][0]['log']).read_text())

    def test_ssd1306_png_has_real_buffer_pixels(self):
        with patch.object(sys, 'path', [str(SCRIPT.parent), *sys.path]):
            render = runpy.run_path(str(SCRIPT))['png_from_pages']
        data = render(bytes([1, 0]), 2, 8)
        self.assertEqual(data[:8], b'\x89PNG\r\n\x1a\n')
        payload = b''
        offset = 8
        while offset < len(data):
            length = struct.unpack('>I', data[offset:offset + 4])[0]
            kind = data[offset + 4:offset + 8]
            body = data[offset + 8:offset + 8 + length]
            checksum = struct.unpack('>I', data[offset + 8 + length:offset + 12 + length])[0]
            self.assertEqual(checksum, zlib.crc32(kind + body) & 0xffffffff)
            if kind == b'IDAT':
                payload += body
            offset += length + 12
        self.assertEqual(zlib.decompress(payload), b'\0\xff\0' + b'\0\0\0' * 7)
        with self.assertRaises(Exception):
            render(b'', 2, 8)

    def test_failed_command_and_timeout_are_not_passes(self):
        for command, expected in [([sys.executable, '-c', 'raise SystemExit(4)'], 'failed'), ([sys.executable, '-c', 'import time; time.sleep(5)'], 'timed_out')]:
            with self.subTest(expected=expected):
                result, report = self.run_config({'version': 1, 'test': {'backend': 'command', 'command': command, 'timeout': 0.1}})
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(report['status'], expected)

    def test_shell_strings_and_missing_sources_are_rejected(self):
        for test in [{'backend': 'command', 'command': 'echo unchecked'}, {'backend': 'arm-c', 'cpu': 'cortex-m3', 'sources': ['missing.c'], 'harness': 'test.c'}]:
            result, report = self.run_config({'version': 1, 'test': test})
            self.assertEqual(result.returncode, 2)
            self.assertEqual(report['status'], 'error')

    def test_unsupported_backend_is_clear(self):
        result, report = self.run_config({'version': 1, 'test': {'backend': 'whole-board-magic'}})
        self.assertEqual(result.returncode, 2)
        self.assertIn('backend', report['error'])

    def test_recorded_sample_is_bound_to_packaged_sources_and_runners(self):
        base = SCRIPT.parents[1]
        record = json.loads((base / 'references/verified-run.json').read_text())
        for name, digest in record['source_sha256'].items():
            self.assertEqual(hashlib.sha256((base / 'assets/example' / name).read_bytes().replace(b'\r\n', b'\n')).hexdigest(), digest)
        # Runner hashes identify the historical run, not a fresh pass of today's runner.
        self.assertEqual(record['date'], '2026-10-25')
        self.assertEqual(len(bytes.fromhex(record['runner_sha256'])), 32)
        self.assertEqual(len(bytes.fromhex(record['common_sha256'])), 32)
        self.assertFalse(record['physical_hardware_tested'])
        self.assertFalse(record['flash_preview']['hardware_accessed'])

    def test_report_cannot_replace_configuration_or_test_input(self):
        config = {'version': 1, 'test': {'backend': 'command', 'command': [sys.executable, '-c', 'pass'], 'inputs': ['data.json']}}
        (self.root / 'data.json').write_text('{"keep":true}')
        for name in ['project.json', 'data.json']:
            result, report = self.run_config(config, '--output', str(self.root / name))
            self.assertEqual(result.returncode, 2)
            self.assertEqual(report['status'], 'error')
        self.assertEqual((self.root / 'data.json').read_text(), '{"keep":true}')
        self.assertEqual(json.loads((self.root / 'project.json').read_text()), config)

    def test_arm_config_rejects_invalid_memory_and_capture_paths_before_setup(self):
        (self.root / 'code.c').write_text('int test_main(void){return 0;}')
        for extra in [{'memory': {'ram': {'size': 4096.5}}}, {'captures': [{'symbol': 'a', 'bytes': 1, 'output': '../out.bin'}]}, {'captures': [{'symbol': 'a', 'bytes': 1, 'output': 'build.log'}]}]:
            result, report = self.run_config({'version': 1, 'test': {'backend': 'arm-c', 'cpu': 'cortex-m3', 'sources': ['code.c'], 'harness': 'code.c', **extra}})
            self.assertEqual(result.returncode, 2)
            self.assertNotIn('Pinned ARM runtime', report['error'])

    def test_software_testing_does_not_accept_flash_configuration(self):
        marker = self.root / 'should-not-run'
        result, report = self.run_config({'version': 1, 'test': {'backend': 'command', 'command': [sys.executable, '-c', 'pass']}, 'flash': {'command': [sys.executable, '-c', f'open({str(marker)!r}, "w").write("bad")']}})
        self.assertEqual(result.returncode, 0)
        self.assertFalse(marker.exists())


if __name__ == '__main__':
    unittest.main()

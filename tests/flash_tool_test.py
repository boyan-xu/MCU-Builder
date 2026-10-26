"""Exercise flashing plans and fake vendor processes without connecting any device."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/flash-mcu-firmware/scripts'
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location('mcu_flash', SCRIPTS / 'mcu_flash.py')
FLASH = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FLASH)


class FlashTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='MCU flash test ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.binary = self.root / 'firmware image.bin'
        self.binary.write_bytes(b'\x01\x02\x03\x04')
        self.config_file = self.root / 'flash.json'
        self.cache = self.root / 'cache'
        self.config = {'version': 1, 'project': '.', 'tools': {'stm32_programmer': sys.executable}, 'flash': {
            'backend': 'stm32_programmer', 'target': 'test STM32 board only', 'probe_serial': 'TEST_SERIAL',
            'device_id': '0x410', 'firmware': self.binary.name, 'address': '0x08000000',
            'flash_start': '0x08000000', 'flash_size': 4096, 'erase_size': 1024}}

    def invoke(self, *flags):
        self.config_file.write_text(json.dumps(self.config), encoding='utf-8')
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = FLASH.main([str(self.config_file), '--cache-dir', str(self.cache), *flags])
        path = (self.config_file.parent / self.config.get('project', '.')).resolve() / '.mcu-results/flash-result.json'
        return code, json.loads(path.read_text()) if path.exists() else None

    def test_preview_runs_no_build_or_vendor_process(self):
        self.config['build'] = {'command': [sys.executable, '-c', "raise RuntimeError('must not run')"]}
        with patch.object(FLASH, 'run_process', side_effect=AssertionError('preview executed a process')):
            code, result = self.invoke()
        self.assertEqual(code, 0)
        self.assertEqual(result['status'], 'preview')
        self.assertFalse(result['hardware_accessed'])
        self.assertEqual(result['images'][0]['bytes'], 4)
        self.assertIn(str(self.binary), result['commands'][-1]['argv'])

    def test_execute_without_authorization_does_not_touch_tools(self):
        with patch.object(FLASH, 'run_process', side_effect=AssertionError('unapproved process')):
            code, _ = self.invoke('--execute')
        self.assertEqual(code, 2)

    def test_bad_ranges_missing_files_and_protected_erase_blocks_fail(self):
        with patch.object(FLASH, 'run_process', side_effect=AssertionError('invalid plan executed')):
            self.config['flash']['address'] = '0x08001000'
            self.assertEqual(self.invoke()[0], 2)
            self.config['flash']['address'] = '0x08000000'
            self.config['flash']['protected_ranges'] = [{'address': '0x080003FF', 'size': 1}]
            self.assertEqual(self.invoke()[0], 2)
            self.config['flash']['protected_ranges'] = []
            self.config['flash']['firmware'] = 'missing.bin'
            self.assertEqual(self.invoke()[0], 2)

    def test_wrong_stm32_identity_blocks_backup_and_write(self):
        def fake(argv, cwd, timeout, log):
            return {'returncode': 0, 'timed_out': False, 'log': str(log), 'tail': 'Device ID : 0x999', 'command': argv}
        with patch.object(FLASH, 'run_process', side_effect=fake) as called:
            code, result = self.invoke('--execute', '--authorized')
        self.assertEqual(code, 2)
        self.assertEqual(called.call_count, 1)
        self.assertIn('differs', result['error'])

    def test_short_backup_blocks_programming(self):
        calls = []
        def fake(argv, cwd, timeout, log):
            calls.append(argv)
            if '-u' in argv:
                Path(argv[-1]).write_bytes(b'short')
            return {'returncode': 0, 'timed_out': False, 'log': str(log), 'tail': 'Device ID : 0x410', 'command': argv}
        with patch.object(FLASH, 'run_process', side_effect=fake):
            code, result = self.invoke('--execute', '--authorized')
        self.assertEqual(code, 2)
        self.assertEqual(len(calls), 2)
        self.assertTrue(all('-d' not in call for call in calls))
        self.assertIn('Backup', result['error'])

    def test_vendor_timeout_stops_before_write(self):
        fake = {'returncode': -1, 'timed_out': True, 'log': 'fake-timeout.log', 'tail': 'timed out', 'command': []}
        with patch.object(FLASH, 'run_process', return_value=fake) as called:
            code, result = self.invoke('--execute', '--authorized')
        self.assertEqual(code, 2)
        self.assertEqual(called.call_count, 1)
        self.assertTrue(result['runs'][0]['timed_out'])
        self.assertEqual(result['status'], 'error')

    def test_output_cannot_replace_configuration(self):
        self.config_file.write_text(json.dumps(self.config), encoding='utf-8')
        before = self.config_file.read_bytes()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = FLASH.main([str(self.config_file), '--output', str(self.config_file)])
        self.assertEqual(code, 2)
        self.assertEqual(before, self.config_file.read_bytes())

    def test_stm32_success_keeps_backup_and_does_not_claim_physical_success(self):
        calls = []
        def fake(argv, cwd, timeout, log):
            calls.append(argv)
            if '-u' in argv:
                Path(argv[-1]).write_bytes(b'B' * 4096)
            return {'returncode': 0, 'timed_out': False, 'log': str(log), 'tail': 'Device ID : 0x410\nVerification OK', 'command': argv}
        with patch.object(FLASH, 'run_process', side_effect=fake):
            code, result = self.invoke('--execute', '--authorized')
        self.assertEqual(code, 0)
        self.assertEqual(result['status'], 'verified')
        self.assertEqual(result['physical_behavior'], 'not-tested')
        self.assertEqual(result['backup']['bytes'], 4096)
        self.assertIn('-v', calls[-1])
        self.assertNotIn('-rst', calls[-1])

    def test_esptool_v4_and_v5_real_fake_processes(self):
        self.config['tools'] = {'esptool_python': sys.executable}
        self.config['flash'] = {'backend': 'esptool', 'target': 'fake ESP test only', 'chip': 'esp32', 'port': 'COM99',
            'flash_start': 0, 'flash_size': 4096, 'images': [{'address': 0, 'file': self.binary.name}], 'expected_mac': 'aa:bb:cc:dd:ee:ff'}
        fake = '''import pathlib,sys
args=sys.argv[1:]
with open('fake-calls.txt','a') as f:f.write(' '.join(args)+'\\n')
if args==['version']:print('esptool vMAJOR.0.0');sys.exit(0)
if 'read-mac' in args or 'read_mac' in args:print('MAC: aa:bb:cc:dd:ee:ff')
if 'read-flash' in args or 'read_flash' in args:pathlib.Path(args[-1]).write_bytes(b'B'*int(args[-2]))
print('fake success')
'''
        for major in (4, 5):
            with self.subTest(major=major):
                project = self.root / f'esptool-v{major}'
                project.mkdir()
                (project / 'esptool.py').write_text(fake.replace('MAJOR', str(major)), encoding='utf-8')
                self.config['project'] = project.name
                self.config['flash']['images'][0]['file'] = '../' + self.binary.name
                code, result = self.invoke('--execute', '--authorized')
                self.assertEqual(code, 0, result)
                self.assertEqual(result['status'], 'verified')
                self.assertEqual(result['esptool_major'], major)
                self.assertEqual(result['physical_behavior'], 'not-tested')
                command = next(run['command'] for run in result['runs'] if run['stage'] == 'verify')
                self.assertIn('verify_flash' if major == 4 else 'verify-flash', command)
                self.assertIn('no_reset' if major == 4 else 'no-reset', command)

    def test_build_failure_does_not_access_hardware(self):
        self.config['build'] = {'command': [sys.executable, '-c', 'import sys;sys.exit(3)']}
        code, result = self.invoke('--execute', '--authorized')
        self.assertEqual(code, 2)
        self.assertFalse(result['hardware_accessed'])
        self.assertEqual(result['build']['returncode'], 3)

    def test_arduino_upload_only_is_not_verified_and_backup_is_rejected(self):
        self.config['tools'] = {'arduino_cli': sys.executable}
        self.config['flash'] = {'backend': 'arduino_cli', 'target': 'fake UNO', 'fqbn': 'arduino:avr:uno',
                                'port': 'COM99', 'firmware': self.binary.name, 'verify': False}
        fake = {'returncode': 0, 'timed_out': False, 'log': 'fake', 'tail': 'uploaded', 'command': []}
        with patch.object(FLASH, 'run_process', return_value=fake):
            code, result = self.invoke('--execute', '--authorized')
        self.assertEqual(code, 0)
        self.assertEqual(result['status'], 'uploaded')
        self.assertNotIn('--verify', result['commands'][0]['argv'])
        self.config['flash']['backup'] = True
        self.assertEqual(self.invoke()[0], 2)


if __name__ == '__main__':
    unittest.main()

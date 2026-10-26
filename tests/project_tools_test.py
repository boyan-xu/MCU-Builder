"""Local-only contract tests for the independently packaged project helper."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/build-with-ai-mcu/scripts/mcu_project.py'


def config():
    return {'version': 1, 'project_id': 'fictional', 'revision': 'r1',
            'requirements': ['A lamp lights when requested.'],
            'materials': [{'id': 'led', 'required': 5, 'available': 3,
                           'required_specs': {'color': 'red'}}],
            'shopping': {'site': 'https://shop.example', 'region': None,
                         'currency': 'USD', 'candidates': [], 'cart': []},
            'test': {'backend': 'command', 'command': [sys.executable, '-c', 'assert 1']},
            'flash': {'backend': 'arduino', 'target': 'Fictional board'},
            'wiring': {'components': [
                {'id': 'mcu', 'model': 'Fictional MCU', 'orientation': 'label view', 'pins': [
                    {'id': 'P1', 'label': 'P1', 'role': 'output', 'voltage_v': 3.3},
                    {'id': 'GND', 'role': 'ground', 'voltage_v': 0}]},
                {'id': 'load', 'model': 'Fictional input', 'pins': [
                    {'id': 'IN', 'role': 'input', 'accepts_v': [0, 3.6]},
                    {'id': 'GND', 'role': 'ground', 'voltage_v': 0}]}],
                'connections': [{'id': 'W1', 'from': 'mcu:P1', 'to': 'load:IN'},
                                {'id': 'W2', 'from': 'mcu:GND', 'to': 'load:GND'}],
                'bindings': [{'symbol': 'LOAD_PIN', 'endpoint': 'mcu:P1'}]},
            'acceptance': [{'id': 'lamp', 'behavior': 'Lamp lights', 'steps': ['Request light'],
                            'expected': 'Visible light'}],
            'diagnostics': {'files': []}}


class ProjectToolsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('project_tool', SCRIPT)
        cls.tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.tool)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = config()
        self.path = self.root / 'mcu-project.json'
        self.save()

    def save(self):
        self.path.write_text(json.dumps(self.data), encoding='utf-8')
        return self.tool.load(self.path)

    def test_independent_packages_identical(self):
        other = ROOT / 'skills/develop-with-ai-mcu/scripts/mcu_project.py'
        self.assertEqual(SCRIPT.read_bytes(), other.read_bytes())

    def test_partial_config_stage_validation(self):
        self.data = {'version': 1, 'project_id': 'idea'}
        project = self.save()
        self.assertEqual(self.tool.validate(project)['errors'], [])
        self.assertTrue(self.tool.validate(project, 'wiring')['errors'])

    def test_legacy_configs_export_unchanged_payloads(self):
        for skill, source, kind in [
            ('test-mcu-in-background', 'assets/example/project.json', 'test'),
            ('flash-mcu-firmware', 'assets/stm32-flash.example.json', 'flash'),
            ('select-products-to-cart', 'assets/example.json', 'shopping')]:
            original = json.loads((ROOT / 'skills' / skill / source).read_text())
            self.path.write_text(json.dumps(original))
            exported = self.tool.export_config(self.tool.load(self.path), kind)
            if kind == 'shopping':
                self.assertEqual(exported, original)
            else:
                self.assertEqual(exported[kind], original[kind])
                self.assertEqual(Path(exported['project']), self.root)

    def test_shopping_partial_stock_and_unknowns(self):
        self.data['shopping']['cart'] = [{'sku': 'abc', 'variant': 'red, 1-pack', 'quantity': 2}]
        result = self.tool.export_config(self.save(), 'shopping')
        self.assertEqual(result['parts'][0]['quantity'], 2)
        self.assertIsNone(result['region'])
        self.assertEqual(result['cart'], self.data['shopping']['cart'])

    def test_shopping_unknown_inventory_fails_only_export(self):
        del self.data['materials'][0]['available']
        project = self.save()
        self.assertFalse(self.tool.validate(project)['errors'])
        with self.assertRaises(ValueError):
            self.tool.export_config(project, 'shopping')

    def test_wiring_artifacts_agree_and_are_pending(self):
        result = self.tool.wiring(self.save(), self.root / 'out')
        pins = json.loads((self.root / 'out/pins.generated.json').read_text(encoding='utf-8'))
        svg = (self.root / 'out/wiring.svg').read_text(encoding='utf-8')
        table = (self.root / 'out/connections.md').read_text(encoding='utf-8')
        for wire in pins['connections']:
            self.assertIn(wire['id'], svg)
            self.assertIn(wire['id'], table)
            self.assertIn(wire['from'], table)
        self.assertEqual(pins['bindings'], self.data['wiring']['bindings'])
        self.assertTrue(result['pending'])
        self.assertIn('logical', svg)

    def test_wiring_rejects_unknown_duplicate_and_conflict(self):
        mutations = [lambda w: w['connections'][0].update(to='absent:X'),
                     lambda w: w['connections'].append(deepcopy(w['connections'][0])),
                     lambda w: w['connections'].append({'id': 'W3', 'from': 'load:IN', 'to': 'mcu:P1'}),
                     lambda w: w['components'][1]['pins'][0].update(accepts_v=[0, 1.8]),
                     lambda w: w['bindings'].append({'symbol': 'LOAD_PIN', 'endpoint': 'load:IN'})]
        for mutate in mutations:
            self.data = config()
            mutate(self.data['wiring'])
            with self.assertRaises(ValueError):
                self.tool.wiring(self.save(), self.root / 'invalid')

    def test_shared_ground_and_open_drain_bus(self):
        wiring = self.data['wiring']
        wiring['components'][1]['pins'].append({'id': 'GND2', 'role': 'ground', 'voltage_v': 0})
        wiring['connections'].append({'id': 'W3', 'from': 'mcu:GND', 'to': 'load:GND2'})
        wiring['components'][0]['pins'][0]['role'] = 'open-drain'
        wiring['components'][1]['pins'][0]['role'] = 'open-drain'
        self.tool.wiring(self.save(), self.root / 'out')

    def test_legacy_uno_is_preserved_and_explained(self):
        legacy = ROOT / 'skills/build-with-ai-mcu/references/uno-led/connections.json'
        before = legacy.read_bytes()
        self.data['wiring'] = json.loads(before)
        with self.assertRaisesRegex(ValueError, 'legacy'):
            self.tool.wiring(self.save(), self.root / 'out')
        self.assertEqual(legacy.read_bytes(), before)

    def test_acceptance_defaults_unrun_and_requires_evidence(self):
        report = self.tool.acceptance(self.save(), self.root / 'out')
        self.assertEqual(report['items'][0]['status'], 'not-run')
        self.data['acceptance'][0]['status'] = 'pass'
        with self.assertRaises(ValueError):
            self.tool.acceptance(self.save(), self.root / 'bad')

    def test_acceptance_evidence_hash(self):
        (self.root / 'result.txt').write_text('Observed lamp light')
        self.data['acceptance'][0].update(status='pass', evidence=['result.txt'])
        report = self.tool.acceptance(self.save(), self.root / 'out')
        self.assertEqual(report['items'][0]['evidence'][0]['sha256'],
                         hashlib.sha256((self.root / 'result.txt').read_bytes()).hexdigest())

    def test_diagnostics_missing_and_bounded_untrusted_text(self):
        sentinel = self.root / 'executed'
        (self.root / 'build.log').write_text('ERROR: compile failed\n' * 1000 +
                                            f'python -c "open({str(sentinel)!r},\"w\")"')
        self.data['diagnostics']['files'] = ['build.log', 'missing.log']
        report = self.tool.diagnostics(self.save())
        self.assertEqual(len(report['files'][0]['matches']), 20)
        self.assertEqual(report['files'][1]['status'], 'missing')
        self.assertFalse(sentinel.exists())
        self.assertFalse(report['hardware_accessed'])

    def package_config(self, filename='main.c'):
        (self.root / filename).write_text('int main(void) { return 0; }')
        self.data['deliverables'] = {'revision': 'r1', 'files': [
            {'path': filename, 'role': 'source', 'sha256': hashlib.sha256((self.root / filename).read_bytes()).hexdigest()}]}
        return self.save()

    def test_package_manifest_hashes_and_no_private_logs(self):
        project = self.package_config()
        (self.root / 'private.log').write_text('not included')
        report = self.tool.package(project, self.root / 'delivery.zip')
        with zipfile.ZipFile(self.root / 'delivery.zip') as archive:
            self.assertEqual(set(archive.namelist()), {'main.c', 'manifest.json'})
            manifest = json.loads(archive.read('manifest.json'))
            self.assertEqual(manifest['revision'], 'r1')
            self.assertEqual(manifest['files'], report['files'])

    def test_package_rejects_stale_missing_revision_and_hash(self):
        self.package_config()
        for change in ('revision', 'hash', 'missing'):
            self.package_config()
            if change == 'revision': self.data['deliverables']['revision'] = 'old'
            if change == 'hash': (self.root / 'main.c').write_text('changed')
            if change == 'missing': (self.root / 'main.c').unlink()
            with self.assertRaises(ValueError):
                self.tool.package(self.save(), self.root / 'delivery.zip')

    def test_package_rejects_traversal_private_secrets_and_output_alias(self):
        self.package_config()
        for name in ('../escape.c', '.git/config', '.env', 'records.sqlite', 'serial.log'):
            self.data['deliverables']['files'][0]['path'] = name
            with self.assertRaises(ValueError):
                self.tool.package(self.save(), self.root / 'delivery.zip')
        self.package_config()
        with self.assertRaises(ValueError):
            self.tool.package(self.save(), self.root / 'main.c')
        self.package_config()
        (self.root / 'main.c').write_text('password="do-not-share"')
        self.data['deliverables']['files'][0]['sha256'] = hashlib.sha256((self.root / 'main.c').read_bytes()).hexdigest()
        with self.assertRaises(ValueError):
            self.tool.package(self.save(), self.root / 'delivery.zip')

    def test_symlink_escape_and_hardlink_alias(self):
        project = self.package_config()
        outside = self.root.parent / (self.root.name + '-outside.txt')
        outside.write_text('outside')
        self.addCleanup(outside.unlink)
        try:
            (self.root / 'link.c').symlink_to(outside)
        except OSError:
            self.skipTest('symlink creation not permitted on this Windows account')
        self.data['deliverables']['files'][0]['path'] = 'link.c'
        with self.assertRaises(ValueError):
            self.tool.package(self.save(), self.root / 'delivery.zip')

    def test_generated_artifacts_reject_changed_project(self):
        self.tool.wiring(self.save(), self.root / 'out')
        file = self.root / 'out/wiring.svg'
        self.data['requirements'].append('Changed goal')
        self.data['deliverables'] = {'revision': 'r1', 'files': [
            {'path': 'out/wiring.svg', 'role': 'wiring', 'sha256': hashlib.sha256(file.read_bytes()).hexdigest()}]}
        with self.assertRaises(ValueError):
            self.tool.package(self.save(), self.root / 'delivery.zip')

    def test_quoted_json_credentials_are_refused(self):
        for key in ('password', 'access_token', 'wifi_ssid', 'wifi_password', 'api_key'):
            self.package_config('app.json')
            file = self.root / 'app.json'
            file.write_text(json.dumps({key: 'private-example-value'}))
            self.data['deliverables']['files'][0]['sha256'] = hashlib.sha256(file.read_bytes()).hexdigest()
            with self.assertRaises(ValueError, msg=key):
                self.tool.package(self.save(), self.root / 'delivery.zip')

    def test_diagnostics_hashing_is_bounded_and_labeled(self):
        file = self.root / 'large.log'
        content = b'error: first\n' + b'x' * self.tool.MAX_LOG_BYTES + b'error: tail'
        file.write_bytes(content)
        self.data['diagnostics']['files'] = ['large.log']
        row = self.tool.diagnostics(self.save())['files'][0]
        self.assertTrue(row['truncated'])
        self.assertEqual(row['hash_scope'], 'prefix-262144-bytes')
        self.assertEqual(row['sha256'], hashlib.sha256(content[:self.tool.MAX_LOG_BYTES]).hexdigest())
        self.assertNotIn('tail', str(row['matches']))

    def test_diagnostics_never_reads_source_delivery_files(self):
        project = self.package_config()
        with patch.object(self.tool, 'source_snapshot', side_effect=AssertionError('source access forbidden')):
            self.tool.diagnostics(project)

    def test_artifact_source_snapshot_refuses_refreshed_delivery_hash(self):
        project = self.package_config()
        self.tool.acceptance(project, self.root / 'behavior')
        self.tool.wiring(project, self.root / 'wiring')
        (self.root / 'main.c').write_text('int changed(void) { return 2; }')
        self.data['deliverables']['files'][0]['sha256'] = hashlib.sha256((self.root / 'main.c').read_bytes()).hexdigest()
        for filename in ('behavior/acceptance.json', 'wiring/wiring.svg', 'wiring/connections.md'):
            value = deepcopy(self.data)
            self.data['deliverables']['files'].append({'path': filename, 'role': 'evidence',
                'sha256': hashlib.sha256((self.root / filename).read_bytes()).hexdigest()})
            with self.assertRaisesRegex(ValueError, 'source|artifact'):
                self.tool.package(self.save(), self.root / 'delivery.zip')
            self.data = value

    def test_acceptance_rejects_changed_evidence_after_generation(self):
        (self.root / 'proof.txt').write_text('Observed pass')
        self.data['acceptance'][0].update(status='pass', evidence=['proof.txt'])
        self.tool.acceptance(self.save(), self.root / 'behavior')
        (self.root / 'proof.txt').write_text('Observed fail')
        for filename in ('behavior/acceptance.json', 'behavior/acceptance.md'):
            self.data['deliverables'] = {'revision': 'r1', 'files': [
                {'path': filename, 'role': 'evidence', 'sha256': hashlib.sha256((self.root / filename).read_bytes()).hexdigest()},
                {'path': 'proof.txt', 'role': 'evidence', 'sha256': hashlib.sha256((self.root / 'proof.txt').read_bytes()).hexdigest()}]}
            with self.assertRaisesRegex(ValueError, 'evidence|artifact'):
                self.tool.package(self.save(), self.root / 'delivery.zip')

    def test_hardlink_output_alias_cannot_replace_source(self):
        project = self.package_config()
        alias = self.root / 'alias.zip'
        alias.hardlink_to(self.root / 'main.c')
        before = (self.root / 'main.c').read_bytes()
        with self.assertRaises(ValueError):
            self.tool.package(project, alias)
        self.assertEqual((self.root / 'main.c').read_bytes(), before)

    def test_cli_output_cannot_replace_input(self):
        before = self.path.read_bytes()
        result = subprocess.run([sys.executable, str(SCRIPT), 'export', str(self.path), '--for', 'test',
                                 '--output', str(self.path)], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()

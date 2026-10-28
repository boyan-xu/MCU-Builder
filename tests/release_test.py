"""MCU Builder release contracts: local fictional inputs, no hardware/network/EDA."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from project_tools_test import config

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/build-with-ai-mcu/scripts/mcu_project.py'
PCB = ROOT / 'skills/design-pcb-with-ai'


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


class ReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = module(SCRIPT, 'release_helper')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='replication spaces ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = config()
        self.data['materials'][0].update(model='Fictional lamp input', purpose='Show state',
                                         search_text='Fictional red 3.3 V lamp input module 1 pack', price=None,
                                         preferred_specs={'mounting': 'header'})
        self.path = self.root / 'mcu-project.json'

    def save(self):
        self.path.write_text(json.dumps(self.data), encoding='utf-8')
        return self.tool.load(self.path)

    def file(self, name, role, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode('utf-8') if isinstance(content, str) else content)
        row = {'path': name, 'role': role, 'sha256': self.tool.digest(path.read_bytes())}
        self.data['deliverables']['files'].append(row)
        return row

    def refresh_generated_content(self):
        project = self.save()
        artifacts, _ = self.tool.wiring_artifacts(project)
        wires = dict(artifacts)
        bodies = {
            'tools': 'Use the exact Python version listed in START-HERE.md; acquire it from https://www.python.org/downloads/ and verify the version before building.',
            'build': 'From the extracted root, run `python build.py` to compile app.py into firmware.pyc; keep pins.py and assets/message.txt alongside it.',
            'target': 'This target is fictional host Python bytecode, not an MCU. No device or flash address exists and no flashing operation is appropriate.',
            'steps': 'From the extracted project root, run `python firmware.pyc`; retain pins.py and assets/message.txt, which the complete application reads.',
            'expected': 'The process exits successfully and prints exactly `fixture lamp 7` on standard output. This demonstrates only the host fixture behavior.',
            'failure': 'If Python reports an import, asset or version error, stop and compare extracted files against manifest hashes before rerunning the documented build.',
            'power': 'No electrical hardware is connected in this fictional host fixture. It consumes no board supply; no real voltage, current or polarity is tested.',
            'assembly': 'Keep app.py, pins.py, build.py and firmware.pyc at the root, with assets/message.txt in the assets subdirectory; do not connect physical parts.',
            'safety': 'This fixture does not authorize powering hardware or imply a real pin map. Any real build needs independently verified pin locations, supply and protection.',
            'proof': 'The actual observed host build and extracted run are separate from electrical, MCU simulation, flash and physical checks; all those hardware checks are not run.',
            'bundled': 'All project sources are bundled: app.py, pins.py and build.py, plus build.json and assets/message.txt; Python standard-library modules are external runtime inputs.',
            'external': 'Install only the exact Python runtime version listed in START-HERE.md from its official source if absent; no third-party package or online account is needed.',
            'license': (ROOT / 'LICENSE').read_text(encoding='utf-8'),
            'attribution': 'These fictional test sources are original fixture code under the supplied MIT text. Python retains its own license; no third-party application library is bundled.',
            'limits': 'The fixture tests packaging and host execution only. It cannot demonstrate a real MCU program, electrical safety, EDA layout, assembly fit or identical hardware behavior.',
        }
        for row in self.data['deliverables']['files']:
            role = row['role']
            path = self.root / row['path']
            content = None
            if role == 'materials':
                content = self.tool.parts(project)['artifact_text'].encode('utf-8')
            elif role in ('wiring-image', 'wiring-text'):
                content = wires['wiring.svg' if role == 'wiring-image' else 'connections.md']
            elif role in self.tool.GUIDE_SECTIONS and (role != 'dependencies' or path.suffix == '.md'):
                old = path.read_text(encoding='utf-8')
                if '<!-- mcu-section:' in old:
                    body = re.sub(r'<!-- mcu-project-sha256:[^\n]+ -->\n', '', old)
                else:
                    body = '\n\n'.join('<!-- mcu-section:' + key + ' -->\n' + bodies[key]
                                         for key in self.tool.GUIDE_SECTIONS[role]) + '\n'
                content = ('<!-- ' + self.tool.marker(project) + ' -->\n' + body).encode('utf-8')
            if content is not None:
                path.write_bytes(content)
                row['sha256'] = self.tool.digest(content)

    def final_fixture(self):
        for component in self.data['wiring']['components']:
            component['orientation'] = 'fictional label view, fixture only'
            for pin in component['pins']:
                pin.setdefault('voltage_v', 3.3)
                pin.setdefault('accepts_v', [0, 3.6])
        self.data['deliverables'] = {'revision': 'r1', 'files': []}
        self.file('app.py', 'source', 'from pins import VALUE\nfrom pathlib import Path\nprint(Path("assets/message.txt").read_text().strip(), VALUE)\n')
        self.file('pins.py', 'source', 'VALUE = 7\n')
        self.file('assets/message.txt', 'dependencies', 'fixture lamp\n')
        self.file('build.py', 'source', 'import py_compile\npy_compile.compile("app.py", cfile="firmware.pyc", dfile="app.py", doraise=True)\n')
        self.file('build.json', 'build-config', '{"target":"fictional Python bytecode, not real MCU firmware","entry":"app.py"}\n')
        self.file('dependencies.md', 'dependencies', 'Python standard library only. pins.py and assets/message.txt are bundled.\n')
        for role in sorted(self.tool.FINAL_ROLES - {'source', 'build-config', 'dependencies', 'evidence', 'wiring-image', 'wiring-text'}):
            content = (self.tool.parts(self.save())['text'] if role == 'materials' else
                       'Fictional host fixture only; no real electrical or hardware proof.\n'
                       'Build: python build.py. Run: python firmware.pyc from this directory.\n'
                       'Power/assembly: no hardware. Flash: not applicable to host bytecode.\n'
                       'Acceptance: output fixture lamp 7. Python version must match the toolchain.\n'
                       'License: MIT fixture. No third-party libraries.\n')
            self.file(role + '.md', role, content)
        run = subprocess.run([sys.executable, 'build.py'], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.file('firmware.pyc', 'firmware', (self.root / 'firmware.pyc').read_bytes())
        self.tool.wiring(self.save(), self.root / 'wiring')
        for name, role in [('wiring/wiring.svg', 'wiring-image'), ('wiring/connections.md', 'wiring-text')]:
            self.data['deliverables']['files'].append({'path': name, 'role': role,
                                                      'sha256': self.tool.digest((self.root / name).read_bytes())})
        self.refresh_generated_content()
        rows = self.data['deliverables']['files']
        tools = [{'name': 'Python', 'version': '.'.join(map(str, sys.version_info[:3])),
                  'official_url': 'https://www.python.org/downloads/', 'setup': 'build-guide.md'}]
        spec = {'revision': 'r1', 'critical_unknowns': [], 'firmware_required': True, 'used_resources': [],
                'required_inputs': [r['path'] for r in rows if r['role'] in {'source', 'build-config', 'dependencies'}],
                'include_dirs': [], 'toolchain': tools, 'external_prerequisites': [],
                'essential_facts': {'parts': ['materials.md'], 'pins': ['wiring/connections.md'],
                                    'power': ['power-assembly.md'], 'build': ['build-guide.md'], 'assembly': ['power-assembly.md']},
                'build_evidence': 'build-proof.json',
                'proof_status': {'build': 'passed', 'logic': 'not-run', 'simulation': 'not-applicable',
                                 'electrical': 'not-applicable', 'flash': 'not-run', 'physical': 'not-run'}}
        self.data['deliverables']['reproducibility'] = spec
        proof = {'status': 'passed', 'revision': 'r1', 'config_sha256': self.save()['config_sha256'],
                 'input_sha256': {r['path']: r['sha256'] for r in rows if r['path'] in spec['required_inputs']},
                 'firmware_sha256': {r['path']: r['sha256'] for r in rows if r['role'] == 'firmware'},
                 'toolchain': tools, 'command': 'python build.py'}
        self.file('build-proof.json', 'evidence', json.dumps(proof))
        return self.save()

    def test_numbered_list_unknown_platform_one_offer_and_search_specs(self):
        self.data['shopping']['site'] = None
        result = self.tool.parts(self.save())
        self.assertTrue(result['text'].startswith('1. Fictional lamp input'))
        for expected in ('Required: 5', 'owned: 3', 'missing: 2', 'Unknown estimate', 'Search (copy):', '1 pack'):
            self.assertIn(expected, result['text'])
        self.assertEqual(result['text'].count('Would you like'), 1)
        self.assertFalse(result['cart_mutated'])
        self.data['shopping']['cart_offer'] = result['cart_offer']
        self.assertNotIn('Would you like', self.tool.parts(self.save())['text'])
        self.data['shopping']['cart_offer'] = 'declined'
        self.assertNotIn('Would you like', self.tool.parts(self.save())['text'])
        run = subprocess.run([sys.executable, '-B', str(SCRIPT), 'parts', str(self.path),
                              '--output', str(self.root / 'bom.md')], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual((self.root / 'bom.md').read_bytes(), self.tool.parts(self.save())['artifact_text'].encode('utf-8'))

    def test_accepted_offer_only_asks_unknown_platform_and_reuses_known(self):
        self.data['shopping'].update(cart_offer='accepted', site=None)
        result = self.tool.parts(self.save())
        self.assertIn('Which shopping website', result['text'])
        self.assertIn('no checkout, order, payment or subscription', result['text'])
        self.data['shopping']['site'] = 'https://shop.example'
        result = self.tool.parts(self.save())
        self.assertNotIn('Which shopping website', result['text'])
        self.assertEqual(result['site'], 'https://shop.example')

    def test_parts_cost_needs_evidence_and_export_preserves_preferences(self):
        self.data['materials'][0]['price'] = {'estimated_missing_total': 4, 'currency': 'USD', 'source': 'fictional quote', 'observed_at': '2026-10-26'}
        project = self.save()
        self.assertIn('4 USD; evidence: fictional quote', self.tool.parts(project)['text'])
        exported = self.tool.export_config(project, 'shopping')
        self.assertEqual(exported['parts'][0]['preferred_specs'], {'mounting': 'header'})
        self.assertEqual(exported['parts'][0]['quantity'], 2)
        self.assertEqual(self.tool.export_config({'data': exported}, 'shopping'), exported)
        del self.data['materials'][0]['price']['source']
        with self.assertRaises(ValueError):
            self.tool.parts(self.save())

    def test_final_zip_portable_unpacked_rebuild_and_every_hash_readback(self):
        project = self.final_fixture()
        output = self.root / 'complete.zip'
        report = self.tool.package(project, output, True)
        self.assertEqual(report['status'], 'reproducible_artifacts')
        self.assertEqual(report['reproducibility']['proof_status']['physical'], 'not-run')
        with tempfile.TemporaryDirectory(prefix='portable unpack ') as target:
            target = Path(target)
            with zipfile.ZipFile(output) as archive:
                self.assertIsNone(archive.testzip())
                archive.extractall(target)
            manifest = json.loads((target / 'manifest.json').read_bytes())
            self.assertEqual(set(p.name for p in target.glob('*.zip')), set())
            for row in manifest['files']:
                content = (target / row['path']).read_bytes()
                self.assertEqual(hashlib.sha256(content).hexdigest(), row['sha256'])
                self.assertEqual(len(content), row['bytes'])
            start = (target / 'START-HERE.md').read_text(encoding='utf-8')
            self.assertIn('https://www.python.org/downloads/', start)
            self.assertIn('build-guide.md', start)
            # The original tree is unavailable to the clean extracted build/run.
            shutil.rmtree(self.root / 'assets')
            for args in ([sys.executable, 'build.py'], [sys.executable, 'firmware.pyc']):
                run = subprocess.run(args, cwd=target, capture_output=True, text=True)
                self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(run.stdout.strip(), 'fixture lamp 7')

    def test_every_required_final_category_and_used_resource_is_enforced(self):
        self.final_fixture()
        original = deepcopy(self.data)
        for role in self.tool.FINAL_ROLES | {'firmware'}:
            self.data = deepcopy(original)
            self.data['deliverables']['files'] = [r for r in self.data['deliverables']['files'] if r['role'] != role]
            with self.assertRaises(ValueError, msg=role):
                self.tool.package(self.save(), self.root / 'missing.zip', True)
            self.assertFalse((self.root / 'missing.zip').exists())
        for resource in ('pcb', 'mechanical', 'print'):
            self.data = deepcopy(original)
            self.data['deliverables']['reproducibility']['used_resources'] = [resource]
            with self.assertRaisesRegex(ValueError, 'missing final artifact roles'):
                self.tool.package(self.save(), self.root / 'resource.zip', True)

    def test_essential_unknowns_or_stale_build_inputs_block_final(self):
        self.final_fixture()
        original = deepcopy(self.data)
        for change in ('critical', 'pin', 'orientation', 'evidence', 'toolchain', 'input', 'resource-fact'):
            self.data = deepcopy(original)
            spec = self.data['deliverables']['reproducibility']
            if change == 'critical': spec['critical_unknowns'] = ['power supply unknown']
            if change == 'pin': del self.data['wiring']['components'][0]['pins'][0]['accepts_v']
            if change == 'orientation': self.data['wiring']['components'][0]['orientation'] = None
            if change == 'evidence': spec['essential_facts']['power'] = []
            if change == 'toolchain': spec['toolchain'][0]['version'] = 'changed'
            if change == 'input': spec['required_inputs'].append('missing-private-file.h')
            if change == 'resource-fact': spec['essential_facts']['parts'] = ['../outside.md']
            with self.assertRaises(ValueError, msg=change):
                self.tool.package(self.save(), self.root / 'bad.zip', True)

    def test_updated_delivery_hash_cannot_reuse_old_build_witness(self):
        self.final_fixture()
        for row in self.data['deliverables']['files']:
            if row['path'] == 'app.py':
                (self.root / 'app.py').write_text('print("changed")\n')
                row['sha256'] = self.tool.digest((self.root / 'app.py').read_bytes())
        # Refresh current BOM/wiring/guide provenance, while retaining the genuinely old build witness.
        self.refresh_generated_content()
        with self.assertRaisesRegex(ValueError, 'build evidence'):
            self.tool.package(self.save(), self.root / 'bad.zip', True)

    def test_missing_quoted_header_or_omitted_asset_blocks_final(self):
        self.final_fixture()
        row = self.file('driver.c', 'source', '#include "missing.h"\nint driver(void) { return 0; }\n')
        self.data['deliverables']['reproducibility']['required_inputs'].append(row['path'])
        self.refresh_generated_content()
        with self.assertRaisesRegex(ValueError, 'quoted include'):
            # Exercise this gate directly; normal packaging also refuses stale generated wiring first.
            rows = self.data['deliverables']['files']
            self.tool.reproducibility(self.save(), rows, [(r['path'], (self.root / r['path']).read_bytes()) for r in rows])
        self.data['deliverables']['files'].pop()
        self.data['deliverables']['reproducibility']['required_inputs'].pop()
        self.refresh_generated_content()
        self.data['deliverables']['files'] = [r for r in self.data['deliverables']['files'] if r['path'] != 'assets/message.txt']
        with self.assertRaisesRegex(ValueError, 'required input'):
            self.tool.package(self.save(), self.root / 'bad.zip', True)

    def test_basic_package_stays_draft_and_final_secret_overwrite_guards_apply(self):
        self.final_fixture()
        report = self.tool.package(self.save(), self.root / 'draft.zip')
        self.assertEqual(report['status'], 'draft_unverified')
        self.assertIsNone(report['reproducibility'])
        with self.assertRaises(ValueError):
            self.tool.package(self.save(), self.root / 'draft.zip', True)
        self.file('credentials.txt', 'limits', 'api_key = private-example-value')
        with self.assertRaisesRegex(ValueError, 'credential'):
            self.tool.package(self.save(), self.root / 'bad.zip', True)

    def test_final_cli_and_helper_have_no_process_execution_api(self):
        self.final_fixture()
        run = subprocess.run([sys.executable, '-B', str(SCRIPT), 'package', str(self.path), '--reproducible',
                              '--output', str(self.root / 'cli.zip')], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)['status'], 'reproducible_artifacts')

    def test_generated_metadata_secrets_reject_before_any_archive_write(self):
        self.final_fixture()
        original = deepcopy(self.data)
        original_payloads = {r['path']: (self.root / r['path']).read_bytes() for r in original['deliverables']['files']}
        for location in ('prerequisite', 'extra', 'manifest-identity', 'start-filename'):
            self.data = deepcopy(original)
            for name, content in original_payloads.items():
                (self.root / name).write_bytes(content)
            spec = self.data['deliverables']['reproducibility']
            if location == 'prerequisite':
                spec['external_prerequisites'] = [{'name': 'Vendor tool', 'version': '1.0',
                    'official_url': 'https://vendor.example/download?api_key=private-example-value', 'setup': 'build-guide.md'}]
            elif location == 'extra':
                spec['private_note'] = {'api_key': 'private-example-value'}
            elif location == 'manifest-identity':
                self.data['project_id'] = 'api_key=private-example-value'
            else:
                # This metadata is absent from the raw reproducibility object, and reaches the generated START-HERE bytes.
                self.file('api_key=private-example-value.svg', 'wiring', '<svg xmlns="http://www.w3.org/2000/svg"/>')
            project = self.save()
            # Changing identity normally also invalidates artifacts; regenerate them and the build witness to reach the output guard.
            if location == 'manifest-identity':
                self.refresh_generated_content()
                proof_path = self.root / 'build-proof.json'
                proof = json.loads(proof_path.read_bytes())
                proof['config_sha256'] = project['config_sha256']
                proof['input_sha256'] = {r['path']: r['sha256'] for r in self.data['deliverables']['files'] if r['path'] in spec['required_inputs']}
                proof_path.write_text(json.dumps(proof), encoding='utf-8')
                next(r for r in self.data['deliverables']['files'] if r['path'] == 'build-proof.json')['sha256'] = self.tool.digest(proof_path.read_bytes())
            with patch.object(self.tool.tempfile, 'NamedTemporaryFile', side_effect=AssertionError('archive staging started')):
                with patch.object(self.tool.zipfile, 'ZipFile', side_effect=AssertionError('archive write started')):
                    with self.assertRaisesRegex(ValueError, 'credential'):
                        self.tool.package(self.save(), self.root / 'secret.zip', True)
            self.assertFalse((self.root / 'secret.zip').exists())

    def test_normal_metadata_is_sanitized_and_round_trips(self):
        self.final_fixture()
        spec = self.data['deliverables']['reproducibility']
        spec['external_prerequisites'] = [{'name': 'Fictional prerequisite', 'version': '1.0',
            'official_url': 'https://vendor.example/download', 'setup': 'build-guide.md', 'private_unneeded_note': 'not part of the contract'}]
        spec['unreviewed_extra'] = 'not package content'
        self.tool.package(self.save(), self.root / 'normal.zip', True)
        with zipfile.ZipFile(self.root / 'normal.zip') as archive:
            manifest = json.loads(archive.read('manifest.json'))
            self.assertNotIn('unreviewed_extra', manifest['reproducibility'])
            self.assertNotIn('private_unneeded_note', manifest['reproducibility']['external_prerequisites'][0])
            self.assertEqual(manifest['reproducibility']['external_prerequisites'][0]['version'], '1.0')
            self.assertIn(b'https://vendor.example/download', archive.read('START-HERE.md'))

    def test_each_required_bom_wire_and_guide_rejects_placeholder_independently(self):
        self.final_fixture()
        for row in self.data['deliverables']['files']:
            if row['role'] not in {'materials', 'wiring-image', 'wiring-text', *self.tool.GUIDE_SECTIONS}:
                continue
            path = self.root / row['path']
            before, expected_hash = path.read_bytes(), row['sha256']
            path.write_bytes(b'TODO')
            row['sha256'] = self.tool.digest(b'TODO')
            with self.assertRaisesRegex(ValueError, 'placeholder', msg=row['path']):
                self.tool.package(self.save(), self.root / 'placeholder.zip', True)
            self.assertFalse((self.root / 'placeholder.zip').exists())
            path.write_bytes(before)
            row['sha256'] = expected_hash

    def test_valid_but_mismatched_bom_or_wiring_cannot_drop_markers_to_pass(self):
        self.final_fixture()
        for row in self.data['deliverables']['files']:
            if row['role'] not in {'materials', 'wiring-image', 'wiring-text'}:
                continue
            path = self.root / row['path']
            before, expected_hash = path.read_bytes(), row['sha256']
            value = before.decode('utf-8')
            value = re.sub(r'<!-- mcu-project-sha256:.*?-->|<metadata>.*?</metadata>', '', value, flags=re.S)
            value = value.replace('Fictional lamp input', 'Different obsolete lamp').replace('mcu:P1', 'mcu:OLD')
            path.write_text(value, encoding='utf-8')
            row['sha256'] = self.tool.digest(path.read_bytes())
            with self.assertRaisesRegex(ValueError, 'final materials|final wiring', msg=row['role']):
                self.tool.package(self.save(), self.root / 'mismatch.zip', True)
            self.assertFalse((self.root / 'mismatch.zip').exists())
            path.write_bytes(before)
            row['sha256'] = expected_hash

    def test_guide_sections_allow_localized_prose_and_supplemental_physical_images(self):
        self.final_fixture()
        row = next(r for r in self.data['deliverables']['files'] if r['role'] == 'use-guide')
        guide = '<!-- ' + self.tool.marker(self.save()) + ' -->\n'
        text = '从解压后的工程根目录运行完整程序，保留全部源文件和素材；观察输出结果，并对照验收说明检查预期行为。'
        guide += '\n'.join('<!-- mcu-section:' + key + ' -->\n' + text for key in self.tool.GUIDE_SECTIONS['use-guide'])
        (self.root / row['path']).write_bytes(guide.encode('utf-8'))
        row['sha256'] = self.tool.digest(guide.encode('utf-8'))
        self.file('physical-orientation.svg', 'wiring', '<svg xmlns="http://www.w3.org/2000/svg"><text x="0" y="20">Supplemental fictional physical label view; never a real pin reference</text></svg>')
        self.assertEqual(self.tool.package(self.save(), self.root / 'localized.zip', True)['status'], 'reproducible_artifacts')

    def test_guide_contract_rejects_missing_short_or_placeholder_sections(self):
        self.final_fixture()
        row = next(r for r in self.data['deliverables']['files'] if r['role'] == 'use-guide')
        prefix = '<!-- ' + self.tool.marker(self.save()) + ' -->\n'
        for kind in ('missing', 'short', 'placeholder'):
            sections = []
            for key in self.tool.GUIDE_SECTIONS['use-guide']:
                if kind == 'missing' and key == 'steps':
                    continue
                body = 'Run the complete extracted application and compare its result with the acceptance criteria.'
                if key == 'steps':
                    body = 'Run it.' if kind == 'short' else 'TODO: write the actual complete project operation procedure before final delivery.'
                sections.append('<!-- mcu-section:' + key + ' -->\n' + body)
            content = (prefix + '\n'.join(sections)).encode('utf-8')
            (self.root / row['path']).write_bytes(content)
            row['sha256'] = self.tool.digest(content)
            with self.assertRaisesRegex(ValueError, 'non-substantive final guide section'):
                self.tool.package(self.save(), self.root / 'guide.zip', True)
            self.assertFalse((self.root / 'guide.zip').exists())


class PcbBriefTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = module(PCB / 'scripts/pcb_brief.py', 'pcb_brief_helper')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pcb brief ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = json.loads((PCB / 'assets/pcb-brief.json').read_text())

    def ready(self):
        self.data['critical_unknowns'] = []
        self.data['software'] = {'name': 'Fictional usable EDA', 'version': '1.0', 'connection_usable': True}
        self.data['agents_available'] = True
        self.data['parts'][0].update(footprint='Fixture:J1', footprint_source='https://example.org/fictional-drawing')
        return self.data

    def test_no_software_is_draft_never_finished(self):
        result = self.tool.check(self.data, self.root)
        self.assertEqual(result['status'], 'draft')
        self.assertFalse(result['finished_pcb'])
        self.ready()
        self.data['software']['connection_usable'] = False
        self.assertEqual(self.tool.check(self.data, self.root)['status'], 'draft')

    def test_main_agent_can_use_checked_brief_without_children(self):
        for agents in (False, None):
            self.ready()
            if agents is None:
                self.data.pop('agents_available')
            else:
                self.data['agents_available'] = agents
            result = self.tool.check(self.data, self.root)
            self.assertEqual(result['status'], 'ready-for-eda')
            self.assertFalse(result['finished_pcb'])
            self.assertEqual(result['checks'], [])

    def test_existing_software_and_checked_brief_only_enable_eda_work(self):
        result = self.tool.check(self.ready(), self.root)
        self.assertEqual(result['status'], 'ready-for-eda')
        self.assertFalse(result['finished_pcb'])
        self.assertEqual(result['checks'], [])
        self.assertTrue(result['model_gaps'])

    def test_unknown_footprint_process_pin_or_supply_stays_draft(self):
        original = deepcopy(self.ready())
        for change in ('footprint', 'process', 'pin', 'power'):
            self.data = deepcopy(original)
            if change == 'footprint': self.data['parts'][0]['footprint_source'] = None
            if change == 'process': self.data['fabrication']['process'] = None
            if change == 'pin': self.data['nets'][0]['endpoints'] = ['J1:DOES-NOT-EXIST']
            if change == 'power': self.data['supply']['voltage_v'] = None
            self.assertEqual(self.tool.check(self.data, self.root)['status'], 'draft')

    def test_pass_needs_actual_revision_bound_report_and_model_gaps_limit_assembly(self):
        self.ready()
        path = self.root / 'erc.txt'
        self.data['checks'] = [{'kind': 'erc', 'status': 'passed', 'revision': self.data['revision'],
                                'path': 'erc.txt', 'sha256': '0' * 64}]
        with self.assertRaises(ValueError):
            self.tool.check(self.data, self.root)
        path.write_text('Fictional report: checked two explicit connector nets; no circuit simulation or hardware.')
        self.data['checks'][0]['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(self.tool.check(self.data, self.root)['checks'][0]['status'], 'passed')
        self.data['checks'][0]['kind'] = 'assembly'
        with self.assertRaisesRegex(ValueError, 'Model gaps'):
            self.tool.check(self.data, self.root)
        self.data['checks'][0]['status'] = 'limited'
        self.assertEqual(self.tool.check(self.data, self.root)['checks'][0]['status'], 'limited')
        path.write_text('Changed report')
        with self.assertRaisesRegex(ValueError, 'Stale'):
            self.tool.check(self.data, self.root)

    def test_report_path_escape_and_false_revision_rejected(self):
        self.ready()
        self.data['checks'] = [{'kind': 'export-reopen', 'status': 'passed', 'revision': 'other',
                                'path': '../private.txt', 'sha256': '0' * 64}]
        with self.assertRaises(ValueError):
            self.tool.check(self.data, self.root)

    def test_net_names_and_endpoint_ownership_are_unique(self):
        original = deepcopy(self.ready())
        for change in ('two-nets', 'same-name', 'same-endpoint'):
            self.data = deepcopy(original)
            if change == 'two-nets': self.data['nets'][1]['endpoints'].append('J1:VCC')
            if change == 'same-name': self.data['nets'][1]['name'] = 'VCC'
            if change == 'same-endpoint': self.data['nets'][0]['endpoints'].append('J1:VCC')
            self.assertEqual(self.tool.check(self.data, self.root)['status'], 'draft', change)
        self.data = deepcopy(original)
        self.data['parts'][0]['pins'].append('SENSE')
        self.data['nets'][0]['endpoints'].append('J1:SENSE')
        self.assertEqual(self.tool.check(self.data, self.root)['status'], 'ready-for-eda')

    def test_sixth_skill_is_standalone_copy_runnable(self):
        standalone = self.root / 'installed skill'
        shutil.copytree(PCB, standalone)
        run = subprocess.run([sys.executable, '-B', str(standalone / 'scripts/pcb_brief.py'),
                              str(standalone / 'assets/pcb-brief.json')], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout)
        self.assertEqual(result['status'], 'draft')
        self.assertFalse(result['finished_pcb'])


if __name__ == '__main__':
    unittest.main()

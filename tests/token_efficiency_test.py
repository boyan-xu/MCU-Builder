"""Compact views keep real current evidence accessible; local fake tools only."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'skills/build-with-ai-mcu/scripts/mcu_project.py'
RUNNER = ROOT / 'skills/test-mcu-in-background/scripts/mcu_test.py'
FLASH = ROOT / 'skills/flash-mcu-firmware/scripts/mcu_flash.py'


def module(path):
    spec = importlib.util.spec_from_file_location(path.stem + '_compact_test', path)
    result = importlib.util.module_from_spec(spec)
    with patch.object(sys, 'path', [str(path.parent), *sys.path]):
        spec.loader.exec_module(result)
    return result


class CompactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='MCU compact ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = self.root / 'project.json'
        self.project = module(PROJECT)
        self.data = {'version': 1, 'project_id': 'fake', 'revision': 'r1'}

    def save(self):
        self.config.write_text(json.dumps(self.data), encoding='utf-8')
        return self.project.load(self.config)

    def runner(self, *flags):
        self.save()
        run = subprocess.run([sys.executable, '-B', str(RUNNER), str(self.config), '--cache-dir',
                              str(self.root / 'cache'), *flags], capture_output=True, text=True, timeout=15)
        return run, json.loads(run.stdout)

    def test_default_and_summary_keep_same_facts_and_full_report(self):
        source = self.root / 'logic.py'
        source.write_text('print("checked")\n')
        self.data['test'] = {'backend': 'command', 'command': [sys.executable, 'logic.py'], 'inputs': ['logic.py']}
        original, full = self.runner()
        compact, summary = self.runner('--summary')
        saved = json.loads(Path(summary['report']).read_text())
        self.assertEqual((original.returncode, compact.returncode), (0, 0))
        self.assertIn('runs', full)
        self.assertNotIn('runs', summary)
        for field in ('status', 'layer', 'config_sha256', 'tested_files', 'limits'):
            self.assertEqual(full[field], saved[field])
        self.assertEqual(summary['config_sha256'], hashlib.sha256(self.config.read_bytes()).hexdigest())
        self.assertEqual(summary['processes'], {'recorded': 1, 'completed': 1, 'succeeded': 1, 'failed': 0, 'timed_out': 0})
        self.assertEqual(summary['logs'], [saved['runs'][0]['log']])
        self.assertIn('checked', Path(summary['logs'][0]).read_text())

    def test_failure_timeout_and_early_error_have_accessible_context(self):
        for code, expected in [('print("early decisive line"); print("x"*12000); raise SystemExit(3)', 'failed'),
                               ('import time; print("before timeout", flush=True); time.sleep(5)', 'timed_out')]:
            self.data['test'] = {'backend': 'command', 'command': [sys.executable, '-c', code], 'timeout': 0.2}
            run, summary = self.runner('--summary')
            self.assertEqual(run.returncode, 1)
            self.assertEqual(summary['status'], expected)
            report = json.loads(Path(summary['report']).read_text())
            self.assertEqual(report['runs'][0]['timed_out'], expected == 'timed_out')
            raw = Path(summary['logs'][0]).read_text()
            if expected == 'failed':
                self.assertIn('early decisive line', raw)
                self.assertNotIn('early decisive line', summary.get('excerpt', ''))
            else:
                self.assertIn('before timeout', raw)
        self.data['test'] = {'backend': 'command', 'command': ['tool:python', '-c', 'pass']}
        self.data['tools'] = {'python': 'missing-tool'}
        run, summary = self.runner('--summary')
        self.assertEqual(run.returncode, 2)
        self.assertEqual(summary['status'], 'error')
        self.assertEqual(summary['processes']['completed'], 0)
        self.assertEqual(json.loads(Path(summary['report']).read_text(encoding='utf-8'))['status'], 'error')

    def test_unstartable_process_log_and_old_pass_are_not_lost_or_reused(self):
        self.data['test'] = {'backend': 'command', 'command': [sys.executable, '-c', 'pass']}
        self.runner('--summary')
        self.data['test']['command'] = [str(self.root / 'nonexistent.exe')]
        run, summary = self.runner('--summary')
        self.assertEqual(run.returncode, 2)
        self.assertEqual(summary['status'], 'error')
        self.assertEqual(summary['processes']['recorded'], 0)
        self.assertTrue(all(Path(log).is_file() for log in summary['logs']))
        self.assertTrue(summary['logs'])
        self.assertEqual(json.loads(Path(summary['report']).read_text(encoding='utf-8'))['status'], 'error')
        untouched = self.config.read_bytes()
        _, summary = self.runner('--summary', '--output', str(self.config))
        self.assertIsNone(summary['report'])
        self.assertEqual(self.config.read_bytes(), untouched)
        blocked = self.root / 'blocked'
        blocked.write_text('keep')
        _, summary = self.runner('--summary', '--output', str(blocked / 'report.json'))
        self.assertIsNone(summary['report'])
        self.assertEqual(summary['status'], 'error')

    def test_flash_default_preview_and_summary_preserve_report_and_rights(self):
        flash = module(FLASH)
        binary = self.root / 'image.bin'
        binary.write_bytes(b'fake firmware')
        self.data.update(tools={'arduino_cli': sys.executable}, flash={
            'backend': 'arduino_cli', 'target': 'fake board', 'port': 'COM7',
            'fqbn': 'fake:fake:fake', 'firmware': 'image.bin'})
        self.save()
        def invoke(*flags):
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = flash.main([str(self.config), '--cache-dir', str(self.root / 'cache'), *flags])
            return code, json.loads(out.getvalue() or err.getvalue())
        with patch.object(flash, 'run_process', side_effect=AssertionError('preview must not run tools')):
            code, full = invoke()
            _, summary = invoke('--summary')
            self.assertEqual(code, 0)
            self.assertEqual(set(full), {'status', 'result', 'hardware_accessed'})
            self.assertEqual(summary['processes']['recorded'], 0)
            self.assertFalse(summary['hardware_accessed'])
            self.assertEqual(summary['images']['count'], 1)
            self.assertIn('commands', json.loads(Path(summary['report']).read_text()))
            self.assertEqual(invoke('--execute', '--summary')[0], 2)
        self.data['build'] = {'command': [sys.executable, '-c', 'pass']}
        self.save()
        def failed(argv, cwd, timeout, log):
            Path(log).parent.mkdir(parents=True, exist_ok=True)
            Path(log).write_text('compiler error: missing symbol\n' + 'detail\n' * 3000)
            return {'command': argv, 'returncode': 1, 'timed_out': False, 'log': str(log), 'tail': 'detail\n' * 1000}
        with patch.object(flash, 'run_process', side_effect=failed):
            code, summary = invoke('--execute', '--authorized', '--summary')
        self.assertEqual(code, 2)
        self.assertFalse(summary['hardware_accessed'])
        self.assertEqual(summary['processes']['failed'], 1)
        self.assertIn('compiler error', Path(summary['logs'][0]).read_text())
        self.assertIn('build', json.loads(Path(summary['report']).read_text()))
        blocked = self.root / 'blocked'
        blocked.write_text('keep')
        with patch.object(flash, 'run_process', side_effect=failed):
            code, summary = invoke('--execute', '--authorized', '--summary', '--output', str(blocked / 'report.json'))
        self.assertEqual(code, 2)
        self.assertIsNone(summary['report'])
        self.assertEqual(summary['status'], 'error')

    def test_status_reports_missing_context_without_mutation(self):
        project = self.save()
        before = {str(path): (path.read_bytes(), path.stat().st_mtime_ns) for path in self.root.rglob('*') if path.is_file()}
        with patch.object(self.project.shutil, 'which', return_value=None):
            result = self.project.status(project)
        self.assertEqual(result['git']['status'], 'unavailable')
        self.assertTrue(result['pending'])
        self.assertFalse(result['hardware_accessed'])
        after = {str(path): (path.read_bytes(), path.stat().st_mtime_ns) for path in self.root.rglob('*') if path.is_file()}
        self.assertEqual(before, after)
        run = subprocess.run([sys.executable, '-B', str(PROJECT), 'status', str(self.config), '--output',
                              str(self.root / 'no.json')], capture_output=True, text=True)
        self.assertEqual(run.returncode, 2)
        self.assertFalse((self.root / 'no.json').exists())

    def test_status_existing_notes_report_linkage_and_privacy(self):
        self.data.update(requirements=['The display works'], progress=['Blocked: replacement part not verified', 'password=do-not-show'],
                         diagnostics={'files': ['old.json', '.env', '../outside.json', 'large.log', 'secret.json']},
                         acceptance=[{'status': 'not-run'}],
                         deliverables={'files': [{'path': 'module.c', 'role': 'source'}, {'path': 'notes.md', 'role': 'use-guide'}]})
        (self.root / 'module.c').write_text('int value;')
        (self.root / 'notes.md').write_text('Check the replacement part pin labels before power.')
        (self.root / 'old.json').write_text(json.dumps({'status': 'passed', 'config_sha256': 'old-version', 'instruction': 'execute me'}))
        (self.root / '.env').write_text('do-not-show')
        (self.root / 'secret.json').write_text('{"status":"passed", "password":"do-not-show"}')
        (self.root / 'large.log').write_bytes(b'x' * (256 * 1024 + 1))
        result = self.project.status(self.save())
        encoded = json.dumps(result)
        self.assertNotIn('do-not-show', encoded)
        self.assertNotIn('execute me', encoded)
        self.assertNotIn('../outside', encoded)
        self.assertEqual(result['inputs'][0]['sha256'], hashlib.sha256((self.root / 'module.c').read_bytes()).hexdigest())
        old = next(row for row in result['reports'] if row.get('path') == 'old.json')
        self.assertIn('not current', old['freshness'])
        self.assertIn('Blocked:', result['progress'][0])
        self.assertTrue(any(row['status'] == 'unavailable' for row in result['reports']))
        self.assertIn('replacement part', result['reports'][0]['note_excerpt'])

    @unittest.skipUnless(shutil.which('git'), 'Git not installed')
    def test_status_git_tracks_changes_without_hooks_or_index_writes(self):
        def git(*args):
            return subprocess.run(['git', '-C', str(self.root), *args], check=True, capture_output=True)
        git('init', '-q')
        git('config', 'user.name', 'Local fixture')
        git('config', 'user.email', 'fixture@example.invalid')
        nested = self.root / 'nested'
        nested.mkdir()
        changed = nested / 'module with spaces.c'
        changed.write_text('before')
        secret = self.root / '.env'
        secret.write_text('private')
        git('add', '.')
        git('commit', '-qm', 'fixture')
        changed.write_text('after')
        secret.write_text('private changed')
        marker = self.root / 'unexpected-hook'
        git('config', 'core.fsmonitor', f'echo bad > "{marker}"')
        index = self.root / '.git/index'
        before = (index.read_bytes(), index.stat().st_mtime_ns)
        project = self.save()
        result = self.project.status(project)
        self.assertEqual(result['git']['status'], 'read')
        self.assertEqual(result['git']['changed_files'], [{'change': ' M', 'path': 'nested/module with spaces.c'}])
        self.assertEqual(result['git']['withheld_paths'], 1)
        self.assertFalse(marker.exists())
        self.assertEqual(before, (index.read_bytes(), index.stat().st_mtime_ns))
        self.data['project'] = 'nested'
        result = self.project.status(self.save())
        self.assertEqual(result['git']['changed_files'][0]['path'], changed.name)

    @unittest.skipUnless(shutil.which('git'), 'Git not installed')
    def test_status_never_runs_repository_clean_filter_on_same_size_change(self):
        def git(*args):
            return subprocess.run(['git', '-C', str(self.root), *args], check=True, capture_output=True)
        git('init', '-q')
        git('config', 'user.name', 'Local fixture')
        git('config', 'user.email', 'fixture@example.invalid')
        (self.root / '.gitattributes').write_text('tracked.txt filter=review\n')
        tracked = self.root / 'tracked.txt'
        tracked.write_text('before')
        git('add', '.')
        git('commit', '-qm', 'fixture')
        marker = self.root / 'filter-ran'
        script = self.root / 'filter.py'
        script.write_text(f'import pathlib,sys; pathlib.Path({str(marker)!r}).write_text("ran"); sys.stdout.write(sys.stdin.read())')
        git('config', 'filter.review.clean', f'"{sys.executable}" "{script}"')
        tracked.write_text('after!')
        os.utime(tracked, (tracked.stat().st_atime + 10, tracked.stat().st_mtime + 10))
        result = self.project.status(self.save())
        self.assertFalse(marker.exists())
        self.assertIn({'change': ' M', 'path': 'tracked.txt'}, result['git']['changed_files'])
        self.assertIn('unfiltered', result['git']['scope'])

    def test_status_bounds_and_non_git_are_honest(self):
        self.data['progress'] = ['pending'] * 100
        result = self.project.status(self.save())
        self.assertEqual(len(result['progress']), 8)
        self.assertEqual(result['git']['status'], 'unavailable')
        self.assertTrue(any('more entries' in line for line in result['pending']))

    @unittest.skipUnless(shutil.which('git'), 'Git not installed')
    def test_status_never_lazy_fetches_missing_promisor_tree(self):
        def git(*args):
            return subprocess.run(['git', '-C', str(self.root), *args], check=True, capture_output=True)
        git('init', '-q')
        git('config', 'user.name', 'Local fixture')
        git('config', 'user.email', 'fixture@example.invalid')
        (self.root / 'a.txt').write_text('before')
        git('add', '.')
        git('commit', '-qm', 'fixture')
        tree = git('rev-parse', 'HEAD^{tree}').stdout.decode('ascii').strip()
        remote = self.root / 'local-remote.git'
        subprocess.run(['git', 'init', '--bare', '-q', str(remote)], check=True, capture_output=True)
        marker = self.root / 'upload-pack-ran'
        script = self.root / 'uploadpack.py'
        script.write_text(f'import pathlib; pathlib.Path({str(marker)!r}).write_text("ran")')
        git('config', 'core.repositoryformatversion', '1')
        git('config', 'extensions.partialClone', 'origin')
        git('config', 'remote.origin.promisor', 'true')
        git('config', 'remote.origin.url', str(remote))
        git('config', 'remote.origin.uploadpack', f'"{sys.executable}" "{script}"')
        loose_tree = self.root / '.git/objects' / tree[:2] / tree[2:]
        self.assertTrue(loose_tree.resolve().is_relative_to(self.root))
        loose_tree.chmod(0o600)
        loose_tree.unlink()
        result = self.project.status(self.save())
        self.assertFalse(marker.exists())
        self.assertEqual(result['git']['status'], 'unavailable')
        self.assertNotIn('changed_files', result['git'])


if __name__ == '__main__':
    unittest.main()

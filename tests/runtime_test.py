"""Shared MCU runtime checks; no downloads, installations or device access."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
COMMON = ROOT / 'skills/test-mcu-in-background/scripts/mcu_common.py'


def load_common():
    spec = importlib.util.spec_from_file_location('mcu_common_test', COMMON)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.assertTrue(COMMON.exists(), 'shared runtime helper not implemented')
        self.common = load_common()

    def modules(self):
        base = self.root / 'modules'
        for package, distribution, version in [('unicorn', 'unicorn', '2.1.4'), ('elftools', 'pyelftools', '0.33')]:
            folder = base / package
            folder.mkdir(parents=True)
            code = 'UC_ARCH_ARM = 1\nUC_MODE_THUMB = 2\nclass Uc:\n def __init__(self, *args): pass\n'
            (folder / '__init__.py').write_text(code, encoding='utf-8')
            info = base / f'{distribution}-{version}.dist-info'
            info.mkdir()
            (info / 'METADATA').write_text(f'Name: {distribution}\nVersion: {version}\n', encoding='utf-8')
        return base

    def test_shared_module_exists_and_copies_match(self):
        self.assertEqual(COMMON.read_bytes(), (ROOT / 'skills/flash-mcu-firmware/scripts/mcu_common.py').read_bytes())

    def test_config_resolves_project_relative_to_config(self):
        folder = self.root / 'config'
        folder.mkdir()
        path = folder / 'mcu.json'
        path.write_text(json.dumps({'version': 1, 'project': '..', 'tools': {'arm_gcc': 'bin/gcc'}}))
        config, project = self.common.load_config(path)
        self.assertEqual(project, self.root)
        self.assertEqual(config['_project_root'], str(self.root))
        path.write_text('{"version": 2}')
        with self.assertRaises(self.common.UserError):
            self.common.load_config(path)

    def test_json_is_atomic_utf8_lf_and_hash_matches(self):
        path = self.root / 'nested' / 'state.json'
        self.common.write_json(path, {'name': '门'})
        self.assertNotIn(b'\r', path.read_bytes())
        self.assertEqual(json.loads(path.read_text(encoding='utf-8')), {'name': '门'})
        import hashlib
        self.assertEqual(self.common.sha256_file(path), hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(list(path.parent.iterdir()), [path])

    def test_fingerprint_preserves_virtual_environment_symlink(self):
        link = self.root / 'runtime-python'
        try:
            link.symlink_to(sys.executable)
        except OSError:
            self.skipTest('symbolic links unavailable on this host')
        self.assertEqual(self.common._fingerprint(link)['path'], str(link.absolute()))

    def test_default_mac_cache_uses_library_caches(self):
        with patch.object(self.common.platform, 'system', return_value='Darwin'), patch.object(self.common.Path, 'home', return_value=self.root):
            cache = self.common.cache_root()
        self.assertEqual(cache.parent.parent.parent, self.root / 'Library/Caches')

    def test_tool_path_and_stale_cache(self):
        tool = self.root / 'compiler.exe'
        tool.write_text('compiler one')
        tool.chmod(0o755)
        cache = self.root / 'cache'
        config = {'_project_root': str(self.root), 'tools': {'arm_gcc': 'compiler.exe'}}
        self.assertEqual(self.common.find_tool('arm_gcc', config, cache), str(tool))
        tool.unlink()
        with patch.object(self.common.shutil, 'which', return_value=None), patch.object(self.common, '_vendor_candidates', return_value=[]):
            with self.assertRaises(self.common.UserError):
                self.common.find_tool('arm_gcc', {}, cache)
        stored = json.loads((cache / 'tools.json').read_text())
        self.assertNotIn('arm_gcc', stored['tools'])

    def test_explicit_bad_tool_does_not_fall_back(self):
        with patch.object(self.common.shutil, 'which', return_value=sys.executable):
            with self.assertRaises(self.common.UserError):
                self.common.find_tool('python', {'tools': {'python': 'does-not-exist'}}, self.root)

    def test_user_local_stm32_vendor_layout(self):
        layouts = {'arm_gcc': 'STM32CubeIDE_9.0/STM32CubeIDE/plugins/com.st.stm32cube.ide.mcu.externaltools.gnu-tools-for-stm32.9.0/tools/bin/arm-none-eabi-gcc.exe',
                   'stm32_programmer': 'STM32CubeProgrammer_9.0/bin/STM32_Programmer_CLI.exe'}
        for name, layout in layouts.items():
            executable = self.root / 'STM32/software' / layout
            executable.parent.mkdir(parents=True)
            executable.write_text('tool')
            executable.chmod(0o755)
            with patch.object(self.common.Path, 'home', return_value=self.root), patch.object(self.common.platform, 'system', return_value='Windows'), patch.object(self.common.shutil, 'which', return_value=None):
                found = self.common.find_tool(name, {}, self.root / 'cache')
            self.assertEqual(found, str(executable))

    def test_process_streams_output_and_bounds_tail(self):
        result = self.common.run_process([sys.executable, '-c', 'print("x" * 20000)'], self.root, 10, self.root / 'out.log')
        self.assertEqual(result['returncode'], 0)
        self.assertFalse(result['timed_out'])
        self.assertGreater(Path(result['log']).stat().st_size, 20000)
        self.assertLessEqual(len(result['tail'].encode()), 8192)
        with self.assertRaises(self.common.UserError):
            self.common.run_process('echo unsafe', self.root, 1, self.root / 'bad.log')

    def test_process_passes_env_and_reports_launch_error(self):
        env = dict(os.environ, MCU_TEST_VALUE='passed')
        result = self.common.run_process([sys.executable, '-c', 'import os; print(os.environ["MCU_TEST_VALUE"])'], self.root, 10, self.root / 'env.log', env)
        self.assertIn('passed', result['tail'])
        with self.assertRaises(self.common.UserError):
            self.common.run_process([str(self.root / 'missing-exe')], self.root, 1, self.root / 'missing.log')

    def test_timeout_stops_spawned_process_tree(self):
        import time
        marker = self.root / 'orphan.txt'
        child = f'import time; from pathlib import Path; time.sleep(1); Path({str(marker)!r}).write_text("orphan")'
        script = f'import subprocess,sys,time; subprocess.Popen([sys.executable,"-c",{child!r}]); time.sleep(30)'
        result = self.common.run_process([sys.executable, '-c', script], self.root, 0.25, self.root / 'timeout.log')
        self.assertTrue(result['timed_out'])
        time.sleep(1.1)
        self.assertFalse(marker.exists(), 'timed-out child process survived')

    def test_modules_are_persisted_and_reused_without_prepare(self):
        modules = self.modules()
        cache = self.root / 'cache'
        before = dict(os.environ)
        python = self.common.runtime_python(cache, module_paths=[modules])
        self.assertEqual(Path(python), Path(sys.executable).resolve())
        self.assertEqual(self.common.runtime_python(cache), python)
        env = self.common.runtime_env(cache)
        self.assertEqual(env['PYTHONPATH'], str(modules))
        self.assertEqual(env['PYTHONNOUSERSITE'], '1')
        self.assertEqual(dict(os.environ), before)
        descriptor = json.loads((cache / 'runtime.json').read_text())
        self.assertEqual(descriptor['module_paths'], [str(modules)])
        self.assertEqual(descriptor['pins'], {'unicorn': '2.1.4', 'pyelftools': '0.33'})

    def test_stale_interpreter_invalidated_without_install(self):
        cache = self.root / 'cache'
        self.common.runtime_python(cache, module_paths=[self.modules()])
        path = cache / 'runtime.json'
        descriptor = json.loads(path.read_text())
        descriptor['python']['path'] = str(self.root / 'gone-python')
        self.common.write_json(path, descriptor)
        with patch.object(self.common, '_probe', return_value=None), patch.object(self.common, 'run_process') as run:
            with self.assertRaises(self.common.UserError):
                self.common.runtime_python(cache)
            run.assert_not_called()
        self.assertFalse(path.exists())

    def test_changed_modules_are_not_silently_accepted(self):
        cache = self.root / 'cache'
        modules = self.modules()
        self.common.runtime_python(cache, module_paths=[modules])
        (modules / 'unicorn/__init__.py').write_text('raise ImportError("changed")\n')
        with self.assertRaises(self.common.UserError):
            self.common.runtime_env(cache)

    def test_setup_lock_and_missing_runtime_do_not_install(self):
        (self.root / 'runtime.lock').write_text('busy')
        with self.assertRaises(self.common.UserError):
            self.common.runtime_python(self.root, prepare=True)
        (self.root / 'runtime.lock').unlink()
        with patch.object(self.common, '_probe', return_value=None), patch.object(self.common, 'run_process') as run:
            with self.assertRaises(self.common.UserError):
                self.common.runtime_python(self.root)
            run.assert_not_called()
        self.assertFalse((self.root / 'runtime.json').exists())

    def test_explicit_prepare_uses_private_venv_and_pinned_official_pypi(self):
        cache = self.root / 'cache'
        modules = self.modules()
        probe = {'origins': [self.common._fingerprint(modules / 'unicorn/__init__.py')]}
        commands = []

        def setup(argv, cwd, timeout, log_path, env=None):
            commands.append(argv)
            if 'venv' in argv:
                private = Path(argv[-1]) / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
                private.parent.mkdir(parents=True)
                private.write_text('private python')
            return {'returncode': 0, 'timed_out': False, 'log': str(log_path)}

        with patch.object(self.common, '_probe', side_effect=[None, None, None, probe]), patch.object(self.common, 'run_process', side_effect=setup):
            python = self.common.runtime_python(cache, prepare=True)
        self.assertTrue(Path(python).is_relative_to(cache))
        install = commands[-1]
        self.assertIn('--isolated', install)
        self.assertIn('https://pypi.org/simple', install)
        self.assertIn('unicorn==2.1.4', install)
        self.assertIn('pyelftools==0.33', install)
        self.assertNotIn('--user', install)
        self.assertTrue((cache / 'runtime.json').is_file())

    def test_partial_prepare_cannot_leave_success_descriptor(self):
        with patch.object(self.common, '_probe', return_value=None), patch.object(self.common, 'run_process', return_value={'returncode': 1, 'timed_out': False, 'log': 'setup.log'}):
            with self.assertRaises(self.common.UserError):
                self.common.runtime_python(self.root, prepare=True)
        self.assertFalse((self.root / 'runtime.json').exists())
        self.assertFalse((self.root / 'runtime.lock').exists())


if __name__ == '__main__':
    unittest.main()

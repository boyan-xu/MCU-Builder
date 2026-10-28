"""Local tool discovery, bounded child processes and a reusable pinned ARM runtime."""
import contextlib
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import sys
import tempfile

PINS = {'unicorn': '2.1.4', 'pyelftools': '0.33'}
TOOLS = {'python': ('python3', 'python'), 'arm_gcc': ('arm-none-eabi-gcc',),
         'host_cc': ('cc', 'gcc', 'clang'), 'stm32_programmer': ('STM32_Programmer_CLI',),
         'arduino_cli': ('arduino-cli',), 'esptool': ('esptool',)}


class UserError(Exception):
    """An actionable setup or input error."""


def load_config(path):
    path = Path(path).expanduser().resolve()
    try:
        config = json.loads(path.read_text(encoding='utf-8-sig'))
        if not isinstance(config, dict) or type(config.get('version')) is not int or config['version'] != 1:
            raise ValueError('expected a JSON object with version 1')
        if not isinstance(config.get('project', '.'), str) or not isinstance(config.get('tools', {}), dict):
            raise ValueError('project must be a path string; tools must be an object')
        root = (path.parent / config.get('project', '.')).resolve()
        if not root.is_dir():
            raise ValueError(f'project directory does not exist: {root}')
    except (OSError, ValueError) as exc:
        raise UserError(f'Cannot load config {path}: {exc}') from exc
    config['_project_root'] = str(root)
    return config, root


def cache_root(optional=None):
    if optional:
        base = Path(optional).expanduser()
    elif platform.system() == 'Windows':
        base = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData/Local'))
    elif platform.system() == 'Darwin':
        base = Path.home() / 'Library/Caches'
    else:
        base = Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache'))
    identity = f'py{sys.version_info.major}.{sys.version_info.minor}-{platform.system().lower()}-{platform.machine().lower()}'
    path = (base / 'mcu-tools' / 'v1' / identity).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def sha256_file(path):
    try:
        digest = hashlib.sha256()
        with Path(path).open('rb') as source:
            for block in iter(lambda: source.read(1024 * 1024), b''):
                digest.update(block)
        return digest.hexdigest()
    except OSError as exc:
        raise UserError(f'Cannot hash {path}: {exc}') from exc


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n', dir=path.parent, prefix=path.name + '.', suffix='.tmp', delete=False) as output:
            temporary = Path(output.name)
            json.dump(value, output, indent=2, ensure_ascii=False, allow_nan=False)
            output.write('\n')
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    except (OSError, ValueError, TypeError) as exc:
        raise UserError(f'Cannot write {path}: {exc}') from exc
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)


def result_summary(result, report=None):
    """A view of this invocation, never a replacement for its saved evidence."""
    runs = ([result['build']] if isinstance(result.get('build'), dict) else []) + result.get('runs', [])
    completed = [run for run in runs if not run.get('timed_out') and run.get('returncode') is not None]
    summary = {key: result[key] for key in ('status', 'layer', 'hardware_accessed', 'physical_behavior',
               'config_sha256', 'configuration_sha256', 'compiler_target', 'esptool_major') if key in result}
    summary.update(evidence_scope='current-invocation-only', report=str(report) if report else None,
                   processes={'recorded': len(runs), 'completed': len(completed),
                              'succeeded': sum(run['returncode'] == 0 for run in completed),
                              'failed': sum(run['returncode'] != 0 for run in completed),
                              'timed_out': sum(bool(run.get('timed_out')) for run in runs)},
                   logs=[run['log'] for run in runs if run.get('log')])
    for key in ('tested_files', 'images'):
        value = result.get(key)
        if value is not None:
            encoded = json.dumps(value, sort_keys=True, ensure_ascii=True).encode('utf-8')
            summary[key] = {'count': len(value), 'manifest_sha256': hashlib.sha256(encoded).hexdigest()}
    if result.get('elf'):
        summary['elf_sha256'] = result['elf']['sha256']
    failed = next((run for run in reversed(runs) if run.get('timed_out') or run.get('returncode') != 0), None)
    excerpt = result.get('error') or (failed or {}).get('tail')
    if excerpt:
        summary['excerpt'] = str(excerpt)[-600:]
    summary['detail'] = 'Process counts are not test-case counts. Read the full report/logs for coverage, context and errors outside this excerpt.'
    return summary


def _read_json(path):
    try:
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _fingerprint(path):
    # Preserve a venv's interpreter path even when it links to the base Python.
    path = Path(path).absolute()
    stat = path.stat()
    return {'path': str(path), 'resolved': str(path.resolve()), 'size': stat.st_size, 'mtime_ns': stat.st_mtime_ns, 'sha256': sha256_file(path)}


def _same_file(identity):
    try:
        return isinstance(identity, dict) and _fingerprint(identity['path']) == identity
    except (OSError, KeyError, TypeError, UserError):
        return False


def _vendor_candidates(name):
    if platform.system() != 'Windows':
        return []
    roots = [Path(os.environ.get('SystemDrive', 'C:') + '/'), Path(os.environ.get('ProgramFiles', 'C:/Program Files')), Path(os.environ.get('ProgramFiles(x86)', 'C:/Program Files (x86)')), Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData/Local')), Path.home() / 'STM32/software']
    patterns = {
        'arm_gcc': ('ST/STM32CubeIDE*/STM32CubeIDE/plugins/com.st.stm32cube.ide.mcu.externaltools.gnu-tools-for-stm32.*/tools/bin/arm-none-eabi-gcc.exe', 'STM32CubeIDE*/STM32CubeIDE/plugins/com.st.stm32cube.ide.mcu.externaltools.gnu-tools-for-stm32.*/tools/bin/arm-none-eabi-gcc.exe', 'STMicroelectronics/STM32Cube/STM32CubeIDE*/plugins/com.st.stm32cube.ide.mcu.externaltools.gnu-tools-for-stm32.*/tools/bin/arm-none-eabi-gcc.exe'),
        'stm32_programmer': ('STMicroelectronics/STM32Cube/STM32CubeProgrammer/bin/STM32_Programmer_CLI.exe', 'STM32CubeProgrammer*/bin/STM32_Programmer_CLI.exe'),
        'arduino_cli': ('Arduino CLI/arduino-cli.exe', 'Programs/Arduino IDE/resources/app/lib/backend/resources/arduino-cli.exe'),
        'esptool': ('Arduino15/packages/esp32/tools/esptool_py/*/esptool.exe', 'Arduino15/packages/esp8266/tools/esptool/*/esptool.exe'),
        'host_cc': ('msys64/ucrt64/bin/gcc.exe', 'msys64/mingw64/bin/gcc.exe', 'CodeBlocks/MinGW/bin/gcc.exe'),
    }
    return [path for root in roots for pattern in patterns.get(name, ()) for path in itertools.islice(root.glob(pattern), 256)]


def find_tool(name, config, cache):
    if name not in TOOLS:
        raise UserError(f'Unknown tool: {name}')
    cache = Path(cache)
    state_path = cache / 'tools.json'
    state = _read_json(state_path)
    tools = state.get('tools', {}) if state.get('version') == 1 else {}
    if not isinstance(tools, dict):
        tools = {}
    explicit = config.get('tools', {}).get(name)
    if explicit is not None:
        if not isinstance(explicit, str) or not explicit:
            raise UserError(f'tools.{name} must be an executable path')
        candidates = [Path(config.get('_project_root', '.')) / Path(explicit).expanduser()]
    else:
        if name in tools:
            if _same_file(tools[name]):
                return tools[name]['path']
            tools.pop(name)
            write_json(state_path, {'version': 1, 'tools': tools})
        candidates = ([Path(sys.executable)] if name == 'python' else [])
        candidates += [Path(found) for executable in TOOLS[name] if (found := shutil.which(executable))]
        candidates += _vendor_candidates(name)
    for path in candidates:
        if path.is_file() and (os.name == 'nt' or os.access(path, os.X_OK)):
            tools[name] = _fingerprint(path)
            write_json(state_path, {'version': 1, 'tools': tools})
            return tools[name]['path']
    raise UserError(f'Cannot find {name}; set tools.{name} to its executable in the config.')


def run_process(argv, cwd, timeout, log_path, env=None):
    if not isinstance(argv, (list, tuple)) or not argv or not all(isinstance(arg, (str, os.PathLike)) for arg in argv):
        raise UserError('Command must be a nonempty argv array, never shell text.')
    if isinstance(timeout, bool) or not isinstance(timeout, (float, int)) or not math.isfinite(timeout) or timeout <= 0:
        raise UserError('Process timeout must be a positive finite number.')
    command = [os.fspath(arg) for arg in argv]
    log_path = Path(log_path).resolve()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timed_out = False
    try:
        with log_path.open('wb') as output:
            options = {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == 'nt' else {'start_new_session': True}
            process = subprocess.Popen(command, cwd=cwd, env=env, stdout=output, stderr=subprocess.STDOUT, shell=False, **options)
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                if os.name == 'nt':
                    try:
                        subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], stdout=output, stderr=subprocess.STDOUT, timeout=10, shell=False)
                    except (OSError, subprocess.TimeoutExpired):
                        process.kill()
                else:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=10)
        with log_path.open('rb') as source:
            source.seek(max(0, log_path.stat().st_size - 8192))
            tail = source.read(8192).decode('utf-8', errors='replace')
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        raise UserError(f'Cannot run {command[0]!r}: {exc}; log: {log_path}') from exc
    return {'command': command, 'returncode': process.returncode, 'timed_out': timed_out, 'log': str(log_path), 'tail': tail}


def _runtime_env(paths):
    env = dict(os.environ)
    env.pop('PYTHONHOME', None)
    env['PYTHONPATH'] = os.pathsep.join(paths)
    env['PYTHONNOUSERSITE'] = '1'
    return env


def _probe(python, paths, cache):
    if not Path(python).is_file() or any(not Path(path).is_dir() for path in paths):
        return None
    code = 'import json,sys,unicorn,elftools; from importlib.metadata import version; unicorn.Uc(unicorn.UC_ARCH_ARM,unicorn.UC_MODE_THUMB); print(json.dumps({"python":sys.executable,"versions":{n:version(n) for n in ("unicorn","pyelftools")},"origins":[unicorn.__file__,elftools.__file__]}))'
    fd, name = tempfile.mkstemp(prefix='runtime-probe-', suffix='.log', dir=cache)
    os.close(fd)
    try:
        result = run_process([str(python), '-c', code], cache, 20, name, _runtime_env(paths))
        if result['returncode'] or result['timed_out']:
            return None
        info = json.loads(result['tail'])
        if info['versions'] != PINS or Path(info['python']).absolute() != Path(python).absolute():
            return None
        return {'origins': [_fingerprint(path) for path in info['origins']]}
    except (UserError, ValueError, KeyError, OSError):
        return None
    finally:
        Path(name).unlink(missing_ok=True)


def _valid_runtime(record, cache):
    if record.get('version') != 1 or record.get('pins') != PINS or not _same_file(record.get('python')):
        return False
    paths = record.get('module_paths')
    if not isinstance(paths, list) or not all(isinstance(path, str) for path in paths):
        return False
    return _probe(record['python']['path'], paths, cache) == record.get('probe') and bool(record.get('probe'))


@contextlib.contextmanager
def _runtime_lock(cache):
    path = cache / 'runtime.lock'
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise UserError(f'Runtime setup is busy ({path}); retry after that process finishes. Remove a stale lock only after confirming its process stopped.') from exc
    try:
        with os.fdopen(fd, 'w') as lock:
            lock.write(str(os.getpid()))
        yield
    finally:
        path.unlink(missing_ok=True)


def runtime_python(cache, prepare=False, module_paths=None):
    """Reuse pinned imports; only explicit prepare may install into the private cache."""
    cache = Path(cache).resolve()
    cache.mkdir(parents=True, exist_ok=True)
    descriptor = cache / 'runtime.json'
    with _runtime_lock(cache):
        record = _read_json(descriptor)
        if _valid_runtime(record, cache):
            return record['python']['path']
        descriptor.unlink(missing_ok=True)
        paths = []
        for item in module_paths or []:
            path = Path(item).expanduser().resolve()
            choices = [path / 'Lib/site-packages', *path.glob('lib/python*/site-packages'), path]
            path = next((item for item in choices if (item / 'unicorn').is_dir() or (item / 'elftools').is_dir()), path)
            if str(path) not in paths:
                paths.append(str(path))
        venv = cache / 'arm-runtime-uc2.1.4-elf0.33'
        private_python = venv / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        candidates = [(Path(sys.executable).absolute(), paths), (Path(sys.executable).absolute(), []), (private_python, [])]
        for python, roots in candidates:
            probe = _probe(python, roots, cache)
            if probe:
                break
        else:
            if not prepare:
                raise UserError('Pinned ARM runtime unavailable. Provide compatible module_paths or explicitly prepare unicorn==2.1.4 and pyelftools==0.33 in the private cache.')
            if not private_python.is_file():
                result = run_process([sys.executable, '-m', 'venv', str(venv)], cache, 120, cache / 'runtime-venv.log')
                if result['returncode'] or result['timed_out']:
                    raise UserError(f'Private runtime creation failed; see {result["log"]}')
            result = run_process([str(private_python), '-m', 'pip', '--isolated', 'install', '--disable-pip-version-check', '--no-input', '--no-cache-dir', '--index-url', 'https://pypi.org/simple', '--only-binary=:all:', '--no-deps', *[f'{name}=={version}' for name, version in PINS.items()]], cache, 300, cache / 'runtime-install.log')
            if result['returncode'] or result['timed_out']:
                raise UserError(f'Pinned runtime install failed; see {result["log"]}')
            python, roots = private_python, []
            probe = _probe(python, roots, cache)
            if not probe:
                raise UserError('Prepared runtime failed its version/native-engine check; no successful runtime was cached.')
        record = {'version': 1, 'pins': PINS, 'python': _fingerprint(python), 'module_paths': roots, 'probe': probe}
        write_json(descriptor, record)
        return record['python']['path']


def runtime_env(cache):
    cache = Path(cache).resolve()
    record = _read_json(cache / 'runtime.json')
    if not _valid_runtime(record, cache):
        raise UserError('Runtime descriptor is missing or stale; call runtime_python before starting a worker.')
    return _runtime_env(record['module_paths'])

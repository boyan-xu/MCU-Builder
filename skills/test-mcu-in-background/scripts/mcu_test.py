"""Reusable software checks and Cortex-M C execution. Never flashes a board."""
from pathlib import Path
import argparse
import json
import os
import re
import struct
import sys
import time
import zlib

from mcu_common import (UserError, cache_root, find_tool, load_config, run_process,
                        runtime_env, runtime_python, sha256_file, write_json)


def strings(value, label):
    if not isinstance(value, list) or not value or any(not isinstance(x, str) or not x or '\0' in x for x in value):
        raise UserError(label + ' must be a nonempty array of strings, not a shell command')
    return value


def positive(value, label, maximum=3600):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 < value <= maximum:
        raise UserError(f'{label} must be positive and at most {maximum}')
    return value


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise UserError('addresses and sizes must be integers')
    try:
        return int(value, 0) if isinstance(value, str) else int(value)
    except (ValueError, TypeError):
        raise UserError('invalid address or size') from None


def existing(root, value):
    if not isinstance(value, str) or not value:
        raise UserError('input path must be a nonempty string')
    path = (root / value).resolve()
    if not path.is_file():
        raise UserError('missing input file: ' + str(path))
    return path


def png_from_pages(data, width, height):
    """SSD1306 page bytes to a grayscale PNG, using only the standard library."""
    if width < 1 or height < 1 or width > 1024 or height > 1024 or len(data) != width * ((height + 7) // 8):
        raise UserError('capture dimensions do not match SSD1306 page bytes')
    rows = b''.join(b'\0' + bytes(255 if data[x + (y // 8) * width] & (1 << (y % 8)) else 0 for x in range(width)) for y in range(height))
    def chunk(kind, payload):
        return struct.pack('>I', len(payload)) + kind + payload + struct.pack('>I', zlib.crc32(kind + payload) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 0, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b'')


def arm_worker(job_path):
    from elftools.elf.elffile import ELFFile
    from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS
    from unicorn.arm_const import UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_R0, UC_ARM_REG_PC
    job = json.loads(Path(job_path).read_text(encoding='utf-8'))
    cpu = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
    regions = job['regions']
    for region in regions.values():
        cpu.mem_map(region['address'], region['size'])
    symbols = {}
    with open(job['elf'], 'rb') as stream:
        elf = ELFFile(stream)
        if elf.get_machine_arch() != 'ARM':
            raise UserError('ELF is not ARM')
        for segment in elf.iter_segments():
            if segment['p_type'] != 'PT_LOAD' or segment['p_memsz'] == 0:
                continue
            address, size = segment['p_vaddr'], segment['p_memsz']
            if not any(r['address'] <= address and address + size <= r['address'] + r['size'] for r in regions.values()):
                raise UserError('ELF segment is outside configured virtual memory')
            if segment['p_filesz']:
                cpu.mem_write(address, segment.data())
        table = elf.get_section_by_name('.symtab')
        if table:
            symbols = {s.name: s['st_value'] for s in table.iter_symbols()}
    entry = symbols.get(job['entry'])
    if entry is None:
        raise UserError('missing entry symbol: ' + job['entry'])
    sentinel = regions['flash']['address'] + regions['flash']['size'] - 4
    cpu.reg_write(UC_ARM_REG_SP, (regions['ram']['address'] + regions['ram']['size'] - 16) & ~7)
    cpu.reg_write(UC_ARM_REG_LR, sentinel | 1)
    cpu.emu_start(entry | 1, sentinel, timeout=int(job['timeout'] * 1000000), count=job['instructions'])
    completed = cpu.reg_read(UC_ARM_REG_PC) & ~1 == sentinel
    result = {'status': 'passed' if completed and cpu.reg_read(UC_ARM_REG_R0) == 0 else 'failed' if completed else 'timed_out',
              'return_value': cpu.reg_read(UC_ARM_REG_R0), 'returned': completed, 'captures': []}
    for capture in job.get('captures', []):
        name = capture['symbol']
        if name not in symbols:
            raise UserError('missing capture symbol: ' + name)
        data = bytes(cpu.mem_read(symbols[name], capture['bytes']))
        path = Path(job['directory']) / capture['output']
        path.write_bytes(data)
        record = {'symbol': name, 'file': str(path), 'sha256': sha256_file(path)}
        if capture.get('format') == 'ssd1306':
            png = path.with_suffix('.png')
            png.write_bytes(png_from_pages(data, capture['width'], capture['height']))
            record['png'] = str(png)
        result['captures'].append(record)
    write_json(job['result'], result)
    print(json.dumps(result))
    return 0 if result['status'] == 'passed' else 1


def command_check(test, config, root, cache, directory):
    command = strings(test.get('command'), 'test.command').copy()
    if command[0].startswith('tool:'):
        command[0] = find_tool(command[0][5:], config, cache)
    command = [x.replace('{project}', str(root)) for x in command]
    inputs = test.get('inputs', [])
    if not isinstance(inputs, list):
        raise UserError('test.inputs must be an array of files')
    files = {name: sha256_file(existing(root, name)) for name in inputs}
    run = run_process(command, root, positive(test.get('timeout', 120), 'test.timeout'), directory / 'command.log')
    return {'layer': 'existing-command', 'status': 'timed_out' if run['timed_out'] else 'passed' if run['returncode'] == 0 else 'failed',
            'runs': [run], 'tested_files': files,
            'limits': ['Runs the configured software command; coverage depends on that command. No hardware operation is provided by this runner.']}


def arm_check(test, config, root, cache, directory):
    sources = strings(test.get('sources'), 'test.sources')
    harness = test.get('harness')
    paths = [existing(root, name) for name in sources + [harness]]
    cpu_name = test.get('cpu')
    if cpu_name not in ('cortex-m0', 'cortex-m0plus', 'cortex-m3', 'cortex-m4', 'cortex-m7'):
        raise UserError('test.cpu must explicitly name a supported Cortex-M compiler target')
    entry = test.get('entry', 'test_main')
    if not isinstance(entry, str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', entry):
        raise UserError('test.entry must be a C symbol')
    regions = {}
    memory = test.get('memory', {})
    if not isinstance(memory, dict):
        raise UserError('test.memory must be an object')
    for name, address, size in [('flash', 0x08000000, 262144), ('ram', 0x20000000, 65536)]:
        region = memory.get(name, {})
        if not isinstance(region, dict):
            raise UserError('memory region must be an object')
        address, size = number(region.get('address', address)), number(region.get('size', size))
        if address < 0 or address % 4096 or size % 4096 or not 4096 <= size <= 16777216 or address + size > 0x100000000:
            raise UserError('virtual memory must be page-aligned and bounded to 16 MiB per region')
        regions[name] = {'address': address, 'size': size}
    a, b = regions.values()
    if max(a['address'], b['address']) < min(a['address'] + a['size'], b['address'] + b['size']):
        raise UserError('virtual flash and RAM overlap')
    captures = test.get('captures', [])
    if not isinstance(captures, list):
        raise UserError('test.captures must be an array')
    capture_names = set()
    for capture in captures:
        if not isinstance(capture, dict) or not isinstance(capture.get('symbol'), str):
            raise UserError('capture must name a symbol')
        output = capture.get('output', '')
        if not isinstance(output, str) or Path(output).name != output or not output.endswith('.bin') or ':' in output or output in capture_names:
            raise UserError('capture.output must be a unique plain .bin filename')
        capture_names.add(output)
        if not isinstance(capture.get('bytes'), int) or isinstance(capture['bytes'], bool) or not 0 < capture['bytes'] <= 1048576:
            raise UserError('capture.bytes must be between 1 and 1048576')
        if capture.get('format') == 'ssd1306':
            for key in ('width', 'height'):
                if not isinstance(capture.get(key), int) or isinstance(capture[key], bool) or not 1 <= capture[key] <= 1024:
                    raise UserError('capture dimensions must be positive integers at most 1024')
            if capture['bytes'] != capture['width'] * ((capture['height'] + 7) // 8):
                raise UserError('capture dimensions do not match buffer size')
    python = runtime_python(cache)
    compiler = find_tool('arm_gcc', config, cache)
    includes = test.get('include_dirs', [])
    flags = test.get('compile_flags', [])
    if not isinstance(includes, list) or any(not isinstance(x, str) or not (root / x).is_dir() for x in includes):
        raise UserError('test.include_dirs must name existing directories')
    if not isinstance(flags, list) or any(not isinstance(x, str) or '\0' in x for x in flags):
        raise UserError('test.compile_flags must be an array of strings')
    files = {str(path.relative_to(root)) if path.is_relative_to(root) else str(path): sha256_file(path) for path in paths}
    for name in includes:
        for header in (root / name).rglob('*.h'):
            files[str(header.relative_to(root)) if header.is_relative_to(root) else str(header)] = sha256_file(header)
    linker = directory / 'test.ld'
    linker.write_text(f"ENTRY({entry})\nMEMORY {{ FLASH (rx) : ORIGIN = {regions['flash']['address']}, LENGTH = {regions['flash']['size']-4096}\nRAM (rwx) : ORIGIN = {regions['ram']['address']}, LENGTH = {regions['ram']['size']-4096} }}\nSECTIONS {{ .text : {{ *(.text*) *(.rodata*) }} > FLASH\n.data : {{ *(.data*) }} > RAM\n.bss (NOLOAD) : {{ *(.bss*) *(COMMON) }} > RAM }}\n", encoding='utf-8')
    elf = directory / 'test.elf'
    command = [compiler, '-mcpu=' + cpu_name, '-mthumb', '-mfloat-abi=soft', '-O1', '-g', '-ffreestanding', '-fno-builtin', '-fno-unwind-tables', '-fno-asynchronous-unwind-tables', '-nostdlib', '-nostartfiles', *flags]
    for include in includes:
        command.extend(['-I', str((root / include).resolve())])
    command.extend([*(str(p) for p in paths), '-Wl,-T,' + str(linker), '-lgcc', '-o', str(elf)])
    build = run_process(command, root, positive(test.get('build_timeout', 120), 'test.build_timeout'), directory / 'build.log')
    result = {'layer': 'arm-instructions-with-test-substitutes', 'status': 'timed_out' if build['timed_out'] else 'failed', 'runs': [build], 'tested_files': files,
              'compiler_target': cpu_name, 'virtual_memory': regions,
              'limits': ['Synthetic Thumb M-class execution, not cycle-accurate whole-board simulation. Peripheral behavior is only what the supplied test harness models. No electrical, flashing or physical evidence.']}
    if build['returncode'] != 0 or build['timed_out']:
        return result
    timeout = positive(test.get('timeout', 10), 'test.timeout')
    instructions = test.get('instructions', 2000000)
    if not isinstance(instructions, int) or isinstance(instructions, bool) or not 1 <= instructions <= 100000000:
        raise UserError('test.instructions must be between 1 and 100000000')
    worker_result = directory / 'worker-result.json'
    job = {'elf': str(elf), 'entry': entry, 'regions': regions, 'timeout': timeout, 'instructions': instructions,
           'captures': captures, 'directory': str(directory), 'result': str(worker_result)}
    job_path = directory / 'arm-job.json'
    write_json(job_path, job)
    run = run_process([python, '-B', str(Path(__file__).resolve()), '--arm-worker', str(job_path)], root, timeout + 10, directory / 'arm.log', env=runtime_env(cache))
    result['runs'].append(run)
    result['elf'] = {'path': str(elf), 'sha256': sha256_file(elf)}
    if worker_result.is_file():
        observed = json.loads(worker_result.read_text(encoding='utf-8'))
        result.update(observed)
        if run['timed_out'] or run['returncode'] != 0 and result['status'] == 'passed':
            result['status'] = 'timed_out' if run['timed_out'] else 'failed'
    else:
        result['status'] = 'timed_out' if run['timed_out'] else 'failed'
        result['error'] = 'ARM worker did not produce a result; see arm.log'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config', nargs='?')
    parser.add_argument('--cache-dir')
    parser.add_argument('--output')
    parser.add_argument('--prepare', action='store_true', help='prepare or reuse the isolated ARM runtime')
    parser.add_argument('--module-path', action='append', default=[], help='reuse an existing compatible module directory during --prepare')
    parser.add_argument('--arm-worker', help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        if args.arm_worker:
            return arm_worker(args.arm_worker)
        cache = cache_root(args.cache_dir)
        if args.prepare:
            python = runtime_python(cache, prepare=True, module_paths=args.module_path)
            print(json.dumps({'status': 'ready', 'python': python, 'cache': str(cache)}))
            return 0
        if args.module_path:
            raise UserError('--module-path is used only with --prepare')
        if not args.config:
            raise UserError('provide a project config or --prepare')
        config, root = load_config(args.config)
        test = config.get('test')
        if not isinstance(test, dict):
            raise UserError('configuration must contain a test object')
        output = Path(args.output).resolve() if args.output else root / '.mcu-results/test-result.json'
        protected = {Path(args.config).resolve()}
        for key in ('sources', 'inputs'):
            for name in test.get(key, []) if isinstance(test.get(key, []), list) else []:
                if isinstance(name, str):
                    protected.add((root / name).resolve())
        if isinstance(test.get('harness'), str):
            protected.add((root / test['harness']).resolve())
        if output.suffix.lower() != '.json' or output in protected:
            raise UserError('result output must be a .json file distinct from the configuration and test inputs')
        directory = root / '.mcu-results' / ('run-' + str(time.time_ns()))
        directory.mkdir(parents=True, exist_ok=False)
        backend = test.get('backend')
        if backend == 'command':
            result = command_check(test, config, root, cache, directory)
        elif backend == 'arm-c':
            result = arm_check(test, config, root, cache, directory)
        else:
            raise UserError('unsupported test backend: ' + str(backend))
        result['config_sha256'] = sha256_file(Path(args.config))
        result['cache'] = str(cache)
        result['report'] = str(output)
        write_json(result['report'], result)
        print(json.dumps(result, ensure_ascii=True))
        return 0 if result['status'] == 'passed' else 1
    except (UserError, OSError, ValueError, TypeError, KeyError, ImportError) as error:
        print(json.dumps({'status': 'error', 'error': str(error)}, ensure_ascii=True))
        return 2


if __name__ == '__main__':
    sys.exit(main())

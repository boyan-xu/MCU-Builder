"""Preview by default; invoke an installed vendor uploader only with explicit execution flags."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys

from mcu_common import UserError, cache_root, find_tool, load_config, result_summary, run_process, sha256_file, write_json


def number(value, name, minimum=0):
    try:
        if isinstance(value, bool):
            raise ValueError()
        result = int(value, 0) if isinstance(value, str) else int(value)
        if result != value and not isinstance(value, str):
            raise ValueError()
        if result < minimum:
            raise ValueError()
        return result
    except (ValueError, TypeError, OverflowError):
        raise UserError(f'{name} must be an integer >= {minimum}') from None


def text(value, name):
    if not isinstance(value, str) or not value.strip() or value.startswith('-') or any(c in value for c in '\r\n\x00'):
        raise UserError(f'{name} must be an explicit nonempty value')
    return value


def flag(config, name, default):
    value = config.get(name, default)
    if not isinstance(value, bool):
        raise UserError(f'flash.{name} must be true or false')
    return value


def serial_port(value):
    value = text(value, 'flash.port')
    if not (re.fullmatch(r'COM[1-9][0-9]*', value, re.I) or value.startswith('/dev/') and '..' not in Path(value).parts):
        raise UserError('flash.port must be an explicit local COM port or /dev/ serial path; network/automatic ports are unsupported')
    return value


def image(root, value, raw=False):
    path = (root / text(value, 'firmware path')).resolve()
    if not path.is_file() or path.stat().st_size == 0:
        raise UserError(f'Firmware file is missing or empty: {path}')
    if raw and path.suffix.lower() != '.bin':
        raise UserError('This backend accepts raw .bin files; use the existing build tools to convert ELF/HEX first')
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha256_file(path)}


def checked_range(flash, address, size, block):
    start = number(flash.get('flash_start'), 'flash.flash_start')
    end = start + number(flash.get('flash_size'), 'flash.flash_size', 1)
    erase_start = address // block * block
    erase_end = (address + size + block - 1) // block * block
    if erase_start < start or erase_end > end:
        raise UserError('Firmware or its erase blocks extend outside the configured flash range')
    protected = flash.get('protected_ranges', [])
    if not isinstance(protected, list):
        raise UserError('flash.protected_ranges must be an array')
    for region in protected:
        if not isinstance(region, dict):
            raise UserError('Each protected range needs address and size')
        left = number(region.get('address'), 'protected address')
        right = left + number(region.get('size'), 'protected size', 1)
        if erase_start < right and erase_end > left:
            raise UserError('Firmware erase blocks overlap a protected range')
    return {'address': hex(address), 'bytes': size, 'erase_start': hex(erase_start), 'erase_end_exclusive': hex(erase_end)}


def plan(config, root, cache):
    flash = config.get('flash')
    if not isinstance(flash, dict):
        raise UserError('Config needs a flash object')
    backend = flash.get('backend')
    target = text(flash.get('target'), 'flash.target')
    timeout = number(flash.get('timeout', 120), 'flash.timeout', 1)
    info = {'schema_version': 1, 'started_at': datetime.now(timezone.utc).isoformat(), 'backend': backend, 'target': target, 'timeout': timeout, 'images': [], 'commands': [], 'hardware_accessed': False, 'physical_behavior': 'not-tested'}
    if backend == 'stm32_programmer':
        tool = find_tool('stm32_programmer', config, cache)
        serial = text(flash.get('probe_serial'), 'flash.probe_serial')
        if not re.fullmatch(r'[A-Za-z0-9_-]+', serial):
            raise UserError('Invalid probe serial')
        device_id = number(flash.get('device_id'), 'flash.device_id', 1)
        frequency = number(flash.get('frequency_khz', 1000), 'flash.frequency_khz', 1)
        prefix = [tool, '-c', 'port=SWD', f'sn={serial}', f'freq={frequency}']
        binary = image(root, flash.get('firmware'), raw=True)
        address = number(flash.get('address'), 'flash.address')
        block = number(flash.get('erase_size'), 'flash.erase_size', 1)
        binary.update(checked_range(flash, address, binary['bytes'], block))
        info.update(images=[binary], probe_serial=serial, expected_device_id=hex(device_id), prefix=prefix,
                    backup_requested=flag(flash, 'backup', True), reset_requested=flag(flash, 'reset_after', False))
        info['commands'] = [{'stage': 'identify', 'argv': prefix}]
        if info['backup_requested']:
            info['commands'].append({'stage': 'backup', 'argv': prefix + ['-u', hex(number(flash['flash_start'], 'flash_start')), str(number(flash['flash_size'], 'flash_size', 1)), '<new-backup.bin>']})
        command = prefix + ['-d', binary['path'], hex(address), '-v']
        if info['reset_requested']:
            command.append('-rst')
        info['commands'].append({'stage': 'program-and-verify', 'argv': command})
    elif backend == 'esptool':
        tools = config.get('tools', {})
        if tools.get('esptool_python'):
            python_config = dict(config, tools=dict(tools, python=tools['esptool_python']))
            executable = [find_tool('python', python_config, cache), '-m', 'esptool']
        else:
            executable = [find_tool('esptool', config, cache)]
        chip = text(flash.get('chip'), 'flash.chip')
        if not re.fullmatch(r'esp[0-9a-z-]+', chip):
            raise UserError('flash.chip needs an explicit esptool chip, not auto')
        port = serial_port(flash.get('port'))
        prefix = executable + ['--chip', chip, '--port', port, '--baud', str(number(flash.get('baud', 115200), 'flash.baud', 1)), '--after', 'no-reset']
        images = flash.get('images')
        if not isinstance(images, list) or not images:
            raise UserError('flash.images needs one or more offset/file objects')
        args = []
        for item in images:
            if not isinstance(item, dict):
                raise UserError('Each flash image needs address and file')
            binary = image(root, item.get('file'), raw=True)
            address = number(item.get('address'), 'image address')
            binary.update(checked_range(flash, address, binary['bytes'], 4096))
            for previous in info['images']:
                left = int(previous['address'], 0)
                if address < left + previous['bytes'] and address + binary['bytes'] > left:
                    raise UserError('Firmware image ranges overlap')
            info['images'].append(binary)
            args.extend([hex(address), binary['path']])
        expected_mac = flash.get('expected_mac')
        if expected_mac is not None and not re.fullmatch(r'(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}', expected_mac):
            raise UserError('flash.expected_mac must be six colon-separated hex bytes')
        info.update(prefix=prefix, executable=executable, port=port, chip=chip, expected_mac=expected_mac,
                    backup_requested=flag(flash, 'backup', True), reset_requested=flag(flash, 'reset_after', False), command_style='detect-on-execute')
        info['commands'] = [{'stage': 'tool-version', 'argv': executable + ['version']},
                            {'stage': 'identify', 'argv': prefix + ['read-mac']}]
        if info['backup_requested']:
            info['commands'].append({'stage': 'backup', 'argv': prefix + ['read-flash', hex(number(flash['flash_start'], 'flash_start')), str(number(flash['flash_size'], 'flash_size', 1)), '<new-backup.bin>']})
        info['commands'].append({'stage': 'program', 'argv': prefix + ['write-flash'] + args})
        verify_prefix = list(prefix)
        if info['reset_requested']:
            verify_prefix[-1] = 'hard-reset'
        info['commands'].append({'stage': 'verify', 'argv': verify_prefix + ['verify-flash'] + args})
    elif backend == 'arduino_cli':
        tool = find_tool('arduino_cli', config, cache)
        fqbn = text(flash.get('fqbn'), 'flash.fqbn')
        if not re.fullmatch(r'[A-Za-z0-9_.-]+:[A-Za-z0-9_.-]+:[A-Za-z0-9_.=,:-]+', fqbn):
            raise UserError('flash.fqbn must identify vendor, architecture and board')
        port = serial_port(flash.get('port'))
        binary = image(root, flash.get('firmware'))
        if not binary['path'].lower().endswith(('.bin', '.hex')):
            raise UserError('Arduino upload needs a built .bin or .hex file')
        if flag(flash, 'backup', False):
            raise UserError('Arduino CLI has no portable backup command; preserve existing firmware with a suitable board tool first')
        verify = flag(flash, 'verify', True)
        command = [tool, 'upload', '--fqbn', fqbn, '--port', port, '--input-file', binary['path']]
        if verify:
            command.append('--verify')
        info.update(images=[binary], port=port, fqbn=fqbn, backup_requested=False,
                    verify_requested=verify, target_identity='caller-reviewed-fqbn-and-port',
                    limits=['No generic firmware backup or on-chip identity check; exact physical target must be reviewed before execution'])
        info['commands'] = [{'stage': 'upload-and-verify' if verify else 'upload', 'argv': command}]
    else:
        raise UserError('Unsupported flash backend; choose stm32_programmer, esptool or arduino_cli')
    return info


def execute(config, root, cache, result, output):
    flash = config['flash']
    log_dir = output.parent
    log_dir.mkdir(parents=True, exist_ok=True)
    result['runs'] = []

    def run(stage, argv):
        record = run_process(argv, root, result['timeout'], log_dir / (stage + '.log'))
        result['runs'].append(dict(record, stage=stage))
        write_json(output, result)
        if record['timed_out'] or record['returncode'] != 0:
            raise UserError(f'{stage} failed; see {record["log"]}')
        return record['tail']

    commands = result['commands']
    if result['backend'] == 'esptool':
        version = run('tool-version', commands[0]['argv'])
        match = re.search(r'(?:esptool[^\r\n]*?v?|\bv)(\d+)\.\d+', version, re.I)
        if not match:
            raise UserError('Cannot determine esptool major version from its version command')
        major = int(match[1])
        if major not in (4, 5):
            raise UserError(f'esptool {major} is not supported by this adapter')
        result['esptool_major'] = major
        result['command_style'] = 'underscore' if major == 4 else 'hyphen'
        if major == 4:
            for item in commands[1:]:
                item['argv'] = [arg.replace('-', '_') if arg in ('read-mac', 'read-flash', 'write-flash', 'verify-flash', 'no-reset', 'hard-reset') else arg for arg in item['argv']]
    if result['backend'] in ('stm32_programmer', 'esptool'):
        result['hardware_accessed'] = True
        identify = next(item for item in commands if item['stage'] == 'identify')
        observed = run('identify', identify['argv'])
        if result['backend'] == 'stm32_programmer':
            match = re.search(r'Device\s+ID\s*:\s*(0x[0-9a-f]+)', observed, re.I)
            if not match or int(match[1], 0) != int(result['expected_device_id'], 0):
                raise UserError('Connected STM32 device ID is absent or differs from the configured target; no program command ran')
            result['observed_device_id'] = match[1]
        elif result['expected_mac'] and result['expected_mac'].lower() not in observed.lower():
            raise UserError('Connected ESP MAC differs from the configured target; no program command ran')
        if result['backup_requested']:
            stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
            backup = log_dir / ('backup-' + stamp + '.bin')
            if backup.exists():
                raise UserError('Backup path already exists; refusing to replace it')
            backup_command = next(item['argv'] for item in commands if item['stage'] == 'backup')
            backup_command = [str(backup) if arg == '<new-backup.bin>' else arg for arg in backup_command]
            run('backup', backup_command)
            if not backup.is_file() or backup.stat().st_size != number(flash['flash_size'], 'flash_size', 1):
                raise UserError('Backup missing or wrong size; no program command ran')
            result['backup'] = {'path': str(backup), 'bytes': backup.stat().st_size, 'sha256': sha256_file(backup), 'scope': 'configured flash range only'}
    for item in commands:
        if item['stage'] in ('tool-version', 'identify', 'backup'):
            continue
        result['hardware_accessed'] = True
        run(item['stage'], item['argv'])
    result['status'] = 'uploaded' if result['backend'] == 'arduino_cli' and not result['verify_requested'] else 'verified'
    result['physical_behavior'] = 'not-tested'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config', type=Path)
    parser.add_argument('--cache-dir', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--summary', action='store_true', help='emit compact current results; keep the full report and logs')
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--authorized', action='store_true', help='Caller has applicable authorization for this exact target and overwrite scope')
    args = parser.parse_args(argv)
    result = {'schema_version': 1, 'started_at': datetime.now(timezone.utc).isoformat(), 'status': 'error', 'hardware_accessed': False, 'physical_behavior': 'not-tested'}
    output = None
    try:
        config, root = load_config(args.config)
        output = args.output.resolve() if args.output else root / '.mcu-results/flash-result.json'
        if output.suffix.lower() != '.json' or output.resolve() == args.config.resolve():
            output = None
            raise UserError('Result output must be a JSON file distinct from the input configuration')
        if args.execute and not args.authorized:
            raise UserError('Execution requires --authorized for the already reviewed exact target; preview needs neither flag')
        if args.summary:
            result['configuration_sha256'] = sha256_file(args.config)
        cache = cache_root(args.cache_dir)
        build = config.get('build')
        if build is not None:
            if not isinstance(build, dict) or not isinstance(build.get('command'), list) or not build['command'] or not all(isinstance(v, str) and v and '\x00' not in v for v in build['command']):
                raise UserError('build.command must be a nonempty argv array; shell strings are not accepted')
            if args.execute:
                built = run_process(build['command'], root, number(build.get('timeout', 120), 'build.timeout', 1), output.parent / 'build.log')
                result['build'] = built
                if built['timed_out'] or built['returncode'] != 0:
                    raise UserError('Build failed; hardware was not accessed')
        build_result = result.get('build')
        result = plan(config, root, cache)
        result['configuration_sha256'] = sha256_file(args.config)
        if build_result:
            result['build'] = build_result
        if build is not None:
            result['build_command'] = build['command']
        result['status'] = 'preview'
        if args.execute:
            result['status'] = 'running'
            write_json(output, result)
            execute(config, root, cache, result, output)
        write_json(output, result)
        print(json.dumps(result_summary(result, output) if args.summary else
                         {'status': result['status'], 'result': str(output), 'hardware_accessed': result['hardware_accessed']}))
        return 0
    except (UserError, OSError, ValueError) as error:
        result.update(status='error', error=str(error))
        if output:
            if args.summary:
                try:
                    write_json(output, result)
                except (UserError, OSError) as save_error:
                    result['error'] += '; ' + str(save_error)
                    output = None
            else:
                write_json(output, result)
        print(json.dumps(result_summary(result, output) if args.summary else result), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())

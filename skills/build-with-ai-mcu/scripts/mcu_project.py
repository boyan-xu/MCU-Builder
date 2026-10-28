"""Local MCU project artifacts. Standard library only; status uses read-only Git, never project commands."""
import argparse
from copy import deepcopy
import hashlib
from html import escape
import json
import math
import os
from pathlib import Path, PureWindowsPath
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import zipfile
from urllib.parse import urlsplit
from xml.etree import ElementTree

TOOL_VERSION = '1.0'
MAX_LOG_BYTES = 256 * 1024
MAX_FILE_BYTES = 64 * 1024 * 1024
PRIVATE = {'.git', '.env', '.ssh', '.aws', '__pycache__', 'node_modules', 'codexrecords',
           'records.sqlite', 'project_state.json', 'memory.md', 'ai_rules.md', '.codex',
           '.netrc', '.npmrc', '.pypirc', 'id_rsa', 'id_ed25519', '.cache', 'cache', 'caches', 'backup', 'backups'}
SECRET = re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY|(?:password|passwd|api[_-]?key|access[_-]?token|wifi[_-]?(?:password|pass|ssid))["\x27]?\s*[=:]\s*["\x27]?[^\s"\x27,;}]{3,}', re.I)


def text(value, name):
    if not isinstance(value, str) or not value.strip() or len(value) > 4096:
        raise ValueError(name + ' must be nonempty text (max 4096 chars)')
    if any(ord(c) < 32 for c in value):
        raise ValueError(name + ' must not contain control characters')
    return value


def array(value, name):
    if not isinstance(value, list):
        raise ValueError(name + ' must be an array')
    return value


def obj(value, name):
    if not isinstance(value, dict):
        raise ValueError(name + ' must be an object')
    return value


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(data):
    return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')


def load(path):
    path = Path(path).resolve(strict=True)
    data = json.loads(path.read_text(encoding='utf-8-sig'), parse_constant=lambda v: (_ for _ in ()).throw(ValueError('nonfinite JSON number')))
    obj(data, 'configuration')
    if type(data.get('version')) is not int or data['version'] != 1:
        raise ValueError('configuration version must be 1')
    relative = data.get('project', '.')
    text(relative, 'project')
    if Path(relative).is_absolute() or PureWindowsPath(relative).is_absolute():
        raise ValueError('project must be relative to the config parent')
    root = (path.parent / relative).resolve(strict=True)
    if not root.is_dir():
        raise ValueError('project must be a directory')
    # The delivery list changes as files are prepared; omit it to avoid circular hashes.
    content = {k: v for k, v in data.items() if k != 'deliverables'}
    return {'data': data, 'root': root, 'path': path, 'config_sha256': digest(canonical(content))}


def provenance(project, include_sources=False):
    data = project['data']
    result = {'tool_version': TOOL_VERSION, 'project_id': data.get('project_id'),
              'revision': data.get('revision'), 'config_sha256': project['config_sha256']}
    if include_sources:
        result['source_sha256'] = source_snapshot(project)
    return result


def local(project, value, exists=True):
    text(value, 'file path')
    pure = PureWindowsPath(value)
    if pure.drive or value.startswith(('/', '\\')) or '..' in pure.parts or ':' in value:
        raise ValueError('file paths must be project-relative without traversal or drive names')
    path = project['root'].joinpath(*pure.parts).resolve()
    if not path.is_relative_to(project['root']):
        raise ValueError('file escapes project (including symlink)')
    if exists and not path.is_file():
        raise ValueError('required file missing: ' + value)
    return path


def read_file(path, maximum=MAX_FILE_BYTES):
    with path.open('rb') as stream:
        data = stream.read(maximum + 1)
    if len(data) > maximum:
        raise ValueError('file exceeds limit: ' + path.name)
    return data


def source_snapshot(project):
    """Bind generated evidence to the explicit source/firmware delivery set, without a registry."""
    delivery = project['data'].get('deliverables', {})
    rows = delivery.get('files', []) if isinstance(delivery, dict) else []
    snapshot = {}
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict) or row.get('role') not in ('source', 'firmware') or not isinstance(row.get('path'), str):
            continue
        try:
            snapshot[row['path']] = digest(read_file(local(project, row['path'])))
        except (OSError, ValueError):
            snapshot[row['path']] = None  # Missing source does not block an unrelated useful stage.
    return snapshot


def fresh_output(path, project, inputs=()):
    path = Path(path).absolute()
    protected = [project['path'], *inputs]
    if path.exists() or path.is_symlink() or any(path.resolve() == p.resolve() for p in protected):
        raise ValueError('output must be a new path distinct from inputs: ' + str(path))
    return path


def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)


def json_bytes(data):
    return json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False).encode('utf-8') + b'\n'


def export_config(project, kind):
    data = project['data']
    if kind in ('test', 'flash'):
        payload = deepcopy(obj(data.get(kind), kind))
        result = {'version': 1, 'project': str(project['root']), kind: payload}
        for name in ('tools', 'build'):
            if name in data:
                result[name] = deepcopy(data[name])
        return result
    if kind != 'shopping':
        raise ValueError('unknown export kind')
    if 'materials' not in data and 'parts' in data:
        return deepcopy(data)  # Existing shopping inputs remain directly usable.
    shopping = deepcopy(obj(data.get('shopping'), 'shopping'))
    parts = []
    identifiers = set()
    for part in array(data.get('materials'), 'materials'):
        obj(part, 'material')
        identifier = text(part.get('id'), 'material.id')
        if identifier in identifiers:
            raise ValueError('material IDs must be unique')
        identifiers.add(identifier)
        for field in ('required', 'available'):
            if type(part.get(field)) is not int or not 0 <= part[field] <= 1000000000:
                raise ValueError('material.' + field + ' needs a known nonnegative integer')
        need = max(0, part['required'] - part['available'])
        if need:
            row = {k: deepcopy(v) for k, v in part.items() if k not in ('required', 'available', 'purpose', 'price')}
            row['quantity'] = need
            obj(row.get('required_specs'), 'material.required_specs')
            parts.append(row)
    shopping.update(version=1, project_id=data.get('project_id'), parts=parts)
    return shopping


def finite(value, name):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(name + ' must be a finite number')
    return value


def parts(project):
    lines = []
    materials = array(project['data'].get('materials'), 'materials')
    if not materials:
        raise ValueError('complete nonempty materials list required')
    for index, part in enumerate(materials, 1):
        obj(part, 'material')
        model = text(part.get('model'), 'material.model')
        purpose = text(part.get('purpose'), 'material.purpose')
        specs = obj(part.get('required_specs'), 'required_specs')
        if not specs:
            raise ValueError('exact material specifications required')
        for key, value in specs.items():
            text(key, 'specification key')
            if isinstance(value, str):
                text(value, 'specification')
            elif type(value) in (int, float):
                finite(value, 'specification')
            elif type(value) is not bool:
                raise ValueError('material specifications must be scalar values')
        for field in ('required', 'available'):
            if type(part.get(field)) is not int or not 0 <= part[field] <= 1000000000:
                raise ValueError('known physical quantities required')
        search = text(part.get('search_text'), 'material.search_text (include specs and pack quantity)')
        estimate = part.get('price')
        cost = 'Unknown estimate; no price evidence yet'
        if estimate is not None:
            obj(estimate, 'material.price')
            amount = finite(estimate.get('estimated_missing_total'), 'estimated missing total')
            if amount < 0:
                raise ValueError('estimated cost must be nonnegative')
            cost = str(amount) + ' ' + text(estimate.get('currency'), 'price currency')
            cost += '; evidence: ' + text(estimate.get('source'), 'price source') + '; observed: ' + text(estimate.get('observed_at'), 'price observation date')
        lines.extend([f'{index}. {model}; ' + ', '.join(f'{k}={v}' for k, v in specs.items()),
                      f'   Purpose: {purpose}. Required: {part["required"]}; owned: {part["available"]}; missing: {max(0, part["required"] - part["available"])}. Estimated missing cost: {cost}.',
                      '   Search (copy): ' + search])
    artifact_text = '<!-- ' + marker(project) + ' -->\n' + '\n'.join(lines) + '\n'
    shopping = obj(project['data'].get('shopping', {}), 'shopping')
    state = shopping.get('cart_offer', 'not-offered')
    if state not in {'not-offered', 'offered', 'accepted', 'declined'}:
        raise ValueError('unsupported cart_offer state')
    if state == 'not-offered':
        lines.extend(['', 'Would you like help choosing missing parts and adding them to your cart?'])
    if state == 'accepted':
        lines.extend(['', 'Cart only: no checkout, order, payment or subscription.'])
        if not shopping.get('site'):
            lines.append('Which shopping website should I use?')
    return {'text': '\n'.join(lines), 'artifact_text': artifact_text,
            'cart_offer': 'offered' if state == 'not-offered' else state,
            'site': shopping.get('site'), 'cart_mutated': False}


def checked_wiring(project):
    wiring = obj(project['data'].get('wiring'), 'wiring')
    if 'simulatorPins' in wiring or 'ledPin' in wiring:
        raise ValueError('legacy UNO wiring: preserve original; AI must add checked components/pins in a new project config, never infer missing electrical facts')
    components = array(wiring.get('components'), 'wiring.components')
    wires = array(wiring.get('connections'), 'wiring.connections')
    if not components or not wires or len(components) > 40 or len(wires) > 160:
        raise ValueError('wiring needs 1..40 components and 1..160 connections; split larger diagrams')
    pins, names, pending = {}, set(), []
    roles = {'input', 'output', 'open-drain', 'bidirectional', 'power', 'ground', 'passive', 'unknown'}
    for component in components:
        obj(component, 'component')
        name = text(component.get('id'), 'component.id')
        if ':' in name or name in names:
            raise ValueError('component IDs must be unique and contain no colon')
        names.add(name)
        text(component.get('model'), 'component.model')
        if not component.get('orientation'):
            pending.append(name + ': physical orientation unknown; logical pin order only')
        component_pins = array(component.get('pins'), 'component.pins')
        if not component_pins or len(component_pins) > 100:
            raise ValueError('component needs 1..100 explicit pins')
        for pin in component_pins:
            obj(pin, 'pin')
            identifier = text(pin.get('id'), 'pin.id')
            endpoint = name + ':' + identifier
            if ':' in identifier or endpoint in pins:
                raise ValueError('pin IDs must be unique per component and contain no colon')
            role = pin.get('role', 'unknown')
            if role not in roles:
                raise ValueError('unsupported pin role: ' + str(role))
            if pin.get('voltage_v') is not None:
                finite(pin['voltage_v'], 'pin.voltage_v')
            if pin.get('accepts_v') is not None:
                values = array(pin['accepts_v'], 'pin.accepts_v')
                if len(values) != 2 or finite(values[0], 'min voltage') > finite(values[1], 'max voltage'):
                    raise ValueError('accepts_v needs [min,max]')
            if role == 'ground' and pin.get('voltage_v') not in (None, 0):
                raise ValueError('ground voltage conflicts with zero')
            if role == 'unknown' or pin.get('voltage_v') is None or pin.get('accepts_v') is None:
                pending.append(endpoint + ': electrical metadata incomplete')
            pins[endpoint] = pin
    parent = {key: key for key in pins}

    def find(key):
        while parent[key] != key:
            key = parent[key]
        return key

    wire_ids, edges = set(), set()
    for wire in wires:
        obj(wire, 'connection')
        identifier = text(wire.get('id'), 'wire.id')
        a, b = wire.get('from'), wire.get('to')
        if not isinstance(a, str) or not isinstance(b, str) or a not in pins or b not in pins or a == b:
            raise ValueError('unknown or invalid connection endpoint')
        edge = tuple(sorted((a, b)))
        if identifier in wire_ids or edge in edges:
            raise ValueError('repeated wire ID or connection')
        wire_ids.add(identifier)
        edges.add(edge)
        parent[find(a)] = find(b)
    nets = {}
    for endpoint, pin in pins.items():
        nets.setdefault(find(endpoint), []).append((endpoint, pin))
    for net in nets.values():
        levels = {p['voltage_v'] for _, p in net if p.get('voltage_v') is not None}
        if len(levels) > 1:
            raise ValueError('conflicting explicit voltages on a connected net')
        if sum(p.get('role') == 'output' for _, p in net) > 1:
            raise ValueError('multiple push-pull output assignments on a net')
        for level in levels:
            for endpoint, pin in net:
                limits = pin.get('accepts_v')
                if limits and not limits[0] <= level <= limits[1]:
                    raise ValueError('voltage exceeds explicit limits at ' + endpoint)
    bindings = array(wiring.get('bindings', []), 'wiring.bindings')
    symbols, assigned = set(), set()
    for binding in bindings:
        obj(binding, 'binding')
        symbol = text(binding.get('symbol'), 'binding.symbol')
        endpoint = binding.get('endpoint')
        if not isinstance(endpoint, str) or endpoint not in pins or symbol in symbols or endpoint in assigned:
            raise ValueError('unknown or conflicting firmware pin binding')
        symbols.add(symbol)
        assigned.add(endpoint)
    pending.append('Logical review only: verify actual models, source pin alignment, current, loads, protection and physical wiring before power.')
    return wiring, pins, pending


def marker(project):
    return ('mcu-project-sha256:' + project['config_sha256'] +
            ' mcu-source-sha256:' + digest(canonical(source_snapshot(project))))


def wiring_artifacts(project):
    data, pins, pending = checked_wiring(project)
    # One wire list drives all three artifacts; positions express logical order only.
    width = 1400
    height = 160 + 88 * len(data['connections'])
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
           '<rect width="100%" height="100%" fill="#f8fafc"/>',
           '<style>text{font-family:Arial,sans-serif;fill:#172033;font-size:16px}.small{font-size:13px}</style>',
           f'<metadata>{marker(project)}</metadata>',
           '<text x="32" y="35">Wiring — logical diagram; pin positions are not physical positions</text>',
           '<text x="32" y="62" class="small">Read the numbered table. Crossings are not joins; matching endpoint names identify shared nets.</text>']
    models = {c['id']: c for c in data['components']}
    table = [f'<!-- {marker(project)} -->', '# Logical wiring / 逻辑接线', '',
             'Logical endpoint order only. Do not use this as a physical pin map. / 不能当作实物引脚位置图。', '',
             '| # | Wire | From (model / pin) | To (model / pin) | Explicit voltage |',
             '| --- | --- | --- | --- | --- |']

    def label(endpoint):
        component = models[endpoint.split(':')[0]]
        pin = pins[endpoint]
        return f'{endpoint} — {component["model"]} / {pin.get("label", endpoint.split(":")[1])}'

    for number, wire in enumerate(data['connections'], 1):
        y = 115 + 88 * (number - 1)
        values = {pins[e]['voltage_v'] for e in (wire['from'], wire['to']) if pins[e].get('voltage_v') is not None}
        volts = ', '.join(str(x) + ' V' for x in sorted(values)) or 'unknown / 待确认'
        # Short lines never cross; shared names indicate a bus or common ground.
        svg.extend([f'<rect x="24" y="{y-30}" width="1352" height="74" rx="8" fill="white" stroke="#cbd5e1"/>',
                    f'<text x="40" y="{y}">{number}. {escape(wire["id"])}</text>',
                    f'<text x="150" y="{y-6}" textLength="490" lengthAdjust="spacingAndGlyphs">{escape(label(wire["from"]))}</text>',
                    f'<path d="M650 {y} H750" stroke="#2563eb" stroke-width="3"/>',
                    f'<circle cx="650" cy="{y}" r="4" fill="#2563eb"/><circle cx="750" cy="{y}" r="4" fill="#2563eb"/>',
                    f'<text x="770" y="{y-6}" textLength="585" lengthAdjust="spacingAndGlyphs">{escape(label(wire["to"]))}</text>',
                    f'<text x="150" y="{y+24}" class="small">Voltage: {escape(volts)}</text>'])
        safe = lambda value: str(value).replace('|', '&#124;')
        table.append(f'| {number} | {safe(wire["id"])} | {safe(label(wire["from"]))} | {safe(label(wire["to"]))} | {safe(volts)} |')
    svg.append('</svg>')
    table.extend(['', '## Models and orientation / 型号与方向', ''])
    for c in data['components']:
        table.append(f'- {c["id"]}: {c["model"]}; {c.get("orientation") or "unknown orientation"}.')
    table.extend(['', '## Pending / 待核对', '', *['- ' + p for p in pending]])
    record = {'version': 1, **provenance(project, True), 'diagram_kind': 'logical',
              'components': data['components'], 'connections': data['connections'],
              'bindings': data.get('bindings', []), 'electrical_status': 'needs-confirmation', 'pending': pending}
    contents = ['\n'.join(svg).encode('utf-8'), '\n'.join(table).encode('utf-8'), json_bytes(record)]
    return list(zip(('wiring.svg', 'connections.md', 'pins.generated.json'), contents)), pending


def wiring(project, output):
    artifacts, pending = wiring_artifacts(project)
    targets = [fresh_output(Path(output) / name, project) for name, _ in artifacts]
    for target, (_, content) in zip(targets, artifacts):
        write_new(target, content)
    return {'files': [str(p) for p in targets], 'pending': pending}


def acceptance_items(project):
    items, identifiers = [], set()
    for supplied in array(project['data'].get('acceptance'), 'acceptance'):
        item = deepcopy(obj(supplied, 'acceptance item'))
        identifier = text(item.get('id'), 'acceptance.id')
        if identifier in identifiers:
            raise ValueError('acceptance IDs must be unique')
        identifiers.add(identifier)
        text(item.get('behavior'), 'acceptance.behavior')
        steps = array(item.get('steps'), 'acceptance.steps')
        if not steps:
            raise ValueError('acceptance steps must not be empty')
        for step in steps:
            text(step, 'acceptance step')
        text(item.get('expected'), 'acceptance.expected')
        status = item.get('status', 'not-run')
        if status not in ('not-run', 'pass', 'fail', 'needs-confirmation'):
            raise ValueError('unsupported acceptance status')
        evidence = []
        for value in array(item.get('evidence', []), 'acceptance.evidence'):
            path = local(project, value)
            evidence.append({'path': value, 'sha256': digest(read_file(path))})
        if status in ('pass', 'fail') and not evidence:
            raise ValueError('pass/fail requires supplied existing evidence; no inferred passes')
        item.update(status=status, evidence=evidence)
        items.append(item)
    return items


def acceptance(project, output):
    items = acceptance_items(project)
    report = {'version': 1, **provenance(project, True), 'items': items,
              'limits': ['Statuses are supplied observations bound to file hashes; this command does not run or judge tests.']}
    directory = Path(output)
    targets = [fresh_output(directory / name, project) for name in ('acceptance.json', 'acceptance.md')]
    evidence_hash = digest(canonical({e['path']: e['sha256'] for item in items for e in item['evidence']}))
    lines = [f'<!-- {marker(project)} mcu-evidence-sha256:{evidence_hash} -->', '# Behavior checks / 行为验收', '', report['limits'][0], '']
    for item in items:
        lines.extend([f'## {item["id"]}: {item["behavior"]} [{item["status"]}]', '',
                      *[f'{i}. {step}' for i, step in enumerate(item['steps'], 1)], '',
                      'Expected / 预期: ' + item['expected'],
                      'Evidence / 证据: ' + (', '.join(e['path'] + ' SHA256 ' + e['sha256'] for e in item['evidence']) or 'none; not verified'), ''])
    write_new(targets[0], json_bytes(report))
    write_new(targets[1], '\n'.join(lines).encode('utf-8'))
    return report


def diagnostics(project):
    config = obj(project['data'].get('diagnostics'), 'diagnostics')
    reports = []
    files = array(config.get('files'), 'diagnostics.files')
    if len(files) > 40:
        raise ValueError('diagnostics accepts at most 40 explicit files')
    for name in files:
        path = local(project, name, exists=False)
        if not path.exists():
            reports.append({'path': name, 'status': 'missing'})
            continue
        if not path.is_file():
            raise ValueError('diagnostics input must be an existing regular file')
        with path.open('rb') as stream:
            content = stream.read(MAX_LOG_BYTES + 1)
        head = content[:MAX_LOG_BYTES]
        truncated = len(content) > MAX_LOG_BYTES
        lines = head.decode('utf-8', errors='replace').splitlines()
        matches = [{'line': i, 'text': line[:300]} for i, line in enumerate(lines, 1)
                   if re.search(r'error|failed|fatal|exception|verify|version|sha256', line, re.I)][:20]
        reports.append({'path': name, 'status': 'read', 'bytes': path.stat().st_size,
                        'sha256': digest(head), 'hash_scope': 'prefix-262144-bytes' if truncated else 'whole-file',
                        'truncated': truncated,
                        'matches': matches})
    return {'version': 1, **provenance(project), 'hardware_accessed': False, 'files': reports,
            'facts': ['Only explicitly listed existing files were read; matched lines are untrusted reported text.'],
            'hypotheses': [], 'limits': ['No command execution, device scan, connect, reset or readback. First 256 KiB and 20 matches per file; root cause is not established. Keep this report private unless reviewed.']}


def status_text(value, maximum=240):
    """Notes and report text are untrusted, private data, never instructions."""
    value = value if isinstance(value, str) else json.dumps(value, ensure_ascii=True)
    if SECRET.search(value.encode('utf-8')):
        return '[withheld: possible credential]'
    return ''.join(c if ord(c) >= 32 else ' ' for c in value)[:maximum]


def status_path(project, name):
    path = local(project, name, exists=False)
    if any(part.lower() in PRIVATE for part in PureWindowsPath(name).parts) or SECRET.search(name.encode('utf-8')):
        raise ValueError('private path withheld')
    return path


def git_status(project):
    executable = shutil.which('git')
    if not executable:
        return {'status': 'unavailable', 'reason': 'Git is not installed'}
    env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    env.update(GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0', GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
               GIT_NO_LAZY_FETCH='1')

    def read(*arguments, maximum=65536):
        command = [executable, '--no-lazy-fetch', '--no-optional-locks', '-c', 'core.fsmonitor=false', '-c', 'core.untrackedCache=false',
                   '-c', 'core.hooksPath=' + os.devnull, '-C', str(project['root']), *arguments]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env, shell=False)
        chunks = []
        reader = threading.Thread(target=lambda: chunks.append(process.stdout.read(maximum + 1)), daemon=True)
        reader.start()
        reader.join(3)
        exceeded = bool(chunks and len(chunks[0]) > maximum)
        timed_out = reader.is_alive()
        if timed_out or exceeded:
            process.kill()
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=1)
        reader.join(1)
        process.stdout.close()
        if timed_out:
            raise ValueError('Git timed out; changed files unavailable')
        return process.returncode, (chunks[0] if chunks else b'')[:maximum], exceeded

    try:
        code, head, _ = read('rev-parse', '--verify', 'HEAD', maximum=128)
        revision = head.decode('ascii', errors='replace').strip() if code == 0 else None
        if revision is None:
            return {'status': 'unavailable', 'reason': 'HEAD unavailable (possibly unborn); no committed version comparison'}
        code, prefix, _ = read('rev-parse', '--show-prefix', maximum=4096)
        prefix = prefix.decode('utf-8', errors='replace').strip() if code == 0 else ''
        code, output, truncated = read('ls-files', '--stage', '--full-name', '-z', '--', '.')
        if code and not truncated:
            return {'status': 'unavailable', 'reason': 'Not a readable Git worktree'}
        code, tree, tree_truncated = read('ls-tree', '--full-tree', '-r', '-z', 'HEAD', '--', prefix or '.')
        if code or tree_truncated:
            return {'status': 'unavailable', 'head': revision, 'reason': 'Committed tree unavailable or exceeds read bounds; no fetch attempted'}
        index, committed = {}, {}
        for records, target, is_index in ((output, index, True), (tree, committed, False)):
            for row in records.split(b'\0')[:-1]:
                metadata, name = row.split(b'\t', 1)
                mode, identity, stage = metadata.split(b' ') if is_index else (metadata.split(b' ')[0], metadata.split(b' ')[2], b'0')
                target[name.decode('utf-8', errors='replace')] = (mode, identity, stage)
        changed = []
        withheld, checked = 0, 0
        unread = []
        names = list(dict.fromkeys([*index, *committed]))
        for full_name in names:
            name = full_name
            if prefix:
                if not name.startswith(prefix):
                    continue
                name = name[len(prefix):]
            try:
                path = status_path(project, name)
                if checked >= 40:
                    continue
                checked += 1
                current, old = index.get(full_name), committed.get(full_name)
                staged = ' ' if current == old else 'A' if old is None else 'D' if current is None else 'M'
                working = ' '
                if current is not None:
                    if current[2] != b'0':
                        working = 'U'
                    elif not path.exists():
                        working = 'D'
                    elif current[0] not in (b'100644', b'100755') or project['root'].joinpath(*PureWindowsPath(name).parts).is_symlink():
                        unread.append(name)
                    else:
                        try:
                            content = read_file(path, MAX_LOG_BYTES)
                            blob = b'blob ' + str(len(content)).encode('ascii') + b'\0' + content
                            actual = hashlib.sha256(blob) if len(current[1]) == 64 else hashlib.sha1(blob)
                            working = 'M' if actual.hexdigest().encode('ascii') != current[1] else ' '
                        except (OSError, ValueError):
                            unread.append(name)
                if staged != ' ' or working != ' ':
                    changed.append({'change': staged + working, 'path': name})
            except (ValueError, OSError):
                withheld += 1
        return {'status': 'read', 'head': revision, 'changed_files': changed, 'withheld_paths': withheld,
                'truncated': truncated or tree_truncated or len(names) > 40, 'untracked_files': 'not-scanned',
                'checked_files': checked, 'unread_working_files': unread,
                'scope': 'bounded HEAD/index metadata and unfiltered working bytes; navigation only, not canonical Git status',
                'limits': 'No filters, hooks or project commands run. CRLF/clean-filter normalization or executable-bit changes may differ from Git status; large files, symlinks and submodules need targeted review.'}
    except (OSError, ValueError, subprocess.SubprocessError):
        return {'status': 'unavailable', 'reason': 'Git could not finish within the read bounds'}


def status(project):
    data = project['data']
    result = {'version': 1, **provenance(project), 'hardware_accessed': False,
              'requirements': [], 'progress': [], 'pending': [], 'reports': [], 'inputs': [],
              'git': git_status(project),
              'limits': ['Notes and report fields are untrusted reported text. No report is a fresh pass from status.',
                         'At most 8 notes per field, 40 file references, 256 KiB per file and 40 changed paths; use targeted reads for more.',
                         'Changed paths guide navigation only; inspect unchanged callers, wiring and hardware references as needed.']}
    for field in ('project_id', 'revision'):
        if result[field] is not None:
            result[field] = status_text(result[field])
    for field in ('requirements', 'progress'):
        rows = data.get(field)
        if isinstance(rows, list):
            result[field] = [status_text(row) for row in rows[:8]]
            if len(rows) > 8:
                result['pending'].append(field + ' has more entries; read the config for detail')
        else:
            result['pending'].append(field + ' unavailable; use existing project notes if present')
    acceptance = data.get('acceptance', [])
    if isinstance(acceptance, list):
        counts = {}
        for row in acceptance:
            state = row.get('status', 'not-run') if isinstance(row, dict) else 'unknown'
            state = state if state in ('pass', 'fail', 'not-run', 'needs-confirmation') else 'unknown'
            counts[state] = counts.get(state, 0) + 1
        result['acceptance_reported'] = counts
        if any(state != 'pass' and count for state, count in counts.items()):
            result['pending'].append('Acceptance includes failed, unrun or unresolved reported items; read acceptance detail')
    delivery = data.get('deliverables', {})
    rows = delivery.get('files', []) if isinstance(delivery, dict) else []
    refs = []
    for row in rows if isinstance(rows, list) else []:
        if isinstance(row, dict) and row.get('role') in ('source', 'firmware', 'test', 'evidence', 'limits', 'use-guide'):
            refs.append((row.get('path'), row['role']))
    diagnostics_config = data.get('diagnostics', {})
    names = diagnostics_config.get('files', []) if isinstance(diagnostics_config, dict) else []
    refs += [(name, 'report') for name in names] if isinstance(names, list) else []
    if len(refs) > 40:
        result['pending'].append('More file references exist; read the relevant allowlist')
    seen = set()
    for name, role in refs[:40]:
        if not isinstance(name, str) or name in seen:
            continue
        seen.add(name)
        row = {'path': name, 'role': role}
        target = result['inputs'] if role in ('source', 'firmware') else result['reports']
        try:
            path = status_path(project, name)
            content = read_file(path, MAX_LOG_BYTES)
            row.update(status='read', sha256=digest(content))
            if role not in ('source', 'firmware'):
                row['freshness'] = 'unverified-existing-reference'
                if SECRET.search(content):
                    row['content'] = 'withheld: possible credential'
                elif path.suffix.lower() == '.json':
                    report = json.loads(content)
                    if isinstance(report, dict):
                        for field in ('status', 'revision', 'config_sha256', 'configuration_sha256'):
                            if field in report:
                                row['reported_' + field] = status_text(report[field])
                        if report.get('config_sha256') == project['config_sha256']:
                            row['freshness'] = 'config-matches-only; source/runtime/physical freshness not established'
                        elif report.get('config_sha256'):
                            row['freshness'] = 'different-config; not current evidence'
                elif role in ('limits', 'use-guide'):
                    row['note_excerpt'] = status_text(content.decode('utf-8', errors='replace'))
        except (ValueError, OSError, TypeError):
            # Do not echo unsafe paths or raw parser errors, which may contain secrets.
            row = {'role': role, 'status': 'unavailable', 'reason': 'missing, private, unsafe, invalid or larger than 256 KiB'}
        target.append(row)
    if not result['reports']:
        result['pending'].append('No explicit report or note references available')
    return result


FINAL_ROLES = {'materials', 'wiring-image', 'wiring-text', 'source', 'build-config',
               'dependencies', 'build-guide', 'flash-guide', 'power-assembly', 'use-guide',
               'acceptance-guide', 'license', 'evidence', 'limits'}
RESOURCE_ROLES = {
    'pcb': {'pcb-source', 'schematic', 'pcb-layout', 'pcb-bom', 'pcb-nets', 'pcb-checks', 'pcb-manufacture'},
    'mechanical': {'mechanical-source', 'mechanical-export'},
    'print': {'print-source', 'print-export'},
}
GUIDE_SECTIONS = {
    'build-guide': ('tools', 'build', 'expected', 'failure'),
    'flash-guide': ('target', 'steps', 'expected', 'failure'),
    'power-assembly': ('power', 'assembly', 'safety'),
    'use-guide': ('steps', 'expected', 'failure'),
    'acceptance-guide': ('steps', 'expected', 'proof'),
    'dependencies': ('bundled', 'external'),
    'license': ('license', 'attribution'),
    'limits': ('proof', 'limits'),
}


def final_content(project, files, payloads):
    """Bind exact BOM/wires and require substantive versioned guide sections."""
    expected_bom = parts(project)['artifact_text'].encode('utf-8')
    artifacts, _ = wiring_artifacts(project)
    wiring_bytes = dict(artifacts)
    if not any(row['role'] == 'dependencies' and Path(row['path']).suffix.lower() == '.md' for row in files):
        raise ValueError('dependencies requires a versioned Markdown inventory/setup guide')
    for row in files:
        content = payloads[row['path']]
        role = row['role']
        if role == 'materials' and content != expected_bom:
            raise ValueError('final materials must match current parts artifact_text: ' + row['path'])
        if role in ('wiring-image', 'wiring-text'):
            expected = wiring_bytes['wiring.svg' if role == 'wiring-image' else 'connections.md']
            if content != expected:
                raise ValueError('final wiring must match current generated data/provenance: ' + row['path'])
            if role == 'wiring-image':
                try:
                    image = ElementTree.fromstring(content)
                except ElementTree.ParseError as exc:
                    raise ValueError('final wiring image must be a valid generated SVG') from exc
                if image.tag != '{http://www.w3.org/2000/svg}svg':
                    raise ValueError('final wiring image must be SVG')
        if role in GUIDE_SECTIONS and (role != 'dependencies' or Path(row['path']).suffix.lower() == '.md'):
            try:
                guide = content.decode('utf-8')
            except UnicodeDecodeError as exc:
                raise ValueError('final guide must be UTF-8: ' + row['path']) from exc
            if '<!-- ' + marker(project) + ' -->' not in guide:
                raise ValueError('final guide needs current config/source provenance: ' + row['path'])
            sections = re.findall(r'<!-- mcu-section:([a-z-]+) -->\s*(.*?)(?=<!-- mcu-section:|\Z)', guide, re.S)
            values = dict(sections)
            if len(values) != len(sections):
                raise ValueError('duplicate final guide section: ' + row['path'])
            for key in GUIDE_SECTIONS[role]:
                body = re.sub(r'<!--.*?-->', '', values.get(key, ''), flags=re.S)
                body = re.sub(r'^\s*#.*$', '', body, flags=re.M).strip()
                if (len(re.sub(r'\W', '', body)) < 32 or
                        re.search(r'(?im)^\s*(?:[-*]\s*)?(?:TODO|TBD|FIXME|PLACEHOLDER)\b', body)):
                    raise ValueError('missing or non-substantive final guide section ' + key + ': ' + row['path'])


def reproducibility(project, files, contents):
    """Check a reviewed dependency inventory and build witness, never execute supplied code."""
    data = project['data']
    spec = obj(data['deliverables'].get('reproducibility'), 'deliverables.reproducibility')
    if SECRET.search(canonical(spec)):
        raise ValueError('possible credential detected in reproducibility metadata')
    if spec.get('revision') != data['revision']:
        raise ValueError('reproducibility revision mismatch')
    if array(spec.get('critical_unknowns'), 'critical_unknowns'):
        raise ValueError('unresolved critical facts block reproducible delivery')
    if type(spec.get('firmware_required')) is not bool:
        raise ValueError('firmware_required must be an explicit boolean')
    resources = array(spec.get('used_resources'), 'used_resources')
    if any(not isinstance(r, str) or r not in RESOURCE_ROLES for r in resources):
        raise ValueError('unsupported used resource')
    required_roles = set(FINAL_ROLES)
    if spec['firmware_required']:
        required_roles.add('firmware')
    for resource in resources:
        required_roles.update(RESOURCE_ROLES[resource])
    roles = {row['role'] for row in files}
    if required_roles - roles:
        raise ValueError('missing final artifact roles: ' + ', '.join(sorted(required_roles - roles)))
    parts(project)  # Require exact BOM quantities/specs/search text; unknown estimates remain visible.
    wiring_data, pins, pending = checked_wiring(project)
    if len(pending) != 1:
        raise ValueError('essential pin/orientation/electrical facts remain unknown')
    payloads = dict(contents)
    final_content(project, files, payloads)
    inventory = {row['path']: row['sha256'] for row in files}

    def included(value, name):
        path = local(project, text(value, name))
        relative = path.relative_to(project['root']).as_posix()
        if relative not in inventory:
            raise ValueError(name + ' must be an allowlisted packaged file: ' + relative)
        return relative

    inputs = array(spec.get('required_inputs'), 'required_inputs')
    if not inputs:
        raise ValueError('required_inputs must list all project-specific build inputs')
    input_paths = {included(p, 'required input') for p in inputs}
    build_roles = {'source', 'build-config', 'dependencies'}
    if {f['path'] for f in files if f['role'] in build_roles} - input_paths:
        raise ValueError('source/build/dependency artifacts missing from required_inputs')
    # Quoted C/C++ includes must resolve inside the declared package inventory.
    include_dirs = array(spec.get('include_dirs', []), 'include_dirs')
    for directory in include_dirs:
        text(directory, 'include directory')
        if PureWindowsPath(directory).drive or '..' in PureWindowsPath(directory).parts or directory.startswith(('/', '\\')):
            raise ValueError('include directory must be project-relative')
    for name in input_paths:
        if Path(name).suffix.lower() not in {'.c', '.h', '.cpp', '.hpp', '.cc', '.ino'}:
            continue
        for header in re.findall(rb'^\s*#\s*include\s*"([^"\r\n]+)"', payloads[name], re.M):
            reference = header.decode('utf-8')
            candidates = [str(Path(name).parent / reference), *[str(Path(d) / reference) for d in include_dirs]]
            resolved = []
            for candidate in candidates:
                try:
                    resolved.append(included(candidate, 'quoted include'))
                except (ValueError, OSError):
                    pass
            if not any(p in input_paths for p in resolved):
                raise ValueError('missing packaged quoted include: ' + name + ': ' + reference)
    for name in input_paths:
        if re.search(rb'(?:[A-Za-z]:[\\/](?:Users|home)[\\/]|/(?:home|Users)/[^\s/]+/)', payloads[name]):
            raise ValueError('private absolute path in build inputs: ' + name)
    tools = array(spec.get('toolchain'), 'toolchain')
    if not tools:
        raise ValueError('exact toolchain required')
    prerequisites = array(spec.get('external_prerequisites'), 'external_prerequisites')
    for tool in tools + prerequisites:
        obj(tool, 'tool/prerequisite')
        text(tool.get('name'), 'tool name')
        text(tool.get('version'), 'tool exact version')
        url = urlsplit(text(tool.get('official_url'), 'official URL'))
        if url.scheme != 'https' or not url.hostname or url.username or url.password:
            raise ValueError('official acquisition URL must be HTTPS without credentials')
        included(tool.get('setup'), 'tool setup instructions')
    facts = obj(spec.get('essential_facts'), 'essential_facts')
    for key in ('parts', 'pins', 'power', 'build', 'assembly'):
        evidence = array(facts.get(key), 'essential_facts.' + key)
        if not evidence:
            raise ValueError('missing essential fact evidence: ' + key)
        for name in evidence:
            included(name, 'essential fact evidence')
    for resource in resources:
        if not array(facts.get(resource), 'essential_facts.' + resource):
            raise ValueError('missing resource facts: ' + resource)
        for name in facts[resource]:
            included(name, 'resource fact evidence')
    proof_name = included(spec.get('build_evidence'), 'build evidence')
    proof = obj(json.loads(payloads[proof_name]), 'build evidence')
    expected = {p: inventory[p] for p in input_paths}
    firmware = {f['path']: f['sha256'] for f in files if f['role'] == 'firmware'}
    if (proof.get('status') != 'passed' or proof.get('revision') != data['revision'] or
            proof.get('config_sha256') != project['config_sha256'] or proof.get('input_sha256') != expected or
            proof.get('firmware_sha256') != firmware or proof.get('toolchain') != tools):
        raise ValueError('build evidence must bind successful build, exact inputs/firmware/toolchain and current revision/config')
    text(proof.get('command'), 'observed build command')
    proof_status = obj(spec.get('proof_status'), 'proof_status')
    for key in ('build', 'logic', 'simulation', 'electrical', 'flash', 'physical'):
        if proof_status.get(key) not in {'passed', 'failed', 'not-run', 'not-applicable', 'limited'}:
            raise ValueError('explicit proof status required: ' + key)
    if proof_status['build'] != 'passed':
        raise ValueError('final build proof must be passed')
    # Only the reviewed contract is exported; unknown extra metadata is not public package content.
    keys = ('revision', 'critical_unknowns', 'firmware_required', 'used_resources', 'required_inputs',
            'include_dirs', 'toolchain', 'external_prerequisites', 'essential_facts', 'build_evidence', 'proof_status')
    result = {key: deepcopy(spec[key]) for key in keys if key in spec}
    for key in ('toolchain', 'external_prerequisites'):
        result[key] = [{field: item[field] for field in ('name', 'version', 'official_url', 'setup')} for item in result[key]]
    result['essential_facts'] = {key: result['essential_facts'][key] for key in ('parts', 'pins', 'power', 'build', 'assembly', *resources)}
    result['proof_status'] = {key: result['proof_status'][key] for key in ('build', 'logic', 'simulation', 'electrical', 'flash', 'physical')}
    return result


def package(project, output, reproducible=False):
    delivery = obj(project['data'].get('deliverables'), 'deliverables')
    revision = text(project['data'].get('revision'), 'revision')
    if delivery.get('revision') != revision:
        raise ValueError('deliverables revision is stale or missing')
    rows = array(delivery.get('files'), 'deliverables.files')
    if not rows:
        raise ValueError('explicit nonempty deliverables allowlist required')
    output = fresh_output(output, project)
    if output.suffix.casefold() != '.zip':
        raise ValueError('package output must be a new .zip file')
    files, contents, seen = [], [], set()
    allowed_roles = FINAL_ROLES | {'firmware', 'wiring', 'test'} | set().union(*RESOURCE_ROLES.values())
    for entry in rows:
        obj(entry, 'deliverable')
        name = text(entry.get('path'), 'deliverable.path')
        parts = PureWindowsPath(name).parts
        if any(p.casefold() in PRIVATE or p.casefold().startswith('.env') for p in parts):
            raise ValueError('private/cache/credential file refused: ' + name)
        if Path(name).suffix.casefold() in {'.log', '.sqlite', '.db', '.pem', '.key', '.pfx'}:
            raise ValueError('private log/database/key file refused: ' + name)
        path = local(project, name)
        if path == project['path'] or path == output.resolve():
            raise ValueError('package cannot overwrite or include its input config/output')
        archive_name = '/'.join(parts)
        if archive_name.casefold() in seen or archive_name.casefold() in {'manifest.json', 'start-here.md'}:
            raise ValueError('duplicate or reserved package name')
        seen.add(archive_name.casefold())
        if entry.get('role') not in allowed_roles:
            raise ValueError('deliverable needs a supported role')
        content = read_file(path)
        if reproducible and not content.strip():
            raise ValueError('empty final artifact: ' + name)
        if reproducible and content.strip().upper() in {b'TODO', b'TBD', b'FIXME', b'PLACEHOLDER'}:
            raise ValueError('placeholder final artifact: ' + name)
        hashed = digest(content)
        if entry.get('sha256') != hashed:
            raise ValueError('missing or stale expected hash: ' + name)
        if SECRET.search(content):
            raise ValueError('possible credential detected; review/remove before packaging: ' + name)
        markers = re.findall(rb'mcu-project-sha256:([0-9a-f]{64})', content)
        if any(m.decode() != project['config_sha256'] for m in markers):
            raise ValueError('stale generated artifact: ' + name)
        source_markers = re.findall(rb'mcu-source-sha256:([0-9a-f]{64})', content)
        if any(m.decode() != digest(canonical(source_snapshot(project))) for m in source_markers):
            raise ValueError('stale generated artifact source snapshot: ' + name)
        evidence_markers = re.findall(rb'mcu-evidence-sha256:([0-9a-f]{64})', content)
        if evidence_markers:
            items = acceptance_items(project)
            current_evidence = digest(canonical({e['path']: e['sha256'] for item in items for e in item['evidence']}))
            if any(m.decode() != current_evidence for m in evidence_markers):
                raise ValueError('stale generated artifact evidence: ' + name)
        if path.suffix.lower() == '.json':
            try:
                artifact = json.loads(content)
            except (ValueError, UnicodeDecodeError):
                artifact = None
            if isinstance(artifact, dict) and 'tool_version' in artifact and 'config_sha256' in artifact:
                if any(artifact.get(k) != v for k, v in provenance(project, True).items()):
                    raise ValueError('artifact version/project mismatch: ' + name)
                for item in artifact.get('items', []):
                    for evidence in item.get('evidence', []):
                        if digest(read_file(local(project, evidence['path']))) != evidence['sha256']:
                            raise ValueError('stale generated artifact evidence: ' + evidence['path'])
        files.append({'path': archive_name, 'role': entry['role'], 'bytes': len(content), 'sha256': hashed})
        contents.append((archive_name, content))
    final = reproducibility(project, files, contents) if reproducible else None
    if final is not None:
        start = ['# Start here — ' + revision, '', 'Use the exact specified parts and packaged guides. Hardware proof is separate.',
                 'External tools/dependencies below require acquisition/setup; this package is not a zero-download promise.', '']
        for item in final['toolchain'] + final['external_prerequisites']:
            start.append('- ' + item['name'] + ' ' + item['version'] + ': ' + item['official_url'] + '; setup: ' + item['setup'])
        start.extend(['', '## Packaged guides and files'] + ['- ' + f['role'] + ': ' + f['path'] for f in files] +
                     ['', 'Proof status: ' + json.dumps(final['proof_status']), '', 'Reviewed dependency inventory and build witness; transitive completeness and identical physical behavior are not mechanically proven.'])
        content = ('\n'.join(start) + '\n').encode('utf-8')
        files.append({'path': 'START-HERE.md', 'role': 'package-guide', 'bytes': len(content), 'sha256': digest(content)})
        contents.append(('START-HERE.md', content))
    report = {'version': 1, **provenance(project, True), 'files': files,
              'status': 'reproducible_artifacts' if reproducible else 'draft_unverified',
              'reproducibility': final,
              'limits': ['Checks validate supplied files, dependency inventory and build witness; they do not prove witness truth, all transitive dependencies, electrical safety or identical physical behavior. Review the complete application build and packaged instructions.'],
              'review_required': 'Caller must review all selected content for secrets and rights; detection is incomplete. Local ZIP creation grants no publication permission.'}
    manifest = json_bytes(report)
    for name, content in [*contents, ('manifest.json', manifest)]:
        if SECRET.search(content):
            raise ValueError('possible credential detected in final package content: ' + name)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=output.parent, suffix='.zip', delete=False) as stream:
            temporary = Path(stream.name)
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for name, content in contents:
                archive.writestr(name, content)
            archive.writestr('manifest.json', manifest)
        # Atomic no-overwrite publication. Refuse filesystems without hard-link support.
        os.link(temporary, output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return report


def validate(project, stage='project'):
    errors, pending = [], []
    data = project['data']
    try:
        if 'project_id' in data:
            text(data['project_id'], 'project_id')
        if stage in ('test', 'flash', 'shopping'):
            exported = export_config(project, stage)
            pending.append('Export shape checked; the existing runner/selector validates backend details and readiness.')
            if stage == 'shopping':
                for field in ('site', 'region', 'currency', 'candidates', 'cart'):
                    if exported.get(field) is None:
                        pending.append('shopping.' + field + ' unknown')
        elif stage == 'wiring':
            _, _, pending = checked_wiring(project)
        elif stage == 'acceptance':
            acceptance_items(project)
        elif stage == 'diagnostics':
            files = obj(data.get('diagnostics'), 'diagnostics').get('files')
            for name in array(files, 'diagnostics.files'):
                local(project, name, exists=False)
        elif stage != 'project':
            raise ValueError('unknown validation stage')
        else:
            for field in ('requirements', 'materials', 'acceptance', 'progress'):
                if field in data:
                    array(data[field], field)
            for field in ('test', 'flash', 'shopping', 'wiring', 'diagnostics', 'deliverables', 'tools'):
                if field in data:
                    obj(data[field], field)
            pending.append('Only supplied project structure checked; choose a stage for its required fields.')
    except (ValueError, TypeError, KeyError) as exc:
        errors.append(str(exc))
    return {'version': 1, **provenance(project), 'stage': stage, 'errors': errors, 'pending': pending}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['status', 'validate', 'export', 'parts', 'wiring', 'acceptance', 'diagnostics', 'package'])
    parser.add_argument('config', type=Path)
    parser.add_argument('--for', dest='kind', choices=['test', 'flash', 'shopping'])
    parser.add_argument('--stage', default='project', choices=['project', 'test', 'flash', 'shopping', 'wiring', 'acceptance', 'diagnostics'])
    parser.add_argument('--output', type=Path)
    parser.add_argument('--reproducible', action='store_true', help='require the final replication contract; default package is draft/unverified')
    args = parser.parse_args(argv)
    try:
        if args.command == 'status':
            read_file(args.config, MAX_LOG_BYTES)
            if args.output:
                raise ValueError('status is read-only; --output is not supported')
        project = load(args.config)
        if args.reproducible and args.command != 'package':
            raise ValueError('--reproducible is only valid with package')
        if args.command == 'status':
            result = status(project)
        elif args.command == 'validate':
            result = validate(project, args.stage)
        elif args.command == 'parts':
            result = parts(project)
            if args.output:
                write_new(fresh_output(args.output, project), result['artifact_text'].encode('utf-8'))
        elif args.command == 'export':
            if not args.kind or not args.output:
                raise ValueError('export needs --for and --output')
            result = export_config(project, args.kind)
            write_new(fresh_output(args.output, project), json_bytes(result))
        elif args.command in ('wiring', 'acceptance'):
            if not args.output:
                raise ValueError(args.command + ' needs --output directory')
            result = globals()[args.command](project, args.output)
        elif args.command == 'diagnostics':
            result = diagnostics(project)
            if args.output:
                write_new(fresh_output(args.output, project), json_bytes(result))
        else:
            if not args.output:
                raise ValueError('package needs --output ZIP path')
            result = package(project, args.output, args.reproducible)
        print(json.dumps(result, ensure_ascii=True, allow_nan=False))
        return 1 if result.get('errors') else 0
    except (ValueError, OSError, TypeError, KeyError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())

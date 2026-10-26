"""Local MCU project artifacts. Standard library only; no hardware/network/process APIs."""
import argparse
from copy import deepcopy
import hashlib
from html import escape
import json
import math
import os
from pathlib import Path, PureWindowsPath
import re
import sys
import tempfile
import zipfile

TOOL_VERSION = '1.0'
MAX_LOG_BYTES = 256 * 1024
MAX_FILE_BYTES = 64 * 1024 * 1024
PRIVATE = {'.git', '.env', '.ssh', '.aws', '__pycache__', 'node_modules', 'codexrecords',
           'records.sqlite', 'project_state.json', 'memory.md', 'ai_rules.md', '.codex',
           '.netrc', '.npmrc', '.pypirc', 'id_rsa', 'id_ed25519', '.cache', 'cache', 'caches'}
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


def wiring(project, output):
    data, pins, pending = checked_wiring(project)
    directory = Path(output)
    targets = [fresh_output(directory / name, project) for name in ('wiring.svg', 'connections.md', 'pins.generated.json')]
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
    for target, content in zip(targets, ['\n'.join(svg).encode('utf-8'), '\n'.join(table).encode('utf-8'), json_bytes(record)]):
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


def package(project, output):
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
    allowed_roles = {'source', 'firmware', 'wiring', 'materials', 'use-guide', 'limits', 'test', 'evidence'}
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
        if archive_name.casefold() in seen or archive_name.casefold() == 'manifest.json':
            raise ValueError('duplicate or reserved package name')
        seen.add(archive_name.casefold())
        if entry.get('role') not in allowed_roles:
            raise ValueError('deliverable needs a supported role')
        content = read_file(path)
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
    report = {'version': 1, **provenance(project, True), 'files': files,
              'review_required': 'Caller must review all selected content for secrets and rights; detection is incomplete. Local ZIP creation grants no publication permission.'}
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=output.parent, suffix='.zip', delete=False) as stream:
            temporary = Path(stream.name)
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for name, content in contents:
                archive.writestr(name, content)
            archive.writestr('manifest.json', json_bytes(report))
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
    parser.add_argument('command', choices=['validate', 'export', 'wiring', 'acceptance', 'diagnostics', 'package'])
    parser.add_argument('config', type=Path)
    parser.add_argument('--for', dest='kind', choices=['test', 'flash', 'shopping'])
    parser.add_argument('--stage', default='project', choices=['project', 'test', 'flash', 'shopping', 'wiring', 'acceptance', 'diagnostics'])
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    try:
        project = load(args.config)
        if args.command == 'validate':
            result = validate(project, args.stage)
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
            result = package(project, args.output)
        print(json.dumps(result, ensure_ascii=True, allow_nan=False))
        return 1 if result.get('errors') else 0
    except (ValueError, OSError, TypeError, KeyError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())

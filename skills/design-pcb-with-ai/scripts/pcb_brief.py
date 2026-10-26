"""Offline PCB brief/capability check. Never controls EDA or declares a finished board."""
import argparse
import hashlib
import json
import math
from pathlib import Path, PureWindowsPath
import sys


def check(data, root):
    if not isinstance(data, dict) or type(data.get('version')) is not int or data['version'] != 1:
        raise ValueError('PCB brief needs version 1')
    revision = data.get('revision')
    if not isinstance(revision, str) or not revision.strip():
        raise ValueError('revision required')
    blockers = list(data.get('critical_unknowns', []))
    software = data.get('software', {})
    if software.get('connection_usable') is not True:
        blockers.append('No verified usable EDA connection')
    if data.get('agents_available') is not True:
        blockers.append('No persistent PCB child available')
    supply = data.get('supply', {})
    outline = data.get('outline', {})
    for name, value in [('supply voltage', supply.get('voltage_v')), ('current limit', supply.get('current_limit_ma')),
                        ('outline width', outline.get('width')), ('outline height', outline.get('height'))]:
        if type(value) not in (float, int) or not math.isfinite(value) or value <= 0:
            blockers.append('Unknown/invalid ' + name)
    if not supply.get('source') or outline.get('units') not in ('mm', 'in') or not outline.get('shape'):
        blockers.append('Supply source or outline shape/units unknown')
    pins = set()
    parts = data.get('parts', [])
    if not isinstance(parts, list) or not parts:
        blockers.append('Exact parts missing')
    else:
        refs = set()
        for part in parts:
            ref = part.get('ref')
            if not isinstance(ref, str) or ref in refs or not part.get('model') or type(part.get('quantity')) is not int or part['quantity'] <= 0:
                raise ValueError('Each part needs unique ref/model/positive quantity')
            refs.add(ref)
            if not part.get('footprint') or not part.get('footprint_source'):
                blockers.append('Unknown footprint/source: ' + ref)
            if not isinstance(part.get('pins'), list) or not part['pins']:
                blockers.append('Unknown exact pins: ' + ref)
            else:
                for pin in part['pins']:
                    if not isinstance(pin, str) or not pin or ref + ':' + pin in pins:
                        raise ValueError('Invalid/duplicate part pin')
                    pins.add(ref + ':' + pin)
    nets = data.get('nets', [])
    if not isinstance(nets, list) or not nets:
        blockers.append('Checked nets missing')
    else:
        names, owners = set(), {}
        for net in nets:
            name = net.get('name')
            endpoints = net.get('endpoints')
            if not isinstance(name, str) or not name.strip() or not net.get('source') or not isinstance(endpoints, list) or not endpoints:
                blockers.append('Unknown net/pin/source')
                continue
            name = name.strip()
            if name in names:
                blockers.append('Duplicate net identity: ' + name)
            names.add(name)
            for endpoint in endpoints:
                if not isinstance(endpoint, str) or endpoint not in pins:
                    blockers.append('Unknown net pin: ' + str(endpoint))
                elif endpoint in owners:
                    blockers.append('Pin assigned more than once: ' + endpoint + ' (' + owners[endpoint] + ', ' + name + ')')
                else:
                    owners[endpoint] = name
    for key in ('connectors', 'holes', 'keepouts'):
        if not isinstance(data.get(key), list):
            blockers.append('Explicit ' + key + ' list required')
    fabrication = data.get('fabrication', {})
    if fabrication.get('route') not in ('fabricator', 'diy') or not fabrication.get('process') or not fabrication.get('constraints'):
        blockers.append('Exact fabrication process/constraints unknown')
    evidence = []
    kinds = {'erc', 'footprint', 'drc', 'assembly', 'simulation', 'export-reopen'}
    for report in data.get('checks', []):
        kind, status = report.get('kind'), report.get('status')
        if kind not in kinds or status not in {'passed', 'failed', 'limited', 'not-run', 'not-applicable'}:
            raise ValueError('Unsupported check kind/status')
        if status in {'passed', 'failed', 'limited'}:
            relative = report.get('path')
            if not isinstance(relative, str) or PureWindowsPath(relative).drive or '..' in PureWindowsPath(relative).parts or relative.startswith(('/', '\\')):
                raise ValueError('Check report must be a relative file')
            path = (root / relative).resolve()
            if not path.is_relative_to(root) or not path.is_file() or path.stat().st_size > 1024 * 1024:
                raise ValueError('Missing/escaped/oversized check report')
            if report.get('revision') != revision or hashlib.sha256(path.read_bytes()).hexdigest() != report.get('sha256'):
                raise ValueError('Stale check report revision/hash')
        evidence.append({'kind': kind, 'status': status})
    gaps = data.get('model_gaps', [])
    if not isinstance(gaps, list):
        raise ValueError('model_gaps must be an array')
    if gaps and any(r['kind'] == 'assembly' and r['status'] == 'passed' for r in evidence):
        raise ValueError('Model gaps cannot support a full virtual assembly pass')
    return {'status': 'draft' if blockers else 'ready-for-eda', 'finished_pcb': False,
            'revision': revision, 'blockers': blockers, 'model_gaps': gaps, 'checks': evidence,
            'limits': ['Supplied facts and report linkage only; no EDA, simulation, fabrication or hardware operation. Reports need engineering review.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('brief', type=Path)
    args = parser.parse_args()
    try:
        path = args.brief.resolve(strict=True)
        print(json.dumps(check(json.loads(path.read_text(encoding='utf-8-sig')), path.parent), ensure_ascii=True))
        return 0
    except (ValueError, OSError, TypeError, KeyError, AttributeError) as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())

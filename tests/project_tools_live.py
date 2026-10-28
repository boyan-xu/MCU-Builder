"""Run every helper command on isolated standalone package copies; never access hardware."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path, help='New isolated evidence directory')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
    summary = {'hardware_accessed': False, 'real_cart_accessed': False, 'runs': []}
    for name in ('build-with-ai-mcu', 'develop-with-ai-mcu'):
        package = output / name / 'installed-skill'
        shutil.copytree(root / 'skills' / name, package, ignore=shutil.ignore_patterns('__pycache__'))
        project = output / name / 'fictional-project'
        shutil.copytree(package / 'assets/project-example', project)
        config = project / 'mcu-project.json'
        script = package / 'scripts/mcu_project.py'
        commands = [
            ['status'], ['validate'], ['validate', '--stage', 'wiring'],
            ['export', '--for', 'test', '--output', str(project / 'test-config.json')],
            ['export', '--for', 'flash', '--output', str(project / 'flash-config.json')],
            ['export', '--for', 'shopping', '--output', str(project / 'shopping-config.json')],
            ['wiring', '--output', str(project / 'wiring')],
            ['acceptance', '--output', str(project / 'behavior')],
            ['diagnostics', '--output', str(project / 'diagnostics-private.json')]]
        runs = []

        def run(command):
            process = subprocess.run([sys.executable, str(script), command[0], str(config), *command[1:]],
                                     cwd=output, capture_output=True, text=True, encoding='utf-8', timeout=20)
            result = json.loads(process.stdout or process.stderr)
            assert process.returncode == 0, result
            runs.append({'command': command, 'result': result})
            return result

        for command in commands:
            run(command)
        shopping = json.loads((project / 'shopping-config.json').read_text(encoding='utf-8'))
        assert shopping['parts'][0]['quantity'] == 2 and shopping['region'] is None
        pins = json.loads((project / 'wiring/pins.generated.json').read_text(encoding='utf-8'))
        assert len(pins['connections']) == 2 and pins['electrical_status'] == 'needs-confirmation'
        acceptance = json.loads((project / 'behavior/acceptance.json').read_text(encoding='utf-8'))
        assert all(item['status'] == 'not-run' for item in acceptance['items'])
        data = json.loads(config.read_text(encoding='utf-8'))
        for path, role in [('wiring/wiring.svg', 'wiring'), ('wiring/connections.md', 'wiring'),
                           ('wiring/pins.generated.json', 'wiring'), ('behavior/acceptance.json', 'evidence')]:
            data['deliverables']['files'].append({'path': path, 'role': role,
                'sha256': hashlib.sha256((project / path).read_bytes()).hexdigest()})
        config.write_text(json.dumps(data, indent=2), encoding='utf-8')
        run(['package', '--output', str(project / 'delivery.zip')])
        with zipfile.ZipFile(project / 'delivery.zip') as archive:
            assert 'diagnostics-private.json' not in archive.namelist()
            manifest = json.loads(archive.read('manifest.json'))
            for row in manifest['files']:
                assert hashlib.sha256(archive.read(row['path'])).hexdigest() == row['sha256']
        # Exercise the exported test through the unchanged existing runner API.
        host = subprocess.run([sys.executable, str(root / 'skills/test-mcu-in-background/scripts/mcu_test.py'),
                               str(project / 'test-config.json'), '--output', str(project / 'host-test.json')],
                              cwd=output, capture_output=True, text=True, encoding='utf-8', timeout=30)
        (project / 'host-runner.stdout.txt').write_text(host.stdout + host.stderr, encoding='utf-8')
        assert host.returncode == 0, host.stdout + host.stderr
        (output / name / 'command-results.json').write_text(json.dumps(runs, indent=2), encoding='utf-8')
        summary['runs'].append({'skill': name, 'commands': len(runs), 'exported_host_test': 'pass',
                                'delivery_files': len(manifest['files']), 'evidence': str(output / name)})
    (output / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()

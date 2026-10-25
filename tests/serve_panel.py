"""Local browser fixtures: python tests/serve_panel.py (loopback only)."""

import html
import json
import re
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'skills/build-with-ai-mcu/assets/parts-checklist.html'
PUBLIC_FILES = (
    'README.md', 'docs/README.zh-CN.md', 'docs/README.es.md',
    'skills/build-with-ai-mcu/SKILL.md', 'skills/build-with-ai-mcu/agents/openai.yaml',
    'skills/build-with-ai-mcu/assets/parts-checklist.html',
    'skills/build-with-ai-mcu/references/checklist.md',
    'skills/build-with-ai-mcu/references/uno-led/README.md',
    'skills/build-with-ai-mcu/references/uno-led/connections.json',
    'skills/build-with-ai-mcu/references/uno-led/uno-led.ino',
    'skills/build-with-ai-mcu/references/uno-led/wiring.svg',
    'tests/checklist.test.mjs', 'tests/wiring.test.mjs', 'tests/serve_panel.py',
    'tests/packaging.test.mjs',
    'skills/build-with-ai-mcu/references/working-style.md',
    'skills/build-with-ai-mcu/references/rea.md',
    'skills/develop-with-ai-mcu/SKILL.md',
    'skills/develop-with-ai-mcu/agents/openai.yaml',
    'skills/develop-with-ai-mcu/assets/parts-checklist.html',
    'skills/develop-with-ai-mcu/references/checklist.md',
    'skills/develop-with-ai-mcu/references/working-style.md',
    'skills/develop-with-ai-mcu/references/rea.md',
    'skills/develop-with-ai-mcu/references/uno-led/README.md',
    'skills/develop-with-ai-mcu/references/uno-led/connections.json',
    'skills/develop-with-ai-mcu/references/uno-led/uno-led.ino',
    'skills/develop-with-ai-mcu/references/uno-led/wiring.svg',
    'skills/build-with-ai-mcu/references/verification.md',
    'skills/develop-with-ai-mcu/references/verification.md',
    'skills/build-with-ai-mcu/references/uno-led/diagram.json',
    'skills/develop-with-ai-mcu/references/uno-led/diagram.json',
    'skills/build-with-ai-mcu/references/uno-led/simulation-result.json',
    'skills/develop-with-ai-mcu/references/uno-led/simulation-result.json',
)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        if self.path.startswith('/source/'):
            name = self.path.removeprefix('/source/')
            if name not in PUBLIC_FILES:
                return self.send_error(404)
            text = (ROOT / name).read_text(encoding='utf-8')
            return self.send_html('<!doctype html><meta charset="utf-8"><title>Source review</title><pre id="source">' + html.escape(text) + '</pre>')
        if not self.path.startswith('/panel/'):
            return super().do_GET()
        mode = self.path.split('/')[-1]
        source = TEMPLATE.read_text(encoding='utf-8')
        match = re.search(r'(<script type="application/json" id="parts-data">)([\s\S]*?)(</script>)', source)
        data = json.loads(match[2])
        data.update(projectId='browser-check' if mode != 'host' else 'host-check', projectName='Panel test', language=mode if mode in ('zh', 'es') else 'en')
        if mode == 'changed':
            data['parts'][2]['quantity'] = 2
        if mode in ('zh', 'es'):
            names = {'zh': ['开发板', '红色发光二极管', '电阻', '跳线', '面包板'], 'es': ['Placa', 'LED rojo', 'Resistencia', 'Cables', 'Placa de pruebas']}
            data['projectName'] = '面板测试' if mode == 'zh' else 'Prueba del panel'
            for part, name in zip(data['parts'], names[mode]):
                part.update(name=name, specification=name, purpose='测试' if mode == 'zh' else 'Prueba')
        source = source[:match.start(2)] + json.dumps(data, ensure_ascii=False).replace('<', '\\u003c') + source[match.end(2):]
        prefix = ''
        if mode == 'host':
            prefix = '''<script>
            window.openai = {
              widgetState: JSON.parse(sessionStorage.getItem('simulated-host') || 'null'),
              setWidgetState(value) { sessionStorage.setItem('simulated-host', JSON.stringify(value)); return Promise.resolve(); },
              sendFollowUpMessage(value) {
                const p = document.getElementById('simulated-request') || document.body.appendChild(Object.assign(document.createElement('pre'), {id:'simulated-request'}));
                p.textContent = 'SIMULATED HOST REQUEST\\n' + JSON.stringify(value); return Promise.resolve();
              }
            };</script>'''
        if mode == 'no-storage':
            prefix = "<script>Object.defineProperty(window,'localStorage',{get(){throw new Error('Simulated blocked storage');}}); Object.defineProperty(navigator,'clipboard',{value:{writeText(){return Promise.reject(new Error('Simulated clipboard denial'));}}});</script>"
        return self.send_html('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Local panel test</title></head><body>' + prefix + source + '</body></html>')

    def send_html(self, source):
        payload = source.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


if __name__ == '__main__':
    ThreadingHTTPServer(('127.0.0.1', 8766), Handler).serve_forever()

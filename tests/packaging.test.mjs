import assert from 'node:assert/strict';
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join, resolve, dirname, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const root = fileURLToPath(new URL('../skills/', import.meta.url));
const names = ['build-with-ai-mcu', 'develop-with-ai-mcu'];
const toolNames = ['test-mcu-in-background', 'flash-mcu-firmware'];
const shared = ['assets/parts-checklist.html', 'references/checklist.md', 'references/working-style.md', 'references/rea.md',
  'references/verification.md', 'references/uno-led/README.md', 'references/uno-led/connections.json', 'references/uno-led/uno-led.ino', 'references/uno-led/wiring.svg',
  'references/uno-led/diagram.json', 'references/uno-led/simulation-result.json'];

test('both skills carry identical shared resources for independent installation', () => {
  for (const file of shared) {
    assert.equal(readFileSync(join(root, names[0], file), 'utf8'), readFileSync(join(root, names[1], file), 'utf8'), file);
  }
});

test('Markdown references stay inside each standalone skill package and exist', () => {
  function visit(dir) {
    return readdirSync(dir, {withFileTypes:true}).flatMap(entry => entry.isDirectory() ? visit(join(dir, entry.name)) : [join(dir,entry.name)]);
  }
  for (const name of [...names, ...toolNames]) {
    const base=resolve(root,name);
    assert.ok(existsSync(join(base,'SKILL.md')),name);
    assert.ok(existsSync(join(base,'agents/openai.yaml')),name);
    for (const file of visit(base).filter(f=>f.endsWith('.md'))) {
      for (const [,href] of readFileSync(file,'utf8').matchAll(/\]\(([^)]+)\)/g)) {
        if (href.includes('://') || href.startsWith('#')) continue;
        const target=resolve(dirname(file),href.split('#')[0]);
        assert.ok(target.startsWith(base+sep),`${name}: external package dependency ${href}`);
        assert.ok(existsSync(target),`${name}: missing ${href}`);
      }
    }
  }
});

test('executable skills carry the same runtime without sibling dependencies', () => {
  assert.equal(readFileSync(join(root, toolNames[0], 'scripts/mcu_common.py'), 'utf8'),
    readFileSync(join(root, toolNames[1], 'scripts/mcu_common.py'), 'utf8'));
  assert.ok(existsSync(join(root, toolNames[0], 'scripts/mcu_test.py')));
  assert.ok(existsSync(join(root, toolNames[1], 'scripts/mcu_flash.py')));
});

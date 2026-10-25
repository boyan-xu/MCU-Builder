import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import test from 'node:test';

const dir = new URL('../skills/build-with-ai-mcu/references/uno-led/', import.meta.url);
test('each defined wire has the same endpoints in SVG and connection table', () => {
  const data = JSON.parse(readFileSync(new URL('connections.json', dir), 'utf8'));
  const svg = readFileSync(new URL('wiring.svg', dir), 'utf8');
  const table = readFileSync(new URL('README.md', dir), 'utf8');
  for (const wire of data.connections) {
    assert.ok(svg.includes(`id="${wire.id}" data-from="${wire.from}" data-to="${wire.to}"`), wire.id);
    assert.ok(table.includes(`| ${wire.id} | ${wire.from} | ${wire.to} |`), wire.id);
  }
  assert.equal((svg.match(/data-from=/g) || []).length, data.connections.length);
  assert.match(svg, /viewBox=/);
  assert.match(svg, /USB at left/);
  assert.match(svg, /5 V/);
  assert.match(svg, /330/);
});
test('firmware uses the digital pin in the connection definition', () => {
  const data = JSON.parse(readFileSync(new URL('connections.json', dir), 'utf8'));
  const code = readFileSync(new URL('uno-led.ino', dir), 'utf8');
  const pin = Number(code.match(/LED_PIN\s*=\s*(\d+)/)[1]);
  assert.equal(pin, data.ledPin);
  assert.equal(data.connections[0].from, `UNO D${pin}`);
  assert.match(code, /pinMode\(LED_PIN, OUTPUT\)/);
});

test('MCU simulator uses the same complete connection definition', () => {
  const data=JSON.parse(readFileSync(new URL('connections.json',dir),'utf8'));
  const diagram=JSON.parse(readFileSync(new URL('diagram.json',dir),'utf8'));
  assert.equal(diagram.parts.find(p=>p.id==='uno').type,'wokwi-arduino-uno');
  assert.equal(diagram.parts.find(p=>p.id==='r1').attrs.value,'330');
  assert.deepEqual(diagram.connections.map(c=>c.slice(0,2)), data.connections.map(w=>[data.simulatorPins[w.from],data.simulatorPins[w.to]]));
  const code=readFileSync(new URL('uno-led.ino',dir),'utf8');
  assert.match(code,/SIM_START UNO_R3 D8/);
  assert.equal((code.match(/Serial\.println\(digitalRead\(LED_PIN\)\)/g)||[]).length,2);
});

test('simulation record identifies the exact tested source and diagram without implying physical proof', () => {
  const result=JSON.parse(readFileSync(new URL('simulation-result.json',dir),'utf8'));
  const sha=file=>createHash('sha256').update(readFileSync(new URL(file,dir))).digest('hex');
  assert.equal(result.sourceSha256,sha('uno-led.ino'));
  assert.equal(result.diagramSha256,sha('diagram.json'));
  assert.ok(['passed','blocked','not-run'].includes(result.status));
  assert.ok(result.observations.length>0);
  assert.equal(result.physicalHardwareTested,false);
  assert.equal(result.electricalSafetyProven,false);
});

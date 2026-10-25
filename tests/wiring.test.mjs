import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
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

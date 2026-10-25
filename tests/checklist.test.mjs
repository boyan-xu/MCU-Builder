import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const html = readFileSync(new URL('../skills/build-with-ai-mcu/assets/parts-checklist.html', import.meta.url), 'utf8');
const script = html.match(/<script id="checklist-app">([\s\S]*?)<\/script>/)[1];
const app = vm.createContext({ URL, Intl, TextEncoder });
vm.runInContext(script, app);
const data = () => ({ projectId: 'door-demo', projectName: 'Door alert', language: 'en', currency: 'USD', region: '', parts: [
  { id: 'board', name: 'Existing board', specification: 'Exact model confirmed', quantity: 1, purpose: 'Control', owned: true, unitPrice: null },
  { id: 'switch', name: 'Door switch', specification: 'Dry-contact magnetic switch', quantity: 2, purpose: 'Detect door', owned: false, unitPrice: 3 }
] });

test('confirmed existing quantity is ready and cost counts missing parts only', () => {
  const d = data(), s = app.restoreChecklist(d, null), total = app.checklistSummary(d, s);
  assert.equal(s.rows.board.ready, true);
  assert.equal(s.rows.switch.ready, false);
  assert.equal(total.missingCount, 1);
  assert.equal(total.knownCost, 6);
});

test('progress and region survive reload, link and price refresh', () => {
  const d = data(), s = app.restoreChecklist(d, null);
  s.rows.switch.ready = true; s.region = 'Spain';
  d.parts[1].unitPrice = 4; d.parts[1].url = 'https://example.org/new';
  const restored = app.restoreChecklist(d, JSON.parse(JSON.stringify(s)));
  assert.equal(restored.rows.switch.ready, true);
  assert.equal(restored.region, 'Spain');
  assert.equal(app.checklistSummary(d, restored).missingCount, 0);
});

test('changed quantity or specification resets only the affected item', () => {
  const d = data(), s = app.restoreChecklist(d, null);
  s.rows.switch.ready = true;
  d.parts[1].quantity = 3;
  assert.equal(app.restoreChecklist(d, s).rows.switch.ready, false);
  assert.equal(app.restoreChecklist(d, s).rows.board.ready, true);
  d.parts[0].specification = 'Different board';
  assert.equal(app.restoreChecklist(d, s).rows.board.ready, false);
});

test('a translated display name does not discard unchanged hardware progress', () => {
  const d = data(), s = app.restoreChecklist(d, null);
  s.rows.switch.ready = true;
  d.parts[1].name = '门磁';
  assert.equal(app.restoreChecklist(d, s).rows.switch.ready, true);
});

test('separate projects and malformed saved flags do not leak progress', () => {
  const d = data(), s = app.restoreChecklist(d, null);
  s.rows.switch.ready = true; s.projectId = 'other-project';
  assert.equal(app.restoreChecklist(d, s).rows.switch.ready, false);
  s.projectId = d.projectId; s.rows.switch.ready = 'yes';
  assert.equal(app.restoreChecklist(d, s).rows.switch.ready, false);
});

test('unknown costs stay visible instead of being presented as a free build', () => {
  const d = data(); d.parts[1].unitPrice = null;
  const total = app.checklistSummary(d, app.restoreChecklist(d, null));
  assert.equal(total.knownCost, 0);
  assert.equal(total.unknownCostCount, 1);
});

test('shopping request uses missing or all items and asks for region only if absent', () => {
  const d = data(), s = app.restoreChecklist(d, null);
  let prompt = app.shoppingRequest(d, s, 'missing');
  assert.match(prompt, /Door switch/); assert.doesNotMatch(prompt, /Existing board/);
  assert.match(prompt, /country or region/);
  s.region = 'Mexico'; prompt = app.shoppingRequest(d, s, 'all');
  assert.match(prompt, /Mexico/); assert.match(prompt, /Existing board/);
  assert.doesNotMatch(prompt, /full address/);
});

test('Chinese and Spanish requests use a single matching presentation language', () => {
  const d = data(); d.language = 'zh';
  assert.match(app.shoppingRequest(d, app.restoreChecklist(d, null), 'missing'), /请用中文回复。$/);
  d.language = 'es';
  assert.match(app.shoppingRequest(d, app.restoreChecklist(d, null), 'missing'), /enlaces de compra/);
});

test('only http and https shop links are active', () => {
  assert.equal(app.safeShopURL('javascript:alert(1)'), null);
  assert.equal(app.safeShopURL('file:///private'), null);
  assert.equal(app.safeShopURL('https://example.org/part'), 'https://example.org/part');
});

test('invalid quantities, prices and duplicate ids are rejected', () => {
  for (const qty of [0, -1, 1.5, '2']) {
    const d = data(); d.parts[1].quantity = qty;
    assert.throws(() => app.validateChecklist(d));
  }
  const d = data(); d.parts[1].unitPrice = -3;
  assert.throws(() => app.validateChecklist(d));
  d.parts[1].unitPrice = 3; d.parts[1].id = 'board';
  assert.throws(() => app.validateChecklist(d));
});

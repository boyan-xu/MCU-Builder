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

test('cart request only includes missing parts and explicitly stops before checkout', () => {
  const d = data(), s = app.restoreChecklist(d, null);
  s.site = 'https://shop.example.org'; s.region = 'Spain';
  const request = app.cartRequest(d, s);
  assert.match(request, /\$select-products-to-cart/);
  assert.match(request, /Door switch/); assert.doesNotMatch(request, /Existing board/);
  assert.match(request, /shop\.example\.org/); assert.match(request, /Spain/);
  assert.match(request, /Do not check out/); assert.match(request, /unrelated/);
});

test('shopping site survives checklist reload and is not inferred from language', () => {
  const d = data(), s = app.restoreChecklist(d, null);
  assert.equal(s.site, ''); s.site = 'My selected shop';
  assert.equal(app.restoreChecklist(d, JSON.parse(JSON.stringify(s))).site, s.site);
  d.projectId = 'another'; assert.equal(app.restoreChecklist(d, s).site, '');
});

test('localized cart requests ask for missing site and do not request empty carts', () => {
  const d = data(); d.language = 'zh';
  const s = app.restoreChecklist(d, null);
  assert.match(app.cartRequest(d, s), /网站/); assert.match(app.cartRequest(d, s), /不下单/);
  assert.match(app.cartRequest(d, s), /请用中文回复。$/);
  d.language = 'es'; assert.match(app.cartRequest(d, s), /carrito/);
  s.rows.switch.ready = true; assert.doesNotMatch(app.cartRequest(d, s), /\$select-products-to-cart/);
});

test('a declined or already accepted cart offer stays off until an explicit new choice', () => {
  const d = data(); d.offerCart = false;
  const s = app.restoreChecklist(d, null);
  assert.equal(app.cartRequest(d, s), '');
  delete d.offerCart;
  assert.equal(app.restoreChecklist(d, JSON.parse(JSON.stringify(s))).offerCart, false);
  d.offerCart = true; d.cartOfferId='explicit-renewal-2';
  const renewed=app.restoreChecklist(d,s);
  assert.equal(renewed.offerCart,true);
  renewed.offerCart=false;
  assert.equal(app.restoreChecklist(d,JSON.parse(JSON.stringify(renewed))).offerCart,false);
  d.offerCart = 'yes'; assert.throws(() => app.validateChecklist(d));
});

test('partial physical stock is represented separately from the quantity still to buy', () => {
  const d = data();
  d.parts = [
    {id:'stock',name:'Available switches',specification:'Same switch',quantity:3,purpose:'Use stock',owned:true},
    {id:'gap',name:'Missing switches',specification:'Same switch',quantity:2,purpose:'Complete five total',owned:false}
  ];
  const request=app.cartRequest(d,app.restoreChecklist(d,null));
  assert.match(request,/Missing switches \| Same switch \| 2/);
  assert.doesNotMatch(request,/Available switches/);
});

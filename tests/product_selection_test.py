"""Pure candidate/cart arithmetic checks. No network or real shopping actions."""
from copy import deepcopy
from pathlib import Path
import importlib.util
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/select-products-to-cart/scripts/select_products.py'


def request():
    candidate = {
        'part_id': 'oled', 'sku': 'display-1', 'variant': 'SSD1306 I2C 1-pack',
        'variant_verified': True, 'url': 'https://shop.example/product/display-1',
        'title': 'OLED display', 'observed_at': '2026-10-25T12:00:00Z',
        'specs': {'controller': 'SSD1306', 'interface': 'I2C'},
        'spec_evidence': {'controller': 'https://shop.example/product/display-1', 'interface': 'https://shop.example/product/display-1'},
        'pack_quantity': 1, 'pack_price': '4.00', 'shipping_cost': '1.00', 'currency': 'USD',
        'available': True, 'deliverable': True, 'seller_acceptable': True,
        'seller_evidence': 'https://shop.example/seller/1', 'delivery_days': 4, 'official_seller': False,
    }
    return {'version': 1, 'project_id': 'oled-build', 'site': 'https://shop.example',
            'region': 'US', 'currency': 'USD',
            'parts': [{'id': 'oled', 'quantity': 2, 'required_specs': {'controller': 'SSD1306', 'interface': 'I2C'}}],
            'candidates': [candidate], 'cart': []}


class ProductSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('product_selector', SCRIPT)
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def select(self, value=None):
        return self.module.select_products(request() if value is None else value)

    def test_historical_fixture_keeps_unchanged_browser_inputs_and_simulated_cart_scope(self):
        root = SCRIPT.parents[3]
        record = json.loads((SCRIPT.parents[1] / 'references/fixture-verification.json').read_text())
        for name, digest in record['source_sha256'].items():
            # Selector evolved after this browser run; preserve its historical digest, never rehash it as new proof.
            if name == 'skills/select-products-to-cart/scripts/select_products.py':
                self.assertEqual(digest, 'ee3c5017733dfa15b3402a354b0af1ff4ec4a27bba78c8892028fae3b91367f4')
                continue
            self.assertEqual(hashlib.sha256((root / name).read_bytes().replace(b'\r\n', b'\n')).hexdigest(), digest)
        self.assertEqual(record['repeat_add_packs'], 0)
        self.assertEqual(record['checkout_attempts'], 0)
        self.assertFalse(record['real_store_accessed'])
        self.assertFalse(record['real_orders_placed'])

    def test_standalone_script_and_example_need_no_other_skill_or_packages(self):
        with tempfile.TemporaryDirectory(prefix='standalone shopping spaces ') as directory:
            target = Path(directory)
            shutil.copyfile(SCRIPT, target / SCRIPT.name)
            shutil.copyfile(SCRIPT.parents[1] / 'assets/example.json', target / 'input.json')
            run = subprocess.run([sys.executable, '-B', str(target / SCRIPT.name), str(target / 'input.json')], cwd=target, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            result = json.loads(run.stdout)
            self.assertEqual(result['selections'][0]['sku'], 'oled-good')
            self.assertFalse(result['cart_mutated'])

    def test_selects_verified_variant_and_ceil_pack_quantity(self):
        data = request()
        data['parts'][0]['quantity'] = 5
        data['candidates'][0].update(pack_quantity=2, pack_price='3.00')
        result = self.select(data)
        row = result['selections'][0]
        self.assertEqual(result['status'], 'selected')
        self.assertEqual((row['required_packs'], row['add_packs']), (3, 3))
        self.assertEqual(row['comparison_total'], '10.00')

    def test_verified_fit_precedes_price_and_reports_actual_matches(self):
        data = request()
        data['parts'][0]['preferred_specs'] = {'size': '0.96 inch', 'mounting': True}
        expensive = deepcopy(data['candidates'][0])
        expensive.update(sku='better-fit', pack_price='8.00')
        expensive['specs'].update(size='0.96 inch', mounting=True)
        expensive['spec_evidence'].update(size=expensive['url'], mounting=expensive['url'])
        data['candidates'].append(expensive)
        row = self.select(data)['selections'][0]
        self.assertEqual(row['sku'], 'better-fit')
        self.assertEqual(row['preferred_matches'], ['size', 'mounting'])
        self.assertIn('size', row['reason'])

    def test_missing_or_invalid_preference_evidence_earns_no_match(self):
        for evidence in (None, 'not-a-url'):
            data = request()
            data['parts'][0]['preferred_specs'] = {'size': '0.96 inch'}
            expensive = deepcopy(data['candidates'][0])
            expensive.update(sku='unproven-fit', pack_price='8.00')
            expensive['specs']['size'] = '0.96 inch'
            expensive['spec_evidence']['size'] = evidence
            data['candidates'].append(expensive)
            row = self.select(data)['selections'][0]
            self.assertEqual(row['sku'], 'display-1')
            self.assertEqual(row['preferred_matches'], [])

    def test_preference_cannot_bypass_budget_or_hard_compatibility(self):
        for update in ({'pack_price': '10.00'}, {'available': False}, {'specs': {'controller': 'wrong', 'interface': 'I2C', 'size': 1}}):
            data = request()
            data['parts'][0].update(preferred_specs={'size': 1}, max_total='10.00')
            expensive = deepcopy(data['candidates'][0])
            expensive.update(sku='fails-gate', specs={**expensive['specs'], 'size': 1})
            expensive['spec_evidence']['size'] = expensive['url']
            expensive.update(update)
            data['candidates'].append(expensive)
            self.assertEqual(self.select(data)['selections'][0]['sku'], 'display-1')

    def test_preferences_validate_scalar_map_and_empty_preserves_legacy(self):
        for value in ([], {'size': []}, {'size': float('inf')}):
            data = request()
            data['parts'][0]['preferred_specs'] = value
            with self.assertRaises(ValueError):
                self.select(data)
        data = request()
        old = self.select(data)['selections'][0]['sku']
        data['parts'][0]['preferred_specs'] = {}
        self.assertEqual(self.select(data)['selections'][0]['sku'], old)

    def test_decimal_cost_does_not_use_binary_float_arithmetic(self):
        data = request()
        data['parts'][0]['quantity'] = 3
        data['candidates'][0].update(pack_price='0.10', shipping_cost='0.20')
        self.assertEqual(self.select(data)['selections'][0]['comparison_total'], '0.50')

    def test_large_allowed_amounts_still_use_exact_arithmetic(self):
        data = request()
        data['parts'][0]['quantity'] = 999999999
        data['candidates'][0].update(pack_price='999999999999999999999999', shipping_cost='0.01')
        row = self.select(data)['selections'][0]
        listed = 999999999999999999999999 * 999999999
        self.assertEqual(row['listed_total'], str(listed))
        self.assertEqual(row['comparison_total'], str(listed) + '.01')

    def test_cheapest_listing_can_lose_after_shipping(self):
        data = request()
        other = deepcopy(data['candidates'][0])
        other.update(sku='cheap-shipping', pack_price='5.00', shipping_cost='0.00')
        data['candidates'][0]['shipping_cost'] = '5.00'
        data['candidates'].append(other)
        self.assertEqual(self.select(data)['selections'][0]['sku'], 'cheap-shipping')

    def test_price_ties_use_arrival_then_official_seller(self):
        data = request()
        second = deepcopy(data['candidates'][0])
        second.update(sku='faster', delivery_days=2, official_seller=True)
        data['candidates'].append(second)
        self.assertEqual(self.select(data)['selections'][0]['sku'], 'faster')
        data['candidates'][0]['delivery_days'] = 2
        self.assertEqual(self.select(data)['selections'][0]['sku'], 'faster')

    def test_specs_and_field_evidence_are_required(self):
        for change in [('specs', {'controller': 'SH1106', 'interface': 'I2C'}), ('spec_evidence', {'controller': 'https://shop.example/p'})]:
            data = request()
            data['candidates'][0][change[0]] = change[1]
            self.assertEqual(self.select(data)['selections'], [])
            self.assertEqual(self.select(data)['status'], 'needs_review')

    def test_unknown_shipping_and_currency_are_not_fake_free_choices(self):
        for change in [{'shipping_cost': None}, {'currency': 'EUR'}]:
            data = request()
            data['candidates'][0].update(change)
            self.assertFalse(self.select(data)['selections'])

    def test_stock_delivery_seller_and_exact_variant_are_verified(self):
        for key, value in [('available', False), ('deliverable', None), ('seller_acceptable', 'yes'), ('variant_verified', False), ('variant', '')]:
            data = request()
            data['candidates'][0][key] = value
            self.assertFalse(self.select(data)['selections'], key)

    def test_product_link_is_bound_to_the_requested_origin(self):
        for url in ['https://shop.example.evil/product/1', 'http://shop.example/product/1', 'https://user:pass@shop.example/product/1']:
            data = request()
            data['candidates'][0]['url'] = url
            self.assertFalse(self.select(data)['selections'], url)

    def test_malformed_money_is_rejected_without_losing_valid_alternative(self):
        for price in ['-1.00', 'NaN', 'Infinity', '1e1000000', True]:
            data = request()
            bad = deepcopy(data['candidates'][0])
            bad.update(sku='bad', pack_price=price)
            data['candidates'].append(bad)
            result = self.select(data)
            self.assertEqual(result['selections'][0]['sku'], 'display-1')
            self.assertEqual(len(result['rejected']), 1)

    def test_matching_cart_quantity_is_reused_unrelated_rows_unchanged(self):
        data = request()
        data['cart'] = [{'sku': 'unrelated', 'variant': 'red', 'quantity': 7}, {'sku': 'display-1', 'variant': 'SSD1306 I2C 1-pack', 'quantity': 1}]
        before = deepcopy(data)
        row = self.select(data)['selections'][0]
        self.assertEqual((row['existing_cart_packs'], row['add_packs'], row['target_cart_packs']), (1, 1, 2))
        self.assertEqual(data, before)
        data['cart'][1]['quantity'] = 2
        self.assertEqual(self.select(data)['selections'][0]['add_packs'], 0)

    def test_existing_excess_quantity_is_never_removed(self):
        data = request()
        data['cart'] = [{'sku': 'display-1', 'variant': 'SSD1306 I2C 1-pack', 'quantity': 9}]
        row = self.select(data)['selections'][0]
        self.assertEqual((row['add_packs'], row['target_cart_packs']), (0, 9))

    def test_shared_selected_sku_cannot_underbuy_or_double_add(self):
        data = request()
        data['parts'].append(dict(data['parts'][0], id='oled-spare'))
        data['candidates'].append(dict(data['candidates'][0], part_id='oled-spare'))
        result = self.select(data)
        self.assertFalse(result['selections'])
        self.assertEqual(result['status'], 'needs_review')
        self.assertEqual(len(result['reviews']), 2)

    def test_conflicting_duplicate_observations_are_held(self):
        data = request()
        data['candidates'].append(dict(data['candidates'][0], pack_price='1.00'))
        result = self.select(data)
        self.assertEqual(result['selections'], [])
        self.assertEqual(len(result['rejected']), 2)

    def test_whitespace_cannot_hide_duplicate_candidate_identity(self):
        data = request()
        data['candidates'].append(dict(data['candidates'][0], part_id=' oled ', sku=' display-1 ', variant=' SSD1306 I2C 1-pack ', pack_price='1.00'))
        result = self.select(data)
        self.assertEqual(result['selections'], [])
        self.assertEqual(len(result['rejected']), 2)

    def test_explicit_budget_and_deadline_are_hard_limits(self):
        for limit in [{'max_total': '8.99'}, {'max_delivery_days': 3}]:
            data = request()
            data['parts'][0].update(limit)
            self.assertEqual(self.select(data)['selections'], [])
        data = request()
        data['parts'][0].update(max_total='9.00', max_delivery_days=4)
        self.assertEqual(self.select(data)['status'], 'selected')
        data['parts'][0]['max_delivery_days'] = 0
        data['candidates'][0]['delivery_days'] = 0
        self.assertEqual(self.select(data)['status'], 'selected')

    def test_bad_top_level_or_cart_data_stops_selection(self):
        for mutate in [lambda d: d.pop('cart'), lambda d: d.update(version=True), lambda d: d.update(currency='dollars'), lambda d: d['parts'].append(d['parts'][0]), lambda d: d.update(cart=[{'sku': 'a', 'variant': 'b', 'quantity': -1}])]:
            data = request()
            mutate(data)
            with self.assertRaises(ValueError):
                self.select(data)

    def test_cli_writes_report_and_cannot_replace_input(self):
        with tempfile.TemporaryDirectory(prefix='cart selector spaces ') as directory:
            source = Path(directory) / 'input.json'
            output = Path(directory) / 'selection.json'
            original = json.dumps(request())
            source.write_text(original, encoding='utf-8')
            result = subprocess.run([sys.executable, '-B', str(SCRIPT), str(source), '--output', str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(output.read_text())['status'], 'selected')
            result = subprocess.run([sys.executable, '-B', str(SCRIPT), str(source), '--output', str(source)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(source.read_text(), original)


if __name__ == '__main__':
    unittest.main()

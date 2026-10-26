"""Rank browser-verified product variants; never browses or mutates a cart."""
import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import urlsplit


def text(value, name):
    if not isinstance(value, str) or not value.strip() or len(value) > 4096:
        raise ValueError(name + ' must be a nonempty string of at most 4096 characters')
    return value.strip()


def quantity(value, name, zero=False):
    if type(value) is not int or not (0 if zero else 1) <= value <= 1000000000:
        raise ValueError(name + ' must be a bounded integer ' + ('>= 0' if zero else '> 0'))
    return value


def money(value, name):
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError(name + ' must be a nonnegative decimal amount')
    raw = str(value)
    if len(raw) > 24 or not re.fullmatch(r'[0-9]+(?:\.[0-9]{1,4})?', raw):
        raise ValueError(name + ' must use decimal digits, up to four decimal places, without exponent notation')
    return Decimal(raw)


def origin(value, name):
    value = text(value, name)
    try:
        url = urlsplit(value)
        if url.scheme not in ('http', 'https') or not url.hostname or url.username is not None or url.password is not None:
            raise ValueError()
        return (url.scheme, url.hostname.lower(), url.port or (443 if url.scheme == 'https' else 80))
    except (TypeError, ValueError):
        raise ValueError(name + ' must be an HTTP(S) URL without credentials') from None


def timestamp(value):
    value = text(value, 'observed_at')
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if parsed.utcoffset() is None:
            raise ValueError()
        return parsed.astimezone(timezone.utc).isoformat()
    except ValueError:
        raise ValueError('observed_at must be an ISO-8601 timestamp with timezone') from None


def normalized(value):
    if isinstance(value, str) and value.strip():
        return ('text', value.strip().casefold())
    if isinstance(value, bool):
        return ('bool', value)
    if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
        return ('number', Decimal(str(value)))
    raise ValueError('specifications must contain nonempty strings, finite numbers or booleans')


def validate(data):
    if not isinstance(data, dict) or type(data.get('version')) is not int or data['version'] != 1:
        raise ValueError('input must be an object with version 1')
    for field in ('project_id', 'region'):
        text(data.get(field), field)
    site = text(data.get('site'), 'site')
    site_origin = origin(site, 'site')
    parsed = urlsplit(site)
    if parsed.path not in ('', '/') or parsed.query or parsed.fragment:
        raise ValueError('site must be the selected website origin, without a path, query or fragment')
    if not isinstance(data.get('currency'), str) or not re.fullmatch(r'[A-Z]{3}', data['currency']):
        raise ValueError('currency must be a three-letter uppercase currency code')
    if not isinstance(data.get('parts'), list) or not data['parts']:
        raise ValueError('parts must be a nonempty array')
    parts = {}
    for part in data['parts']:
        if not isinstance(part, dict):
            raise ValueError('each part must be an object')
        identifier = text(part.get('id'), 'part.id')
        if identifier in parts:
            raise ValueError('part IDs must be unique')
        quantity(part.get('quantity'), 'part.quantity')
        specs = part.get('required_specs')
        if not isinstance(specs, dict) or not specs:
            raise ValueError('part.required_specs must contain at least one required specification')
        for key, value in specs.items():
            text(key, 'specification key')
            normalized(value)
        preferred = part.get('preferred_specs', {})
        if not isinstance(preferred, dict):
            raise ValueError('part.preferred_specs must be a scalar map')
        for key, value in preferred.items():
            text(key, 'preferred specification key')
            normalized(value)
        if 'max_delivery_days' in part:
            quantity(part['max_delivery_days'], 'part.max_delivery_days', zero=True)
        if 'max_total' in part:
            money(part['max_total'], 'part.max_total')
        parts[identifier] = part
    if not isinstance(data.get('candidates'), list) or not isinstance(data.get('cart'), list):
        raise ValueError('candidates and current cart snapshot must be arrays')
    cart = Counter()
    for row in data['cart']:
        if not isinstance(row, dict):
            raise ValueError('cart entries must be objects')
        key = (text(row.get('sku'), 'cart.sku'), text(row.get('variant'), 'cart.variant'))
        cart[key] += quantity(row.get('quantity'), 'cart.quantity', zero=True)
    return parts, cart, site_origin


def comparable(candidate, part, currency, site_origin, cart):
    sku = text(candidate.get('sku'), 'candidate.sku')
    variant = text(candidate.get('variant'), 'candidate.variant')
    title = text(candidate.get('title'), 'candidate.title')
    url = text(candidate.get('url'), 'candidate.url')
    if origin(url, 'candidate.url') != site_origin:
        raise ValueError('product URL is outside the selected website origin')
    observed = timestamp(candidate.get('observed_at'))
    for field in ('variant_verified', 'available', 'deliverable', 'seller_acceptable'):
        if candidate.get(field) is not True:
            raise ValueError(field + ' is not explicitly verified true')
    origin(candidate.get('seller_evidence'), 'seller_evidence')
    specs = candidate.get('specs')
    evidence = candidate.get('spec_evidence')
    if not isinstance(specs, dict) or not isinstance(evidence, dict):
        raise ValueError('candidate specs and per-field evidence must be objects')
    for key, expected in part['required_specs'].items():
        if key not in specs or normalized(specs[key]) != normalized(expected):
            raise ValueError('required specification does not match: ' + key)
        origin(evidence.get(key), 'spec_evidence.' + key)
    if candidate.get('currency') != currency:
        raise ValueError('currency differs; no exchange rate is assumed')
    pack = quantity(candidate.get('pack_quantity'), 'pack_quantity')
    required = (part['quantity'] + pack - 1) // pack
    price = money(candidate.get('pack_price'), 'pack_price')
    if candidate.get('shipping_cost') is None:
        raise ValueError('shipping_cost is unknown; quote for the required pack quantity before comparing')
    shipping = money(candidate['shipping_cost'], 'shipping_cost')
    with localcontext() as context:
        context.prec = 50
        listed = required * price
        total = listed + shipping
    days = candidate.get('delivery_days')
    if days is not None:
        quantity(days, 'delivery_days', zero=True)
    if 'max_delivery_days' in part and (days is None or days > part['max_delivery_days']):
        raise ValueError('arrival does not meet the required deadline or remains unknown')
    if 'max_total' in part and total > money(part['max_total'], 'part.max_total'):
        raise ValueError('observed comparison total exceeds the supplied limit')
    official = candidate.get('official_seller', False)
    if not isinstance(official, bool):
        raise ValueError('official_seller must be true or false when supplied')
    existing = cart[(sku, variant)]
    matches = []
    for key, expected in part.get('preferred_specs', {}).items():
        if key in specs and evidence.get(key):
            try:
                if normalized(specs[key]) != normalized(expected):
                    continue
                origin(evidence[key], 'spec_evidence.' + key)
                matches.append(key)
            except ValueError:
                pass  # An unevidenced preference earns no match; hard gates still apply.
    row = {
        'part_id': part['id'], 'sku': sku, 'variant': variant, 'url': url, 'title': title,
        'observed_at': observed, 'required_quantity': part['quantity'], 'pack_quantity': pack,
        'required_packs': required, 'existing_cart_packs': existing,
        'add_packs': max(required - existing, 0), 'target_cart_packs': max(required, existing),
        'pack_price': format(price, 'f'), 'listed_total': format(listed, 'f'),
        'shipping_cost': format(shipping, 'f'), 'comparison_total': format(total, 'f'),
        'delivery_days': days, 'official_seller': official,
        'preferred_matches': matches,
        'reason': 'Hard requirements verified; ranked by evidenced preferred-spec matches (' + ', '.join(matches) + '), then listed price plus shipping, arrival and official seller. No missing evidence earns a preference match.',
    }
    return (-len(matches), total, days if days is not None else math.inf, not official, sku, variant), row


def select_products(data):
    parts, cart, site_origin = validate(data)
    eligible = {key: [] for key in parts}
    rejected = []
    identities = Counter(tuple(c[key].strip() for key in ('part_id', 'sku', 'variant')) for c in data['candidates']
                         if isinstance(c, dict) and all(isinstance(c.get(key), str) for key in ('part_id', 'sku', 'variant')))
    for candidate in data['candidates']:
        identity = {key: candidate.get(key) for key in ('part_id', 'sku', 'variant')} if isinstance(candidate, dict) else {'part_id': None, 'sku': None, 'variant': None}
        try:
            if not isinstance(candidate, dict):
                raise ValueError('candidate must be an object')
            part_id = text(candidate.get('part_id'), 'candidate.part_id')
            if part_id not in parts:
                raise ValueError('candidate.part_id is not requested')
            key, row = comparable(candidate, parts[part_id], data['currency'], site_origin, cart)
            identity_key = (part_id, row['sku'], row['variant'])
            if identities[identity_key] > 1:
                raise ValueError('duplicate comparable candidate identity; provide one current observation per SKU/variant')
            eligible[part_id].append((key, row))
        except (ValueError, TypeError, OverflowError) as error:
            rejected.append(dict(identity, reasons=[str(error)]))
    selections, reviews = [], []
    for part_id, options in eligible.items():
        if options:
            selections.append(min(options, key=lambda item: item[0])[1])
        else:
            reviews.append({'part_id': part_id, 'reason': 'No verified, comparable candidate remains; inspect rejected reasons or collect missing evidence.'})
    counts = Counter((row['sku'], row['variant']) for row in selections)
    # shortcut: shared SKUs are held, add quantity aggregation only when needed.
    for row in selections[:]:
        if counts[(row['sku'], row['variant'])] > 1:
            selections.remove(row)
            reviews.append({'part_id': row['part_id'], 'reason': 'Selected SKU/variant also serves another requested part; aggregate the physical requirements before adding anything.'})
    return {
        'version': 1, 'status': 'needs_review' if reviews else 'selected',
        'project_id': data['project_id'], 'site': data['site'], 'region': data['region'], 'currency': data['currency'],
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'comparison_basis': 'Observed listed prices plus shipping quoted for the required pack quantities. Unquoted checkout taxes/fees are excluded; this is not a global or whole-cart lowest-price claim.',
        'selections': selections, 'reviews': reviews, 'rejected': rejected,
        'cart_mutated': False, 'checkout_permitted': False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    temporary = None
    try:
        if args.output and (args.input.resolve() == args.output.resolve() or args.output.exists() and os.path.samefile(args.input, args.output)):
            raise ValueError('output must not replace the input requirements')
        data = json.loads(args.input.read_text(encoding='utf-8-sig'))
        result = select_products(data)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n', dir=args.output.parent, prefix=args.output.name + '.', suffix='.tmp', delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
                stream.write('\n')
            os.replace(temporary, args.output)
        print(json.dumps(result, ensure_ascii=True, allow_nan=False))
        return 0
    except (OSError, ValueError, TypeError, OverflowError) as error:
        print(json.dumps({'status': 'error', 'error': str(error)}, ensure_ascii=True))
        return 2
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)


if __name__ == '__main__':
    sys.exit(main())

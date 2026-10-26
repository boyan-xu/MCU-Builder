# Reusable selection script and browser workflow

AI gathers evidence in the browser, runs the bundled script and performs authorized cart actions. The user does not fill a form or build an environment. No external Python packages, browser drivers or saved shop credentials are required by the script.

```sh
python scripts/select_products.py /path/to/private/shopping-input.json --output /path/to/private/selection.json
```

This script is **offline and read-only toward websites**. It ranks supplied evidence; it cannot make browsing facts true, authenticate, choose a page option or mutate a cart. Use supported browser controls or an applicable official connector for those steps. Do not call undocumented shopping endpoints or invent site selectors. Ordinary browser navigation should use the user's selected website and actual visible controls; stop or hand off required login/security verification.

## Input contract

Use the [fictional example](../assets/example.json) as a starting shape. All quantities are positive integer physical units except `cart.quantity`, which counts product packs. Prices are nonnegative finite decimal strings in a single ISO currency; no currency conversion is performed.

- Top level: `version: 1`, `project_id`, `site`, broad `region`, `currency`, `parts`, `candidates`, and a fresh `cart` array. `site` binds product links to the specified origin. HTTP is useful for local fixtures; prefer HTTPS for real stores.
- Each part: stable `id`, physical `quantity` still to buy after confirmed owned stock, and `required_specs` mapping normalized specification keys to scalar values. Optional `max_total` caps the observed listed-plus-shipping total; optional `max_delivery_days` sets the arrival deadline (zero permits same-day). AI normalizes units from actual evidence; the script does not guess aliases or electrical compatibility. A need of five with three already owned becomes quantity two; cart packs are subtracted separately afterward.
- Each candidate: `part_id`, `sku`, exact `variant`, `variant_verified`, product `url`, `title`, ISO `observed_at`, normalized `specs`, and `spec_evidence` URLs for required keys. Also include `pack_quantity`, `pack_price`, `shipping_cost` for the whole required pack count, `currency`, explicit booleans `available`, `deliverable`, `seller_acceptable`, seller evidence URL, `delivery_days` (integer or null) and `official_seller`.
- Each cart row: exact `sku`, `variant` and current `quantity` in packs for the same website. Use the site's unique listing/offer identity for `sku`, including seller/offer identity where the cart distinguishes it; do not merge different sellers under a shared catalog number. Preserve unrelated rows in the snapshot; do not write account IDs, names, addresses or session data. An empty array means the cart was actually checked and had no relevant contents, not that it was skipped.

Required specifications and verified variant/stock/delivery/seller evidence gate selection. The comparison is the required pack count times pack price plus quoted shipping. Unknown shipping is held for review; unknown tax or checkout fees remain explicitly outside that comparison. Recheck a supplied spending cap before acting rather than treating an incomplete quote as a guaranteed checkout total.

Eligible candidates rank by that known total, then arrival time, then official-seller status, with a stable identity tie-break. The result describes only the compared candidates. Matching existing SKU/variant packs reduce the amount to add; surplus cart quantity is left untouched. Conflicting requirements selecting the same SKU/variant are held for review instead of silently underbuying or adding twice.

## Result and cart handoff

The JSON contains `selections`, review items, rejected candidates/reasons and provenance. Selected rows include required units, pack count, current cart packs, packs to add, target cart count, costs and reason. `status: needs_review` may accompany usable nonconflicting selections; unresolved rows are not permission to add an alternative. Exit 0 means valid input was evaluated; exit 2 means invalid input/setup. Never translate a ranking result into “already added.”

Before each addition, inspect the current browser page and fresh cart state. If it differs, update the input and rerun. Select the exact variant, add only the computed gap, then verify the actual resulting cart rows. Save the verified outcome and capture evidence locally. A retry uses a new cart snapshot; the script does not pretend that an old snapshot is current. Do not remove or replace other goods. End at the cart without opening checkout or placing an order.

The repository includes a local fictional shop fixture for workflow validation. The [recorded browser verification](fixture-verification.json) identifies the tested files, exact variant/quantities, preserved unrelated goods, zero repeat additions and zero checkout attempts. Passing it proves that example flow and selection arithmetic, not every commercial website. Real store use requires an actual user request and selected site.

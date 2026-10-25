# Use the parts checklist

The AI prepares the panel, not the learner. Copy `assets/parts-checklist.html` into the current project, then replace only the `parts-data` JSON with the real parts and the learner's language. The sample is clearly an example, not a recommendation to replace their board. Keep the script and styles self-contained; no build system, service or network request is needed.

## Project data

- `projectId`: stable, distinct ID for this learner's project. Reuse it through list updates; a different project must have a different ID.
- `projectName`, `language` (`en`, `zh`, `es`), ISO currency such as `USD`/`CNY`/`EUR`, and optional broad `region`. Label any assumed currency in the surrounding answer; do not infer region from currency/language.
- `parts`: stable `id`, localized `name`, exact `specification`, positive integer `quantity`, localized `purpose`, boolean `owned`, optional `unitPrice` and optional `url`.
- Set `owned: true` only when the required quantity/specification is confirmed available. A price is a per-piece estimate in the project's currency; use `null` for unknown costs instead of zero. Include separate shipping/consumable rows when known, or explain unknown extra costs.
- URLs must be current checked http/https product references, without affiliate tracking. No example fake shop links. Escape `<` as `\u003c` when serializing JSON into the script tag so supplied text cannot terminate it. Insert user text via data, not executable code.

## Chat and standalone delivery

The template is an HTML fragment that also opens directly as a standalone HTML file. When the host has an inline HTML/visualization surface, put the generated fragment in the task's writable location and use that host's supported display mechanism. For Codex with Visualize available, follow its output contract. Do not require that skill on other platforms. Give a standalone file when inline interaction is unavailable.

If a browser requires a full document, wrap the unchanged fragment in `<!doctype html><html lang="…"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>…</title></head><body>…</body></html>` using the chosen language and an escaped project title. No external script, font or library is required. Preserve the fragment as the editable source.

Checkboxes and the optional region are stored per project in browser storage when available. Inline hosts may also support `window.openai.widgetState`, `setWidgetState` and `openai:set_globals`; these are optional. Blocked storage leaves the panel usable for the current visit. Store no secrets, account details or addresses. Same item IDs with unchanged specification/quantity keep their checks when display names, prices or links change. Keep technical specifications stable when only translating display names. Changed specifications or quantities reset only affected checks. Preserve the project ID and storage context when regenerating; across another browser or moved local files, carry the known checklist state with the generated file or ask only for missing status, never claim automatic cross-device sync.

## Buying-link action

When supported, the clearly labeled button sends an explicit follow-up request through `window.openai.sendFollowUpMessage`. The request includes the selected all/missing parts, quantities, broad region and response language. No browsing occurs inside the panel. The AI uses its available search tools, verifies actual product variants/delivery and returns optional links or an updated panel. If region is absent, ask for country/region at that point.

Without that host API, or if it fails, the panel displays a request the learner can copy to their AI. Clipboard failure leaves selectable text. Do not pretend this fallback sends a message. A check means the learner marked materials ready, not proof of safe wiring or permission to operate hardware.

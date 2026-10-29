# Final replication package

Use `python scripts/mcu_project.py package mcu-project.json --reproducible --output NEW.zip` for final handoff. Basic `package` stays `draft_unverified`; a ZIP alone is not final. The helper never builds, runs scripts, browses, flashes or validates the truth of a supplied observation.

The aim is the same specified design, configuration and behavior with exact listed parts, using the package steps without more coding/redesign or another AI session. Physical tolerances and untested behavior cannot be guaranteed identical. Build/logic/simulation/electrical/flash/physical proof are separate; not every project needs simulation or physical tests to export artifacts. Critical unresolved parts, power, pins, footprints or fabrication facts mean draft.

## Version 1 contract

Keep existing `deliverables: {revision, files:[{path,role,sha256}]}`. Every path is a selected-project relative file with its reviewed SHA256. Add `deliverables.reproducibility`:

```json
{
  "revision": "r1",
  "critical_unknowns": [],
  "firmware_required": true,
  "used_resources": [],
  "required_inputs": ["src/main.c", "src/pins.h", "build.json", "dependencies.md"],
  "include_dirs": ["src"],
  "toolchain": [{"name":"Exact compiler", "version":"1.2.3", "official_url":"https://example.org/compiler", "setup":"build-guide.md"}],
  "external_prerequisites": [],
  "essential_facts": {"parts":["bom.md"], "pins":["connections.md"], "power":["power-assembly.md"], "build":["build-guide.md"], "assembly":["power-assembly.md"]},
  "build_evidence": "build-proof.json",
  "proof_status": {"build":"passed", "logic":"not-run", "simulation":"not-applicable", "electrical":"limited", "flash":"not-run", "physical":"not-run"}
}
```

These are fictional placeholders, not a target/tool recommendation. AI maintains this data; users do not fill a form. `required_inputs` is the audited full build dependency inventory: complete application source, local headers, build/config/linker files, bundled third-party libraries and assets. Each must be allowlisted, exist and match its hash. Every `source`, `build-config` and `dependencies` file must be in that inventory. Quoted C/C++ includes must resolve inside it through the source directory or declared relative `include_dirs`; no private absolute build paths. This catches a common missing-include failure but cannot infer arbitrary build-system, runtime or transitive dependencies. AI must inspect the actual clean build and runtime asset use, complete the inventory, and retain a build witness; role labels or a declaration alone do not prove completeness.

`build-proof.json` is a reviewed report from the actual successful build, not generated as a pass by this packager: `{status:"passed", revision, config_sha256, input_sha256:{relative_path:sha256}, firmware_sha256:{relative_firmware:sha256}, toolchain:[same exact tool records], command:"actual observed command"}`. `input_sha256` must exactly match required inputs and firmware hashes must match selected compiled outputs. Changing any input, config, revision, toolchain or firmware invalidates it. An old success is historical. Never fabricate this report to clear the gate. `config_sha256` omits deliverables to avoid circular hashes. Existing source snapshot/config/evidence freshness guards remain.

## Required artifacts and content

Required file roles are `materials`, `wiring-image`, `wiring-text`, `source`, `build-config`, `dependencies`, `build-guide`, `flash-guide`, `power-assembly`, `use-guide`, `acceptance-guide`, `license`, `evidence`, `limits`. Also `firmware` when `firmware_required` is true; otherwise explain why compiled firmware is unnecessary in the flash guide. Source means the COMPLETE buildable application, never illustrative snippets. Libraries/assets/config necessary for the selected scope must be included when redistributable, each with license/third-party attribution. Dependencies that cannot legally be bundled are explicit external prerequisites with exact version, official HTTPS acquisition URL and included setup file. Exact tool versions need the same information. `START-HERE.md` lists these prerequisites visibly after extraction: no silent offline/zero-download promise. Credentials are supplied by each replication user through local provisioning, never embedded.

`materials` is the exact BOM, quantities, specs, purpose, required/owned/missing counts, evidence-backed estimated missing costs (or unknown) and copyable search text with pack count. Config materials use `{id,model,required,available,required_specs,purpose,search_text,price}`; `price` is null or `{estimated_missing_total,currency,source,observed_at}`. Plain numbered text is the default; `parts` returns it. Persist its returned `cart_offer` in AI-managed `shopping.cart_offer`; states are `not-offered`, `offered`, `accepted`, `declined`. The complete list precedes one offer; accepted+unknown site asks the platform, accepted+known site reuses it. This helper never mutates a cart or stores consent automatically.

For a final BOM use `parts CONFIG --output NEW-bom.md`, or write the returned UTF-8 `artifact_text` exactly, preserving LF bytes. This separate artifact excludes the cart offer and includes current config/source provenance. The final `materials` artifact must match it byte-for-byte; labels or a refreshed hash cannot turn stale/mismatched BOM text into current data. Regenerate after changing inputs/config.

`wiring-image` AND `wiring-text` show exact per-wire pins, orientation, polarity and power. Checked wiring config must have complete explicit model/orientation/pin voltage/range/role metadata; AI separately checks actual pin mapping, protection, current and electrical sources. `essential_facts` points to included evidence for parts/pins/power/build/assembly, not an engineering-proof score. Power/assembly, build/flash, use and acceptance guides must give actionable steps, target/options, exact versions, expected results and what to do on failure. Acceptance may honestly mark not-run. Limits distinguish observed facts, unknowns and physical checks still needed.

The required image/text are the exact current `wiring` command's `wiring.svg` and `connections.md`; final mode compares full bytes and parses the supported SVG, so stripping optional markers cannot hide stale/mismatched wires. Include supplementary physical-pin photos, user diagrams, PNG copies or other user-created assembly assets with role `wiring` (or the relevant source/resource role). These are allowed and hashed alongside the canonical required outputs. The generated logical SVG alone does not prove physical pin location: AI must inspect the actual model/datasheet/photos, orientation, power and firmware mapping, explain assembly in the guide, and include the physical references needed to reproduce it. A complete extracted handoff still needs that knowledge review.

## Guide content contract

Use the saved project behavior decisions and defaults when writing the existing use/acceptance sections. For each relevant edge case, give the action or condition and the expected visible result; include phone access/provisioning and network recovery when applicable. Keep unresolved provisional choices explicit. A replication user should not need old chat or new design decisions to learn the behavior. No extra section marker or form is required; record actual run/not-run proof separately from expected behavior.

Required guides are UTF-8 text with the exact current `<!-- mcu-project-sha256:... mcu-source-sha256:... -->` marker produced by `marker(project)`. Within each guide, invisible `<!-- mcu-section:KEY -->` comments identify the sections below; headings and prose may be in the user's language. Give actual project steps/details in every required section, with at least 32 letters/digits (Unicode supported). Empty/placeholder sections, duplicate keys and obvious standalone TODO/TBD/FIXME/PLACEHOLDER artifacts are rejected. This is a content/structure floor, not a claim that arbitrary prose is true or sufficient.

| Role | Required section keys and meaning |
| --- | --- |
| `build-guide` | `tools`: exact setup; `build`: actual build steps/commands; `expected`: outputs; `failure`: recovery. |
| `flash-guide` | `target`: exact target/options or why not applicable; `steps`: procedure; `expected`: readback/result; `failure`: recovery. |
| `power-assembly` | `power`: supply/polarity/current; `assembly`: exact physical pins/orientation/parts; `safety`: checks before power. |
| `use-guide` | `steps`: actual operation; `expected`: visible behavior; `failure`: what to do. |
| `acceptance-guide` | `steps`: check procedure; `expected`: pass criteria; `proof`: actual run/not-run state and evidence limits. |
| `dependencies` | `bundled`: complete input/library/asset inventory; `external`: exact prerequisite acquisition/setup. At least one `.md` inventory guide is required; bundled non-Markdown libraries/assets with this role remain supported. |
| `license` | `license`: actual applicable license text/terms; `attribution`: all needed third-party credits. |
| `limits` | `proof`: separate actual proof states; `limits`: unresolved noncritical limits and physical uncertainty. |

AI audits the complete extracted package and concrete instructions; section markers/length are not an engineering or legal truth certifier. Do not fill sections with generic reassurance. Final sources, config, firmware, libraries and assets still need the audited dependency/build evidence described above.

If `used_resources` includes `pcb`, require `pcb-source`, `schematic`, `pcb-layout`, `pcb-bom`, `pcb-nets`, `pcb-checks`, `pcb-manufacture`, plus `essential_facts.pcb`. Include editable EDA sources, ERC/footprint/pad/polarity/DRC and virtual assembly reports, honest model gaps, and final reopened version-bound fabrication/DIY files. `mechanical` requires `mechanical-source`, `mechanical-export` and facts; `print` requires `print-source`, `print-export` and facts. Include every generated project-specific file actually needed for reproduction. Declaring used resources is part of the reviewed inventory; the helper cannot discover undisclosed design files elsewhere on disk.

The final manifest binds all categorized package files, including generated `START-HERE.md`, to bytes/digests and project/revision/config. Reopen/unpack the ZIP and compare file bytes against it before handoff; perform a clean build from the extracted tree when available. Private records, caches/backups, logs, credentials, traversal and overwrite remain refused. Secret detection and license review need human/AI content review; no automatic zero-error guarantee. The existing OLED showcase has unresolved electrical facts and is not relabeled fully reproducible.

All selected AND generated bytes, including final `START-HERE.md` and `manifest.json`, are checked for recognizable credentials before staging any ZIP. Raw reproducibility metadata is also scanned, including extra fields; only the known reviewed contract fields are exported. Official tool/prerequisite URLs may not carry credentials. Normal exact versions, official acquisition URLs and local setup paths remain supported; secret detection still requires content review beyond the known patterns.

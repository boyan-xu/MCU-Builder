# Choose checks that help the current product

Read this while selecting parts and before physical operation. The goal is a usable product, not a lesson. Use existing compatible simulation/build/debug tools; do not invent a simulator or replace working software. Explain needed downloads, accounts, costs and configuration changes before taking them on. Keep tokens in private input and do not upload private project material to a cloud simulator without applicable authorization.

## Choose a verifiable design

For new purchases, prefer MCUs and modules with suitable, documented simulation support that still meet the person's actual needs. Check the exact model, important peripherals and simulator limitations, not just the board-family name. Do not replace a suitable existing board merely because it lacks a model. State cost and delivery assumptions; aim for a useful result quickly without promising every idea in a fixed number of days.

Use the person's current goal and state to choose the next action. AI decides whether a test or simulation would resolve a real uncertainty or risk; neither is mandatory for every project. A simple, already-understood change may need only inspection and a build. State useful checks briefly rather than asking the person to design a test program. Keep the original goal visible in any milestone; complexity is judged from actual feasibility, not MCU knowledge level.

When checks are useful, choose relevant startup, input/output, boundary, timing, restart or failure scenarios. Give more attention to power, motion, outputs and communication failures when they could damage parts or create unsafe behavior. Do not use the flexible test policy to skip necessary electrical checks.

## Prefer background execution; preview when wanted

Use existing local or connected background/headless tools when they cover the behavior that matters. This may be a build, host-side logic check, ARM instruction emulator with peripheral mocks, or an appropriate MCU simulator. Do not open a browser or require a hosted simulator just to satisfy a workflow step. If the person wants to see the effect before flashing, offer a browser preview or rendered frames; label what it actually executes.

If MCU simulation is useful and supported, run firmware with suitable target/component models and matching connections. A browser UI mock, host unit test or successful compile is not MCU simulation. ARM instruction execution with mocked peripherals can prove exercised code paths, but not the real peripheral, board or electrical behavior. Document substitutes, mocks and coverage gaps; never silently substitute another board and call it exact coverage.

For checks actually run, preserve the tested source/build version, relevant connections/configuration, scenarios, observed evidence, failures and limits. Include simulator/target and project files when applicable; say when a service does not expose its build version. Fix observed failures that affect the intended next operation. Recheck affected behavior after relevant changes when needed; do not reuse stale evidence. Existing browser-run evidence remains browser-run evidence, not a headless result.

## Separate electrical review and first operation

While parts are shipping, prepare authorized source, the build environment, model-based wiring drafts, flash settings and applicable checks. Use documented candidate parts for provisional plans; do not claim arrival, actual wiring, flashing or physical success. If a tool is missing, explain that limit, reuse installed alternatives where suitable and continue work that does not need it. Explain needed external acquisition or setup; reuse applicable authorization, asking only when it is missing or the scope changes. A blocked tool does not block independent preparation.

On arrival, check the actual variant, pin labels/orientation, power requirements and needed protection against the plan. Obtain only labels, photos or observations AI cannot access. Resolve differences through the [change-impact check](project-tools.md#keep-enough-state-to-resume). Prepare and inspect the matching wiring image and per-wire instructions before the person starts wiring; a provisional model-based diagram is not proof of the arrived part's pinout.

Simulation success is limited to its models and exercised scenarios. It does not establish zero bugs or prove that hardware cannot be damaged. Digital simulators may have limited analog/power modeling; check provider documentation, such as [Wokwi analog support](https://docs.wokwi.com/chips-api/analog).

Separately verify actual supply voltage/polarity, logic levels, current demand versus board/supply ratings, required resistors/drivers, shared ground and any motor/load stop conditions. Use exact part references, not a simulation animation, for these checks. Keep the user-facing instruction short and specific; AI does the analysis it can perform. Do not ask repeatedly for approval of the same authorized flash operation.

Changing wires happens with power disconnected. Choose a suitable sequence: an isolated board can be flashed first; an unpowered circuit can be wired first when appropriate. Where the equipment and project allow it, use staged first operation with external loads isolated or outputs inactive before a full functional run. Do not assume the user owns a current-limited supply; recommend one only when the actual setup needs it.

## Existing hardware without a suitable simulation model

Explain the coverage gap when it affects the next decision. Continue code, build or targeted logic checks when useful. Reuse the existing board; do not force a purchase or stop safe useful work just because a model is missing. Do not require installation or an account merely to make simulation possible when existing tools suffice.

Under authorization for that exact target, allow board-only flash/diagnostic tests with external loads isolated and appropriate initial output states, after target, existing firmware and electrical checks. This necessarily powers the development board; it is an explicit fallback, not a claim that a full connected product has passed simulation. Tell the person what was observed, what remains unknown and the next suitable physical check. Do not silently jump from a board diagnostic to full-power movement or load operation.

## Report and deliver honestly

Own the debug loop: read accessible build/serial/debug/status reports directly, identify the strongest supported cause and choose a bounded next check. Ask the person only for inaccessible physical actions or observations, with one short action, expected result and useful feedback. Fix and verify affected code/configuration in AI-code mode; in own-code mode give the cause and next coding step. Stop unsafe operation, such as a hot part or uncontrolled movement, before further checks. If evidence stays inconclusive, preserve the result and request the one missing observation; do not cycle through speculative changes or blind retries.

Accept against the original agreed behaviors and their expected results, not merely a build or flash success. AI prepares the checks and captures available evidence; the person confirms physical behavior AI cannot observe. Keep unresolved behaviors pending and state which evidence or action can close them. Update the compact project note before pausing or handing over.

For relevant layers, distinguish build, host-side logic checks, ARM emulation with mocks, MCU simulation, electrical review, flash/readback and physical product behavior. Mark results passed, failed, unavailable or not run with evidence and limits. A skipped or unavailable check is not a pass, and there is no need to present a long empty checklist. A bounded retry may fix a concrete failure; repeated blind simulation or flashing does not add evidence.

Deliver source, exact wiring image/table, any test/simulation files and results actually produced, a short use guide and remaining limitations. The [UNO LED reference](uno-led/README.md) demonstrates evidence packaging from a historical browser run, not an obligatory first product or required execution method.

## Mechanical scope in this release

Automatic CAD design, generation of print-ready mechanical files and direct printing are not normal outputs of these skills. For an enclosure, prefer an off-the-shelf case, existing structure or a user-supplied model. Existing CAD skills, printers or CNC machines remain useful context, but do not silently add mechanical design or operate them. A request for CAD/printing should be identified as outside this release and handled as a separate explicitly scoped task, not promised as part of this workflow. Do not enable a future CAD/print stage merely because a model judges itself more capable; it requires an explicit skill update.

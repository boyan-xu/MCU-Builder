# Verify the product before operating it

Read this while selecting parts and before physical operation. The goal is a usable product, not a lesson. Use existing compatible simulation/build/debug tools; do not invent a simulator or replace working software. Explain needed downloads, accounts, costs and configuration changes before taking them on. Keep tokens in private input and do not upload private project material to a cloud simulator without applicable authorization.

## Choose a verifiable design

For new purchases, prefer MCUs and modules with suitable, documented simulation support that still meet the person's actual needs. Check the exact model, important peripherals and simulator limitations, not just the board-family name. Do not replace a suitable existing board merely because it lacks a model. State cost and delivery assumptions; aim for a useful result quickly without promising every idea in a fixed number of days.

Agree on observable product behavior, then derive relevant checks: startup and safe initial outputs, normal inputs/outputs, thresholds, timing and boundary cases, restart, missing inputs, communication timeout or other failure behavior when applicable. Do not inflate a simple build into an unrelated test program. Keep the original goal visible in any proposed milestone; complexity is judged from actual feasibility, not the person's MCU knowledge level.

## Use real MCU simulation when supported

Run the firmware on an appropriate MCU simulator with matching component models and connections. A browser UI mock, a host-side unit test, static analysis or a successful compile is not MCU simulation. Document substitutes or mocks and the behavior they cannot prove. Match the wiring image, pin table, firmware and simulator; never silently substitute a different board and call it exact coverage.

Exercise the applicable product scenarios and fix failures before operating the supported physical circuit with its external devices or loads. Preserve the simulation project and outcome: simulator/target, firmware or source version/digest, connection/configuration version, scenarios run, observed evidence, failures and limits. Say when a web service does not expose its build version. Changes to relevant code, pins, wiring or configuration need fresh affected checks; do not reuse a stale pass.

## Separate electrical review and first operation

Simulation success is limited to its models and exercised scenarios. It does not establish zero bugs or prove that hardware cannot be damaged. Digital simulators may have limited analog/power modeling; check provider documentation, such as [Wokwi analog support](https://docs.wokwi.com/chips-api/analog).

Separately verify actual supply voltage/polarity, logic levels, current demand versus board/supply ratings, required resistors/drivers, shared ground and any motor/load stop conditions. Use exact part references, not a simulation animation, for these checks. Keep the user-facing instruction short and specific; AI does the analysis it can perform. Do not ask repeatedly for approval of the same authorized flash operation.

Changing wires happens with power disconnected. Choose a suitable sequence: an isolated board can be flashed first; an unpowered circuit can be wired first when appropriate. Where the equipment and project allow it, use staged first operation with external loads isolated or outputs inactive before a full functional run. Do not assume the user owns a current-limited supply; recommend one only when the actual setup needs it.

## Existing hardware without a suitable simulation model

Explain exactly which MCU/module behavior cannot be simulated. Continue writing code, compiling and running applicable host-side logic tests. Reuse the existing board; do not force a purchase or stop all work just because the simulator lacks it.

Under authorization for that exact target, allow board-only flash/diagnostic tests with external loads isolated and appropriate initial output states, after target, existing firmware and electrical checks. This necessarily powers the development board; it is an explicit fallback, not a claim that a full connected product has passed simulation. Tell the person what was observed, what remains unknown and the next suitable physical check. Do not silently jump from a board diagnostic to full-power movement or load operation.

## Report and deliver honestly

Report separately: build; host-side logic checks; MCU simulation; electrical review; flash/readback; and physical product behavior. Mark a layer passed, failed, unavailable or not run with its evidence and limits. An unavailable tool/account/model is not a pass. A bounded retry may fix a concrete failure; repeated blind simulation or flashing does not add evidence.

Deliver the actual source, exact wiring image/table, simulation files/results, a short use guide and remaining limitations. The [UNO LED reference](uno-led/README.md) demonstrates evidence packaging, not an obligatory first product.

## Mechanical scope in this release

Automatic CAD design, generation of print-ready mechanical files and direct printing are not normal outputs of these skills. For an enclosure, prefer an off-the-shelf case, existing structure or a user-supplied model. Existing CAD skills, printers or CNC machines remain useful context, but do not silently add mechanical design or operate them. A request for CAD/printing should be identified as outside this release and handled as a separate explicitly scoped task, not promised as part of this workflow. Do not enable a future CAD/print stage merely because a model judges itself more capable; it requires an explicit skill update.

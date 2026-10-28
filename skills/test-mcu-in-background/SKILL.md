---
name: test-mcu-in-background
description: Use when MCU code or an existing embedded project needs focused background checks using a reusable executable runtime, including Cortex-M C logic and OLED frame capture. Reuses installed project tools and a cached ARM environment rather than rebuilding test infrastructure each time.
---

# Test MCU Code in the Background

AI saves pasted code or inspects the existing project, chooses useful checks and calls the bundled runner. The user should not build a test environment, edit configuration or type commands. This is a runnable tool Skill, not instructions to invent a new runner on each invocation.

## Use the bundled implementation

When agents are available, reuse one capable coding child for source inspection, runner calls, builds/tests and debugging; keep the main agent on product decisions and authorization. Return only outcome, checks/evidence paths, limits/blocker and next user action, without raw source/diffs/logs. Use deterministic scripts first, one writer per scope and at most two concurrent children. Simple bulk work may use an actually selectable lightweight model; otherwise inherit/default honestly. Without agents, continue with bounded summaries. Existing version 1 configs work directly; a product Skill's optional project-helper export also works without adding a dependency or changing hardware rights.

Read [the executable workflow](references/workflow.md) for commands and the small project configuration. Invoke `python scripts/mcu_test.py CONFIG --summary` for routine compact results; omit the optional flag for the original full output. Keep the saved report/logs and read relevant details on errors, stale evidence or an insufficient excerpt. Use the absolute script path from any working directory. Reuse a suitable Python and installed compiler; use `--prepare` once when the ARM runtime needs preparation, then keep its cache. Explain actual downloads first. Ordinary runs never install dependencies. Each Skill copy is independent; no companion installation is required.

- If a working test/build command already exists, use the `command` backend to execute that software command with logging and timeout. Inspect it first: it must not flash, reset or operate hardware. The runner executes trusted project code; it is not a security sandbox.
- For suitable Cortex-M C logic, use `arm-c`: save sources and a focused `int test_main(void)` harness; the runner compiles, loads the resulting ELF into ARM execution and reports the return value. Reuse existing tests and substitutes. Capture an actual framebuffer symbol if a preview is useful; do not redraw an invented picture and call it executed firmware.
- Keep each project's configuration and assertions with that project. Reuse them on later changes; do not create another environment or replacement test framework. Only missing project-specific hardware substitutes or meaningful assertions need new code. A universal runner cannot infer all peripheral behavior from an arbitrary program.
- Follow the person's current goal and preferred style. Clear code and purpose skip unrelated questions. Inspect available context for target/framework first; ask one short choice only when a missing fact prevents a meaningful check. When expected behavior is unknown, report compilation/execution only rather than inventing acceptance criteria.
- Run checks proportional to the change. Background execution is preferred; user-requested browser previews remain possible using existing tools. Do not require an MCU simulator or change working hardware merely to satisfy the Skill.
- Report build, configured software checks, ARM execution with substitutes, MCU simulation and physical proof accurately. Virtual memory and mocked peripherals are not the board or its electrical behavior. This Skill never invokes the flashing runner. Deliver logs, result JSON and generated test/capture files actually produced; do not publish local caches or private project paths.

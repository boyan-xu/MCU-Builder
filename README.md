[English](README.md) · [简体中文](docs/README.zh-CN.md) · [Español](docs/README.es.md)

# Make Your MCU Ideas Real

**Bring an idea. Make something you can use.**

Make Your MCU Ideas Real helps turn your ideas into practical MCU products. Describe what you want it to do; AI works out the requirements and handles design, parts, firmware, simulation, setup and debugging with the tools it can actually use. You do not need to learn MCU programming or manage the code to begin.

Start with the hardware and software you already have. Get a checkable materials list with optional buying links for your region, a clear wiring image and short steps for the physical work. AI tests supported designs in a real MCU simulator and checks the electrical design separately before guiding the first connected run.

A reminder, a controller, a sensor device: your desired behavior sets the direction. The path follows your idea and actual feasibility rather than an imposed experience tier. Work toward a usable result in clear milestones, with the files and instructions to keep using and improving it.

## Choose how to work

| Entry | What it does | Who writes code |
| --- | --- | --- |
| [Make Your MCU Ideas Real](skills/build-with-ai-mcu/SKILL.md) | AI handles the technical path from idea to product | AI by default |
| [Develop with AI MCU](skills/develop-with-ai-mcu/SKILL.md) | Collaborate on a new product or continue an existing project | You or AI; change the choice when needed |

Each entry works on its own. Both adapt to your actual experience and preferred way of working. A clear request skips unrelated intake; no level test determines what you are allowed to create. The public title changed, but the repository address, folders and `$build-with-ai-mcu` / `$develop-with-ai-mcu` calls remain compatible.

## From idea to product

1. **Make the goal clear.** Discuss what it should do and how to check success. Relevant memory can include tools, experience, chat preferences, learning style and small habits. Your current request takes priority; no budget or style questionnaire is required.
2. **Use what fits.** Check existing code, settings, interfaces and hardware first. For new parts, prefer suitable MCU/module combinations with documented simulation support. A workable existing board is not replaced merely for convenience.
3. **See what to get.** Use the parts panel for specifications, quantities, available materials, missing items and estimated extra cost. Regional buying links are examples; equivalent sellers and parts are welcome.
4. **Let AI implement and verify.** AI writes, compiles, simulates and fixes the firmware using available tools. Choose your own coding role in the collaborative entry if wanted. You do not have to complete a course or manage code changes.
5. **Connect and try it.** Receive a checked wiring image and matching text. The order of unpowered wiring and board flashing follows the setup. Get one short action, expected result and feedback point at a time; existing authorization is reused for the same target.
6. **Keep your product.** Receive source, wiring, simulation files/results, a short use guide and known limits. You decide whether your own project stays private or becomes open source.

Conversation follows your pace without repeated probing or drifting away from the goal. Once the next step is clear, start doing it. A useful result within days is a goal when scope, tools and parts allow it, not a promise for every idea; product difficulty is assessed from real constraints rather than a fixed beginner catalog.

## Simulation and first operation

For supported designs, run relevant startup, normal, boundary, timing and failure scenarios before operating the connected circuit with external devices or loads. Keep the actual source/build version, connections, simulation project and observed result; recheck affected changes. A compile, a host unit test or a browser mock is not MCU simulation.

Simulation cannot prove zero bugs or that hardware cannot be damaged. Separately check actual supply, polarity, logic levels, current, resistors/drivers and load limits. Report build, logic tests, MCU simulation, electrical review, flash/readback and physical behavior separately.

Already own a board or module without a suitable simulation model? AI explains the coverage gap, keeps writing code and compiling, and runs applicable logic checks. With authorization for the exact target, isolated-board flashing/diagnostics can proceed after target and electrical checks. That powers the board; it does not mean the complete connected product passed simulation or is ready for full-load operation. See [the verification rules](skills/build-with-ai-mcu/references/verification.md).

## Install and start

Download with **Code → Download ZIP** or clone:

```sh
git clone https://github.com/boyan-xu/build-with-ai-mcu.git
```

Copy the whole folder for either or both entries (`skills/build-with-ai-mcu`, `skills/develop-with-ai-mcu`) into your tool's supported skills directory. For Codex, use `$CODEX_HOME/skills` when set, otherwise `~/.codex/skills`. Check an existing same-name skill before replacing it; refresh discovery or start a new session if needed. Each entry carries its own resources and one instruction set for all three languages. Available tools vary by platform.

```text
Use $build-with-ai-mcu. Make a reminder that sounds when my door stays open
for more than 30 seconds. Handle the technical work; I have an ESP32
and Arduino IDE already. Help me get a working result.
```

```text
Use $develop-with-ai-mcu. Continue my working STM32 project and add PWM control.
I want to write the code. Inspect the existing timer setup and help me
choose the next small implementation step.
```

No idea yet? Ask for five suitable possibilities. Already have parts or a partly working product? Start there. A milestone should lead toward your own goal, not replace it with an unrelated exercise.

## Included tools and evidence

- [Parts panel](skills/build-with-ai-mcu/assets/parts-checklist.html) and [integration notes](skills/build-with-ai-mcu/references/checklist.md): check items and retain valid progress in supported chat panels or standalone HTML. Link requests use the host's AI action when available; otherwise selectable request text is shown. The page does not secretly contact shops or an AI.
- [Low-voltage example](skills/build-with-ai-mcu/references/uno-led/README.md): matching image, connection definition, firmware and simulator diagram, with a [real MCU simulation record](skills/build-with-ai-mcu/references/uno-led/simulation-result.json) bound to the tested files. Its startup and digital-output checks passed in Wokwi; no physical device or electrical safety was tested. It is evidence of these scenarios, not a required first product.
- [Optional REA workflow](skills/build-with-ai-mcu/references/rea.md): when reproducing a product function, reuse an applicable existing [REA](https://github.com/morluto/rea) connection; only offer setup if needed and missing. Declining it does not stop ordinary work. Clarify rights before commercialization/public release; tool access does not grant rights to proprietary code or assets.

## Mechanical scope and practical limits

This release does not normally deliver automatic CAD, print-ready mechanical design or direct printing. For an enclosure, prefer ready-made cases/structures or a user-supplied model. Existing CAD skills, printers or CNC machines remain context. A future automatic CAD/print stage requires an explicit skill update; it is not enabled by a model's own confidence.

AI needs working tool connections to build, debug, simulate or access hardware. Necessary downloads, accounts and costs are explained first. Browser flashing needs compatible hardware and local access; universal zero-install support is not promised. Private credentials, memory and project records stay out of public files. This is a product workflow, not a fixed MCU course.

## Check the source

Run `node --test tests/*.test.mjs` for panel, package, connection and simulation-record consistency checks. Skill format can be checked with the official [skill-creator validator](https://github.com/openai/skills/tree/main/skills/.system/skill-creator). Unit checks are separate from the recorded MCU run and do not replace physical tests.

## License

[MIT](LICENSE). You may use, share and change these skills. Each person chooses their own product's publication and license.

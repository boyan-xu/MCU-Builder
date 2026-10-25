[English](README.md) · [简体中文](docs/README.zh-CN.md) · [Español](docs/README.es.md)

# Build with AI MCU

**Turn your idea into something you can use.**

Build with AI MCU offers two AI skills: one for your first microcontroller project, and one for the projects that follow. You do not need to learn coding or electronics before starting. If you already have some experience, choose to write your own code or let AI handle it. Start with what you want to make and how it should work.

The AI helps shape your idea and finds a practical way to build it using the hardware, tools, and skills you already have. It helps with parts lists, optional shopping links, clear wiring diagrams, code, flashing, and debugging, so you can focus on what you want your project to do.

There is no fixed course that everyone must follow. Start with one small feature or work toward a bigger goal. The path adapts to your situation, and the result is a project that fits your needs, with the files and instructions to keep using and changing it.

## Choose your skill

| Skill | Who it fits | Code ownership |
| --- | --- | --- |
| [Build with AI MCU](skills/build-with-ai-mcu/SKILL.md) | Little or no MCU experience | AI handles code by default |
| [Develop with AI MCU](skills/develop-with-ai-mcu/SKILL.md) | Understands basic operation and flashing; has made simple projects | You write, or AI writes; the choice can change |

Each skill works on its own. Known experience and current requests take priority; no repeated level test or forced switch is needed. If background is unknown and the request is vague, a short beginner/has-built-projects choice is enough.

## How it works

- **Your idea comes first.** A clear first message is enough to skip unrelated intake. Relevant memory can include MCU experience, chat preferences, learning style and small habits. These are used independently; current needs lead. No budget or style questionnaire is required.
- **Talk naturally, then act.** Get short choices when useful, not the same question over and over. The conversation follows your pace and stays on the project. Once the next step is clear, start doing it; you do not have to finish a long interview.
- **Reuse what you have.** AI checks code, configuration and available interfaces for a software solution before proposing new hardware. It does not replace a suitable board just for convenience, or try to solve a real missing sensor or power stage with code alone. Existing development and flash tools come first.
- **See what is missing.** Get a checkable parts panel with specifications, quantities, purpose and estimated extra cost. Optional buying links can be found for your country or region; equivalent products from other sellers are welcome.
- **Wire with a clear picture.** Get a labeled image and matching connection steps. AI checks the exact parts, explains a few needed basics and chooses whether wiring or flashing should come first.
- **Choose who writes when you have some experience.** In the beginner entry, AI handles code by default. In the next-project entry, you can write with guidance, review and debugging help, or let AI implement. Known choices are not asked again, and your request can change them. Existing flashing permission is reused for the same target.
- **Keep your own result.** Receive source files, wiring and a short use guide. You choose whether your project stays private or becomes open source.

## Install

Download this repository with **Code → Download ZIP**, or clone it:

```sh
git clone https://github.com/boyan-xu/build-with-ai-mcu.git
```

Copy the whole folder for the skill you want (`skills/build-with-ai-mcu` or `skills/develop-with-ai-mcu`) into your AI tool's supported skills directory; you may install either or both. For Codex, use `$CODEX_HOME/skills` when set, otherwise `~/.codex/skills`. Check an existing same-name skill before replacing it. Refresh skill discovery or start a new session if needed.

Each skill has one set of instructions for all three languages and includes its own resources. The conversation, parts panel and project instructions follow your chosen language. Other AI tools must support this skill format or let you load its instructions; available tools vary.

## Start with your idea

```text
Use $build-with-ai-mcu. I want a reminder when I leave a door open.
I already have an ESP32 and Arduino IDE. I have never used a microcontroller.
Help me work out how it should behave, and handle the code for me.
```

Have no idea yet? Ask for five suitable projects. Have parts or a half-built project? Start there. A difficult goal can be split into related steps without losing the original idea.

Already have project experience? For example:

```text
Use $develop-with-ai-mcu. Continue my working STM32 project and add PWM control.
I want to write the code myself. Help me inspect the existing timer setup
and choose the smallest next coding step.
```

## A feature you saw in another product

Name the specific behavior you want. When applicable, AI checks for a working [REA](https://github.com/morluto/rea) connection and reuses it; only if needed and missing does it offer installation or connection. Ordinary projects do not require REA, and declining it does not stop the work. See [the optional workflow](skills/build-with-ai-mcu/references/rea.md).

Permissions and relevant rights must be clear before commercial use or public release of a reproduction. REA does not grant rights to the target; personal learning is not automatic permission. The aim is your own implementation of the understood behavior, not redistribution of proprietary code or assets.

## Parts panel and wiring example

- [Reusable checklist](skills/build-with-ai-mcu/assets/parts-checklist.html): AI fills it with your actual parts. It works in a supported chat panel or as a standalone HTML file. Checks are saved when the host or browser allows it; changed specifications or quantities need checking again.
- [Panel integration notes](skills/build-with-ai-mcu/references/checklist.md): buying-link requests use the host's AI action when available, otherwise they become text you can copy. A standalone page does not secretly contact an AI or shop.
- [Low-voltage wiring example](skills/build-with-ai-mcu/references/uno-led/README.md): an inspected diagram, connection table and matching pin assignment. It illustrates the delivery standard, not a required first project.

## Tools and limits

These skills cover first builds and basic project experience, not an advanced embedded course or a flashing service. AI needs working tool connections to build, debug or reach your device. Browser flashing still needs compatible hardware, firmware and local access; zero-install support is not guaranteed.

Necessary downloads are explained first. Your existing work and private credentials are protected. A successful build or flash does not prove the physical project works. Hardware checks and permission still matter, without repeated approval requests for the same authorized operation. Your memory and private records are not published with projects.

## Check the source

Run `node --test tests/*.test.mjs` for the panel logic and example consistency checks. The skill can also be checked with the official [skill-creator validator](https://github.com/openai/skills/tree/main/skills/.system/skill-creator). Simulation and software checks do not replace physical testing.

## License

[MIT](LICENSE). You may use, share and change this skill. Each learner chooses their own project's publication and license.

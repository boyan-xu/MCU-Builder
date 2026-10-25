[English](README.md) · [简体中文](docs/README.zh-CN.md) · [Español](docs/README.es.md)

# Build with AI MCU

**Turn your idea into something you can use.**

Build with AI MCU is an AI skill for people who are new to microcontrollers. You do not need to learn coding or electronics first. Start by telling the AI what you want to make and how you want it to work.

The AI helps shape your idea and finds a practical way to build it using the hardware, tools, and skills you already have. It helps with parts lists, optional shopping links, clear wiring diagrams, code, flashing, and debugging, so you can focus on what you want your project to do.

There is no fixed course that everyone must follow. Start with one small feature or work toward a bigger goal. The path adapts to your situation, and the result is a project that fits your needs, with the files and instructions to keep using and changing it.

## How it works

- **Your idea comes first.** Talk about what you want to make, where you will use it and what success looks like. Available memory helps, but your current needs lead. No budget interview or theory course is required to begin.
- **Reuse what you have.** AI checks existing boards, parts and software before suggesting purchases or downloads. A suitable board is not replaced just because another is easier to use.
- **See what is missing.** Get a checkable parts panel with specifications, quantities, purpose and estimated extra cost. Optional buying links can be found for your country or region; equivalent products from other sellers are welcome.
- **Wire with a clear picture.** Get a labeled image and matching connection steps. AI checks the exact parts, explains a few needed basics and chooses whether wiring or flashing should come first.
- **Let AI handle code and debugging.** You describe behavior and help with physical steps. AI uses available tools and reuses existing flashing permission for the same target. It reports tested results and limits honestly.
- **Keep your own result.** Receive source files, wiring and a short use guide. You choose whether your project stays private or becomes open source.

## Install

Download this repository with **Code → Download ZIP**, or clone it:

```sh
git clone https://github.com/boyan-xu/build-with-ai-mcu.git
```

Copy the entire `skills/build-with-ai-mcu` folder into your AI tool's supported skills directory. For Codex, use `$CODEX_HOME/skills` when set, otherwise `~/.codex/skills`. Check an existing same-name skill before replacing it. Refresh skill discovery or start a new session if needed.

One set of [skill instructions](skills/build-with-ai-mcu/SKILL.md) serves all three languages. The conversation, parts panel and project instructions follow your chosen language. Other AI tools must support this skill format or let you load its instructions; available tools vary.

## Start with your idea

```text
Use $build-with-ai-mcu. I want a reminder when I leave a door open.
I already have an ESP32 and Arduino IDE. I have never used a microcontroller.
Help me work out how it should behave, and handle the code for me.
```

Have no idea yet? Ask for five suitable projects. Have parts or a half-built project? Start there. A difficult goal can be split into related steps without losing the original idea.

## Parts panel and wiring example

- [Reusable checklist](skills/build-with-ai-mcu/assets/parts-checklist.html): AI fills it with your actual parts. It works in a supported chat panel or as a standalone HTML file. Checks are saved when the host or browser allows it; changed specifications or quantities need checking again.
- [Panel integration notes](skills/build-with-ai-mcu/references/checklist.md): buying-link requests use the host's AI action when available, otherwise they become text you can copy. A standalone page does not secretly contact an AI or shop.
- [Low-voltage wiring example](skills/build-with-ai-mcu/references/uno-led/README.md): an inspected diagram, connection table and matching pin assignment. It illustrates the delivery standard, not a required first project.

## Tools and limits

This is a beginner skill, not an advanced embedded course or a flashing service. AI needs working tool connections to build, debug or reach your device. Browser flashing still needs compatible hardware, firmware and local access; zero-install support is not guaranteed.

Necessary downloads are explained first. Your existing work and private credentials are protected. A successful build or flash does not prove the physical project works. Hardware checks and permission still matter, without repeated approval requests for the same authorized operation. Your memory and private records are not published with projects.

## Check the source

Run `node --test tests/*.test.mjs` for the panel logic and example consistency checks. The skill can also be checked with the official [skill-creator validator](https://github.com/openai/skills/tree/main/skills/.system/skill-creator). Simulation and software checks do not replace physical testing.

## License

[MIT](LICENSE). You may use, share and change this skill. Each learner chooses their own project's publication and license.

---
name: build-with-ai-mcu
description: Use when a microcontroller beginner wants to turn a personal idea into a working hardware project with AI, needs suitable project ideas or parts, or wants help with wiring, firmware and debugging without having to manage code. Supports ESP32, STM32 and Arduino projects. Not an advanced embedded engineering curriculum or a standalone theory lesson.
---

# Build with AI MCU

Help a beginner make their own idea real. Understanding the desired result is the main job; AI carries the technical work it can actually do. The person's present situation and choices lead, not the order of this document. No theory, coding experience, fixed lesson or budget interview is required to start.

At entry, read [working style and pacing](references/working-style.md). Use relevant memory about communication, learning and small habits independently of MCU experience. A concrete first-message goal takes priority over intake questions. If experience is unknown and the request is vague, offer one short beginner/has-built-simple-projects choice; otherwise proceed with the useful next step. The companion `develop-with-ai-mcu` is for people with some project experience, but do not force a switch or sibling installation when it would obstruct the current request.

## Understand the idea and the current state

- Start from the goal already stated. Fill only missing details about behavior, use or success that affect the next decision. Use natural short choices where possible, not a survey of prerequisites. Do not rephrase unanswered questions repeatedly or end every reply with a question. Once enough is known for a safe useful action, start it instead of extending the interview.
- Before suggesting projects, consult relevant global memory when the platform exposes it. Include communication style, learning preferences, small habits and pace as well as interests, past builds, parts, tools and skills. Current user statements and verified facts override old memory. Do not invent access, scan unrelated private history or repeat reliable known information. Unknown MCU ability does not erase known interaction preferences.
- Adapt to their current stage. A person with an idea needs a design; someone with parts needs a compatibility check; someone already wired may need debugging. Skip completed steps. If no memory is available, ask only for context that matters now.
- If they have no direction, offer five suitable ideas from easy to hard, with the intended result, rough extra cost and main challenge. Adapt to interests and existing resources; no fixed list or mandatory starter exercise.
- If a goal is difficult or costly, explain the concrete gap and offer a smaller related step. Keep the original goal visible, explain what can be reused and what result leads to the next step. Let the person choose; never silently replace their project.
- Budget is optional context, not a gate. Show a minimal workable proposal and estimated costs without waiting for a spending cap. Honor a supplied limit and do not keep asking for it. Discuss cost only when a real tradeoff needs a choice; label currency assumptions and unverified prices.

## Reuse what they have; show what is needed

- First check existing code, configuration, protocols and interfaces for a software solution. Establish a real capability gap before recommending new hardware; software cannot replace a missing sensor, radio or required power stage. Follow the person's current stage and skip unnecessary purchases or discussions.
- Inspect existing boards, modules, fabrication tools and installed software first. Reuse suitable hardware even if another board would be easier for AI. Replace it only when it cannot meet the agreed need, explaining the limitation and alternatives. Account for CAD, a 3D printer or CNC when useful; do not force their use.
- Once the first task is clear, give the minimum parts list: exact specification/compatible alternatives, quantity, purpose, confirmed available parts, missing parts and estimated extra cost. Include needed cables, power, shipping and fabrication consumables, with unknown costs visible. Having a part does not establish that enough of it is available.
- Use [the checklist template](assets/parts-checklist.html) and [its integration notes](references/checklist.md) to make a project-specific interactive panel. Show it in chat when supported and provide a standalone HTML copy otherwise. Preserve valid progress when the list changes; changed specifications or quantities need rechecking. Do not make the learner edit JSON or template code.
- Buying links are optional examples, not required products or sellers. Offer the panel action to ask AI for links for all items or only missing items. Use a reliable known country/region; if unknown, ask only when finding links and do not delay the parts list. Never infer a shipping region from language or timezone, or ask for a full address.
- When links are requested, research current listings and official specifications. Match the actual variant, quantity and delivery region; state unverified stock, shipping or prices. Update the panel without losing unchanged checks. No automatic purchases, affiliate tracking or collection of payment details.

## Let AI handle code and available tools

- By default in this beginner entry, AI writes and fixes code, builds firmware and operates available programming/debugging/flashing tools. Deliver code as files; do not assign coding homework or ask the learner to manage source changes. They describe behavior, connect parts and report physical results. If they explicitly want to write code themselves, respect that choice: guide, review and debug instead of taking over the implementation.
- Prefer the person's existing IDE, debugger, compiler or flashing tool. Do not build a replacement IDE, serial console or custom flashing platform when an existing tool works. Tool availability is not proof of device access; say what AI can actually operate.
- Use working interfaces or compatible browser flashing where useful. Browser flashing still needs compiled firmware, a compatible device/browser and local access. Never promise universal zero-install support or claim that cloud AI can reach USB without a bridge.
- Before any necessary download, explain what it is, why it is needed and its official source. This includes drivers, board packages, compilers and flash tools. Respect a no-install limit and report the exact blocker or a supported alternative; do not silently install or bypass security prompts.
- Explain the few essentials needed for the current action in plain language, even when not asked: for example voltage compatibility, common ground, LED polarity or why a motor needs a driver. Tie each point to the next action; no prerequisite course, quiz, long theory section or default register/syntax lesson. Explain code or deeper logic when requested, then return to the project.

## Show wiring, then connect or flash as appropriate

- Before the learner wires anything, identify exact board/module models and verify pin labels, voltage, power and any required driver/limiting parts against official references. Ask for labels or clear photos when needed; do not guess a pinout from a board family name.
- Generate and inspect a clear wiring image plus matching text. Prefer a deterministic labeled SVG diagram: show board/module names, viewing direction, voltage, every wire ID and both endpoint pin names. Distinguish joins from crossings without relying on color alone. Use overview/detail views when crowded. Do not use an unverified AI illustration as the electrical reference.
- Use one connection definition for the image, the numbered connection table and the firmware pin assignments. Check them together, render the image and inspect legibility/endpoints before delivery. Provide a scalable image and export PNG if the client cannot show SVG. See the [low-voltage example](references/uno-led/README.md) for the image/table/code check; it is not a compulsory project.
- Choose wiring/flash order from the actual setup: an isolated board may be flashed first; another project may need unpowered wiring first. Tell the learner to disconnect power before changing wires. Motor movement needs verified power, wiring and limits plus a suitable stop behavior.
- Once the learner authorizes flashing a specific target, reuse that authorization through ordinary debugging iterations. Do not ask again before each flash. AI still verifies target, port, wiring, power, active debugger and existing firmware without turning checks into repeated approval questions. Ask only when the target/scope changes, authorization is absent or a newly discovered overwrite risk requires a choice. Build-only does not authorize flashing. Preserve existing work and back it up when supported.

## When the idea comes from another product

Read [optional REA analysis](references/rea.md) when the goal is to reproduce a product function. Reuse a working REA connection when applicable; only offer installation/connection when actually missing. Ordinary projects do not require REA. A photograph is not access to firmware or circuitry. Keep evidence, guesses and release rights distinct, and return to the learner's own project after understanding the desired behavior.

## Debug to the person's goal, then hand it over

- Use available logs, debugger and measurements to diagnose failures and make bounded, evidence-based fixes. Ask the learner only for physical actions or observations AI cannot obtain. Do not send them to edit code or repeatedly flash blindly.
- Report code checks, build, flash/readback and physical behavior separately. A compiled project is not a working device. Be clear about untested results; when blocked, leave the current files and one concrete next action.
- Test the agreed behavior, then give the working source, exact wiring image/table and a short use guide suited to this person. The deliverable may differ for two people with the same rough idea. This skill is for beginners; do not add an advanced-user curriculum.
- Keep passwords/tokens in private input or local provisioning, outside chat, shared code, logs and firmware. Do not expose a control endpoint to the internet as a shortcut. Distinguish local phone control from access over the internet when the project needs that choice.
- Each learner chooses whether their project is public. Reuse clear permission already given for the same installation, flashing or publication; ask again only if scope changes. Before an authorized publication, resolve destination/license, check files and history for secrets, publish only chosen project material and read back the remote files. Global memory, profiles and private records stay private.
- Speak in the learner's chosen language, including the panel, wiring labels and explanations. Keep English, Chinese and Spanish presentations separate rather than mixing translations sentence by sentence. Adapt the path as new facts arrive; never prioritize this checklist over the person's actual needs.

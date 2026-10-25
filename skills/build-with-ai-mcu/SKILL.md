---
name: build-with-ai-mcu
description: Use when someone wants to start or grow a hands-on microcontroller or maker project with AI, needs project ideas or a parts list, or wants AI to turn a hardware idea into working firmware. Also use for 单片机入门、创客项目、按预算选项目 and AI-assisted ESP32, STM32, or Arduino builds. Not for a standalone code explanation or theory lesson.
---

# Build with AI MCU / 从想法到单片机作品

Help people make what they want. The learner describes the result; AI handles the code and tool work it can actually do. A working first step matters more than a course outline.
帮助学习者把想法做出来：人说清需求，AI 负责能实际完成的代码和工具操作。先做成一个小功能，不先安排理论课程。

## 1. Know the person first / 先了解当前状态

Before suggesting projects, read relevant global memory that the current AI platform makes available. Look for maker interests, past projects, tools, parts, and skills. Use focused retrieval; do not scan unrelated private history. Never invent memory access or require a personal path, account, or memory system.
推荐前先看平台可访问的相关全局记忆，了解兴趣、做过的项目、设备、材料与基础；不翻无关隐私，不编造已读取的记忆，不绑定任何人的目录或账号。

Treat memory as context, not fresh facts or permission. Briefly check anything old that affects the choice. If memory is absent, say so in one short sentence and ask for the needed context. Do not make the learner repeat reliable facts already given.
记忆不是当前事实或操作授权；影响选择的旧信息需确认。无记忆时简短说明，再问必要信息；已有可靠信息不重复问。

Ask what they want to make and confirm their **current budget and currency before recommending projects or purchases**. Learn which parts they already own and whether the budget covers only new parts or the whole build. An old budget is not today's budget. If they do not know a budget yet, help set a provisional ceiling before choosing.
先问想做什么，并在推荐项目或购物前确认本次预算、币种、已有材料，以及预算只算新增材料还是整套成本。旧预算不能直接沿用；没想好时先协助定一个暂定上限。

Use memory and a short question to fill only gaps that change the advice: 3D printer, CNC or other fabrication tools; boards, sensors, motors, power supplies and basic electronics tools; CAD/modeling, code, wiring and electronics experience. Ask about device/OS, workspace or time only when it affects the next choice.
结合记忆补齐会影响建议的信息：3D 打印机、CNC 等加工设备，板子、传感器、电机、电源和电子工具，以及建模、代码、接线与电子基础。电脑系统、场地或时间只在影响下一步时询问。

Keep the opening short: reuse known facts and bundle two or three related questions. Ask further questions when a real choice needs them; do not turn intake into a long form.
开场复用已知事实，合并两三个相关问题；遇到实际选择再继续问，不让新手先填长问卷。

## 2. Choose a useful first project / 选合适的第一步

If the learner has a goal, work toward it. If they have no idea, offer **five projects, ordered from easy to hard**, after checking the budget and resources. For each, state the result, estimated extra cost in the agreed currency, parts to buy/reuse, and the main challenge. Keep ideas within budget; do not pad the list with unaffordable builds. Verify current buying advice with official specs and current listings when tools allow; label unverified prices as estimates.
已有目标就围绕目标推进；没方向时，确认预算与资源后给五个从易到难的项目。每项说明效果、预计新增花费、购买与复用材料及主要难点。建议须符合预算；能查时核实规格和现价，未核实价格注明估算。

Use the person's strengths: CAD and a printer can help with an enclosure or simple mechanism; coding experience may support a richer interface if wanted. Do not make every project use every owned tool, or make coding skill a condition of entry.
会建模、有打印机，可以考虑外壳或简单结构；有代码基础且有兴趣，可增加界面功能。不强迫用遍所有设备，也不把会代码当作入门门槛。

If useful, adapt this easy-to-hard seed list: button light → room display → phone-controlled low-voltage light → remote plant monitor → phone-controlled car. It is a starting point, not a fixed curriculum; replace it to fit interests, tools, budget and local costs.
可参考：按钮灯 → 环境数据显示 → 手机控制低压小灯 → 远程植物监测 → 手机控制小车。这只是候选示例，须按兴趣、设备、预算和当地成本调整。

When a goal is too hard or costly, explain the specific gap and propose a smaller **related** task, keeping the original goal visible. Say what it proves, what can be reused, and what result unlocks the next step. Let the learner choose; do not silently replace their goal or force a detour if they prefer the full task.
目标过难或超预算时，说清具体缺口，建议与原目标相关的小任务，保留最终目标。说明小任务验证什么、后续复用什么、达到什么效果再进阶；由学习者选择，不擅自换题或强制绕路。

Example: an internet-controlled robot arm can start with one servo and a safe light load, then local phone control, more joints, and finally internet access. Check the budget for each step; never imply the first step's price buys the full arm. Do not spend the whole budget on the final design before the first step works.
例如外网机械臂可先做单舵机轻载，再做同一 Wi-Fi 手机控制、多关节，最后接入外网。分步核算成本，小任务价格不代表整机价格；第一步未验证前不买齐最终方案。

## 3. Turn the idea into a build / 从需求到制作

Agree on the first task and an observable success check in plain words. Ask only for missing details that change the build: input/action/output, size or load, power, range, and failure behavior. For phone control, distinguish same-Wi-Fi control from access over the internet; Wi-Fi on a board alone does not provide safe remote access.
用日常语言确认第一步与可观察的成功效果；按需问输入、动作、输出、尺寸或负载、供电、距离与出错行为。手机控制须区分同一 Wi-Fi 和外网；板子带 Wi-Fi 不等于已具备安全的外网控制。

Choose a board to fit the job, available tools and cost. ESP32 is a candidate for wireless work, not a rule; STM32, Arduino-compatible boards or an existing board may fit better. Give the minimum parts list with quantity, purpose and relevant compatibility (exact board/part, voltage, pins, connectors, power and any programmer). Include needed cables, power, shipping and fabrication consumables; show any cost not yet known before a purchase. Do not place orders without a purchase request.
按任务、现有工具和成本选板；无线项目可考虑 ESP32，但不固定选它。清单列数量、用途与相关兼容要求，计入必需线材、电源、运费与加工耗材；购买前说明未确定费用。未经购买请求不下单。

AI writes the firmware, builds it and handles available tools. The learner describes behavior, connects hardware and checks the result. Do not assign code-writing homework, dump code into the conversation, quiz prerequisites, or teach syntax/registers by default. Deliver source as files. If asked about code or low-level logic, explain the requested part in small steps, then return to the project.
AI 写固件、编译并操作可用工具；学习者描述效果、接线与验收。默认不布置写代码作业、不在对话里堆代码、不考前置知识或讲寄存器；源码交付文件。主动问代码或底层时再分步讲相关部分，然后回到项目。

## 4. Use the least setup that works / 少安装，能验证

First inspect available interfaces, tool connections and installed tools. Prefer an existing working path; use browser flashing or a direct tool/API when compatible. A browser flasher still needs compiled firmware and device access. A cloud AI cannot reach a local USB port without a working bridge and user-granted access. Never promise zero setup for all boards or computers.
先查现有接口、工具连接与已安装工具；优先可用路径，兼容时用网页或接口烧录。网页仍需已编译固件和设备访问权限；云端 AI 不能凭空访问本地 USB，不能承诺所有环境零安装。

**Before any download**, tell the learner what will be downloaded, why, and its official source. This includes drivers, compiler packages, board support and flashing tools. Reuse installed tools; download only what this step needs. AI does the setup where authorized and possible. If the learner requires no installs, respect that limit and offer a supported route or state the exact blocker. Do not bypass security prompts or install silently.
任何下载前先说明下载什么、为什么需要、官方来源；驱动、编译器、板卡支持包与烧录工具都包括。复用已有工具，只下当前必需内容；坚持不安装时尊重限制，给可行替代或说明具体阻碍，不静默安装或绕过安全提示。

Before flashing, verify the exact board/chip, connection/port, wiring and power, existing firmware and any active debugger, and the learner's authorization for that target. Preserve existing work and make a backup when supported; explain any known loss before an overwrite. A request to build code alone is not permission to flash. For motors or moving parts, confirm wiring, power and limits before movement, and add a suitable stop behavior.
烧录前确认芯片板型、连接端口、接线供电、原固件、活动调试器及目标授权；保护已有成果，支持时备份，覆盖前说明已知损失。只编译不等于允许烧录；电机或运动部件先确认接线、供电与限位，并设置合适的停止行为。

Keep Wi-Fi passwords and tokens in private input or local provisioning, outside public source, logs and chat. Provide a blank example config if needed. No real secrets in examples, commits or shared firmware. Do not expose a control endpoint to the public internet as a shortcut.
Wi-Fi 密码和令牌走私密输入或设备配置，不进入公开源码、日志或聊天。需要时提供空白配置示例；示例、提交与共享固件不得带真实秘密，不靠直接暴露控制接口省事。

Report code checks, build, flash/readback and physical behavior separately, with real evidence. If something fails, inspect the evidence, ask the smallest useful question, and try a bounded fix. Do not call a compiled project a working device or repeat blind flashing attempts. When blocked, leave the source and one clear next action.
分别报告代码检查、编译、烧录或读回、实物效果及证据。出问题先查证据，只问必要问题，有限次尝试；不把编译通过说成实物成功，不盲目反复烧录。受阻时保留源码和明确下一步。

## 5. Finish, then offer sharing / 完成后自选开源

Review the agreed success check and the next related step. Ask whether the learner wants this project public; using this skill does not grant publication permission. If yes, prepare source, wiring/pin map, parts, setup/build/flash steps and test limits. Agree on the destination and license, check files and Git history for secrets/private data, publish only authorized content, then read the remote files to verify the result.
按约定验收，并指出后续相关步骤。询问是否公开项目，使用 Skill 不等于同意发布；同意后整理源码、接线、材料、操作步骤与验证限制，确认仓库及许可证，检查文件和 Git 历史，发布后读取远端核实。

Reuse clear permission already given for the same installation or publication; do not ask again unless its scope changes. Still resolve missing target details and disclose downloads before they happen.
同一次安装或发布已有明确授权就复用，不重复确认；范围变化才再问。仍需查清目标，并在下载前说明。

Global memory, personal profiles and private project records stay private. Share only the project material the learner chose. If sharing is declined, deliver locally and continue normally.
全局记忆、个人画像与私有工程记录保持私密，只分享学习者选定的项目材料。不愿开源就本地交付，正常继续。

Use short, plain steps in the learner's language; retain useful terms such as GPIO or firmware with a brief meaning when needed. Match their pace, and ask directly when a missing fact changes the next action.
用学习者能懂的语言写短步骤，必要术语顺手解释；按其节奏推进，缺少会影响下一步的事实就直接问。

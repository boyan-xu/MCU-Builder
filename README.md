# Build with AI MCU / 从想法到单片机作品

An AI skill for people who want to make things with microcontrollers, even if they have never written code.
一个面向单片机新手与创客的 AI Skill：你描述想要的效果，AI 帮你选材料、写代码、使用工具和验证结果。

**Start with what you want to make, not a code course.**
先做想做的东西；只有你想了解代码或底层逻辑时，再深入解释。

## How it helps / 它怎么帮你

1. **Know you first.** Read relevant global memory when your AI can access it; check your current budget, tools and skills. 没有可用记忆就简短询问，不假装了解你，也不重复问可靠的已知信息。
2. **Pick a project that fits.** If you have no idea, get five ideas from easy to hard, with rough extra cost and the main challenge. 结合兴趣、已有材料、3D 打印机、CNC、建模或代码基础推荐，不固定让每个人买同一块板。
3. **Keep big goals, start small.** A hard goal becomes a related first task, with parts and progress you can reuse. 保留最终目标，每一步有具体效果；不会把小任务预算说成整机预算。
4. **Describe, build, check.** AI handles code and available tool work; you connect parts and check the result. 默认不布置写代码作业；接线、供电和实际效果仍需你配合。
5. **Share if you want.** Your own project can stay private or become open source. 本 Skill 开源，不代表你的作品也必须公开。

## Install / 安装

Download this repository with **Code → Download ZIP**, or clone it:
可用 GitHub 的 **Code → Download ZIP** 下载，也可运行：

```sh
git clone https://github.com/boyan-xu/build-with-ai-mcu.git
```

Copy the entire `skills/build-with-ai-mcu` folder into your AI tool's supported skill directory. For Codex, use `$CODEX_HOME/skills` if set, otherwise `~/.codex/skills`. The result should contain:
把整个 Skill 文件夹放进所用 AI 工具支持的 Skills 目录。Codex 优先使用已设置的 `$CODEX_HOME/skills`，否则使用 `~/.codex/skills`。目录结果如下：

```text
<skills-directory>/build-with-ai-mcu/
  SKILL.md
  agents/openai.yaml
```

Do not replace an existing skill without checking it first. Refresh skill discovery or start a new session if your tool needs it.
已有同名 Skill 时先检查，不直接覆盖；按工具要求刷新技能发现或开启新会话。

This is an instruction skill, not a driver, compiler or flashing service. There is no required MCP server or bundled executable. Other AI tools need to support a `SKILL.md` skill, or let you load the file as instructions; tool access differs by platform.
它是流程指令，不是驱动、编译器或烧录服务，不依赖指定 MCP 服务，也不附带可执行程序。其他 AI 平台需支持此类 Skill 或手动加载指令；可用工具因平台而异。

## Try it / 开始使用

```text
Use $build-with-ai-mcu. I have never used a microcontroller.
I have a 3D printer and some CAD skills. My new-parts budget is 200 CNY.
Help me choose something useful to make.
```

```text
用 $build-with-ai-mcu。我想做外出也能用手机控制的机械臂，
但我刚入门，会一点建模，预算 200 元。
先帮我找一个能通向这个目标的小任务，代码由你来写。
```

Have a board already? Say what it is and what you want it to do. The skill should reuse it when it fits rather than start a shopping list from scratch.
已经有板子就说明型号和目标，合适时先复用；你无需先学会写代码。

## Tools and limits / 工具与边界

- **Memory is optional.** An AI can use only the memory its platform exposes. Old facts need checking, and your private memory stays out of public projects. 全局记忆不可用时先问必要信息，不要求新建个人数据库。
- **Budget comes before advice.** Costs include needed cables, power and tools; prices are estimates unless checked. 先问本次预算与币种，再推荐；按已有材料计算新增花费，不承诺固定价格。
- **No silent downloads.** Before a driver, compiler or other download, AI must say what it is, why it is needed and the official source. 下载前说明，不默认安装整套 IDE；不愿安装时尊重限制。
- **Browser flashing is a possible route.** It still needs a compatible browser/board, compiled firmware and local device access. AI cannot reach USB hardware without a working connection. 网页烧录不等于所有设备零安装，也不代替编译。
- **Protect existing work.** Build-only requests do not authorize flashing. Verify the target and preserve existing firmware; confirm motor wiring, power and limits before movement. 编译、烧录和实物成功分别报告，不把一个说成另一个。
- **Keep secrets private.** Use private device setup or local input for passwords and tokens, not chat or public source. 不上传秘密、个人记忆或私有工程记录；公开项目须经你选择。

For browser flashing, see the vendor's [esptool-js](https://github.com/espressif/esptool-js). It writes compatible ESP firmware through Web Serial; it does not compile your source. For the skill format, see [OpenAI's skill-creator](https://github.com/openai/skills/tree/main/skills/.system/skill-creator).
网页烧录可参考上述 Espressif 官方项目；具体板型与浏览器兼容性应在实际操作前核实。

## License / 许可证

[MIT](LICENSE). You may use, share and change this skill. Your hardware projects keep their own ownership and license choices.
你可以使用、分享与修改此 Skill；自己的硬件项目由你决定归属与许可方式。

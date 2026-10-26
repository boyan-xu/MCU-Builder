[English](../README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md)

# 让你的想法成真

**带着想法来，做出可以使用的东西。**

告诉 AI 你希望产品怎样工作，它会利用实际可访问的工具，协助需求、方案、材料、固件、必要检查、配置和调试。优先使用已有软硬件；不用先学编程或管理代码，也可以选择自己写代码。已有明确目标时跳过无关问卷，不按经验水平人为限定作品难度。

## 选择入口

| Skill | 用途 |
| --- | --- |
| [MCU Builder](../skills/build-with-ai-mcu/SKILL.md) — `$build-with-ai-mcu` | AI 承担从想法到产品的技术工作。 |
| [代码协作](../skills/develop-with-ai-mcu/SKILL.md) — `$develop-with-ai-mcu` | 新建或继续工程，自选谁写代码。 |
| [后台检查](../skills/test-mcu-in-background/SKILL.md) — `$test-mcu-in-background` | 复用已有软件和缓存，执行针对性检查。 |
| [固件烧录](../skills/flash-mcu-firmware/SKILL.md) — `$flash-mcu-firmware` | 用已有工具预览并执行已授权烧录。 |
| [产品选购](../skills/select-products-to-cart/SKILL.md) — `$select-products-to-cart` | 比较有证据的规格并补齐购物车，绝不下单。 |
| [可选 PCB 设计](../skills/design-pcb-with-ai/SKILL.md) — `$design-pcb-with-ai` | 使用已有、可操作的 EDA 软件完成用户要求的电路板设计和检查。 |

六个文件夹均可独立安装；已有五个调用名及仓库路径不变。不会强制安装其他入口。下载 ZIP 或克隆后，将需要的完整文件夹从 `skills/` 复制到工具支持的 Skill 目录。Codex 使用 `$CODEX_HOME/skills`，未设置时使用 `~/.codex/skills`；替换前检查旧副本，必要时刷新发现。平台可用工具可能不同。

```sh
git clone https://github.com/boyan-xu/build-with-ai-mcu.git
```

```text
使用 $build-with-ai-mcu。做一个门开超过 30 秒就响的提醒器。
我已有 ESP32 和 Arduino IDE，请负责代码。
```

```text
使用 $develop-with-ai-mcu。继续我的 STM32 工程，增加 PWM 控制。
我想自己写代码，请先检查定时器配置并指导下一步。
```

## 默认直接给可复制的编号材料清单

先给完整的普通编号文字清单，每项包含准确型号/规格、用途、所需/已有/缺少数量，以及有来源和日期的预计补购费用；没有证据就明确写未知。另给可直接复制的搜索词，保留关键规格和包装数量，包含电线、电源及必要耗材。未知购物平台或地区不耽误清单；核实过的链接可以补充文字。旧交互面板只在用户要求时作为可选资源。

完整清单后仅询问一次是否需要购物车帮助。同意后，仅在平台未知时再问平台，并说明只加购物车，不结算、下单、付款或订阅；复用已知清单/网站授权，拒绝后不重复询问，仅要链接就只给链接。硬性规格、兼容性、库存、配送、商家与明确预算先作为门槛，再按有证据的偏好匹配数量排序，之后才比较价格。可选 `preferred_specs` 是标量映射，以候选 `specs` 和逐项 `spec_evidence` 为依据；没有证据不加匹配分，省略偏好保持原有总价/到货/官方商家顺序，不编造适配评分。核对准确变体、包装数量及最新购物车，保留其他商品。[选购契约](../skills/select-products-to-cart/references/workflow.md)。

## 主对话聊产品，技术工作交给持续子代理

支持子代理时，同一个能力合适的固件子代理负责源码、构建、测试和调试；仅在要求 PCB 时增加独立 PCB 子代理。最多并行两个，同一范围一个写入者。主 AI 掌握产品选择和授权，只接收简短结果、检查/证据路径、限制和下一步；用户自己写代码时不擅自重写。没有子代理时继续有界工作并明确能力限制；委派不增加硬件、购物、安装或发布授权。

两个产品入口均包含完全相同、独立的标准库工具 `scripts/mcu_project.py`，要求 Python 3.10+，无兄弟 Skill 导入，也不建立登记系统。AI 维护可选项目数据，不让用户填 JSON 表单；复用已有工具与缓存，必要下载先解释。

| 命令 | 结果 |
| --- | --- |
| `validate` / `export --for test\|flash\|shopping` | 按阶段检查并导出现有执行器输入；按实物库存扣除已有数量。 |
| `parts` | 普通编号的准确材料/搜索文字及一次询问、平台复用状态。 |
| `wiring` | 同一连接定义生成 SVG、逐根接线文字和引脚绑定。 |
| `acceptance` / `diagnostics` | 如实记录验收状态与证据，并摘要明确允许的本地报告。 |
| `package` | 明确文件清单和哈希的 ZIP，标为草稿/未验证。 |
| `package --reproducible` | 最终交付模式，检查分类、输入、构建/版本关联并附解压后的入口指南。 |

[项目工具契约](../skills/build-with-ai-mcu/references/project-tools.md) · [复制包契约](../skills/build-with-ai-mcu/references/replication.md) · [虚构草稿示例](../skills/build-with-ai-mcu/assets/project-example/mcu-project.json)。

## 仅在需要时设计 PCB

主 AI 从已核实的准确器件、网络/引脚、电源、封装来源、板框尺寸/形状/单位、连接器、安装孔、禁布区及制造约束生成 `pcb-brief.json`，只问阻塞事实。持续的 PCB 子代理在用户已有且可操作的 EDA 软件中实际画原理图、摆件、布线，与固件子代理分工。没有可用软件连接或子代理时，如实交付 brief/草稿，不能声称电路板已完成，也不强迫安装软件。

检查包括原理图/ERC、真实器件与封装焊盘/极性对应、布局布线/DRC，以及虚拟器件和三维装配的间隙、方向、尺寸及连接器可操作空间。缺少模型继续未知；有用且有可靠模型时才选择电路仿真。各类证据分开报告，没有零错误保证。

交付可编辑 EDA 源文件、原理图、PCB、准确 BOM、网络/连接及检查报告和限制。代工路线含 Gerber/钻孔及必要装配资料；DIY 路线含对应工艺的 1:1 铜层、板框和钻孔图。不知道准确机器、刀具和工艺时不生成通用 G-code。重新打开最终制造文件，核对并绑定版本。关键器件、网络、电源、封装或工艺未知时只能标为草稿。PCB 属于电子设计，自动机械 CAD 和直接打印仍不在本版本范围。[PCB 工作流](../skills/design-pcb-with-ai/references/workflow.md)。

## 别人能照着做的最终复制包

最终包包含接线图片和逐根引脚文字、准确 BOM/规格/数量/搜索词、完整可构建应用源码/配置/库/素材、需要时匹配的编译固件、准确工具/环境版本及构建/烧录步骤、电源/装配/使用/验收说明、使用过的 PCB/机械/打印文件、许可证/第三方署名、证据/版本哈希及已知限制。必须包含选定项目所有必要输入，不能缺 include/素材、依赖私有路径、隐藏 AI 修复，或再找一次 AI 完成设计。

不能合法打包的工具或依赖，明确给出准确版本、官方获取/配置说明和外部前置条件；解压后的 `START-HERE.md` 会列出它们，不能暗示零下载或完全离线。凭据由复制者本地配置。`--reproducible` 检查文件分类、引用头文件及成功构建报告与输入/固件/工具/版本的关联，不执行代码；AI 仍需审核真实干净构建及完整依赖清单，工具不能单凭标签证明任意传递依赖完整或报告真实。普通包继续标为草稿。

目标是按准确器件和步骤得到同一设计、配置和行为，不再写代码或重新设计。文件完整与实物验证分开；物理公差和未测试行为不能保证完全相同。最终状态前必须解决关键电源/引脚/设计事实，否则明确阻塞项。

## 验证与实物边界

按项目、变化和风险选择检查，不要求每个项目运行所有测试或仿真器；优先现有后台工具，需要时提供浏览器预览。构建、主机逻辑、MCU 仿真、电气审核、烧录/读回和实物结果分开报告，证据绑定受测版本。主机测试或网页模拟不是 MCU 仿真，也不证明电气安全。

接线/上电前核对准确型号、引脚、电源、极性、电流及驱动，检查图片与固件引脚一致。改线断电；运动需要限位和停止措施。只构建不授权烧录。同一目标正常调试复用已有明确烧录授权，仍核对当前固件、目标、调试器并保留原工程。下载、安装和发布各有边界，私密记录与秘密不进公开文件，本地 ZIP 不等于发布。

## 真实案例与历史证据

[STMGames V1](../showcases/stm-games-v1/README.zh-CN.md) 是经过多轮交流和修改的真实 STM32 OLED 游戏机。制作者设计外壳并完成实物，GPT-6.1 Sol 完成应用代码，保留第三方署名。[源码包](../showcases/stm-games-v1/firmware-source.zip)、[接线图](../showcases/stm-games-v1/wiring.svg)、[原始 3MF](../showcases/stm-games-v1/OLEDGames.3mf)。电源/电气事实仍有未知，因此**不能称为完整可复制**；本轮未操作硬件或重跑所有游戏。

![黄色外壳中的 STMGames V1](../showcases/stm-games-v1/photos/front.jpg)

[UNO 低压例子](../skills/build-with-ai-mcu/references/uno-led/README.md) 和[虚构商店浏览器记录](../skills/select-products-to-cart/references/fixture-verification.json) 是其当时源码和场景的历史证据；修改源码不代表重新运行浏览器或 MCU。[REA 分析](../skills/build-with-ai-mcu/references/rea.md) 继续可选，优先已有软硬件。

## 检查源码与许可

运行 `python -B -m unittest discover -s tests -p "*_test.py"` 与 `node --test tests/*.test.mjs`，逐个使用 skill-creator 校验 Skill。测试使用本地虚构目标/厂商进程，不操作实物或真实购物账户。[MIT 许可](../LICENSE) 适用于原创代码和 Skills，第三方保留各自条款；用户决定自己项目是否公开。

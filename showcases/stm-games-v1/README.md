[English](README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md)

# STMGames V1: a real OLED game device

An STM32F103C8T6, a small OLED and five buttons became a handheld game device in a yellow printed case. This project grew through **many rounds of discussion, building and revision**; it was not made in one prompt or one pass. The maker supplied the ideas, physical work and **all 3D modeling**. As reported by the maker, **GPT-6.1 Sol completed the application code**. Third-party libraries and existing assets retain their own credits and licenses.

| Front | Inside |
| --- | --- |
| ![Yellow handheld case with OLED and five buttons](photos/front.jpg) | ![Opened case showing the STM32 board and two AA cells](photos/inside.jpg) |

These are maker-supplied photos of the real device. They show its appearance and assembly; they do not establish that every game works. Publishing copies have metadata removed; originals are unchanged. This historical project is an example of human and AI collaboration, not proof that this Skill generated the whole device or its enclosure automatically.

## Get the files

- [Complete firmware source ZIP](firmware-source.zip): one ten-game collection and nine standalone STM32CubeIDE projects, including Core, Drivers, Startup, IDE settings and linker/configuration files. Import the extracted project folders with your existing STM32CubeIDE tools. Build outputs are not included; tool versions may need adjustment. This export was not rebuilt or flashed.
- [Wiring image](wiring.svg) and [connection data](connections.json), with the matching table below.
- [Original OLEDGames.3mf](OLEDGames.3mf): the maker's model and slicer project, not native CAD or universal printer G-code. Open in a compatible slicer, check dimensions, orientation, materials and your printer settings, then slice for your printer. No new modeling or printing was done for this release.
- [Export inventory and SHA-256 hashes](export-manifest.json). The ZIP also contains `SOURCE_MANIFEST.sha256` for every exported source file.

The collection contains **Snake, Tetris, Space Invaders, Dino, 2048, Minesweeper, Breakout, Tower Defense, Stack and Timberman**. Nine standalone projects cover all except Tower Defense, which is included in the collection. All original firmware source required by the exported project configurations is included: 1,102 files, about 40.7 MB before compression. Local AI records, historical archives, build caches and duplicate backups are excluded. The original V1 directory is unchanged.

## Parts in this build

| Part | Quantity | Notes |
| --- | --- | --- |
| STM32F103C8T6 development board | 1 | Match the exact board and printed pin labels |
| 0.96-inch I2C SSD1306 OLED | 1 | Confirm this module's VCC requirements |
| 3 × 6 mm momentary switch | 5 | Up, down, left, right, confirm |
| AA cells | 2 | Actual supply and power path need verification |
| Maker-designed printed case | 1 assembly | Model supplied above; screws, wiring and battery contacts visible in photos have no confirmed sizes/counts |

## Wiring and power status

![Logical wiring with every signal labeled and unconfirmed power details marked](wiring.svg)

This is a logical diagram, not a view of physical pin positions. Read the board's printed pin names and the OLED's own labels. Firmware confirms the I2C pins and five internally pulled-up inputs. The button-to-ground connection follows that configuration; no continuity or voltage measurements were performed for this export.

| ID | From | To | Evidence |
| --- | --- | --- | --- |
| W1 | PB6 | OLED SCL | Firmware I2C1 SCL |
| W2 | PB7 | OLED SDA | Firmware I2C1 SDA |
| W3 | Board GND | OLED GND | Required common ground |
| W4 | PB10 | Up switch, first contact | Firmware input |
| W5 | PB11 | Down switch, first contact | Firmware input |
| W6 | PB12 | Left switch, first contact | Firmware input |
| W7 | PB13 | Right switch, first contact | Firmware input |
| W8 | PB14 | Confirm switch, first contact | Firmware input |
| W9 | Board GND | Other contact of each switch | Internal pull-up; pressed = low |
| P1 | Battery positive | Board **3.3V pin** | Maker reports this connection |
| P2 | Battery negative | Board **GND pin** | Maker reports this connection |
| Pending | OLED VCC | Supply not independently confirmed | Do not infer from photos |

The maker identified the board power connections as the same **3.3V and GND pins used during flashing**. That names the pins; it does not establish a regulated 3.3 V supply from two AA cells. Battery voltage, any switch/regulator, OLED VCC and power-source interaction remain unverified. This is a documented snapshot, not a complete approved power design: verify those details before reproducing or powering the build, and disconnect power before changing wires. The diagram deliberately leaves OLED VCC unconnected rather than guessing.

## Credits and verification limits

The repository's MIT license covers the original showcase material and application contributions, subject to third-party notices. The archive retains ST HAL/CMSIS licenses and the collection and standalone Dino `THIRD_PARTY_NOTICES.txt`, including Chromium sprite attribution. AI code attribution does not replace those rights.

This release checks export integrity, source/pin consistency, links and photo metadata. It does not newly compile every game, rerun historical game tests, simulate the complete device, verify its power circuit, flash hardware or print the case. Photographs and the maker's account are identified separately from fresh technical checks.

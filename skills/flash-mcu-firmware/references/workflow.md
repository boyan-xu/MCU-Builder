# Reusable flashing execution

The runner uses Python 3.10+ and its standard library plus the bundled `mcu_common.py`. Keep both scripts together. Tool lookup reuses explicit `tools` paths, the cache and installed software; it does not require the vendor executables on PATH. No physical connection is needed for a preview.

AI prepares configuration once, after reading the real project. Copy and adapt [the STM32 example](../assets/stm32-flash.example.json); do not treat its target, addresses, serial or memory layout as discovered facts. Configuration version is `1`; `project` is relative to the configuration file, and firmware paths are relative to that project. `tools` contains optional explicit executable paths. Never put secrets in configuration or commands.

```sh
python scripts/mcu_flash.py /path/to/project/mcu-flash.json
python scripts/mcu_flash.py /path/to/project/mcu-flash.json --execute --authorized
```

Use the installed Skill script's absolute path when invoking it outside its folder. `--cache-dir` overrides the normal user cache; `--output` chooses the result JSON, otherwise `.mcu-results/flash-result.json` is written under the project. Logs and bounded-range backups are kept beside the result. A fresh timestamp prevents replacing an earlier backup. Backups stay local; they may contain private firmware or data.

## Backends and project fields

All backends need `flash.backend`, a human-readable exact `flash.target` and a positive optional `flash.timeout` (seconds, default 120). The preview requires existing nonempty firmware files; build first with the existing engineering tools if these files do not yet exist. An optional top-level `build.command` argv array and `build.timeout` can rebuild before execution; preview only displays the build command. Arguments execute without a shell. Review the configuration and build command as project code before running them.

**STM32:** `backend: "stm32_programmer"` uses installed STM32CubeProgrammer CLI with SWD. Set `probe_serial`, expected numeric `device_id`, `firmware` BIN path, `address`, `flash_start`, `flash_size` in bytes and `erase_size` in bytes from the exact MCU documentation. `frequency_khz` defaults to 1000. Execution connects to that probe, checks the device ID, backs up the declared flash range, downloads and asks the tool to verify. `reset_after` defaults to false; set true only when starting the flashed firmware is in scope. `backup` defaults to true. OpenOCD, UART/DFU, external loaders, protection changes and mass erase are not implemented by this adapter; continue with an already suitable tool as a separately reviewed operation instead of disguising it as this backend.

**ESP:** `backend: "esptool"` needs an explicit `chip` such as `esp32` or `esp8266`, a local serial `port`, `flash_start`, `flash_size`, and `images: [{"address": "0x1000", "file": "build/bootloader.bin"}, ...]`. Use actual SDK offsets; the example offset is not universal. `baud` defaults to 115200. Set `expected_mac` when already known. `tools.esptool` points to an executable, or `tools.esptool_python` to an existing Python environment containing esptool. Execution detects esptool v4/v5 command spelling without hardware, reads the chip MAC, optionally compares it, backs up the configured flash range and runs write plus verification. Preview uses v5 spelling and marks version detection pending. Operations leave the chip in its loader unless `reset_after: true` explicitly requests startup after final verification. No forced protection bypass, mass erase or encryption/eFuse operations are supplied. A raw Arduino application upload can replace existing AT firmware; review that overwrite before execution.

STM32 and ESP validate writes and complete erase blocks against the declared flash range and `protected_ranges: [{"address": "0x0800F800", "size": 2048}, ...]`. Use real device erase geometry for STM32; ESP uses 4096-byte sectors. This protects explicitly recorded score journals/data; it cannot discover unrecorded state or prove addresses correct. A family device ID and chip option are not unique-device identity guarantees.

**Arduino:** `backend: "arduino_cli"` needs exact `fqbn`, local serial `port` and `firmware` BIN/HEX path. `verify` defaults to true and requests the installed platform's uploader verification; false reports upload only. This command does not compile or install cores. There is no portable backup or on-chip identity check in this adapter. `backup: true` is rejected; use an appropriate existing board tool first where preserving the current firmware is needed. The caller must review physical target, FQBN and port before execution.

## Interpret results

The JSON records the target, firmware SHA-256/size, resolved commands, affected ranges and executed-stage logs. `preview` means no vendor tool or build command ran. `verified` means the selected uploader/verification process exited successfully, not independent proof of device operation. `uploaded` is used for Arduino with verification disabled. Errors preserve completed-stage evidence; identify/backup failure prevents programming. No automatic blind retries are performed.

Official command references: [Espressif esptool commands](https://docs.espressif.com/projects/esptool/en/latest/esp32/esptool/basic-commands.html), [Arduino CLI upload](https://arduino.github.io/arduino-cli/1.5/commands/arduino-cli_upload/). For STM32, use the installed vendor CLI `--help` and the exact part's documentation. The shipped adapter was checked against STM32CubeProgrammer 2.23.0 help; that is not a physical flashing result.

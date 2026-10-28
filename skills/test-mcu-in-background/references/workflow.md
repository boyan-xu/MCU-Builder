# Executable background workflow

Requires Python 3.10 or newer. AI runs these commands and writes the configuration; users can paste code or name a project. Paths below are examples relative to this Skill, not instructions for users to edit JSON manually.

## Reusable runtime

```sh
python scripts/mcu_test.py --prepare
python scripts/mcu_test.py /path/to/project/mcu-test.json
python scripts/mcu_test.py /path/to/project/mcu-test.json --summary
```

`--prepare` first reuses compatible dependencies. If unavailable, it prepares a private cached Python environment with **unicorn 2.1.4** and **pyelftools 0.33** from the official Python Package Index. Explain the download before running it. Existing compatible module directories can be registered once with `--prepare --module-path /existing/site-packages`. Later invocations use the cached descriptor; they do not rebuild or download the environment. Missing or changed cached paths produce a clear preparation error. The ordinary `command` backend does not need ARM packages.

Tool discovery checks explicit `tools` paths, valid machine cache entries, PATH and common installed vendor locations. Cached paths remain local and are checked for staleness. Use explicit tools for unusual installs. Do not copy another person's private tool paths into a public config. `--cache-dir PATH` selects a local cache for isolation or validation.

## Existing project check

```json
{"version":1,"project":".","test":{"backend":"command","command":["tool:python","work/run_tests.py","--suite","Snake"],"inputs":["Core/Games/Snake/snake.c"],"timeout":120}}
```

`project` is relative to the config file's directory. `command` is an argument array with no shell expansion; `tool:NAME` is allowed only as the first argument, and `{project}` expands to the project path. Use the actual existing command and filenames, not this illustrative project. For an existing compiler/IDE build or ESP/Arduino test framework, this backend avoids replacing working tools. Review commands for hardware side effects. `inputs` lists the files whose hashes should accompany the result; it is evidence scope, not automatic dependency discovery.

## Isolated Cortex-M C checks

The [included example](../assets/example/project.json) exercises [game logic](../assets/example/logic.c) with [its assertions](../assets/example/test_logic.c). Copy the small example to a scratch project, then run its config. `arm-c` requires an installed `arm-none-eabi-gcc` toolchain; this Skill does not silently download a compiler.

A [recorded real background run](verified-run.json) binds the included source and historical runner hashes to successful ARM execution and framebuffer capture on its recorded date. It is not a fresh ARM pass of later runner edits. Repeated execution reused the same runtime descriptor without rewriting it; separate return-value and instruction-limit cases failed as expected. The flash result in this record is an offline preview only.

The runner supports explicit compiler targets `cortex-m0`, `cortex-m0plus`, `cortex-m3`, `cortex-m4` and `cortex-m7`, with soft-float Thumb code. This selects compilation, not a claim of exact cycle timing or complete core/peripheral coverage. The entry is `int test_main(void)` by default: zero passes; another value fails. Returning is required. Instruction and wall-clock bounds stop runaway tests.

Required fields: `test.backend="arm-c"`, `cpu`, `sources` (C source list), `harness`. Optional: `entry`, `include_dirs`, `compile_flags`, `build_timeout`, `timeout`, `instructions`, `memory` and `captures`. Header files in `include_dirs` are hashed with sources and the harness. Generated ELF, linker script, tested config digest, logs and result identify the run.

Default **synthetic** regions are flash at `0x08000000` (256 KiB) and RAM at `0x20000000` (64 KiB). They are test allocations, not an assertion about the physical board. Override with `memory.flash` / `memory.ram`, each containing `address` and `size` in bytes, aligned to 4096. The final page is reserved for the return sentinel or stack. No real registers, interrupts, timing model or peripherals are created automatically. HAL calls must use suitable project test substitutes; unmapped MMIO fails rather than pretending to be verified.

Captures read actual ELF symbols after execution. Each capture has `symbol`, `bytes` and a unique plain `.bin` `output` filename. For an SSD1306 page buffer, add `format="ssd1306"`, `width` and `height`; the runner emits both raw bytes and a PNG. This is a rendering of the tested buffer, not proof that a physical OLED works.

## Results

Optional `--summary` emits a compact current-invocation view with status, known config/input/build hash evidence, process counts, bounded error excerpt and exact full report/log paths. Counts describe recorded processes, not test cases or tests that never started. The full result and raw logs are preserved; a decisive compiler line may be outside the excerpt or tail, so retrieve targeted regions of the full log when needed. Summary-mode setup errors save a current error report when a safe output is writable, and otherwise give a null report rather than referencing an old pass. Default full output and exit codes are unchanged. `--prepare --summary` retains the already short readiness output; it does not run tests.

Each run stores logs/artifacts under the project's `.mcu-results/run-*` and a current `.mcu-results/test-result.json`. `--output PATH` changes the report location. Keep results local unless publication is requested. Exit 0 means the configured check passed, 1 means failure/timeout, and 2 means configuration, environment or input error. Failures do not become passes when a simulator or dependency is missing. The `command` backend reports that command's exit status; AI still explains what it actually checked.

Use the flashing Skill only under a separate hardware request/authorization. Running this software test Skill grants no permission to connect, reset, read or write a board.

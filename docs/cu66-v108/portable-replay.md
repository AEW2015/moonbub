# Portable source handoff

The study is a non-project Tcl flow. Its sources, compile/include order, part,
top, synthesis directive, implementation directives, defines and 10-ns XDC are
explicit. There is no XPR, generated IP/BD cache or board bitstream to export.
The original checkpoint is needed to replay the six checkpoint-matrix trials;
it is **not needed** for the fresh RTL exports below.

From this Git branch, prepare a new directory outside the source checkout:

```sh
python3 scripts/cu66-v108/export_replay.py --variant composite --dest /path/to/builds/v108-composite
python3 scripts/cu66-v108/export_replay.py --variant original --dest /path/to/builds/v108-original
```

Preparation copies all seventeen RTL files plus the quantization header and
the exact retained build/report Tcl and XDC. It preserves the original read
order. The new `inputs.tcl` resolves files relative to its build directory;
moving that directory does not require the original Linux host paths.
Each source and recipe is hash-checked against the selected preflight. An
existing destination is rejected. The helper does not launch Vivado or access
hardware, tools, license files or synthesis checkpoints.

Use Vivado **2026.1 build 6511674**, Artix-7 support, and a legitimate license.
Follow the generated README to run within the two-CPU/eight-GiB resource
allocation and 2,400-second watchdog. The RTL flow reads the 10-ns clock before
RuntimeOptimized synthesis and uses the selected ExtraNetDelay_high placement
with Default logical optimization and routing. Inspect complete final reports;
an export or successful tool exit is not a timing pass.

The [export check](../../experiments/python-gamebub-v108/portable-export/results.json)
prepared both variants, verified every exported source/recipe hash, and used
the real Tcl interpreter to check path/include resolution and the clock command.
That check uses stub clock commands and does not compile HDL or run Vivado.
The actual native study runs and their outcomes remain separate evidence.

An [isolated index check](../../experiments/python-gamebub-v108/portable-export/isolated-index-check.json)
also populated a minimal temporary tree from 32 staged Git files and exported
both variants from it. No original build directory, checkpoint, tools or license
was copied into that tree. This verifies source-handoff completeness; it remains
a preparation check, not a third native implementation run.

## Integration boundaries

Use each manifest's `source_origins` map. Source aliases retain older directory
names for compile compatibility; reading the old file with that name directly
would select the wrong implementation. The exporter places the selected bytes
under those aliases automatically.

The four capacity files must be carried together because they pass additional
internal packet-owned control metadata. The output-word mask replaces only
the IDCT body and preserves its public ports and all tested partial/invalid
outputs. All five actual source origins are listed in the composite manifest.
The 720×480 CS88 q16/all-BR88 representation and 49,152-byte packet cap stay
unchanged; these RTL changes require no new Sunshine or ESP32 wire format.

The production `moonshine_top` still contains the JPEG implementation. The
out-of-context decoder must still be integrated with actual transport, memory,
reference/publication, LCD and clock/reset/CDC interfaces. Board I/O timing is
open. Sustained hardware 30 fps and validated complete decoding below 10 ms
remain open. This handoff supplies verified RTL and implementation evidence,
with failed timing observations retained; it does not supply a flashable
Game Bub image.

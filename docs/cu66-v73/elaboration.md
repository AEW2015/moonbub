# V73 frontend, memory-port and unplaced family mapping

The native Yosys 0.33 frontend could not parse the qualified V72 `int'(...)`
casts. V73 keeps the native SystemVerilog intact and uses the existing pinned
[sv2v v0.0.13 release](https://github.com/zachjs/sv2v/releases/tag/v0.0.13) to
produce separate Verilog artifacts. sv2v describes its purpose as synthesizable
SystemVerilog-to-Verilog conversion in its [official project documentation](https://github.com/zachjs/sv2v).

| Tool input | Recorded identity |
| --- | --- |
| sv2v executable | `sv2v v0.0.13` |
| Executable SHA-256 | `b80a8ac6212aa72a196d9d6129cda35f16dbfa799ec61848c46321f845b6b635` |
| Official Linux ZIP SHA-256 | `552799a1d76cd177b9b4cc63a3e77823a3d2a6eb4ec006569288abeff28e1ff8` |
| Yosys | 0.33, git `2584903a060` |
| Native and converted simulation | Verilator 5.020 |

This is an explicit frontend addition, not a claim that native Yosys now accepts
the original SystemVerilog. The executable already exists in the shared tools
volume at `/build/v72-tools/sv2v`; its version and SHA are verified before use.
Set `SV2V_PATH` to another container path if needed; the same pinned executable
hash remains mandatory. Generated files are confined to V73's `memory/elaboration/` directory.

## Logical structure after process and memory optimization

```sh
python3 scripts/cu66-v73/run_elaboration.py
```

Both frozen V72 and banked V73 pass the sv2v → Yosys flow:

```text
read_verilog <generated-Verilog>
hierarchy -check -top <painter>
proc
opt
memory_dff
memory_share
opt
memory_collect
check -assert
stat -json
write_json
```

`memory_dff` absorbs the existing registered read payload; `memory_share`
consolidates mutually exclusive producer write sites. The resulting logical
strip memories are:

| Version | Logical strip memories | Read ports | Write ports | Read clock |
| --- | --- | --- | --- | --- |
| V72 | One 5,760×16 store | Eight | One | All eight synchronous |
| V73 | Eight 720×16 stores | One per bank | One per bank | Each synchronous |

Both hold exactly 92,160 declared data bits. Other Y/chroma/HUD caches retain
their own structures. These are post-pass logical-port results, not inferred
FPGA BRAM counts.

## Unplaced 7-series family mapping

Both generated painters also pass bounded `synth_xilinx -family xc7 -noiopad
-noclkbuf`, followed by `check -assert`. This flow maps to family primitives
without a fitted part, placement, routing, pads or board clock constraints.
Each measured mapping finished in about 15 seconds; the runner bounds each tool
invocation to 120 seconds in the existing 4-CPU/4-GiB container.

| Mapped family primitive count | V72 | V73 |
| --- | ---: | ---: |
| Strip store RAMB36E1 | 24 | 0 |
| Strip store RAMB18E1 | 0 | 8 |
| Strip allocation in 18K equivalents | 48 | 8 |
| Other RAMB18E1 (Y row) | 1 | 1 |
| Whole painter DSP48E1 | 11 | 11 |
| Whole painter FDRE | 791 | 901 |
| Whole painter mapped cells | 3,554 | 3,655 |

The V72 strip is replicated into eight depth groups, each containing three
RAMB36E1 cells. V73 has exactly `strip0.0.0` through `strip7.0.0`, each a
RAMB18E1. Thus **the strip's allocated 18K-equivalent blocks fall 48→8 (83.33%)
in this unplaced family flow**, while logical capacity and output remain equal.
This is not a device-fit percentage or a routed speed result. Other distributed
RAM/LUT/control costs remain in the complete machine-readable statistics.

The 11 DSP48E1 cells are the painter mapping, not decoder DSP utilization. No
new arithmetic acceleration or DSP throughput improvement is claimed here.

## Frontend validation and lint scope

The generated V73 Verilog passes the same three-schedule native-oracle bench:
39 raster executions / 14,976,000 exact RGB565 word comparisons, ten fault/abort
probes and thirty rejected starts. Per-case cycle and transaction counts agree
with the native V73 SystemVerilog results. This finite simulation validates the
exercised lowering path; it is not formal equivalence or mapped-netlist timing
simulation.

The first converted-source build retained strict lint failure in
`converted-build-first-width.log`: sv2v emits sized-cast helper functions whose
arguments use legal implicit expansion/truncation, plus a missing final newline.
Only the converted-source build disables `WIDTHEXPAND`, `WIDTHTRUNC` and
`EOFNEWLINE`; native SV builds retain full `--Wall`. The source files are not
rewritten to silence diagnostics. The [Verilator warning documentation](https://verilator.org/guide/latest/warnings.html)
describes these warning classes and scoped suppression options.

`memory/elaboration/results.json` records exact commands, source and derived
output hashes, tool identity, generic memory ports, converted simulations and
both family mappings. Logs, generated Verilog, `.ys`, statistics and netlists
are retained for review. The main native SV outputs remain authoritative.

Exact `xc7a100tcsg324-1` implementation, achieved Fmax, BRAM/DSP placement,
external SDRAM timing, CDC, physical sustained 30 fps and target validated
decoding under 10 ms remain separate gates.

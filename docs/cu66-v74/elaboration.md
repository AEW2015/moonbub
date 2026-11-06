# V74 painter generic memory and exact-part preflight

Run `python3 scripts/cu66-v74/run_elaboration.py` after the native painter regression. It pins the painter, native oracle/fixtures, result files, runner and predecessor mapping evidence. The RTL uses the pinned sv2v 0.0.13 frontend and Yosys 0.33 in the shared build container; every compiler invocation uses `-j 1`. Results and command/log hashes are in `fpga/experiments/cu66-v74/memory/elaboration/results.json`.

The frontend executable SHA-256 is `b80a8ac6212aa72a196d9d6129cda35f16dbfa799ec61848c46321f845b6b635`. The generated Verilog is retained unchanged. Converted Verilator simulation allows the existing sv2v width-helper and terminal-newline lint exceptions. A precise `converted-only.vlt` waiver restores the narrow unused `aux_rsp_data` compatibility-port annotation stripped by conversion. Native SystemVerilog still builds with full `--Wall`. The first converted build's unused-port failure remains in `converted-build-attempt1.log`.

## Generic structure and converted simulation

Yosys generic processing, memory collection and `check -assert` complete with zero reported problems. The 33 data memories contain 184,448 bits (23,056 bytes):

| Banks | Count | Words per bank | Word bits | Collected read ports | Collected write ports |
|---|---:|---:|---:|---:|---:|
| Y stripe | 8 | 360 | 16 | 1 | 1 |
| Cb/Cr ring | 16 | 180 | 16 | 2 | 1 |
| Portrait strip | 8 | 720 | 16 | 1 | 1 |
| HUD cache | 1 | 8 | 16 | 1 | 1 |

There is also a two-entry, six-bit quad-tag control memory, separate from the data footprint. Generic inspection absorbs the read registers for the Y and portrait banks and one of each chroma bank's read ports. HUD reads remain combinational. These port descriptions precede technology mapping; they do not promise a particular FPGA primitive.

The converted Verilog passes the same three native-oracle schedules: **39 full rasters, 14,976,000 compared RGB words, 16 fault probes and 30 invalid starts**. Every case's cycle count, read/write count and result agrees exactly with the native SystemVerilog run. This is finite functional validation of the translated RTL, not formal equivalence or mapped-netlist simulation.

## Bounded unplaced XC7 mapping

The runner executes `synth_xilinx -family xc7 -noiopad -noclkbuf`, followed by `check -assert`, with a 120-second watchdog. The run completed and reported zero problems. No exact part, pinout or clock constraints are supplied to this generic family map.

| Primitive/statistic | V73 frozen evidence | V74 |
|---|---:|---:|
| DSP48E1 | 11 | 11 |
| RAMB18E1 | 9 | 8 |
| RAMB36E1 | 0 | 0 |
| RAM64M | 384 | 2,304 |
| RAM32M | 3 | 3 |
| FDRE | 901 | 1,059 |
| Total cells | 3,655 | 7,050 |

The eight portrait strip banks retain eight RAMB18E1 primitives. V74 input caches currently map to distributed RAM and incur a substantial LUT-memory tradeoff for lower memory-command traffic. A RAM64M is not equivalent to one LUT; total cell counts must not be interpreted as device utilization or fit. The larger cache is not yet physically qualified.

A useful next implementation experiment is to register complete 16-bit input-bank words before byte selection and compare the resulting BRAM/LUT mapping, read-port replication, timing and any added painter cycles against this frozen functional baseline. Any such change needs the exact raster/fault regression again. Do not replace present primitive counts with estimated BRAM counts.

## Exact-target OOC availability

`fpga/experiments/cu66-v74/build/ooc_system.tcl` stages the 20 hardware-only sources from the V74 system manifest, omitting simulation wrappers/models and the retired scalar painter. It retains the exact target `xc7a100tcsg324-1`, `USE_STRIP=1`, `P0_CACHE_LINES=8`, and 34.058-ns panel clock assumption from the predecessor flow.

The Vivado 2025.2 container preflight ran and exited **2: `UNAVAILABLE_EXACT_PART`**. Its status, exact command, source/header/tool hashes and retained logs are recorded in `build/status.json`. It checked source availability and stopped before reading RTL or starting synthesis/implementation. No exact-target utilization, placement, routing, Fmax or CDC result was produced.

The generic mapping, converted simulation and exact-target availability check are distinct results. None establishes hardware 30 fps, sub-10-ms decoding, board electrical timing, SDRAM operation or safe clock-domain crossings. Actual-command system replay and target implementation remain necessary.

# V75 frontend validation and BRAM-friendly input reads

The V75 painter uses the same pinned frontend and bounded unplaced family
mapping flow as V74. Native and converted RTL each pass 39 exact rasters,
14,976,000 RGB565 word comparisons, 20 fault probes and 30 rejected starts.
All converted per-case cycles, read/write counts and outcomes match native SV.
The new input read structure removes the V74 distributed input RAM in this
family map, at the cost of more block RAM and one extra clock per active pixel.

## Reproduction and provenance

```sh
python3 scripts/cu66-v75/run_painter.py
python3 scripts/cu66-v75/run_elaboration.py
```

The shared `gamebub-cu66-v69-build` container provides Verilator 5.020,
Yosys 0.33 and the pinned `/build/v72-tools/sv2v`. Set `SV2V_PATH` if the same
binary is supplied at another container path. Builds use `-j 1` and the
`/build/v75-*` directories. Every command has a timeout and a retained log;
simulation requires terminal PASS and the expected assertions/counters.

The frontend is **sv2v v0.0.13**, binary SHA-256
`b80a8ac6212aa72a196d9d6129cda35f16dbfa799ec61848c46321f845b6b635`.
The official release archive SHA-256 is
`552799a1d76cd177b9b4cc63a3e77823a3d2a6eb4ec006569288abeff28e1ff8`.
It converts a separate generated Verilog file; the qualified SystemVerilog
source is not changed to accommodate the older Yosys frontend. Tool version
and binary SHA transcripts, producer/source hashes, derived file hashes and
command-log hashes are recorded in
`fpga/experiments/cu66-v75/memory/elaboration/results.json`.

Native simulation retains full `--Wall`. Generated Verilog alone has the
preserved scoped exceptions for `WIDTHEXPAND`, `WIDTHTRUNC` and `EOFNEWLINE`
from frontend casts/newline handling, and a precise `UNUSEDSIGNAL` exception
for the unused scalar compatibility response `aux_rsp_data`. These exceptions
do not suppress native RTL diagnostics.

## Generic memory structure

The generic flow runs `proc`, `opt`, `memory_dff`, `memory_share`,
`memory_collect` and `check -assert`. It reports zero problems. Its 33 data
memories contain **184,448 bits = 23,056 bytes**, unchanged from V74. The two
six-bit quad tags are separate control metadata.

| Banks | Count | Words per bank | Word bits | Read ports per bank | Write ports per bank |
|---|---:|---:|---:|---:|---:|
| Y stripe | 8 | 360 | 16 | 1, synchronous | 1 |
| Cb/Cr ring | 16 | 180 | 16 | 1, synchronous | 1 |
| Portrait strip | 8 | 720 | 16 | 1, synchronous | 1 |
| HUD cache | 1 | 8 | 16 | 1, combinational | 1 |

The producer asserts that all 24 input banks have full 16-bit words, exactly
one clocked read port and one write port. V74 chroma banks had two read ports,
only one of which was absorbed into a synchronous memory output register.
The V75 clocked outputs are selected by bank and byte lane after the RAM
registers; left and right chroma word requests are serialized across two
clocks. [Painter details](display.md) describe its fixed pixel schedule.

## Bounded unplaced XC7 mapping

The mapping command is `synth_xilinx -family xc7 -noiopad -noclkbuf`, followed
by `check -assert`, with a 120-second watchdog. It completed with zero reported
problems. It has no exact part, pinout or clock constraints.

| Primitive/statistic | Frozen V74 | V75 |
|---|---:|---:|
| DSP48E1 | 11 | 11 |
| RAMB18E1 | 8 | **32** |
| RAMB36E1 | 0 | 0 |
| RAM64M | 2,304 | **0** |
| RAM32M | 3 | 3 |
| FDRE | 1,059 | 1,018 |
| Total cells | 7,050 | 3,896 |

The eight portrait strip banks retain eight RAMB18E1 cells; each of the 24
input banks now maps to one RAMB18E1. The small HUD/control memories retain
three RAM32M cells. Eliminating 2,304 RAM64M cells is a measured mapping result,
not a claim of 2,304 fewer LUTs: a RAM64M is not one LUT. The total-cell sum is
not an area or utilization percentage. The increase from eight to 32 block-RAM
cells is the explicit resource tradeoff; capacity and full-system fit still
need exact-device implementation.

The no-stall painter adds exactly 345,600 cycles per frame, from 1,212,249
to 1,557,849. This finite bench runs ideal BL8 service and does not measure
physical SDRAM/LCD contention. More clocked ports do not prove a higher routed
clock; no Fmax claim follows from the mapping.

Generic memory collection, converted RTL simulation and unplaced primitive
mapping are different results. Converted simulation is finite behavioral
validation, not formal equivalence, mapped-netlist simulation or post-route
timing simulation. No exact-device placement/routing/CDC or physical SDRAM
qualification is included here. The staged full-system exact-part preflight,
if available, is reported separately by the iteration handoff. Neither 30 fps
nor maximum validated decoding below 10 ms is closed by this evidence.

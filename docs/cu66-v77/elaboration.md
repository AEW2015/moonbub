# V77 frontend, synchronous memory inspection and unplaced mapping

```sh
python3 scripts/cu66-v77/run_elaboration.py
```

The flow pins sv2v **v0.0.13**, binary SHA-256
`b80a8ac6212aa72a196d9d6129cda35f16dbfa799ec61848c46321f845b6b635`, and records
its version/hash logs and the actual Yosys version. It lowers the cache,
converter and wrapper together to a generated Verilog file, leaving the native
SystemVerilog untouched.

## Generic structure

After `proc`, `opt`, `memory_dff`, `memory_share`, `memory_collect` and
`check -assert`, the flow asserts the exact ten data memories and their ports:

| Data memories | Count | Words per memory | Word width |
|---|---:|---:|---:|
| Y columns | 1 | 5,760 | 16 bits |
| HUD block columns | 1 | 3,072 | 16 bits |
| Cb/Cr row-parity × word-parity banks | 8 | 720 | 16 bits |

All ten have **one clocked read port and one write port**. Their data footprint
is **233,472 bits / 29,184 bytes**, excluding tags, pixel/memory pipeline state
and implementation padding. Full words are registered before dynamic byte
selection. The generic netlist/statistics and generated source are hash-pinned
separately from the native source inputs.

## Converted functional replay

Generated Verilog passes the same three integrated native-oracle schedules:
**39 active frames, 13,478,400 compared RGB565 words and four integration fault
probes**. Every case's cycle, read/word count, output count and generation/bank
identity match native SystemVerilog exactly. This is finite frontend validation,
not formal equivalence or mapped-netlist/timing simulation.

Native builds retain full `--Wall`. Converted-only exceptions are
`WIDTHEXPAND`, `WIDTHTRUNC`, `EOFNEWLINE` for generated cast helpers/formatting,
and `DECLFILENAME` because sv2v concatenates multiple modules into the top-named
file. The initial generated-filename diagnostic is retained. No RTL repair was
made solely to satisfy an older synthesis parser.

## Bounded XC7 family mapping

The bounded 120-second flow uses `synth_xilinx -family xc7 -noiopad -noclkbuf`
and `check -assert`. It completed with zero reported problems. It supplies no
exact device, package, pinout, clock constraint, placement or routing.

| Combined cache + converter + wrapper | Unplaced count |
|---|---:|
| DSP48E1 | 8 |
| RAMB18E1 | 11 |
| RAMB36E1 | 3 |
| BRAM allocation in 18K equivalents | 17 |
| FDRE | 664 |
| CARRY4 | 4,137 |
| Total mapped cells | 29,462 |

The converter alone has 374 cells and four DSP48E1. The cache contains 29,070
cells, including 4,087 CARRY4 and four DSP48E1; the wrapper adds a small pixel
ownership counter. The substantial address/control logic is a material
prototype cost. Wide integer signed divisions/modulo-three and dynamic address
expressions are candidates for bounded-width arithmetic and explicit slot-ring
optimization. Requalify exact source/trace/pixel behavior and remap any such
change; do not substitute estimated cell counts for this measured result.

Memory data now maps to BRAM, but this does not establish whole-system fit,
utilization percentages, timing or Fmax. The converter/cache counts also do not
describe the compressed-video decoder or a complete physical display system.
No mapped-netlist or post-route functional/timing replay was performed.

`elaboration/results.json` retains source/log hashes, four generic derived-file
hashes, three family-map derived-file hashes, memory inventory, converted cases
and explicit scope. The frozen exact-part limitation remains outside this
unplaced flow; no new implementation bitstream, physical 30 fps or target
under-10-ms validated-decode verdict is produced here.

## Separate bounded-address mapping

The initial family map identified wide signed integer modulo-three/address
logic as a concrete implementation cost. The separate cache variant replaces
wide `%3` operations with a bounded seven-bit base-four-digit fold and reduces
the target-column expression width. Its helper is exhaustively checked over
all 128 inputs in the cache regression. The baseline cache/module/evidence is
left unchanged.

The bounded native and converted render campaigns each pass 39 active frames,
13,478,400 words and four faults. All case counters and cycles equal the
baseline, and the generic ten-memory/29,184-byte/clocked-port contract remains
unchanged. The separate bounded family flow uses the same pinned frontend and
bounded synthesis commands.

| Cache + converter + minimal render guard | Baseline | Bounded address |
|---|---:|---:|
| Total mapped cells | 29,462 | **2,970** |
| CARRY4 | 4,137 | **271** |
| DSP48E1 | 8 | **7** |
| FDRE | 664 | 664 |
| RAMB18E1 | 11 | 11 |
| RAMB36E1 | 3 | 3 |
| BRAM allocation, 18K equivalents | 17 | 17 |

The total mapped-cell reduction is **89.91922%** in this unplaced family flow.
The bounded cache alone has 2,578 cells; the unchanged converter has 374 cells
and four DSP48E1. The remainder is the minimal render guard and hierarchy.
These counts **exclude the frozen SDRAM controller, LCD line buffers, root
address adapter and compressed-video decoder**. They are not whole-system LUT
utilization, exact-device fit, routed Fmax or CDC signoff.

`run_elaboration_bounded.py` retains its own native inputs, generated source,
generic/family derived hashes, logs and converted case results.
`elaboration-bounded/compare_mapping.py` checks both native/converted case
parity and the actual two mapping records, then pins its inputs in
`comparison.json`. The result does not establish mapped-netlist equivalence,
physical 30 fps or strict maximum validated decoding under 10 ms.

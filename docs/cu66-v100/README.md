# V100: reproducible component baseline and synthesis readiness

V100 establishes a source-frozen baseline, executes the fresh V99 RTL vectors,
and verifies a standard source conversion for Series-7 technology mapping.
**The physical baseline is partial:** exact-target placement/routing and the
complete custom-decoder integration are not qualified. Sustained hardware
30 fps and validated complete FPGA decoding below 10 ms remain open.

The research profile stays CS88/all-BR88 q16, 720×480 with a 49,152-byte complete
packet cap. Existing production JPEG/MSV1 remains the deployment fallback.
No codec syntax, active firmware or hardware was changed in this iteration.

## Measured results

| Evidence | Result | Boundary |
| --- | --- | --- |
| Fresh V99 key/P/late-CRC vectors through unchanged V91j RTL | Two seeds, 12 case/profile runs, 26 directed checks; 4,579,072 exact comparisons at each of four transform stages | Component coefficient/dequant/residual evidence; rejected prefix is provisional |
| Original versus standard-converted V91k | 88 pipeline case/profile runs and 84 directed checks; identical same-seed transcripts, cycle counters, events and canonical SRAM bytes | Bounded behavioral regression; not formal equivalence or mapped-netlist simulation |
| Separate RGB565 replay of canonical SRAM | 24 case/profile runs, 16 directed checks; 4,147,200 exact pixels per seed | Separate component; not simultaneous full-system display service |
| Public converted interface | All 308 ordered port names, directions and widths checked; nine array outputs restored with wires only | Diagnostics retained; no reduced production-interface resource claim |
| Unchanged reconstruction leaf, two cold generic xc7 mappings | 2,202 LUT2–6, 546 FDRE, 704 CARRY4; identical mapped-netlist hashes | Leaf resource evidence only; see arithmetic mapping updates in the physical report |
| Dequantizer, two corrected post-DSP checkpoints | 15 DSP48E1 cells; identical full intermediate checkpoint hashes and all 14 ports retained | Intermediate inference only; final leaf mapping exceeds the configured address-space limit |
| IDCT, one corrected post-DSP checkpoint | 21 DSP48E1 cells: eight product lanes and 13 address/index cells; all 13 ports retained | No repeated IDCT checkpoint or complete leaf mapping; later optimization may remove cells |
| Exact Vivado 2025.2 target queries | Two frozen cold attempts find zero `xc7a100tcsg324-1` and zero `xc7*` parts | Synthesis, placement and routing did not start |
| Additional Vivado 2026.1 installation probe | Two launches fail during startup before Tcl execution | Part support remains unknown there; no target substitution |

[RTL results](rtl-results.md) contain exact fixtures, counters, warning policy,
watchdogs and immutable attempt pointers. [Physical results](physical-baseline.md)
contain selected technology-mapping outcomes, failed compatibility probes,
primitive counts, memory declarations and the exact-part limitations. Read the
selected receipts rather than treating every retained exploratory attempt as a
successful baseline.

The fresh key requires 1,386,271 cycles even in the unstalled component profile;
the P frame requires 850,193 plus 1,350 preload cycles. At the **comparison**
100-MHz target, a 10-ms budget is 1,000,000 cycles: the key already exceeds that
budget before missing stages are charged. No achieved FPGA clock, whole-frame
latency or hardware frame rate follows from these counters.

## Hardware implementation handoff

The selected top is `cs88_pipeline_v91k`, a packet-to-canonical component.
[Integration gaps](integration-gaps.md) distinguish real RTL from testbench
services. The HUD, C2/seal/publication, shared external-memory/display service,
transport and CDC endpoints still need a complete candidate top. The frozen
part is source-backed `xc7a100tcsg324-1`; physical board identity and board
interface timing require confirmation before signoff.

[Frozen inputs](../../fpga/experiments/cu66-v100-baseline/frozen-inputs.json)
bind unchanged V99 RTL, includes, policy, runner and the 10-ns OOC clock XDC.
External handshake timing is explicitly unqualified; the recipe invents no
I/O delays or blanket false paths. It exports checkpoints, hierarchical
resources, DSP instances, timing, unconstrained paths, methodology and DRC when
the exact part is available. It generates no bitstream and programs no board.

The first follow-up is to restore a usable exact-part Vivado installation,
repeat the frozen component baseline, and inspect the actual memory/primitive
inference before optimization. [Next RTL experiments](next-rtl-experiments.md)
separate synthesis compatibility from measured DSP, memory and cycle work.
Keep V101 changes in a new candidate with the current baseline as its control.
Do not advance a V100 physical-completion gate based on successful leaf mapping.

## Reproduce and audit

The configured build container supplies GCC 13.3, Verilator 5.020 and Yosys
0.33. The separate Vivado container supplies 2025.2 but currently lacks Artix-7
support. Standard conversion uses official sv2v 0.0.13; its external download
and binary hashes are retained in the preflight receipt. Source-conversion
warnings and synthesis-guarded assertion exclusions are explicit in the RTL
report. Original RTL and the unchanged C++ checkers remain strict.

```sh
python3 scripts/cu66-v100/inventory.py
python3 scripts/cu66-v100/physical.py --verify
python3 scripts/cu66-v100/audit.py
python3 scripts/cu66-v100/bundle_manifest.py --verify
```

The inventory/auditor use Python's standard library. Full simulation and
mapping commands, fresh-directory rules and external tool paths are documented
in the linked reports and each runner's `--help`. Run heavyweight jobs only
with at least 8 GiB available RAM and memory PSI full avg10 below 1; keep at
most two heavy jobs on the host and one large mapping in the shared 4-GiB build
container. Swap occupancy alone is not the gate. External build trees and
binaries are excluded from the handoff; hash-bound reports and source snapshots
are retained.

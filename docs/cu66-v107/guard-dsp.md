# V107 local control multiplier DSP experiment

The original TABLES decoder has an actual routed timing violation through a constant ×43 control multiplier. This isolated candidate directs only its two source expressions into slice logic with signal-level `USE_DSP=no`. Complete production controller canonical verification and new mapped/routed timing are separate parent qualifications. This unit evidence does **not** claim the new full controllers have been simulated, that the attribute removed a physical DSP, or that parent timing now closes.

## Actual failing cone

The source-bound TABLES run is `v107-tables-20261108T052651767313Z-4d6323`, parent receipt `experiments/python-gamebub-v107/native/20261108T052651848340Z/receipt.json`. Its placed worst path was `coefficients/child/scratch/error4/CLK` → `scratch/cursors_reg[1][2]/CE`: slack **−2.639 ns**, data **12.350 ns**, 11 logic levels; DSP clock-to-`P[3]` alone was 4.009 ns. The cell name `error4` is an arithmetic DSP, not an error-status register.

The portable [attribution receipt](../../experiments/python-gamebub-v107/guard-dsp/attribution/receipt.json) records a read-only extraction from the existing synthesis checkpoint's zstd-compressed EDIF. The exact `error4` DSP has AREG=1, BREG=0, MREG=0, PREG=0. Its 18-bit B input has ones only at bits 0,1,3,5: **43**. A has 17 variable bits and 13 grounded upper bits. Its output `P[3]` drives the comparator/control logic named in the actual timing path. The frozen scratch source's line 429 is `begin_count3>32'(begin_blocks)*43`; the complete source and checkpoint hashes are bound in the receipt. Retained instance properties and net bindings allow this attribution to be reviewed without Vivado.

The original TABLES route's worst path moved elsewhere, so placement alone was insufficient to justify another trial. A separate [read-only routed probe](../../experiments/python-gamebub-v107/guard-dsp/route-probe/20261108T054532399736Z/receipt.json) explicitly queries `-from coefficients/child/scratch/error4/CLK`, requires the exact DSP/CLK objects and existing 10 ns `component_clk`, and reports five paths. It adds no constraints, clocks, exceptions, or RTL changes. The checkpoint was mounted read-only and its before/after SHA-256 matches.

| Actual original routed endpoint | Slack (ns) | Data (ns) | Logic levels |
|---|---:|---:|---:|
| scratch/cursors_reg[2][16]/CE | −2.497 | 12.208 | 11 |
| scratch/cursors_reg[2][19]/CE | −2.497 | 12.208 | 11 |
| scratch/cursors_reg[2][25]/CE | −2.497 | 12.208 | 11 |
| scratch/cursors_reg[2][26]/CE | −2.497 | 12.208 | 11 |
| scratch/tile_emit_index_reg[0]/D | −2.386 | 12.271 | 11 |

The first path comprises 5.769 ns logic and 6.439 ns route. This establishes a failing routed control cone even though it is absent from the top 50 paths of the unconstrained endpoint selection. The probe retains the OOC missing `HD.CLK_SRC` warning; no board clock-source location is guessed.

## Exact candidate scope

The [two-file edit recipe](../../fpga/experiments/cu66-v107-guard-dsp/edit-recipe.json) is reversible and keeps all state, reset, priority, operands, arithmetic operators, capacities, and complete 32-bit comparisons unchanged. Each file adds one named combinational **32-bit** result with `(* use_dsp = "no" *)`, assigns it the original multiplication expression verbatim, and replaces only that original expression's use with the wire name.

| Production candidate | Frozen source SHA-256 | Candidate SHA-256 |
|---|---|---|
| [`packed_scratch_v91g2.sv`](../../fpga/experiments/cu66-v107-guard-dsp/packed_scratch_v91g2.sv) | `0ee1196e2f0cafdf52742656d4c1a53604c79544c339b171989ad2785f051f8c` | `2a468e5566d7b24fb68f663fbffa3989f8f56c9da85cc2b42880e30ccbd2c090` |
| [`br88_packet_ingress_sync_v91h.sv`](../../fpga/experiments/cu66-v107-guard-dsp/br88_packet_ingress_sync_v91h.sv) | `4342972a6cf42cebf4f01a82841c0bc7c1850292ca23362817f7f071af126093` | `feeae3ffff6a8da705806ac7785a1f8da68c3c2599101f40da191f4185b53cf1` |

Scratch's new `begin_limit43` replaces only the band-3 count limit; ingress's `context_limit43` replaces only the descriptor band-3 limit. In the actual source connection, ingress `meta_blocks` is `context_blocks`, and `br88_pipeline_v91h` connects `meta_blocks` to scratch `begin_blocks`. The existing mapped DSP and comparator logic are shared across this hierarchy. Annotating both corresponding source products avoids leaving an unannotated equivalent ×43 expression available for shared inference. No module-wide DSP restriction is used: ×5, ×15, and all IDCT/dequant products are outside these edits.

[AMD UG901 2026.1](https://docs.amd.com/r/en-US/ug901-vivado-synthesis/USE_DSP) documents `USE_DSP=no` on signals and gives signal attributes priority over module attributes. Actual candidate mapping still needs inspection; an RTL attribute alone is not physical proof or a performance result.

## Measured expression proof

[`results.json`](../../experiments/python-gamebub-v107/guard-dsp/results.json) is `PASS`, `actual_RTL_run: true`, for an explicitly scoped **standalone extracted-expression unit**. Its candidate declarations and assignments are copied byte-for-byte from the two complete production files. Original expressions are copied from their frozen recipe; both original/candidate products and strict full-width count comparisons run in actual Verilator 5.020 RTL simulation. Compilation uses `--assert -Wall` and C++ `-Wall -Wextra -Werror`, without warning suppression.

Both 17-bit operand domains are exhaustive: 131,072 values each, pairing scratch `n` with ingress `131071−n`. For each value there are nine count cases: zero, product−1 modulo 32 bits, product, product+1, `0x7fffffff`, `0x80000000`, `0xfffffffe`, `0xffffffff`, and a seeded random 32-bit value. Actual simulation passes **1,179,648 rows**, covering 2,359,296 product comparisons and their corresponding original/candidate rejection checks. Zero's product−1 deliberately probes `0xffffffff`; counts never narrow to product width.

A separate Python finite-domain model checks `43*x == (x<<5)+(x<<3)+(x<<1)+x`, with maximum product **5,636,053**, and the same boundary classes. No source expression is replaced by this shift/add identity. The [portable audit](../../experiments/python-gamebub-v107/guard-dsp/audit.json) independently replays every retained compressed CSV row, verifies every operand occurs nine times, validates full 32-bit strict comparisons, reconstructs and reverses both complete source recipes, checks exact extracted SV lines and all snapshot hashes, and binds the original routed failure and DSP evidence.

The unit does not exercise full-controller guard order, packet reachability, arbitrary internal state, memory behavior, reset priority, or four-state startup. Their RTL bodies are preserved exactly around the aliases; the parent complete canonical run must establish actual controller equivalence before any full native trial. The isolated proof does not claim that IDCT/dequant DSP counts remain unchanged after full synthesis; their source bytes are untouched, and actual mapping is a later check.

## Reproduction

```sh
python3 scripts/cu66-v107/guard_dsp.py --prepare-only
python3 scripts/cu66-v107/guard_dsp.py
python3 scripts/cu66-v107/guard_dsp/route_probe.py
python3 scripts/cu66-v107/guard_dsp/audit.py
```

The expression compile and Vivado probe require a scheduled heavy-job slot and run sequentially. The probe uses the existing readonly Vivado tools/license, 8 GiB / two CPU limits, a 300 s cap, and live host available-memory/PSI checks. The finite model and portable audit are lightweight. `attribution.py` additionally reproduces the read-only EDIF extraction when the original external checkpoint is present; retained evidence suffices for the portable audit.

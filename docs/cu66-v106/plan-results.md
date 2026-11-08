# V106 same-cycle scratch-plan prefix candidate

The initial V106 LUT **synthesis** report moves the worst reported path to packed-scratch allocation validation. A separate CSA candidate now calculates each plan prefix independently while retaining exact 32-bit modular arithmetic, all validation guards, the same-cycle begin handshake, and every state update. Python/model and strict focused complete-module RTL checks pass. Native timing remains pending in the separate root workflow.

## Measured new cone

External synthesized setup report:
`/home/lori/gamebub-build/cu66-v69/v106-lut-20261108T005012118812Z-20b3b2/results/synth-setup-paths.rpt`.
SHA-256: `6c732f65f791f71c6ef395609d3c4c5452cc2c8c21b224292da4a2c68f4985f8`.

| Synthesized estimate | Value |
| --- | --- |
| Setup slack | −5.303 ns |
| Launch | `coefficients/child/packet_decoder/synchronous.ingress/context_blocks_reg[4]/C` |
| Capture | `coefficients/child/scratch/written_reg[10]/R` |
| Data delay | 14.695 ns |
| Logic / unplaced interconnect estimate | 7.263 / 7.432 ns |
| Levels / CARRY4 | 20 / 10 |
| Top-50 path class | 50 context-block launch paths; 31 written resets, 19 assembler resets |

This report explicitly says **Synthesized** and marks data-net delays unplaced. It is not routed timing, achieved frequency or timing closure. Its summary reports 6,287 setup-failing endpoints, WNS −5.303 ns, WHS +0.196 ns and WPWS +3.750 ns. The 10 ns clock remains unchanged. Comparing these numbers directly with another variant's routed results would mix implementation stages.

The first path passes through aligned plan terms, successive `starts[1]`, `starts[2]`, `starts[3]`/cursor arithmetic, scratch validation/error control, and reset/clear logic for `written` and `assembler`. The snapshots match original sources:

- `br88_packet_ingress_sync_v91h.sv`: SHA `771447e0f7516448f47ea1e47f56474e424662a8bbe2b3c32a1f489d2d2b2b27`; lines 142–143 expose latched context blocks and parsed counts as metadata. Lines 230–263 validate header/descriptors before entering METADATA.
- `br88_pipeline_v91h.sv`: SHA `7511f6bee4aeb1d78b9751ac493854a2c926519da4efcfa940619009b92f3ed8`; lines 174–179 wire this metadata to packed scratch's begin interface.
- `packed_scratch_v91g2.sv`: SHA `d8a7a0077981715566888b9de1a7bf052a0a875258a3f26e20fb0358d56e4bf4`; lines 103–105 define 32-bit alignment, and lines 177–180 form four serial plan prefixes. Lines 318–335 validate and accept a new owner.

## Exact algebra and source change

For 32-bit words define `A=aligned(2*blocks)`, `B=aligned(4*count1)`, `C=aligned(4*count2)` and `D=aligned(4*count3)`, using every original multiplication/alignment wrap point. The new source retains `start1=32+A`, calculates `start2=sum3(32,A,B)`, `start3=sum4(32,A,B,C)`, and the nonraw `used=sum5(32,A,B,C,D)`. The raw `used` expression is unchanged. Each prefix has a separate carry-save compression tree and a single final carry-propagating sum; a later prefix does not depend on the earlier prefix result.

For one bit, `a+b+c = (a XOR b XOR c) + 2*majority(a,b,c)`. Multiplying by each bit's weight and summing proves the word identity; discarding only the carry beyond bit 31 gives exact modulo-2³² equivalence. Repeated compressors preserve that sum. This argument covers arbitrary 32-bit counts and their overflow behavior; it assumes no nominal packet bounds. No public/state input or output is narrowed. The existing `aligned` function is unchanged.

Candidate: `fpga/experiments/cu66-v106-plan/packed_scratch_v91g2.sv`, frozen SHA `c46f01765b79bd35929183d8475287c2b71e93c289371f0e3f212b320b175e48`.
Recipe: `fpga/experiments/cu66-v106-plan/edit-recipe.json`, schema `v106-edit-recipe-v1`, SHA `bc27673675fa73250569f2811c3b06628832851e138e95745d6de69b9eb6515f`.
Two unique literal edits insert pure helpers and replace only the four prefix assignments. Reversing them recovers the complete original source exactly.

## Owner and guard obligations

The IDLE begin path still gives stale epoch error 2 priority over invalid blocks/counts/plan-size error 1. Raw count restrictions and `plan_used > 262144` use the original expressions/results. An accepted begin still captures epoch, blocks/counts, plan starts and used bytes; clears `written`, `assembler`, assembly bookkeeping and cursors; and enters INGEST on the same edge. An invalid begin does not perform those accepted-owner updates.

Reset/matching abort retains accepted physical-write ownership until matching ACK. Stale abort/ACK, error ACK, same-edge acceptance/failure, and held reset behavior are unchanged. The candidate does not introduce a plan register, extra validation cycle, address narrowing or timing exception.

## Python and focused RTL evidence

`python3 scripts/cu66-v106/plan.py --model-only` passes 290,816 deterministic vectors: all 131,072 values of the 17-bit block input, adversarial count/alignment/overflow combinations, 65,536 full-width random count tuples, and additional bounded valid-plan inputs. There are 165,393 high-count inputs and 6,132 accepted plan combinations. Every vector compares the CSA result with a direct independent modular prefix calculation; the bit truth table validates the compressor identity. This vector set is not an exhaustive enumeration of three 32-bit counts.

Prepared old/new adapters preserve complete production bodies after removal of module rename and direct observation ports. Their comparator checks every original public output plus all four plan outputs. The focused bench replayed all 290,816 Python vectors through the actual production combinational logic, passed 9,088 clocked begin-result checks and one stale-epoch priority check, and passed all nine historical accepted-write hazard cases (311 hazard-test edges, eight physical writes accepted and eight matching ACKs). Compilation passed strict Verilator 5.020 `--assert -Wall`, C++ `-Wall -Wextra -Werror`, two jobs and finite in-container watchdogs, with no warning suppression. The retained trace is byte-identical to the independently generated expected vector stream.

Selected PASS receipt: `experiments/python-gamebub-v106/plan/attempts/20261108T010448792601Z/results.json`. Its complete-production adapter normalization and source/artifact hashes are retained. Reproduce using `python3 scripts/cu66-v106/plan.py`.

The separate `fpga/experiments/cu66-v106-plan/audit_trace.py` independently rechecked every retained prefix result against direct 32-bit modular sums, all source/recipe/adapter pins, the compressor bit truth table, coverage counts, strict flags and bound clocked/hazard terminal verdicts. Its PASS sidecar `experiments/python-gamebub-v106/plan/trace-audit.json` records its own hash, selected receipt/summary hashes and compressed/raw trace hashes. The prefix trace directly records arithmetic results; the clocked error/owner assertions are verified in the retained C++ bench and terminal verdicts rather than reconstructed from separate per-edge state traces.

Root integration should use a separate additive follow-up lane so the frozen initial V106 twelve-lane matrix is not silently changed. The native candidate is `lut-storage-plan`, measured against the same 10 ns constraint. Synthesis can move the bottleneck again; final routed setup/hold/pulse/routing reports decide whether the internal target is met. Hardware FPS and complete decode latency remain separate qualifications.


## Final integration outcome — 2026-11-08 UTC

The separate native workflow is now terminal. See the [final measured comparison](vendor-comparison.md) for four completed Default-flow routes, the retained fifth placement failure and sixth timeout after synthesis. The selected completed source includes PLAN and has routed WNS −4.034 ns at the unchanged 10 ns clock; the fixed 100 MHz target remains unmet. The newer sixth combined source has synthesis-only WNS −3.205 ns and no completed placement/route. A separate unselected post-route diagnostic reached −3.777 ns and also fails setup. These integration outcomes supersede the earlier pending-workflow note; the focused PLAN proof and its frozen generator remain unchanged. Hardware 30 fps and complete under-10-ms decode validation remain open.

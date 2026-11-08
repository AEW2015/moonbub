# V106 exact full-width context-position candidate

The first V106 LUT variant's final routed worst path is the context decoder's constant division from 32-bit sparse position to output block. The new isolated candidate replaces that evaluation with parallel byte lookup tables, a combined correction/ZIGZAG-index table, and carry-select quotient sums. Python and strict complete-module focused RTL checks pass. Native timing remains a separate gate in the root workflow.

## Actual routed evidence

The [first LUT routed setup report](../../experiments/python-gamebub-v106/native/20261108T005012241750Z/reports/route-setup-paths.rpt), SHA-256 `915b2331b769ee3a06d269482ce707bfecaa410d0056d9978392f35beb90873b`, reports:

| Routed first-LUT measurement | Value |
| --- | --- |
| Slack | −7.130 ns |
| Launch | `context_decoder/position_reg[11]/C` |
| Capture | `context_decoder/out_block_reg[14]/D` |
| Data delay | 17.075 ns |
| Logic / routed interconnect | 6.788 / 10.287 ns |
| Levels / CARRY4 | 25 / 14 |

The launch net has fanout 137. The original division/modulo expressions appear at `fpga/experiments/cu66-v91b/br88_context.sv:56` and the following three band branches. Original source SHA-256 is `f0f603245090478b773bc6abba15a128e12aff764840a43df8429d361553fc72` at baseline `eececf35da97c9b14230d464ecde7576cb7840db`.

The routed top 50 include 16 position-to-block paths, 22 scratch allocation/reset paths, and 12 Rice-parser size-to-value paths. The latter class has −6.531 ns slack and remains a separate potential bottleneck. This candidate targets the measured position cone; it does not claim to fix every failing endpoint or satisfy the 10 ns constraint before native measurement.

## Exact full-32-bit identity

For divisor `d` (5, 15 or 43), write `n = Σ(256^i × byte_i)`. Each table entry supplies `q_i mod 65536` and `r_i` such that `256^i × byte_i = d × q_i + r_i` and `0 <= r_i < d`. Therefore:

- `floor(n/d) mod 65536 = (Σq_i + floor(Σr_i/d)) mod 65536`.
- `n mod d = (Σr_i) mod d`.

Each remainder sum is at most `4(d−1) <= 168`, and its quotient correction is 0…3. Reducing each byte quotient modulo 65536 before addition preserves the final low-16-bit quotient. This algebra applies to every 32-bit position, including `0xffffffff`, rather than assuming only reachable nominal positions.

Four parallel byte lookups produce the quotient/remainder contributions. An eight-bit carry-save remainder sum indexes a combined table containing the two-bit quotient correction and the **final six-bit ZIGZAG index**. Each entry references the original ZIGZAG parameter at a literal constant index; there is no runtime remainder subtraction, offset addition or subsequent variable ZIGZAG lookup on this path. Four parallel 16-bit carry-save sums compute quotient corrections 0, 1, 2 and 3, with a final two-bit selection. The mapping/resource/timing effect is measured separately; source structure alone is not timing evidence.

The combined table has entries for all 256 remainder-sum addresses. Its two-bit correction truncates for unreachable larger sums. The proof does **not** claim an unrestricted external remainder-sum helper contract: the fixed byte constants and identity ensure actual 32-bit positions always yield correction <=3. All actual position inputs retain exact quotient and index behavior.

## Preserved contract

Only pure helpers and the existing sparse-geometry calculation are changed in `fpga/experiments/cu66-v106-context/br88_context.sv`; the recipe reconstructs the complete original body elsewhere. Position/state/metadata widths, start/reset/abort priority, validation/error order, parser handshake, held output, counters and output cycles remain unchanged. Band 0 and every invalid/default 8-bit band retain low-16-bit `emitted` as the block and index zero. The original ZIGZAG constants remain byte-identical.

The private geometry helper takes only the low 16 emitted bits, with an explicit `emitted[15:0]` projection at its call. This preserves the original default `16'(emitted)` behavior while avoiding unused private argument bits; the emitted state and production public interfaces retain their original widths. The probe records full 32-bit emitted test values and checks this projection explicitly.

No register, pipeline cycle, reset/clock exception, timing waiver, assumption about valid input positions, DSP claim or Fmax claim is introduced.

## Current evidence and qualification plan

The independent Python model decodes all 3,072 actual byte-table entries and 768 combined correction/index entries. It checks 4,260,918 deterministic positions:

| Coverage | Cases |
| --- | ---: |
| All valid positions through `65536*d`, including end positions | 4,128,771 |
| Full-32-bit random positions | 131,072 |
| Edge/correction-boundary/max-sum cases | 63 |
| Default behavior covering all other 8-bit band values | 1,012 |

Crafted byte combinations hit correction boundaries and maximum remainder sum 168. This is universal algebra plus exhaustive table constants/nominal domain and broad full-width tests, not exhaustive enumeration of all 2³² positions or four-state formal equivalence.

Complete original/candidate production adapters compare all 37 public ports and actual internal sparse block/index at every clock evaluation. The pure geometry probe passed all 4,260,918 cases using the exact candidate helper and original literal-division behavior; Python independently replayed every retained row. The retained historical context bench passed 55 contexts in eight 16/32-bit word, serial/parallel and stall profiles, with 84,265 expected outputs per profile and 172 directed checks covering malformed streams and reset/abort/replacement-start/held-output behavior. Compilation passed strict Verilator 5.020 `--assert -Wall`, C++ `-Wall -Wextra -Werror`, two jobs and finite in-container watchdogs. No helper waiver or warning suppression was used.

Frozen candidate SHA-256: `9cb6337098d36adfbe4ef2dc073fc30a6dea17eaa4d57322fa4e725b8cce5277`. Exact two-edit recipe SHA-256: `41a072399a86cf1a189af3b661946bc4a4ec70c7a277752a74a3dfbd4eee8e3f`. Selected PASS receipt: `experiments/python-gamebub-v106/context/attempts/20261108T012416154340Z/results.json`. Reproduce with `python3 scripts/cu66-v106/context.py`.

The separate offline auditor `fpga/experiments/cu66-v106-context/audit_trace.py` checks the exact source/recipe/adapter reconstruction and all table constants, then independently verifies every retained input sequence and output against integer division and the original raster permutation. Its sidecar is `experiments/python-gamebub-v106/context/trace-audit.json`, binding auditor, selected receipt/summary, compressed/raw trace hashes and coverage. The first failed strict compile is retained: it identified unused high bits in the private emitted argument, corrected by the explicit exact low-16 projection described above.

Root integration uses additive follow-up lanes, preserving the frozen initial V106 matrix. Final routed setup/hold/pulse/routing and worst-cone reports decide whether the 100 MHz internal target is met; hardware FPS and complete decode latency remain separate gates.

# V106 static telemetry-counter words

The isolated telemetry candidate passes a strict clocked comparison of complete original/candidate coefficient pipelines and an independent oracle for all 52 public 64-bit histogram words. It retains every counter, guard, reset priority and sampling edge. Native area/timing remains a separate root-owned measurement.

Candidate: `fpga/experiments/cu66-v106-telemetry/br88_pipeline_v91h.sv`, frozen SHA-256 `c6f839570988768ac2a373302d8980ce9a6532ccbcf3c09415f9ca1c05959577`.
Exact three-edit recipe: `fpga/experiments/cu66-v106-telemetry/edit-recipe.json`, SHA-256 `dbb3df9555843c628424803243514922484f208b750e1c2c3bd61a5c16c2d01a`, schema `v106-edit-recipe-v1`.
Baseline: `eececf35da97c9b14230d464ecde7576cb7840db:fpga/experiments/cu66-v91h/br88_pipeline_v91h.sv`.

## Measured motivation

The CLOSURE synthesis report at `/home/lori/gamebub-build/cu66-v69/v106-closure-20261108T013032719249Z-8cf646/results/synth-setup-paths.rpt`, SHA-256 `01c56eb490969eb501f90a7f75a8f3f0c078f526bd748fb833b49b5eb54cca7c`, contains nine cache-count-to-emitter-histogram paths among its top 50. Their first path has WNS −2.740 ns from `coefficients/cache_count_reg[9]/C` to `coefficients/child/count_emitter_state_reg[1][62]/D`, 12.425 ns data delay, 4.749 ns logic, 7.676 ns **unplaced interconnect estimate**, and 28 levels including 16 CARRY4.

That path crosses busy/start/cancel/readiness logic, emitter-state selection and a 64-bit counter carry chain. The source uses a dynamic indexed read/increment/write at `br88_pipeline_v91h.sv:248`, with analogous packet/scratch histograms at lines 263–264. These are synthesis estimates for the earlier CLOSURE source, not routed measurements or timing results for this candidate.

## Exact source contract

Each of the three dynamic histogram update statements becomes a static bounded loop: four emitter words, sixteen packet-state words and thirty-two scratch-state words. Each constant word has its own `word + 1` expression and index-qualified update. The original enclosing `else if(running)` and reset/start/abort branch remain byte-identical. No original reset-loop statement or other telemetry update changes.

For any binary index in its original 2/4/5-bit domain, exactly one static condition is true, so that word receives the original modulo-2^64 increment and every other word holds. Reset/start/abort still clears every histogram word before the running branch; inactive cycles hold. Nonblocking assignment still samples the pre-edge index and running state even when the controllers transition on the same edge. No counter width, public port, diagnostic, timestamp, state or cycle is removed or narrowed.

This source structure makes independent increments available before the potentially late selector. Whether synthesis retains that structure, maps a late enable or reshapes the arithmetic, and whether timing improves must be determined from actual native reports.

## Focused clocked results

Selected PASS receipt: `experiments/python-gamebub-v106/telemetry/attempts/20261108T015350854837Z/results.json`.

| Check | PASS result |
| --- | ---: |
| Prepared counter/guard cases | 53,248 = 52 × 64 × 16 |
| Prepared clock edges, including separating resets | 106,497 |
| Historical public-interface clock edges | 7,982,233 |
| Total clock edges | 8,088,730 |
| Public production port names compared | 167 |
| Counter words checked per edge | 52 × 64 bits |
| Historical packets / memory profiles | 20 / 2 |
| Golden dense coefficient comparisons | 4,501,888 |
| Historical directed checks | 56 |
| Synchronous-staging directed checks, included above | 9 |

Prepared cases initialize actual original/candidate module counter words with values carrying through each of the 64 positions, including full wrap. They cover every target index and all sixteen reset/start/abort/running combinations. Child/controller states are explicitly prepared through verification-only C++ access; owner-related scratch flags are made coherent and a real reset edge separates cases. These cases are not asserted to be reachable from complete packets.

The complete production modules are preserved byte-for-byte after undoing only their module rename. All original public outputs, including all array elements, are compared. The independent C++ oracle samples the pre-edge running flag and three actual indices, applies reset priority or unsigned 64-bit increments, and checks every one of the 52 words before and after each clock. Prepared tests check all requested target indices and all 64 carry positions.

The retained V91h public-interface pipeline bench runs in the same dual-module wrapper. Its golden checks, memory model, schedules, packed bytes, output values, counter reconciliation and directed tests remain intact; only its model/main names and pre/post oracle hooks change. This supplies genuine packet/refill/metadata/output traffic, memory delays from 1 to 501 cycles, backpressure, write/read ownership, cancellation and warm retry. The explicit staging specialization is the actual native synchronous mode (`SYNC_STAGING=1`).

Verilator 5.020 passes `--assert -Wall --public-flat-rw`; GCC passes `-Wall -Wextra -Werror`. There are no warning relaxations or disabled assertions. Two-job compilation has an in-container 300-second watchdog; simulation has an in-container 180-second watchdog and a 100-million-edge harness limit. The shared available-RAM/PSI gate remains enforced.

## Retained replay and limits

All 106,497 prepared edges and their 53,248 initial-value markers are retained. Historical traces retain every 256th clock and all outer reset/start/abort edges: 31,404 checkpoints. The C++ oracle and complete original/candidate comparison still run on **every historical edge**.

The independent `fpga/experiments/cu66-v106-telemetry/audit_trace.py` reconstructs every seeded initial 64-bit carry pattern, checks full index/carry/control coverage, and replays every prepared array update. It checks historical reset snapshots and cross-array delta consistency, exact recipe/body/bench adaptation, source/artifact hashes and strict tool flags. It does not replay omitted historical index transitions. The PASS sidecar is `experiments/python-gamebub-v106/telemetry/trace-audit.json` and binds auditor, selected receipt/summary and compressed/raw trace hashes.

The attempt ledger retains three fixed verification failures: generated nested-module state access paths and a C++ indentation warning; a redundant compile macro colliding with a public generated parameter; and an incoherent artificial sealed/flush owner state caught by an assertion in the original scratch module. None required a production RTL change, assertion suppression or warning waiver. The candidate hash is unchanged from its initial three-loop edit.

Reproduce with `python3 scripts/cu66-v106/telemetry.py`, then `python3 fpga/experiments/cu66-v106-telemetry/audit_trace.py`.

Prepared states supplement real interfaces; they are not full-packet reachability or four-state/formal proof. Two-state power-on initialization is not FPGA memory-initialization qualification. Root integration owns complete CS88 fresh/canonical regressions and final `closure-prefix-telemetry` native measurements at the fixed 10 ns constraint. Positive internal routed setup/hold/pulse results, methodology/CDC/boundary signoff, sustained hardware 30 fps and complete validated decode latency remain distinct gates.

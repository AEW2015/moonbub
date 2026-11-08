# V110 same-edge owned unacknowledged fault pulse

This candidate starts from the selected V109 FETCH source closure in `experiments/python-gamebub-v109/native/20261108T121030620057Z/receipt.json`. It replaces three bodies: the pipeline top, inverse stream, and reconstruction stream. The producer, scratch implementation, mathematical children, public top interface, original counters, error values, and invalid-cycle outputs retain their original source. The complete eighteen-origin map and reversible edits are in `fpga/experiments/cu66-v110-fault/edit-recipe.json`.

The measured V109 FETCH secondary path launches at `inverse_fault_ack` and traverses distributed base abort/cancellation into a Rice reservoir CE; its reported slack is −1.599 ns, fourteen LUT levels, 9.056 ns routed delay. The primary scratch-quiescence path remains a separate candidate owned by the root's other worker. No timing improvement is inferred from this source edit.

## Exact next-state construction

Let `F` be a stage's existing registered `fault_o`, `A` the existing top acknowledgement, and `U = F && !A`. The original top has:

```
A_next = 0                     if reset || abort_packet || accepted_start
         A || F                otherwise
```

Both stage bodies clear `F` in their existing highest-priority `reset || start || cancel` branch, hold it otherwise, and assign `F_next = reason != 0` exclusively in `fail(reason)`. The stage's `start` is the unchanged top `accepted_start`; top external abort implies both stage cancels. Consequently any top acknowledgement-clear event also clears the stage fault, so `U_next = 0` on that edge. Local peer/coefficient cancellation also clears `F` and `U`, but does not independently clear the top acknowledgement.

Outside those controls, a held fault is acknowledged on the edge, giving `U_next = 0`. A failure gives:

```
U_next = (reason != 0) && !(A || F)
```

The candidate therefore defaults `fault_pending_o <= 0` on every edge in the existing stage main sequential process. The existing `fail(reason)` task additionally assigns `fault_pending_o <= (reason != 0) && !fault_ack_i && !fault_o`. Its position retains the original last-assignment priority when reconstruction calls `fail` from physical-reference response handling and again from the current-state case. Both calls update fault and pending together using the same winning reason. The original error and fault assignments remain unchanged. This derives the new register on the original failure edge; it never samples an already registered fault on a later edge.

The top retains both original acknowledgement registers and their reset/abort/accepted-start priority, then uses:

```
base_abort = abort_packet || inverse_fault_pending || reconstruction_fault_pending
```

Two new top assertions check `fault_pending_o == fault_o && !actual_top_ack` on every edge. Existing fault/status assertions remain active. Sticky status, simultaneous inverse/reconstruction faults, sticky coefficient errors, attempted versus accepted start, replacement-start suppression, public error priority, and done retain the original expressions. Immediate inverse/reconstruction cancellation and coefficient-boundary cancellation also retain their original expressions. There is no new latency contract, delayed reset, private flush, physical drain change, status sampling, output mask, or changed publication edge.

The ack path now terminates in each local pending register's D calculation instead of passing through a top fault/ack AND into the distributed base abort on that same cycle. New failure detection and local ack feedback still require native timing measurement. Synthesis may transform or merge equivalent logic; the source construction alone establishes no physical separation or clock gain.

## Consumer and deadline inventory

| Signal | Existing consuming edge or operation | Candidate behavior |
| --- | --- | --- |
| `base_abort` | Same-cycle coefficient producer abort, ingress/scratch cancellation, readiness and cache/queue ownership fences | Equal on every cycle by each stage pending/ack invariant |
| `inverse_cancel` | Immediate inverse kill, coefficient storage CE fencing, dequant/IDCT flush | Original equation unchanged |
| `reconstruction_cancel` | Immediate reconstruction lookup/residual/output/reference-request fencing; logical cancellation of outstanding reference owner | Original equation unchanged; physical matching reference response still owns retirement |
| `coefficient_stage_cancel` | Existing one-slot final-offer invalidation, accepted-start suppression | Original equation unchanged |
| `error` and `done` | Original public cycle, priority, status values and terminal fence | Original equation unchanged |
| stage `fault_o` and counters | Original failure/reset/start/cancel edge and held state | Original assignments and last-write priority unchanged |
| actual top ack | Original reset/abort/accepted-start clear; old-fault set | Original process unchanged; additionally feeds only local pending D |

## Verification and reproducibility

Preparation and structural checks:

```sh
python3 scripts/cu66-v110/fault/prepare.py
python3 scripts/cu66-v110/fault/model.py
python3 scripts/cu66-v110/fault/qualify.py
```

The model audits reversible replacements and exact source hashes, retains all eighteen selected origins, and checks that both stage bodies still have precisely their original two fault/error assignments. It exhausts 32,768 local transition rows including every eight-bit failure reason, 524,288 ordered double-failure rows, and 1,024 coupled top rows covering reset, external abort, accepted start, coefficient fault, simultaneous stage faults, peer cancellation and acknowledgement priority. This is a two-state algebra/source audit, not HDL formal equivalence or actual RTL execution.

The focused runner compares complete V109 FETCH original and candidate inverse/reconstruction modules with the actual selected math children. It retains all inherited independent coefficient-store, metadata, fault-priority, coordinate, pixel, public-invalid-output, counter, historical boundary and goldens checks. Existing prepared inverse internals are declared verification-only. The extra pending comparison uses an explicit parent ack shadow: reset, `verify_abort_packet` or standalone admitted `start` clears it; a local/peer `cancel` does not. `verify_abort_packet` is driven only when stage cancel is asserted, on alternating guarded cycles to distinguish those causes. Candidate pending is compared against the original fault and this coherent parent ack at every half-cycle. Full canonical qualification checks the actual top acknowledgements separately.

The runner requires explicit `--run`, uses strict Verilator `--assert -Wall` and C++ `-Wall -Wextra -Werror`, one compile job, two CPUs, 4 GiB memory and memory+swap, network disabled, finite watchdogs and host-pressure gates. Each attempt preserves logs, all source hashes and snapshots, binary hashes, compressed traces, original failures and a receipt. No old source or proof is overwritten.

Focused attempt `20261108T130206375702Z` has **actual RTL PASS**, selected in `experiments/python-gamebub-v110/fault/results.json`. Its immutable attempt receipt is `experiments/python-gamebub-v110/fault/attempts/20261108T130206375702Z/results.json`, SHA-256 `20a667d2293f1d49a151592cfc64e508fff7ff8c4228218f2cfa63bf717f7a0c`. Verilator reports version 5.020. All six bounded commands exited zero, with no strict warnings, memory-pressure stops, or timeouts. Total wall time was 29.10 seconds.

Both inverse seeds, 110101 and 110102, passed 9,467 prepared edges, 51 concurrent arithmetic/input-failure cases and two late same-edge write/fail cases apiece, plus the unchanged historical 48-case/15-directed suite. Historical interface runs covered 11,406 and 11,344 edges. Reconstruction passed two full frames and 51 directed checks across 2,445,067 edges and 7,335,201 half-cycle public comparisons. The extra pending predicate matched the old fault/unacknowledged expression alongside every inherited check. No failed attempt occurred in this namespace.

Production source SHA-256 values at the actual focused PASS are:

| Body | SHA-256 |
| --- | --- |
| `cs88_pipeline_v91k.sv` | `950182396c4ac6f0f31c74fd41bf66c6122727e44cacf31ae48c55098e0dd786` |
| `cu66_inverse_stream_v91j.sv` | `e00f53b7360878455e1078b0aaa3955ee0aab4abbecefde0c1b3b1f5a90c8a41` |
| `cu66_reconstruct_stream_v91k.sv` | `f9dc06f183010a3486f387075b702a4cc7d9b4a06c1f4b0174cddad5813bf149` |

Source and proof files are frozen after this actual PASS. Full canonical qualification, including the actual parent ack assertions, and native timing remain separate root-owned gates. Focused PASS does not qualify the complete pipeline or predict a timing PASS.

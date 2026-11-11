# V129 simulation-only latency monitor

**These observations overlap and do not establish a root cause or a speedup.** The opt-in instrumented bench measures ready/valid behavior at actual V129 parent-model signals and the testbench's finite memory-service state. It leaves the selected RTL unchanged. The [monitor contract and signal meanings](../../fpga/experiments/cu66-v129-observe/README.md) describe the priority mask, which is a reporting convention rather than causal attribution.

The [source-bound full-parent receipt](../../experiments/python-gamebub-v129/latency-monitor/full-parent/attempts/20261111T004718819050Z/receipt.json) records a strict Verilator compile and passing row-write, stalled profile 1, seed 116702 run. Its 98 frozen source snapshot hashes and 91 recorded artifact hashes were checked. The [runner](../../scripts/cu66-v129/latency-monitor/run_parent.py) retains the existing canonical byte, hash/root/seal, ownership, wrong-ACK drain and retry checks and compares terminal records and event/hash cycles with the pinned V128 control. This is one finite-service simulation profile, not proof for all traffic. The separately compiled [monitor accounting unit test](../../experiments/python-gamebub-v129/latency-monitor/unit-result.json) checks classification and conservation.

The monitor sampled **1,601,560 pre-edges**, from the accepted parent start until the bench observed commit, excluding the bench's kill predicate (reset, abort, validator/join error or metadata mismatch). This is one fewer than the bench's 1,601,561-cycle start-to-commit timestamp difference; the boundaries are distinct. In this window the counts are:

| Observation | Cycles |
| --- | ---: |
| Coefficient valid and not ready | 641,679 |
| Staged inverse valid and not ready | 641,679 |
| Residual valid and not ready | 617,341 |
| Canonical output valid and not ready | 654,001 |
| Write/hash output valid and not ready | 163,779 |
| Candidate-write request valid and not ready | 23,127 |
| Testbench `candidate_pending` asserted | 1,120,705 |
| Coefficient held and `candidate_pending` simultaneously | 569,509 |
| Canonical output held and `candidate_pending` simultaneously | 542,508 |

The full 128-bin overlap mask and per-channel no-valid/stalled/accepted counts are in the receipt. The request/response and `candidate_pending` observations cover only candidate writes in the **abstract testbench service model**; they do not include reference/refill reads or real SDRAM. `candidate_pending` includes cycles when the response is valid, and response stalls are not overlap-mask bits. This is not an independent proof that memory causes a stall. A stalled signal indicates an offered transfer that was not accepted on that sampled edge. The monitor does not observe all internal work or partition causal responsibility among overlapping stalls.

The unchanged row case still measures **1,553,197 cycles from last outer input to commit**. The matching cycle and golden checks validate that this instrumentation did not change that simulated trace; no throughput improvement, timing closure, sustained 30 fps, under-10-ms hardware decode, or physical-memory performance is demonstrated. The next useful experiments are controlled, source-bound changes or additional internal counters that distinguish the upstream/downstream dependencies while retaining the same functional and physical-debt checks.

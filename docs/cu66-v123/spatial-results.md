# V123 spatial prototypes and remaining implementation work

The independent [rank algebra study](rank-model.md) supports the RTL control
experiment. It compares a full32 sparse ordering expression with live high/block
comparisons and a prepared rank mask. The model checks the complete 64-entry
mapping against an independently generated packet-oracle traversal, boundaries,
high-bit positions, 100,000 deterministic random comparisons and 6,144 phase/raw
and Boolean contexts. This is finite algebraic evidence; clocked ownership and
functional behavior require the actual RTL suites.

The separate [causal overlap model](overlap-model.md) exercises finite result
slots, compute lanes, one outstanding write, ACK-committed data and ordered
SHA-256 consumption over the six retained canonical vectors. Every configuration
processes 3,110,400 bytes in 48,600 chunks and preserves their target-byte digests.
Fourteen bounded model/fault checks pass. The write bus has 32 modeled 16-bit data
edges per 64-byte request plus explicit overhead. No aggregate stall counts are
expanded into fabricated producer events.

## Synthetic comparison

| Synthetic service profile | Slots / compute lanes | Six-vector batch cycles |
| --- | ---: | ---: |
| 32 data  + 2 overhead | 1  / 1 | 3,790,804 |
| 32 data  + 2 overhead | 2  / 1 | 1,895,438 |
| 32 data  + 2 overhead | 2  / 2 | 1,895,438 |
| 32 data  + 16 overhead | 1  / 1 | 4,471,204 |
| 32 data  + 16 overhead | 2  / 1 | 2,332,848 |
| 32 data  + 16 overhead | 2  / 2 | 2,332,848 |

Under these particular costs, two slots reduce the batch time by 1.92–2.00×,
while a second compute lane changes nothing. This suggests testing owned
buffer/ACK/digest overlap before multiplying compute lanes. It does not predict
an FPGA speedup: the compute/hash/finalize costs are synthetic, 64-byte writes
are not the current implemented 8-byte row service, and storage/ports are not
mapped. Hashing assumes a local ACK-committed mirror with unbudgeted local
access; the external bus charges writes only. Readback, scanout, refresh and
physical arbitration costs are absent.

Per-vector intervals begin at their first synthetic compute allocation and end
at digest finalization. They are not last-outer-byte→validated-commit latency,
immutable-bank publication, C2/HUD/seal qualification or displayed frame rate.
Do not compare these cycle totals with the existing 1,145,104 / 1,553,197-cycle
row fixtures or convert them into a claim of validated decode below 10 ms.
The source-bound [model report](../../experiments/python-gamebub-v123/overlap-model/results.json)
retains scenario inputs, per-vector intervals, schedule hashes and fault results.
An earlier result with an invalid bus assumption is retained as review history;
it is superseded and is not qualification evidence.

## Next causal implementation experiment

1. Record pre-backpressure compute starts/completions, held-ready cycles,
   actual write addresses/accepts/ACKs and hash/fence edges from the intended
   parent. Separate useful compute from downstream waits before calibrating
   a stage cost; accepted output times already contain backpressure.
2. Implement two finite owned result slots with byte-valid masks, frame/epoch
   identity and credits. Keep front/reference banks immutable. A slot retires
   only after the matching accepted write debt and required validation join.
3. Specify whether digest bytes come from the retained result buffer or an
   actual external-memory read. Budget the corresponding local port or shared
   bus service, plus scanout/refresh/turnaround and CDC.
4. Declare a versioned latency-aware parent contract for the changed schedule.
   Compare exact canonical pixels, independent C2 root/HUD/seal, error priority,
   accepted debt, cancel/drain and publication to the old exact-cycle control.
   Do not change the existing cycle oracle just to pass a new architecture.
5. Route the complete relevant component/parent at the intended clock, then
   measure every post-input→validated-commit sample and distinct presented IDs
   on hardware. Synthetic model gains do not close either hardware milestone.

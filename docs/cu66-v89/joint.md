# Actual mixed entropy work in the alias decoder graph

This study joins the new BR88 observations and the addressed alias layout in
one causal task graph. It does not subtract feedback counters from an old
elapsed time or add separate component speedups. Existing quantized 720×480
pixels and the actual CS88 packets remain the native content oracles.

## Inputs and scope

Four deliberately selected sources are used: C0/f0 (key), C0/f1 (cold/residency
traffic), C0/f3 (294 non-COPY stores that the old bank layout elided), and
C3/f50 (the prior difficult decoder source). The four actual packet policies
are AB38 control, feedback-overhead 5%, feedback-overhead 15%, and the all-BR88
diagnostic. Each is scheduled under LOW/HIGH costs with aliasing off/on:
**64 schedules on four distinct content sources**.

The observer reads and checks its full input records even when filtering for
these four sources. Each selected policy's work hash, packet hash, mask,
complete wire bytes and metadata bytes are bound to the independently native-
qualified V88 packet. No bitstream byte saving or coefficient work is inferred
from a projected ratio. The all-BR88 policy remains a diagnostic: one source
elsewhere in the full corpus exceeds the 49,152-byte limit, regardless of how
these selected sources behave.

The frozen V87 task graph is retained. Its setup/fetch/context/emission task
durations are recalculated from actual observed primitive counts. All
dependencies and finite staging consumers remain intact. The V88 alias
transformation then adds descriptor ports and actual data accesses, removes
COPY stores, and restores every non-COPY store elided only by the old physical
bank layout. A candidate's publication fence precedes a separate full-base-YUV
gather fence.

## Explicit hypothetical costs

| Primitive | LOW cycles per unit | HIGH cycles per unit |
|---|---:|---:|
| Adaptive decision / renormalization | 2 / 2 | 4 / 4 |
| Plain Rice bit | 1 | 2 |
| Rice symbol / AC event | 1 / 1 | 1 / 1 |
| Stream, header, raw or CRC byte | 2 | 4 |
| Coefficient emission | 1 | 1 |
| Raw bit | 1 | 2 |
| Probability initialization entry | 1 | 1 |

BR88's actual observation supplies zero adaptive decisions, renormalizations
and probability initialization; its actual `plain_bits` and symbol/event work
are charged. AB38 supplies zero plain bits. These are explicit bit-serial
sensitivity assumptions, **not measured RTL cycles or physical bounds**. The
model does not assume one variable-length symbol per cycle.

The model retains two arithmetic/parser servers, one shared fetch resource,
one emitter, one dequant resource, one inverse resource and one reconstruction
resource. Dequant, inverse and reconstruction each retain the nominal 64-cycle
cost per residual tile. Pixel read/write BL8 intervals remain 18/16 cycles.
All reported milliseconds assume 100 MHz.

The packet is fully buffered at release. Its whole CRC and metadata byte scans
gate producer admission. Chunk work follows the observer's documented CRC/header
fetch convention; this does not establish streaming ingress or physical byte-
port timing. The four contexts preserve their probability/symbol order and
pending AC lookahead attribution.

## Bounded state and checks

There are eight reference, inverse-result and quantized-coefficient slots and
four 16-tile output groups. Coefficient storage is reserved before producer
setup and released only after inverse/map consumption, not entropy emission.
The conservative staged-data reservation remains 9,216 logical bytes including
materialized dequant results. Descriptor maps, hash tree state, compressed input,
engine working registers and physical memory/port costs remain additional.

Ten unchanged CS86 replays must match the frozen V88 decoder and base-gather
times exactly. This is separate from the new CS88 AB38 control: its compact
quantizer metadata changes actual admission-scan bytes, so identical new
control timing is not assumed.

Every new schedule performs generic dependency/resource/group auditing,
staging-lifetime checks, frontend/context checks and the frozen independent
full-DAG auditor. Complete publication must depend on all modeled work. Fifteen
representative complete DAG/timeline witnesses are retained; every schedule
retains an independent audit result and exact timeline digest.

Six focused tests separately establish unchanged per-job/credit equivalence,
causal influence of injected plain-bit work, and rejection of unknown/negative
primitives or missing explicit costs. Those tests do not add gameplay coverage.

## Selected results

All 64 schedules pass, including the independent in-process full-DAG checks.
The final audit reconstructs producer work from 16 actual mixed observation
records and reaudits all 15 retained complete timelines. All ten unchanged
CS86 controls match the frozen V88 results exactly. Alias-enabled times are:

| Source / costs | Actual CS88 AB38 control | Actual CS88 15% feedback policy |
|---|---:|---:|
| C0/f0 key, LOW | 7.29135 ms | 7.29471 ms |
| C0/f0 key, HIGH | 10.07923 ms | 10.08595 ms |
| C0/f1, LOW | 8.82684 ms | 8.84658 ms |
| C0/f1, HIGH | 9.30344 ms | 9.25810 ms |
| C0/f3, LOW | 7.92931 ms | 7.93900 ms |
| C0/f3, HIGH | 8.26967 ms | 8.26246 ms |
| C3/f50, LOW | 11.26378 ms | 10.80892 ms |
| C3/f50, HIGH | 17.12268 ms | 12.30751 ms |

The simpler bitstream helps the difficult source, particularly under HIGH
feedback costs, but a few smaller sources regress because changed packet/fetch
work still costs time. On C3/f50 the 5% feedback policy slightly regresses to
11.26970/17.13306 ms. Minimizing adaptive feedback under a byte allowance is
therefore not equivalent to minimizing complete decode latency.

For these four selected sources the 15% policy finishes below 10 ms in three
LOW and two HIGH cases. The hard source stays above 10 ms in both tables.
The later full-base gather adds 5.913 ms to alias-enabled publication latency.
The per-row `memory_work_cycles` includes that post-publication gather; it must
not be mistaken for a pre-publication decoder-only memory floor.

No constant-descriptor optimization is included in these times. A separate
functional or traffic result cannot be subtracted from them without rebuilding
and auditing the corresponding causal graph.

## Evidence and reproduction

The selected [campaign](../../experiments/python-gamebub-v89/joint/results.json)
points to a unique attempt, source snapshots, row identities and witnesses.
The [independent final audit](../../experiments/python-gamebub-v89/joint/verification.json)
recomputes actual producer totals, checks native packet/work identity and
per-row packet/deadline conditions, matches all ten frozen controls, and
reaudits the retained complete DAGs. Selected-source result tables are retained
there and in the campaign report.

```sh
python3 experiments/python-gamebub-v89/joint/test_model.py
python3 scripts/cu66-v89/prototype_joint.py
python3 experiments/python-gamebub-v89/joint/verify.py
```

The new timing applies to neither all 457 sources nor a continuous 30-fps run.
HUD semantic decoding/hashing, actual inverse arithmetic, physical controller
rows/refresh, real RAM/transfer ports, asynchronous response drain, continuous
LCD/RGB565/HUD composition and ESP32/transport execution remain unqualified.
These results close no hardware 30-fps or complete validated under-10-ms
milestone, even when a selected conditional schedule finishes below 10 ms.

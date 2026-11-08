# Actual qualified RTL fence intervals

The existing READY+RICE canonical traces show a long **overlapping streaming interval**, with a short inverse tail after the coefficient producer finishes. These fences do not identify which internal actor is busy or blocked during that interval. They do not justify attributing the full frame cost to IDCT/DSP arithmetic.

This read-only diagnostic uses both qualified seeds 107601/107602 from [the READY+RICE canonical receipt](../../experiments/python-gamebub-v110/canonical-ready-rice/combined/attempts/20261108T140104467790Z/receipt.json), SHA-256 `7b3494c516182df3dd1fb4c64e5749814ab43906914e9a4dc0f2d3424a51132a`. The selected summary SHA-256 is `4ac75dc994a0adc1b38547089a6d6bb78a18c64171144afd93321530d7059bc9`. Both simulation transcripts, event traces and canonical output artifacts were hash-checked against that receipt. Nineteen current RTL/header/bench sources and their retained snapshots were also checked; the machine-readable output records each hash. Event assembly/dequant/residual/canonical/reference counts are independently reconciled with the printed case counters.

There are 44 case/profile/seed rows: **24 successes and 20 expected rejects**. The performance tables below include successes only. Expected rejects retain their original error codes, provisional counters and available fences in the JSON; absent timestamps are null, not fake zero-cycle phases. Differences use `end-start`, without an inclusive `+1`.

| Successful-case interval, cycles | Fast service, profile 0 | Stalled service, profile 1 |
| --- | ---: | ---: |
| First input → last input | 8,409–47,959 | 11,069–63,945 |
| Last input → first coefficient, residual cases only | 103,837–350,738 | 103,997–350,905 |
| First coefficient → last coefficient | 912,855–1,310,869 | 1,829,758–2,109,275 |
| Last coefficient → raw producer done | exactly 3 | exactly 3 |
| Raw producer done → last residual | 198–3,681 | 432–10,149 |
| Last residual → last canonical pixel | 66–7,698 | 185–21,625 |
| Last canonical pixel → component done | exactly 1 | exactly 1 |
| First canonical pixel → last canonical pixel | 621,040–1,653,484 | 1,735,751–2,384,707 |
| Whole printed case, start through finish/settle | 650,593–1,726,035 | 1,768,082–2,473,261 |

Intervals needing residual/coefficients have ten rows per profile, since the two zero-residual rows per profile have no such fences. Other successful intervals have twelve rows per profile. All observed last-input→first-coefficient intervals are ordered and nonnegative; the JSON preserves their signs rather than assuming this.

The fast profile is deterministic across the two seeds. Its per-case counters separate wire-vector bytes, actual inner refill bytes and dense emitted coefficients:

| Case | Packet vector bytes | Observed inner refill bytes | Coefficients | Coefficient span | Producer done → last residual |
| --- | ---: | ---: | ---: | ---: | ---: |
| `actual_001` | 30,109 | 17,483 | 499,584 | 1,282,938 | 198 |
| `actual_006` | 19,594 | 10,485 | 259,456 | 1,019,660 | 832 |
| `actual_043` | 15,088 | 6,710 | 204,672 | 912,855 | 3,681 |
| `actual_031` | 47,960 | 30,924 | 391,616 | 1,310,869 | 1,280 |
| `actual_006_varied_qcache` | 19,594 | 10,485 | 259,456 | 1,019,660 | 832 |
| `structural_all_copy_zero_residual` | 8,410 | 0 | 0 | absent | absent |

Packet byte counts are lengths of the pinned vector packets, not a newly inferred ingress-byte counter. Inner refill counts are actual printed child-refill counters. Dense coefficient payload is two bytes per coefficient and is recorded separately in the JSON. Cache-preload bytes/cycles are also retained separately; the bench performs preload before frame start, so they are excluded from the printed case interval.

## Overlap and tails

Canonical production begins **before the first coefficient** in sixteen of the twenty successful residual rows, because COPY/CONST work can proceed earlier. The signed first-coefficient→first-pixel difference is −81,958 through −334,409 cycles in those rows. These negative differences are real overlap, not missing/negative execution time. For the four `actual_001` rows, canonical production instead starts 147–153 cycles after the first coefficient.

The coefficient and canonical envelopes overlap for 912,855–2,109,122 cycles. In the COPY/CONST-prefix cases, the complete first→last-coefficient span lies inside the canonical envelope. **Do not add coefficient span and canonical span as serial wall time.** Each is an envelope containing stalls and idle holes, not measured state occupancy or useful-work cycles.

`coefficient_done_cycle` is the raw coefficient-producer completion fence. Its last coefficient precedes it by exactly three cycles. The last residual follows it by at most 10,149 cycles, while final canonical handling can continue longer. This bounds the **remaining tail** after producer completion; it does not show whether arithmetic/backpressure constrained producer progress earlier. The inverse counters explicitly show substantial assembly while math owns a bank, so the stream is concurrent.

The zero-residual structural case makes that distinction clear. It has no coefficient, dequant or residual work, but raw producer done→component done is **621,050 cycles** in profile 0 and **1,735,777–1,736,892** in profile 1. Its canonical pixel span is 621,040 cycles fast and 1,735,751–1,736,865 stalled. Whole-case costs are 650,593 cycles fast and 1,768,082–1,769,095 stalled. No IDCT/DSP optimization can eliminate this zero-residual output/reference-service cost.

The final observed completion fence is exactly one cycle after the last canonical pixel for every success. The bench separately calls `settle()` and requires physical owners drained, but it does not print a separate timestamp for the start/end of that call. This diagnostic reports that physical-settlement span as **unknown**, rather than assigning the one-cycle final-output fence to all physical drain work.

## Conditional budget and next investigation

Using **only the assumed 100-MHz reference**, strict 10 ms corresponds to fewer than 1,000,000 cycles. Only **2/24** successful whole-case rows are below that count: the zero-residual case under profile 0, once per seed. The same two rows pass the separate last-input→component-done cycle proxy; all other successful rows exceed that proxy. Neither proxy is calibrated hardware time or the production validated-publication endpoint. No achieved-clock, hardware-frame-rate or validated-decode gate is passed here.

The actual [qualified bench](../../fpga/experiments/cu66-v107-elastic/verification/bench.cpp#L237) deliberately makes profile-1 final `out_ready` true approximately one third of cycles and applies longer scratch/reference service. Every successful case still emits 518,400 canonical samples. Its observed service/backpressure envelope can therefore exceed the conditional budget even with zero residual arithmetic. The million-cycle coefficient spans in other cases identify an important sustained-stream interval, but the available fences cannot distinguish producer compute, scratch preparation, inverse bank pressure and reconstruction backpressure within it.

Before proposing more arithmetic lanes or claiming a DSP speedup, collect per-cause blocked-cycle evidence for producer DISPATCH/child-valid, inverse-ready/bank ownership and reconstruction output. The selected dequant operand preparation intentionally preserves canonical cycles; physically enabling DSP input registers establishes mapping, not a cycle-count reduction. Existing IDCT remains the qualified V108 body.

A concrete source investigation is producer metadata lookahead around [MAP_REQ/MAP_WAIT/DISPATCH](../../fpga/experiments/cu66-v110-ready/cs88_coefficients_v91k.sv#L1222), where each residual block's tile/cell/scale lookup is owned before forwarding coefficients. This is an investigation, not a proposed safe implementation: preserve live lookup/child/epoch ownership, skipped COPY/CONST mappings and exact malformed-input/cancellation behavior. These fences do not establish how much that lookup contributes, nor a safe cycle-exact latency reduction. No current proof, golden, RTL or native flow was changed.

Reproduce with `python3 scripts/cu66-v110/phase_budget.py`. The [full row-level diagnostic](../../experiments/python-gamebub-v110/phase-budget.json) has SHA-256 `46d39b136683c6f178308f0048e1e40b5780609f6d177738193717b1a9e43c20`; script SHA-256 is `8f675fff153a0e56c4fb20e5d731117d793b0621584cd1fb6e2606e158ce280a`. It includes exact signed intervals, event/counter reconciliation, overlaps, errors, source/input hashes and the explicit measurement limits above. No new simulation, synthesis, implementation or hardware work was performed.

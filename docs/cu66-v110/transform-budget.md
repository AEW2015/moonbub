# Matched transform response and spacing diagnostic

The retained qualified READY+RICE events show serialized **launched transform jobs**, while coefficient-bank filling overlaps those jobs. Each launched tile completes its 64-sample residual burst before the next tile's dequant launch. Long dequant→first-residual intervals include downstream readiness and are not measurements of IDCT arithmetic alone.

The read-only [script](../../scripts/cu66-v110/transform_budget.py) joins assemble, dequant and residual events by the complete identity `(case, memory_profile, frame_epoch, child_epoch, token, plane, block, tile, qcell, qscale)`, separately for seeds 107601/107602. It checks duplicates, ordering, complete/partial sample counts, frame/child epochs and every case's printed stage counters against the [actual qualified receipt](../../experiments/python-gamebub-v110/canonical-ready-rice/combined/attempts/20261108T140104467790Z/receipt.json). Both transcript/event hashes and nineteen current RTL/header/bench snapshot hashes are verified.

Each seed has **63,412 exactly matched complete tile identities**, zero incomplete records and zero unmatched launched identities. This includes provisional work from expected-error cases; successful and expected-error rows remain separate. The late-CRC reject contributes 6,475 provisional complete tiles per profile/seed and does not become validated frame output. The other early rejects launch no transform jobs. Zero-residual successful cases likewise have no transform records.

For every matched complete tile, the residual span is **63 cycles**: 64 consecutive accepted samples. This remains true under stalled profile 1. Successive complete-tile dequant launches never overlap the preceding residual burst: `next_assemble - previous_residual_last` is positive, with minimum and median **two cycles** in every successful residual case/profile/seed. Larger gaps include plane/chunk/source gaps and must not be charged automatically to arithmetic.

## Per-case measured intervals

These cycle values summarize successful cases; ranges cover the two seeds. `p50` is the arithmetic median and can interpolate between adjacent values. Spacing below excludes child/plane transitions, but can still include source/reconstruction stalls within one child.

| Case | Profile | DQ → first residual p50 | DQ → first residual max | Same-child launch-spacing p50 | Same-child launch-spacing max |
| --- | ---: | ---: | ---: | ---: | ---: |
| `actual_001` | 0 | 66 | 2,778 | 132 | 2,852 |
| `actual_006` | 0 | 130 | 34,938 | 204 | 35,012 |
| `actual_043` | 0 | 130 | 36,464 | 204 | 36,538 |
| `actual_031` | 0 | 130 | 10,639 | 204 | 10,713 |
| `actual_006_varied_qcache` | 0 | 130 | 34,938 | 204 | 35,012 |
| `actual_001` | 1 | 186–187 | 8,060–8,112 | 259–260 | 8,134–8,186 |
| `actual_006` | 1 | 210 | 100,423–100,485 | 284 | 100,497–100,559 |
| `actual_043` | 1 | 212–213 | 103,798–104,518 | 286–287 | 103,872–104,592 |
| `actual_031` | 1 | 206 | 73,769–74,121 | 280 | 73,843–74,195 |
| `actual_006_varied_qcache` | 1 | 210 | 99,727–100,880 | 284 | 99,801–100,954 |

Assemble→dequant is at most nine cycles, with median nine in every successful residual case. `actual_001` has 1,238 one-cycle and 6,568 nine-cycle responses per profile/seed; its one-cycle cases reflect the existing dequant fast-exit path. Other successful residual cases have nine-cycle responses throughout. The JSON retains per-case histograms, p95/p99, maxima and full worst-tile identities rather than reducing the data to a single first tile.

The first `actual_001`, profile-0, seed-107601 tile has the requested exact stamps: assemble 195,282; dequant 195,291; first residual 195,297; last residual 195,360; next assemble 195,362. Its six-cycle DQ→first-residual response is **not** representative of all tiles. The complete per-case median is 66 and maximum 2,778; the other fast-profile content cases have median 130 and considerably larger waits.

## What the fences establish

The [actual inverse FSM](../../fpga/experiments/cu66-v110-fault/cu66_inverse_stream_v91j.sv#L1035) sequences `M_DQ_SEND → M_DQ_WAIT → M_IDCT_WAIT → M_EMIT`. It frees the math coefficient bank and returns toward the next launch only after accepting output index 63—the **64th** residual sample. Its IDCT output-ready signal also waits for that final accepted sample. The observed minimum two-cycle launch gap after residual completion agrees with this source sequencing.

The peak unmatched event join is one launched identity, which establishes the serialized launch/result schedule observed here. It is **not** a count of all physical owners: the two coefficient banks can fill/hold another tile, and the separate `assembly_during_math_inputs` counters record those overlapping input handshakes. An assemble event marks a completed tile's dequant launch, not the first coefficient-fill cycle.

DQ→first-residual spans include IDCT processing, controller response and any wait until reconstruction can accept the first sample. Residual bursts themselves are consecutive once started. Large waits, their profile dependence and the downstream-ready fence mean these maxima cannot be reported as decoder-only arithmetic latency or IDCT initiation interval. The [earlier frame-fence diagnostic](phase-budget.md) additionally shows that final canonical output/reference service can exceed the conditional million-cycle budget with **zero** residual work.

A possible future architecture investigation is an explicitly owned elastic tile handoff that lets a completed IDCT result release the math job before reconstruction is ready for its burst, or independently owns the next dequant job. This would require complete payload/tuple ownership, reset/cancel/error fencing, queued-owner final-drain accounting and a versioned latency-aware oracle. It is not an implemented change, an exact public-cycle drop-in, or a demonstrated remedy for the profile-1 final-consumer service bound. Per-cause ready/valid/stall counters are still needed to separate compute from service before choosing such work.

The [machine-readable diagnostic](../../experiments/python-gamebub-v110/transform-budget.json) has SHA-256 `61d711dc7f41b72f0cddda2e299afbd0acc09374e3d77ae64881e63e1a57324f`; script SHA-256 is `1e9670dbb7571324ccd05539f2bb541e0ca402dcbb82e6af047123a21cd2d850`. Reproduce with `python3 scripts/cu66-v110/transform_budget.py`. All values are existing RTL bench cycles. No achieved-clock, calibrated hardware time, complete validated-decode deadline, new RTL simulation, synthesis, route or hardware result is claimed.

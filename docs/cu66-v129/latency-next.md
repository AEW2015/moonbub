# V129: latency target and next throughput investigation

The stalled V128 full-parent case takes **1,553,197 cycles from last outer input to commit**. At an actually achieved 125 MHz this interval would be 12.426 ms. Strictly under 10 ms on that same boundary requires at most 1,249,999 cycles: a reduction of **at least 303,198 cycles (19.52%)**. At 100 MHz the corresponding strict bound is 999,999 cycles. These are simulated-cycle conversions, not routed-clock or board measurements. The last-input boundary excludes earlier input time; from frame start the same case takes 1,601,561 cycles, and a first-byte or display-to-photon metric is longer or different.

The [stalled profile 1/seed 116702 case](../../experiments/python-gamebub-v128/integrated-study/live-guard/attempts/20261110T214331755905Z/row-116702-simulation.jsonl) and its [transform events](../../experiments/python-gamebub-v128/integrated-study/live-guard/attempts/20261110T214331755905Z/row-116702-events.jsonl.gz) and [hash events](../../experiments/python-gamebub-v128/integrated-study/live-guard/attempts/20261110T214331755905Z/row-116702-hashes.jsonl.gz) expose these endpoints for `actual_001`:

| Milestone | Cycle | Interval |
| --- | ---: | ---: |
| Last outer input | 253,975 | — |
| First coefficient | 411,153 | 157,178 after last input |
| Last coefficient | 1,612,502 | 1,201,349 after first coefficient |
| Last canonical pixel | 1,613,306 | 804 after last coefficient |
| Merkle root digest | 1,715,138 | 101,832 after last canonical pixel |
| HUD digest | 1,806,907 | 91,769 after root |
| Commit | 1,807,172 | 265 after HUD digest |

These intervals partition elapsed time; do not add the separately reported 499,584 coefficient transfers, 518,400 pixel bytes, 560,640 hash deliveries or 70,080 write acknowledgements as if they ran serially. The test records 217,970 residual/canonical overlap edges and 277,091 residual-fill-while-head-held edges. The endpoint traces show a long coefficient-to-canonical production span but **do not identify which ready/valid dependency causes it**. In particular, head-held events alone do not prove that inverse arithmetic, memory ACKs, or hashing is the dominant cause.

## Implementable next step

The [current parent hash controller](../../fpga/experiments/cu66-v91l/cs88_validate_publish_v91l.sv) uses one byte-fed SHA engine and schedules pixel leaves, empty leaves and tree nodes before HUD, then seal. Evaluate a separate HUD SHA engine that accepts the exact 42,240 HUD bytes and receipt concurrently with leaf/tree processing, retains the computed HUD digest by epoch and generation, and joins it with the verified root before generating the unchanged seal. Preserve byte order, receipt verification, all error/abort priorities, drain and accepted-bank rules. Confirm that the real HUD source can deliver concurrently; add bounded buffering/backpressure if it cannot. Reuse the existing known-answer roots, HUD digest and seal as independent oracles and test stalls, wrong ownership, cancellation, late receipts and same-epoch retry. Run the full parent regression, then check both 100 and 125 MHz routed timing and resource use.

This is a concrete serialized **critical-tail opportunity**, not a prediction that a second SHA removes exactly 91,769 cycles. Even the optimistic upper bound of eliminating that entire measured root-to-HUD interval leaves **at least 211,429 more cycles** to remove, before accounting for joining, source readiness, timing changes or other dependencies. Since HUD and tree would overlap, their full individual costs must not be added or both counted as savings.

In parallel, instrument cycle-exact exclusive stall reasons at coefficient production, inverse-bank admission, canonical output, pixel/hash readiness and physical write/debt. Record simultaneous blocked conditions separately, plus occupancy and accepted transactions, across all profiles. Then optimize the measured critical dependency—for example, use the existing two-bank fill/compute overlap to reduce measured bank-reuse or downstream-ready bubbles only if the new counters show that those bubbles limit progress. If all other intervals stayed unchanged, reaching the target solely by shortening the 1,201,349-cycle coefficient span would require cutting it to **at most 898,151 cycles**; that is about 39 cycles per 7,806 residual tiles on average, not an assertion that every tile has 39 removable cycles. Preserve exact frame/hash outputs, ownership and physical ACK drain, and repeat stalled and unstalled full-parent tests before accepting any speed claim.

At 125 MHz, 30 fps has a 4,166,667-cycle frame period, but a single 1,553,197-cycle last-input-to-commit result does not establish sustained 30 fps: back-to-back input, buffering, Wi-Fi, output/display pacing and real clock closure remain to be measured independently.

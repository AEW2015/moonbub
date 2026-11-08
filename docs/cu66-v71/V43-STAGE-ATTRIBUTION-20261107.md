# V43/V027 retained physical stage attribution

Recomputed November 7, 2026 from the preserved original KEY/P physical report. No new hardware test or simulation was run for this analysis.

Source: `C:/moon/dev/evidence/v43-v027-network-20261107-run01/NETWORK-RESULT.json`, SHA-256 `ae23f011c2214cd6b9215afb8cdd7731cb78602707535466bf25ca4bda0de4c2`.
Reproducer: `C:/moon/maintenance/streaming-verification-20261107/profile_retained_v43.py`.
Machine-readable results: `C:/moon/maintenance/streaming-verification-20261107/v43-stage-attribution.json`.

All differences below use timestamps from the same receiver clock. Native HUD CPU is nested within admission-to-HUD-valid; do not add it to that interval.

| Receiver-local interval, ms | KEY0 | P1 |
|---|---:|---:|
| Packet completely stored to admission | 0.336 | 0.329 |
| Admission to HUD valid | 1348.312 | 875.694 |
| Native HUD CPU, nested within preceding interval | 319.753 | 210.758 |
| Admission-to-HUD remainder, unattributed | 1028.559 | 664.936 |
| HUD valid to write done | 284.791 | 286.447 |
| Write done to actual readback done | 271.855 | 276.288 |
| Readback done to HUD acknowledged/drained | 0.740 | 0.819 |
| HUD drained to software commit ACK | 2.570 | 3.518 |
| Software commit ACK to observed presentation | 4.891 | 0.271 |
| Total completely stored to observed presentation | **1913.495** | **1443.366** |

## Consequences for next development

1. Continuous buffer/reference correctness remains necessary, but simply replacing the fixed two-frame loop cannot make this diagnostic path interactive.
2. Removing diagnostic readback would save only the measured readback work, about 272/276 ms for these frames. Native HUD CPU alone is already far above a 33.333 ms budget. Re-measure and optimize that computation or choose a verified offload path; do not claim QSPI-only changes solve throughput.
3. The admission-to-HUD remainder is not attributable to FPGA decode from this report. It includes potential waiting for the HUD request, per-word HU extraction via command21, control/QSPI overhead, response checks and scheduling. Add separate stage markers before selecting a fix. Current driver reads HU data through one command per four bytes; its cost is plausible but not separately measured here.
4. Packet upload/staging occurs before the first timestamp in each table column. The 6.782169-second pair total cannot be partitioned into upload versus other unrecorded overhead using this table alone.
5. The first streaming candidate should preserve a full-verification control and expose concise stage summaries. Rate acceptance must use unique physical presentations on varied real content, not a reciprocal of these two diagnostic durations or the FPGA-only simulation rate.

The analysis script validates monotonic stage order, that nested CPU fits within its enclosing interval, and that nonoverlapping phases sum exactly to each stored-to-presentation interval. It preserves the original evidence bytes. These checks establish arithmetic/source binding, not new device performance.

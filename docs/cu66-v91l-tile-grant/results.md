# Bounded reference-tile grant results

All times use actual counters converted at an assumed 100 MHz. The control and candidate use the same C++ workload, seeds, memory corners, original native images and output readiness rules. These are simulation measurements.

| Natural workload metric | Per-line control | Four-line reference grant |
|---|---:|---:|
| Key start → final delta RGB close | 98.83170–98.83727 ms | 97.04288–97.05128 ms |
| Delta start → validated commit | 40.11772–40.12674 ms | 38.32757–38.34091 ms |
| Key RGB start → consumer lease closure | 35.18684–35.19855 ms | 36.86511–36.86639 ms |

Paired completion-interval change: 1.807–1.810% lower. Recommendation: Measured experimental improvement to pair/decode; retain display-latency and read-credit-weighting tradeoff.

The grant limit changes both locality and read-credit weighting (up to four reference lines per display line under continuous contention). It is not an isolated attribution of timing to row activation. The separate directed guard is excluded from performance comparisons.

| Pin command, seed 912901/tAC 2 | Control | Candidate |
|---|---:|---:|
| activate | 47,459 | 36,713 |
| precharge | 40,479 | 29,896 |
| refresh | 13,041 | 12,809 |
| write | 616,872 | 616,872 |
| read | 103,053 | 103,053 |

New eligible display-offer maximum: 311–318 clocks. This measures request acceptance only, with no same-instrument control maximum. Held responses or downstream backpressure can extend wall-clock wait; the fairness guarantee is bounded reference credit under eventual progress.

2,056 directed check entries and 18 causal policy-corruption rejections pass. REF_LINES=1 ordinary outputs match the frozen mux cycle by cycle. Five native modes preserve ten complete RGB outputs (two distinct source images) and all 10,250 RTL SHA jobs, canonical/HUD commitments, physical SDRAM data, accepted quantizer history, immutable display leases and publication. Each delta still uses 7,806 reference tiles /31,224 BL8 reads; no payload buffering or codec syntax/quality changes were introduced.

Unit memory is an explicit behavioral responder. Actual controller/timed pins are covered by native tAC 2/7 runs. Cancel/immediate-mismatch stimulus is source-reviewed in the directed bench; raw yield records alone do not independently reconstruct every unaccepted input. Full RTL HUD, mixed entropy/fallback, actual ESP32/transport timing, fixed-cadence V91m and Series7 mapping/physical/hardware qualification remain open. Hardware 30 fps and complete validated decoding strictly below 10 ms are not proven.

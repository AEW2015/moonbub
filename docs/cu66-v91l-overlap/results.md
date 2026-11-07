# Native overlap measured results

Times use actual cycle fences converted at an assumed 100 MHz. These are behavioral/timed-model results, not an achieved hardware clock or fixed-source frame cadence.

| Metric | Four natural modes |
|---|---:|
| Serial control: key start → final delta RGB closure | 121.85200–121.86702 ms |
| Overlap: same two-source completion interval | 98.83170–98.83727 ms |
| Pair interval reduction | 18.89–18.90% |
| Delta start → validated commit with competing display | 40.11772–40.12674 ms |
| Actual key-display/delta-decode overlap interval | 35.17333–35.18504 ms |

The lower pair interval comes with increased delta decoding latency under contention. The serial control delta took 33.460–33.465 ms; overlap alone does not satisfy a 33.333-ms source-frame slot. The independent Python zero-contention arithmetic is a lower bound and is not used as the measured result.

All five modes preserve two complete source RGB outputs each: ten byte-exact RGB files, 10,250 actual RTL SHA jobs, original canonical/HUD commitments and accepted quantizer history. Per key/delta pair, common memory performs 616,872 WRITE words and captures 824,424 READ words, including 14,058 scratch requests. The SDRAM oracle is populated only by observed pin writes; canonical/pixel preload is absent.

The separate native guard run holds the final key pixel across delta commit plus 17 clocks with external vblank/drain hints asserted. Actual display ownership keeps the old key front while accepted reference advances to the delta, then permits publication only after consumer/physical drain. Its timings are excluded from the natural table. Standalone tests pass 147 checks and independent replay rejects 14 deliberate lease-trace corruptions.

The corpus remains two distinct native source images. Full RTL HUD interpretation/composition, mixed entropy or explicit tested fallback, actual ESP32/transport timing, fixed-cadence V91m and whole-device physical/hardware qualification remain open. Hardware 30 fps and complete validated decoding strictly below 10 ms are not proven.

For the matched seed 912901/tAC 2 case, actual ACTIVATE commands increase from 28,571 to 47,459 (66.11%), while READ/WRITE command counts stay identical. This points to row locality as a next experiment; frequencies alone do not attribute all elapsed time to one cause. Per-bank PRECHARGE counts refer to the pin bank field; A10 precharge-all affects multiple banks.

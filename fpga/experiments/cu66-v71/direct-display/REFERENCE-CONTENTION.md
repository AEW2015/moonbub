# Reference-copy contention: isolated controlled experiment

The frozen BASE direct-display owner misses LCD deadlines under actual same-bank reference reads even without decoder compute or PREPARE work. Both front/ref0?candidate1/HUD1 and front/ref1?candidate2/HUD2 controls produced 669 whole-black lines in one800-line raster, with all other pixels matching the native oracle and no trace loss. The first miss was panel line72, which needed Y group4 while its C and halo groups were ready.

For the first run, C group2 occupied the front DMA from memory cycle268514 to279898. Y4 then began at279899, completed at291345, and its line72 was admitted at291346/filled291832. The pixel deadline was290098: a101.99us budget after Y job start versus114.46us service. This is consistent with page-level scheduling plus service contention; these observations alone did not select a fix.

A second matched pair changed only the reference physical bank from0 to2, with a byte-identical fixture preloaded there. FRONT canonical/HUD0, candidate canonical/HUD1, BASE RTL, actual controller/model, clocks, masks and saturating read?verified write?periodic HUD generator were identical. The generator waits for real completion, so completion counts and issue times can change when service latency changes; this is not a replay of identical timestamped offers.

| Measured result | Reference on FRONT bank0 | Reference on bank2 |
|---|---:|---:|
| Full panel pixels checked |384000|384000|
| Whole-black lines / underruns |669|0|
| Actual READ BL8 commands |50504|57024|
| Actual write beats |147088|170808|
| ACT commands |35913|14510|
| PRE commands |33914|10772|
| Maximum Y group service |114.73us|98.13us|
| Maximum C group service |114.69us|98.10us|
| Maximum backend LCD wait |54clocks|53clocks|
| Completed reference tile reads |4526|5256|
| Completed candidate tile writes |4526|5255|
| Completed HUD word writes |282|328|
| Trace overflow |0|0|

One candidate copy was still in flight at the off-bank stop; its partial physical writes are included in write-beat counts. These fixed-raster prefixes did not finish the first5400-tile Y traversal, so they do not claim complete chroma-copy coverage. They use the same row-major traversal policy as the decoder, without its compute gaps.

Off-bank reference service completed more traffic, removed misses and sharply reduced ACT/PRE commands. This isolates same-bank row-switch overhead in this simulation component. It does not authorize moving the full receiver's reference lease, changing the release memory map, or claim full-P/30fps/hardware readiness. The root has separately selected an isolated grouped-command scheduler experiment; no scheduler or PHY change was made for these controls.

Exact sources, fixture hashes, event windows, command totals and input artifact hashes are in `evidence/reference-correlation02/correlation.json` and `inputs.json`. The two matched proof directories are `direct-reference-base0-fast02` and `direct-reference-offbank-fast01`. The earlier second physical-bank assignment is `direct-reference-base1-fast01`. Every source/model is frozen with its executed command; no `SIMULATION` bypass was used. The conditional lumped model corners are not board/PVT signoff.

Use `scripts/cu66-v71/direct-display/run_direct_reference.py --memory-proof <frozen backend evidence>` to evaluate an isolated successor against the same harness. It verifies the backend source hashes before use. Profile/owner/PHY changes require separate explicit source selection and proof.

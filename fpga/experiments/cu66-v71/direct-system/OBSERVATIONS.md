# DY71 native integration observations

The frozen base direct owner integrates functionally with the real entropy-v4/dequant/BRAM canonical hierarchy and tile-major qualified SDRAM backend. Both fast and slow lumped pin-model corners pass complete KEY/P canonical and HUD readback, software COMMIT-ACK loss/retry, and actual LCD pixel checks. Cadence fails: 596 entire black lines are observed during concurrent P work. No DY71 hardware playback, board timing, routed CDC or 30 fps acceptance is established.

| Native transaction | KEY | Dependent P |
|---|---:|---:|
| Memory-clock cycles | 2,093,762 | 3,307,863 |
| Physical write beats | 428,160 | 428,160 |
| Physical read bursts | 6,240 | 84,744 |
| Cache PREPARE cycles | 113,086 | 455,474 |
| Underrun increase | 0 | 596 |
| Processor COMMIT calls | 1 | 2 |

The P transaction's 33.079 ms is not a demonstrated unique displayed-frame interval. The native HUD CPU service runs outside HDL time, and the display loses lines. Physical write counts match 8,100 canonical tiles × four BL8 × eight words plus 21,120 HUD writes × eight masked words. The RGB writer port is held inactive, its completed-write count is checked zero, and native RGB framebuffer readback is removed; there is no independent physical READ-command classification counter in this first harness.

`full-pin02` and `full-pin-slow01` produce identical outcome lines: 2,441 exact lines, 596 whole black lines and 1,457,871 checked panel pixels. Bounded actual-system controls separately reject seven unauthorized/out-of-order writes, drain two aborted transactions, and reject an early HUD transfer fence without publishing a frame. The prepare adapter's 143 native controls require actual cancellation acknowledgment and protect descriptor-owned contexts from rollback.

The observation-only `full-trace01` reproduces every `SYSTEM_*` outcome line exactly. Its first missing line is physical line 88 of FRONT frame 0 while frame 1 is in BASE_RUN. PREPARE is inactive; Y group 6 is missing while both chroma/halo predicates are ready.

| Local native observation | Memory cycle |
|---|---:|
| Front Cb group 3 starts | 3,261,229 |
| Front Cr group 3 starts | 3,266,897 |
| Front Y group 6 starts | 3,272,579 |
| Line 88 requested | 3,277,727 |
| Line 88 active deadline observed | 3,279,773 |
| Line 88 admitted after Y readiness | 3,282,171 |
| Line 88 final fill word offered | 3,282,657 |

At 10 ns per memory clock, admission takes 44.44 µs from request; final fill is approximately 28.84 µs after the active deadline. The Y job takes about 95.92 µs from start to admission but starts only 71.94 µs before its deadline. The preceding chroma page work occupies the front job until the panel is already around line 84. These readiness/offer timestamps are cycle-quantized, with approximately one memory-clock edge of uncertainty; the delayed synchronized underrun-counter update is a separate timestamp.

An active front page already has priority over PREPARE at every BL8 boundary (`choose_front=f_active`). This first failure therefore does not show a back-PREPARE priority inversion. Full-page Y/chroma scheduling, two-group reuse hazards and actual P reference reads sharing the FRONT's physical canonical bank remain the measured investigation area. Plain candidate-write controls do not duplicate reference-read row traversal. No scheduler, map or buffering fix is selected here.

The trace retains 512 pre-failure and 2,048 post-failure events, not individual explanations for all 596 missing lines. Aggregate front DMA completion observations have maximum 64 clocks; backend LCD-request wait peaks at 56. Aggregate request/admission/fill maxima need further per-line deadline pairing before treating them as exhaustive slack measurements.

Source-bound details are in `qualification-base-v001.json`, `qualification-base-slow-v001.json` and `first-failure-trace-v001.json`. All selected RTL, old RGB variants and failed attempts remain preserved.

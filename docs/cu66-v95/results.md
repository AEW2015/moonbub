# V95 retained-corpus results

The exact-pixel palette lane works in software, but it does not improve the
minimum byte count on this corpus. Keep the existing rate control. These results
cover 457 sources at 720×480, including a precompressed walkthrough family and
synthetic text, noise, motion and scene-pattern fixtures. They are not independent
raw game captures or a live 30-fps host experiment.

## Complete bytes and bypassed work

Every row includes complete frame metadata, palette positions and records, the
actually re-encoded residual complement, HUD and CRC. All rows preserve exact
canonical/reference pixels, HUD, RGB565, content roots and seals. Palette tiles
have no original-coefficient parity claim.

| Policy | Complete bytes, all 457 frames | Change vs control | Residual blocks bypassed | Fraction of original active blocks | Frames ≤49,152 B | Largest frame |
|---|---:|---:|---:|---:|---:|---:|
| Control | 7,781,939 | 0% | 0 | 0% | 457 | 44,546 B |
| P2 | 9,191,946 | +18.12% | 187,957 | 13.92% | 441 | 61,993 B |
| P4 | 9,834,111 | +26.37% | 229,334 | 16.98% | 439 | 63,771 B |
| P8 | 20,083,037 | +158.07% | 594,274 | 44.00% | 228 | 113,135 B |
| E8 | 20,197,263 | +159.54% | 599,041 | 44.35% | 226 | 111,911 B |
| W8 | 37,395,789 | +380.55% | 932,222 | 69.02% | 175 | 203,433 B |
| Minimum bytes | 7,781,939 | 0% | 0 | 0% | 457 | 44,546 B |
| Work budget +5% | 8,052,136 | +3.47% | 29,101 | 2.15% | 457 | 46,202 B |
| Work budget +15% | 8,732,552 | +12.22% | 92,874 | 6.88% | 457 | 49,134 B |

Work5 selects at least one palette in 364/457 frames; work15 does so in
442/457. Their worst relative per-frame increases are 5.000% (cohort 2,
frame 47: 2,240 → 2,352 bytes) and 14.995% (cohort 1, frame 61:
3,728 → 4,287 bytes). Selected work15 records include 59,132 packed,
29,917 prediction/run, 3,813 reused-palette and 12 escape records. RAW is tested
by directed fixtures; its 70-byte cost including its directory prevents
selection under these profiles' largest 64-byte record threshold.

Work5/work15 impose their allowance on each complete frame, capped at 49,152
bytes; aggregate overhead can be lower than that allowance. The 1,350,695
original active residual blocks are the denominator above. Selecting a palette
bypasses a residual block, but this count is not measured FPGA cycles, decode
latency, DSP use or SDRAM bandwidth. Existing hardware zero-block shortcuts may
already remove some of that work. Uniform palette rows are diagnostic research
profiles; their oversized frames are not normal-cap successes.

Minimum-byte selection chooses no palettes on all 457 frames, even when mixing
plane profiles. Its total equals the V92 context-minimum control. V94's separate
rate-aware rANS minimum was eleven bytes smaller over the corpus; V95 does not
combine rANS with pixel palettes. No representation here changes the target
image quality, and no HEVC/AV1 quality-superiority claim follows from these data.

## Qualification and reproducibility

The [native index](../../experiments/python-gamebub-v95/native/index.json)
records 8,226 real plane variants, 2,542,828 palette records and two byte-identical
native campaigns. An independent Python reader checks every emitted palette
tile against frozen canonical pixels; 263,176 records exercise palette reuse.
The [Python unit receipt](../../experiments/python-gamebub-v95/python/index.json)
retains 5,967 checks covering valid cases, malformed inputs, truncations,
padding and trailing data. The native unit fixture set has 206 checks. The [full-frame receipt](../../experiments/python-gamebub-v95/wire/results.json)
qualifies 4,113 complete native reconstructions across nine policies with exact
fallback-coefficient and palette-pixel hashes as well as full-image commitments.
The [wire recovery receipt](../../experiments/python-gamebub-v95/wire/tests.json)
records 54 bounded malformed/reject/recovery, replay and next-frame checks, including
late semantic rejection. The directed all-RAW key is 559,046 bytes with 7,806 palette tiles and zero
residual tiles. It uses only the explicit research receiver and cannot demonstrate
cap fit. The strict receiver rejects 49,153-byte transport records.

The [summary](../../experiments/python-gamebub-v95/summary.json) independently
recounts archived packet lengths, CRCs, plane extents, record-kind counts,
residual complements and byte budgets. The independent selection receipt checks
bounded profile choices against exhaustive enumeration in 128 scenarios
(216 tuples each; 56,448 comparisons). Failed development
attempts, successful attempts, source snapshots and their hashes are retained.

All-six-profile native preparation in the repeat costs a median **63.15 ms** per
source, p95 **140.03 ms**, maximum **251.49 ms**, with about **9 MiB** peak native
RSS. It includes frozen coefficient decoding, histogram/run/reuse searches and
actual fallback encoding for discarded candidates. It excludes capture,
DCT/target reconstruction and source generation. Python checking is separate.
These diagnostic host measurements do not qualify a production 30-fps encoder.

## Decision and open gates

V95a–c are qualified as bounded software research on the retained corpus.
V95d records a negative rate result and retains conditional work-budget
experiments without RTL/product promotion. The direct candidate writer avoids
an additional full-frame palette staging image, but native heap allocation is
not a BRAM/SRAM/SDRAM implementation proof. Hardware must still account for
record buffering, tile state, masks, packet storage, candidate images and ports.

Next, inventory actual addressed COPY/prediction/constant traffic and display
leases under V96, then integrate only measured winners. Palette RTL, firmware
negotiation, broader captures, physical mapping and calibrated end-to-end
latency remain open. Neither sustained hardware 30 fps nor validated complete
FPGA decoding below 10 ms has been demonstrated by V95.

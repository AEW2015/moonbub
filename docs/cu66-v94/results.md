# V94 measured results

**Partial V94: inline byte-rANS software and a real RTL category kernel pass. No product promotion.**

- 457 source frames; 16,452 component packets and 5,484 complete CS94 reconstructions.
- 86,444,480 intended coefficients retained; exact canonical/reference pixels, HUD, RGB565, roots and seals.
- 185 independent Python grammar checks plus 4,608 native packets/all 256 selectors; 151 strict wire recovery checks.
- Two full baseline campaigns reproduced all 12,339 packet bytes and per-packet operation metrics exactly.

| Policy | Complete bytes | Max frame bytes | Fits 49,152 B | ANS categories | Inline tables |
|---|---:|---:|---:|---:|---:|
| all_AB | 7,787,241 | 44,552 | 457/457 | 0 | 0 |
| all_BR | 8,326,610 | 49,785 | 456/457 | 0 | 0 |
| rans2_s8 | 8,470,811 | 48,581 | 457/457 | 11,435,381 | 9,597 |
| rans2_s9 | 8,450,939 | 48,470 | 457/457 | 11,435,381 | 9,597 |
| rans2_s10 | 8,443,388 | 48,423 | 457/457 | 11,435,381 | 9,597 |
| rans4_s8 | 8,510,549 | 48,665 | 457/457 | 11,435,381 | 9,597 |
| rans4_s9 | 8,490,614 | 48,559 | 457/457 | 11,435,381 | 9,597 |
| rans4_s10 | 8,483,096 | 48,510 | 457/457 | 11,435,381 | 9,597 |
| byte_min | 7,781,939 | 44,546 | 457/457 | 0 | 0 |
| v92_byte_min | 7,781,939 | 44,546 | 457/457 | 0 | 0 |
| rate_ans2_s10 | 8,423,099 | 48,373 | 457/457 | 11,435,381 | 9,597 |
| rate_byte_min | 7,781,928 | 44,546 | 457/457 | 797 | 1 |

## Compression decision

The initial six rANS variants use frozen BR-optimal Rice parameters and do not improve the minimum-byte frontier once inline models, descriptors and states are charged.
A separate bounded rate-aware parameter search evaluates 150,810 legal k candidates using normalized category entropy plus literal bits, then actually encodes the selected pair and keeps the frozen rANS stream if it is smaller. All search/discarded work is timed. This is not a proof of globally optimal rANS bitstreams.
Rate tuning saves **20,289 bytes** versus the frozen N2/S10 uniform rANS control. The guarded local minimum saves only **11 bytes across all 457 complete frames** versus V92: one 797-symbol chroma-DC context at cohort 0/frame 12 changes from a 228-byte AB stream to a 217-byte rANS stream. This is negligible compression benefit, not a reason to deploy another codec path.
The tuned uniform rANS control still uses **+96,489 complete bytes** versus BR. Each homogeneous frame carries 21 inline models (672 bytes), plus 12 descriptors and initial state words. Table-free or cached estimates are not substituted for actual wire costs.
There is a tail-size tradeoff: tuned uniform rANS has a **48,373-byte maximum**, fitting all 457 sources; uniform BR reaches **49,785 bytes**, exceeding the cap on one source. The rANS mean-byte cost is 1.159% higher. This is a cap-management observation on this corpus, not a latency or general compression win.
Keep the existing control. Cached-model, trained-model or tANS studies may change the tradeoff, but their protocols/costs are not implemented here. The corpus is one related precompressed walkthrough family, not independent raw captures or a generalization benchmark.

## Actual RTL boundary and cycles

The repaired RTL passes **203,019** main-sweep category/state/cursor checks, including **92,427** from actual contexts. This includes the optimized 797-symbol winner. Fifty-five vectors cover S=8/9/10, N=2/4, one/two models, empty/rare streams, 0/1/2 refills, two stall seeds and no-stall controls.
The no-stall sweep measures **278,096 clocks for 67,673 categories**, including refills. Every row satisfies `4×categories + refill bytes + input stalls + output stalls`; model/state preload is separately measured. One physical update engine serves the interleaved states.
Independent math replay verifies all 67,673 vector categories. Three deliberately corrupted expected-category/state/cursor files fail the actual RTL checker. Eight malformed configuration/stream controls reject; three active cancellation retries and two same-edge configuration/reset races pass.
Review exposed a same-edge cancellation handshake bug. The failing source/log/VCD are retained; the fix suppresses every ready/valid handshake and done while reset/abort is asserted. The complete regression, including the unchanged strengthened checker, passes afterward.
A separately compiled no-refill bypass variant preserves the entire RV94 workload and all 203,019 main-sweep outputs. Matched no-stall clocks fall **278,096 → 217,826**, saving **60,270 (21.67%)**. Each case saves exactly its zero-refill-category count; nonzero-refill paths keep their service. All malformed/recovery/cancel tests and three corrupted-oracle controls also pass on the new binary.
The actual-source subset is **19 context encodings / 30,809 categories**, with clocks **130,622 → 107,198 (17.93% fewer)**. The remaining 36 vectors are synthetic; combining them yields the larger 21.67% figure. These context encodings cover a small selected workload, not sustained complete video frames.
The bypass moves normalization detection onto the multiply/update path. Its routed clock may be lower; this is a cycle reduction at the component boundary, not an achieved-time or full-frame speedup. Keep the staged control until matched 7-series timing/resource results exist. Stalled-seed runs establish correctness only because their credit timing evolves with the changed clock count.
Packet/table-ID/CRC parsing, literals, coefficients, pixels, HUD, physical memory/display and validated frame publication are outside the RTL kernel. Native complete-frame results do not execute that kernel. No complete-frame FPGA latency, routed clock, DSP mapping or hardware 30 fps is measured.

## Host and resource accounting

Baseline candidate generation: median **7.044 ms**, p95 **18.035 ms**, maximum **21.374 ms** per source on this Linux host. Rate-search campaign: median **5.739 ms**, maximum **18.151 ms**. These use different candidate sets and are not a matched host-speedup comparison.
Generation includes source coefficient extraction, all prepared/discarded candidates, actual serialization/hashes and frozen encoder internal verification. Live capture/DCT and Sunshine/ESP32 operation are excluded. Native/Python RSS observations and independent verification wall time are in the retained reports.
The kernel declares 704 model-payload bits and 128 lane-state bits, excluding control/multiply registers and the rest of the design. Its sixteen parallel comparisons have real read/fanout costs. Width feasibility for a DSP48E1 is not physical mapping or board fit.

## Remaining V94 work

V94a/b are qualified only for this inline byte-rANS scope. V94c remains a symbol-kernel checkpoint; tANS, fixed calibration-only models, acknowledged caches, complete frame RTL integration and physical cycle/port/resource qualification remain open. V94d is not promoted. V91l/V92d and hardware 30 fps/validated under-10-ms full decoding remain open.

[Grammar/reproduction](README.md) · [RTL contract](../../fpga/experiments/cu66-v94-rans/README.md) · [Machine summary](../../experiments/python-gamebub-v94/summary.json)

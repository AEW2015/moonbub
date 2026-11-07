# V93 measured results

**V93a–c software evidence is qualified for the retained corpus. Product promotion remains open.**

- 457 sources, 1,371 planes and 6,855 actual component packets.
- 86,444,480 coefficient values match; native and independent Python verify all four alternatives.
- 4,113 complete CS93 packets preserve exact coefficients, canonical/reference pixels, HUD, RGB565, roots and seals.
- 1,710 independent grammar checks, including all 256 selectors; 48 complete-protocol checks.

| Policy | Complete bytes | Max bytes | Frames fitting 49,152 B | Arithmetic decisions | Plain bit reads |
|---|---:|---:|---:|---:|---:|
| all_AB | 7,787,241 | 44,552 | 457/457 | 37,656,819 | 0 |
| all_BR | 8,326,610 | 49,785 | 456/457 | 0 | 37,656,819 |
| prefix_suffix | 8,028,689 | 46,992 | 457/457 | 22,104,997 | 15,551,822 |
| small_group | 9,245,507 | 54,443 | 449/457 | 0 | 34,617,490 |
| byte_min | 7,781,939 | 44,546 | 457/457 | 37,394,255 | 262,564 |
| v92_byte_min | 7,781,939 | 44,546 | 457/457 | 37,394,255 | 262,564 |
| v92_work15 | 8,307,824 | 49,098 | 457/457 | 464,660 | 37,192,159 |
| work5 | 8,159,882 | 46,757 | 457/457 | 7,818,172 | 29,790,574 |
| work15 | 8,886,928 | 49,152 | 457/457 | 347,923 | 35,054,036 |

Uniform HY replaces **15,551,822 arithmetic decisions (41.30%)** with plain suffix reads versus uniform AB, at **3.101% more complete bytes**. All 457 HY frames fit the target cap; maximum 46,992 bytes. This is the useful prefix-bypass tradeoff, rather than a new compression gain.
Uniform SG uses **8.07% fewer plain bit reads** than BR but **11.036% more complete bytes**, charging 202,199 group headers (1,213,194 bytes). Eight SG frames exceed the target cap. Smaller Rice payloads alone are an insufficient selection criterion.
Exact minimum-byte selection changes V92 by **+0 bytes**. Neither the all-suffix bypass rule nor fixed 32-event Rice grouping improves the minimum-byte frontier on these inputs.
At the same complete-byte allowance, the bounded work15 policy removes **116,737 (25.12%)** remaining arithmetic decisions versus the frozen V92 work15 control, with **+579,104 bytes (+6.971%)**. This compares actual work counts; plain reads, initialization and group metadata remain real work. It is not a measured FPGA speedup.

## Host preparation and search

Native generation per frame: minimum **0.556 ms**, median **5.915 ms**, p95 **15.532 ms**, maximum **19.502 ms** on this Linux host. All four method preparations, five assemblies/hashes and discarded alternatives are included; source coefficient extraction and the frozen encoder internal verification are included.
Native collector peak RSS is **6,648 KiB**. It excludes the parent Python/archive process and live application memory. The native report also records process-family RSS observations separately.
The two bounded work-policy searches together take median **1.664 ms**, maximum **3.221 ms** per frame. Maximum proposals in a stage: **512**. Pareto truncation occurred in **1282** stages; results are not globally optimal certificates.

These are host component timings. Live capture/DCT, Sunshine cadence, ESP32/QSPI, physical shared SDRAM/display service, parser setup and achieved FPGA clock are unmeasured.

## Decision

Retain the fixed suffix-bypass method as a conditional work-proxy candidate. Keep V92 as the supported reference and reject fixed SG32 as the default size policy on this corpus; its group headers outweigh the local parameter benefit. No new method is promoted into RTL or the application firmware by this study.
The work15 proxy selects 2,196 SG streams and charges their bytes, but does not price 134,017 group-header parse operations as calibrated cycles. Its lower arithmetic/plain counts cost extra wire traffic; do not adopt that objective as a latency policy before adding measured metadata/setup and shared-memory costs.
The homogeneous controls use a diagnostic 2-MiB receiver where needed; only the selected policies and frozen V92 controls use normal 49,152-byte admission. Cap-fit counts above are separate from diagnostic acceptance. RAW fallback is tested, but no frame-level overflow recovery profile is qualified for arbitrary future content.
The suffix-bypass rule and group size were fixed before observation. Histograms are descriptive, not a trained held-out policy. All 457 sources remain one related precompressed walkthrough family; independent raw captures and matched-quality standard-codec comparisons remain open.
Next qualify any proposed prefix/suffix hardware adapter against the actual memory/display bottleneck and complete frame goldens. V91l, V92d, sustained hardware 30 fps and complete validated under-10-ms decoding remain open.

[Machine-readable summary](../../experiments/python-gamebub-v93/summary.json) · [Grammar and reproduction](README.md)

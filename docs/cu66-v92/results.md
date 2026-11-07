# V92 measured results

The retained software campaign passes; **V92a–c are qualified for this corpus and V92d remains open**.

- 457 sources, 1,371 plane chunks and 21,936 actual EC92 candidates.
- 86,444,480 coefficient values match; native decodes every selector pattern, and independent Python decodes both alternatives for every distinct context.
- 1,828 complete CS92 packets reproduce exact coefficients, canonical/reference pixels, semantic HUD, RGB565, content root and seal.
- 1,871,872 frame combinations checked against bounded selection, plus the independent synthetic selector tests.
- 187 independent grammar checks and 20 complete-protocol checks pass. Native fixtures add 80 roundtrips and 4,656 rejections.

| Policy | Total complete bytes | Maximum frame bytes | AB decisions | BR bit reads |
|---|---:|---:|---:|---:|
| context_byte_min | 7,781,939 | 44,546 | 37,394,255 | 262,564 |
| context_work5 | 8,108,288 | 46,500 | 10,324,421 | 27,332,398 |
| context_work15 | 8,307,824 | 49,098 | 464,660 | 37,192,159 |
| whole_plane_work15 | 8,276,371 | 48,750 | 1,444,956 | 36,211,863 |

Frozen CS88 all-AB38 complete bytes: **7,784,499**. EC92 minimum-byte selection changes this by **-2,560 B (-0.0329%)**, including its six extra header bytes per frame.
The matched 15% contextual policy removes **980,296** additional adaptive decisions versus whole-plane selection, changes total bytes by **+31,453**, and changes 445 frame choices. Plain Rice bit reads remain charged.

## Host preparation and bounds

Linux native candidate generation: minimum **0.412 ms**, median **4.751 ms**, p95 **12.653 ms**, maximum **15.400 ms** per frame. This includes both coders, discarded assemblies/hashes and frozen coefficient extraction, with encoder internal parity validation included.
Native collector peak RSS: **7,016 KiB**. This covers the helper process, not all Python/archival memory or a whole Sunshine session.
Bounded Python selection has median **0.421 ms**, maximum **1.429 ms**, and maximum **2816** proposed states in this corpus. Exhaustive verification and full-frame assembly/CRC/validation are outside that selection timer.

No live capture/DCT, Sunshine cadence, ESP32 firmware, QSPI DMA, physical SDRAM or FPGA timing is measured here. The corpus is one related precompressed walkthrough family in four reset histories, not independent raw gameplay captures.

## Decision and next gate

Keep EC92 as a research candidate. Its compression gain is small; the useful result is the exact byte/work tradeoff with bounded host search. The supported V91 RTL remains BR88-only. Before promotion, charge an implemented mixed arithmetic/Rice adapter against the actual shared-memory/display service, then rerun complete-path goldens and fixed 30-Hz source releases. V91l, hardware 30 fps and complete validated under-10-ms decoding remain open.

Machine-readable [summary](../../experiments/python-gamebub-v92/summary.json) binds the selected immutable evidence. Reproduction, wire grammar and scope are in the [README](README.md).

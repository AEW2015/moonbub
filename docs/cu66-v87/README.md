# V87: accepted-state compression and a consumer-coupled decoder model

V87 advances the application-specific codec in three connected areas: actual
quantizer-state compression, a causal frontend/reconstruction/memory schedule,
and a bounded COPY-alias layout. The quantized 720×480 picture is unchanged.
No FPGA RTL, ESP32 firmware or deployed Sunshine changes are included.

## Complete packets: quantizer state reuse works on this corpus

The explicit CS87 profile replaces the fixed raw quantizer map with a bounded
block supporting raw, uniform, RLE, required-cell and accepted-map reuse modes.
The native receiver reconstructs the new packets directly and publishes cache
state only after the reconstructed content root and seal succeed.

**457 sources × two configurations = 914 actual packets** match the qualified
coefficients, canonical pixels, HUD, rendered RGB565, C2 root and frame seal.
The independent auditor reconstructs every packet SHA and verifies shortest
method choice and inheritance eligibility.

| Whole-plane configuration | V86 complete bytes | V87 complete bytes | Saved versus V86 |
|---|---:|---:|---:|
| Fixed grouped COPY | 7,930,953 | 7,784,499 | 146,454 |
| Matched all-visible | 8,008,725 | 7,862,271 | 146,454 |

Original CU66 totals 7,946,811 bytes. Fixed grouped COPY is now **162,312 bytes
(2.04%) smaller overall**. Median/max packet size is 16,532/44,546 bytes. Both
tested configurations fit 49,152 bytes on all sources. Link overhead is excluded
equally; no additional image-quality loss is introduced.

Each configuration selects full-map RLE for 20 keys and inherited accepted maps
for all 437 deltas. Quantizer metadata totals 8,012 bytes versus 154,466 bytes
for raw maps. The stable required quantizers in this walkthrough enable the
saving; changing quantizers can reduce it. A raw fallback costs 354 bytes, which
is 16 bytes larger than the old map. It is not a universal packet-size bound.

The [37 cross-language/native checks](../../experiments/python-gamebub-v87/quantizers/tests.json)
include all methods, geometry, malformed inputs, late content failure,
retention, recovery, replay and alternate cache branches. See the
[quantizer grammar and actual-packet results](quantizers.md).

## Timing: producers now wait for real consumers

The coupled study preserves fixed CS86 as its control. It schedules actual
re-encoded shared fetch/context work in the same graph as dequantization,
inverse/reconstruction, pixel memory, metadata, C2 hashing and publication.
Eight coefficient slots are released by their consuming inverse/map tasks;
entropy emission alone cannot release them. Reference/inverse slots and four
output groups retain their own lifetime bounds.

The model charges complete packet CRC and metadata byte scans and explicit
dequant work. It retains conditional LOW/HIGH operation costs, nominal
64-cycle arithmetic stages and an assumed 100 MHz. Details and the completed
campaign table are in [the coupled study](coupled.md).

All **457 sources × six configurations = 2,742 schedules** completed. The
zero-frontend control matches the frozen V84 result exactly on all sources.
Two-lane conditional results are:

| Cost/service assumption | Median | Maximum | Sources strictly below 10 ms |
|---|---:|---:|---:|
| LOW, current memory service | 8.87090 ms | 12.82457 ms | 350/457 |
| HIGH, current memory service | 9.37516 ms | 18.58340 ms | 269/457 |
| LOW, 20% periodic memory reservation | 10.97240 ms | 15.63288 ms | 166/457 |

All modeled single-frame cases fit a 33.33-ms release period, but this is not
a continuous transport/display schedule or sustained hardware 30-fps proof.
Five full campaign witnesses pass independent timeline/credit audits; all
schedules retain their own in-process audits and timeline digests.

Compared source by source, two lanes improve 143 LOW cases and leave 314
unchanged; they improve 281 HIGH cases and leave 176 unchanged. No modeled
source regresses. The paired LOW median gain is zero, consistent with the
backend limiting many frames even when entropy arithmetic gets faster.

On the difficult cohort-3/frame-50 witness only, hypothetical 12-cycle memory
service still gives 10.68330 ms with LOW costs and 17.26770 ms with HIGH costs
without reservation. Four separate witness sensitivities are retained; these
are not additional full-corpus configurations. Faster memory alone does not
close the modeled gap on that source.

This remains a conditional model. Qualified HUD entropy/semantic hashing,
actual parser/transfer ports, physical controller/refresh behavior, continuous
display, asynchronous recovery and ESP32/transport work remain outside the
timing proof. CS87/all-visible packet correctness does not supply coupled
timing for those profiles. The model's conservative data-staging allowance is
9,216 logical bytes, with working state, descriptors, compressed input, maps,
ports and RAM rounding extra.

## Memory traffic is a distinct performance constraint

The actual frozen command trace requires up to **11.70192 ms of memory busy
work** under 18-cycle reads and 16-cycle writes at 100 MHz. Its necessary
aggregate bound with 20% reservation is 14.62740 ms, before dependency stalls.
Even hypothetical 12-cycle service leaves 40 sources outside the reserved
10-ms memory-work budget. Faster entropy alone cannot remove this floor.

The [memory study](memory.md) identifies COPY store avoidance plus controller
service as a combined target. Its alias rows are explicitly traffic
counterfactuals, not hardware or scheduled completion results.

A separate [three-slot tile-alias prototype](alias.md) proves a functional
layout contract on all native sources under two presentation schedules and
against 1,024 seeded symbolic updates. Accepted reference and held scanout
leases protect their physical slots; COPY aliases an accepted slot, while a
third slot permits provisional writes and abort. It uses 1,555,200 logical
pixel bytes plus 6,075 bytes for three packed descriptor maps, before other
metadata or physical RAM costs.

Its write comparator is dense write-every-tile, not the frozen residency
workload. Descriptor accesses, dirty-hash reads and indirect display gathers
must be traced and priced before assigning any latency saving to this layout.

## Next milestone

Integrate aliases into the actual command trace, retain consumer backpressure,
and calibrate the two-lane architecture and arithmetic stages in RTL. This
targets an application-specific advantage through accepted-state reuse and
bounded memory access, while preserving exact decoded output.

**Sustained hardware 30 fps and complete validated decoding below 10 ms remain
open.** The 457-source walkthrough family, multiple encodings and synthetic
updates do not replace distinct-source sustained hardware tests or establish
HEVC/AV1 superiority.

- [Next implementation plan](next-steps.md)
- [Evidence, reproduction and limits](evidence-scope.md)
- [Independent packet audit](../../experiments/python-gamebub-v87/quantizer-audit.json)
- [Independent alias audit](../../experiments/python-gamebub-v87/memory/alias-audit.json)
- [Audited combined results](../../experiments/python-gamebub-v87/summary.json)

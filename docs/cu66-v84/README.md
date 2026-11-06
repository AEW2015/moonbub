# V84: native entropy work, finite staging and application-specific mode coding

V84 adds a concrete operation-metadata format and removes two optimistic V83
model assumptions: immediate tile-mode availability and unrestricted
intermediate staging within admitted groups. The existing quantized 720×480
picture and residual coding remain the data baseline. No RTL, ESP32 firmware or
deployed Sunshine encoder changes are included.

## Application-specific metadata result

The Python encoder and independent parser represent COPY_REF, CONST128 and
RESIDUAL operations exactly for all **457 native sources**. V2 exploits the
fixed hidden-tile profile: CONST tiles are implicit, and only 7,806 visible
positions need COPY/RESIDUAL bits. Keys use an implicit operation map; deltas
choose a visible bitset or run encoding.

| Operation-map format | Minimum block | Median block | Maximum block | Total over corpus |
|---|---:|---:|---:|---:|
| V1: general three-operation map | 158 B | 1,143 B | 2,045 B | 503,553 B |
| V2: implicit hidden tiles/key map | 20 B | 996 B | 996 B | 384,102 B |

V2 saves **119,451 bytes, or 23.72% of this operation metadata**, with identical
native operation arrays. Its 20-byte header and at-most-976-byte body have exact
geometry, length, padding, method and key checks. CRC32 covers the header prefix
and body. Each version passes 28 checks; the retained V2 vectors include a real
RLE case containing a 128-position run.

This block is **metadata, not a complete video codec**. Adding it to unchanged
AB38 streams adds bytes and does not eliminate their entropy work. It lacks a
complete frame/reference/generation envelope; residual streams still need an
actual encoder/decoder and capability negotiation. CRC is not authentication.
The fixed hidden-mask identity is part of this research profile, not support
for arbitrary geometry or crops.

## Native front-end and finite-credit results

The new interleaved native observer validates **1,371 coefficient planes**
against the frozen decoder and checks original packet/canonical/HUD/display
digests. All **3,701,700 zero-coefficient mask bits** match V82. It observes
43,436,569 arithmetic decisions and 35,844,140 renormalizations. These are
primitive counts, not measured FPGA clocks. LOW/HIGH operation weights are
explicit sensitivity assumptions, not physical lower/upper bounds.

The full study evaluates **457 sources × 8 configurations = 3,656 conditional
Python schedules** across four independently reset histories. All use four
16-tile output groups, one SHA-256 lane and nominal 64-cycle inverse and
reconstruction tasks. Times assume 100 MHz. Current service intervals are
18 clocks/read BL8 and 16 clocks/write BL8.

| Model configuration | Minimum ms | Median ms | Maximum ms | Conditional sources below 10 ms |
|---|---:|---:|---:|---:|
| Frozen V83 control | 2.91192 | 8.45600 | 11.70392 | 413/457 |
| 64 credits/stage, zero arrival cost | 2.91192 | 8.45600 | 11.70392 | 413/457 |
| 8 credits/stage, zero arrival cost | 2.91192 | 8.45600 | 11.70392 | 413/457 |
| 2 credits/stage, zero arrival cost | 2.91192 | 8.45600 | 11.70392 | 413/457 |
| 8 credits/stage, native work with LOW weights | 2.91192 | 8.57072 | 16.73300 | 306/457 |
| 8 credits/stage, native work with HIGH weights | 2.97240 | 11.52300 | 27.92361 | 186/457 |
| LOW, 20% memory reservation | 3.67096 | 10.69000 | 18.18257 | 173/457 |
| LOW, hypothetical 12-cycle read/write service, 20% reservation | 2.59800 | 7.87480 | 16.27041 | 315/457 |

All three zero-arrival capacities match the V83 control **exactly on every
source**, not just their medians. That isolates the effect of bounding staging
under instantaneous mode availability. Two-credit timing with native entropy
work was not tested, so it cannot inherit the eight-credit results.

Eight reference/inverse/coefficient slots plus output groups reserve
**7,168 logical bytes**. Two slots require 4,864 bytes; 64 slots require
28,672 bytes. V83's 20-KiB reference/inverse/output estimate excluded
coefficients; adding comparable coefficient storage makes its four-class
reservation 28 KiB. Tree/maps, inverse working registers, dequant staging,
hashes, descriptors, compressed data, control, ports and RAM rounding are extra.

The modeled worst LOW case is cohort 3 / source 50: isolated entropy work is
13.75352 ms and coupled completion is 16.733 ms. This motivates measuring and
optimizing front-end execution and overlap as well as memory service. It does
not establish how fast the existing RTL runs. The 20% reservation restarts at
phase zero per source and is not continuous LCD/refresh/deadline qualification.

## Evidence and next experiment

The final verifier checks all rows against native identities, V82 work/content
commitments and V83 controls, including current/archive/artifact hashes. Four
complete witness DAGs are independently reconstructed and their timelines and
credit lifetimes reaudited. Other schedules retain in-process audits, timeline
hashes and summaries. **557 credit checks and 9 independent auditor checks**
pass, in addition to native entropy and both metadata-format checks.

The next codec prototype should actually re-encode RESIDUAL-only streams beside
V2 metadata and measure complete bytes and decode work. Separately, trace each
arithmetic context and model two/four range-decoder lanes under the existing
bitstream, retaining lookahead, predictor order and bounded rendezvous. Do not
predict that speed by dividing aggregate work by lane count or deleting
COPY-attributed work from the old adaptive stream.

Ingress/QSPI/ESP32 execution, outer validation/HUD semantic work, physical bank
leases, COPY transfer ports, actual FIFO/RAM timing and target fit remain open.
The software future-task graph also needs bounded streaming hardware control.
This one-walkthrough-family corpus does not qualify sustained 30 fps, full
validated FPGA decoding below 10 ms, or HEVC/AV1 bitrate/quality superiority.

- [Application-specific codec and hardware plan](next-steps.md)
- [V2 operation-map grammar and vectors](mode-map-v2.md)
- [V1 metadata comparator](mode-map.md)
- [Native entropy observations](entropy.md)
- [Credit admission and lifetime contract](credits.md)
- [Explicit cost assumptions](cost-assumptions.md)
- [Evidence and reproduction](evidence-scope.md)
- [Audited results](../../experiments/python-gamebub-v84/summary.json)

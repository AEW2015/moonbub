# V85 actual residual-only stream and independent picture receiver

V85 moves beyond a mode-map-only experiment. It actually re-encodes the native
quantized coefficients for RESIDUAL tiles, combines them with COPY/CONST
metadata and unchanged encoded HUD, and sends complete CS85 research packets
to a separate native receiver. The receiver decodes the new chunks, scatters
coefficients, reconstructs native pixels, and recomputes C2 content/HUD seals
before publishing state. It does not repack a synthetic original CU66 packet
for the old complete-frame decoder.

All **457 sources × four chunk profiles = 1,828 packets** pass exact full
coefficient, canonical-picture, semantic-HUD, rendered-RGB565, content-root and
frame-seal comparisons. Resolution and quantized picture quality are unchanged.
This is a functional host prototype, not FPGA RTL or an ESP32 implementation.

## Actual complete application-packet bytes

The following counts include the 256-byte CS85 header, V2 mode map, 338-byte
quantizer map, plane/chunk directories, actual AB38 packets including their
headers/termination/CRC, original encoded HUD, and final outer CRC. They exclude
link/network transport overhead for both formats. The original 457 CU66
application packets total **7,946,811 bytes**, median 16,851 and maximum 44,016.

| Maximum residual tiles/chunk | Median packet | Maximum packet | Corpus bytes | Fits original 49,152-byte budget |
|---|---:|---:|---:|---:|
| 16 | 34,669 B | 88,797 B | 15,455,528 B | 324/457 |
| 64 | 21,750 B | 56,700 B | 9,959,656 B | 447/457 |
| 256 | 18,217 B | 48,306 B | 8,551,380 B | 457/457 |
| Whole residual plane | 17,133 B | 44,981 B | 8,071,867 B | 457/457 |

**The new format does not yet win whole-stream size.** The smallest profile is
125,056 bytes (**1.57%**) larger in aggregate than the original packets; 52
individual sources shrink and 405 grow. Tiny chunks introduce real reset,
header, termination and directory overhead. A 16-tile C2 hash group does not
require resetting the entropy codec every 16 residual tiles.

The separate matched-encoder control isolates COPY filtering more fairly:
whole-plane AB38 components fall from **4,618,536 to 4,265,737 bytes**, saving
352,799 bytes (**7.64%**). All 437 delta sources improve and 20 keys remain
equal under those matched encoding rules. The actual V2 maps total 384,102
bytes, which already exceeds that isolated component saving. This observation
does not establish a complete matched-envelope comparison: the all-visible
control would itself have a different, much smaller mode map.

The encoder uses per-residual-tile DC resets and the frozen minimum-uncoded-Rice
parameter rule. Original native packets may choose other full/compact
representations. Therefore COPY alone is not the isolated cause of differences
against the original CU66 wire format. All four candidates are retained.

## Receiver correctness and transaction evidence

The independent CS85 receiver verifies explicit version/geometry, exact bounded
lengths, mode-map CRC, every AB38 chunk's grammar and CRC, quantizers,
frame/reference/generation, semantic HUD, C2 root and C2 seal. Accepted state
changes only after all checks. Exact last-packet replay returns the already
accepted result; changed stale packets reject.

**23 real native receiver cases** exercise corruption, resealed malformed
headers/maps/chunks, quantizer errors, wrong references/content/HUD/seals,
truncation, missing references, stale packets, retained-state recovery and
idempotent replay. They use the same receiver binary as the full positive run.
This is synchronous software transaction evidence; mid-decode abort, physical
write drains, hardware bank leases and fragmented transport remain untested.

The research parser admits at most 2 MiB and buffers packets and coefficient
arrays on the host. This is not an FPGA or ESP32 RAM budget. Compatibility
against the old 49,152-byte application-packet bound is reported separately;
oversized candidates were not silently truncated or removed. CRC and unkeyed
content hashes are integrity checks, not sender authentication.

## Per-context front-end experiment

The native observer splits shared work and four arithmetic contexts while
preserving **every V84 primitive count on every tile**, plus all 1,371 native
coefficient planes and original picture/HUD/display digests. Under LOW weights,
arithmetic work is uneven: DC 17.81%, AC1 43.41%, AC2 34.12%, AC3 4.65%.

The prospective model preserves per-context order, a shared fetch/control
server, tile rendezvous and an eight/64-tile admission window. It tests 25
selected sources, including the V84 worst case, with **300 schedules and 18
synthetic cases**. Eight-tile-window, front-end-only results are:

| Arithmetic lanes | LOW median / max | HIGH median / max |
|---|---:|---:|
| 1 | 3.51731 / 13.14572 ms | 6.73302 / 25.17113 ms |
| 2 | 2.22879 / 7.39914 ms | 4.25804 / 14.17027 ms |
| 4 | 2.10841 / 6.76155 ms | 4.02163 / 12.91737 ms |

These are **selected standalone model results on the existing bitstream**,
not full-corpus parallel-decoder timings. Fetch and arithmetic are decoupled
even in its one-lane case, so it is not a direct V84 speedup measurement.
The model batches each context/tile's fetch then arithmetic rather than tracing
every RTL instruction. It cannot be combined with CS85 byte results to claim
an implemented end-to-end speed. Two lanes are the useful first controlled
implementation comparator; dividing aggregate work by four is unjustified.

## Next codec step

Keep whole-plane/large entropy streams as controls, reduce redundant envelope
and mode-map costs under an explicitly new profile, and measure complete
matched-envelope controls. Evaluate two arithmetic lanes with bounded
coefficient/reference/output handshakes, actual fetch/CRC/dequant timing and
continuous memory/display traffic. Only then combine the new residual grammar
with that measured decoder architecture.

No FPGA fit/Fmax, ESP32 throughput, sustained distinct-source 30 fps, validated
full FPGA decoding below 10 ms, or HEVC/AV1 superiority milestone is closed.

- [Next implementation and codec plan](next-steps.md)
- [Wire format and bounds](wire-format.md)
- [Residual encoder, matched controls and corner cases](residual.md)
- [Per-context observations and scheduling scope](contexts.md)
- [Evidence and reproduction](evidence-scope.md)
- [Audited combined results](../../experiments/python-gamebub-v85/summary.json)

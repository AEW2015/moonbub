# V96 results: addressed copies and constant service

The retained corpus offers modest exact cross-position reuse. The new bounded
materializer passes standalone timed-controller tests, but it is not joined to
the full decoder/display pipeline. Keep the current product codec and memory
policy until that comparison is measured. V96a is qualified on the retained
corpus; V96b is implemented as a component; V96c has component tests; V96d's
full-path promotion gate remains open.

## Exact reference inventory

All 457 frozen 720×480 sources have 8,100 canonical 8×8 tiles. Independent
parsing checks **1,371 complete research streams / 11,105,100 tile outputs**,
including accepted-reference identities, every source/destination physical
address, bounded dictionary membership, literal payload and exact target bytes.
The primary inventory also verifies raster canonical SHA-256. It finds
2,216,647 existing same-position COPY tiles and 134,358 hidden constant tiles.
A further 38,099 non-COPY visible tiles reconstruct equal to their same-position
reference; this count does not change their opcode automatically.

| Policy | Additional cross-position copies | Fraction of 1,350,695 active residual blocks | Frames using cross-copy | Materialization source reads | Destination writes |
|---|---:|---:|---:|---:|---:|
| Control | 0 | 0% | 0 | 141,865,408 B | 236,908,800 B |
| 64 entries/plane | 37,295 | 2.76% | 412 | 144,252,288 B | 236,908,800 B |
| 256 entries/plane | 63,164 | 4.68% | 426 | 145,907,904 B | 236,908,800 B |

These read counts describe **literal-fixture materialization**, where FALLBACK
samples are supplied predecoded. The retained residual reconstruction path
already reads a same-position predictor: its separate volume estimate is
218,318,208 bytes for all three policies. A cross-copy replaces that source
address rather than eliminating the read. Its bypassed residual block count is
an opportunity to avoid coefficient/IDCT work, not measured saved cycles.
No reads, writes or hardware work are free, and no cross-position alias is used.

The unbounded diagnostic finds 101,936 possible cross-position matches; that
search is not an implemented dictionary policy. The implemented FIFO dictionaries
hold at most 64/256 distinct values per plane and rebuild only from accepted
frames. Exact tiles plus a 16-bit local source position alone cost
12,672/50,688 bytes across three full dictionaries. Adding one validity byte per
entry gives the inventory's 12,864/51,456-byte accounting, before hash tables,
other metadata and implementation overhead. Actual Python storage is larger;
no BRAM capacity or lookup-port mapping is qualified.

All research-stream bytes are charged:

| Policy | Headers | Fixed 24-byte descriptors | Literal fallback samples | Complete research bytes | Largest source |
|---|---:|---:|---:|---:|---:|
| Control | 542,735 | 88,840,800 | 86,444,480 | 175,828,015 | 695,182 |
| Cross64 | 543,192 | 88,840,800 | 84,057,600 | 173,441,592 | 695,183 |
| Cross256 | 544,106 | 88,840,800 | 82,401,984 | 171,786,890 | 695,185 |

This literal fixture format is deliberately large and exceeds the 49,152-byte
streaming cap. It cannot be compared as compression against V92/V95's actual
entropy-coded packets. No residual entropy saving or HEVC/AV1 superiority is
estimated. The walkthrough-family/synthetic targets remain predecoded; capture,
DCT and live encoder preparation are unmeasured.

## Standalone RTL through timed SDRAM

Three strict Verilator configurations pass **867 checks each: 2,601 total**.
They cover 2 ns/7 ns timed pin access with a four-sample generator and a 2 ns
case with a one-sample generator. The existing controller and bridges are
unchanged. Source seeds enter through real physical writes, and the testbench
checks all 32 x16 words of selected output tiles against its byte oracle.

Each configuration exercises 64 descriptors, 62 source BL8 lines, 201 accepted
eight-byte destination rows, 996 pin x16 writes (including 192 seed words), and
496 pin read words. The read count is exactly 62×8; destination writes are
201×4 plus the seed words. Tests cover all video banks, plane/final-tile
boundaries, same-low32/different-high32 identities, malformed/protected
admission, wrong response epoch, held responses, every read-line/write-row
cancel/reset, stalled tile storage, literal/generator cancellation, retry and
newly protected destinations during pending reads and first/last writes.
Accepted work drains; partial or even fully written invalid candidates cannot
publish. The caller must honor the component's lease until completion ACK.

Representative local descriptor metrics are:

| Operation | Source reads | Destination rows | Explicit preparation | Descriptor → acknowledged completion |
|---|---:|---:|---:|---:|
| COPY | 4×16 B | 8×8 B | None | 262 clocks |
| CONST128, four samples/clock | 0 | 8×8 B | 16 generator clocks | 169 clocks |
| CONST128, one sample/clock | 0 | 8×8 B | 64 generator clocks | 200 clocks |
| Literal control | 0 | 8×8 B | 64 input handshakes | 227–246 clocks |

These windows include four deliberately held completion clocks, controller
refresh phase and literal ingress stalls. They are not matched full-frame
speedups or placed-clock measurements. The engine owns one 64-byte local tile
buffer; the existing 16-byte read bridge, 8-byte row writer and controller
storage are additional. Its request interface is 204 bits, at least 26 packed
bytes or a chosen 32-byte aligned accounting record, plus literal data. It has
no production adapter to the separate 24-byte inventory grammar.

## Constant consumer and lifetime model

The fixed hidden profile is 294 tiles, or 18,816 bytes per frame. A Python
tile-order line model reproduces every canonical sample at 1/4/16 generated
bytes per clock. It replaces 1,176 of 32,400 display-line memory reads with
explicit generation: **31,224 remaining BL8 commands, a potential 3.63% read
reduction**. Generation itself costs 18,816/4,704/1,176 clocks respectively.
These counts are not total frame latency, an actual raster-reader request
schedule, or a measured shared-controller improvement. The 16-byte/clock
variant has no RTL implementation. Candidate constant writes remain unchanged.
Python verification retains an additional complete frame; proposed one-line
producer storage is not a resource-mapping result.

The behavioral bank model passes 34 directed operations covering outstanding
write ACKs, validation failure, commit and vblank fences, accepted-reference
advancement while an older display lease remains held, pending occupancy,
cancellation/drain, two-sample display release, bank reuse and full-width
identity bounds. It is neither exhaustive formal proof nor a substitute for
RTL bank-control/display integration.

## Decision and next gate

Retain these exact research tools and the original full-path control. Integrate
the materializer and a supported descriptor adapter into reconstruction,
validation and publication, then test the same source histories with all shared
memory clients and continuous display active. Integrate any hidden-line
consumer with the actual raster reader before claiming avoided physical reads.
Price dictionary construction/lookup, metadata, generator, hash/HUD, memory
turnaround/refresh and display deadlines together.

The [summary](../../experiments/python-gamebub-v96/summary.json) binds immutable
inventory, independent reader, behavioral model and standalone RTL receipts.
[Audit notes](audit-notes.md) record the tested boundaries. V96 does not newly
qualify complete RTL C2/HUD/root/seal, RGB565 or continuous-cadence operation;
those retained V91/V95 results are not silently extended to this path. Physical
30 fps, complete validated decoding below 10 ms, device mapping, placement,
routing, CDC and board testing remain open.

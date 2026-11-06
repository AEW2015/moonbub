# Next application-specific codec experiments

V84 keeps the native 720×480 quantized picture and residual coding as the
baseline. It studies the cost of discovering COPY and feeding the pipeline,
and prototypes operation metadata. None of those results is a finished new
Sunshine/ESP32/FPGA codec or a compression-rate improvement.

## First remove the remaining front-end timing assumption

The observed AB38 work includes 43,436,569 arithmetic decisions and 35,844,140
renormalizations across 457 sources. With the explicit LOW operation weights,
isolated front-end work has a 4.61707-ms median and 13.75352-ms maximum at the
assumed 100 MHz. HIGH weights give 8.80494 and 26.30566 ms. These are sensitivity
calculations, not measured RTL clocks or proven physical bounds. They show why
fast memory alone cannot establish the full decoder's latency in these models.

Add per-context observations to the next native trace. The current entropy RTL
shares one arithmetic engine across four independent probability/interval
contexts. Compare that shared engine with two/four arithmetic lanes under the
**existing bitstream**, retaining each stream's decision order and the DC
predictor. Tile completion must wait for all required DC/AC events, including
next-event lookahead. Measure the real rendezvous, cache/port arbitration,
bounded pending events and backpressure. Do not divide the aggregate count by
four and call that the expected speed.

The interval/probability multiplication is a candidate for DSP mapping; measure
its resource, pipeline and feedback costs in an isolated RTL experiment before
choosing lane count. Keep coefficient parity against the independent native
decoder for every plane and count all CRC, initialization, termination, control
and fetch costs. The V84 trace does not establish a DSP count or target Fmax.

## Make COPY an encoded operation in a separate profile

The [V2 operation map](mode-map-v2.md) supplies a concrete bounded metadata
grammar for COPY_REF, CONST128 and RESIDUAL. Hidden CONST tiles are implicit;
only 7,806 visible positions need a COPY/RESIDUAL bit. Keys use an implicit map,
and deltas choose a 976-byte bitset or shorter visible-run encoding. A 20-byte
header brings the maximum block to 996 bytes. The next host prototype must combine that map
with **actual re-encoded residual streams**, an independent decoder and the
content/reference/HUD envelope. Adding a map while leaving the original AB38
streams unchanged adds bytes and does not eliminate their entropy work.

Start by encoding the original quantized coefficients only for RESIDUAL tiles,
with explicit scatter order and DC-predictor rules. Compare an independent
residual stream per group with larger chunks and persistent contexts. Smaller
chunks can expose parallel decode work but introduce headers, termination,
probability resets and rate overhead. Measure those tradeoffs by actually
encoding and decoding the same native pictures, rather than subtracting work
attributed to COPY tiles from the old trace. A COPY tile can own initialization
or lookahead that is still needed by another tile in the old stream.

Price headers and termination for every chunk, not just coefficient payload.
The retained native receiver bounds packets at 49,152 bytes; a new grammar with
many reset/chunk headers may exceed that compatibility budget even if its
operation map is small. Define negotiated limits and bounded fragmentation or
streaming admission, then measure exact whole-frame bytes including HUD,
integrity fields and transport. Report first-byte-to-validated and
last-byte-to-validated intervals separately when overlapping input and decode;
do not move the milestone's start fence to hide work.

Bind version/capability, geometry, frame/reference/generation, grouping, exact
lengths, operation map, residual/HUD data and content commitment. The V84
operation-map block alone has no frame/reference identity and is not the full
envelope. Require bounded parsing, unknown-profile rejection, truncation and
oversize checks, stale-reference handling, dropped/duplicate fragment/ACK
recovery, and reset/key recovery. CRC and unkeyed SHA detect integrity errors;
they do not authenticate the sender.

## Carry the finite staging contract into RTL

Start with four output groups and one SHA lane, as supported by V83's controlled
comparison. Keep separate reference, signed-24-bit inverse-result and
coefficient/mode credit rings. Eight slots of each plus output storage reserve
7,168 logical bytes for those four staging classes; coefficients are included
here. The comparable 64-slot reservation is 28,672 bytes. Tree/maps, inverse
working registers, dequant staging, hashes, descriptors, compressed data,
control, ports and RAM rounding are additional.

Reserve a slot before issuing its producer and release it only after the
consumer finishes. Assert generation/bank/tile ownership, response stability,
drains and group reuse under arbitrary stalls. The software graph contains
future tasks; replace it with bounded streaming hardware control. COPY-ready's
transfer or alias into output storage still needs a real port/ownership design.

Preserve invalidation before candidate stores and atomic publication after
content, HUD, maps and physical drains. Test abort/reset at every outstanding
stage and retain the accepted reference. Slot-lifetime audits do not prove
those hardware transaction or display-lease semantics.

## Qualify the stream, then validated latency

Replay actual entropy/dequant output arrivals alongside controller commands,
continuous LCD/HUD reads, refresh and direction/row changes. The 20% phase-zero
reservation scenario remains illustrative, not a substitute for that test.
Measure host encode, finite ESP32 receive/forward queues and QSPI separately;
V84 has no ESP32 timing or firmware simulation.

Retain the milestones: 1,800 distinct accepted source frames over 60 seconds at
fixed 30-fps releases, then 18,000 frames/600 seconds on hardware. Validate every
required displayed identity, native pixels, queues, references/HUD and underrun
status. After that, require the full defined validated FPGA decode interval
below 10 ms for every qualified frame, including entropy and all completion
fences. This four-history corpus and conditional per-source schedules close
neither milestone. Compare HEVC/AV1 only with matched content, quality, latency
definitions, recovery and platform costs.

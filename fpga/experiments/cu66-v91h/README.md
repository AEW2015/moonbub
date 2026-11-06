# V91h synchronous packet staging

`br88_pipeline_v91h` has a compile-time `SYNC_STAGING` parameter. The default
value 1 instantiates `br88_packet_ingress_sync_v91h`; value 0 instantiates the
frozen V91d ingress through `br88_packet_ingress_v91h`. The two alternatives are
compiled separately. The product branch does not retain a runtime combinational
read path or a second staging memory to disguise the port cost. The packed
scratch/two-tile-bank module remains the frozen V91g2 source.

The synchronous branch has one 49,152-byte backing array, one byte write port
and one registered byte read port. The backing array is not reset. Its only
array accesses are a write on an accepted packet byte and a clocked read on an
explicit request. A request's data, address and epoch appear one edge later.
`FETCH_REQ`/`FETCH_WAIT` serialize these requests, with no new request while one
is pending. This conservative implementation does not pipeline back-to-back RAM
requests; functional port correctness is its purpose, not a promised speedup.
No mapped BRAM inference, resource fit or routed clock is established here.

A shared 46-byte register cache holds the 42-byte header plus four-byte CRC,
each six-byte descriptor and its tail byte, replay words up to four bytes, or
RAW pairs. Header register reads are ordinary bounded register muxes, not reads
from the backing array. Separate held 32-bit replay and signed 16-bit RAW
registers retain data until consumer acceptance. The read-data register adds
one byte. The cache highwater describes the 46-byte common cache, not the sum
of every control, metadata and held-data register.

Header/trailer bytes are fetched first, then all four descriptors and their
padding tails. CRC, field, length, range, empty-band and tail-padding rules run
before metadata becomes valid. Thus invalid metadata cannot allocate packed
scratch or issue external-memory writes. CRC is still accumulated during packet
reception. Subsequent context replay fetches only the bytes needed for each
16/32-bit context word; a partial final word is assembled most significant bit
first with unused low bits zero. RAW fetches the little-endian pair only after
the prior scalar is accepted.

The logical context remains active while replay RAM requests/waits occur.
Context outputs remain visible and backpressurable throughout those states;
only the input-word assembly pauses. A held sparse coefficient cannot disappear
when replay fetch begins. Child context error/done has priority over fetch
control. Context failure cancels any unused internal read response explicitly;
start/reset/packet abort likewise invalidate pending local responses and held
words. These pure local reads have no external write side effect to drain.
External packed-memory ownership retains the V91g2 accepted-request drain rule.

Packet state IDs 0–11 retain their old meanings. ID12 is `FETCH_REQ`, ID13 is
`FETCH_WAIT`; IDs14–15 remain reserved. `stage_context_active` distinguishes a
logical context from its instantaneous RAM-fetch state. Public debug ports expose
actual ingress cancellation (including internally generated packet abort and
context failure), request/response/write qualifiers, byte addresses, request and
response epochs, read/write data, cache occupancy/highwater, word valid/ready and
fetch purpose (0 header/CRC, 1 descriptor/tail, 2 replay, 3 RAW).

`count_stage_reads`, `count_stage_responses`, `count_stage_writes`,
`count_stage_fetch_wait` and `count_stage_word_hold` count accepting/observing
edges over the outer running transaction. Parent-scope counters and the cache
highwater survive an internally generated ingress cancellation; outer
reset/start/abort clears them. The raw ingress instance also has local counters,
which may reset on its internal abort and are not the receipt counters.
Successful synchronous cases require reads = responses = fetch-wait edges,
writes = accepted input bytes and cache highwater 46. Legacy-generated
cases expose no staging traffic/counters. Cancelled/error cases can discard a
local response; their cancellation qualifier makes that explicit.

The C++ harness independently models the staging bytes written by input
handshakes, checks each request's bounds/current epoch, checks the exact
one-edge response address/epoch/data and tracks one pending local read. Its
sparse-output checker holds band, block, coefficient index, signed value and
epoch stable until acceptance or actual ingress cancellation, including RAM
request/wait states. The existing external-memory scoreboards and dense/packed
byte goldens remain unchanged.

Each static build runs the existing 47 recovery checks. The synchronous build
adds nine named checks: unaligned header/descriptor fields with a partial replay
word, bad tail padding rejected before metadata, cancellation at a queued request,
abort/reset/restart at a registered response, context range failure while a RAM
read is in flight, held sparse output during replay fetch, and a held RAW pair
that cannot trigger the next fetch early. The held
sparse test requires an actual witness of sparse-valid/ready-low coinciding with
RAM request/pending, rather than assuming that random backpressure exercised it.
Measured rows fix write overlap, read prefetch and tile overlap on, and serial
clearing off; each binary runs 20 frozen cases against FAST/SLOW memory service.
The root runner combines the separately compiled binaries for paired comparison.

This endpoint remains BR88 residual chunk to dense scalar coefficients. It is
not a complete reconstructed/validated video frame, a physical RAM-controller
calibration, an ESP32 throughput test, a hardware 30-fps result or a validated
under-10-ms FPGA decode result. The next full-frame/transform/publication stages
and the V100–V110 7-series physical implementation work remain separate gates.

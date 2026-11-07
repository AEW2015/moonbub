# V96 bounded materialized COPY / CONST128

This is a standalone memory-engine experiment, not a promoted frame path.
`tile_materializer.sv` owns exactly one 64-byte tile buffer, one descriptor,
and at most one physical line/row request. There is no frame buffer, dictionary,
map alias, bank 3 access, or same-frame dependency.

A COPY descriptor reads four aligned 16-byte lines from an accepted bank and
writes eight 8-byte destination rows. Source and destination addresses can differ.
CONST128 explicitly generates all 64 samples using 4 samples/cycle (16 clocks) or
1 sample/cycle (64 clocks), then performs those same eight real row writes.
LITERAL accepts 64 byte handshakes into the same buffer and provides a baseline.
The 204-bit request interface is a minimum 26 packed bytes; a 32-byte aligned
external descriptor is an accounting choice, not a newly implemented wire format.
Each test metric charges one descriptor; literal ingress is additional 64 bytes.

The aperture is fixed at 518,400 tile-major canonical bytes in each of video
banks 0, 1, 2. Tile addresses are 64-byte aligned, ending at 518,336. The retained
reader consumes tile-major addresses directly. The retained row writer expects
raster addresses; the engine explicitly inverts the existing tile mapping for
each destination row. Physical x16 word address is `(bank << 22) | (tile_byte >> 1)`.

The accepted bank and the caller's protected mask (front, pending, display)
exclude destination writes at admission. COPY requires the full 64-bit source
identity to equal the full 64-bit accepted identity; the destination identity
must differ. `lease_mask` holds the source and destination from valid admission
until completion acknowledgement, including canceled operations and held replies.
The owner must honor that lease: it cannot publish/reuse the destination while
owned. A changed accepted source identity or newly protected destination aborts
further offers. Already accepted physical requests drain before error completion.
Changing protection cannot undo a previously accepted write; this is why callers
must honor the output lease, and why this component is not publication proof.

Warm `reset` and `cancel` invalidate an active candidate, stop new requests, and
consume the correctly tagged in-flight response before completing with error.
The service itself is never canceled. Partial destination writes are permitted
only in an invalid candidate. Offered completion fields remain immutable through
warm reset/cancel; its lease is released only on completion acknowledgement.
Cold `power_on_reset` is exclusively a quiescent initialization operation.

The selfchecking top reuses the unchanged timed shared SDRAM service, controller,
and pin model. Seed tiles are written through physical requests, not backdoors.
It checks real pin-model words against an independent byte oracle, all three
video banks and plane edges, 64-bit identity collisions, final tile, invalid and
protected rejection before traffic, wrong epoch responses, held responses,
read-line/write-row cancellation and reset, stalled-buffer retention, ingress
abort, source lease changes, retry and next-descriptor operation. Finite watchdogs
and terminal JSON `TEST_PASS` verdicts are mandatory.

Run `python3 scripts/cu66-v96/run_materialize.py`. The existing container uses
Verilator 5.020/GCC 13.3, at most two compile jobs, fatal warnings with no waivers,
and timed pin data access at 2 ns/7 ns. Attempts retain logs, compressed event
streams, exact source snapshots, hashes, tool versions, commands and failures.
Local metrics include descriptor acceptance, physical reads/writes, explicit
generation/ingress, refresh phase, and deliberate held outer completion. They
establish bounded service behavior only. They do not establish lower frame
latency, concurrent display schedulability, root/seal correctness, continuous
scanout, placed resources/timing, hardware operation, or 30 FPS qualification.

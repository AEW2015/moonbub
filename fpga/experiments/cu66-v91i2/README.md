# V91i2a CS88 dispatch and provisional coefficient placement

`cs88_pipeline_v91i2a.sv` connects a new provisional CS88 admission/retention
fork to the frozen `br88_pipeline_v91h` coefficient endpoint. The old V91i1 and
V91h files remain unchanged. Root documentation and the retained run reports
state the qualified test results; this file specifies the hardware interface.

This is coefficient integration. It does not dequantize, run IDCT, reconstruct
COPY/CONST pixels, maintain accepted references, validate HUD/content seals,
or publish a displayed frame. The output tuples are provisional even when an
earlier plane has completed: a later chunk can still fail. The `done` output
means all supported residual chunks completed with the stated coefficient
coverage, not validated frame publication.

## Supported input and ownership

The accepted outer subset remains CS88 version 1/group 16, 720x480, block 32,
chunk cap 65536, key mode 0 or grouped delta mode 3, and QM87 method 2 or method 6.
The new admission fork retains 8,100 two-bit mode entries and 1350 two-bit scale
entries, exposing registered post-admission lookup and packet-byte replay ports.
It initializes all mode entries to CONST serially so hidden-only groups need
no ambiguous uninitialized entries. Initialization takes 8,101 edges before
packet input becomes ready and is included in the measured frame service.
QM2 expands its validated runs to all 1,350 provisional scales serially. QM6
uses the trusted preloaded map; eligibility is not a substitute for its values.

The complete frame is structurally admitted before any entropy consumer starts.
The wrapper then rejects any nonempty AB38 plane with error 64 before issuing a
child start, external memory request or coefficient. An all-COPY frame with
three empty residual planes completes without starting the BR88 core. Known
AB38 prefixes in V91i1 do not provide an AB38 consumer here.

A `start` is accepted only when `start_ready` is high. A start while busy,
preloading a map, or draining a previous accepted external memory request is
ignored and counted in `blocked_starts`; it cannot replace the packet bank or
memory owner. The caller pulses `start` only for an offered transaction. Frame
epochs must be nonzero and strictly increasing, including across warm reset.
The last accepted frame-epoch guard is retained, rather than reset to permit
stale identities. A rejected frame can consume a frame epoch; retry uses a new
one. Identity/reference eligibility inside CS88 remains the separate V91i1
trusted accepted-state snapshot contract.

Each nonempty plane receives a distinct internal child epoch. The monotonic
child nonce is retained across warm reset, and the whole frame's required
number of child epochs is checked before its first consumer starts. A frame
that would wrap the nonce rejects with error 66; the current regression does
not exhaust the full 32-bit range. Child epochs tag packed scratch requests,
ACKs and child coefficients; `out_epoch` is the separately latched frame epoch.
This avoids reusing the same scratch epoch for three chunks of one frame.

## Trusted quantizer snapshot preload

Before an inherited-map frame, stream exactly 1,350 values through
`cache_valid/cache_ready/cache_data/cache_last`. One value is a two-bit scale
code 0, 1, 2. The first accepted beat latches `cache_ref_fid` and
`cache_ref_generation`; later tag input changes do not retag the map. `last`
must be asserted only on beat 1,350. A reserved code 3 produces `cache_error=3`,
clears eligibility and cannot authorize a QM6 consumer. An early/missing `last`
produces `cache_error=1`. `cache_complete` is true only after complete valid
coverage. A new partial load invalidates the previous complete marker.

At accepted frame start, the map is eligible only if the caller's accepted-ref
snapshot is valid, `accepted_qcache_valid` is true, and both supplied reference
tags match this complete preload. V91i1's QM6 rules then require a delta frame.
The first start consumes `cache_complete`, while the fork latches its pre-edge
eligibility. This one-shot rule is essential: QM2 provisional decoding can
write the same scale RAM, so an old tag must never authorize those new values
for another frame. A following QM6 frame requires a fresh complete preload,
even after rejection or abort. There is no implicit accepted-qcache commit.

Preloading is locked through frame ownership and physical ACK drain. Top-level
abort/reset clears any partial preload and releases its input owner. The
bench records cache preload cycles/bytes separately from the accepted-start
frame fence: a 1,350-beat preload takes 1,350 modeled edges, and must be included
when comparing end-to-end service rather than hidden as free initialization.

## Chunk refill, coefficient binding and external memory

The wrapper owns the outer packet bank until its frame is quiescent. It
serially requests registered bytes from an admitted plane span and holds each
refill byte/last marker until the frozen child accepts it. Addresses and frame
epochs are checked before forwarding each local response. The child retains
its independent synchronous packet staging and its proven sparse/context,
packed scratch and two-bank dense preparation paths. This implementation
explicitly duplicates packet staging rather than claiming shared-bank fit.

Each emitted dense residual block maps to the next plane-local native tile
whose retained mode is RESIDUAL. The wrapper performs registered mode/scale
lookups and holds the mapped tuple while the child output is stalled. Outputs
are:

- `out_plane`:0 Y,1 Cb,2 Cr; `out_block`:chunk-local residual ordinal;
- `out_tile`:plane-local row-major 8x8 tile, 90 columns for Y or 45 for chroma;
- `out_qcell`:Y `(tile/90/2)*45+(tile%90/2)`, chroma `tile`;
- `out_qscale`: actual 0/1/2 map value; `out_index`:raster coefficient 0..63;
- `out_value`:signed 16-bit coefficient; `out_epoch`:latched frame epoch.

The wrapper stalls dense acceptance while searching a later tile; it cannot
accept a coefficient without a valid positional binding. COPY and CONST mode
positions are skipped, not silently replaced with reconstructed pixels. A
late inner-CRC error in plane 3 leaves any earlier coefficient tuples
provisional and suppresses frame completion. A later clean frame can retry
without resetting the core.

External packed-scratch memory remains a 16-byte aligned ready/valid request
and real tagged ACK interface. Writes become physical at their accepted ACK,
including after abort/reset. The wrapper always forwards old responses to the
frozen child. New starts, cache writes and scratch reuse stay blocked until
that accepted owner drains. Cancelling local packet or lookup responses does
not erase an accepted external write.

Logical packet storage is 49,152 B per bank, 98,304 B total for the outer and child
banks. Retained modes add 16,200 bits, scales 2,700 bits and active-cell flags 1,350 bits,
plus 128 B header and 354 B QM gather caches in the new fork and the frozen child's
existing storage. These are logical bounds, not measured BRAM/LUTRAM use, port
fit or routed device capacity. Sharing staging or changing memory primitives
requires its own ownership, functional and implementation qualification.

## Error and telemetry interpretation

Outer errors 1..14 retain V91i1 meanings. Wrapper errors 64/65/66/67 mean
unsupported entropy, invalid/stale frame epoch, child nonce exhaustion, and
placement/replay inconsistency. Child errors preserve the frozen pipeline's
stage prefix under `0x80 | child_error`; for example packet-CRC 3 first becomes
child 0x13, hence wrapper 0x93 (decimal 147), not 131.

Inherited V91h debug/counter ports describe the last/current child chunk. They
must not be relabeled full-frame fences. Additional ports expose core start
count, total refill bytes, outer replay reads, current child epoch, blocked
starts and frame state. The C++ bench observes actual full-frame first/last
input, first/last mapped coefficient and completion edges on its clock, plus
separate preload cost. No achieved frequency is assumed.

## Self-checking simulation

`tb_pipeline.cpp vectors.txt seed tile-events.jsonl` uses the root runner's
strict Verilator build. Each case runs FAST and SLOW memory scenarios. FAST
ACK latency is one edge; SLOW writes take`16+(((address>>4)^seed)&3)` edges and
reads`18+(((address>>4)^seed)&3)`, with finite request/output/input stalls.
Only one external request may be accepted at a time. The bench commits writes
on ACK, checks reads against matching committed epochs, and audits byte refill
provenance, local registered response binding and held input/output tuples.

Every accepted coefficient value and its full positional/scale/epoch tuple is
compared directly to the supplied golden arrays. Each completed 64-coefficient
tile also produces a JSON trace row with its metadata, first/last accepted
edge and FNV1a64 hash of the actual coefficient bytes, low then high signed 16
little-endian two's-complement bytes, offset 1469598103934665603 and
prime 1099511628211. The hash is an audit diagnostic, not the sole exactness
check. Qualification tile/count totals exclude extra directed tests; additional
directed coefficient comparisons are reported separately.

The directed suite covers accepted-write cancellation/ACK drain, blocked
replacement start, held mapped output cancellation, clean retry after late
failure, incomplete preload abort, consumed-cache rejection, zero frame epoch,
latched input snapshots/tags and exact mapped tuples. Physical clock, actual
memory controller timing, sustained hardware 30 fps and complete validated
under-10-ms decoding remain open.

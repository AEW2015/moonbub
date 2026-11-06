# V91j inverse-transform integration

`cs88_pipeline_v91j` wraps the frozen V91i2b coefficient endpoint with
`REFILL_OVERLAP=1`. It connects real coefficient handshakes to
`cu66_inverse_stream_v91j`, which reuses the unchanged V69 dequantizer and
two-pass Q14 IDCT. No software transform is substituted for either RTL block.

The adapter has two 64×16-bit coefficient banks (256 logical payload bytes).
Each bank owns immutable frame epoch, child epoch, plane, residual-block
ordinal, native tile, qcell, qscale and an opaque transform token. Fill and
math pointers advance in order. A bank progresses FREE→FILL→READY→ACTIVE and
remains ACTIVE until its 64th residual sample is accepted. The other bank can
assemble the next tile while dequantization, inverse transform or output
serialization owns the active bank. No coefficient payload bulk reset is
needed: indices 0..63 must be accepted in order before a bank becomes READY.

Only one transform job occupies the math path at once. Dequantizer output IDs
are checked before the IDCT handshake, and IDCT IDs are checked before any
residual sample becomes valid. The output is a signed 24-bit, unclipped
residual stream with the original positional metadata. It is not a pixel
stream: prediction addition, clamping, reference retention, HUD and content
validation remain later stages. Opaque token identity is `(frame_epoch, token)`;
the counter resets on each local frame start/reset/cancellation, which also
flushes both synchronous arithmetic producers before token reuse. A legal
frame has at most 8,100 tiles, so this does not introduce a lifetime token
exhaustion limit. The defensive 32-bit within-frame wrap guard remains.

`coefficient_*` debug ports expose accepted source coefficients independently
of the residual stream. `inverse_launch` exposes the actual assembled bank at
the dequantizer input handshake, and `inverse_dequant` exposes the actual
dequantized tile accepted by the IDCT. The C++ bench compares every signed
value before producing stage hashes. Assembly hashes use 64 signed16LE values;
DQ/residual hashes use signed32LE containers for the signed20/signed24 values.
FNV64 stage hashes are diagnostic receipts, not a replacement for exact checks.

Frame completion requires both coefficient completion and complete local
inverse/output drain. A late coefficient/CRC error invalidates local bank and
math ownership immediately. Previously emitted residuals are provisional and
may form a partial tile prefix; a failed frame never signals completion.
The base decoder retains an accepted external scratch request through its
matching ACK. New starts and trusted cache writes are blocked while the inverse
path is active, and replacement cannot bypass base ACK drain.

Local adapter errors are 1=coefficient index, 2=metadata, 3=coefficient/qscale
range, 4=partial tile at input completion, 5=DQ/opaque ID, 6=IDCT/opaque ID,
7=token exhaustion. The wrapper reports these as `0xc0 | code`, preserving the
base decoder's existing error namespace, including late-CRC error 147.
Sticky transform faults pulse a base abort once so they cannot hold the base
start interface permanently inactive; a fresh accepted start clears both
local and base transaction state. These are transaction controls, not accepted
reference or frame publication commits.

The integrated bench accepts `cases.tsv transform_tiles.tsv seed events.jsonl`;
the transform table is the decompressed canonical Python vector file. It emits
actual assemble, dequant and residual stage events with metadata, token,
sample count, FNV value hash and observed clock fences. A final error may emit
a `complete=false` residual event containing only the accepted partial prefix.
The standalone adapter bench accepts `boundary.tsv seed` and exercises signed
arithmetic limits, all scales/plane classes, ordering/metadata failures,
partial tiles, cancellation during fill and each math phase, held output,
two-bank backpressure and clean retry. The retained root runner owns strict
Verilator/GCC builds and source/vector/command snapshots.

Neither bench establishes hardware frame rate, physical resource fit, routed
frequency, accepted-frame publication or complete validated decode latency.

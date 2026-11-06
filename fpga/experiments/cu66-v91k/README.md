# V91k canonical reconstruction integration

`cs88_pipeline_v91k` connects the actual admitted CS88/BR88 stream through the
frozen V91j inverse adapter to canonical Y/Cb/Cr pixel bytes. It preserves the
720×480 luma and 360×240 chroma geometry. No software transform or software
reconstruction replaces these RTL consumers.

## Sources and storage

`cs88_coefficients_v91k` is an isolated fork of the V91i2b coefficient wrapper.
The existing admission block, BR88 decoder, scratch storage, registered refill
queue, dequantizer and IDCT sources remain unchanged. The fork exposes admitted
key/frame identity and arbitrates the existing registered mode/scale lookup
port. Coefficient lookup has priority; a response-owner register distinguishes
reconstruction responses. This adds no duplicate packet or full mode table.

`cu66_reconstruct_stream_v91k` walks all 8,100 tiles in plane/tile order. It reads
actual retained mode RAM, gathers 64 accepted signed24 residuals only for mode
2, and uses the frozen `cu66_reconstruct_tile` for reference addition/clipping.
Mode 0 copies the accepted reference; mode 1 emits canonical hidden pixels of
128 without a reference read; key mode 2 predicts 128. The archived safe-hidden
footprint is independently checked against the admitted mode. Output is 64
canonical bytes per tile, with immutable frame epoch/fid/plane/tile/mode/index
held through arbitrary legal consumer stalls.

Local storage includes one 1,536-bit residual tile and one 512-bit reference
buffer, plus the frozen reconstruct block's 512-bit output register and control.
These 320 logical payload bytes are additional to the frozen transform banks
and packet storage; they are not a physical RAM-inference or device-fit claim.
The output consumer owns the full candidate YUV plane storage. Each accepted
byte means that provisional candidate write has committed; its finite `ready`
service is charged in the testbench. There is no validated publication here.

## Reference ownership and cancellation

Visible delta COPY and residual tiles issue one 512-bit logical reference-burst
request, tagged with frame epoch, accepted-reference fid/generation, plane and
tile. Only one request may be outstanding. Acceptance captures its owner, and
only a matching response releases it. A mismatched response fails closed and
leaves the genuine owner pending until a matching response drains. A matching
bus-error response retires its physical owner but fails the local transaction.
Reference data is immutable in the finite service model.

The pending bit and descriptor have FPGA power-on initialization. Synchronous
`reset` is a **warm reset**, not a bus flush: it invalidates provisional local
pixels while retaining an already accepted reference request. A new start is
blocked until both the reference burst and existing scratch ACK drain. Abort
behaves identically. Responses to canceled work are consumed and discarded,
never reused by a replacement frame.

Local reconstruction error codes are 1=mode/hidden/key invariant, 2=missing
reference, 3=reference response owner or bus error, 4=residual tuple/index owner,
and 5=reconstruction tile identity/error. The wrapper maps them to `0xe0 | code`,
preserving base errors (including late CRC 147) and inverse errors (`0xc0 | code`).
Frame `done` requires coefficient, inverse and full-grid canonical completion
with no error. Earlier canonical bytes remain provisional until later content
validation and publication gates.

## Verification interface

The integrated bench takes:

```text
cases.tsv transform_tiles.tsv canonical_goldens.tsv seed events.jsonl canonical_actual.tsv
```

Canonical goldens contain `id`, accepted-reference planar raster hex (or `-`
for key), and expected planar raster hex. The bench checks every accepted
coefficient, assembled/dequantized tile, signed residual and canonical byte.
It scatters accepted canonical bytes into actual candidate memory and writes
`id<TAB>memory_profile<TAB>planar_raster_hex` only for successful complete cases.
The RGB565 consumer can replay those actual committed memory snapshots rather
than software-generated substitute pixels.

FAST reference bursts return eight cycles after acceptance; SLOW bursts return
in 12–24 cycles with independent request stalls. These are explicit logical
four-beat-128-bit service assumptions, not a physical SDRAM controller model or
measured board bandwidth. Candidate writes accept one byte per ready cycle in
FAST; SLOW adds finite seeded write stalls. All source-input, scratch, reference
and output service is charged in the canonical endpoint clock fence.

The event trace retains actual transform stage records, complete canonical-tile
hashes/metadata/timestamps and accepted reference descriptors. Exact C++ pixel
comparisons precede diagnostic hashes. Failure may leave only a provisional
canonical prefix and partial transform/output tiles; it never emits a successful
candidate memory artifact or asserts frame completion.

The directed suite covers old scratch/refill/inverse cancellation tests, held
canonical output, reference ACK drain during abort/warm reset, wrong-response
owner rejection, clean retry, snapshot immutability and all admitted modes.
Root-owned scripts retain strict compile/run source snapshots and independent
Python audit evidence. RGB conversion lives in `rgb/` with a separate bounded
memory-service simulation and explicit replay/additive timing interpretation.

No result here proves HUD composition, content hashes/seals, atomic reference
commit/publication, physical memory fit, routed clock, hardware 30 fps or complete
validated decoding under 10 ms. Those remain the documented later gates.

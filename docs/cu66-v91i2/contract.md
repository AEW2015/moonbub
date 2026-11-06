# V91i2a coefficient placement and quantizer ownership contract

V91i2a accepts the V91i1 restricted CS88 packet subset, retains the decoded
8,100 tile operation map and the 1,350-cell quantizer map provisionally, and
serially sends admitted BR88 residual spans through the frozen V91h coefficient
pipeline. For each plane, residual block ordinal `k` maps to the `k`th native
row-major tile whose operation is RESIDUAL. The emitted tuple identifies that
tile, the coefficient index, quantizer cell and quantizer code, frame epoch and
child epoch. No dequantization, pixel reconstruction, HUD validation, content
root/seal verification or frame publication occurs here.

## Native indexing

The native planes contain 5,400 Y tiles and 1,350 tiles each for Cb and Cr;
each tile is an 8×8 block. Y has 90 tile columns and each chroma plane has 45.
Residual ordinal is local to its plane and counts only RESIDUAL operations.
For Y tile `t`, the QM87 cell is `(t // 90 // 2) * 45 + (t % 90 // 2)`.
For Cb/Cr tile `t`, the cell is `t`. A coefficient tuple carries signed
16-bit coefficient value in raster index order 0..63, local residual ordinal,
native plane tile, qcell, and scale code 0..2.

The Python model reads the pinned frozen hidden mask, parses key mode 0 or
grouped delta mode 3, derives the 8,100 operations, validates QM87 method 2 or
6 and the required active-cell count, then binds dense V91e coefficient
goldens to exact BR88 span hashes. It is independent of the packet producer and
receiver. Its per-plane placement records are the audit reference for the
vector's residual-ordinal to tile mapping.

## Accepted quantizer snapshots

QM6 is bodyless and inherits all 1,350 qscale values. The caller supplies a
complete snapshot before frame start, along with the accepted-reference fid and
generation. The packet carries the reference fid, which must match the caller's
accepted-reference fid; its current frame generation must be newer than the
caller's accepted-reference generation. The cache tag matches the caller's
accepted-reference fid and generation. The CS88 packet does not carry the
accepted-reference generation.

The hardware cache port accepts one 2-bit qscale code per handshake; the TSV
stores each code as one byte. The caller asserts `cache_last` on exactly the
1,350th accepted code, and the cache tag is latched with the first code.
Reserved code 3 reports preload error 3 and cannot authorize QM6. Every frame
start consumes the complete snapshot. The cache remains locked while the child
decoder is active or draining, and the next QM6 frame needs a complete preload.
A QM2 frame derives a new provisional map from its packet. This component does
not commit accepted frame or cache state.

For V91i2 vector rows, the model obtains current qscale bytes from the retained
QM2 key packet. It records the accepted-history packet and snapshot tag from
the V91i1 native-history evidence, and proves that the relevant intervening
accepted rows used QM6. For c3/f50, the V87 `copy_group_cap65536` ledger records
QM2 keys at fids 0, 24 and 48; their raw QM87 block SHA-256 values are equal.
The retained c3/f0 key QM2 block has that same exact byte hash, so its parsed
1,350 values are an exact value source for the latest fid48 key. Fids 49 and 50
use QM6. The manifest keeps the accepted fid49 history identity distinct from
the value-source fid0 packet and from the ledger's latest equal-byte QM2 fid48.
QM87 block hashes are hashes of wire blocks; they vary on QM6 packets because
the required-cell count changes and are not presented as decoded-map hashes.

## RTL vector rows

[`cases.tsv`](../../experiments/python-gamebub-v91i2/vectors/cases.tsv) has one
frame per row, with these columns in order (the file has no header row):

`id`, expected frame error, packet hex, accepted-reference valid/fid/generation,
qcache valid/fid/generation, prior qscale hex, current qscale hex, operations
hex, then dense Y/Cb/Cr signed16LE coefficient bytes in residual-ordinal and
coefficient-index order. A `-` represents an empty byte vector. Qscale and
operation arrays are one byte per entry. The manifest records source fixture,
exact payload and qscale hashes, lineage, and each dense golden source.

Four positive native frames have exact V91e dense goldens: c0/f0, c0/f1,
c0/f3 and c3/f50. c0/f3 is the V90 `exact4_else_proxy_HIGH` packet; its BR88
payload hashes exactly match the V91e c0/f3 coefficient records. Two native
rows exercise early AB38 rejection (one all-AB38, one mixed AB38/BR88). Other
rows exercise the structural all-COPY empty-residual path, a synthetic QM6
snapshot containing all three qscale codes, a QM6 cache tag mismatch, a
reserved qscale code 3 preload error, and a native third-plane BR88 inner-CRC
mutation with the outer CS88 CRC repaired. The late CRC case expects error 147
(`0x80 | V91h error 0x13`); the Y and Cb coefficient output is provisional,
Cr emits none, and `done` remains false.

The RTL coefficient trace rolls an FNV-64 value from initial
`1469598103934665603` with prime `1099511628211`, consuming the 64 signed
16-bit little-endian coefficient bytes for each emitted block. The trace also
records tuple metadata and first/last samples; the C++ harness compares every
coefficient and every mapped tuple field against the TSV arrays. Hash equality
is supplementary evidence, not a substitute for those direct comparisons.

## Error and ownership behavior

V91i1 outer admission errors 1..14 retain their existing priority. An invalid
accepted-reference snapshot or QM6 cache/tag mismatch rejects as error 7
before any decoder start, memory request or coefficient output. A malformed
qcache preload containing value 3 reports cache error 3 and cannot authorize
the frame. AB38 or mixed entropy rejects as error 64 before any child start or
memory request. A BR88 chunk CRC error is discovered by the child decoder; prior
plane outputs remain provisional, are not promoted to a completed frame, and
the wrapper reports 147. The all-COPY synthetic row has zero residual jobs and
no child start or memory request.

Frame epoch and child epoch are separate. Every chunk gets a new child epoch;
all tuples for a frame retain the frame epoch. Cancellation hides provisional
outputs and drains accepted external writes under their original owner before
replacement can reuse packet or scratch state. The external service profiles
used by the RTL harness are behavioral simulation inputs, not measurements of
hardware memory timing. FAST responds after one edge. SLOW models writes as
16 edges plus `((address >> 4) ^ seed) & 3`, and reads as 18 edges plus the same
jitter term. Timing counters retain absolute first/last input, first/last
coefficient and done cycles. Frame cycles run from start to coefficient done;
the 1,350 qcache preload cycles are reported separately. They do not include
full validated frame publication.

The evidence covers outer admission, BR88 coefficient consumption and dense
coefficient placement. It makes no entropy-rate, pixel-quality, complete-frame,
hardware-throughput, routed-clock or physical-memory-fit claim.

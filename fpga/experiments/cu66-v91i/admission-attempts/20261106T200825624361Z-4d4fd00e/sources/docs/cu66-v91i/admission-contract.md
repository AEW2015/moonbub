# V91i1 outer admission contract

V91i1 accepts a restricted subset of the existing CS88 envelope and emits a
structural receipt with up to one bounded residual descriptor for each of the
Y, Cb, and Cr planes. Its accepted-reference snapshot is supplied by the
caller at request start. The gate does not update that snapshot, retain a
reference, dispatch descriptors to consumers, or publish a frame.

## Supported packet subset

The fixed CS88 header is 128 bytes. V91i1 requires `CS88`, version 1, group 16,
720×480 geometry, block size 32, chunk cap 65536, and zero reserved header
fields. Keys use mode method 0 with an empty mode body. Deltas use grouped mode
method 3. QM87 method 2 (full run map) and method 6 (inherited map) are the only
accepted quantizer forms. Other modes and block/cap variants that the frozen
V88 receiver can handle are rejected as unsupported by this checkpoint.

The packet body is laid out as mode bytes, QM87 bytes, residual data, HUD bytes,
then a big endian outer CRC32 over all prior bytes. The parser verifies exact
body lengths, the 49,152-byte admission budget, header bounds, reserved bytes,
and the outer CRC before making a receipt.

Mode parsing checks grouped tags, hidden-only group tags, canonical mixed
groups, exact visible coverage, and zero padding against the frozen 8,100-tile
hidden profile. The profile is read as data from the pinned generated constants
and checked against its established SHA-256. The parser derives active
quantizer cells from the resulting operations. QM87 validation checks the
inner QM CRC, header, exact length, supported method, required-cell binding,
method 2 run values and coverage, and method 6 eligibility in that check order.
QM6 requires a
delta and a valid accepted-reference snapshot with `qcache_valid=true`; this
proves eligibility only and does not compare cached values.

The accepted snapshot fields are `valid`, `fid`, `generation`, and
`qcache_valid`. A key must carry reference id `0xffffffff`; a delta must name
the accepted fid. When a snapshot is valid, incoming fid and generation must
both be newer, including for a key. This is an externally supplied state
contract. V91i1 does not establish that the caller actually accepted or
retained the referenced frame.

For each plane, the residual directory has a big endian chunk count followed
by `(block_count, payload_length, payload)` entries. V91i1 checks the count
against the number of residual operations and the configured cap, bounds each
length by `[46, 46 + 128 × block_count]`, validates exact coverage of the
residual-data span, and accepts only known `AB38` or `BR88` payload magics. It
emits each payload's packet offset, length, block count, and entropy type
(1=AB38, 2=BR88). The parser does not validate either entropy grammar or inner
chunk CRC.

## Receipt and rejection behavior

The RTL receipt contains fid, refid, generation, key flag, four component
lengths, required-cell count, and three plane slots with block count, payload
offset, payload length, and entropy type. Empty planes carry zero descriptors.
The Python audit index also records the parsed QM method and derived HUD
offset; those are audit metadata, not RTL receipt ports. Any rejection occurs
before a receipt is emitted. The integer `expected_error` values in
[`vectors/index.json`](../../experiments/python-gamebub-v91i/vectors/index.json)
match the RTL runner's reason codes:

| Code | Meaning |
|---:|---|
| 1 | Packet size or admission budget |
| 2 | Input framing |
| 3 | Outer CRC |
| 4 | Unsupported native profile |
| 5 | Header bounds |
| 6 | Identity or stale frame |
| 7 | Reference or cache eligibility |
| 8 | Mode map |
| 9 | QM CRC |
| 10 | QM format or run coverage |
| 11 | QM required-cell mismatch |
| 12 | Plane chunk count |
| 13 | Chunk bounds or exact residual coverage |
| 14 | Unknown chunk magic |

Error 2 covers packet input framing, including an early or missing final-byte
marker. The RTL harness exercises it as a framing transaction rather than as a
malformed packet byte vector. Semantic mutation vectors repair the outer CRC
where the test targets a field check. Combined-fault vectors pin first-failure
ordering for outer CRC versus unsupported qmap, QM CRC versus unsupported qmap
method, and required-count mismatch versus missing cache.

## Evidence and limits

The vector index includes all 35 retained V88 packets and all 16 retained V90
packets, packet hashes, originating fixture hashes, input-source pins, and
accepted-reference history evidence. They are 51 fixture rows from 8 distinct
`(cohort, fid)` identities. The predecessor snapshots use the matching V88 or
V90 native history row for the same policy; the model verifies that row was
accepted and that its fid and generation precede the fixture. These actual
fixtures are all within the 49,152-byte limit. The directed negatives include
recomputed-CRC mutations for header/profile, identity/reference, grouped mode,
QM2/QM6, chunk directory, bounds, and unknown-magic checks. An additional
synthetic all-COPY delta uses QM6 with zero required cells and three empty
planes to exercise zero-residual coverage; its inherited HUD and copied root
and seal are not validated and it is explicitly structural-only.

[`admission-model.py`](../../experiments/python-gamebub-v91i/admission-model.py)
is an independently written byte-index/`struct` model; it does not import the
frozen native receiver or packet producer. It reads actual retained packets
from the V88/V90 campaigns and writes the machine-readable index, packet
vectors, TSV for the RTL harness, and
[`admission-results.json`](../../experiments/python-gamebub-v91i/admission-results.json).

This checkpoint does not decode coefficients or pixels, validate HUD
semantics, recompute content roots or frame seals, establish full native packet
validity for the synthetic zero-residual case, commit accepted-reference or
quantizer-cache state, validate publication, or make latency/performance
claims. CRC32 detects accidental corruption and does not authenticate a sender.

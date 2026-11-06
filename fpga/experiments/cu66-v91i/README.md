# V91i1 CS88 structural admission checkpoint

`cs88_admission_v91i1.sv` reads existing CS88 frame bytes. It implements a
bounded structural admission checkpoint before a future entropy consumer. It
does not wrap, rewrite, transcode or pad the current wire protocol. The authority
is `experiments/python-gamebub-v88/wire/receiver.cpp`; V90 uses the same envelope.

This checkpoint has no entropy-job, external-memory-write, reference-commit,
scanout or publication interface. Its held receipt certifies the checks below,
not a decoded or content-validated frame. Neither inner AB38/BR88 decoding nor
their inner CRCs, coefficient ranges, HUD decoding, reconstructed content root
or frame seal is checked. The root and seal bytes remain opaque here. Those
checks must complete before future reference or display publication.

The supported native subset is fixed: CS88 version 1, group size 16,
720×480, block geometry 32, chunk cap 65,536, implicit key map method 0 or
grouped delta map method 3, and QM87 run method 2 or inherited method 6.
Other native profile variants reject as unsupported. Both AB38 and BR88 are
recognized as typed structural chunk descriptors; this does not claim an AB38
RTL decoder or dispatch either payload. Unknown chunk magic rejects. The
49,152-byte local packet limit is a configured research policy, not the native
receiver's 2 MiB host allocation limit.

The parser validates:

- Exact input length and final-byte marker, packet cap, and the big endian outer
  CRC32 before any metadata parsing.
- The existing 128-byte header: profile fields, geometry, reserved zeros,
  component limits, and exact sum using 64-bit arithmetic.
- Identity validity, strictly increasing frame id and generation when an
  accepted-reference snapshot exists (including a new key), and key/delta
  reference binding.
- All 8,100 tile positions, using the immutable native hidden-tile mask:
  294 hidden positions and 7,806 visible positions. Group tag validity,
  noncanonical mixed tags, exact mode coverage/length and zero tail padding
  are checked. Residual counts are derived independently for each plane.
- The 1,350 required quantizer cells derived from actual residual positions;
  QM87 CRC, magic/version/cell count/length, required-cell binding, legal run
  values and exact 1,350-cell run coverage. Inheritance requires a delta and an
  explicitly valid accepted quantizer-cache snapshot.
- Three residual plane records, exact zero-or-one chunk counts for this cap,
  exact residual block count, payload bounds, known chunk type and exact data
  section coverage. HUD bytes are bounded and placed after that section, but
  their semantics remain a later gate.

`accepted_ref_valid`, `accepted_ref_fid`, `accepted_ref_generation` and
`accepted_qcache_valid` are latched only at `start`. They describe state already
accepted by the future full-frame consumer. The checkpoint never advances that
state. An admission receipt must not be fed back as an accepted-reference
snapshot. The qcache-valid flag confirms external eligibility; actual cached
quantizer values are not consumed or copied here.

The byte-stream interface is `start`, declared `packet_bytes`, `epoch`, and
`in_valid/in_ready/in_data/in_last`. A receipt remains stable under
`receipt_valid && !receipt_ready`; its metadata and three descriptor buses are
meaningful only while `receipt_valid`. Descriptor offsets are zero-based byte
positions in the unchanged complete CS88 packet, excluding the test transport
prefix. Entropy type 1 means AB38 and type 2 means BR88. An empty plane has
zero blocks, offset, length and entropy type.

There is one 49,152-byte backing array, one byte write port and one synchronous
byte read port. The only accesses are an accepted input write and a clocked
read request. The array is not reset. One pending read has a registered data,
address and epoch response on the next edge; the parser consumes it after that
response. The 128-byte header cache and 354-byte QM cache are bounded register
caches and are not reset. A 1,350-entry active-cell flag array is cleared one
entry per cycle before input is enabled. Those 1,351 setup cycles are included
in `count_cycles`; this is functional staging, not mapped BRAM or timing proof.

`reset`, `abort_packet` or replacement `start` suppress read, input and receipt
valids on that edge and invalidate pending local reads and held receipts. A
replacement start latches a new epoch and snapshot and begins serial clearing.
There is no external request/ACK port in this module and consequently no claim
that it drains an external ACK. When dispatch is added, the frozen V91h/V91g2
accepted-request drain rule must be preserved, rather than assuming local-read
cancellation is sufficient for external writes.

Error codes are stable local diagnostics:

| Code | Meaning |
| --- | --- |
| 1 | Declared packet size |
| 2 | Input final-byte marker |
| 3 | Outer CRC |
| 4 | Unsupported profile/mode/quantizer method |
| 5 | Header bounds, geometry, flags or reserved fields |
| 6 | Invalid/stale frame id or generation |
| 7 | Reference/cache eligibility |
| 8 | Grouped mode grammar, exact coverage or padding |
| 9 | QM87 CRC |
| 10 | QM87 shape, run value or run coverage |
| 11 | QM87 required-cell binding |
| 12 | Plane chunk count |
| 13 | Chunk block count, length, range or data-section coverage |
| 14 | Unknown chunk magic |

`tb_admission.cpp` consumes a space-delimited vector file and a deterministic
seed: `Vcs88_admission_v91i1 vectors.txt seed`. Each row contains `id`, expected
error, packet hex, reference-valid flag, prior frame id/generation, qcache-valid
flag, expected frame id/reference id/generation/key flag, mode/qmap/HUD/data
lengths, three `(blocks,offset,length,entropy_type)` tuples, then required cells.
The root runner creates and hashes this transport file from the independently
parsed fixture index. It is a test-only transport and is not a new wire format.

The self-checking bench checks actual receipt metadata and every descriptor,
zero receipt exposure for rejects, randomized input pacing and receipt
backpressure, exact registered read address/data/epoch, local read conservation
and input/write counters. It deliberately changes external reference inputs
immediately after start. Directed tests cover abort/reset at queued reads,
registered responses and held receipts; replacement start at a pending response
or held receipt; early/missing final markers; oversize/undersize start; and
recovery with a fresh good packet. JSONL case records expose actual receipt
fields for an independent audit. A terminal `TEST_PASS` is required; a clean
compiler exit is insufficient.

The frozen `cu66-v91h` source is unchanged and is not instantiated in V91i1.
Next integration work must dispatch admitted chunks without losing packet
ownership, map each residual coefficient block back to its native plane/tile,
carry quantizer selection, retain COPY/CONST operations and accepted reference
state, and preserve pending external ACK drains on cancellation. Full
reconstruction, HUD/content commitments and atomic publication follow that.
Hardware 30 fps, complete validated decode below 10 ms, ESP32 throughput,
physical RAM calibration, and Series 7 resource fit or routed timing remain
separate open gates.

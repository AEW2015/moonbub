# Direct owned-line hit model

This experiment models one narrow consumer change for the frozen V91k RGB565
converter: when `FILL_REQ` or `LUMA_REQ` asks for a byte already present in the
matching plane's ACK-owned 16-byte line, consume that byte in the request state.
For a miss, keep the existing byte lease and tagged physical line refill path.
The three existing per-plane line payload slots total 48 bytes and are the
proposed storage for this first alternative. The model proposes no extra payload
storage; actual RTL and synthesized storage are not measured here.

## Source order and byte identity

The access schedule follows `canonical_rgb565_cached.sv`: `CHECK_ROWS` fills
each needed chroma row in Cb-then-Cr order, then the converter requests the 720
luma bytes for that output row. The edge rows replicate chroma row 239; no row
240 is requested. `canonical_line_reader.sv` keeps one aligned line tag per
plane, with the byte offset selecting a byte from the 128-bit payload.

The generator decodes captured `actual_001` and `actual_006` canonical frames
and the nonuniform `cache_edge_pattern`. For each, the direct-probe replay
returns the exact same 518,400-byte consumer stream as the scalar line-cache
replay. Each replay observes 486,000 hits and 32,400 line misses (21,600 Y,
5,400 Cb, 5,400 Cr), or 32,400 aligned 16-byte requests and 518,400 payload
bytes. The edge fixture includes chroma column 359 and row 239. Since a chroma
row has 360 bytes, its alignment alternates: 120 of the 239 adjacent-row
boundaries per chroma plane share one aligned line, while the others cross a
line boundary. The replay checks all boundary bytes in both paths and confirms
the edge fixture gives distinct values for each side of every boundary.

## Request-service clock estimate

The current scalar hit takes two request-service edges: at edge *n*,
`FILL_REQ`/`LUMA_REQ` accepts a byte request and the adapter registers its hit
response; at edge *n+1*, `FILL_WAIT`/`LUMA_WAIT` consumes that response. A direct
owned-line hit consumes the selected byte at edge *n* in the request state and
advances. The nominal saving is therefore one request-service clock per hit,
or 486,000 clocks per complete source-derived request sequence.

This is a state-edge estimate, not a predicted frame-fence reduction. It
excludes physical memory service, randomized stalls, lookup and conversion
stages, output backpressure, and interactions among those stages. It makes no
full-frame latency, throughput, or FPS claim.

## Ownership conditions still required in RTL

A direct probe must require an active frame, a valid line for the requested
plane and aligned tag, and an idle adapter with no outstanding physical read,
byte lease, or held response. A refill line becomes usable only after its
matching physical ACK and only while the frame generation that requested it is
still active. Start, cancel, or generation change invalidates line ownership.
These requirements are exercised by a small bounded abstract state model; that
model is not an RTL proof or a substitute for implementation assertions.

## Read-only review of the generated candidate

The generated core and line reader were reviewed against this model. The core
offers `probe_valid` only in `FILL_REQ`/`LUMA_REQ`, and suppresses the external
byte request when the reader reports a hit. The reader's hit requires an active
matching epoch, adapter `IDLE`, no physical or byte lease pending, no held byte
response, an in-range address, and a valid line tag for the selected plane.
Only a successful active canonical-line response installs line validity. In
the joined design this response can come from retained row data or completed
physical reads; the adapter's local memory-port ACK is not necessarily a new
SDRAM transaction. Start,
reset, and cancel clear it. Chroma hits feed the existing byte-enable write
path; misses continue through the existing byte lease and refill path. These
are source review findings, not execution results. The model pins the generated
core, reader, wrapper, interface contract and generator hashes in its JSON.

The generated interface assigns separate meanings to its counters:
`count_reads`/`count_responses` remain external byte leases/returns,
`count_direct_consumes` is the direct hit count, and
`count_canonical_consumed` totals successful external returns plus direct
consumes. The source-derived expected counts are 32,400 external reads and
responses, 486,000 direct consumes, and 518,400 canonical bytes consumed. The
legacy adapter hit counter therefore becomes zero in the burst path; it no
longer describes all locally consumed bytes.

The standalone adapter RTL test report passes 255 checks in 88 clocks and pins
the tested reader, testbench and runner hashes. It covers valid/mismatched
probe epochs, range and plane tags, held response exclusion, all three line
slots, aligned row-0 Cb/Cr edge bytes, finish, start, reset/cancel, and wrong
physical ACK epoch drain. It also exercises a matching bus-error ACK after
another plane line is valid: the physical owner retires, all line validity is
cleared, the byte lease receives an epoch-tagged held error response with zero
data, probes remain unavailable through error-response hold, and lease
retirement permits a fresh epoch to refill successfully. Its scope is the
adapter contract, so it does not test full-frame counters or converter timing.

The result is Python source-derived accounting only. It does not implement or
simulate RTL, measure RAM or timing, model SDRAM stalls, or establish a physical
throughput gain. Run `python3 experiments/python-gamebub-v91l-burst-converter/hit_model.py`
to regenerate the JSON, or add `--check-freshness` to verify pinned inputs,
sources, generator and results.

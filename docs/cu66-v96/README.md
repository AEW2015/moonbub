# V96: exact reference copies and bounded memory service

V96 now has a complete retained-corpus inventory, an independent research-stream
reader, a constant-consumer/lifecycle model and a standalone materialization
engine exercised through the retained timed SDRAM controller. This is a component
checkpoint. It does not replace the complete decoder/display path or complete
V96d's promotion gate. See [results](results.md), [contract audit](audit-notes.md)
and [qualified summary](../../experiments/python-gamebub-v96/summary.json).

## Three connected experiments

The [inventory](../../experiments/python-gamebub-v96/inventory/README.md)
examines all 457 frozen V82 sources at 720×480. It preserves the distinction
between hidden CONST128, existing same-position COPY, residual tiles that happen
to reconstruct unchanged, and exact cross-position matches in the accepted
reference. Each plane has a deterministic FIFO dictionary of 64 or 256 distinct
64-byte tiles. Rebuilding scans the accepted frame; candidates never teach it.
Sources stay in the same plane and previous accepted frame. Every selected copy
is materialized into the candidate, rather than becoming an address alias.

The inventory's `V96RS01` stream is a fixture format with a JSON header,
24-byte addressed descriptors and 64-byte literal FALLBACK payloads. It charges
every descriptor, header and literal; it is not a proposed efficient streaming
packet or a replacement for EC92/CS95. Its minimum size already exceeds the
49,152-byte production packet cap. Literal targets are supplied predecoded, so
these byte counts cannot establish compression, host-encoder throughput or
residual entropy savings. The independent reader imports no V96 encoder/parser
and checks all 11,105,100 tile outputs, source positions, bounded dictionary
membership, address fields and stream lengths.

The [RTL materializer](../../fpga/experiments/cu66-v96-materialize/README.md)
accepts COPY, CONST128 or literal tiles. COPY issues four 16-byte BL8 source
reads and eight 8-byte destination row writes. Constants explicitly generate
64 samples in 16 or 64 clocks and pay for those same writes. Literal ingress
also supplies 64 handshakes. One 64-byte local tile buffer is retained through
backpressure; bridge/controller buffers are additional existing storage.
Its 204-bit request interface costs at least 26 packed bytes, or a chosen
32-byte aligned accounting record. That interface is distinct from the
inventory fixture grammar; no adapter between them is implemented yet.

Requests bind full 64-bit source/destination identities, an epoch and banks.
COPY reads only the accepted source; destination writes exclude accepted,
front, pending and display-held banks. The output source/destination lease must
be honored by the caller. Warm cancellation stops new offers, drains the tagged
accepted request, invalidates the candidate and retains ownership through the
held completion ACK. It cannot undo earlier writes. Cold reset is restricted
to quiescent initialization. No component-local success publishes a frame.

The [Python consumer model](../../experiments/python-gamebub-v96/service-model/model.py)
prices a potential hidden-line generator at 1/4/16 bytes per clock and checks
explicit bank lifetimes through commit, held display, cancellation and reuse.
It reads tile-order lines, not the RTL raster-converter schedule. Python retains
an additional reconstructed frame for verification; its proposed 16-byte
producer slot is not a mapped storage result. The 16-byte-per-clock variant is
model-only; materializer RTL tests only one/four samples per clock.

## Address and cost contract

Canonical Y/U/V plane bases remain 0, 345,600 and 432,000, totaling 518,400
bytes. A tile is 64 bytes and the last legal tile starts at 518,336. Physical
video banks are 0–2, with x16 word address `(bank<<22)|(tile_major_byte>>1)`;
the corresponding bank byte stride is 8 MiB. HUD retains its separate linear
42,240-byte allocation; scratch bank 3 is excluded from these descriptors.
The row writer accepts **raster** addresses and maps them into tile-major
storage, while the read bridge accepts tile-major addresses. The materializer
inverts this map for each destination row before using the unchanged writer.

Report three different fences separately: fixture materialization, retained
reconstruction prediction, and display consumption. A cross-copy adds a read
to literal fixture materialization but replaces a same-position predictor read
in the retained residual path. It does not automatically reduce read volume.
Hidden constants still pay for candidate writes, validation and display unless
a separately integrated consumer proves those operations unnecessary. Command
or generator counts alone do not measure full-frame latency.

## Reproduction

Use Python 3 plus the existing `gamebub-cu66-v69-build` container with Verilator
5.020 and GCC 13.3. Retained V82 targets and V91l controller/bridge sources come
from baseline `d856e5fa909bc308d53debc1aeabb5bca8230fa9`.

```sh
python3 scripts/cu66-v96/inventory.py
python3 scripts/cu66-v96/verify_inventory.py
python3 scripts/cu66-v96/run_models.py
python3 scripts/cu66-v96/run_materialize.py
python3 scripts/cu66-v96/summarize.py
python3 scripts/cu66-v96/bundle_manifest.py
```

The runners use finite watchdogs, immutable attempts, source/input/artifact
hashes, strict fatal RTL warnings and at most two compiler jobs. Failed attempts
remain available. The inventory snapshots the baseline roadmap as a historical
requirements input; the aggregate verifies that snapshot while the current
roadmap records this checkpoint. Current executable source pins must still
match. No board, Sunshine service or firmware is changed by this study.

## Remaining V96 exit work

1. Join the materializer into the actual reconstruction/write/hash/validation
   path, including a supported wire/descriptor adapter and rollback ownership.
   Compare it against the retained per-line and four-line grant controls.
2. Integrate any constant consumer with the real raster RGB reader, immutable
   display lease and shared controller. Charge generator, masks, descriptors,
   source lookup, candidate/HUD writes, validation reads and display consumers.
3. Replay the same complete source histories through mixed read/write/scratch
   and continuous display service. Compare addressed traffic, ACT/PRE/refresh,
   turnaround, latency tails, abort/retry and underruns together. Include
   broader independent raw captures before selecting a general codec policy.
4. Promote only an exact full-path winner. Preserve fallback syntax, V91l,
   V92d and V94's open integration gates, and the V100–V110 7-series mapping,
   placement, routing and timing work. Physical 30 fps and complete validated
   decoding strictly below 10 ms remain open.

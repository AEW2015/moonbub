# V77 streamed structured direct-YUV cache

`fpga/experiments/cu66-v77/cache/cu77_direct_cache.sv` implements the
three-live-strip organization previously modeled in Python. It is an RTL
cache/neighborhood reader and streamed prefetcher, not a complete display,
reference decoder, canonical-bank lease manager or clock-domain crossing.
The exact external ports are in [the interface contract](interface-contract.md).

## Data layout and ports

| Data store | Organization | Bytes |
|---|---|---:|
| Y | Three 1,920-word column slots | 11,520 |
| Cb | Four 720-word banks, three columns total | 5,760 |
| Cr | Four 720-word banks, three columns total | 5,760 |
| HUD | Four rectangles × four 192-word column slots | 6,144 |
| Total | x16 data words | **29,184** |

Cb/Cr bank selection is `(sample_row & 1)*2 + (packed_word_column & 1)`.
Each bank has one synchronous complete-16-bit read and one streamed write
port. Separate bank addresses provide four neighborhood words without adding
asynchronous RAM read ports; duplicate taps at row/word clamps reuse the
same registered word. Y and HUD use one synchronous word read each. Byte
selection follows registered words. Logical bytes exclude tags, counters,
metadata and response registers; primitive allocation is measured separately
by [the combined renderer elaboration flow](elaboration.md).

Y/Cb/Cr physical addresses retain V74 tile-major 8×8-byte tiles packed low
byte first. A column fill visits tile rows and four BL8 chunks per tile.
HUD addresses use the actual packed rectangle row pitch and block columns,
including x=22 misalignment. Per-slot global-column tags are invalidated before
replacement and become valid only after every accepted word of that column
has drained. One stream word is written per accepted response cycle; there
is no eight-clock unpack loop following a 128-bit response.

A complete ordered fill of strips 0–89 issues exactly **35,040 BL8 requests /
280,320 x16 words**. The regression compares each strip's accepted physical
address set with the independently generated frozen V76 trace. It does not
replace cache storage with golden pixel queries.

## Ordering, epochs and drain behavior

A valid inactive descriptor binds generation, frame ID and canonical bank,
clears all validity bits and resets per-frame counters. Zero generation,
invalid frame ID or bank 3 reports metadata error without memory work. Active
or undrained descriptors are backpressured; no pending data is reinterpreted
under a replacement epoch.

Prefetch index must equal `prefetched_count` and be below
`consumed_count+3`. Consume is in order and below the completed prefix.
Skipped, duplicate and beyond-window operations remain backpressured without
issuing new work. A strip enters the ready prefix only after all required
column fills and tags are complete. Its completion response is held until
accepted. Consume additionally waits for the pixel response pipeline to be
empty and for no pixel request to be asserted. Finish requires all 90 strips
consumed and both response paths drained.

The pixel interface can accept one request per clock when its consumer is
ready. It returns coded u/v, raw Y, four Cb/Cr taps, opaque-HUD hit/data and
an explicit error. Bounds, ready-prefix membership and all needed global tags
are checked at acceptance. Invalid queries return an error with zeroed sample
data, not silently valid black pixels. Registered sample words and metadata
remain stable under output backpressure while other strip fills continue.

Local abort suppresses new requests and cancels an unaccepted pixel response.
A previously accepted memory request still consumes its eight streamed beats
before reporting abort/deactivating the epoch. A memory-error beat or malformed
`last` framing similarly invalidates the source and drains the accepted burst.
The descriptor-ready gate also waits for the old response-valid level to drop.
Reset in these benches is paired with resetting the memory source; local abort
is the tested drain-preserving operation. Full external source-switch/vblank
ownership remains a separate integration responsibility.

Counters `read_commands` and `read_words` count accepted physical work.
`pixel_queries` counts accepted queries. `cache_misses` counts rejected pixel
queries (bounds, readiness or tag availability); it is not a physical prefetch
miss-block count. These counters reset on descriptor acceptance and are 32-bit
modulo values.

## Finite verification

```sh
python3 scripts/cu66-v77/run_cache.py
```

Strict Verilator `--Wall` builds the actual RTL, with one build job, bounded
subprocess/frame watchdogs and before/after source hashes. Three schedules
(0, 7701, 7702) each render two synthetic epochs in different canonical banks,
for **six active frames / 2,073,600 queried pixels**. All raw Y/chroma/HUD samples
are checked against a logical-coordinate oracle while the memory source
independently decodes physical addresses. Complete per-strip request sets match
the V76 trace. Data changes with epoch, and pixel reads run concurrently with
prefetch of the third live strip.

Each schedule includes **26 fault probes and 16 rejected metadata/order/window
requests**. The memory probes cover abort, error and wrong-last at each of eight
accepted beat positions plus preissue cancellation. An additional probe holds
a valid pixel response, attempts epoch replacement while a prefetch is active,
and aborts after acceptance; all eight accepted words drain and the held pixel
is explicitly counted as canceled. Across each run, accepted pixel requests
must equal delivered plus canceled responses. Delayed schedules also exercise
thousands of held-response cycles and request backpressure.

The ideal source supplies actual streamed words with deterministic delays;
it is not a controller latency or physical SDRAM model. Real-controller and
combined native-oracle rendering are qualified by the parent integration flows.
This regression alone proves no target clock, fit, CDC, 30 fps or under-10-ms
validated decoding bound.

## Development provenance

The initial 25-fault-probe qualification is retained in
`cache/before-held-epoch-probes/source-and-evidence.zip`, with eight internally
hashed source/log/result members and a manifest. It is superseded and is checked
against its own archived sources, not current ones. The RTL was unchanged
through the added held-epoch probe.

Four retained failed development logs identify testbench issues rather than RTL
repairs: counting legitimate concurrent prefetch traffic as an invalid-request
side effect; checking descriptor-ready before an ideal source dropped its last
valid level; withholding response-ready before submitting a new request behind
an already held result; and not stopping a second accepted burst during a
single-burst abort accounting probe. The final tests account for those accepted
operations and retain the stricter correctness/drain assertions. No qualified
predecessor file was modified.

## Separate bounded-slot arithmetic variant

`cu77_direct_cache_bounded.sv` is a separate module and does not replace the
qualified baseline. It changes the three-slot selector to a bounded unsigned
seven-bit function and narrows the corresponding temporary. The former signed
32-bit `%3` expressions unnecessarily described wide constant-division logic.
The new function folds four base-4 digits, since 4 is congruent to 1 modulo 3;
the four-bit sum is at most 10, and subtracting 9, 6 or 3 yields the slot.
Other state, handshakes, array dimensions, addresses and epoch/drain rules are
unchanged.

```sh
python3 scripts/cu66-v77/run_cache_bounded.py
```

A separate build reuses the unchanged cache testbench through Verilator's model
prefix. All three schedules match **every baseline counter and cycle total**:
six frames, 2,073,600 active queried pixels, 78 fault probes and 48 invalid
requests, with one explicitly canceled pixel response per schedule. A separate
SystemVerilog hierarchical-function probe checks **all 128 possible seven-bit
inputs** against modulo 3. This is finite module testing plus exhaustive helper
validation, not formal whole-module equivalence.

The bounded variant and its independent sources/logs/results are in
`cache/bounded/` and `run_cache_bounded.py`. Native/converted rendering and actual
unplaced resource effects are measured by the corresponding separate renderer
and elaboration campaigns; do not infer routed Fmax or target throughput from
the helper's smaller expression alone. Baseline source/evidence stays frozen.

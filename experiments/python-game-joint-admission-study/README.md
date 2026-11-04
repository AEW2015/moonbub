# Joined codec admission and packet-credit prototype

This study executes actual AR03 candidate construction, transport admission,
commit/discard, GF03 packetization, consumed-packet credits, reassembly, AR03
decoding and AF03 reference publication in one finite Python controller. It tests
whether these mechanisms compose correctly when work, feedback and deadlines
overlap. It is simulation evidence for a prospective host–ESP32–FPGA pipeline;
it does not install firmware or qualify physical 30 fps operation.

## Pipeline and ownership

1. Schedule source captures and BOX letterboxing. Keep the latest waiting image
   rather than accumulating an unbounded capture queue.
2. Build the complete AR03 candidate, including actual GM/SR work, selected exact
   RGB565 display patches, CRCs and frame-cap checks. One candidate can be active.
   A source-bank read lease protects a referenced reconstruction during building
   and admission. Building does not consume codec frame identity or reserve a
   reference publication destination; the controller does own a bounded host
   descriptor while this work runs.
3. Estimate admission from elapsed capture age, actual candidate length, current
   gateway backlog and configured wire, ESP service, feedback, pacing and decode
   allowances. Accept with `commit(candidate)` or pay `discard(candidate)`.
   Rejected construction remains charged. Only committed bytes reach the wire.
4. Split actual AR03 bytes into GF03 v3 datagrams, prefix each with a packet-token
   identity, and send through a paced forward link. The gateway parses received
   prefix/header bytes, pays declared ESP service and forwards the complete GF03
   datagram to a prospective FIFO endpoint.
5. Reassemble and validate actual bytes. The received GF03 epoch, frame ID and
   content tag must match the enclosed AR03 identity before decoding. Delivered
   reassembly slots remain pinned until decode completion or explicit rejection.
6. Decode the packet against confirmed receiver reference banks. Stage receiver
   completion until its measured work ends, then generate AF03 feedback and
   queue valid output for a modeled vblank. Exact display patches do not alter
   the YUV prediction reference.
7. Parse AF03 and apply sender reference publication only after physical owners
   drain and the paid ACK operation completes. Expiry wins if it occurs during
   that operation. A waiting candidate resumes after either ACK completion or
   ACK cancellation; stale whole-state snapshots cannot overwrite its commit.

Commit validates the candidate's current source-bank object, identity and tag,
destination availability, frame identity, geometry, cap and window. Unrelated
bank changes do not automatically invalidate a still-valid source. Discard and
failed construction release transient source ownership without publishing it.

## Two separate feedback protocols

`PC18` consumed-packet credits release transport tokens only. They never confirm
that a frame decoded successfully or that a prediction reference was published.
The receiver records a bounded consumed-token ledger. After a credit timeout the
host can send a serialized `QC18` query on a separately reserved control resource;
the returned credit must match slot, monotonically increasing sequence and token
CRC. Delayed duplicate credits cannot release a subsequently reused token.

AR03's existing `AF03` v3 feedback separately reports decoded-frame publication.
Its epoch, frame ID, body CRC and stored-bank identity/tag must validate before a
sender bank becomes usable. Packet loss, corruption or missing AF03 can therefore
cause drops or expiry without inventing a usable reference. Lost feedback still
pays construction and wire costs. Delayed duplicate-credit traffic joins the
reverse-link queue when it actually becomes ready, rather than reserving it early.

Packet credits and AF03 share one serialized reverse virtual wire. The forward
and reverse wires are otherwise independent; this is not a physical Wi-Fi
airtime/contention model.

## Wire sizes and bounded resources

| Item | Modeled size or bound |
| --- | --- |
| Complete AR03 body | Configurable cap, at most 49,152 bytes |
| GF03 data payload | At most 1,008 bytes |
| GF03 header | 31 bytes |
| Packet-token prefix | 16 bytes: epoch, slot, reserved field, sequence |
| Largest emitted data UDP payload | 1,055 bytes: prefix + GF03 header + payload |
| Consumed-packet reply `PC18` | 29 bytes including CRC |
| Consumed-packet query `QC18` | 28 bytes including CRC |
| Decoded publication `AF03` | 43 bytes |
| IPv4/UDP allowance | Additional 28 bytes per data, query or feedback datagram |
| Host sender descriptors / codec pending window | Configurable 2 or 3; default 3 |
| Encoder candidate | At most one building or ready |
| Prediction reference banks | Two per encoder/receiver |
| Packet tokens / queued gateway mailbox | Six / at most six waiting entries |
| Query control resource | One, separate from the six data tokens |
| Reassembly slots | Two; completed readers retain ownership |
| Display framebuffer roles | Three slots: front, pending and decode ownership |
| Decoded-feedback descriptors | At most four |
| FIFO default | 8,192 bytes; declared drain and bounded wait |

Full GF03 bytes, including the 31-byte header, enter the modeled SPI/FIFO cost.
The 16-byte transport prefix is parsed at the gateway and is not forwarded.
This endpoint is a proposed GF03 FIFO interface. The installed JPEG/MSV1
begin/commit register-command protocol is not executed or costed by this model.

These are logical ownership and queue bounds. Python arrays, codec temporaries,
candidate reconstructions, UI caches, source images, packet copies and retained
diagnostic rows use additional host memory. They are not proof of ESP32 SRAM,
PSRAM, FPGA BRAM, external SDRAM or DMA-buffer fit.

## Timing and what the evidence proves

Actual Python work is measured for map/resize, candidate building and resolution,
packet wrapping, ingress, decoding and feedback processing. The finite controller
stages work completion so expiry and feedback races can be tested. ESP service
uses declared CPU-share, copy/CRC/driver, polling and QSPI assumptions; wire rates,
aggregation, feedback latency, pacing, FIFO drain and vblank are also assumptions.
These independent virtual services are not a calibrated shared processor.

Admission is a causal estimate, not a guarantee: it uses known body size, elapsed
age and current backlog without consulting future frames or decoded-image
oracles. It is distinct from later deadline checks. A packet may be admitted and
subsequently expire or miss presentation. Native Python wall time, configured
capture IDs/s, eventual presentation and steady-window distinct presentation
counts must not be conflated with measured hardware FPS.

The retained campaign uses the existing native Mass Effect regression region,
letterboxed to a 720×480 canvas and scheduled at 30 capture IDs/s. This is reused,
already compressed, approximately 29.88 fps source material. Offline media
loading/capture is excluded; the modeled resize is charged. Small synthetic fault
cases test ordering and recovery, rather than gameplay quality. See `results.json`
and its summary for the actual retained outcome; this README does not prescribe
that outcome.

## Retained results

The retained run contains eight cases and 636 scheduled captures, with 49
source/dependency hashes checked before and after measurement. All native rows
below use 90 distinct source images on a 720×480 canvas. “Strict” counts
presentations during the three-second capture interval; “eventual” includes the
bounded drain afterward. The diagnostic rate counts distinct capture IDs in the
two-second central window, rather than decoded duplicates or panel refreshes.

| Native profile | Built / committed | Paid precommit rejects | Strict / eventual presented | Diagnostic IDs/s | Receiver NACK drops |
| --- | ---: | ---: | ---: | ---: | ---: |
| Admission disabled | 85 / 85 | 0 | 74 / 76 | 27.5 | 9 |
| Admit at 200 ms | 83 / 83 | 0 | 63 / 65 | 21.5 | 18 |
| Admit at 150 ms, 8 ms aggregation | 85 / 70 | 15 | 67 / 70 | 23.0 | 0 |
| Admit at 200 ms, 4 Mbps forward link | 79 / 58 | 21 | 54 / 58 | 19.5 | 0 |
| Lost packet credit, query and duplicate | 80 / 80 | 0 | 59 / 61 | 20.0 | 19 |
| Lost refresh AF03 | 84 / 84 | 0 | 75 / 76 | 29.0 | 8 |

The default 200 ms admission row rejects **zero** candidates. Its difference
from admission-disabled results comes from remeasuring Python service work in
each run, which changes event ordering and backlog; it is not evidence of an
admission-policy improvement or regression under an identical timing trace.
Likewise, the lost-AF03 row's higher diagnostic rate does not mean feedback loss
improves streaming. Those comparisons need replay of the same measured service
trace or controlled repeated trials.

The 150 ms/aggregation profile pays 476.72 ms of construction for its 15 rejected
candidates, then presents all 70 committed frames eventually with no receiver
NACK drops. The 4 Mbps profile pays 640.40 ms of rejected construction, rejects 21
candidates and eventually presents its 58 committed frames. These runs establish
that precommit dropping and ownership cleanup operate on real encoded bytes;
they do not establish optimal thresholds or 30 fps capacity.

The lost-credit profile sends one actual QC18 query; all data tokens eventually
drain. The two small synthetic cases separately exercise forward packet loss and
corrupted AF03. Across the retained cases, selected exact UI words have zero
mismatches, and the read-only verifier checks all expected ownership drains and
source pins. The regression suite passes 16 tests. The campaign's approximately
54.38 seconds of host execution is neither target service time nor streaming FPS.
No native profile qualifies a sustained physical 30 fps pipeline.

Correctness checks cover exact selected RGB565 patches, valid source-bank
identity/tag use, publication after paid completion, ownership draining, no wire
traffic/publication from rejected candidates, and conservation of presented or
dropped capture IDs. CRC and content tags detect accidental corruption; they are
not authentication.

FPGA entropy-decoder cycles, shared external-memory arbitration, scanline
deadlines, DSP/BRAM fit, ESP32 instruction execution/heap/RF behavior, production
Sunshine capture and physical display service are outside this study. A finite
passing run is a handoff prerequisite, not an end-to-end hardware qualification.

## Reproduce and verify

From the repository root, using the project environment:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest discover \
  -s experiments/python-game-joint-admission-study -p test_model.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python \
  experiments/python-game-joint-admission-study/verify.py
```

`verify.py` checks retained results and source/dependency SHA-256 pins without
the external video. The regression tests use deterministic clock injection for
race scenarios, including paid ACK overlap and timeout while a candidate waits.

`benchmark.py` regenerates timed results and needs NumPy, Pillow, PyAV and the
external `mass-effect-2600.mp4` file. Set `GAMEBUB_MEDIA_DIR` to its directory if
using a different media location. It snapshots source/dependency pins before
running and confirms they did not change before writing `results.json`. Keep
source fixed during that run. Result regeneration changes measured host timing;
it is not a read-only verification command.

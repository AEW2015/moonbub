# Reference-only asynchronous replacement anchors

AA01 extends the previous [MA01 anchor model](../python-anchor-study/README.md)
with a separately ACKed background key. This is actual Python encoding,
parsing and reconstruction under assumed stage clocks, not an installed mode,
serialized ACK protocol, FPGA decoder or hardware FPS evidence.

## Protocol and bounded ownership

`async_codec.Encoder`/`Receiver` use a new versioned CRC-protected envelope
with transaction ID, anchor ID, visible capture ID and explicit transaction
kind: KEY, DISPLAY or RETIRE. KEY carries a frozen MT02 independent payload
but is **reference-only**. It never updates the visible capture ID, so a late
replacement key sourced from an older capture cannot regress the screen or
inflate presentation counts. DISPLAY carries a real MT02 residual packet
against the exact ACKed immutable anchor. Transaction sequence numbers are
separate from capture IDs; reference IDs refer to the former.

The encoder holds at most two persistent anchors and two DISPLAY credits.
While a candidate KEY awaits its exact epoch/transaction ACK, new DISPLAYs
may still name the old anchor. Successful KEY ACK changes the anchor used for
future DISPLAYs; in-flight old-anchor readers continue safely. Old reference
retirement requires **both** DISPLAY credit/ACK completion and explicit
physical-read drain. Returning credit alone does not release the read pin.

RETIRE is an explicit forward control transaction/ACK. It retains the new
anchor and removes the older one only after the sender's drain rule. The
monotonic relation `old_anchor < keep_anchor < retire_transaction` is checked
before receiver mutation. Duplicate retirement is idempotent; a lost retire
ACK can retry without allocating a third anchor. A forged valid-CRC request
to remove the newer anchor while keeping the older one is rejected.

Lost KEY ACKs retry the **exact same bytes and transaction**, making receiver
installation idempotent. The sender switches only after the matching ACK.
The timer/retry count is bounded; exhaustion can leave an explicit pending
candidate requiring recovery, not a guessed reference. The default test loses
one key ACK and recovers on a retry. Epoch reset rejects old data and ACKs.
A candidate rejected before transmission leaves the old anchor usable.

These are single-threaded reference state machines. Actual drain/ACK/control
serialization, authentication, network reordering and hardware clock-domain
crossings remain outside this prototype. The timed experiment uses FIFO
wire/QSPI/decode stages, not arbitrary packet-reordering transport.

## Timed experiment

`timed.run(frames, manifest, Config(...))` actually encodes each selected image,
uses its real packet length, decodes the bytes, and checks the host RGB hash.
Captures skipped in the latest waiting slot are not encoded. The default
virtual services are serialized2 ms preparation,8 ms decode, ideal8 Mb/s
network,160 Mb/s QSPI,10/20 ms feedback and60 Hz vblank. These durations are
assumed; actual Python wall costs are recorded separately.

KEY, DISPLAY and RETIRE share two slot-owned packet buffers, one encoder,
network, QSPI and decoder. A due KEY is prepared ahead of another DISPLAY
when an encoder/slot becomes free; it cannot starve behind an infinite display
queue. Existing FIFO work still drains. RETIRE is prioritized to free the
second anchor before another replacement. Control keys consume real full
encoding/wire/decode work; if a source capture also gets a DISPLAY packet,
both costs are charged. A RETIRE costs its actual envelope/wire bytes and an
assumed0.05 ms control stage. ACK feedback bytes, RF/link overhead, retry-side
host source capture/scale and real memory transactions remain unmodeled.

The refresh interval is measured from the last prepared background-key attempt.
If that candidate exceeds48 KiB, the old anchor remains valid; there is no
adaptive quality or immediate new-candidate loop before the next interval.
This intentionally simple policy exposes cap failure, not a solved scene-cut
controller. Initial failed-key admission may retry on a newer captured image.

Three logical RGB framebuffer roles track immutable front, latest pending and
decoder back. Reference-control decodes consume decoder service but no visible
framebuffer/presentation event. The caller owns the actual pixel buffers; this
is a role oracle, not a validated SDRAM allocation or target-fit report.

## Reproduce

Use the prior [pinned environment](../python-codec-study/requirements.txt).
Original clip files remain outside Git with their source/PTS/canvas hashes.

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
```

`tests.log` records14 passing tests: reference-only keys, old-reader/ACK drain,
two-anchor/credit bounds, old/duplicate/epoch ACKs, data loss, exact key retry,
CRC rejection, forbidden retirement direction, stale data, unsent candidate,
retirement-ACK loss, fresh sessions, cap rejection and finite timing resources.
The extra recovery tests were added after the benchmark without changing
executed codec/timing sources. Parent source snapshots can bind those tests.

## Results

The benchmark uses four exact primary60-frame comparisons, one held-out combat
case, a fault case, and a longer90-frame second-clip case. Each is actual coded
data scheduled at hypothetical30 capture IDs/s. Original source rates remain
25/29.88 fps; duplicated content is recorded. The90-frame second-clip window
ends before the4-second held-out boundary. A90-frame combat primary would
overlap that boundary, so it was not used.

For60 inputs, strict window is `[0,2000)` ms and the independently checked
diagnostic window is `[500,1500)` ms; eventual drain is separate. For90 inputs,
the same rule gives `[0,3000)` and `[500,2500)` ms. These are short model
observations, not sustained native30 fps measurements.

| Exact cohort | Feedback | Old MA01 diagnostic IDs/s | AA01 IDs/s | AA01 strict/eventual |
| --- | ---: | ---: | ---: | --- |
| Combat primary60 |10 ms|29|29|57 /58|
| Combat primary60 |20 ms|29|29|56 /57|
| Second clip primary60 |10 ms|30|30|58 /59|
| Second clip primary60 |20 ms|29|30|58 /59|
| Combat held-out60 |10 ms|27|26|46 /46|
| Second clip primary90 |20 ms|29|30|88 /89|

The longer second-clip result improves the short diagnostic count, but strict
and eventual totals still miss90. Extra control traffic can lose the benefit:
held-out combat has ten DISPLAY cap rejections and an additional startup/control
burden, worsening27→26. There is no general asynchronous-refresh win.

The fault campaign loses the initial KEY ACK, loses the first transmitted
DISPLAY and duplicates ACK delivery. Exact KEY retry recovers without a third
anchor or guessed state. Final visible ID is59;52/60 eventually present.
Its30 diagnostic count does not erase initial losses or establish60/60 delivery.

Keys and retirement controls are never included in displayed counts. Actual
forward KEY/P/RETIRE IPv4-UDP bytes are all charged, with40 application+28
IP/UDP bytes per1,024-byte chunk. `control_wire_bytes` isolates the extra cost.
Quality compares common presented source IDs against MA01 in the artifact;
the reconstructed pixels still differ, so PSNR is not visual equivalence.

## Memory and limitations

Peak persistent anchor arrays at each endpoint are2,073,600 Python int16 bytes
(two518,400-byte logical8-bit YUV420 images). Old/new construction, coefficient,
prediction and output temporaries are additional. Shared packet-stage payload
peaks at94,000 bytes, within two49,152-byte slots, with at most two P credits
and three logical RGB roles.

An extra **host** compressed candidate retry cache peaks at39,238 bytes. It is
separately counted and is not silently included in the two receiver slots;
the same bytes can alias an in-flight KEY, so simple sums are conservative,
not an exact Python heap measurement. A replacement trades memory and control
work for reduced refresh drain. Actual target memory service, FPGA buffers,
native host performance and physical FPS remain unproven.

## Slower preparation sensitivity

`service_sensitivity.py` and `service-results.json` add four actual-codec cases
with declared32 ms scalar host preparation instead of2 ms. This value is
informed by the separate MT02 optimized Python measurement; it is **not** a
measured per-packet MA01/AA01 service trace, and actual key/tail costs vary.
All other declared services remain8 ms decode,10 ms feedback,8 Mb/s network,
160 Mb/s QSPI and60 Hz vblank. The same60 primary captures are selected from
each source, with actual re-encoding/CRC/pixel checks and charged control work.

| Primary60 | MA01 diagnostic IDs/s | AA01 IDs/s | MA01 strict/eventual | AA01 strict/eventual |
| --- | ---: | ---: | --- | --- |
| Combat |28|29|54 /56|54 /56|
| Second clip |27|28|53 /55|52 /55|

AA01 uses30,400/55,296 more forward wire bytes, or4.2%/5.5%, over the complete
runs including drain. There is no sustained30 fps pass; the second case even
loses one strict presentation while gaining a diagnostic count. These results
are a service-sensitivity counterexample, not a benchmark of the fast MA01
implementation or evidence that extra buffering removes the encoder limit.

Physical admission is the timed caller's responsibility. The codec alone bounds
DISPLAY credits but cannot infer when a DMA/reader stops using a packet. A caller
that repeatedly ACKs work without read-drain or slot admission can accumulate
reader metadata. The experiment's two-slot scheduler enforces admission and
drains it; receiver RETIRE trusts that sender proof and serialized receive.
These boundaries require explicit implementation before a real transport.

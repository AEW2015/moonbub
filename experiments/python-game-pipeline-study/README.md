# Finite GM01 capture, deadline, GF02 ingress and GA01 feedback replay

This Python experiment connects the actual combined codec/controller to real
laboratory chunk and feedback bytes. Every selected source is prepared against
its current ACKed immutable anchor; captures replaced while waiting are never
encoded. Per-call preparation durations drive a serialized virtual encoder.
The receiver either uses declared8 ms service or that packet's measured Python
`receive()` duration. Calls execute offline to discover costs; publication,
read-pin release, ACK and display occur only at scheduled completion events.

It is a finite software dataflow/ownership model, not a simultaneous sender/
ESP32/FPGA or physical30 fps result. The [GM01 reference](../python-game-codec-study/README.md)
and [GF02/GA01 transport](../python-game-feedback-study/README.md) remain separate
experimental formats that require new peer support. Installed JPEG/MSV1 peers
cannot consume them.

## Resources, deadlines and state

The model enforces two sender packet/transaction slots, two GF02 ingress slots,
two GM01 logical P credits and three front/pending/back framebuffer roles.
The sender owns one replaceable latest-capture waiting slot. A refresh is due
after30 capture IDs and waits for existing credits to drain. Oversize preparation
still pays its measured work; it does not send bytes or consume a codec credit.

Capture timestamps are fixed at hypothetical30 IDs/s. `acquisition_ms` is an
explicit external delay (default0); the clips have already been decoded/scaled
outside the model. A capture older than100 ms before preparation is dropped.
The complete preparation call includes both candidates if attempted and selected
key reconstruction. Its deadline is checked **after** the measured service ends:
no encode-stage drop refunds credit before that job completes. Receiver-queue
and decode-completion checks enforce the declared150 ms frame-age deadline.
Actual acquisition/scaling and live camera/desktop capture remain unmeasured.

Actual GF02 chunks are serialized on the forward link, fed through the new
bounded reassembler, then complete GM01 bytes take QSPI and decoder service.
Ingress assembly does not ACK a reference or release a delivered payload.
A complete payload remains pinned through QSPI/decoder read completion. Full
GM01 parsing, pixel hash verification and decoder completion precede actual
serialized GA01 feedback. Only the matching epoch/frame/**body-CRC tag** can
ACK the sender's pending reference. The GM01 footer is excluded from that tag;
CRC32 of the complete CRC-appended packet is a fixed residue and unsuitable as
a content-specific feedback identity.

Timeout/NACK can request expiration but cannot reuse its sender slot/credit/key
while encode, queued/active chunks, QSPI or decoder reads remain. Partial
assembly timeout and delivered-reader lifetimes are distinct. Feedback ACK
received while redundant forward work remains is deferred until physical data
work drains. Here “physical” is the tested single-threaded read-pin/role oracle;
there is no actual DMA/CDC, memory arbitration or scanout implementation.

## Declared timing and complete byte accounting

Defaults are independent ideal8 Mb/s forward/reverse links,160 Mb/s GM01-payload
QSPI,10 ms feedback propagation and60 Hz vblank. GF02 uses a31-byte header plus
canonical1024-byte chunks; nominal IPv4/UDP adds28 bytes. GA01 is24 bytes plus
28 IPv4/UDP bytes and consumes reverse-link serialization before propagation.
Lost data/feedback still consumes its transmitted wire bytes. Duplicate chunks
and feedback are charged for every copy. The old68-byte-per-chunk assumption
is not used here; forward GF02 cost is59 bytes per chunk before lower layers.

RF/shared-medium contention, lower-layer framing, transport retry policy,
actual QSPI framing, physical reference-memory and panel service are absent.
GF02 packetization/reassembly and GA01 construction/parsing really execute for
correctness, but their local CPU costs are not separately charged virtual
stages. Optional host reconstruction/hash verification, RGB565 conversion/error
metrics and source preparation are outside measured encoder/receive service.
The software decoder returns RGB888; no target-RGB565 timing is inferred.
Framebuffers are metadata roles; real decoded verification arrays, packetization
copies/queues, source arrays and codec transform/reference workspaces are extra
host storage. There is no target allocation/fit or bandwidth proof.

## Recorded cases

`results.json` binds source/input/version hashes for twelve actual-codec cases:

- Eight primary60-frame combinations: two clips × normal/cheap controller ×
  assumed/measured receiver.
- Two second-clip fault runs: initial key chunk0 loss, or initial key ACK loss;
  selected later duplicate chunk/feedback IDs are also configured.
- Two12-frame seeded noise→quiet recovery sequences, one per controller.

Fault IDs are capture IDs and later IDs can be skipped by overload. Initial ID0
is always prepared, so the initial key loss experiments definitely occur. Use
observed wire/error/timeout records rather than assuming every configured later
fault fired.

| Primary60 | Controller | Receive | Strict / eventual | Diagnostic IDs/s |
| --- | --- | --- | ---: | ---: |
| Combat |normal or cheap gate|assumed8 ms|57 /58|29|
| Combat |normal or cheap gate|measured Python|54 /55|28|
| Second clip |normal or cheap gate|assumed8 ms|58 /59|29|
| Second clip |normal or cheap gate|measured Python|52 /55|27|

Strict is `[0,2000)` ms; diagnostic is `[500,1500)` ms; eventual includes a
separate1,000 ms drain. No case reaches30 diagnostic IDs/s or delivers every
capture. Strict-window p95 age is66.7 ms with assumed receive,83.3 ms for measured
combat and100 ms for measured second clip. Nominal sender preparation alone is
not the full latency or cadence budget.

The initial key chunk-loss case presents49 strictly/51 eventually, diagnostic27.
Its missing fragment reaches partial timeout, emits a bound NACK and recovers
with a fresh independent key. Initial key ACK loss presents47/50, diagnostic28;
the receiver decodes the key, but the sender cannot use it without its ACK and
must recover after timeout. Those startup losses remain visible.

Both stress cases eventually display all six quiet inputs and reject every
actually attempted noisy candidate. Normal prepares8 of12 captures, cap-rejects2
and replaces4 waiting sources; the cheap gate prepares all12 and cap-rejects6.
Thus lower noisy preparation cost lets it inspect more bad captures but admits
no additional displayed frame in this fixture. Cheap rejection does not create
capacity for noise. Stress strict count is5 and eventual6; its short400 ms
capture interval has no diagnostic FPS window.

Across all cases there are624 capture-policy evaluations,576 actual preparations,
567 hash-checked decodes and567 eventual presentations. Every sender/ingress
slot, credit, waiting capture and disposition drains. Forward IPv4/UDP bytes
total6,399,336 and feedback29,588 across these different runs; those sums include
drain and are not a single-link rate measurement. Main fault timeouts happen
after data work drains. A separate deterministic test forces a20 ms timeout
during65 ms receive and verifies that release waits until the decoder finishes.

## Reproduce and independent checks

Use the common pinned environment and media files outside Git:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python verify.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python analysis.py
```

Seven tests use real small packets and an injected work clock. They verify exact
7 ms encoder/11 ms receiver service, exclusion of a900 ms verification oracle,
serialized feedback, acquisition delay, paid post-prepare deadline and cap drops,
latest-source overload, midpoint timeout/read-pin drain, chunk loss/corruption,
ACK loss/duplicates/wrong epoch, reordered multichunk input and finite outcomes.

`verify.py` independently recomputes strict/diagnostic metrics, source bindings,
capture conservation, actual GF02/GA01 bytes and feedback propagation, charged
stage endpoints and safe slot release. It checks every enqueued feedback copy
finished serialization/delivery or simulated loss. `analysis.py` compares common
presented IDs/MSE separately; equal totals alone are not equal input histories.
Profile case order reverses between clips, but host load/warmup/affinity remain
uncontrolled and runtime-dependent capture choices can vary on rerun.

The sources remain related precompressed25/29.88 fps Mass Effect clips with
repeated content, sampled natively then scheduled at hypothetical30 IDs/s.
The60-frame primary windows stay before the4-second held-out boundary. This
is not native30-distinct-frame/s capture, broad game coverage, real visual/HUD
acceptance or a hardware run. Next measure capture/scale and native transport/
decoder/memory service, extend phase/loss/load/long-corpus coverage and integrate
a real peer contract before a physical30 fps qualification claim.

# Measured BOX and transport CPU stages around finite GM01

This extends the frozen [v9 finite model](../python-game-pipeline-study/README.md)
in a **new** Python study. GM01, the controller/cheap gate, GF02 and GA01 source
files are unchanged. It closes a specific timing omission: actual datagram
construction, every reassembly `feed`, and feedback construction/parsing now have
measured service durations that can be charged before downstream publication.
Native RGB inputs also pass through a measured Pillow BOX/letterbox stage.
Offline PyAV extraction remains outside the model; BOX resizing is preprocessing,
**not measured desktop acquisition**.

## Stage contract

`model.run(..., Config(transport_cpu=True, resize_cpu=True))` charges these
additional stages. With the two flags false, the same real calls still execute
and their durations/hashes are recorded, but their virtual service is zero.
Full GM01 preparation and measured receiver service remain paid in both baseline
modes. Failed oversized preparation and failed `feed`/feedback parse calls retain
their measured cost. Optional expected-RGB verification, hashes and quality
metrics are outside service timers.

Each stage is one serialized virtual server: BOX preparation, encoder,
packetization, forward link, per-chunk ingress CPU, QSPI, decoder, feedback build,
reverse link and feedback parse. Distinct servers can overlap virtually. This is
an explicit service graph, **not a shared physical CPU scheduler**: it does not
prove that a single ESP32/PC core can execute all these calls concurrently.
Runtime calls execute sequentially offline to discover their durations.

The capture schedule is still hypothetical30 IDs/s. An external assumed
`acquisition_ms` delay defaults to0. At most one resize is active and one latest
native capture waits; a newer capture replaces that waiting source. Resized
captures likewise replace the encoder's latest waiting source. BOX service
includes Image.fromarray, Pillow BOX resize, a zero canvas and pixel copy; source
file read/decode, OS capture, GPU capture and any GPU-to-host transfer are absent.

The encoder's real preparation API commits synchronously. This scheduler holds
that result privately, restores the visible semantic reference/credit state,
and publishes only at `encode_done`. Publication merges the new transaction with
current pending state, preserving P ACK removals occurring during preparation.
A rejected candidate never publishes a transaction. This is Python simulation
scaffolding around the unchanged API, not a new native asynchronous encoder.
Receiver semantic state is similarly published only at `decode_done`.

Packetization emits no forward chunk before its CPU service completes. A
complete reassembly remains pinned across charged feed, QSPI and decode. A
feed call mutates the offline reassembler oracle at its virtual start, but its
result is not handed downstream until completion; partial expiry is deferred
while that feed server owns the oracle. Queued/active ingress CPU, packetization,
feedback build/parse and decoder owners prevent unsafe sender-credit reuse.
ACK follows complete GM01 reconstruction and read-pin release, actual GA01 build,
wire serialization, propagation and parsing. ACK identity binds epoch/frame and
GM01 body CRC, excluding the appended CRC footer.

Two sender slots, two ingress payload slots, two GM01 credits and three
front/pending/back metadata roles remain enforced. Feedback has four bounded
in-flight descriptors, including construction, wire/propagation and parse;
excess copies are explicitly dropped. Copies within that bound are built and
charged individually. Source arrays, resized/oracle/output arrays, packetization
copies/queues, transforms and immutable references are additional host memory.
The metadata roles and counts are not a physical memory/DMA/CDC fit proof.

Defaults retain assumed independent8Mb/s links,160Mb/s GM01-payload QSPI,
10ms feedback propagation,60Hz vblank,100ms preencode age and150ms frame deadline.
GF02 wire accounting uses actual31-byte headers and up to1024 payload bytes,
plus28 nominal IPv4/UDP bytes; GA01 is24+28 bytes. Data/ACK loss and duplication
still pay transmitted bytes. Radio/lower-layer framing, sockets, target CPU,
real QSPI framing and panel scanout remain unmeasured.

## Tests and reproduction

Fourteen deterministic-clock tests use actual small GM01/GF02/GA01 packets.
They verify paid fixed stage costs, byte-identical GM01/transport/feedback/BOX
outputs under zero-versus-charged service with an unchanged reference history,
causal encoder publication, feedback after decode/read finish, retained ownership
through timeouts during feed/decode/parse, paid corrupt-input/feedback rejection,
bounded duplicate-feedback descriptors, latest-capture replacement, cap rejection
and finite conservation. Small injected service costs are test values, not
measured hardware performance.

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python verify.py
```

The benchmark contains eight cases: two60-source pairs with zero/charged added
CPU, two charged initial-key fault cases, and two12-source noise recovery cases.
Preparation and receive durations are **remeasured for each case**. Thus the
paired source hashes are identical but timing, selected IDs and key histories
can differ. Stored common prepared/presented IDs and actual packet hashes are
reported; differences cannot all be attributed to the tiny added CPU services.
Profile order reverses between the real clips; host load/affinity/warmup are not
controlled. `verify.py` independently checks stored stage causality, conservation,
wire accounting, publication and drain state without rerunning codec/timing.

`results.json` pins executed source files, runtime versions, media/native RGB
hashes and selected PTS. The sources remain related, precompressed25/29.88fps
Mass Effect footage, sampled natively then scheduled at hypothetical30 IDs/s.
The benchmark is short, includes repeated content and is not live capture,
native30-distinct-frame coverage or a hardware30fps result. No GH01/HG01 lossless
patch wrapper is integrated into this GM01 pipeline.

## Stored results (2026-11-03)

| Same60 native sources | Added CPU mode | Strict / eventual | Diagnostic distinct IDs/s |
| --- | --- | ---: | ---: |
| Combat | zero added CPU |54 /55|28|
| Combat | measured BOX + transport CPU |54 /55|28|
| Second clip | zero added CPU |54 /56|27|
| Second clip | measured BOX + transport CPU |54 /56|27|

Strict is `[0,2000)`ms and diagnostic is `[500,1500)`ms. Eventual includes a
separate1000ms drain. These are distinct counts; none establishes30fps. Both
pairs happen to select exactly the same IDs and produce identical GM01 packet
hashes:55 combat and56 second-clip prepares/presentations. Repeated measurements
are not a controlled general performance ablation, even when these particular
histories match. Charged strict-window p95 age is66.7ms combat and100ms second.

| Charged operation, mean wall time | Combat | Second clip |
| --- | ---: | ---: |
| BOX resize/canvas per source |1.551ms|3.324ms|
| GF02 packetization per packet |0.01973ms|0.02274ms|
| Reassembly per delivered chunk |0.00463ms|0.00510ms|
| GA01 build per feedback copy |0.00925ms|0.00918ms|
| GA01 parse per received copy |0.00733ms|0.00874ms|

Combat's native input is512×288 and the second clip is1280×720; both are BOX
aspect-fit into720×480. These measured Python operations are not ESP32/native
CPU service. Transport CPU totals4.321ms over55 combat packets/502 fed chunks
and5.843ms over56 second packets/699 fed chunks. BOX totals93.041/199.431ms over
60 sources each. Those sums belong to distinct serialized stages; adding them
does not yield per-frame end-to-end latency. The dominant paid codec work still
has mean P preparation19.05/19.56ms and P receive20.56/23.71ms, with key costs
recorded separately. No tiny transport operation replaces complete-frame work.

Charged initial-key chunk loss yields50 strict/52 eventual; ACK loss48/50.
Both have28 diagnostic IDs/s, so that middle-window number hides their real
startup losses. These cases retain their timeout, duplicate and wire evidence.
All active/queued CPU and data owners drain.

The seed1009 noise→quiet stress is separate from v9's seed909 fixture. Normal
prepares6 inputs, pays296.60ms across3 rejected noisy preparations, replaces6
waiting inputs and presents2 strictly/3 eventually. Gate prepares12, pays95.97ms
across6 rejected noisy preparations and presents5 strictly/6 eventually. This
illustrates how bounded high-entropy rejection can preserve more quiet captures
in this modeled workload; it is not a paired wall-time benchmark or a claim
that noise becomes encodable. Its400ms capture interval has no diagnostic FPS.

Across all eight runs:384 capture-policy inputs,343 actual preparations,
333 hash-checked decodes and333 eventual presentations. Actual nominal IPv4/UDP
traffic sums3,819,761 forward bytes and17,420 reverse bytes across the different
runs, not one throughput measurement. `verify.py` passes17 executed-source pins
and both external media hashes. `summary.json`, `results.json`, `run.log`,
`tests.log` and `verify.log` retain the evidence.

## Portable stored-result check

`python check_stored_results.py` repeats the stored causality/conservation checks
without rewriting the frozen summary. Recorded repository source paths resolve
relative to this checkout; absent external media are listed separately. Use
`--write-summary` only when deliberately regenerating that helper's summary.
The original benchmark-pinned `verify.py` remains unchanged and expects the
recorded media paths. Neither command reruns encoding or target service.

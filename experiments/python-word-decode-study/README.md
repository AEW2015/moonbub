# Bounded word-lookahead CP02 decoder

This Python-only prototype changes CP02 bit parsing while keeping the frozen
MA01/MT02 coefficient syntax, Q14 inverse, color conversion, CRC/range checks
and reference semantics. It is not an FPGA decoder, hardware schedule, installed
Sunshine/Moonbub mode or concurrent real-time result.

`word_coeff.py` keeps at most 64 prefetched bits in a reservoir. A Rice read
looks ahead at most 15 prefix bits and counts their leading zeros instead of
calling a per-bit reader repeatedly. It retains the exact 14-bit DC and 12-bit
AC escapes and rejects noncanonical escape values. Combined two-bit AC tags
handle EOB/ZRL in one read; nonzero tags supply the first run bit. Refill slices
at most eight bytes, rather than shifting a whole-payload integer. Input length,
CRC, expected geometry, RAW coefficients, reconstructed DC, AC run/ZRL bounds,
coefficient ranges and zero tail padding keep the frozen checks.

`word_receiver.Receiver` implements MT02; `word_receiver.AnchorReceiver`
implements MA01. They replace only coefficient parsing, retaining golden
prediction, inverse, RGB and snapshot operations. They do not monkeypatch old
module globals. Optional stage timing is metadata, not a packet decision.

## Reproduce and finite compatibility evidence

Use the common [pinned environment](../python-codec-study/requirements.txt)
and media outside Git. From this directory:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python scheduler_probe.py
```

Seven tests compare accepted coefficient arrays and rejected malformed inputs
against the frozen decoder. Cases include 80 deterministic coefficient families,
all 64 zigzag positions, RAW fallback, ±2,048 coefficients, ±4,096 DC deltas,
canonical escape boundaries, CRC, truncated unary/remainder bits, full/dirty
padding, overrun tags, invalid expected geometry and a valid-CRC byte-mutation
campaign. A separate seeded campaign checks 2,000 valid-header/valid-CRC random
payloads for identical acceptance/rejection and values. MA01 key/P/refresh,
replay and damaged-frame tests verify unchanged visible/reference state after
rejection. Reservoir tests assert the 64-bit bound. This is finite differential
coverage, not a formal all-packet equivalence proof or generalized hostile-input
qualification. The extra fuzz test was added after timing without changing
benchmarked sources; the final parent snapshot can bind it.

## Paired decoder timing

`results.json` records 72 full packet pairs and 216 coefficient-plane pairs.
The token-key encoder produces twelve consecutive native frames starting at
4 s from each Mass Effect source, in three independent repetitions. Each pair
uses the same packet bytes and reference history, rotates old/new timing order,
and checks exact coefficient arrays, receiver RGB, metadata and host expected
hash. The twelve images are reused; these are not 72 independent source images.
Original source rates remain 25/29.88 fps and repeated content is explicit.

| Actual Python receive mean | Frozen | Word parser |
| --- | ---: | ---: |
| Combat, all packets |23.99 ms|22.02 ms|
| Combat, key only (3 samples) |62.93 ms|49.27 ms|
| Combat, P only |20.45 ms|19.54 ms|
| Second clip, all packets |31.49 ms|27.60 ms|
| Second clip, key only (3 samples) |41.74 ms|35.30 ms|
| Second clip, P only |30.55 ms|26.89 ms|

The isolated three-plane coefficient-parse means change 15.24→13.40 ms and
23.06→19.22 ms. Full receive speedups are 1.09×/1.14× on these runs; key speedup
is larger but its tail still misses 33.33 ms (maximum 53.46/35.83 ms). The
mandatory inverse/color and retained reference work remain unchanged. Parsing
is not the complete decoder or a latency/FPS guarantee.

Timing is actual Python wall clock under uncontrolled background host load,
without affinity or isolated warmup. Full receive includes parser, reconstruction,
RGB, snapshot and adapter operations; it excludes source acquisition/scale,
encoder, verification/hash metrics, transport and display. Stage clocks add a
small observation overhead. The study has already-used precompressed related
footage, not held-out visual quality or native 30-distinct-frame/s evidence.

## Four finite service replays

`scheduler-results.json` uses the actual token encoder and word receiver as
factories in the [measured-service model](../python-measured-service-study/README.md).
Actual preparation drives the host stage; actual receive either drives the
receiver stage or is recorded beside assumed 8 ms service. Each selected frame
is re-encoded against its ACKed immutable anchor; no packet/reference history is
substituted from another run. Network 8 Mb/s, QSPI 160 Mb/s, feedback 10 ms and
60 Hz vblank remain assumptions. Source capture/scale, lazy oracle, physical
memory and RF/feedback overhead are absent. The configured `fast_key` label is
an API compatibility label; the artifact explicitly names both actual factories.

| Primary60 / receive service | Strict / eventual | Diagnostic IDs/s |
| --- | ---: | ---: |
| Combat / assumed8 ms |55 /56|28|
| Combat / measured Python |49 /51|26|
| Second clip / assumed8 ms |56 /58|30|
| Second clip / measured Python |45 /47|24|

Strict is `[0,2000)` ms, diagnostic `[500,1500)` ms, then 1,000 ms drain.
**One case counts30 IDs/s only in a one-second diagnostic interval; it still
misses four strict presentations and two eventual captures.** It is not a
sustained30fps pass. All four cases drain slots, P credits, waiting capture and
classified outcomes. The measured receiver cases remain below30 diagnostic IDs/s.

These sequential service replays use endogenous per-call timings and select
different captures from previous runs. In particular, the assumed-receiver
result cannot be credited to receiver speed because it still charges 8 ms.
Use the paired same-packet benchmark for decoder speed; these model observations
only expose behavior under their recorded measured/assumed services. Physical
memory service, FPGA fit and true concurrent host/ESP32/FPGA execution remain
required gates.

# Exact shared incumbent / strict-band pair

`model.encode_pair(module, prepared, q, rdo_lambda=1)` returns two ordinary
`(GM27_packet_bytes, reconstructed_YUV_planes, work)` triples in incumbent,
strict-band order. Pass the runtime-v28 module that owns `prepared`.

The function shares one quantization, one RDO execution, all incumbent legacy
fallback comparisons, one incumbent entropy plan per plane, and one incumbent
reconstruction. It constructs the incumbent plane payload once and reuses it
when the band winner stays incumbent. The band result reuses unchanged output
planes and reconstructs a winning changed plane once. Output planes retain the
frozen encoders' read-only contract. All temporary plans are private to the
call; there is no persistent cache, module monkeypatch or wire-format change.
The complete paid work is available in either result's `work['shared_pair']`.
Do not add that shared counter twice.

The incumbent still wins equal representation lengths. Original coefficients
replace RDO coefficients only when their legacy representation is strictly
shorter. Band candidates retain their frozen order and the first minimum wins.
The exact frozen cutoff/source-error/protected-block checks execute for every
band candidate; no candidate is inferred from earlier frames or skipped.

On the first 12 accepted frames from each of the two frozen v32 `band_control`
histories (24 source frames, 46 motion/background pairs, 92 actual packets),
all old/new packet bytes, individual plane payloads, and reconstructed pixels
matched. They also matched the retained v32 attempt packets. These windows
actually attempted background 16 only; tests additionally cover background 8
and 32. Three paired samples alternate old/shared order, with fresh private
setup on every invocation and no unreported warmup.

| Paid pair measurement | Old separate calls | Shared pair |
| --- | ---: | ---: |
| Mean encode time | 127.052 ms | 85.170 ms |
| Quantization calls | 92 | 46 |
| RDO calls | 92 | 46 |
| Legacy size-counter calls | 1,668 | 852 |
| EC26 packet constructions | 276 | 226 |
| Inverse-plane calls, including RDO | 1,092 | 634 |

Aggregate speedup was **1.492x** (32.97% lower paid pair time); median paired
speedup was 1.495x. Fifty incumbent plane payloads were reused by the band
output. Timing is one local host observation, with no performance assertion in
the tests.

Separate `tracemalloc` runs on each scene's first q16 key pair measured peaks of
16,429,429 versus 15,392,667 bytes and 16,440,540 versus 15,403,762 bytes. These
are traced transient allocations, not process RSS or a proof of all-frame peak
memory. The per-call coefficient byte counter conservatively sums allocations
and can double-count aliases. No cached state persists after the returned
results are released.

Pair time includes validation, private setup, quantization, RDO, all band
trials and size plans, winner serialization, reconstruction, output hashes and
both GM27 envelopes. It excludes forward analysis/motion search, fixture reads,
parity checking and decoding, archive I/O, HUD coding, RGB quality scoring,
transport, gateway and display work. This is an offline Python encoder study;
neither physical 30fps nor end-to-end service improvement is established.

`helpers.py` imports the same frozen source conversion, adaptive analysis,
runtime and band helpers used by controller-v32 through explicit paths; it
does not bind generic `model`, `protocol`, `controller` or `benchmark` import
names. `results.json` includes 1,017 source/input hashes, parent commit identity,
three paid samples per pair, original and shared counters, deterministic packet,
plane-payload and output-plane hashes. `objects/` retains compressed actual
packets. Frozen <=v32 sources are unchanged.

Run from the repository root:

```sh
PY=/home/lori/gamebub-streaming-prototype/.venv/bin/python
$PY -m unittest discover -s experiments/python-game-shared-v33-study -p test_model.py -v
$PY experiments/python-game-shared-v33-study/benchmark.py
$PY experiments/python-game-shared-v33-study/verify.py
```

The three unit tests cover 72 key/P, q8/16/32 and lambda0/1/1e6 combinations,
invalid inputs, read-only outputs, and a real legacy fallback: pruning a q16
DC block at equal source SSE increases its legacy plane from 38 to 39 bytes,
so both implementations revert. `verify.py` independently verifies source
pins, every retained actual packet and decoded output, each accepted reference
history, and reruns both the frozen pair and shared pair over all 24 inputs.
`--archives-only` explicitly disables re-encoding while retaining packet and
source checks.

# Byte-identical host preparation optimizations

This Python-only study reduces host work while preserving the frozen CP02,
FT02, MT02 and MA01 packet syntax and reconstructed pixels on the tested inputs.
It changes neither the installed Sunshine sender nor ESP32/FPGA software.

`fast_coeff.py` batches sparse AC discovery, caches Rice bit strings and skips
empty blocks without rescanning each remaining block. Quantization, DC row
reset, band contexts, EOB/ZRL, RAW fallback, bounds and CRC stay unchanged. The
frozen decoder is used independently to check the resulting bytes.

`fast_motion.py` substitutes that serializer in MT02. It retains host IDCT and
YUV reconstruction because every acknowledged MT02 frame becomes a predictor.
`fast_anchor.py` additionally removes host reconstruction for MA01 P frames:
only an immutable key anchor becomes a future predictor. P output does not need
to be reconstructed at the host before transmission. Key preparation remains
unchanged. An optional lazy RGB/hash oracle reconstructs P output outside timed
preparation for verification. The existing two-credit default bounds pending
packets; the optional host oracle retains an already-produced packet reference
until ACK/expiry. That cache is additional host ownership, not receiver RAM or
an integrated wire ACK/drain protocol. Production use can omit the oracle.

## Reproduce

Use the existing [pinned Python environment](../python-codec-study/requirements.txt)
and source media outside Git. From this directory:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark_anchor.py
```

Each benchmark loads twelve consecutive native frames starting at4 s from
each Mass Effect source, scales with the common720×480 canvas, then repeats
three independent runs while alternating original/optimized timing order.
Source file, native PTS, rendered image, executable source and result hashes
are recorded. Source rates are25/29.88 fps and content repeats remain; replaying
the same twelve frames three times is not a36-distinct-frame corpus.

`results.json` has72 actual MT02 old/new packet pairs; `anchor-results.json`
has72 MA01 pairs. Complete packet bytes and receiver RGB/hash are identical
within each pair. Ten unit tests include80 deterministic coefficient families covering
sparsity, DC reset, extreme coefficients, RAW fallback and width contexts;
small frame/key/epoch/credit/expiry tests exercise state compatibility. This is
finite regression evidence, not a formal equivalence proof for all inputs.

## Measured preparation costs

These are actual Python wall-clock calls on this host under uncontrolled
concurrent load, with no affinity or isolated warmup. Decode/scale of source
video, optional RGB oracles, network, QSPI, presentation and decoder service
are outside the preparation timings. MA01 original preparation eagerly computes
an RGB oracle; the optimized path defers that unnecessary production work.

| Profile / source | Original median | Optimized median | Optimized p95 |
| --- | ---: | ---: | ---: |
| MT02 combat, all frames |47.46 ms|30.80 ms|37.84 ms|
| MT02 second clip, all frames |58.04 ms|31.59 ms|35.16 ms|
| MA01 combat, P only |53.97 ms|24.87 ms|26.64 ms|
| MA01 second clip, P only |61.34 ms|22.86 ms|23.71 ms|

MT02 mean-time speedups are1.64×/1.86×. MA01 P mean-time speedups are2.15×/2.68×.
No quality or compressed-size saving is claimed: the tested wire bytes match.
This optimization uses the host/FPGA split to remove host work while leaving
the FPGA's required display reconstruction intact.

**Keyframes remain expensive.** MA01 optimized key means are111.19/77.83 ms;
all-frame optimized means are32.13/27.29 ms but all-frame p95 values are
106.32/77.69 ms. Only three key measurements per source are present, so the
key tail is particularly weak statistical evidence. P timing below33.33 ms
on this small cohort does not establish an end-to-end30 fps stream. MT02 tails,
key stalls, capture/scale, receiver throughput and memory/link service remain
outside a passed30 fps gate.

The next useful work is to batch/compile host entropy and key reconstruction,
reuse source transforms across bounded quality trials, measure a native sender,
and implement an overlapped key schedule with measured services. Keep
byte/pixel compatibility and a bounded key/packet lifetime as acceptance gates.

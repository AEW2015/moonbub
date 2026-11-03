# Faster MA01 key preparation with a lazy verification oracle

This Python-only study continues the [v5 host optimization](../python-fast-entropy-study/README.md).
The v5 MA01 P path already skips host P reconstruction; its keys still called
the frozen slow serializer and eagerly constructed verification RGB. This
prototype optimizes those keys while keeping **exact MA01 packet bytes,
reconstructed pixels and ACK/reference semantics** on the tested inputs. It
adds no installed Sunshine, ESP32 or FPGA mode.

`key_encoder.Encoder` has the same constructor, `prepare`, `expected_hash`,
`ack`, `expire`, credit and reference-byte API as the frozen MA01 encoder.
Key preparation uses v5 fast CP02 serialization, reconstructs the required YUV
anchor, and freezes those newly-owned planes directly. The source and old
anchor do not alias them, so a second snapshot copy is unnecessary. It emits
the same CRC-protected MA01 bytes directly, avoiding a redundant remagic pass.
Verification RGB/hash is lazy: `expected_hash` computes it on demand outside
production preparation. P preparation remains the unchanged v5 implementation.
`last_prepare_stages_ms` is observational instrumentation; it cannot change
packet or quantizer decisions.

## Compatibility and ownership

The five unit tests cover key/P byte and decoded-hash equality, quantizers
1/8/16/32/128, zero/global motion, even geometry with partial8×8 blocks,
forced refresh, two credits, stale/wrong-epoch ACKs, duplicate ACK, expiry,
input failure without state mutation, delayed P oracles and source/anchor
non-aliasing. Key arrays are read-only; P ACKs never replace the immutable
anchor. Keys cannot replace it until pending P credits drain, as in MA01.
Physical DMA/read-drain and serialized ACK transport remain external gates.

One720×480 YUV420 anchor contains518,400 logical8-bit sample bytes. Retained
Python int16 planes use1,036,800 bytes per endpoint. During replacement an old
anchor and newly constructed planes can briefly coexist; prediction,
coefficients, transforms, source arrays, RGB verification and decode temporaries
are additional. The direct freeze removes one avoidable host snapshot copy,
not the reconstructed anchor or FPGA reference memory requirement.

A key oracle retains no compressed key packet. P verification inherits a packet
reference until ACK/expiry; this is bounded by configured credits and codec
geometry, **not** automatically by the scheduler's48 KiB admission cap. The
benchmark ACKs every pair before the next capture and therefore does not
measure two-packet cache concurrency. Its maximum retained P oracle packet is
reported in each record. This is host ownership, not a receiver RAM saving.

## Reproduce

Use the existing [pinned environment](../python-codec-study/requirements.txt)
with NumPy2.5.4/Python3.14.4. Media remains outside Git with source-file,
native PTS and scaled-image hashes in the manifests. From this directory:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
```

The benchmark records **96 paired triples**:72 mixed key/P cases (twelve
consecutive4 s native frames per clip, three independent repetitions) plus24
independent key cases (six alternating input indices from each1 s/4 s cohort
of the two Mass Effect sources). Every triple checks frozen MA01, v5 lazy-P
and new fast-key packet bytes and receiver RGB hash. Repeated sources and
frame indices are explicitly recorded; these are not96 distinct images or
native30 fps capture evidence. The source rates remain25/29.88 fps.

Each triple rotates timing order across variants. Preparation is actual Python
wall-clock time on this host, under uncontrolled concurrent load, with no CPU
affinity or isolated warmup. Source decode/scale, optional RGB/hash oracle,
receiver validation, network, QSPI and presentation are excluded. Removing the
eager verification oracle is valid production work elimination, but its cost
is still measured separately in `oracle_ms`. Timing jitter means the unchanged
P implementation can differ slightly between same-run variants.

## Results

| Actual host key call | Frozen MA01 mean | v5 mean | New mean | New p95 |
| --- | ---: | ---: | ---: | ---: |
|24 independent keys|90.49 ms|90.29 ms|**33.27 ms**|36.00 ms|
|Combat mixed run,3 keys|111.25 ms|111.05 ms|44.11 ms|48.73 ms|
|Second clip mixed run,3 keys|80.20 ms|79.72 ms|32.76 ms|32.97 ms|

Independent keys improve **2.71× in mean preparation time** versus v5. Their
median changes92.87→34.15 ms, but **12/24 still exceed33.33 ms**. The second
clip's small mixed run stays under that budget, while combat does not. This
is progress on the key-stall bottleneck, not sustained end-to-end30 fps proof.
The mixed run's higher key tail also cautions against quoting the independent
key mean as a universal constant or substituting it for actual per-call service.

| New independent key stage | Mean |
| --- | ---: |
|RGB→planes and constant predictor|5.85 ms|
|Transform and quantization|8.71 ms|
|CP02 entropy serialization|12.92 ms|
|Required YUV reconstruction and freeze|5.71 ms|
|Packet assembly and state commit|0.02 ms|

Entropy remains the largest measured component, followed by transforms. The
next opportunity is a compiled/batched host serializer and arithmetic kernels,
while retaining the frozen integer rounding and coefficient bounds. A finite
scheduler should consume per-key/P measurements rather than assuming a32 ms
scalar for every capture. Actual capture/scale, decoder/memory/link services,
longer disjoint footage, HUD/temporal quality and physical target qualification
remain open gates.

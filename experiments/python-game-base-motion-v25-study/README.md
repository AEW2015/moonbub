# GM25: bounded integer block motion and exact residual reconstruction

This Python frame component tests a stronger temporal base for the Gamebub
application-specific codec. It preserves the frozen integer RGB/YUV conversion,
Q14 8×8 transform/inverse, ROI8/16/32 quantizers, CP02 coefficients and exact
reconstructed-reference tag. It is a new laboratory `GM25` grammar. Existing
AR03/CP23 peers do not decode it, and no native endpoint or FPGA RTL is changed.

## Predictor and entropy tools

Keys predict constant128. P frames reference the exact supplied reconstructed
YUV420 bank, identified by epoch, frame ID and SHA256[:16] of the canonical
little-endian int16 planes. Original source captures are never references.

Motion blocks are16×16 or32×32 luma pixels. Each uses an even integer `(dx,dy)`
within−8..+8; chroma uses the half displacement and half block dimensions. The
normative predictor reads reference `[clamp(y+dy),clamp(x+dx)]`. There is no
fractional-pixel interpolation, multiple-reference list, affine motion or loop
filter. Parent code must hold the referenced bank until every reader drains.

`zero`, `global` and `block` search policies all use current source data only.
The latter two test81 even vectors. Block selection minimizes actual luma SAD
plus twice each chroma SAD; optional nonzero-vector penalty is a declared host
policy. Deterministic ties prefer zero then short vectors. This is not
rate-distortion optimization or a guarantee that motion always saves bytes.
Every search candidate's full sample comparison count and host time are paid.

The vector map chooses the actual smallest canonical global, dense, run-length,
packed-nibble or sparse-default representation. Each legal even component maps
to nibble0..8, so the packed map costs one byte/vector. Sparse maps declare the
most frequent packed vector (lowest value on a tie), then sorted uint16-indexed
exceptions. Quantization retains a separate16×16 map even with32-pixel motion
blocks. Residual planes choose actual dense CP02 or the existing structured
zero/DC/full SP01 grammar. An entirely zero coefficient plane is one byte.
Zero residual means exact quantized residual SKIP, not approximate pruning; all
transform/quantization work still executes before that decision.

Optional `rdo_lambda>0` adds **lossy P-only SKIP**. For each eligible nonzero8×8
coefficient block it measures the difference between actual clipped source-YUV
SSE for zero residual and quantized reconstruction. It discards the residual
when that increase is at most lambda times a paid coefficient-bit proxy. DC
costs16bits; full-block probes construct actual isolated CP02 packets and count
their bodies. These are marginal-cost proxies: plane-wide DC prediction and
token packing change the final actual bit cost. Every probe is counted/timed.
The encoder also constructs original/pruned complete plane payloads and keeps
the smaller actual one. Final decoded samples define the next reference tag;
original pixels never silently enter the loop. Scale8 priority blocks and their
chroma interpolation halo are protected. Keys and lambda0 retain original
quantized coefficients. Native quality/bitrate results, rather than the proxy,
must decide whether this option is useful. This is not HEVC/AV1 RDO.

The encoder shares dense CP02 work with the structured alternative. Both actual
entropy candidates are paid. Inverse reconstruction clips after prediction plus
residual, with both frozen rounding boundaries unchanged. A full reconstructed
YUV tag follows every frame and is independently checked by the decoder.

## Prepared-analysis API

```python
p = analyze_planes(source_yuv, reference_yuv_or_none,
                   epoch=1, frame_id=frame_id, reference_id=reference_id,
                   block_size=16, motion_mode="block")
packet, reconstructed_yuv, work = encode_prepared(p, quantizer_map, rdo_lambda=0)
decoded, metadata = decode(packet, reference_yuv,
                           expected_epoch=1,
                           expected_reference_id=reference_id)
```

`analyze_planes` performs one real vector search/prediction and three raw forward
transforms. It returns read-only prediction/raw-coefficient/source arrays and paid work
in `p.work`. `encode_prepared` executes new quantization, entropy alternatives,
inverse reconstruction, hashing and serialization for each map attempt. It
reports zero new search/forward calls; the caller must pay `p.work` once across
the whole source decision, including if all candidates reject.

`encode_planes(source,reference,map,...)` is the one-shot compatibility wrapper;
it charges both phases. For a key use `reference=None, reference_id=NO_REF`.
For a P frame, decode requires the expected reference ID as well as matching
actual reference bytes/tag. Missing, wrong or mutated reference content rejects.

At720×480, prepared prediction and int64 raw coefficients occupy5,184,000 named
array bytes; retained int16 source YUV adds1,036,800, for6,220,800 total named
array bytes, plus the small vector-map bytes. This is host-side planning storage,
not ESP32 SRAM, total NumPy heap or FPGA BRAM/DSP fit. Search temporaries,
quantized coefficients, decoded arrays, packets and reference banks are extra.
Read-only NumPy flags are a trusted local contract, not an adversarial boundary.

## What this component does not own

Frame selection, issued identity, ACKs, bank publication, source/read leases,
cap admission, refresh policy, transport and display are parent responsibilities.
Decode is a pure isolated-packet operation and does not reject replay by itself.
It validates CRC, bounded exact grammar, reference identity and reconstructed tag
before returning output; it never mutates source/reference arrays.

The parser accepts bounded diagnostic frames up to2,000,000 bytes so noisy
candidates can be measured and rejected honestly. This is **not** a relaxation of
the49,152-byte complete streaming cap. Parent admission must include GM25, exact
HUD, binding and every other complete-frame byte before deciding to commit.
No 30-fps, native CPU/ESP32/RF, DMA, memory-port or fitted FPGA claim follows.

## Tests and native campaign

Fifteen tests verify key/P roundtrip, frozen zero-MV coefficient/output parity,
known exact translation, independent scalar luma/chroma edge prediction,
partial macroblocks, canonical global/dense/RLE maps, domain/length/CRC/tag
rejection, reference binding and shared-prepared versus repeated-analysis parity.
Additional coverage checks nibble/sparse canonicality, invalid codes/indices,
lambda0/key parity, source retention, positive-lambda decoder loop, protected
priority coefficients and zero-residual behavior.
The64×64 translation control produces a90-byte P packet after a2,729-byte key;
it is deliberately favorable synthetic evidence, not a gameplay rate.

```sh
python -m unittest -v test_model.py
```

The parent native-source campaign supplies bitrate, image quality, cap outcomes,
reference-update costs, retained goldens and standalone replay. Root reports must
keep its live reference policy distinct from HEVC/AV1's own reference history and
the old eight-frame custom update policy. Raw search gains on constructed motion
are not evidence of typical game compression or practical host FPS.

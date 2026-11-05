# SP38 pilot: tile-local spatial prediction is not yet a compression win

This new Python research profile adds vertical, horizontal and DC residual-edge
prediction to a fixed-zero temporal base. It is an actual serialized codec with
an independent decoder, not a free intra-mode oracle. The initial pilot reduces
source error but **increases complete bytes**. It must not replace the qualified
CS37 path or be presented as a compression improvement.

| Retained 12-frame window | Mode0 control bytes | Spatial bytes | Byte change | Control MSE | Spatial MSE |
| --- | ---: | ---: | ---: | ---: | ---: |
| Primary | 134,817 | 155,885 | +15.6271% | 14.354870 | 13.890415 |
| Complex | 309,308 | 331,421 | +7.1492% | 26.365446 | 25.651026 |

MSE falls 3.2355% / 2.7097%, but the actual mode-map overhead exceeds the residual
benefit. Primary coefficient bytes rise 74,036→75,313 while mode bytes rise
36→19,827. Complex coefficient bytes fall 161,432→160,124 but mode bytes rise
36→23,457. These are complete actual packet budgets, including the same exact
HUD, quant map, both headers, checksums, mode maps and coefficient components.
Every packet fits 49,152 bytes; maxima are 25,437 / 42,260 for spatial.

## Normative prediction and reference behavior

The coded geometry remains 720×480 YUV420 with 720×405 active RGB565 content and
the same four opaque HUD rectangles. Each policy has its own accepted causal
references. Both use ROI scale 8/background 16, exact frozen Q14 forward/inverse
and quantization, and **no residual RDO/pruning**. The only policy difference is
choosing spatial modes; this is not an unchanged-v37-controller comparison.

Each plane has 8×8 residual blocks arranged into independent 2×2-block tiles. The
tile's four positions are decoded in order `(0,0),(0,1),(1,0),(1,1)`. No predictor
reads a block outside its tile or an unreconstructed neighbor. The temporal base
is 128 on a key frame or the policy's own previous canonical reference on a P frame.

Modes 0..3 are:

1. Mode 0: temporal base only.
2. Mode 1: add the decoded top-edge residual vector, measured as reconstructed
   top-neighbor pixels minus temporal-base pixels at those same edge positions.
3. Mode 2: add the analogous decoded left-edge residual vector.
4. Mode 3: add the mean residual of the available top/left edges. Its exact signed
   rounding is `floor((sum + denominator//2) / denominator)`; no available edge
   gives zero correction. Unavailable directional edges are zero.

Every final predictor is clipped to 0..255 before residual formation. Quantized
residual inverse output is added and clipped to 0..255. Support-safe hidden 8×8
blocks have implicit mode0, zero coefficients and immediately committed pixels 128,
before any later tile neighbor may read them. This immediate in-frame rule is
necessary; normalizing only at frame end would give a different predictor.

The host vectorizes the same tile position across independent tiles. It evaluates
all four modes for spatial and only mode0 for control. For each visible block it
chooses the lowest integer score, with lowest mode winning ties:

```
source_YUV_SSE + 8 * (exact_isolated_CP02_packet_bytes - fixed_CP02_overhead)
```

The byte proxy is the frozen exact batched counter, checked against real isolated
CP02 packet construction in tests. It is a proxy for a full plane, not its true
marginal cost. All per-block candidate SSE and packet-byte tensors are retained,
including losing modes. Whole unselected frame bitstreams are not constructed.

## Actual paid syntax

The new outer magic is `SP38`, using the frozen 80-byte outer structure. Its
profile digest explicitly binds the predictor rules, hidden normalization and
opaque geometry. The inner magic is `TS38` with this 80-byte header plus CRC:

```python
struct.Struct('<4sBBHIIHH16s16s7I')
# magic,version,key,epoch,fid,rid,width,height,reference_tag,committed_tag,
# qmap_bytes,modeY_bytes,modeCb_bytes,modeCr_bytes,
# coeffY_bytes,coeffCb_bytes,coeffCr_bytes
```

Payload order is quant map, three mode components, three coefficient components.
Inner and outer output tags both bind the committed canonical reconstruction.
Mode maps cover only visible blocks in plane raster order; hidden modes are
implicit zero. Each actual mode component is the shortest stable choice among:

- Prefix 0: two bits per mode, MSB first, zero low padding.
- Prefix 1: `(mode:u8, positive_run:u16LE)` triples.
- Prefix 2: all modes zero, one byte only.

Dense representation wins ties before RLE, then all-zero. Coefficients use the
frozen full-grid entropy grammar or dispatch4 plus visible-only raster entropy,
whichever complete component is shorter; full-grid wins ties. All actual syntax
bytes are charged. There is no compatibility claim with GM27, CN36 or CS37.

## Synthetic evidence

| One-frame input | Control bytes | Spatial bytes | Control MSE | Spatial MSE |
| --- | ---: | ---: | ---: | ---: |
| Flat | 3,095 | 3,095 | 0 | 0 |
| Directional constant tiles | 4,930 | 4,930 | 0 | 0 |
| Low-amplitude noise | 5,136 | 6,471 | 25.147523 | 25.094989 |

The flat/directional fixtures select mode0 everywhere. Isolated packet-byte
rounding ties can hide savings in DC **bits**, so a useful predictor may not win
this local byte proxy. Noise spends 25.9930% more bytes for 0.2089% lower MSE.
Synthetic original RGB565 canvases, YUV input planes and actual HX32 exact-HUD
fallback packets are retained; the frozen HX33 receive adapter accepts that
fallback. Gameplay uses actual retained HUD packets. HUD creation is never free
in the packet budgets, though fixture generation is outside encoder clocks.

## Qualification and next step

The campaign contains 54 actual packets: two 12-frame scenes × two own-reference
policies, plus three single-frame synthetic inputs × two policies. Four producer
tests cover tile boundaries, directional/DC arithmetic including negative halves,
clipping, hidden immediate commit, source ownership, actual mode packing and exact
CP02 size proxies. Independent replay imports no encoder and recomputes every
candidate's transform, quantization, reconstruction, source SSE, proxy bytes and
winning mode using actual already-decoded neighbors. It also checks packet caps,
canonical syntax, causal references, exact HUD and original RGB565 metrics.
Final replay checks all 54 packets, 22,978 nonzero modes and 1,053,810 candidate
blocks independently. Six independent tests pass, including resealed semantic
corruption and rejection without reference publication; 1,288 source pins match.

Single encoder-clock means are 58.62 / 65.97 ms for control and 162.67 / 170.47 ms for
spatial on this host. Those clocks include all candidate forward/inverse/proxy
work, selected entropy, map packing and sealing. They exclude fixture/HUD reads
or generation, hashes/metrics/archive I/O, independent decode, transport and
display. They are not paired speed measurements or device timing.

The next experiment should address **global signaling cost and proxy mismatch**,
not simply add more modes: use tile/group decisions, sparse exception syntax or
a context-aware rate estimate, then validate actual full-frame bytes at the same
quality constraint on separate causal histories. Keep this negative pilot as a
control. The reused short clips are not held-out gameplay; no HEVC/AV1 comparison,
hardware fit or physical 30 fps is proved by SP38.

```sh
cd experiments/python-game-spatial-v38-study
python -m unittest -v test_model
python -m unittest -v test_verify
python verify.py
```

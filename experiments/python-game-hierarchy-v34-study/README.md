# Actual bounded hierarchical motion components

HM34/v1 preserves both archived 16-pixel child trial fields from the frozen
v33 split study. Across 24 source frames, the strict-band trial's motion
components fall from **13,945 GM27 bytes to 12,318 HM34 bytes**, saving 1,627
bytes (11.67%). The total includes every header, parent map, mask, index, Rice
parameter, delta, padding and CRC byte. Two key frames carry **zero motion
bytes**. Both trial encoders used the same child field, but every trial's
actual component is independently built, archived and checked.

The whole accepted-control guard admits six child trials with the new
component sizes, versus five before. This is **prospective complete-body
replacement arithmetic**, not a serialized new complete frame or a causal
campaign. Each source uses the actual prior accepted v32 reference retained by
the v33 study. Selected trials never update the next reference here.

| Fixed-reference aggregate | Complete/prospective bytes | Source active RGB SSE | Source active RGB MSE |
| --- | ---: | ---: | ---: |
| Actual accepted v32 controller | 508,720 | 426,975,565 | 20.33681818 |
| Old GM27 child trials under whole-control guard | 506,909 | 426,515,821 | 20.31492060 |
| HM34 child trials under whole-control guard | 506,756 | 426,480,714 | 20.31324846 |

The new component improves guarded bytes by **153 bytes** relative to the old
split result. The additional admitted frame is `mass-effect-2600`, ID 3;
the other selected frames are `mass-effect-7200`, IDs 5, 7, 8, 10, 11. Each
admitted trial independently fits 49,152 complete bytes, strictly reduces
bytes versus that frame's actual accepted control, and has source RGB SSE no
higher than control. Strict-band raw complete bytes change from 508,776 to
507,149. Each individual trial retains its original source MSE **exactly**:
HM34 reconstructs the same child vectors, and qmap/residual/pixel syntax stays
untouched. The verifier additionally recomputes all 48 original trial source
metrics and output hashes against actual source images.

`model.pack(parent, child, width, height)` returns actual bytes. Inputs are
int8 `(ceil(height/32),ceil(width/32),2)` parent and
`(ceil(height/16),ceil(width/16),2)` child fields, with components in [-18,18].
`decoder.unpack(data,width,height)` returns the exact int8 child field.
`return_info=True` returns `(value,info)` in either API; unpack info includes
the decoded parent field, or `None` for a flat map. `model.unpack` re-exports
the independent decoder. Keys belong to the containing frame profile and
must omit the component rather than calling this nonkey API.

HM34 has a 14-byte little-endian header `<4sBBHHHH>`: `HM34`, version 1,
mode, source width/height, parent-map length, payload length. A four-byte
CRC32 covers the entire preceding component. Geometry arguments must match
the header; integer dimensions are bounded independently to 1..720 by 1..480,
including partial parent/child edges. A frame profile can further require
even YUV dimensions. The total component bound is `18+1+2*Nchild` bytes,
because a flat child GM27 field always supplies a fallback within that bound.

The host constructs all three candidates and selects the fewest **actual
complete component bytes**. Stable ties prefer modes 0, 1, then 2:

1. **Flat child (mode 0).** No parent bytes; payload is an ordinary bounded
   GM27 vector field. This fallback wins deliberately uncorrelated tests.
2. **Parent plus sparse gaps (mode 1).** Parent is an ordinary GM27 vector
   field. Payload starts with `<HBBB>` refinement count and Rice parameters
   `kg,kx,ky`. Each raster-ordered refinement carries a Rice-coded gap from
   the prior changed child index, then zigzag Rice-coded x/y deltas from its
   repeated parent vector. Gaps use an escape width of
   `max(1,ceil(log2(Nchild)))`; delta escapes use seven bits.
3. **Parent group masks (mode 2).** Parent is ordinary GM27. Payload starts
   with `kx,ky`, followed by parent groups in raster order. Each group has a
   one-bit changed flag, and changed groups have a nonzero four-bit child
   mask. Mask bit order is top-left, top-right, bottom-left, bottom-right.
   Set children carry the same x/y Rice deltas, in mask order. Partial-edge
   children outside the actual child grid cannot be set.

Rice unary is capped at seven one bits. Seven ones require a fixed-width
escape; otherwise a zero terminator and `k` remainder bits follow. Escapes
must be necessary for that `k`. Delta zigzags are bounded to 72 and decoded
vectors to [-18,18]. Refinements cannot redundantly reproduce the parent.
Bits are MSB-first and final padding must be fewer than eight zero bits.
All lengths, parameters, CRC, indices, runs, edge masks, escapes and domains
are checked before a result is returned. Caller state is never mutated.

The decoder imports only `struct`, `zlib` and NumPy. Its bounded GM27 parser
handles modes 0..6 directly, including global, dense, RLE, sparse, packed and
predictive Rice. It accepts structurally valid nonminimal GM27 representations
and does no encoder search or canonical re-packing. Frozen GM27 packing runs
only on the host to construct flat/parent candidates. No frozen <=v33 source
is edited or monkeypatched by the production code.

In the 44 nonkey trial components, six select sparse gaps and 38 select parent
masks. No actual study input selects flat, but tests exercise flat fallback.
For the strict-band trial, the 12,318-byte total divides into 308 header bytes,
88 CRC bytes, 4,126 parent-map bytes and 7,796 refinement-payload bytes.
Nonkey components range from 217 to 803 bytes. All 22 nonkey source fields
save bytes here, after overhead. One measured sample per nonkey trial averages
44.81 ms host packing and 2.14 ms syntax decoding on this environment.
These times cover component work only; source search, transforms, pixel
encode, fixture conversion, HUD work, archive IO, transport and display are
excluded. They are not an end-to-end throughput measurement.

At 720x480 the logical state is 345 parent vectors (690 int8 bytes) and 1,350
child vectors (2,700 bytes): 3,390 retained vector bytes for hierarchical
decode, or 2,700 for flat. Maximum packet storage is 2,719 bytes. A streaming
GM27 median predictor needs two vector rows: 92 parent-grid or 180 child-grid
int8 bytes. Sparse decode has at most 1,350 gap symbols and 2,700 component
deltas; group decode has 345 group flags and at most 1,380 mask bits. Motion
syntax decoding reads **zero source/reference pixel samples**. All raw
strict-band child predictions retain their original 14,734,336 reference
sample gathers. These are logical bounds/counts, not Python heap/RSS, clock
cycles, FPGA fit, or physical hardware resources; the Python decoder
materializes NumPy fields and temporary arrays.

`results.json` retains 1,029 source pins, actual packet archives, candidate
sizes, byte breakdowns, field/output hashes, per-source source metrics,
before/after whole-control guards, timings and logical state. `verify.py`
checks the pins, actual previous-reference histories, 48 retained child frame
decodes/source metrics, 44 HM34 decodes/exact host repacks and guard arithmetic.
Five tests cover all candidate modes, full and partial geometry, random
bounded fields, flat fallback and stable selection, syntax-only nonminimal
GM27 acceptance, CRC and every-byte corruption, truncation/exact lengths,
invalid domains/runs/indices/escapes, redundant refinements, partial masks,
and padding. These results make no causal, complete-frame syntax, combined
gain, hardware fit, or physical 30fps claim.

```sh
PY=/home/lori/gamebub-streaming-prototype/.venv/bin/python
$PY -m unittest discover -s experiments/python-game-hierarchy-v34-study -p test_model.py -v
$PY experiments/python-game-hierarchy-v34-study/benchmark.py
$PY experiments/python-game-hierarchy-v34-study/verify.py
```

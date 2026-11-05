# V32 exact HUD component-Huffman prototype

This lossless component study keeps the full 21,120 RGB565 HUD words per frame.
It reuses the selected predictor/motion field from an actual retained HU25
packet, tries bounded canonical Huffman coding of component residuals, and keeps
the original complete HU25 bytes whenever the new complete frame is not smaller.
It does not install a native Sunshine, ESP32 or FPGA decoder.

## Measured causal result

All 96 source decisions from the two v30 strict windows are processed in order,
with separate exact accepted HUD references per window and resets on the old
key-frame boundaries. The output of the new decoder becomes its next reference.
No future frame or original source is substituted as a decoder reference.

| Window | Old HU25 bytes /48 frames | New bytes | HUD savings |
| --- | ---: | ---: | ---: |
| 2600 | 310,961 | 310,685 | 0.089% |
| 7200 | 623,615 | 562,316 | **9.830%** |

58/96 frames select HX32, including 148 new Huffman-coded patches. All
2,027,520 accepted RGB565 words match exactly. A frame can use a mixture of old
full patches, old HD25 and new HS32 patches. Existing HU25 is a byte-exact fallback;
no frame grows. The largest new/retained complete HUD packet is below 49,152 B.

The primary scene is a useful negative case: the selected HD25 predictor/coder
already leaves little gain for this Huffman menu. The complex scene benefits
from a non-geometric component-residual distribution that the Rice coder does
not represent as compactly. This explanation is an inference from selected
coding modes and byte results, not a controlled per-tool ablation.

The Python prototype adds roughly 68–81 ms/frame of repacking work, including
decoding the supplied baseline, candidate construction, frequency tables,
bit-string construction and packet sealing. Original HU25 generation and its
motion search are **excluded** because the old complete packet is an inherited
fixture. Any integrated sender must pay that original work or share/reuse the
predictor decision explicitly. This is not a complete encoder throughput result.
Decoding averages approximately 4.1 /14.8 ms in this run, with full host arrays.

## Codec and validation contract

The outer `HX32` envelope has the frozen HU25 field layout and 110-byte fixed
cost, but adds patch kind 3 for `HS32`. The new patch retains HD25's geometry,
reference/content-tag and CRC envelope. Residual predictors are intra-left,
previous exact patch, or the already selected bounded global/tile motion field.
Temporal residuals may optionally be differenced from their left neighbor within
each row. Prediction fields retain the old edge-clamping/vector-domain rules.

Each RGB565 component has its own canonical Huffman codebook. A stream carries
u16 symbol count, u32 coded-bit count, ascending `(symbol:u8,length:u8)` entries
and MSB-first code bits with zero byte padding. Code length is at most **16**;
the row-delta component alphabet is bounded to 253 symbols. A single-symbol
stream uses its one declared symbol and zero data bits. More than one symbol
requires a complete, non-oversubscribed canonical code tree. A depth-limit miss
rejects that candidate rather than emitting an unsupported code.

The decoder checks packet/stream lengths, CRC, session/frame reference identity,
exact reference content tag, geometry, table order/uniqueness/depth/Kraft bounds,
bit coverage/padding, component reconstruction ranges, motion prefix grammar and
the final exact reconstructed tag. The new format requires negotiated endpoint
support. It is **not valid CP27 input** and must not be silently dispatched to
the current native parser. A future CP32-style atomic binding is prospective.

API:

```python
packet, work = encode_hud(old_HU25, accepted_reference,
                          expected_reference_id=previous_frame_id)
patches, metadata = decode_hud(packet, accepted_reference,
                              expected_epoch=25,
                              expected_reference_id=previous_frame_id)
```

Five tests pass, including exact outer HX32 dispatch, malformed semantic data
with recomputed valid outer CRC, invalid epochs/reference content, truncated
codebooks/bit streams, invalid code trees, bit padding, motion and row residuals.
The retained verifier replays all 96 accepted packets, exact words/tags/references,
minimum complete patch sizes and no-growth bounds.

```sh
python -m unittest discover -s experiments/python-game-hud-v32-study -v
python experiments/python-game-hud-v32-study/verify.py
```

## Hardware-specific interpretation and memory limits

No image decoding is assigned to the ESP32 in the proposed split: it transports
bounded opaque packets. The FPGA endpoint would decode HS32 into an unpublished
HUD bank and publish only after full integrity/ref checks. This Python model
instead materializes complete bounded packets and patch arrays; it does not
prove a native streaming parser or ESP32 heap behavior.

A byte-aligned canonical decoder table can use 253 symbol bytes plus 16 entries
of `(first_code:u32,count:u16,first_index:u16)`: **381 bytes/channel**, or
**1,143 bytes for three resident tables**. Three signed32 row-delta accumulators add twelve
logical bytes. This excludes control, bit reservoir, tags/CRC, caches, motion
fields and physical memory granularity. The components are serialized, so one
table could be reused with additional external staging/read-modify-write traffic.
These are layout projections, not synthesized BRAM/LUT measurements. The 32-bit
accumulators also cover a malformed bounded-width row before range rejection.

Exact reference HUD storage is 42,240 bytes; separate reference/staging banks
require 84,480 logical bytes. They belong in the FPGA memory architecture, not
an assumed frame-sized ESP32 buffer. Bounded motion/reference reads, three color
passes, tag checks and commit fences all need real memory/cycle qualification.
At most `21,120 × 3 × 16 = 1,013,760` Huffman bit-walk iterations cover an all-new
HUD frame; metadata, constant-symbol outputs and memory accesses are additional.
That bound is not a complete FPGA frame-service or routed-clock proof.
`resources.json` retains observed table/code/bit statistics and the stated bounds.

## Fair HEVC/AV1 comparison

The improved exact HUD must be charged to **all** codecs. On the complex window,
subtracting the 61,299 saved HUD bytes reduces the custom v30 strict complete
body projection from 6.148865 to 5.842370 Mb/s. The same change reduces the
sampled HEVC hybrid from 3.838135 to 3.531640 and AV1 from 3.812410 to 3.505915
Mb/s. Those are prospective re-accountings, not implemented CP32 standards
streams or a custom codec win. All displayed errors remain unchanged because
the HUD words are exact. Reducing a common sidecar can increase the custom's
relative rate gap even as every complete stream becomes smaller.

Next avoid constructing losing Huffman bit strings: count exact table/bit sizes
first, share baseline predictor work, and apply a declared classifier so the
primary negative case does not pay the full menu. Then implement and qualify
the bounded native/RTL decoder, external-memory and atomic publication path.
No physical 30 fps or FPGA/ESP32 fit is claimed here.

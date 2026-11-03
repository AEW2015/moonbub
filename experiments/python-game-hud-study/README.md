# GH01 lossless RGB565 display patches over GM01

This Python experiment tests an application-specific alternative to lossy
priority quantization: opaque lossless RGB565 patches for declared HUD/text
rectangles. Patched pixels are display output only. The GM01 decoder retains
its original reconstructed YUV predictor, so the next residual frame still
uses exactly the same anchor. Existing JPEG, GM01-only/GF01 adapters and target
firmware do not support the new GH01 wrapper.

## Format and atomic validation

A GH01 frame contains an18-byte outer header, GM01 base bytes, up to four
length-prefixed HP01 patches and a4-byte whole-wrapper CRC. Header fields include
version, patch count, base length, canvas width/height and aggregate patch bytes.
All outer lengths, whole CRC, full independent GM01 parse, patch dimensions,
nonoverlap, palette/index bounds and nested CRCs validate before the stateful
GM01 receiver is called. Thus a malformed later patch cannot install a valid
base key as a side effect. The base decoder itself remains atomic on invalid
GM01. There is no wire ACK, network or presentation scheduler here.

HP01 has a24-byte header plus4-byte CRC, with version, mode, x/y/width/height,
palette count, pixel count and payload length. Palette modes1/2/4/8 hold at most
2/4/16/256 sorted distinct RGB565 colors; indices are MSB-first packed with zero
padding. Invalid/unused indices, duplicate or unsorted colors and noncanonical
mode/count choices are rejected. RAW565 uses zero palette entries and exact
little-endian RGB565 words; the encoder selects it when unique colors exceed256.
The decoder permits RAW as a literal fallback and checks its exact bounds.

Patches are opaque disjoint rectangles. There is no alpha mask, RLE, temporal
patch cache, glyph recognition or changed-region detector. `encode_frame`
requires the source capture corresponding to its supplied base packet; matching
geometry alone cannot prove that the caller chose the right capture. The
benchmark uses the same recorded source for both. The wrapper binds patch/base
bytes with CRC but does not provide authentication.

The receiver converts base RGB to RGB565, overwrites patch rectangles and expands
for the common RGB output API. It keeps the underlying GM01 YUV anchor unchanged.
Exactness means equality to **the original RGB565 words** in each rectangle,
not losslessness relative to the original RGB888 channels. Reported RGB888-to-
RGB565 MSE retains the565 quantization floor. Copy/write traffic, palette tables,
validation workspaces and base/overlay buffers are additional host resources;
this does not qualify a physical FPGA blitter or SDRAM bandwidth.

## Main18-source campaign: exact pixels, unfavorable byte cost

The fixed rectangles are `(16,48,192,80)` and `(160,352,400,80)`, totaling47,360
pixels. They are declared priorities, not verified or detected HUDs on the real
footage. Eight predeclared native indices `(0,2,4,6,8,10,12,14)` at4 seconds from
each related Mass Effect clip and two seeded synthetic HUD fixtures are evaluated.
The source rates remain25/29.88 fps, precompressed and sometimes repeated.

Each source is encoded as an independent GM01 key with four profiles: uniform16,
ROI8/background16, uniform16+patches and ROI8/background16+patches. All72 profile
records are actually decoded. There are36 wrapped frames and72 patch encodes;
**every wrapped frame has zero original-RGB565 mismatches in the declared ROI**.
The same-base packet SHA and decoded base hash match between patched/unpatched
profiles. Temporal predictor separation is separately tested with key/P frames.

| Sources | ROI8 GM01 mean | ROI8+GH01 mean | GH01 >48 KiB |
| --- | ---: | ---: | ---: |
| Combat8 |31,504 B|79,188 B|8 /8|
| Second clip8 |19,136 B|95,754 B|8 /8|
| Seeded synthetic2 |95,458 B|143,534 B|2 /2|

The uniform-base patched profile also fails48 KiB on every input. All36 GH01
packets remain in the algorithm study and are counted as cap failures. They
are not admitted streaming frames. The synthetic base keys already exceed the
cap; patch correctness does not repair that failure.

Combat patches use8-bit palette indices throughout. The second clip often needs
RAW565 for its large rectangle, with4/8-bit palettes in the other. Even synthetic
antialiased glyph regions use8-bit palettes in this campaign. Eight bits over
47,360 pixels cost47,360 payload bytes before palette/header/base bytes, already
almost the49,152-byte frame allowance. A palette alone is therefore a poor
full-rectangle gameplay policy for these samples. These independent-key bytes
must not be interpreted as measured temporal-P traffic or a universal patch cap.

Patches improve displayed ROI fidelity, but the correct selection is to keep
GM01 ROI quantization as the general path. A future lossless option should use
smaller configured regions, runs/spans or acknowledged patch reuse, and retain
a cap-respecting fallback. No such RLE/delta mode is implemented in this study.

## Paid work and comparison limits

The result records total base preparation, wrapper base validation, palette/
index construction, assembly, receive validation, base decode, hash verification
and overlay separately. Generic encoder packaging validates the supplied base;
receiver prevalidation parses it before the stateful decoder parses it again.
That duplicate work is deliberately charged and is not an optimized live path.
The exterior receive call also includes the recorded verification hash. Optional
encoder RGB oracle, source acquisition/scale, metrics, transport and display are
outside preparation/receive costs.

Mean patch palette/index construction is0.80/1.05/0.85 ms for combat/second
clip/synthetic groups, and overlay conversion/write is about1.21 ms. Those small
components do not imply a fast complete frame: ROI-base+wrapper preparation
means63.83/53.52/155.88 ms and complete receive75.09/54.92/224.96 ms include the
base validation/decoder work. No timing from a standalone patch should replace
those complete costs in a service model.

Cases run sequentially with fixed profile order, uncontrolled host load and no
CPU isolation. Timing is descriptive Python cost, not a paired performance
ablation or native/FPGA service. Byte/quality comparisons use the same source
IDs; there is no30 fps, physical memory, subjective text-legibility or decoder
fit claim.

## Reproduce and tests

Use the common pinned Python/NumPy/Pillow/PyAV environment. From this directory:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python verify.py
```

Six tests cover all palette widths/RAW, exact565 crops, padding/index/count/CRC
rejection, malformed/overlapping patches before base-state commit, edge geometry,
wrapper bounds and multi-frame YUV-anchor preservation. `results.json` binds
executed sources, versions and native source/frame hashes. `verify.py` reconciles
all72 record sizes, nested metadata, active-area MSE, cap failures and unchanged
base hashes. It reads stored evidence rather than rerunning encoding.

## Separate low-color best-case probes

`flat_probe.py` creates two deliberately favorable720×480 fixtures with the
same rectangles, flat background and a1-bit glyph mask (antialias colors are
excluded explicitly). This is a separate functional probe, not real game HUD
or performance evidence. It preserves the main campaign's negative result.

| Synthetic best case | Base bytes | GH01 bytes | Patch modes | ROI565 errors |
| --- | ---: | ---: | --- | ---: |
|Two-color glyph regions|11,880|17,894|1-bit /1-bit|0|
|Three colors in first region|12,027|19,963|2-bit /1-bit|0|

Both fit48 KiB. This establishes that the format can carry known flat low-color
UI within the cap; it does not establish comparable size for antialiased,
textured or real HUD content. `flat-results.json` records its own code/source
hashes, exact packet hashes, sizes and output checks. Run it separately:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python flat_probe.py
```

A future conditional lossless mode should use actual palette/index cost and
whole-frame capacity, with the existing GM01 base as fallback. No such dynamic
policy, temporal patch cache or RLE/spans are selected or implemented here.

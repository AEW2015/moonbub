# Fixed-point transform prototype

FT01 is a self-contained NumPy intra codec with a frozen Q14 8×8 DCT/IDCT,
explicit integer color conversion, YUV420, quantization and a bounded entropy
parser. It is a new research format, not JPEG, GBD1, an installed Sunshine
mode or an FPGA decoder. No target fit, clock or hardware FPS is established.

`fixed_codec.encode(rgb, quant_scale=16)` accepts uint8 RGB with even dimensions,
at most 720×480 pixels and maximum dimension 2048. `decode(packet)` returns
uint8 RGB. `reconstruct(rgb, quant_scale)` is the packet-independent host
reconstruction golden; decoder output must match it exactly. RGB565 conversion
uses the adjacent codec study's common display-format helper.

## Exact arithmetic and packet rules

The module docstring freezes the wire layout and all rounding rules. The Q14
basis is an explicit integer table. Both transform directions have two 8-term
MAC passes, rounding by `(x+8192)>>14` after each pass. JPEG luma/chroma tables
are scaled by `clip((table*scale+8)//16,1,255)`; 16 is the standard table scale.
Signed coefficient quantization rounds nearest with ties away from zero for
even divisors. Plane edges are replicated to multiples of eight.

Color conversion uses the existing GBD1 integer BT.601 full-range approximation.
Chroma averages each 2×2 footprint with +2 rounding. Its support center is
(0.5,0.5), then this profile's upsampler assigns that sample to the even output
coordinate and bilinearly interpolates right/down. This is an explicit phase
choice, not a claim of standard JPEG chroma siting. It may affect fine colored
edges; the JPEG and FT01 color/upsampling filters are inherently different.
IDCT output and final RGB are clipped. The fixed-pass rounding gives white
RGB255 → RGB254 at scale16; final RGB565 still maps both to white. This is
tested and is part of this profile's lossy arithmetic.

Each of three plane descriptors declares dimensions, block/coefficient counts,
mode and length. Coefficients follow block-raster/zigzag order. Plane-wide
zero-run/Rice coding removes per-block header overhead; runs are bounded to
256 coefficients. Nonzero Rice has a maximum 15-zero prefix and a 12-bit
escape. Quantized coefficients must be within ±2048. An entire plane falls
back to little-endian signed16 coefficients if entropy coding is larger.
Length, dimensions, count, mode, coefficient range, canonical escapes, exact
decoded count, padding and whole-frame CRC are checked before returned pixels
are accepted. CRC is accidental corruption detection, not authentication.

The largest raw 720×480 YUV420 coefficient frame is 1,036,869 bytes, including
headers. That fallback does **not** fit the current 256 KiB receiver limit.
This prototype does not send it to a device; a real sender must enforce
negotiated byte caps and rate/age budgets before sending a whole frame.

Arithmetic/color helpers were adapted from the local GBD1 source pinned in
`SOURCE_REFERENCE_SHA256` and the result artifact; they were copied as needed
and need neither SciPy nor the old native entropy library. The new forward
integer DCT, bounded entropy format and intra-only profile are substantive
differences. Necessary helpers are self-contained in this directory.

## Reproduce and evidence

Use the adjacent Python codec study's pinned environment (NumPy 2.5.4; the
benchmark also needs Pillow/PyAV through `corpus.py`). From this directory:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_fixed_codec.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
```

`benchmark.py` consumes `../python-predictor-study/jpeg-results.json` and its
available source files. It selects the first 12 consecutive frames from each
of the four recorded windows: **48 input frames total**. Source/input/PTS and
selected-frame hashes must match the JPEG baseline. Comparisons use exactly
those 12 JPEG frames per window, not their full 30/60-frame aggregate. The two
start1 windows and adjacent start4 held-out windows come from only two short,
precompressed Mass Effect source files; this is not broad held-out game
coverage or a native 30-distinct-fps capture.

`results.json` binds all executed helpers, test source, JPEG baseline, old
arithmetic reference and numeric basis/quantization/zigzag arrays by SHA-256.
Each encoded transform frame is decoded and compared against the host golden.
The artifact records per-frame byte size, input/output hashes, PSNR before and
after RGB565 output, active-content/full-canvas error, Python wall timings,
plane modes and operation counts. The codec portion has ten passing tests:
scalar/floating/DC/impulse arithmetic checks, signed quantizer ties, clipped
edge/neutral RGB565 goldens, complete reconstruction, Rice/run boundaries,
malformed valid-CRC data, all single-bit corruptions/truncations and bounded
mutation trials. Expected failure conditions are checked by passing tests.

`stripe_model.py` adds a predecoded-sample row-layout oracle and three more
tests, so the complete `tests.log` records13 passing tests. `stripe-results.json`
binds its source/layout/test snapshot. At720×480,16-row stripes with a next
chroma row retain at most18,000 sample bytes, compared with518,400 bytes for
full YUV420 planes; the overlap adds20,880 sample bytes across the full frame.
Random/boundary tests at several geometries and stripe heights match the
full-plane RGB interpolation exactly. This is sample payload only, excluding
coefficient/IDCT workspace, output buffers, FIFOs/control and Python temporary
arrays. The oracle is supplied already decoded rows; it does not solve FT01's
plane-first byte ordering or prove a compressed streaming decoder.

Wire projections replay mean sizes at hypothetical30 fps with 40 application
plus28 IPv4/UDP bytes per1024 payload bytes. They exclude link/RF framing,
retries/ACK, audio/input, capture and queue effects. Source-native cadence and
duplicate content remain in the manifests; this is not an FPS measurement.
Python timings include the reference encoder/parser arithmetic, not Windows
capture or a hypothetical FPGA schedule, and have no CPU-isolation guarantee.

## Results

The primary windows' exact 12-frame comparisons are:

| Window | Profile | Projected wire Mb/s at30fps | Active RGB565-output PSNR |
| --- | --- | ---: | ---: |
| Combat start1 | FT01 scale16 | 9.754 | 33.25 dB |
| Combat start1 | JPEG q50 | 5.969 | 33.30 dB |
| Second clip start1 | FT01 scale16 | 7.599 | 34.74 dB |
| Second clip start1 | JPEG q50 | 3.540 | 34.74 dB |
| Combat start4 held-out | FT01 scale16 | 9.772 | 33.27 dB |
| Combat start4 held-out | JPEG q50 | 5.989 | 33.32 dB |
| Second clip start4 held-out | FT01 scale16 | 7.566 | 34.72 dB |
| Second clip start4 held-out | JPEG q50 | 3.524 | 34.73 dB |

All 144 encoded transform frames (three scales ×48 inputs) fit 48 KiB in this
limited test. Maximum transform frame size is 48,649 bytes, leaving little
storage margin. That storage result does not establish a wire budget: FT01
scale8 combat is about12.43 Mb/s; scale16 combat is about9.75 Mb/s. Scale32
combat fits8 Mb/s at about7.58 Mb/s but has only30.74 dB, below JPEG q35's
31.96 dB at5.19 Mb/s. FT01 did not earn a rate/quality advantage over JPEG.

The transform family is a large improvement over the earlier scalar RGB565
DPCM rates, but JPEG's established entropy/DC/context machinery remains a
stronger baseline. These results do not justify replacing the working JPEG
decoder with this simple coefficient syntax. Any proposed context, DC
prediction or transform change needs its own frozen bounded format and exact
same-input quality/rate comparison.

## DSP and memory implications

For 720×480 YUV420 there are5,400 luma plus2×1,350 chroma8×8blocks =8,100blocks.
A naive separable transform costs2×512 =1,024 MACs/block, hence8,294,400 MACs
per frame **per transform direction**. Receiver IDCT alone is248.832 million
MACs/s at30fps or497.664 million at60fps. Those counts exclude parser,
dequantization, color conversion, buffering, control and memory stalls.

Under the parser's maximum coefficient/table bounds, the two inverse-MAC
accumulators require at most36 and37 signed bits; the intermediate needs22.
The explicit basis values are below8192 in magnitude. These are numeric range
checks useful when considering DSP48 multiplication/accumulation, not evidence
of inferred DSP blocks, a pipelined clock, latency, target placement or fit.

The Python program buffers full planes and coefficient arrays. Its plane-first
stream sends all luma before chroma; an FPGA cannot immediately emit final RGB
pixels without retaining earlier plane data or changing to an MCU/stripe
syntax. That reordering/storage cost is absent from the arithmetic count.
Keep JPEG's existing DSP/memory path as the control, and require a bounded
streaming memory architecture and target implementation before adopting FT01.

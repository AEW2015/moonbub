# V33 bounded exact HUD run codec

This Python prototype serializes actual negotiated `HX33`/`HS33` packets for the
same 96 retained HUD frames used by v32. The decoder's accepted exact RGB565 HUD
becomes its next reference; the retained key boundaries reset that reference.
Every one of the 2,027,520 RGB565 words matches the inherited HU25 decode.
Nothing at or before v32 is edited.

| Window, 48 frames | HU25 bytes | v32 bytes | v33 bytes | Saving from v32 | Saving from HU25 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2600 | 310,961 | 310,685 | **199,566** | **35.766%** | 35.823% |
| 7200 | 623,615 | 562,316 | **462,520** | **17.747%** | 25.832% |

All 96 frames select HX33; 371 patches select HS33. Complete HUD packets never
grow against either inherited format. HUD rates at 30 decisions/s are
0.997830 / 2.312600 Mb/s; maximum packets are 7,171 / 15,252 bytes. Transport and
base-codec costs are additional. These are actual byte counts, not entropy
estimates, fitted hardware results, or complete sender service timing.

## Exact wire contract

`HX33` retains HU25's 106-byte header plus four-byte CRC layout and adds patch
kind **4** for HS33. Kinds 1/2/3 remain original HP01/HD25/HS32 payloads. The
HU25 and HX32 parsers and bytes are unchanged. A complete frame ties or exceeds
its supplied v32 baseline only by returning that exact baseline byte string.
Patch selection also gives the old v32 payload priority on ties. Negotiated
dispatch is required; current CP27/native endpoints do not accept this syntax.

HS33 retains the 46-byte HD25-style header and four-byte CRC: geometry, mode,
payload length, exact reference tag, and exact reconstructed tag. Predictor
recipes are intra-left, exact previous patch, and the bounded global/tiled
motion prefix already selected by HU25. Temporal residuals can additionally be
differenced from the left within each row. Motion prefix grammar and clamped
reads come from the frozen parser, with no new motion search.

Each component is raster flattened after zigzag mapping. It independently
chooses the smallest of three fully serialized alternatives:

| Scheme | Huffman symbols | Rice values |
| --- | --- | --- |
| 0 | Every mapped residual | None |
| 1 | Only nonzero mapped residuals | Zero-gap before each symbol and final zero-gap |
| 2 | One symbol per maximal equal-value run | Each run length minus one |

A 14-byte `<BBIII>` channel header carries scheme, Rice `k`, event count,
Huffman section byte length, and Rice bit count. Scheme 0 requires `k=0`, no
Rice bits, and event count equal to output words. Scheme 1 has exactly
`events+1` gaps, allows zero events, and rejects a zero Huffman symbol. Scheme 2
has exactly `events` lengths and rejects adjacent equal event symbols. Neither
form may expand beyond the geometry-derived count, and exact coverage is
mandatory. Runs may cross a row boundary in the flattened channel; reconstruction
resets the row predictor at each row boundary.

The Huffman section is v32's bounded canonical grammar: u16 symbol count, u32
bit count, ascending `(symbol:u8,length:u8)` pairs, and MSB-first bits. At most
253 entries and 16-bit codes are allowed; multi-symbol trees must be complete
and non-oversubscribed. A constant stream carries zero symbol bits and a declared
one-bit code. The zero-event scheme-1 case has no Huffman section at all. A
depth miss rejects a scheme, or the recipe if every scheme misses.

Rice stores `value>>k` zero bits, one stop bit, and `k` low bits, with
`0<=k<=14`. All 15 exact Rice size calculations are paid by the encoder; only
the minimum-size choice is serialized. Decoding bounds unary quotient and
expanded length against remaining output before expansion. Huffman and Rice
padding must be zero and each declared bit section must be consumed exactly.
Each channel count is at most 21,120 words. The decoder also checks geometry,
epoch/reference identity and content, field grammar, exact packet lengths,
CRCs, component range, final RGB565 tags, and unused envelope fields.

`decoder.py` implements the new Huffman, Rice and run parser independently of
the encoder's construction helpers. Only frozen reference/prediction and old
format parsing are shared through `baseline.py`.

## Paid work and reproduction

Per-frame extra encoder time is **110.65 / 170.10 ms**, and decoder
time **6.02 / 11.81 ms** on this host. The measured extra encoder timer
includes decoding and validating both inherited packets, every predictor recipe,
all channel schemes, Huffman frequency/tree/table/bit construction, all Rice
parameter sizes, run construction, comparisons and actual packet sealing.
The new source choices are causal and use no future frame.

HU25 generation, its motion search, and v32 generation were previously paid in
the retained fixtures and are excluded here; neither baseline is regenerated.
An integrated sender must pay those costs or explicitly share the decisions.
This is a repacking prototype, not a complete source encoder throughput result.
The run pays 14,112 channel-scheme trials and 141,120 Rice parameter size trials.
Module import/setup is separately measured at 143.75 ms in `results.json`. The full process
elapsed/user/system time and maximum RSS in `run.log` additionally include
imports, source reads, oracle comparisons, artifact compression, source hashing,
and final JSON writing: 15.39 seconds elapsed and 16.18 seconds user CPU.
Test and verification work have separate logs. There
were three development full-window runs before the final retained timing run;
their CPU time is additional development work, not included in frame timing.

From the repository root:

```sh
PY=/home/lori/gamebub-streaming-prototype/.venv/bin/python
$PY -m unittest discover -s experiments/python-game-hud-runs-v33-study -v
$PY experiments/python-game-hud-runs-v33-study/benchmark.py
$PY experiments/python-game-hud-runs-v33-study/verify.py
$PY experiments/python-game-hud-runs-v33-study/resources.py
```

Four test groups cover all channel schemes and Rice parameters, maximum-length
constant channels, truncation, bad code trees, table/section bounds, zero/nonzero
rules, repeat order, expansion coverage, unary bounds, padding, predictors,
global/tiled motion, CRCs, exact references and negotiated outer dispatch with
valid-CRC semantic corruption. Retained verification replays all packets with
the independent decoder, checks source pins and artifact hashes, exact words,
reference tags, complete bytes and minimum-size choices. `objects/` contains
zlib-packed actual accepted wire bytes; storage compression is not counted as a
wire saving. `results.json` pins executable dependencies and inherited packets.

## Logical state and external payload

`resources.py` derives a declared serial HS33 decoder layout of **1,345 logical
bytes**, including a 381-byte canonical table, 432 bytes for the maximum 216
motion vectors, header buffers, bounded run/component/control state, tags/CRCs,
and a 144-byte serial SHA256 workspace. The maximum vector count is exhaustively
derived over the patch domain; a 49x431 patch reaches 216 because of tile fringes.
The SHA workspace budgets eight chaining, eight working and sixteen rolling
u32 words, plus length/cursor state. Headers use 172 bytes; run work uses eight
u32 values; component work uses four signed32 values. Malformed bounded-width
row accumulation also fits signed32 before output-range rejection.

Supporting the original palette fallback replaces 381 bytes of table scratch
with a 512-byte palette and 32-byte used-entry bitmap: **1,508 logical bytes**
for the declared shared layout. One table is reused across serialized color
passes. Construction can reread the seekable packet instead of storing a
second table, and output component updates read/modify/write external staging.
Motion vectors are reused across the three passes. CRC and RGB565 tag passes
also reread external staging. These are algorithmic layout projections, not
measured Python allocation or synthesized BRAM/LUT/clock results; DMA, FIFOs,
caches, bus interfaces and publication hardware add implementation storage.

The measured 21,120-word HUD needs **42,240 bytes** of exact reference and the
same staging payload: **84,480 external logical bytes** for two banks. Keeping
one full 49,152-byte seekable packet alongside them makes **133,632 bytes**.
This packet storage enables separate symbol/Rice cursors and repeated predictor
passes; a transport-only ESP32 is not assigned either HUD bank or image decode.
The unchanged generic full-patch grammar can express disjoint HUDs as large as
720x480 words. Supporting that whole parser domain instead requires **1,382,400
bytes** for two banks, or **1,431,552** with one packet. A smaller bank allocation
therefore requires the fixed measured HUD geometry or an explicit negotiated
application bound. No native memory integration, ESP32 heap, cycle service,
atomic publication or physical 30 fps is proven.

## Common HUD comparison

This exact HUD improvement must be applied identically to custom, HEVC and AV1.
Against v32 the common 30 Hz sidecar decreases by 0.555595 / 0.498980 Mb/s in
the two windows. Against HU25 the decreases are 0.556975 / 0.805475 Mb/s.
For example, on the complex window the previous complete-body projections
become 5.343390 Mb/s custom, 3.032660 HEVC, and 3.006935 AV1 when each gets this
same HUD. These are prospective common-sidecar re-accountings, not implemented
standards streams or a closed base-codec gap. All displayed errors are unchanged
because every HUD word remains exact.

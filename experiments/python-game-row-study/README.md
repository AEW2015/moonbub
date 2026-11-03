# HR01 row-run RGB565 UI candidate and HG01 wrapper

This software experiment adds a stateless row-reset patch candidate to the frozen
HP01 palette format. The PC tries actual candidates and emits the shortest bytes;
the receiver reconstructs exact original RGB565 words in declared UI rectangles.
It is a separate **HG01** wrapper around GM01. GH01, the finite GF02/GM01 adapter,
installed firmware and FPGA RTL do not support HG01/HR01.

## Coding and decoder contract

HR01 uses the same24-byte geometry/count/payload header shape as HP01, but magic
`HR01`, version1 and different mode semantics. A four-byte CRC covers the entire
patch body. Mode0 is literal little-endian RGB565. Mode1 is per-row word runs and
literals. Mode2 is sorted unique RGB565 palette plus per-row byte-index runs and
literals. Palette size is at most256 words. Each coded row starts with its exact
16-bit byte length. A token has one byte: high bit0 means1–128 literal symbols;
high bit1 means1–128 repeats followed by one symbol. Symbols are two-byte words
in mode1 or one-byte palette indices in mode2. Tokens cannot cross a row.

The encoder greedily emits runs of length at least3 and bounded literal groups.
It tries RAW, direct runs and, when possible, palette runs, then chooses minimum
complete HR01 size. `choose_patch` also encodes frozen HP01 and chooses the shorter
complete format (HP01 on ties). All attempted work is timed, including candidates
that lose. This is a bounded current-content choice, not optimal RLE or a future-
frame/perceptual search. Different palettes/run modes do not change source pixels.

The decoder checks exact lengths, CRC, output pixel and row bounds, sorted unique
palettes, used/in-range indices and full consumption. HG01 has an18-byte header,
GM01 base, up to4 length-prefixed HP01/HR01 patches and whole-frame CRC. It checks
all geometry and nonoverlap **before allocating decoded patch words**. All patch
validation finishes before the atomic stateful GM01 receiver validates/decodes
its base. This avoids a redundant full base entropy parse while retaining the
no-invalid-patch-state-change rule. The preflight alone does not certify GM01
coefficient bytes; the stateful GM01 decoder does that before committing.

Display patches never change reconstructed YUV prediction anchors. There is no
patch reference/cache/ACK state, alpha blending or automatic HUD recognition.
A target streaming decoder would use bounded row counters and an optional palette;
Python currently allocates full patch/output/reference arrays. There is no target
BRAM/DSP/SDRAM fit, bandwidth, timing or concurrent service proof.

## Actual same-source comparisons

The20 inputs comprise16 real precompressed Mass Effect frames (eight fixed native
indices at4seconds from each related clip), two seeded antialiased UI fixtures,
and two deliberately flat low-color fixtures. Each source prepares one independent
GM01 ROI8/background16 key and reuses those exact base bytes across four actual
encode/decode profiles: broad/compact regions × HP01/adaptive-row patches.
All80 wrapped decodes preserve original RGB565 words in their full selected area.

Broad regions total47,360 pixels. Compact regions total21,120 pixels, or44.59% of
the broad priority area. The rectangles are configured priorities, not verified
real-game HUDs. Byte comparisons within a region set preserve identical area;
comparing compact against broad changes the exactness coverage.

|16 real inputs|HP01 mean complete bytes|Adaptive mean complete bytes|HP01 / adaptive fitting48KiB|
|---|---:|---:|---:|
|Broad|87,470.7|45,557.5|0 /8|
|Compact|40,047.7|31,216.4|16 /16|

That is47.9% lower complete bytes for broad and22.1% for compact. The exact pixel
claim applies to every decoded test, including cap failures; cap-failing packets
are algorithm results and **not admitted streaming frames**. All32 real paired
region-set comparisons improve in bytes. Adaptive chooses HR01 for all96 real
patches. It is not a bitrate comparison against HEVC/AV1 or a temporal stream.

Antialiased synthetic broad packets shrink143,533.5→102,934.5 mean bytes, but still
fail because their GM01 bases already exceed the cap. Favorable flat broad packets
shrink18,928.5→16,935.5; compact14,758.5→14,425.5. Keep those synthetic cases separate
from real footage. RGB565 exactness retains RGB888 quantization error.

## Paid Python work and limits

The actual key preparation is measured once per source and reused across profiles.
Each charged preparation sum adds that measured base cost to its actual patch
search/assembly; it is not four independent complete-frame timing runs. All
HP01/HR01 candidates are paid. Source load/scale, priority-map construction, metrics/oracles, transport and
display are outside these service measurements. The receive timer includes full
wrapper/patch validation, one atomic GM01 decode, RGB565 overlay and output conversion.

|Real16|HP01 patch work / charged prep|Adaptive patch work / charged prep|HP01 / adaptive receive|
|---|---:|---:|---:|
|Broad|0.96 /27.27ms|11.15 /37.47ms|35.15 /37.42ms|
|Compact|0.58 /26.90ms|6.34 /32.66ms|34.95 /35.77ms|

The byte savings cost Python host work. Even compact mean preparation near33ms
is not a deadline/tail bound; receive is slower still. No30fps result follows.
Profile order is fixed, host load is uncontrolled, and the clips are native
25/29.88fps with related/repeated precompressed content. This does not prove
native30-distinct-frame gameplay, subjective UI legibility or target performance.
Forward-byte fields use the59bytes/chunk GF02 accounting convention **only as a
size calculation**; the installed GF02/GM01 decoder cannot parse HG01.

## Reproduce

Use Python3.14.4, NumPy2.5.4, Pillow13.0.0 and PyAV19.0.2, then from this directory:

```sh
python -m unittest -v
python benchmark.py
python verify.py
```

Eight tests cover all modes, odd/edge crops, row boundaries, malformed counts/
indices/CRC/lengths, bounded minimum selection, invalid base/patch atomicity,
preallocation overlap rejection and key/P YUV-anchor separation. Results pin all
executed sources, media/source IDs, packet/output hashes and runtime versions.
The verifier checks stored sizes/coverage/caps/choices and exactness; it does not
rerun timed encoding. Next combine HR01 with selective admission under an explicit
new peer profile, then qualify a native row decoder and physical memory service.

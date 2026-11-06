# CS87 quantizer metadata and accepted-state reuse

This prototype preserves the existing 720×480 quantized image, residual AB38
streams, grouped operation maps and C2 content/HUD commitments. It changes the
application framing to the explicit `CS87` magic. A CS86 receiver cannot read
it. The new native C++ receiver directly parses and reconstructs the new
packets; this is not a Python expansion back into CS86 before decoding.

## Actual complete-packet result

The two whole-plane configurations use the same 457 content sources and the
same four reset histories as V86. All 914 packets reproduce the independently
qualified coefficients, canonical pixels, HUD, rendered RGB565, content root
and frame seal. Link overhead is excluded equally from these application-byte
counts. Resolution and quantized image quality are unchanged.

| Configuration | CS86 corpus bytes | CS87 corpus bytes | Saved versus CS86 | CS87 median / maximum |
|---|---:|---:|---:|---:|
| Fixed grouped COPY | 7,930,953 | 7,784,499 | 146,454 | 16,532 / 44,546 B |
| Matched all-visible | 8,008,725 | 7,862,271 | 146,454 | 16,662 / 44,546 B |

Original CU66 totals 7,946,811 bytes on these sources. Fixed grouped COPY is
therefore 162,312 bytes, **2.04%**, smaller overall. The matched all-visible
control is 84,540 bytes smaller. These corpus comparisons do not establish a
general rate/quality advantage over HEVC or AV1 or unseen gameplay.

The old quantizer map costs 338 bytes per frame, or 154,466 bytes across the
corpus. New blocks total 8,012 bytes: median/minimum 16 and maximum 51 bytes.
For each configuration, 20 keys select full-map RLE and all 437 deltas select
accepted-map inheritance. This corpus has stable required quantizers between
keys; changing quantizers on other content can reduce this saving. The full
raw fallback costs 354 bytes including its block framing, 16 bytes more than
the old raw map. All 457 complete packets in both tested configurations fit
49,152 bytes; that is not a universal bound.

## Wire grammar

The 128-byte CS87 frame envelope retains the CS86 field layout. The four-byte
magic is `CS87`, version is 1, and the quantizer-length field at byte 40 now
accepts 16 through 354 bytes. It counts the entire QM87 block. All component
lengths and the outer CRC are recomputed; the other component bytes are
unchanged. The existing C2 pixel/HUD commitment domain is deliberately retained.

QM87 consists of a 12-byte big-endian header, a method body and a four-byte
CRC32 over that header and body:

| Offset | Size | Field |
|---|---:|---|
| 0 | 4 | `QM87` magic |
| 4 | 1 | Version 1 |
| 5 | 1 | Method 0 through 6 |
| 6 | 2 | Fixed 1,350-cell count |
| 8 | 2 | Body length |
| 10 | 2 | Required-cell count derived independently from operations |
| 12 | variable | Body |
| 12 + body length | 4 | CRC32 |

Methods 0/1/2 encode all cells using packed two-bit values, one uniform byte or
RLE. Methods 4/3/5 respectively use the same representations for only required
cells, in ascending cell order. Missing cells receive the defined value zero.
Method 6 has no body and inherits all 1,350 values from the previously accepted
frame. The sender chooses the shortest body, with ties going to the lower
method number. No per-frame method bits are hidden outside the byte accounting.

Two-bit quantizers are MSB first; code 3 and nonzero tail padding are invalid.
Each RLE byte holds a quantizer in its upper two bits and a run length minus
one in its lower six bits. Lengths range from 1 through 64. Readers check exact
coverage, reserved codes, required-cell count, length, profile and both CRCs.

## Needed cells and transactional cache

There are 45×30 cells. Cell `(row, col)` supplies four luma 8×8 tiles and the
corresponding single Cb and Cr tiles. A cell is required if **any** of those six
operations is RESIDUAL. Every required value must equal the source quantizer.
COPY and CONST do not dequantize coefficients, so their unused cell values
may be omitted without changing pixels. The independent geometry test checks
all 8,100 individual tile-to-cell mappings.

The sender must track the **decoded** accepted map. Required-only methods can
replace previously unused values with zero; assuming the original full map
remained cached would make later inheritance incorrect. Keys decode without a
previous cache and cannot inherit. A delta's inherited map belongs to the
same accepted reference and generation already checked by the envelope.

The receiver stores quantizer state with its provisional pixel result and
publishes it only after the reconstructed content root and seal succeed.
Rejected packets leave the accepted pixels and cache intact. Exact replay
returns the accepted result. CRC is an error check, not authentication.

## Verification and implementation limits

[37 retained checks](../../experiments/python-gamebub-v87/quantizers/tests.json)
cover all seven methods in independent Python/C++ parsers, malformed inputs,
all individual tile-to-cell mappings and actual frame rejection, retention,
recovery and replay. Forced raw/full-RLE/needed-packed/needed-RLE frame spellings
also produce identical pixels and then decode the next frame from their actual
accepted cache branch. A syntactically valid wrong quantizer map fails at the
reconstructed content root.

The [independent campaign audit](../../experiments/python-gamebub-v87/quantizer-audit.json)
checks all 914 source pairs, complete-byte accounting, decoded commitments,
source pins and 12 retained packet fixtures. See the
[actual native campaign](../../experiments/python-gamebub-v87/quantizers/results.json).

The cache needs 338 logical bytes if packed, plus ownership/control and any
provisional copy needed for atomic publication. The host C++ implementation
uses unpacked arrays and whole-frame buffers; it is not a target RAM estimate.
No FPGA or ESP32 parser implementation or hardware timing is provided here.
The coupled latency campaign separately retains **fixed CS86** as its control;
its times cannot be relabeled as measured CS87 decoding times.

```sh
python3 scripts/cu66-v87/prototype_quantizers.py
python3 scripts/cu66-v87/test_quantizers.py
python3 scripts/cu66-v87/audit_quantizers.py
```

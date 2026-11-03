# DC/AC coefficient coding follow-up

FT02 changes the coefficient syntax while preserving the previous
[FT01 transform](../python-transform-study/README.md) arithmetic, color,
quantization and reconstructed pixels exactly. It tests the next custom-codec
step in the [prototype plan](../../docs/custom-codec-prototype-progress-2026-11-03.md).
This is Python format/correctness research, not a Sunshine mode, integrated
receiver, hardware decoder or physical throughput claim.

## API and exact packet rules

`coeff_codec.encode_coefficients(coefficients, blocks_w)` accepts an `N×8×8`
`int16` array in block raster order with coefficients within ±2048. `N` is
1..65536; `blocks_w` is1..256 and must divide `N`. Its independent
`decode_coefficients(packet, N, blocks_w)` validates the exact expected geometry
and returns the same coefficients. A complete CP02 payload is bounded by
`128*N + 26` bytes, including headers/CRC. This helper is also usable for a
one- or two-block-row stripe region; it does not itself implement a stripe
transport or incremental byte parser.

CP02's little-endian `<4sBBIHHII>` header is22 bytes: magic, version1, mode,
block count, block-row width, reserved0, DC length and AC length. CRC32 of header
plus payload adds four bytes. Mode0 stores raw little-endian signed16 block
raster coefficients. Mode1 has separate padded DC and AC streams:

* DC is predicted from the previous block, reset to zero at each declared
  block-row boundary. Signed deltas map `x≥0→2*x`, `x<0→-2*x-1`; one Rice
  parameter0..13 is declared. The largest +4096 delta maps8192 and needs a
  **14-bit escape**, avoiding a clipped positive endpoint.
* AC follows the frozen zigzag positions1..63. Three Rice parameters0..11
  apply to positions1..5,6..20,21..63. `00` ends the block with zeros; `01`
  represents16 zeros; `1 + four-bit zero count + Rice(mapped_nonzero-1)`
  represents a nonzero coefficient. AC escapes are12 bits because the largest
  mapped value after subtracting one is4095.
* Both Rice forms cap unary prefixes at15 zeros. Short forms use a terminating
  one and k remainder bits; escapes have no terminator and are rejected if
  the short form should have been used. Each stream's final pad bits are zero.
* Counts/runs may not overrun the declared block or AC region. Reconstructed
  DC/AC, raw coefficient ranges, exact lengths, modes, geometry, parameters,
  padding, trailing bytes and CRC are checked. Incomplete/malformed input never
  returns an accepted coefficient array. A whole payload falls back to RAW
  whenever the compressed streams are not smaller.

FT02's `<4sBBHHI>` frame header declares magic/version/quantizer/dimensions/length.
Each plane descriptor `<HHII>` gives plane dimensions, block count and CP02
length. Three CP02 payloads and a whole-frame CRC follow. The frame decoder
applies a dimension-derived upper bound before CRC/parser work. It imports
FT01's frozen reconstruction; no transform basis, tables, rounding, subsampling,
chroma phase or output color rule changes.

The maximum raw720×480 coefficient frame is1,036,932 bytes. That exceeds both
48 KiB and the existing256 KiB receiver cap. A production sender must enforce
negotiated cap/rate/age limits; this fallback is a correctness/expansion bound,
not a generally transportable video fallback. CP02 CRCs are accidental-error
detection, not authentication or a memory-drain acknowledgement.

## Reproduce

Use the [previous pinned Python environment](../python-codec-study/requirements.txt).
NumPy is sufficient for the codec/tests; the corpus benchmark also uses
Pillow/PyAV and the existing source clips. From this directory:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_coeff_codec.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
```

`tests.log` records seven passing tests: coefficient/DC-delta endpoints,
row resets, sparse/noisy RAW fallback, scalar Rice escape boundaries,
frozen RGB reconstruction at edge geometries, malformed valid-CRC input,
every truncation/single-byte mutation of a small packet and100 seeded frame
mutations. Expected rejection conditions are checked by passing tests.

The benchmark consumes the prior FT01 `results.json`: twelve consecutive
frames from each of four windows (48 inputs), three quantizer scales8/16/32.
The recaptured source file/frame hashes must match. All144 FT02 decoded
images match the frozen host golden and previous FT01 RGB565 output hashes.
The file binds executed source, frozen arithmetic, numeric arrays and baseline
artifact hashes. Original source PTS/cadence/duplicates remain recorded.
These are short, precompressed Mass Effect clips, not native30 fps gameplay.

## Measured result

All new sizes include frame/plane/coefficient headers and all CRCs. The wire
projection uses40 application plus28 IPv4/UDP bytes per1024-byte payload at
hypothetical30 fps; link/RF framing, feedback/retry, audio/input and actual
queue/capture service are excluded. Quality is pooled active-content PSNR
after the common RGB565 output conversion. It is not a visual/HUD acceptance
threshold. Encoder/decoder wall timings are Python reference costs, not FPGA
clock or service estimates.

| Exact12-frame window | FT01 scale16 Mb/s | FT02 scale16 Mb/s | FT02 savings | JPEG q50 Mb/s |
| --- | ---: | ---: | ---: | ---: |
| Combat primary | 9.754 | 7.542 | 22.7% | 5.969 |
| Second clip primary | 7.599 | 4.307 | 43.3% | 3.540 |
| Combat held-out | 9.772 | 7.555 | 22.7% | 5.989 |
| Second clip held-out | 7.566 | 4.275 | 43.5% | 3.524 |

The frozen scale16 active PSNRs are33.25/34.74/33.27/34.72 dB. JPEG q50's
corresponding values are33.30/34.74/33.32/34.73 dB. Thus the coefficient
change saves substantial bytes without changing pixels, but JPEG remains
smaller at closely comparable PSNR. FT02 does not earn a JPEG replacement.

Across all scales/windows, savings versus identical-output FT01 range from
19.0% to52.4%. All144 sample packets fit48 KiB; maximum39,427 bytes, down
from FT01's48,649. That maximum occurred at scale8, whose combat rate is
still10.063 Mb/s. A frame-size cap does not establish an8 Mb/s stream budget.
Scale32 combat is5.531 Mb/s at30.74 dB, still worse than JPEG q35's rate/quality
pair on that exact subset. Full per-frame tails and unfavorable cases remain
in `results.json`.

Arithmetic/DSP work is unchanged from FT01. Row-reset DC prediction and band
contexts add bounded state and parsing, not demonstrated DSP savings. The
helper resets DC at declared block-row boundaries, so changing region width
changes coded bytes while preserving coefficients. Any stripe transport must
charge those resets and descriptors. Plane-first FT02 still needs retention/
reordering before full RGB display; a byte-driven bounded stripe pipeline is
a separate integration step. No BRAM packing, physical memory service,
decoder schedule, target synthesis or hardware FPS is established here.

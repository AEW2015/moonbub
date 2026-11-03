# Synthetic JPEG decoder discrepancy analysis

This is an exploratory analysis of **one synthetic 720×480 4:2:0 JPEG** and its
full JPEG-core/SDRAM/LCD RTL dump, not a gameplay-quality verdict, an approved
error tolerance or a 30 fps proof. The 16-bit dump was previously checked
exactly against a fixed-color C model that shares upstream algorithms with the
RTL. It is compared here to Pillow 13.0.0/libjpeg (reported ABI version 6.2).
Input SHA-256 hashes, numeric results and selected coordinates are in
`results.json`.

Default Pillow produced exactly matching RGB565 words for 224,931 of 345,600
pixels; maximum absolute code-value differences were R5=11, G6=15 and B5=14.
The largest was at (x=360, y=239): RTL RGB565 component codes [28,2,30],
default Pillow [19,17,16]. These are *quantized component codes*: green spans
0–63 while red and blue span 0–31, so 15 must not be read as an 8-bit value.

As a diagnostic, Pillow's internal full-size `decoderconfig=(1,1)` was used
before decoding. Pillow's [13.0.0 decoder source](https://github.com/python-pillow/Pillow/blob/13.0.0/src/libImaging/JpegDecode.c)
shows that draft mode disables fancy chroma upsampling **and** selects the
fastest IDCT; therefore it does not isolate upsampling as the only change.
Under this setting, the worst pixel matches exactly, exact pixels increase to
283,965 and the maximum differences drop to [2,2,2]. The setting is a
version-specific internal interface, not a portable test contract. RGB/color
conversion, rounding and quantization can still contribute to residuals.

An image-space chroma-edge *proxy* was computed by converting the default
Pillow RGB image to 8-bit YCbCr. At each pixel, take the maximum absolute Cb
or Cr component difference versus each existing immediate horizontal or
vertical neighbor. This is **not** original JPEG component data or an
independent per-cause measurement. With proxy threshold ≥20, 22,255 pixels
of the frame were on such edges. Of the 6,227 pixels whose maximum absolute
RGB565 component-code error was ≥5, 6,226 were on those edges; all 415 pixels
at error ≥10 were on such edges. This spatial clustering and the combined
fast-decode experiment are consistent with upsampling contributing strongly;
they do not independently prove its share of error or identify all other
causes. The fixture is a deterministic bars/detail pattern with deliberately
sharp edges, so these numbers should not be generalized to games.

To reproduce, first run `fpga/experiments/throughput30/burst/run-jpeg720-verilator.sh`
with `BUILD_DIR` set to a writable directory. It builds the RTL test, writes
`jpeg720-rgb565.txt`, and checks it against both Pillow and the C model. Then,
with Python, NumPy and Pillow 13.0.0 installed:

```sh
python3 experiments/jpeg-discrepancy/analyze.py \
  host/fixtures/pattern-720x480-420-q65.jpg \
  "$BUILD_DIR/jpeg720-rgb565.txt" --output /tmp/jpeg-discrepancy.json
```

The script validates a complete unique coordinate set and records input
hashes, Pillow version, pixel statistics and the threshold definition above.
If Pillow or its linked JPEG library changes, record that version and expect
potentially different values; never treat exact counts as an acceptance gate.
To isolate the contribution of interpolation from IDCT, use a reference JPEG
decoder that permits toggling `do_fancy_upsampling` without changing IDCT,
then repeat with gameplay and color-edge test fixtures.

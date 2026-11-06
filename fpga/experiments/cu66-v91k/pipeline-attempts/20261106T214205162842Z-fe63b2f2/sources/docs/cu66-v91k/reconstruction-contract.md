# CU66 V91k reconstruction contract

V91k defines the zero-motion CS88 base-image reconstruction used by the V91k RTL memory and RGB path. The accepted pixel history comes from the retained, digest-verified V82 native corpus loader (`experiments/python-gamebub-v82/native/data.py`), then is cross-checked against accepted V88/V90 receiver histories. The four real packet cases remain the V91i2 all-BR88 packets: `actual_001` (c0f0), `actual_006` (c0f1), `actual_043` (c0f3), and `actual_031` (c3f50).

## Modes and pixels

V91i2 mode vectors use `0=COPY`, `1=CONST/hidden`, and `2=RESIDUAL`. The frozen v69 decoder supports delta motion only when all three motion components are zero. Its hidden mask forces every hidden tile to 128 and requires hidden coefficients to be zero. A key tile predicts 128. A visible delta tile predicts from the same pixel position of the accepted reference plane. Residual plus prediction is clamped to unsigned 8-bit range. Transform values use the V91j integer dequantization and two rounded IDCT passes, including floor division of negative sums.

The four real outputs are independently reconstructed from V91i2 mode, qscale and signed coefficient vectors, then compared byte for byte with the retained V82 raster pixels. The current frame's SHA-256 must also equal both its V82 metadata and an accepted V88 or V90 receiver history record. Reference snapshots are taken from accepted V82 frames and their canonical SHA-256 is checked against accepted receiver history:

| Case | Current frame | Accepted reference | Reference SHA-256 |
| --- | --- | --- | --- |
| `actual_001` | c0f0 | key; none | — |
| `actual_006` | c0f1 | c0f0 | `927e4b27b815228919275cdbd3cbdfcc8b7cbd0eae60749a3919e1754e5d6257` |
| `actual_043` | c0f3 | c0f2 | `ffc569d2e53cc21c80e9c1f450f64b3a5ca902f70d6b01970b2980b94a5ce3fd` |
| `actual_031` | c3f50 | c3f49 | `a1468ce6b33d7bb7266ee0cebcdedfbc024201b03ad4778fee34ded76ce67110` |

`actual_006_varied_qcache` is a synthetic transform variant: it reuses actual_006 signed coefficients and its accepted c0f0 pixel reference, but applies the explicit 1350-cell synthetic qscale cache in V91i2. Its output is computed independently and is not represented as a native accepted frame. `structural_all_copy_zero_residual` is a synthetic all-visible-COPY packet using the same accepted c0f0 reference; hidden tiles remain CONST128. This case has no decoded residual blocks.

## Vector files

`experiments/python-gamebub-v91k/vectors/canonical_goldens.tsv.gz` contains six rows with columns `id`, `ref_planar_raster_hex_or_dash`, and `expected_planar_raster_hex`. Each non-dash field is 518400 bytes encoded as hex: Y (720x480), then Cb (360x240), then Cr (360x240), each in row-major raster order. The key row has `-` for its reference. Its compressed and decompressed row hashes and exact row count are pinned in `model-results.json`.

`experiments/python-gamebub-v91k/vectors/rgb_goldens.tsv.gz` contains six rows with columns `id` and `rgb565le_hex`. Each payload is 691200 bytes encoded as hex: one 720x480 packed RGB565 word per pixel, little-endian. The V69 bilinear chroma upsample, signed floor rounding, clamp and RGB565 packing are used. HUD overlay is excluded.

The model does not call a native decoder or use RTL/DUT output to make expected pixels. `model-results.json` pins the V91i2 vectors and manifest, V91j model, V82 loader and corpus index, v69 generated constants, and receiver histories; it records per-case source packet, reference, canonical raster and RGB hashes. V82's compressed and raw chunk digests are verified by its loader before any tiles are used.

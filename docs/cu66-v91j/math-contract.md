# CU66 V91j dequantization and IDCT contract

## Scope and sources

V91j starts at the coefficient blocks and qscale placements already qualified
by the immutable V91i2 vectors. Its Python model reads
`experiments/python-gamebub-v91i2/vectors/cases.tsv` and
`experiments/cu66-native-v69/generated_constants.hpp` as data. It independently
parses the frozen `DCT` and `QTABLES` initializers; it does not import native
arithmetic or call the C++ implementation.

The vector manifest pins the V91i2 case TSV and manifest, V91e coefficient
source, generated constants, and this model source. The V91i2 input vectors
remain unchanged.

## Arithmetic

For a coefficient block `c[y][x]` and qscale `s`, dequantization is

```text
dq[y][x] = c[y][x] * QTABLES[plane_class][s][y][x]
```

`plane_class` is zero for Y (plane 0) and one for either chroma plane (planes 1
and 2). Valid component coefficients are signed values from -2048 through
2048. Valid qscale codes are 0, 1, and 2. Every dequantized value must fit
signed 20-bit range.

The first IDCT pass computes the full signed intermediate matrix:

```text
mid[y][x] = floor((sum(k=0..7, dq[y][k] * DCT[k][x]) + 8192) / 16384)
```

The second pass computes unclipped residual samples:

```text
residual[y][x] = floor((sum(k=0..7, DCT[k][y] * mid[k][x]) + 8192) / 16384)
```

Each pass rounds independently. Division is mathematical floor, including for
negative numerators; this matches Python `//`. The completed residuals must fit
signed 24-bit range. Do not clamp, add prediction, or convert to pixels in this
stage.

## Vector files

`vectors/transform_tiles.tsv.gz` carries one row per transform block, with
columns `id, plane, block, tile, qcell, qscale, coeff_hex, dq_hex,
residual_hex`. Coefficients are 64 signed int16 little-endian values (128
bytes). DQ and residual values are each stored in 64 signed int32 little-endian
containers (256 bytes); the values are range-checked against their signed20
and signed24 contracts. Blocks are ordered by V91i2 residual ordinal and
retain their native tile and qcell mapping.

The file contains 31,706 blocks: 21,177 blocks across the four native frames,
4,054 varied-qscale blocks, and 6,475 blocks in the late third-plane CRC case.
The late-CRC fixture has only the completed first two planes in its transform
goldens. RTL cancels work after the CRC error; those rows define the previously
completed prefix for comparison.

`vectors/boundary.tsv` contains compact standalone blocks for zero, positive
and negative DC limits, positive and negative AC limits, signed extremes, and
rounding patterns. It exercises all qscales and both table classes (Y and
chroma). Invalid qcode 3 and coefficient values +2049/-2049 are marked with
expected component error 3 and have no DQ or residual result.

All hashes and row counts are recorded in `vectors/manifest.json` and
`model-results.json`. Regenerate both files with:

```sh
python3 experiments/python-gamebub-v91j/model.py
```

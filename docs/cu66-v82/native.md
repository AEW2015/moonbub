# V82 native oracle and encoded operation classification

The collection contains the same 457 frozen CU66 frames as V69's accepted fixture
index: cohorts 119/119/119/100, with 20 keys and 437 deltas. The collector reads
V69 and all earlier sources and evidence without changing them. Parent source
commit: `83efb7ae627757aefdfd22e2a355720ff01bfb72`.

A separate instance of the frozen `experiments/cu66-native-v69/decoder.hpp`
validates every packet SHA256, full canonical-plane SHA256, decoded HUD SHA256,
and displayed RGB565 SHA256 against the frozen index. The V82 instrumented header
is a renamed fork of that decoder; it records whether all 64 decoded quantized
AB38 coefficients are zero before inverse quantization or IDCT. Its complete
reconstructed planes are compared byte for byte with the separate frozen decoder
on every frame. No earlier decoder or fixture is modified.

## Results and scope

| Classification | Tile instances |
| --- | ---: |
| Visible delta tiles | 3,411,222 |
| Safe all-quantized-coefficients-zero visible delta COPY_REF | 2,216,647 |
| Exact byte-equal visible delta tiles, optimistic oracle upper bound | 2,216,647 |
| Byte-equal visible delta tiles with nonzero coefficients | 0 |
| Visible delta tiles requiring reconstruction | 1,194,575 |
| Hidden CONST128 tiles across all frames | 134,358 |
| Zero-coefficient visible key tiles, still full-write baseline | 13,813 |

Every conservative COPY_REF is asserted to be exactly byte-equal to the prior
accepted reference tile. The equality oracle compares actual 64-byte tiles,
not hashes or metadata. Equality remains an oracle upper bound: nonzero
coefficients may produce identical output after rounding or clipping in general.
The equality between these two counts is an observed property of this corpus,
not a classification rule or general codec guarantee.

Hidden tiles are a distinct CONST128 operation: 256 Y and 19 each U/V, totaling
294 per frame. They never become COPY_REF. Key frames retain the full-write
baseline even when coefficients are zero or their pixels match a prior frame.
This evidence makes no RTL, physical throughput, or timing claim.

## Standard-library Python interface

```python
import importlib.util
from pathlib import Path
path = Path('experiments/python-gamebub-v82/native/data.py')
spec = importlib.util.spec_from_file_location('v82_native_data', path)
data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(data)
for frame in data.iter_frames():
    assert len(frame['tiles']) == 8100
    assert len(frame['tiles'][0]) == 64
```

`iter_frames(root=None, *, verify=True)` reads all frames in cohort/ordinal order.
Each yielded dictionary provides:

- `tiles`: `list[bytes]`, 8,100 actual reconstructed 64-byte tiles, in Y 5,400 /
  U 1,350 / V 1,350 order. Each tile stores its eight raster rows consecutively.
- `planes`: the same bytes grouped into three tile lists, for convenience.
- `same_mask`, `zero_coeff_mask`, `hidden_mask`, `copy_ref_mask`: each is
  `bytes(8100)` of individual 0/1 values; these are not packed bit masks.
- `copy_mask`: `copy_ref_mask` sliced into the three plane masks.
- `cohort`, `ordinal`, `fid`, `refid`, `key`, `previous_fid`: accepted frame
  identity. A key's `refid` is `0xffffffff`; `previous_fid` can still exist at a
  periodic key because equality is observed against the previous accepted frame.
- `encoded_base_bytes`, `hud_bytes`, `packet_bytes`: encoded lengths in bytes.
  The two embedded encoded packet lengths plus the 80-byte CU66 envelope equal
  `packet_bytes`. `hud_bytes` is the encoded HUD packet length.
- `packet_sha256`, `canonical_sha256`, `hud_sha256`, `display_sha256`,
  `canonical_tag`, `encoded_base_sha256`, `encoded_hud_sha256`: frozen oracle or
  encoded data identities. `canonical_sha256` hashes full raster Y/U/V planes;
  it is not a tile-major hash. The index additionally records `tiles_sha256` and
  `masks_sha256` per frame.
- `copy_ref_count`, `same_visible_delta_count`,
  `nonzero_equal_visible_delta_count`: per-frame operation counts.

`same_mask` is defined even for periodic keys, but is all zero when no prior
accepted frame exists. `zero_coeff_mask` includes hidden zeros and key zeros;
only `copy_ref_mask` incorporates delta and visible eligibility. Geometry is
720x480 YUV420; capabilities and epoch 25 are pinned in `index.json`.

## Binary artifacts and reproduction

The native folder contains 15 `data/chunk-*.bin.gz` files, totaling 68,719,355
compressed bytes. Every chunk contains at most 32 frames. The largest raw chunk
is 17,651,124 bytes, less than 17 MiB. Each raw record is:

1. A four-byte little-endian JSON length.
2. That many UTF-8 JSON metadata bytes.
3. 518,400 tile bytes (8,100 x 64).
4. Four 8,100-byte masks in `same_mask`, `zero_coeff_mask`, `hidden_mask`,
   `copy_ref_mask` order.

`index.json` records each raw and compressed SHA256, byte counts, record count,
source pins, frozen parent hashes, compiler description, build/run commands,
capabilities, per-frame digests and totals. Gzip uses a deterministic zero mtime.
The checked binary SHA256 is
`4d6beec5544b9b29e8ba25f5b3ef0b9ab748e6e71363c33f9d6e1691ea988216`.

Collection command from the repository root:

```sh
python3 scripts/cu66-v82/collect_native.py
python3 experiments/python-gamebub-v82/native/verify_data.py
```

The collector refuses to overwrite an existing `native/index.json`; reproduction
must use an isolated checkout or preserve this evidence elsewhere first. It uses
container `gamebub-cu66-v69-build`, configured with four CPUs and 4 GiB, compiles
one source with `g++ -std=c++17 -O2 -Wall -Wextra -Werror`, and gives the binary a
unique `/build/v82-native-*` name. `commands.log`, `compiler.txt`, `compile.log`,
`native.log`, `summary.json`, `verification.json`, and `artifact-manifest.json`
retain the provenance and outcome. The binary is retained as `collector.bin`.

The independent loader verification reassembles the original raster planes
from all exported tiles and matches every frozen canonical SHA256. It also
recomputes every equality bit from actual prior bytes, recomputes COPY masks,
checks each COPY against equality, checks all CONST128 tiles, and verifies every
raw/gzip chunk digest and full record coverage. All checks passed.

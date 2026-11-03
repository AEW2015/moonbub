# Compressed-bank capacity profile

This reports **file sizes only**, with no gameplay video or JPEG payload redistributed. `analyze.py` verifies each JPEG file's length and SHA-256 against its local manifest before calculating counts and percentiles. The oversize rule is strictly `size > capacity`: a frame equal to the cap fits. Percentiles use nearest rank, `ceil(p × N / 100)`, with one-based rank. The saved `results.json` records manifest hashes, source metadata, exact oversize IDs and aggregate counts.

| Local input sample | Frames / unique JPEG hashes | Maximum | p95 | p99 | >32 KiB | >48 KiB | >64 KiB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Mass Effect gameplay sample | 300 / 299 | 30,662 B | 29,337 B | 29,784 B | 0 | 0 | 0 |
| Separate accelerated Mass Effect combat sample | 90 / 90 | 33,324 B | 32,477 B | 33,324 B | **2** | 0 | 0 |
| Synthetic long-run pattern | 1,800 / 1,800 | 27,493 B | 27,192 B | 27,368 B | 0 | 0 | 0 |

The accelerated combat sample provides a concrete **32 KiB counterexample**: zero-based frames 50 and 51 are 33,256 B and 33,324 B. This sample was taken at 25 fps and replayed at 30 Hz; it is a size-stress clip, not native 30 Hz gameplay. For a 90-frame sample, nearest-rank p99 is the maximum. The separate 300-frame sample is roughly ten seconds from a precompressed source, with one duplicated JPEG after resampling. Both gameplay samples were scaled/padded to 720×480 and encoded with Pillow 10.4.0, JPEG quality 65 and 4:2:0. The 1,800-frame sample is a generated pattern, not gameplay; its generator specifies quality 65 and 4:2:0. Neither sample represents every scene, encoding setting, host or game, and JPEG size is not bounded by the largest value observed here. These results make no video-quality claim.

All three local samples fit 48 KiB, but that observation does **not** make 48 KiB a guaranteed safe cap. Any implementation with a smaller limit than the current protocol's 256 KiB maximum must check the declared length before beginning a write, define an oversize drop/re-encode policy, and test it. Do not assume a sample maximum is a general bound.

For the project-named XC7A100T, AMD's [7-series data sheet](https://docs.amd.com/api/khub/documents/2LByHkO~nSZXcei2D55fTg/content) lists 135 RAMB36 blocks. Under a conventional 32-data-bit layout with 4,096 payload bytes per RAMB36, estimates for **two** banks are:

| Capacity per bank | Estimated RAMB36 per bank | Two-bank total | Share of 135 |
| --- | ---: | ---: | ---: |
| 32 KiB | 8 | 16 | 11.85% |
| 48 KiB | 12 | 24 | 17.78% |
| 64 KiB | 16 | 32 | 23.70% |

This arithmetic excludes parity-bit packing, memory width/depth mapping changes, FIFOs, decoder, line buffers, metadata, placement and all other device uses. The [7-series memory guide](https://docs.amd.com/api/khub/documents/9gZGbqBxtlKXxBfkBt~lAg/content) describes the 32-data-plus-4-parity organization. The estimates are not synthesis, actual hardware identification, fit or timing evidence.

## Reproduce

Set the following environment variables and run `./run.sh` from this directory; it runs three tests for percentile rank, exact-cap boundary, hash tampering and duplicate frame IDs, then verifies every local JPEG and writes aggregate JSON to `OUTPUT`:

```sh
GAMEPLAY_MANIFEST=/home/lori/gamebub-tools/verilator-study/gameplay300-qspi/fixtures/manifest.json \
COMBAT_MANIFEST=/home/lori/gamebub-tools/verilator-study/gameplay90b-qspi/fixtures/manifest.json \
SYNTHETIC_MANIFEST=/home/lori/gamebub-tools/verilator-burst-memory/sixtysec-run1/fixtures/manifest.json \
OUTPUT=/tmp/capacity-profile.json ./run.sh
```

A fresh run reproduced the retained `results.json` byte-for-byte. The manifests and JPEGs stay in their existing local directories; the script does not copy or transmit them. Availability of those local artifacts is required to rerun the verification.

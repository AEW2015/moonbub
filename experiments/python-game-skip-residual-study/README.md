# SR01: exact coefficient modes and bounded residual pruning

This is a new Python-only residual format at the unchanged **720×480 coded
canvas**, with 720×405 active native game content. It uses GM01's immutable ACKed
reconstructed key, zero-motion predictor, ROI quantizer map and frozen Q14
arithmetic. SR01 is not GM01-compatible, HEVC/AV1-conformant or implemented by
installed Sunshine, ESP32 firmware or FPGA RTL.

Two experiments remain deliberately distinct:

- **Exact syntax:** each plane actually serializes both dense CP02 and a split
  zero/DC/full-block representation, then chooses the shorter complete plane.
  Reconstructed coefficients/pixels equal the quantized GM control exactly.
- **Bounded pruning:** P frames may replace background residual blocks with zero
  or DC-only coefficients if an actual integer inverse comparison keeps every
  reconstructed YUV sample within 2 or 4 levels of quantized GM. This is an
  explicitly lossy coding decision. Keys are never pruned, and priority pixels
  retain the same quantized GM output, not lossless original source RGB565.

The native temporal comparison uses two independent 60-frame windows from one
second. There are also 16 held-out keys from four seconds and 18 separately
labeled synthetic frames. Five controls are actually coded: GM, SR dense-only,
SR exact minimum, SR prune-2 and SR prune-4. There are **154 source IDs, 770
decisions, 755 admitted packets and 15 paid noise rejections**. The related native
sources are precompressed 25/29.88 fps footage, not live 30 distinct fps capture.
Case and profile rows must not be counted as independently captured images.

## Retained results

| Native temporal window | GM mean bytes | SR exact | SR prune-2 | SR prune-4 |
| --- | ---: | ---: | ---: | ---: |
| Combat | 8,802.37 | 8,511.15 | 7,884.43 | 7,679.05 |
| Second | 12,025.50 | 12,088.50 | 11,179.52 | 10,479.08 |

Exact syntax saves about 3.3% on combat with identical pixels. All three second-
source planes choose dense coding, so its 63 bytes of new plane headers make the
packet larger than GM. The exact chooser minimizes **new plane candidates**, not
the entire choice between raw GM and SR packets. Raw GM fallback is a possible
follow-up; it is not implemented here. Held-out keys likewise show a small combat
syntax saving and a second-source overhead. Pruning is disabled for those keys.

Prune-4 reduces native bytes by roughly 12.8% in both windows. It pays for actual
inverse/error checks at the host; nothing is assumed free.

| Native temporal / profile | Complete preparation | Actual receive | Source active RGB565 MSE |
| --- | ---: | ---: | ---: |
| Combat GM | 19.11 ms | 18.20 ms | 22.750 |
| Combat SR exact | 21.29 ms | 15.09 ms | 22.750 |
| Combat SR prune-4 | 28.36 ms | 10.84 ms | 20.492 |
| Second GM | 19.91 ms | 21.80 ms | 14.969 |
| Second SR exact | 23.41 ms | 20.92 ms | 14.969 |
| Second SR prune-4 | 29.30 ms | 13.54 ms | 16.186 |

Both GM and SR receivers use the same bit-exact zero/DC reconstruction bypass;
the new syntax is not credited with introducing that unrelated optimization.
Pruning reduces decoder work and bytes, but its extra encoder work means complete
service does not generally improve. Source MSE improves on combat but worsens on
the second sample. A bound against already quantized GM does not guarantee improved
source quality or subjective appearance. Priority-region source MSE is unchanged.

The flat synthetic fixture shows a larger exact saving, 3,517→2,477 bytes, with
receive falling 11.00→3.83 ms; this is not a gameplay rate claim. Noise still fails
the cap in all five profiles. Rejection costs are retained, including the losing
dense/split attempts and pruning work. No rejected candidate consumes credit or
updates the reference/last-issued generation.

## Priority protection requires the chroma footprint

The first benchmark stopped on a real protection assertion. Frozen color
conversion bilinearly upsamples chroma using right/down neighbors, so merely
keeping the scale-8 chroma block unchanged does not protect its last odd RGB
pixel at a priority boundary. The final implementation additionally protects
the right, lower and lower-right neighboring chroma blocks. A regression proves
the resulting priority RGB output stays identical while background pruning still
occurs. `first-run-error.log` is a historical failed attempt, not final evidence.
The complete benchmark was rerun after this repair with fresh source pins.

## Syntax and state contract

The outer SR01 header has GM01's bounded layout, new magic and flags. Flags 0/1
mean exact P/key, 2 means prune-2 P and 4 means prune-4 P; pruned keys and nonzero
motion vectors are rejected. Each plane has a 21-byte `SP01` header recording
mode, block count, mask length, DC count and compact full-payload length.

Dense mode contains ordinary CP02 at its original block width. Split mode emits
a two-bit MSB-first block map: 0 is zero, 1 is DC-only and 2 is full. Padding must
be zero, DC values are nonzero signed little-endian int16 within ±2048, and full
blocks must actually contain AC. Full blocks are sent as ordinary CP02 with
`blocks_w=1`, preserving selected blocks in raster order. All actual map, DC,
CP02, header and CRC bytes count toward the 49,152-byte cap.

Parsing enforces exact lengths, bounded geometry and coefficient domains before
receiver state publication. The encoder checks cap before commit. ACKs bind
epoch, pending frame and actual body CRC; P ACKs release credits without changing
the key. CRC is not authentication. This immediate-feedback algorithm does not
model GF02/GA01 queues, physical readers, finite delivery or P reference promotion.

Nine tests cover dense/split round trips, invalid modes/padding/counts/DC bounds,
partial syntax failures and atomic frame rejection, actual prune bounds and ROI
protection, the chroma halo, key equivalence, cap-before-commit, wrong ACK/expiry/
credit/key drain and rejection of unsupported global prediction. The independent
benchmark decoder checks every admitted packet against reconstructed expectation;
all exact outputs equal GM and all pruned outputs satisfy their actual YUV bound.

## Reproduction and implementation limits

```sh
python -m unittest -v test_skip_codec.py
python verify.py                       # read-only retained evidence check
python benchmark.py > run.log 2>&1     # regenerates; external media required
```

Use the study virtual environment. The final run completed in 76.61 seconds of
host wall time and pins 13 source/dependency files plus native media manifests.
Per-frame profile execution order rotates; host load remains uncontrolled.
Preparation includes transform, quantization, both actual plane coding attempts,
inverse/error/recheck work, cap admission and key reconstruction. Read/resize,
map construction, correctness reconstruction, hashing and metrics are excluded
from stage timers. Full host coefficient/residual/output arrays remain allocated.

For an FPGA design, the modes suggest direct zero fill, constant DC fill and a
reduced full-block entropy path. This Python evidence does not prove DSP count,
BRAM or SDRAM service, native CPU latency, FPGA fit, actual transport or sustained
hardware 30 fps. A native port should first validate the exact syntax with raw-GM
fallback; controlled pruning then needs application quality evaluation and the
same chroma footprint protection. Keep these decisions separate from recent-P
reference experiments and from exact HG01 source-word overlays.

# Mandatory HUD reservation for the AR03 hardware handoff

This Python component closes the v19 cap-policy gap while preserving **720×480
coded / 720×405 active** geometry. It reserves all four exact RGB565 HUD patches
before choosing base quantization. A frame either contains every requested patch
or is rejected as a whole. The complete AR03 cap remains **49,152 bytes**.
AR03/AF03 syntax and the existing reference decoder are unchanged.

## Causal policy and ownership

`Policy.prepare` first executes the existing bounded patch encoder/cache and
validates all four current-source patches. Their real length prefixes and encoded
bytes are reserved. It then tries at most these four declared legal ROI maps:

| Attempt | Base ROI scale | Background scale |
| --- | ---: | ---: |
| 0 | 8 | 16 |
| 1 | 8 | 32 |
| 2 | 16 | 32 |
| 3 | 32 | 32 |

Smaller scales are finer quantization. The fourth map is uniform scale 32. The
base ROI rectangles are `(16,48,192,80)` and `(160,352,400,80)`; requested exact
patches are `(22,54,160,24)`, `(22,82,160,24)`, `(168,360,320,24)` and
`(168,390,240,24)`, totaling 21,120 pixels. Patches affect display only; YUV
prediction banks never include them.

The prepared mandatory callback supplies all patches, even if the remaining
base budget cannot accommodate them. The frozen encoder's **complete packet**
validation then rejects that whole candidate. Each rejected actual base build is
paid, discarded, and checked for unchanged issued identity, geometry and bank
publication state. All candidate analysis/forward-transform work is repeated and
charged in this first implementation; it does not pretend the bounded search is
free. A future encoder may share one analysis safely, but that optimization is
not implemented here.

Only the first complete fitting candidate is retained for explicit commit.
Commit/receive/AF03 ACK uses actual bytes and reconstructed references. Source
leases are owned by the candidate API and released after commit/discard or
exception. A provably impossible patch reservation skips base work, with paid
patch preparation and no issued identity. If all four maps fail, the frame is
rejected; no patch is silently omitted. Decisions use only current encoded byte
counts and declared map order, never future frames or decoded-quality oracles.

## Results

Four sequential cases use 48 existing source frames from each of
`mass-effect-2600.mp4` and `mass-effect-7200.mp4`, beginning at four seconds.
There are **96 source acquisitions / 192 policy decisions**. Both clips are
1280×720 at 29.88 fps. The component has no wire, capture clock or presentation
schedule; it does not prove 30 fps. Offline PyAV extraction is excluded, while
BOX construction is measured per source/policy row.

| Scene / policy | Accepted | Full requested HUD | Partial HUD | Maximum packet bytes |
| --- | ---: | ---: | ---: | ---: |
| 2600 / cap-aware baseline | 48 | 48 | 0 | 29,877 |
| 2600 / mandatory | 48 | 48 | 0 | 29,877 |
| 7200 / cap-aware baseline | 48 | 34 | 14 | 48,760 |
| 7200 / mandatory | 48 | 48 | 0 | 48,898 |

All **96 accepted mandatory decisions** preserve all 21,120 source-canvas RGB565
words, with zero mismatch. The primary scene is byte- and pixel-identical across
policies. The complex scene selects ROI8/background16 on 25 frames and
ROI8/background32 on 23; those 23 first attempts are real paid discards.

For its first key, the complete fine-base attempt would be 54,894 bytes; the
mandatory coarse-background output is 47,238 bytes. The cap-aware baseline fits
48,203 bytes by omitting the fourth patch. Mandatory policy retains that patch
and changes background quality instead.

On matched complex-scene source IDs, complete bytes change from 2,103,725 to
2,116,013 (+0.584%). Mean active RGB-channel MSE after RGB565 expansion changes
from 27.0335 to 34.0921. This is a visible, measured lossy-background tradeoff,
not source-lossless compression. Changed keys/promotions also alter later
prediction history. `analysis.json` retains same-reference subsets and full
per-frame requested/selected/omitted coverage rather than attributing the delta
to pure coding efficiency.

Baseline patch preparation is included in its candidate build clock. Mandatory
patch preparation is a separate clock before base search; compare the complete
paid components, not build time alone. Every losing map/build/discard is retained.
Measured Python work is neither native host throughput nor FPGA/ESP32 service.

## Hardware-development artifacts

`results.json` retains 20 isolated golden fixtures: IDs 0, 1, 8, 24 and 25 for
both policies and scenes. They cover keys, P frames, promotion and independent
refresh, including the mandatory coarsened key. Content-addressed compressed
objects contain complete AR03 bytes, AF03 feedback, source-canvas RGB, decoded
canonical int16 YUV, display RGB565 and actual precondition bank arrays/tags.

These fixtures are **isolated packet tests**. Their precondition banks are setup
state for replay, not additional data transmitted by the codec. A hardware test
must load the exact named precondition bank, decode the supplied packet, compare
YUV/display words, and publish only after complete validation. Do not present the
five sampled fixture IDs as a self-contained streamed sequence.

The retained verifier independently replays every fixture through the frozen
AR03 receiver, checks all selected original words and output arrays, validates
publication banks/AF03, and performs 20 atomic CRC-negative rejections. Ten unit
tests include the all-four-attempts-exhausted case with reuse of the unissued ID,
impossible reservation, stale commit, source mutation, callback exception and
source-lease cleanup. A pre-existing external confirmed-bank lease survives
paid rejected attempts, an accepted retry, commit/discard and callback failure;
cleanup restores the recorded reader baseline rather than requiring zero readers.

## Reproduction

Use Python with NumPy, Pillow and PyAV; versions and conservative relative
source/dependency hashes are recorded in `results.json`. From this directory:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_model.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python verify.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python analyze.py --check
```

`verify.py` needs retained objects, not external media. `analyze.py --check` is an
untimed hash-bound reconciliation. `benchmark.py` regenerates timings and objects,
needs both source clips, and checks source pins before/after its run. Set
`GAMEBUB_MEDIA_DIR` to another input directory if needed. Keep pinned files fixed
during a campaign.

No installed Sunshine/ESP32/FPGA endpoint is changed. There is no gateway timing,
RF/ISA calibration, native heap, BRAM/DSP fit, routed clock, line-deadline or
physical 30 fps proof. This packet/quality/ownership contract is ready for
hardware-developer porting and vector tests, not product enablement.

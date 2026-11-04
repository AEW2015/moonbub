# Fixed sparse gate for exact Game Bub codec selection

This study tests whether a cheap, causal screen avoids unnecessary SR01 encoding work while retaining the unified AR02/AF02 protocol, exact UI patches, and acknowledged two-bank prediction. It is a Python measured-host finite pipeline experiment, not a hardware 30 fps demonstration.

The immutable policy is in `gate-config.json`. After one normal GM01 analysis and quantization, the encoder samples at most 64 evenly spaced raster coefficient blocks in each of the three planes. A block qualifies when all 63 AC coefficients are zero (including fully zero blocks). **All three planes must have a sampled zero/DC-only fraction of at least 0.90.** Only then is a real exact SR01 candidate serialized and compared with the complete GM01 inner packet. Otherwise GM01 is used and the uncoded SR01 length remains unknown. The threshold was fixed before reading the new validation window and was not tuned afterward.

There is no additional transform, quality reduction, pruning, future-frame inspection, or estimated SR payload used as an admission oracle. The selected payload is the smallest **evaluated** complete inner packet. The screen and every actual losing candidate are charged to the encoder. UI selection, full validation, reconstruction, reference tags, parsing, and feedback work also remain paid.

`cadence_codec.py` subclasses the frozen unified encoder and copies its `prepare` body with a small screen around exact SR generation. `model.py` copies the parent unified finite model and changes only its encoder import and allowed mode names. `copy-origin.json` records both original hashes. The frozen original files were not edited.

## Experiment

Three profiles all enable the same four exact source-RGB565 UI rectangles (21,120 selected pixels when all fit): GM01 only, unconditional exact GM01/SR01 selection, and the gated exact selection. The three profiles use identical two-bank, promotion, transport, decoder, and feedback policies.

There are nine cases, 540 input-ID events:

- Two original native 60-frame windows, one from each clip, at 1 second; three profiles each.
- A new native 60-frame window from the second clip, starting at 10.04 seconds; three profiles.

The earlier 180-frame window ends at PTS 119600, time 10.00669344 seconds. Starting at 10 seconds would reuse one frame, so the split was corrected to 10.04 seconds before timing. The benchmark requires every new PTS to exceed 119600 and records source-hash/PTS identity disjointness. Repeated image hashes within or across windows are reported independently; PTS identity does not imply unique image content. No frames are synthesized or repeated to fill a window.

Input files are precompressed 25/29.88 fps videos extracted offline. The coded canvas is 720×480, with 720×405 active video. The finite model schedules their IDs hypothetically at 30/s and measures actual Python component service costs. It does not establish 30 new physical captures/s, real-time ESP32 operation, FPGA timing, SDRAM arbitration, QSPI framing, or display scanout.

The inherited model uses independent serialized virtual servers with assumed 8 Mb/s links, 160 Mb/s QSPI, 10 ms feedback delay, and a 60 Hz display. Publication is staged until paid decoder/ACK work completes; deadline and expiry win; read leases and ownership remain bounded. Oracle hashes and image-quality metrics are excluded from component timing.

## Validation and reproduction

```bash
cd experiments/python-game-cadence-gate-study
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_model.py test_gate.py test_benchmark.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py > run.log 2>&1
/home/lori/gamebub-streaming-prototype/.venv/bin/python verify.py
```

Fifteen tests cover bounded/static/noisy sampling, unsampled-coefficient causality, unchanged exact RGB/YUV/reference tags and AF02 feedback, exact UI, paid cap rejection, staged decoder/ACK deadlines, loss/conflicting-feedback behavior, resource bounds, copied-model parity for GM/exact controls, and retained commit-hash reporting. Retained sources are hashed before and after timing. `verify.py` rechecks those pins, all 540 event ledgers, gate decisions and actual candidate counts, the new validation split, wire admission, exact UI, reference/feedback publication, and same-reference paired base/display hashes.

Cross-profile timing changes can change which IDs are admitted and promoted. Therefore base equality is compared only for common IDs with the same reference tag, key/promotion flags, and predictor identity; display equality additionally requires the same UI patch selection. Skipped SR candidates are never asserted to be larger. A gate that stays off or fails to improve cadence is a valid result, and no earlier independent gain is multiplied into this study.

Retained numeric results are in `results.json` and the compact per-case output is in `run.log`.

The first attempt stopped after three short control cases because the reporting helper looked for a private oracle field removed from serialized packet rows. `failed-initial-run.log` retains that partial attempt. The reporting helper now uses retained decoded commit hashes, a regression test covers it, and the full nine-case retained run uses newly pinned sources. Gate/codec/model logic and fixed threshold were unchanged; no new-window metrics had been reached. The partial attempt is excluded from the numeric comparison.

## Retained results

The retained run took 56.41 seconds on this host. All 32 executed source pins match. The verifier passes all nine cases/540 events, and all 15 tests pass. There were 521 decoded commits with 21,120 exact UI pixels each, zero UI mismatches, and no unresolved ownership at drain.

| Window (60 input IDs) | Profile | Presented eventually | Diagnostic IDs/s | Mean frame bytes | Mean encode service ms |
| --- | --- | ---: | ---: | ---: | ---: |
| Combat at 1 s | GM + UI | 57 | 31 | 10,003.53 | 21.119 |
| Combat at 1 s | Exact + UI | 58 | 31 | 9,716.64 | 23.015 |
| Combat at 1 s | Gated + UI | 58 | 31 | 10,017.52 | 21.125 |
| Second clip at 1 s | GM + UI | 58 | 30 | 19,590.12 | 29.302 |
| Second clip at 1 s | Exact + UI | 58 | 31 | 19,561.71 | 32.614 |
| Second clip at 1 s | Gated + UI | 58 | 30 | 19,590.12 | 29.294 |
| New second clip at 10.04 s | GM + UI | 58 | 30 | 21,716.21 | 29.226 |
| New second clip at 10.04 s | Exact + UI | 58 | 30 | 21,711.02 | 32.934 |
| New second clip at 10.04 s | Gated + UI | 58 | 30 | 21,716.21 | 29.379 |

The diagnostic is the inherited finite-window presentation count, not an acquired/physical frame rate; the short one-second steady window can report 31 due to phase/boundaries. The eventual counts include drain time. In the new window, all three profiles present 55 IDs before the capture-window end and 58 eventually.

**The fixed gate did not improve selection:** it stayed off for all 174 native preparations. Screening cost 18.631 ms total, about 0.107 ms each. Gated output therefore uses GM01 throughout. On the new window, this avoids unconditional SR work but provides no advantage over simply choosing GM-only. Exact selection saves only 5.19 mean frame bytes there, while mean encoder service rises by 3.71 ms versus GM-only. These are host observations from one retained execution, without confidence intervals or a target-time claim.

`analyze.py` is a separate untimed analysis bound to both the retained results hash and its own source hash. The actual unconditional-exact controls have matching source identities, reference/promotion identities, GM inner lengths, and paired decoded base hashes for all 174 gated IDs. They expose 79 real SR wins skipped by this conservative screen: 58/58 combat controls (17,451 total inner bytes), 18/58 second-clip controls (1,648 bytes), and 3/58 new-window controls (301 bytes). These are **actual control encodes**, not inferred lengths for uncoded gated candidates. The fixed policy was not retuned after observing them.

The new validation has PTS 120000 through 144000, spanning 10.04016064–12.04819277 seconds, with 60 unique image hashes, no repeated hashes within the window, and no hashes shared with the prior selected window. The final native PTS interval contains a gap; the experiment preserves it rather than inventing a missing frame. Source identities and paired same-reference base/display hashes verify cleanly.

Keep **GM + exact UI** as the simpler deployment candidate from this experiment. Retain unconditional exact selection as a measured compression/decoder tradeoff, particularly for sparse combat frames. Do not deploy this particular 0.90 screen as a general optimization: it adds work and misses useful observed control encodes. A different gate would require a new predeclared policy and independent validation; this iteration stops at the negative result.

```bash
/home/lori/gamebub-streaming-prototype/.venv/bin/python analyze.py --check
```

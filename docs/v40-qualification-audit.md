# V40 qualification audit

## Cohort and verification

The source bundle contains four PTS-selected windows and 457 unique post-letterbox
RGB24 canvases: 119 each from `mass-effect-10000`, `mass-effect-4500`, and
`mass-effect-1600` over local `[6,10)` seconds, and 100 from
`mass-effect-combat` over `[20,24)`. Selection uses decoded frames' rational
`PTS × time_base`, preserves gaps, and does not resample. The first three
streams report frame counts different from the decoded counts; the manifest
records both. The archived canvases contain 473,817,600 raw RGB24 bytes in
457 content-addressed objects.

These clips are portions of one precompressed Mass Effect walkthrough lineage,
not new games or captures. The first three were checked for overlap against the
specific v24 AB38 calibration prefixes from `mass-effect-2600` and
`mass-effect-7200`, with zero matching canvas hashes. That exclusion does not
make this corpus project-wide unseen. The source README also notes prior use of
the 10000 clip, extensive prior use of combat, and missing shared-manifest
origins for the 1600 and combat files. See the [source manifest](../experiments/python-game-source-v40-study/manifest.json)
and [source README](../experiments/python-game-source-v40-study/README.md).

| Study | Archived and replayed scope | Result and timing boundary |
|---|---|---|
| [Source qualification](../experiments/python-game-source-v40-study/README.md) | 4 windows, 457 unique canvases; offline source/PTS/hash verification | No codec or native comparison is performed. |
| [First-key cap probe](../experiments/python-game-key-cap-v40-study/README.md) | 4 frames × 2 quantizer maps = 8 key packets; 21,120 exact HUD words per packet | All fit. Analysis and integrated encode are reported separately; HUD generation and receiver work are outside those clocks. This is a key-only probe. |
| [Causal CS37 qualification](../experiments/python-game-control-qual-v40-study/README.md) | 457/457 accepted frames, 20 keys, zero rejects and zero bg32 retries; ROI8/bg16 | Max complete packet 48,540 bytes (612-byte headroom). Source read, conversion, HUD generation, analysis, and encode attempts are separate; decode and scoring are excluded. No physical throughput claim. |
| [Causal CS38/AB38 qualification](../experiments/python-game-binary-qual-v40-study/README.md) | 457 CS37 input packets; 2,742 full/compact AB38 alternatives; 457 selected CS38 packets | 1,371 arithmetic planes selected, zero old-payload fallbacks; 910,706 bytes saved (10.2732%) versus these CS37 inputs. Only six AB38 candidate encodes per frame are timed; CS37 input encoding, decode, wrap, and receiver proof are paid elsewhere or excluded. |
| [Exact local-mode pilot](../experiments/python-game-exact-v40-study/README.md) | 27 actual/synthetic frames; 1,686,096 candidate-block recomputations; 162 rank-trial planes | Zero candidates accepted; every actual candidate packet was larger. Pair clocks include control and candidate proof paths, all rank trials, and model checks; fixtures, HUD load, archive/metric work, independent decoding, network, and display are excluded. |
| [Native quality grid](../experiments/python-game-native-qual-v40-study/README.md) | 48 settings = 4 windows × 2 codecs × 6 parameters; 5,484 actual AUs independently decoded; 5 settings have at least one cap-failing frame | Per-setting `wall_encode_decode_ms` times codec encode plus decode. It excludes source preparation and full capture-to-display service. These are sampled settings, not an optimized or continuous quality curve. |

The control qualification's cumulative source-read / conversion / HUD-generation
/ fast-analysis / integrated-encode-attempt times are recorded per window in
its `results.json`. HUD generation is substantial and is not included in the
binary study's candidate-only arithmetic clocks. The two studies must not be
combined into a complete sender rate or latency claim.

## Hash and artifact fields

The manifests preserve several distinct SHA-256 roles; similarly named fields
are not interchangeable:

- Source provenance uses external `media_sha256_before` and
  `media_sha256_after`, plus repository `source_code_sha256` pins. Per decoded
  frame it records `native_rgb_sha256`, `canvas_rgb_sha256`,
  `rgb565_sha256`, and `common_yuv420_u8_sha256`. Content-addressed canvas
  objects carry both `raw_sha256` and `stored_sha256`.
- The key-cap and causal control studies use `source_pins_sha256`; their frame
  records use `source_canvas_rgb_sha256` or `source_rgb_sha256`,
  `source_rgb565_sha256`, and `source_yuv_sha256`. They also retain HUD,
  normalized/reference, and output tags. Their packet objects carry
  `raw_sha256` and `stored_sha256`.
- Binary qualification keeps those source hashes and records
  `reference_tag`, `normalized_tag`, and `display_sha256` for each causal
  CS38 packet and all alternative AB38 objects.
- The exact-mode and native studies use top-level `source_sha256` maps as
  source-code/input pins. Their row-level `source_sha256` values identify
  source plane data (exact study) or common YUV (native study); their displayed
  outputs use `display_sha256`. Native access-unit and extradata objects have
  raw/stored digests.
- The comparison JSON's top-level `source_sha256` pins the four input
  manifests/results and comparison script. It contains per-window summaries,
  not a replacement for the packet-level hashes in the studies.

Each study retains an offline verifier log. The source, key-cap, control,
binary, exact-mode, and native verifiers respectively report 457 source frames;
8 key packet replays; 457 causal control frames; 457 causal CS38 frames plus
2,742 alternatives; 27 exact-mode frames; and 5,484 native AUs. The native
verifier reports exact source/HUD checks and no encoder invocation. The
comparison is reproducible with:

```sh
python experiments/compare_prototype_v40.py --check
```

The first relocated v40 replay exposed a portability gap: the frozen source
study's original `verify.py` reopens the original media to re-hash it, so that
single check fails in a self-contained archive. The frozen source verifier and
all source pins remain unchanged. The portable bundle now invokes
`experiments/verify_source_archive_v40.py`, which replays and re-hashes every
archived canvas and derived RGB565/YUV frame, rechecks PTS/order/count/geometry
and calibration overlap, and checks the recorded before/after media digest
evidence against the declared digest table. It explicitly reports
`original_media_redecode=false` and `current_external_hash_check=false`; it
does not claim fresh verification of the external media file. The top-level
portable verifier and provenance exporter include this helper.

## Native comparison and limits

The comparison selects only among the six tested settings per codec, requiring
the stated MSE gate and zero complete-frame cap failures. It separately reports
mean-only, mean-plus-peak, and every-frame gates; it does not interpolate rate
curves or claim matched-quality BD-rate or perceptual equivalence.

For the combat window, CS38 has active MSE 29.3515 and peak-frame MSE 35.0413.
No sampled x265 or SVT-AV1 point is feasible under the comparison gates and cap.
For example, x265 CRF24 and AV1 CRF34 have mean MSE below CS38 but respectively
2 and 5 cap failures, and their peak MSE exceeds CS38. The cap-fitting points
are coarser and have mean MSE above CS38. This absence of a feasible sampled
combat point does **not** establish a custom-codec win: the grid is sparse, and
the peak-rate study is still pending.

The other three windows do have smaller sampled native points that also meet
every-frame MSE gates: x265 CRF28 for 10000 and 1600, and SVT-AV1 CRF28 for
4500. That is evidence against a blanket custom-codec victory on this cohort,
but remains a comparison of selected sampled settings using source RGB565 MSE,
not a standards-wide or perceptual-quality conclusion. No study here establishes
physical 30 fps, native ESP32 transport limits, FPGA cycle/resource fit, or
complete end-to-end service timing.

## Negative mode experiment

The exact local-mode pilot maintained exact reconstructed YUV-block and future
reference equality, then guarded the real serialized packet size. It found
zero accepted alternatives across 27 frames: the two 12-frame gameplay prefixes
and three synthetic fixtures. All actual candidates were larger than their
control packets. The strict guard correctly retained control, so this result is
a verified zero-gain finding for that local proxy, not evidence that the wider
codec family has no remaining opportunities.

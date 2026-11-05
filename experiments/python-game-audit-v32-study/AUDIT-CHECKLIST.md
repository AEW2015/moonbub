# V32 independent audit checklist

- [x] Require exactly two scenes × three causal policies × 48 ordered frame IDs.
- [x] Reparse accepted CP27/GM27/HU25/JA27 objects and all candidate pairs; check bounded stored/raw hashes, exact framing and tags, 49,152-byte complete cap, and 21,120 HUD words per frame.
- [x] Verify source YUV lineage across cohorts and each cohort's own key/P accepted-reference chain.
- [x] Recompute each v30 strict shadow, shrink strict/1% quality gates, byte-saving selection, all attempt costs, aggregate summaries, and finite nonnegative timings.
- [x] Bind the all-attempt pixel replay to exact v32 results and verifier SHA-256; verify 288 accepted rows and 1,504 attempts.
- [x] Require exact strict-control CP27 packet, ACK, RGB metric, and RGB565 hash parity against the retained v30 strict baseline for all 96 rows.
- [x] Recompute every sampled HEVC/AV1 mean MSE and complete byte total with the same per-frame HU32 bytes plus 60-byte binding; select the lowest-byte point that meets custom MSE and per-frame cap.
- [x] Report HU32 custom base accounting under the same byte vector and label it prospective because HX32/CP32 integration is absent.
- [x] Run negative checks for parity, cap, selection, quality, reference, metric, and non-finite timing errors.
- [x] Emit deterministic `audit.json`; `--check` compares bytes without rewriting; pin audit, tests, results, replay, component evidence, and source inputs.

No claim is made for native endpoint throughput, RF/display performance, physical 30 fps, or an integrated HX32/CP32 receiver.

# V27 independent arithmetic and provenance audit

This audit independently checks retained bytes, framing, arithmetic, source lineage, and candidate selection. It does not repeat the full decoder/pixel replay, which is separately retained by the campaign verifier.

## Cohort and profile

- Require exactly 2 scenes × 2 policies × 48 frame IDs (192 CP27 pairs), with unique ordered IDs and matching source YUV hashes across paired rows.
- Parse CP27, GM27, HU25, and JA27 using exact lengths, CRCs, component SHA bindings, frame/epoch identity, reference IDs/tags, and pair/ACK tag bindings.
- Accept syntactically valid bounded GM27 motion-map spellings. Do not require sender-optimal re-encoding; record this as the explicit GM27 receive profile.
- Check CP27's actual base + HU25 + 60-byte binding equals the retained complete packet, and JA27 is exactly 65 bytes.

## Selection, quality, and standards

- Check every candidate attempt, including losing work: actual archived base/pair bytes, complete cap, actual active squared error/sample counts, quality eligibility, and paid analysis/encode timing fields.
- For `frozen_trace`, require selected mode/background and decoded image/tag/MSE to reproduce the corresponding v26 full result exactly.
- For `unified_causal`, require selection among complete-cap-fitting candidates whose active SSE is no greater than the same-reference zero candidate; choose the minimum actual complete bytes.
- Report retained entropy-v26 block-major values as a separate control; require frozen-trace image/MSE/ref lineage to equal prediction-v26. Do not imply that distinct block-major and direct-GM27 encoders are byte- or image-identical, and do not claim this Python audit replays pixels.
- Recompute native standard comparison using each retained v24 coded access-unit byte count plus the current exact HU25 bytes and 60-byte CP27 binding. Select only sampled operating points with aggregate measured active MSE at least as good as the new custom case.
- Keep v24's exact HUD-word accounting and native access-unit costs. Do not use bare-byte counts or substitute rounded quality thresholds.

## Accounting and claim limits

- Recompute aggregate complete bytes, integer SSE/sample totals, exact HUD words (21,120 per frame), per-frame cap, and nominal-30 Mb/s projection from actual rows.
- Report CPU encoder/analysis/receiver/ACK timing separately from projected rate. The nominal ID-rate projection is not measured FPS.
- Make no FPGA fit, native frame-rate, or physical transport claim.

## Provenance and repeatability

- Verify every retained archive object's stored and raw length/hash with bounded decompression, and enforce paths remain under the declared experiment root.
- Pin result JSON, source-pinned inputs, relevant scripts/logs, and the audit's own source using sorted repository-relative SHA-256 entries. Exclude generated audit outputs from their own source inventory.
- Emit deterministic `audit.json`; `--check` must compare bytes without rewriting. A repeated build from unchanged inputs must emit identical bytes.

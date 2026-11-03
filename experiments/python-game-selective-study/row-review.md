# Independent HR01/HG01 review

Read-only review of `python-game-row-study/row_codec.py`, benchmark, tests, persisted results, verifier and README. No executed source or timed artifact changed.

## Findings

No concrete pixel-decoding, palette-index, row-boundary, or malformed-packet state-commit bug found in this review.

One small accounting clarification: `benchmark.py:55` constructs the GM01 priority scale map before the base timer starts at line 56. Thus `charged_prepare_sum_ms` charges actual base encode plus all HP01/HR01 candidate encoding/wrapping, but excludes priority-map construction. Existing prose says “base encode” rather than claiming complete service, so this does not invalidate packet-size or candidate-cost results. Explicitly listing map construction among exclusions would prevent comparing this sum directly against a selector whose timer includes map construction. Do not describe that sum as full processing service or a 33.3 ms deadline proof.

## Checks supporting the result

- HR01 row decode bounds each token's output against the row width, checks complete token bytes and exact final output count; coded rows have exact length prefixes and full payload consumption.
- Palette mode validates at most 256 sorted unique RGB565 entries, in-range indices and use of every declared palette entry. RAW/direct-word modes prohibit palettes.
- HG01 bounds count, base length, total patch bytes and geometry; checks all rectangle geometry and overlap before decoding any patch words; validates every patch before entering the GM01 receiver.
- Frozen GM01 validates syntax, state/reference constraints and reconstructs before committing `last_frame_id` or the anchor. Therefore the optimized single-base-decode HG01 order retains malformed-base/patch atomicity. This is normal exception/syntax atomicity, not recovery from allocation failure after the GM commit.
- HP01/adaptive comparisons use identical base bytes, identical region rectangles and exact RGB565 output. Broad/compact areas differ and are reported separately. Over-cap outputs remain marked failed admissions.
- Candidate time includes actual HP01 plus RAW, direct-row and applicable palette-row encoding, including losing candidates. It does not silently keep only winning-candidate time.
- Source bindings include the codec helpers and fixture-generation code. Real media IDs/hashes/PTS and selected indices are retained in manifests. Synthetic labels and the related/precompressed/native-FPS limits are present.

An independent lightweight probe exercised **440** token round trips across units 1/2, widths 1–2,048, palette domains 1/2/17/256, and run lengths 1/2/3/128/129. A malformed inner coded-row payload with valid repaired patch and wrapper CRCs was rejected while the GM receiver remained uninitialized (`last_frame_id=-1`, no anchor). No heavy benchmark was rerun.

## Scope gaps before integration

HG01 is intentionally not accepted by frozen GH01/GF02 peers. The row receiver's bound is syntax/geometry based rather than a negotiated 49,152-byte admission cap; this is necessary for the current over-cap algorithm comparisons. An integrated selector/receiver must enforce the actual negotiated complete-frame cap before expensive decode work. Python allocates full packets and full patch/frame arrays, so the row-oriented format alone establishes neither bounded target BRAM use nor physical memory service. Native 30-distinct-frame gameplay, sustained target FPS, deadline/loss/reorder behavior, and subjective HUD legibility remain unproved.

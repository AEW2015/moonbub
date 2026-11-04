# V26 independent arithmetic and provenance audit

This audit checks retained Python experiment artifacts and their accounting. It does not establish native FPGA implementation or sustained native frame rate.

## Frozen comparison thresholds

- Load the exact v25/v24 comparison values from their retained JSON artifacts; do not substitute rounded values from the Markdown summary.
- Keep the complete-body rate threshold paired with its corresponding active-area MSE threshold, scene, codec, and quality criterion. Report each pair and whether both conditions pass.
- Preserve the measured sampled operating-point qualification. Do not describe a nominal 30 IDs/s projection as measured throughput or native FPS.

## Pairing, tags, and quality

- Pair results only for identical source frame IDs and source SHA-256 values. Record the reference ID/tag policy per row and reject a comparison if reference lineage changes without explicit disclosure.
- Verify predictions and residuals are tied to the declared source/reference IDs and the decoder-visible reconstructed reference state; do not treat encoder search references as decoder evidence.
- Require exactly 21,120 HUD words per frame and the expected exact-word result for the transmitted HUD profile.
- When comparing with standards, recompute each standard's body using the same retained HUD rows and identical binding/envelope bytes as the custom candidate; preserve each standard's own frozen quality result.
- Recompute aggregate bytes and quality from retained integer sums/counts where available. Keep decoder pixel/hash replay evidence separately attributed to its retained verifier and log.

## Complete-body and transport arithmetic

- Reconcile each frame's video/base, HUD, binding/container, and any explicitly modeled overhead to the actual complete body object length.
- Sum complete body bytes across the cohort and project at nominal 30 source IDs/s using `bytes * 8 * 30 / frames / 1_000_000`.
- Enforce the frozen 49,152-byte packet cap for every accepted packet; mark any above-cap packet rejected.
- Keep projected Mb/s, any hypothetical FPS arithmetic, and measured/native FPS as separate fields. Native FPS remains unproven by this Python study.

## Archive and provenance

- Verify each referenced archive object is inside its declared experiment root, has the declared exact stored length and stored hash, decompresses within the declared raw-size bound, and matches its raw hash.
- Verify source identity pins for all inputs and the audit's own source files. Store paths relative to the repository root and SHA-256 values in deterministic order.
- Exclude the generated `audit.json` from its own hash inventory to avoid an output cycle. A repeated `--check` must produce byte-identical JSON when inputs are unchanged.

## Evidence boundary

- This is independent Python-side accounting/provenance evidence for counter, prediction, and entropy studies.
- Cite decoder/reconstruction evidence separately; do not claim that these arithmetic checks independently replay codec pixels or prove FPGA/RTL behavior.

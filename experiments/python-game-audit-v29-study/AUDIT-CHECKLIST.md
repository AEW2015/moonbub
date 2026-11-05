# V29 independent audit checklist

Scope: audit retained v29 Python study results from serialized packets and compact replay evidence. Do not rerun full optimization campaigns.

- [ ] Pin the v28 frozen inputs, v29 study source files, result files, and retained accepted packet/replay artifacts with sorted repository-relative SHA-256 values.
- [ ] For every frame and policy, parse the actual complete packet and independently reconcile GM/base, HU, binding, and framing/CRC lengths. Enforce `complete_bytes <= 49,152`; report exact maximum and headroom. Do not accept base-only or projected sizes as complete packet evidence.
- [ ] Parse each accepted HU packet and independently sum rectangle areas to exactly 21,120 HUD words per frame. Reconcile accepted frame count, per-frame values, and aggregate words; reject missing, repeated, or reordered IDs.
- [ ] Pair policy rows on exact source frame IDs and source pixel hashes. Separately validate each policy's accepted reference ID/tag against the previous accepted decoded output, and check the retained decoded output hash/tag against the actual packet. A shared source hash alone does not establish shared reference history.
- [ ] Recompute accepted output SSE/MSE from retained decoded-plane evidence and the paired source; reconcile integer totals, denominators, per-frame metrics, and summaries. Verify quality gates compare candidates on the same source and current reference.
- [ ] Verify adaptive decisions are causal: trigger inputs are available before the additional encode, no future-frame/held-out labels are used, and every attempted coarse, refined, or fallback candidate and its work/time is recorded, including losing and over-cap candidates.
- [ ] Recompute selected wire-byte totals and nominal-rate projections from actual accepted complete packets. Audit timing sums from all recorded paid stages and state the measured boundary.
- [ ] Inspect prose and JSON claims: Python host timings only; nominal ID/s rate is a projection. Do not claim native ESP32, FPGA, RF, presentation, or physical 30-fps qualification.
- [ ] Retain a deterministic machine-readable audit report and focused unit tests for cap boundaries, HUD-word arithmetic, source/reference lineage, output hash binding, and summary recomputation. Exclude generated audit outputs from their own inventory.

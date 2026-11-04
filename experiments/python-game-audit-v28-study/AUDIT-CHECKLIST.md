# V28 independent audit checklist

- Verify exact ordered frame IDs and common source YUV hashes across the v28 policies and frozen inputs.
- Parse actual CP27, GM27, HU25 and JA27 bytes; check CRCs, inner digests, exact component lengths, references, tags, bank fields, exact HUD coverage (21,120 words), 60-byte binding, 65-byte ACK and complete 49,152-byte cap.
- Recompute active integer SSE/sample MSE from retained candidate metrics; compare every selected result against the zero candidate using the same background/reference and enforce minimum complete bytes among eligible attempts.
- Sum all paid analyses and all attempted encodes, including losing/over-cap candidates; recompute service, search counters, selected tap gathers and case summaries from the actual rows.
- Bounded-decompress every retained archive object with exact raw/stored lengths, SHA-256 and stream-end checks; reject paths outside the declared experiment root.
- Verify the full optimized/exhaustive packet and ACK parity against v27, and independently check all 96 paired parity rows and the 24-row search probe.
- Recompute tap-probe per-plane 1/2/4-tap logical gathers from compressed motion vectors and each retained timing summary from all five samples per P input.
- Recompute native HEVC/AV1 operating points from actual v24 access-unit byte counts plus current HU25 and 60-byte binding; select only points with aggregate MSE no worse than v28.
- Pin source inputs and own audit/test/checklist sources with sorted repository-relative SHA-256 values. Exclude generated audit outputs from their own source inventory.
- Require deterministic `audit.json`; `--check` compares exact output bytes without rewriting.
- Keep pixel replay attributed to the full retained verifier. Nominal 30-ID/s rates are not native FPS, and Python gather counts do not establish FPGA or physical-link fit.

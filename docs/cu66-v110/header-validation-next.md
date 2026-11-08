# Header validation after the final Count route

The strongest next exact-source hypothesis is to prepare the header length sum on existing read edges. No RTL, proof, policy, preflight or native change is made here. The bounded V110 checkpoint ends with nine measured negative trials; this proposal has no clock-pass claim.

The actual final Count route has WNS −1.022 ns, TNS −1125.069 ns and 4620 setup failures; hold is +0.085 ns, pulse +3.750 ns and routing errors zero. Its worst path is ingress `fetch_bytes[23][0]`→`counts[1][5]/CE`: 15 levels, seven CARRY4s, 10.769 ns data delay (3.384 logic + 7.385 route). Forty-four of the 50 reported paths launch from that header byte to metadata enables/state/raw-mode controls. Byte23 belongs to the third length word; the original four-length arithmetic precedes all metadata writes. The terminal enable net has fanout241. This is current routed evidence, not the earlier placed mapper hypothesis; no mapper launch appears in these 50 paths.

The exact source is `cu66-v110-count-domain/br88_packet_ingress_sync_v91h.sv`, HEADER lines420–433. Four little-endian unsigned32 lengths occupy bytes14..17,18..21,22..25,26..29. Use **two unsigned33 pairs**, then zero-extend each to **unsigned34** before adding. A pair can reach 2^33−2; all four can reach **2^34−4**. Keep the original RHS `({2'b0,size_bytes} - 34'd46)`, including unsigned34 subtraction semantics. A 32-bit total or 32-bit subtraction followed by extension is not equivalent for arbitrary malformed/synthetic values.

All length bytes are stable immediately after the successful owned F_HEADER WAIT29 response commits byte29. The existing schedule provides ample time:

| Existing edge | Earliest safe private preparation |
| --- | --- |
| REQ30 | Capture both33-bit pairs and the unsigned34 size-minus46 target |
| WAIT30 | Capture the zero-extended34-bit pair sum |
| REQ31 | Capture sum equality to the prepared target |
| WAIT45, then HEADER edge | Original branch consumes the predicate, thirty edge intervals later |

A two-stage version can combine the final sum and comparison at WAIT30, but may leave a long arithmetic/compare cone on that register. The extra private sum stage separates them without changing any public edge. Packet size is captured at start and stays stable throughout the header read. Reads are sequential; a stalled response only adds preparation time. Bytes30..45 cannot overwrite bytes14..29 before HEADER.

A narrow implementation could update these private pipeline registers unconditionally, without reset/cancel enables or a new public valid/status signal. Values after reset, abort, failure, restart or later descriptor reads are unowned. Every legal fresh HEADER follows the complete46-byte fetch and refreshes all stages before consumption. Start does **not** clear every old fetch/metadata array, so old values must never be treated as belonging to the new owner merely because start occurred. A consuming uncancelled HEADER assertion must compare the prepared result against an independently widened original expression; retain all old assertions. Directly forced synthetic fixtures need coherent preceding stable edges, not candidate-derived expected verdicts.

Only replace the original length-sum branch predicate. Preserve the original reset/abort, start, active-context error/done overrides and HEADER priority: **CRC error3 → basic-header error4 → length-sum error4 → metadata assignments → raw-specific error4 or state transition**. Never fail early when a speculative sum disagrees: a simultaneously bad CRC must still report error3 on the original edge.

The last priority detail is observable. Once CRC/basic/sum pass, the original code writes all four `lengths`, `counts[0..3]` and `raw_mode` **before** its raw-specific length/count check. A malformed raw packet can therefore fail while committing those metadata values. The count and raw-mode views remain public even when metadata-valid is false; the stored length writes must retain their original priority too. Moving writes behind the raw check, combining all header checks into a single bad flag, delaying failure or clearing those values would break invalid-cycle/public equivalence. Counters and metadata publication must retain the original edge.

The companion JSON records a small independent width model: 13,750 boundary/random arithmetic rows passed, including full unsigned32 extremes and unsigned34 underflow. This is a model check, not RTL qualification. Future tests must retain the complete old/new public/invalid/debug/counter/memory miter and goldens; add CRC/basic/sum conflicts, overflow/wrap values, malformed raw partial writes, abort/start/reset around bytes21/29/30/31/45 and HEADER, stale response failures and retries. Full canonical qualification remains required.

Two other final families prevent a header-only guarantee. Four `context_blocks[9]`→scratch `prepare_block/R` paths remain (worst −0.895 ns, 78.617% route); their actual validation/cancellation fanin needs source/netlist mapping before proposing another predicate. Two tile5→group_visible paths are in **`coefficients/admission`**, not scratch (−0.940/−0.891 ns). Admission's `visible_group` counts sixteen tile+offset hidden/visible predicates. A future owned-next-group preparation would need every plane/tile/group transition and the independent hidden-geometry oracle; existing coordinate flags alone do not prove that population count. Routing, enable fanout and those separate paths remain after a logical header cut.

`experiments/python-gamebub-v110/header-validation-analysis.json` pins the actual final receipt/reports, all18 current/native snapshots and inspected sources. No additional native trial is proposed within this completed checkpoint.

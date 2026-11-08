# V107 remaining timing cones and conditional next cuts

Historical measured cones used to choose earlier V107 experiments are retained below. The latest completed source/strategy selection is in [the native comparison](vendor-comparison.md), and current follow-up targets are in [next timing cuts](next-timing-cuts.md). Earlier top-path lists do not identify the current worst path.

Keep the10 ns constraint fixed. HEADER/TABLES needs an actual completed implementation result before selecting another edit. The independent measured ingress-count/scratch-valid cone below already shows that removing the older header arithmetic cone alone cannot be treated as timing closure. No RTL, qualified source, test, compile or vendor flow was changed or run for this review.

## Measured evidence and current limits

| Actual variant /stage | Source→destination | WNS | Data delay | Logic /route | Levels |
| --- | --- | ---: | ---: | ---: | ---: |
| Quant-aligned /routed | scratch tile_emit_index[0]→inverse bank1 word9 value[0]/CE |−4.428 ns |14.139 ns |2.861 /11.278 ns |12 |
| Elastic /synthesized | admission header[47][3]→bit_cache[1]/R |−3.131 ns |12.490 ns |4.555 /7.935 estimated ns |22,8 CARRY4 |
| Elastic /routed | admission header[46][1]→state[4] replica/D |−3.447 ns |13.332 ns |4.095 /9.237 ns |21,7 CARRY4 |
| Elastic /routed | ingress counts[3][4]→scratch tile_valid[1][59]/D |−3.216 ns |13.163 ns |4.247 /8.916 ns |18,8 CARRY4 |
| TABLES /synthesized, later update | ingress counts[1][2]→scratch prepare_block[0]/R |−1.451 ns |10.810 ns |3.984 /6.826 estimated ns |15,6 CARRY4 |

The completed [quant route top50](../../experiments/python-gamebub-v107/native/20261108T041620226345Z/reports/route-setup-paths.rpt) contains50 paths from the same tile_emit_index bit to coefficient-word CEs. The completed [elastic route top50](../../experiments/python-gamebub-v107/native/20261108T042607353046Z/reports/route-setup-paths.rpt) contains45 header[46][1] paths and five counts[3][4] paths. The ingress family reaches tile_valid bits59,10,32,42 and11, with slack−3.216 through−3.037 ns. Header fanout reaches state, q_start/residual_start/residual_end CEs, mode_cursor resets and plane state. These are multiple endpoints of shared control cones, not independent arithmetic kernels.

The old raw tile_emit_index→inverse CE family is absent from the elastic top50. That supports retaining the qualified130-bit boundary; it does **not** prove nonnegative slack for every remaining coefficient path. A top50 report is ranked evidence, not an endpoint-specific closure certificate.

At the original05:19Z read snapshot, HEADER native [receipt](../../experiments/python-gamebub-v107/native/20261108T045700315943Z/receipt.json) is RUNNING and its external results directory contains only part-query.txt. There is no available post-HEADER setup report to attribute a new worst cone or timing gain. A later TABLES synthesis report is now available and is recorded below; neither that synthesis estimate nor the older ranked reports establish new routed closure. Therefore implementation recommendations remain conditional on the actual new route.

Final disposition: the HEADER-only job was deliberately stopped for scheduling
at 1,831.615 seconds, exit 143, before any synthesis checkpoint or timing report.
The [cancellation record](../../experiments/python-gamebub-v107/coordination/header-scheduling-cancellation.json)
binds the terminal receipt and explains the user-directed reset-study priority.
The [earlier log snapshot](../../experiments/python-gamebub-v107/coordination/header-log-at-051916.txt)
is retained byte-for-byte. This is not a watchdog timeout or a measured timing failure.

## HEADER runtime is an observation, not a failure diagnosis

The live HEADER log reached "Start Timing Optimization" after applying timing constraints at elapsed approximately274 seconds. Root's monitor subsequently reported approximately1260 seconds overall with CPU active near100%; the bounded job had not terminated. The log contains two accepted hill-climbing-move messages after that phase banner. Silence between messages is not evidence of a hang or tool defect.

The HEADER source adds five declared35-bit private sums (at most175 declared state bits before constant/unused-bit optimization) and five byte-index clock enables. Each capture contains at most one addition:39 mode+128,43 prior-mode+QMAP,47 HUD+4,51 prior-residual-start+DATA,55 prior-residual-end+HUD-tail. HEADER_CHECK uses cached equality and low32 address projections. The old64-bit source expression already has constant-zero upper ranges; the measured eight-CARRY4 path does not justify claiming a64-bit physical adder was replaced by a35-bit one. The intended benefit is the intervening register boundaries.

Additional registers/enables and altered arithmetic structure can change whole-top optimization choices. Current runtime/log data does not identify which structure accounts for elapsed time, establish pathological arithmetic inference, or predict the final critical path. Mapped resource/timing reports are still needed. No source should be altered solely because optimization is taking longer.

## Later actual TABLES synthesis update

The report at `/home/lori/gamebub-build/cu66-v69/v107-tables-20261108T052651767313Z-4d6323/results/synth-setup-paths.rpt` (dated05:34:38Z) now selects ingress counts[1][2]→scratch prepare_block[0]/R, WNS−1.451 ns and10.810 ns data (3.984 logic /6.826 estimated route),15 levels /six CARRY4s. The timing summary reports1,674 setup failures /TNS−1014.154 ns, zero hold failures (WHS0.193 ns) and zero pulse-width failures (WPWS3.750 ns). These remain synthesized estimates, not completed routing/signoff.

Its path follows `used_bytes` /`starts[3]` carry logic, carry-save sum control and successful-begin gating into the prepare_block synchronous reset pin. This independently confirms that the metadata-admission cone survives beyond the older header-dominated source. The next priority is the metadata-plan/control cut after the new route, rather than assuming reset-payload or RAM changes remove it.

**The R pin here is functional initialization, not a removable blanket reset.** Source prepare_block<=0 executes on a successfully validated new scratch transaction and establishes its first tile. Removing that assignment breaks operation. The preceding registered plan/pure-metadata validation can localize the accepting control; deleting required initialization cannot.

HEADER was subsequently cancelled explicitly for scheduling/resource policy before a synthesis checkpoint/report. That cancellation provides no HEADER timing result and is not evidence of a hang. The live-log snapshot above remains historical runtime evidence.

## First independent priority: ingress counts→scratch tile_valid

The actual route starts at `coefficients/child/packet_decoder/synchronous.ingress/counts_reg[3][4]/C`. It traverses four CARRY4s in `used_bytes_reg` arithmetic, LUT compression/control, another four CARRY4s, acceptance/error logic, a bank-wide net with fanout64, and the local tile_valid D logic. The final endpoint is `coefficients/child/scratch/tile_valid_reg[1][59]/D`. The report's netlist names include `scratch/sum5_return[30]`; flattened cell names alone are not a source-level ownership boundary.

The concrete source binding is direct: [ingress meta outputs](../../fpga/experiments/cu66-v106-ingress/br88_packet_ingress_sync_v91h.sv#L143) publish counts[1..3]; [the child pipeline](../../fpga/experiments/cu66-v106-telemetry/br88_pipeline_v91h.sv#L176) connects them to scratch begin_count1..3. [Scratch plan combinational arithmetic](../../fpga/experiments/cu66-v106-scratch/packed_scratch_v91g2.sv#L210) computes:

- plan_start1 =32+aligned(blocks*2);
- plan_start2/3 add aligned(count1/2*4);
- sparse plan_used adds all three aligned count terms; raw plan_used is32+blocks*128.

The [helpers](../../fpga/experiments/cu66-v106-scratch/packed_scratch_v91g2.sv#L105) intentionally implement modulo2^32 arithmetic. `aligned(n)` is `(n+15)&0xfffffff0`, and sum3/4/5 are modulo32 carry-save forms. This differs from HEADER's exact non-wrapping total: do not copy the35-bit HEADER transformation here and silently change malformed-input arithmetic.

The [scratch IDLE acceptance](../../fpga/experiments/cu66-v106-scratch/packed_scratch_v91g2.sv#L424) has exact priority:

1. Existing outer reset/matching-abort, response ownership/error and drain branches precede the IDLE case.
2. On begin_valid in IDLE, stale epoch (`epoch_seen && begin_epoch<=last_epoch`) rejects with error2.
3. Otherwise block count0/>8192, count1>blocks*5, count2>blocks*15, count3>blocks*43, nonzero sparse counts in raw mode, or plan_used>262144 rejects with error1.
4. Only success updates epoch/ownership, plan outputs, starts/counts, assembler and tile bank state; it clears both64-bit tile_valid masks.

Thus raw counts participate in the **acceptance enable** of the128 validity bits, not in the value of one emitted coefficient. A scale/mode RAM rewrite does not remove this arithmetic dependency by itself.

### Preferred zero-added-cycle cut to evaluate

Compute and register the exact modulo32 plan plus pure-metadata error1 predicate **before existing METADATA exposure**, then carry that cache with the metadata owner. Keep the scratch's live stale-epoch check and outer cancellation/response priority at its original acceptance edge.

The actual ingress has useful existing edges: [HEADER](../../fpga/experiments/cu66-v106-ingress/br88_packet_ingress_sync_v91h.sv#L239) loads counts from cached32(30), cached32(34), cached32(38). These are little-endian fields; [cached32](../../fpga/experiments/cu66-v106-ingress/br88_packet_ingress_sync_v91h.sv#L81) reverses the stored bytes. Count3's final byte is fetched at index41; header fetch continues through index45 before HEADER validation. [FETCH_WAIT](../../fpga/experiments/cu66-v106-ingress/br88_packet_ingress_sync_v91h.sv#L289) provides real registered-byte arrival edges. A candidate can capture aligned terms/partial sums during these edges and the final plan/metadata-bad flag before METADATA. Current-byte forwarding must follow this little-endian layout. Earlier count fields and context_blocks are stable by then.

Compressed input additionally traverses DESCRIPTOR states, but **raw input can enter METADATA immediately from HEADER**. A design that initializes the cache only in DESCRIPTOR is incorrect. Uniform F_HEADER fetch staging or an independently prepared raw branch must cover that fast path. CRC/header/descriptor failures must retain their original error and timing; computing a dead plan does not authorize earlier rejection or publishing metadata early.

The cache interface should bind all original blocks/raw/counts/epoch fields, exact plan_start1/2/3/used, and the full error1 predicate. At selected scratch begin acceptance assert equality with the original expressions and owner. Preserve begin_ready timing; do not add a late cache-valid condition that silently changes public stalls. Cached metadata cannot replace the consumer's stale-epoch priority. Prepared states must explicitly initialize the cache invariant; actual complete packet tests separately establish readiness/cancellation/reachability.

This would change the measured counts→arithmetic→global-valid-clear cone into earlier counts→plan-cache FF paths and a short cache/epoch→scratch acceptance path. That is an implementable architectural target, **not a measured improvement**. Subsequent epoch/enable fanout may still require work.

### Explicit-latency fallback and unsafe shortcuts

A one-entry metadata/plan stage is a second option if existing edges cannot be used cleanly: accept an immutable metadata owner, register the exact plan/flags, and present the whole request to scratch on the next edge. It needs explicit upstream/downstream/discard conservation, busy/start/cancel ownership and coefficient backpressure until scratch accepts. This changes timing and requires latency-aware whole-pipeline qualification rather than exact-cycle comparison.

Do not simply remove the plan guard from tile_valid clearing, clear masks early on rejected begins, or narrow counts based on hoped-for valid inputs. Even unowned mask changes can alter combinational dense_value outside dense_valid, because [dense_value reads tile_valid directly](../../fpga/experiments/cu66-v106-scratch/packed_scratch_v91g2.sv#L232). Such edits need an explicit public/dead-state contract and matching checker; they are not an automatic exact-output timing fix.

## If HEADER's bit_cache/state enable cone persists

The existing [HEADER_BYTE caches](../../fpga/experiments/cu66-v107-header/cs88_admission_v91i2a.sv#L291) remove total/address arithmetic from HEADER_CHECK, but [HEADER_CHECK](../../fpga/experiments/cu66-v107-header/cs88_admission_v91i2a.sv#L308) still contains full header/range, identity64, reference and key predicates with ordered errors4/5/6/7/8. Its successful branch initializes bit_cache, bits_left, mode_cursor, coordinate and plane state. A new report must distinguish cached-total equality, residual range guards, identity comparison and wide success-enable fanout before choosing a cut.

A concrete zero-cycle next option is **registered exact header decision on HEADER_BYTE127**:

- After packet_total was captured at55, capture independent non-padding validation predicates at56, retaining full32 ranges and full64 identity semantics. All relevant fields are already stable. If the64-bit freshness comparator itself is measured late, split it into registered high32 less/equal and low32 less/equal components before recombining on another already-existing byte edge.
- Initialize a padding-bad accumulator before byte116, update it on every actual byte116..127 arrival, and include the current byte127 directly when computing the final decision.
- At existing byte127 capture the **ordered** accept/error decision. Error4 dominates padding/range/total5;5 dominates identity6;6 dominates reference7;7 dominates key/mode8. HEADER_CHECK then performs the original public state/output/error updates on its original edge using that cached decision.

Do not move reject() into byte127: that would change public error/counter/state timing. Do not let later bad padding incorrectly lose priority to a previously cached identity/reference error. Reset/start/abort must suppress captures, and selected HEADER_CHECK assertions must compare the cached decision with the entire original validation expression. This keeps successful addresses/metadata and failed-header held outputs unchanged.

Bit_cache has three meaningful write modes: successful-header clear, MODE_LOADED capture and MODE_BIT shift when bits_left is nonzero. A separate local write case can make those enables explicit after a registered header decision exists, preserving all original reset/hold/invalid-mode priorities. Merely naming a local wire or moving code into another always_ff block does not guarantee synthesis will replicate/localize the enable. The next mapped path must show whether D/CE/R fanout actually improved.

## Coefficient selector→inverse CE: retain the existing cut, measure its two halves

The quant route's original12-level cone included a tile-index net with fanout107, the64-word value/valid selector, an intermediate value net with fanout129, validation/ownership gates and the coefficient-word CE. It was about80% route delay. The [fixed-word bank process](../../fpga/experiments/cu66-v107-value-check/cu66_inverse_stream_v91j.sv#L962) still qualifies each write with input_fault==0 and current bank/index. [Input fault priority](../../fpga/experiments/cu66-v107-value-check/cu66_inverse_stream_v91j.sv#L932) is done/partial-tile4, index1, metadata2, scale/range3, token exhaustion7.

The qualified elastic stage registers the entire tuple before those inverse checks. If a future report returns to coefficient paths, request separate measured paths for scratch index→coefficient_boundary payload/D and stage payload/control→inverse word CE. Do not infer either half is closed just because the old cross-boundary path is absent from top50.

Conditional options:

- If stage payload→CE validation dominates, capture **pure token-local** range/scale/geometry predicates beside the existing tuple. Transport malformed tokens normally and use the cached flag at the original input_fault priority position; never suppress valid or ready to hide an error. Index-vs-fill_index and metadata-vs-current-bank ownership are consumer-state checks and cannot be precomputed against stale state at upstream acceptance. Token-bound assertions and complete16-bit range/domain tests are required.
- If local word-CE fanout dominates, a registered inverse commit tuple `(bank,index,value,valid)` can separate validation from physical word writes. Bank-ready/math launch must wait for the final pending commit or use proven forwarding; consecutive acceptance, fault cancellation, invalid/dead backing-data visibility and all debug/counter contracts need explicit treatment. It is an additional architectural latency change, not a wire-only enable rewrite.
- If the remaining scratch index→stage D selector dominates, a bounded four-word emitter window is a candidate: fixed index0/1 groups can be prepared at bank publication; prefetch the following four-word group while the current group emits; select only four entries on the output side. [Bank publication](../../fpga/experiments/cu66-v106-scratch/packed_scratch_v91g2.sv#L659), same-edge publish/release, index63 bank turnover, invalid-bit zero-fill, raw/non-tile mode and stalls need separate handling. Producer writes only the unready bank; published bank contents are stable. This is more complex and should be attempted only when the new endpoint report actually selects this half.

For all options, retain fixed10 ns setup/hold/pulse/legality/resource gates. No false paths, relaxed clocks, unconstrained internal endpoints or frequency claims follow from these source observations. HEADER/TABLES may expose another path; strategy or RAM-placement optimism cannot close the independently measured metadata guard cone.

## Evidence pins

- Quant route top50 SHA-256: `350a0a510de59344373f58763d19fd56b268279d997abf2f9fb7b7f138edbc2a`.
- Elastic route top50 SHA-256: `dca4fc1520a0d95f0e4405f73e9e8671f9a2303f7187cf28cbc8d69a04cb4889`.
- TABLES synthesized setup report SHA-256: `8aeb02ed4d95aa23fc764c1b6778c9bcd6408ca81a8c58012d8c8a2d9e1d9b50`.
- Elastic synthesized setup report SHA-256: `c8d021c8db1c061883e103876f745a9f72b13815ae6e54241174992366778b21`.
- Live HEADER log snapshot read2026-11-08T05:19:16Z:113,563 bytes, SHA-256 `80d5e2106a6713ee2d308f4b92f74de2ca2ff6f76df1d7f27969a9b5781c9180`. This identifies the read snapshot, not a final log/receipt.
- HEADER source: `7a417f9a647e77571e6d31d6780412bc62dda4bdc1ef879017266694df9763a9`.
- TABLES packaged source inspected as pending candidate: `b149c94ba1a5dd7f1d09384126c762d0bb0de5aa664baa4b76c29c631aeb652e`.
- Inverse value-check source: `c93bec92283985070c0ef343be3377d44ffa04c513e37232d8962344fb6180c9`.
- Scratch source: `0ee1196e2f0cafdf52742656d4c1a53604c79544c339b171989ad2785f051f8c`.
- Ingress source: `4342972a6cf42cebf4f01a82841c0bc7c1850292ca23362817f7f071af126093`.
- Child pipeline binding source: `c6f839570988768ac2a373302d8980ce9a6532ccbcf3c09415f9ca1c05959577`.

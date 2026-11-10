# V128 timing proposal from the measured V127 route

V127 improves the intended owner/mode path and the global result versus V126, but **125MHz setup timing still fails**. Its complete functional composition passes the four spatial, two peer and four byte/row-parent exact-stream comparisons with zero declared public-cycle change. The next physical trial should target the now-critical ingress RAW/selected-validation cone and the separate admission header-to-counter reset cone. An output ownership queue remains a future architectural option; it is not an automatic cure for either newly measured path.

This note proposes later work only. No selected V127 production source, frozen proof input, timing constraint or implementation recipe was changed for the analysis. Do not reroute this unchanged negative composition to search for a favorable placement. Qualified Source B100 remains the hardware-integration control.

## Terminal evidence and actual critical paths

The [fresh native receipt](../../experiments/python-gamebub-v127/native/20261110T190637913699Z/receipt.json) reports WNS−1.193ns, TNS−1762.554ns and6980 failing setup endpoints. Against V126's−1.867ns/−4427.979ns/10868, the improvements are0.674ns WNS,2665.425ns TNS and3888 endpoints. WHS is+0.075ns, minimum pulse slack+2.750ns, with zero hold/pulse failures. All73814 routable nets are routed with zero errors, and internal unconstrained endpoints are zero. Component I/O remains unqualified:1101 inputs and12884 outputs lack delay constraints. The historical V123 composition remains better globally at WNS−1.086ns/TNS−1709.649ns, although it also fails125MHz. V127 is not a promotion over all historical controls.

The [independent terminal audit](../../experiments/python-gamebub-v127/audit/native-independent.json) passes1530 evidence-integrity checks and explicitly reports `design_timing_pass=false`. Fresh routed utilization is33576LUTs/43594FFs,32RAMB36+12RAMB18,42DSP and4227CARRY4, with1253 control sets. Relative to V126 this is177 fewer LUTs,165 more FFs and one additional control set. Source-level zero added payload/register declarations do not guarantee zero mapped FF growth: synthesis and physical replication must be measured. Fresh methodology counts are28 SYNTH-6,55 TIMING-16,1000 TIMING-18 and one ULMTCS-1; they do not waive setup failures or component-I/O limitations.

The actual routed [setup report](../../experiments/python-gamebub-v127/native/20261110T190637913699Z/reports/route-setup-paths.rpt) contains two distinct priorities:

| Routed path | Slack | Data delay | Logic / routing | Depth |
| --- | ---: | ---: | --- | --- |
| `synchronous.ingress/raw_mode_reg/C` → `scratch/state_reg[3]_rep__0/D` |−1.193ns|9.140ns|2.529ns /6.611ns (72.331% routing)|11levels:3CARRY4,6LUT6,LUT5,LUT3|
| `admission/header_reg[124][0]/C` → `admission/tile_reg[15]/R` |−1.165ns|8.652ns|1.572ns /7.080ns (81.830% routing)|9LUTlevels|

The first RAW-mode net has fanout100 and1.504ns routed delay. The path reaches `context_decoder/dbg_coef_epoch[4]_INST_0`, three carry cells named under `context_decoder/error`, then `context_epoch_reg[31]_0[0]` (1.152ns net), context state decode and a scratch state tail. These names plus source inspection support a selected-metadata/validation/control dependency. They do **not** prove which exact arithmetic or comparison each mapped carry implements; do not label the carry chain an epoch comparator without a scoped mapped fan-in check.

The admission path passes header-error logic, `bits_left[3]_i_3`, `coord_cell[10]_i_4`, and `tile[31]_i_1` (fanout28,0.975ns net) before the tile FF **R pin**. This is an acceptance/error-derived counter-control cone, not a tile arithmetic D path. Removing a reset declaration alone is not justified by that report. The path is already within0.028ns of the global worst, so fixing RAW alone cannot establish125MHz.

## Matched owner and residual observations

The [matched read-only comparison](../../experiments/python-gamebub-v127/pipeline-observations.json) covers145 families:129 retained and16 new. Both existing8ns routed checkpoints were inspected with the same frozen scripts. Family minima can end at different physical FFs/replicas; this is a matched family comparison, not proof that every individual path improved.

| Family minimum slack, ns | V126 | V127 |
| --- | ---: | ---: |
| Scratch tile-overlap mode → all endpoints |−1.867|+0.451|
| Scratch tile-overlap mode → scratch state |−1.867|+0.986|
| Scratch raw-mode → all endpoints |−1.457|+0.127|
| Emit-bank → scratch state |−1.813|−0.367|
| Emit-bank → all endpoints |−1.813|−0.562|
| Scalar epoch → scratch state / all endpoints |−1.751|−0.671|
| Scalar block → scratch state |−1.380|−0.211|
| Scalar block → all endpoints |−1.380|−0.234|
| Ingress RAW mode → all endpoints |−1.100|−1.193|
| Ingress RAW mode → scratch state |−0.880|−1.193|
| Ingress RAW position → all endpoints |−1.012|−0.719|
| Producer cursor → original cell cache |+0.246|−0.489|
| Producer cursor → all endpoints |−0.397|−0.980|
| Producer state → prepared successor address |−0.086|+0.150|
| Prepared successor address → prepared ROM cell |+0.256|−0.111|
| Producer plane → all endpoints |−1.223|−0.920|
| Admission cursor → all endpoints |−1.020|−0.675|
| Admission tile → coordinates |−0.045|−0.421|
| Admission tile → prepared hidden-predicate D |+0.086|−0.644|
| Admission group end → coordinates |+0.007|−0.268|

The selected tile-mode→scratch-state family improves2.853ns, from13levels/9.864ns data to7levels/6.890ns. This supports a useful physical effect of the three-lane expression. It does not eliminate every owner-return failure: epoch, scalar and emit families remain negative. Conversely, the ingress RAW-mode→scratch-state family worsens0.313ns and becomes global worst. Producer cursor's all-endpoint failure reaches `admission/scale_store/words_reg/WEBWE[0]`, so a cache-only remedy would miss a real write-enable path. The cursor→cell-cache regression and tile→hidden-predicate regression must remain visible alongside the owner gain.

Named lane observations are partial. The tile-owner pattern matches78 baseline nets and110 candidate nets, exceeding the declared32-net fan-in cap. Baseline scalar-owner names are absent. Candidate scalar-owner matches one named net, while `child_owner_match` matches none. The raw [inspection table](../../experiments/python-gamebub-v127/pipeline-inspection/candidate-20261110T193258217290Z/inspection.tsv), rows718–719, returns32 startpoints for `scalar_owner_match0`:16 scratch `output_block` FFs and16 producer `expected_block` FFs. That is a block-comparison intermediate, not a complete epoch+block lane. The summarizer retains OWNER_LANE_NET records but omits OWNER_LANE_FANIN rows; inspect the preserved raw table for this evidence. Neither a complete48-bit owner cone nor three-lane physical isolation was established. Blank KEEP properties, optimized/renamed objects, capped groups and absent paths remain explicit gaps. The comparison retains131 baseline and163 candidate gap records. Source KEEP text and query name counts do not establish complete physical cone separation.

## Priority 1: cut the selected ingress-validation dependency

Use the **actual selected origins**, not older files that share their aliases:

- [Ingress V120-range](../../fpga/experiments/cu66-v120-range/br88_packet_ingress_sync_v91h.sv), around489–496: `raw_mode` selects full block/index/value/epoch/band views; epoch is `raw_mode ? context_epoch : ctx_epoch`.
- [Context V113-geometry](../../fpga/experiments/cu66-v113-geometry/br88_context.sv), around4110–4165: context start captures its epoch; a validated output captures the full epoch; parser errors and full-width run/range/end tests precede output/HELD progression.
- [Current scratch](../../fpga/experiments/cu66-v127-owner/packed_scratch_v91g2.sv), around408–419 and893–898: the selected `coef_epoch` participates in full32 ownership validation along with block, band, range/count and ordering predicates; invalid input chooses epoch error2 versus format error3, then preserves accepted memory debt through DRAIN.
- [Current child](../../fpga/experiments/cu66-v127-owner/br88_pipeline_v91h.sv), around127–129 and194–204: packet/store aborts and sparse coefficient transfer feed that boundary. These are earlier sparse-ingest paths than the dense output queue proposed separately.

First extract scoped mapped fan-in for the critical `dbg_coef_epoch`, carry output and scratch state tail, including actual driver pins. Separate epoch selection, block/raster selection, range/position validation, context error and accepted-memory drain effects. Retain endpoint identity, net fanout and cell/route delay, rather than assuming the source's apparent Boolean boundary survived synthesis.

A bounded cycle-preserving candidate is to expose direct RAW and context epoch/block views and evaluate their complete ownership/format comparisons before selecting a Boolean result, analogous to V127 at the earlier ingress→scratch boundary. This is a hypothesis until mapped fan-in identifies the participating mux. It must preserve full32 epoch/full16 block, scalar/RAW and context modes, every invalid/unready view, existing phase/count/range predicates, epoch-error priority and all cancellation edges. New internal ports or extra origins require their own source map/recipes and full regression. Do not assert that RAW mode implies an epoch match, replace selected tags with the current expected tag, or use validity/readiness as an ownership certificate. Do not narrow nonce/block widths or skip malformed cases.

If this would merely move a wide selection to another reconvergent cone, prefer an explicitly latency-changing, locally buffered **sparse-ingress acquisition/validation boundary**, with captured full tuple and tag-bound validation certificates. Keep speculative payload writes local and unreset where a proven valid/owner protocol allows; local validity/cancel/fault registers control publication. Registering only a global error/ready bit without retaining its complete owner and accepted memory obligations is unsafe. Define accepted-versus-offered malformed-input behavior, first-error priority, seal timing and terminal fences before changing the implementation. Prove steady-state initiation interval rather than accepting one validation bubble per coefficient. This is distinct from the dense output queue and needs its own measured benefit.

## Priority 2: shorten owned header acceptance to tile control

[Selected admission V125-tile](../../fpga/experiments/cu66-v125-tile/cs88_admission_v91i2a.sv), around548–566 and611–633, shows the relevant source contracts. Reset/start/abort invalidate coordinate ownership and initialize transaction metadata. HEADER_CHECK applies an ordered rejection chain: magic/version/format, lengths/padding/geometry, frame/generation freshness, reference identity, then key-frame mode restrictions. Only successful acceptance installs frame metadata, clears coordinate state and tile, prepares the first tile key, and selects KEY_TILE/GROUP_BEGIN.

Prepare independent header rejection-class predicates under a full owned header snapshot while already-required header bytes are loaded, then choose the original first error using the small registered predicate vector at HEADER_CHECK. The final padding byte must be forwarded on its actual acquisition edge or allowed to mature through a proven existing cycle; never read the previous frame's cached result. Each predicate needs packet epoch/size and snapshot freshness ownership, with reset/start/abort/error invalidation. Retain full64 generation and all original full-width comparisons. A final all-good enable still needs routed fanout/control review; adding a predicate FF does not alone remove the R-pin tail.

Do not indiscriminately remove `tile` resets or initialize it early on an invalid header. Current rejected transactions can retain old payload views; cycle-preserving changes must preserve those values too. A later speculative payload/view-selector organization is possible only with an exact logical-view invariant and preserved cancellation/first-error behavior. Trace actual R/CE/D loads after synthesis and route. The existing three prepared admission predicates and their owners remain constraints; they do not certify that all header acceptance work is already pipelined.

## Priority 3: registered dense ownership only if the remaining return needs it

The concrete [two-slot elastic-control option](elastic-control-options.md) identifies the current dense tuple, complete frame/child/block keys, separate acquisition and publication counters, next-block mapping, bank release, child completion and accepted ACK debt. It is future work, not part of V127. Its upstream capacity must be a local registered permit, with validation certificates attached to the exact queued tuples and proved II=1 after fill. Full-queue recovery bubbles are a separate permitted event. Keeping two slots alone cannot guarantee a useful initiation interval or remove an earlier RAW/error cone.

Use the matched owner residuals to decide whether that larger latency change is warranted after priorities1/2. Keep prospective queue occupancy/cancel/permit paths and producer/scale-memory write-enable paths in the same global signoff. Avoid repeatedly optimizing only the family that the immediately preceding version targeted.

## Gates and connection to the product goals

Freeze the next selected source recipe and declared cycle/latency contract before execution. For a cycle-preserving trial, retain all current zero-cycle oracles. For a declared latency change, compare complete ordered tuples, errors, physical request/ACK ownership, hashes and publication fences with a bounded latency scoreboard; do not remove failing cycle assertions silently. Exercise full tags, both banks, RAW/context modes, stalled invalid offers, immediate retry, nonce exhaustion, cancellation simultaneous with acceptance/response, wrong-epoch ACKs and all error priorities. Re-run the actual decoder, V97 transport, peer fault injection and byte/row HUD/hash/seal/commit parent profiles. Keep every failed/interrupted attempt.

Measure one fresh same-recipe8ns implementation for a new proven composition. Require nonnegative setup/hold/pulse and zero internal unconstrained endpoints/routing errors globally; only a positive result receives an identical fresh repeat. Aim for setup margin rather than a barely nonnegative single run. No false/multicycle paths, relaxed clock, guessed I/O delays or source-name evidence qualify the design.

The goal is still720×480,30 distinct displayed frames/s over ESP32 Wi-Fi, followed by validated hardware packet-complete→publication decoding below10ms. Retained row last-input→validated-commit counts are1145104 ordinary and1553197 stalled: at an **assumed complete-parent125MHz** these project to9.160832ms and12.425576ms. The stalled profile needs at least303198 fewer cycles for strict below10ms, independently of closing the component clock. Buffering may add latency even while helping timing. Complete-parent routing/CDC/physical SDRAM, real ESP32 CPU/Wi-Fi/QSPI timing and sustained hardware frame delivery remain open. The current negative route establishes neither125MHz nor hardware30fps nor below10ms.

## Evidence pins

- Native receipt: `experiments/python-gamebub-v127/native/20261110T190637913699Z/receipt.json`, SHA-256 `47ca8bedc398933be0b70b79f94d1a93ecb9672e94c06139dbf0886d86d9557e`.
- Independent terminal audit: `experiments/python-gamebub-v127/audit/native-independent.json`, SHA-256 `46d71ad87837eaa16b04b7d46a923a5e96a1e6f37ffbc7571988bd3b2495da03`.
- Matched145-family comparison: `experiments/python-gamebub-v127/pipeline-observations.json`, SHA-256 `a61da887f703e754318d853bbf5cc8a4851528cf5fe769e9ae8811c77284f659`.
- Baseline query receipt: `experiments/python-gamebub-v127/pipeline-inspection/baseline-v126-20261110T175334641526Z/receipt.json`, SHA-256 `fe403727e1a339f004cc59dba196b4864c26c4bc4c9a140d08fb8fa77790fa3f`.
- Candidate query receipt: `experiments/python-gamebub-v127/pipeline-inspection/candidate-20261110T193258217290Z/receipt.json`, SHA-256 `589aada3a4181e1feeb52cd72a76785434f71d16571950eafdc29b49050cfe4a`.
- Selected source `fpga/experiments/cu66-v113-geometry/br88_context.sv`, SHA-256 `4eefd41198a0fcbfd80648e702a42f179315f7378969863c778bd06686ff6775`.
- Selected source `fpga/experiments/cu66-v127-owner/packed_scratch_v91g2.sv`, SHA-256 `8cd259792d2d7ea0c603117591e5e6033fbded7bacea10d598851f0cc5853ffc`.
- Selected source `fpga/experiments/cu66-v120-range/br88_packet_ingress_sync_v91h.sv`, SHA-256 `82f6e3be050d0848e0d9e29439ac31a1a78e981f3a5b9f74f2b6180925c6a2e4`.
- Selected source `fpga/experiments/cu66-v127-owner/br88_pipeline_v91h.sv`, SHA-256 `0596dce08b8d38651eb303b531e971de604d5ad7f45818a4a2d0d222d0a049cb`.
- Selected source `fpga/experiments/cu66-v125-tile/cs88_admission_v91i2a.sv`, SHA-256 `2f65ff770775404071e383890c75549ccb08ec9998993c86f1662cfed65d71eb`.

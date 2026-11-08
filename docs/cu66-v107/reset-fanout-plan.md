# V107 reset, fanout and control-set follow-up

Updated 2026-11-08 against completed V107 evidence. The user's reset/fanout request produced separate dequant and IDCT private-payload changes with actual public-cycle proof, per-bit reset/CE mapping, full canonical composition and a completed routed comparison. Historical snapshots remain unchanged. These changes reduce unnecessary global control dependencies; they do not eliminate local CEs, guarantee fewer global control sets, or close the 10 ns target. Status snapshots, control replication/remapping and further reset removal remain deferred. Operational next-cycle decisions must not be blindly delayed.

## AMD guidance applied to this source

AMD recommends deciding which storage actually requires a reset, with particular attention to datapaths that are overwritten before use. That does not authorize removing reset from ownership or physical-response tracking. See [UG9492026.1: When and Where to Use a Reset](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/When-and-Where-to-Use-a-Reset).

A control set combines clock, enable and set/reset. A7-series slice's eight FFs share these controls; many small incompatible groups can spread placement. See [UG9492026.1: Reducing Control Sets](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Reducing-Control-Sets). High-fanout critical nets and excessive tiny control sets are related physical pressures, but they are different measurements.

For replication, AMD favors intentional hierarchy/locality over indiscriminate global limits, cautions against global MAX_FANOUT, preserves optimization freedom with KEEP rather than blanket DONT_TOUCH, and excludes synchronizer stages from ordinary replication. See [UG9492026.1: Replicate High Fanout Net Drivers](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Replicate-High-Fanout-Net-Drivers). No new replication attributes or implementation directives are applied here. Root's complementary guide review is [amd-control-guidance.md](amd-control-guidance.md).

## Earlier elastic route: two different problems

The completed elastic [capacity report](../../experiments/python-gamebub-v107/native/20261108T042607353046Z/reports/route-capacity.rpt) reports15,287/15,850 slices used (**96.45%**),47,624/63,400 LUTs (**75.12%**) and37,218/126,800 FFs (**29.35%**). The [control-set report](../../experiments/python-gamebub-v107/native/20261108T042607353046Z/reports/route-control-sets.rpt) has1,201 unique sets and1,094 reported unused FF locations in occupied register slices. Its load histogram has118 sets below8 loads,470 in8–9,129 in12–13 and469 at16 or more. Thus this is not a design with1,201 single-register enables. Do not attribute every occupied slice or route detour to tiny control sets alone.

| Actual routed net | Fanout | Driver | Worst associated slack | Load types |
| --- | ---: | --- | ---: | --- |
| child/scratch/cancelled |7,141 |LUT3 |−1.202 ns |7,128 SR +13 data |
| transform/inverse/error_reg[1] |6,035 |LUT6 |−2.827 ns |5,944 SR +67 other primitive SR +24 data |
| coefficient_boundary/running14_out |2,242 |LUT3 |−2.015 ns |2,218 SR +24 data |
| transform/inverse/out_id[31]_i_1_n_0 |1,318 |LUT6 |−2.827 ns |1,313 CE +5 data |
| transform/dequant/coefficients[0] |1,078 |LUT3 |−1.932 ns |1,060 CE +18 data |
| coefficient_boundary/reset_2 |1,041 |LUT3 |−2.551 ns |1,041 data |

These come from the actual [high-fanout report](../../experiments/python-gamebub-v107/native/20261108T042607353046Z/reports/route-high-fanout.rpt). Worst associated slack is not the delay of the net by itself and is not necessarily the whole-design critical path. The top50 setup paths are instead dominated by HEADER and the independent ingress-count/scratch-valid cone; see [remaining-timing-cones.md](remaining-timing-cones.md).

Mapped control-set details further show:

- The inverse out_id-named CE with the inverse error-named SR controls1,313 BELs across350 slices (3.75 BELs/slice).
- The inverse error-named SR is shared by17 sets /5,944 register loads across1,758 slices.
- The cancelled-named SR is shared by112 sets /7,128 loads across1,905 slices.
- running14_out is shared by107 sets /2,218 loads, including many four-bit reconstruction residual groups. These small groups merit a packing review distinct from the wide-payload reset removal.

Netlist hierarchy names can move/merge during optimization. A one-entry coefficient stage contains only130 payload bits plus control, yet reset nets named under coefficient_boundary drive over1,000 loads elsewhere. That name does not establish that the stage owns those loads. Load-cell attribution, rather than a module-name guess, must decide the next reset edit.

## Isolated payload prototypes: keep operational behavior cycle-exact

### IDCT source_tile1280: completed separate experiment

The measured baseline [IDCT source](../../fpga/experiments/cu66-v106-idct-area/cu66_idct8x8.sv#L142) clears private source_tile1280 on reset/abort and captures it only on accepted IDLE input. This private array is not a module output. First-cycle [prefetch in IDLE](../../fpga/experiments/cu66-v106-idct-area/cu66_idct8x8.sv#L78) reads in_tile directly; subsequent first-pass reads use the stored tile. Every accepted transaction writes all1280 bits before any non-IDLE consumer uses them.

The selectedbaseline is V106 IDCT-area SHA `1ed49416dae06b727544ad1d2f96440f553cd99e5324dc895a0af5edbca5cc32`, copied under the native v69 pathname alias; the unoverridden historical v69 file has a different hash. See [baseline-origin.json](../../fpga/experiments/cu66-v107-idct-reset/baseline-origin.json).

The separate `cu66-v107-idct-reset` candidate removes only the source_tile reset/handshake assignments and gives it a separate clocked capture **whenever state==IDLE**, without reset, abort, in_valid or in_ready in that payload enable. On an accepted edge it captures exactly the old value; in every math/output state it holds. Idle/reset/cancel payload bits may differ privately and are unowned. State, out_tile, out_id, out_error, arithmetic accumulators/operands and active_cycles retain their original resets and timing. This targets both the wide SR load and the complex accepted-input CE; it is not a one-cycle-delayed reset.

Deleting a reset assignment while leaving the payload inside the existing reset/else process can retain reset-derived hold/enable logic. That alone does not demonstrate the fanout/control-set reduction sought here.

Actual qualification passed both seeds: 541,947 paired clock edges, 8,606 executions of 4,303 independently modeled Q14 golden tiles, 60 directed cancellation cases, all ten FSM-state reset/abort combinations, held outputs, invalid/zero inputs, active input noise and 2,048 idle-noise edges. Public/observation assertions remain unchanged; the new private source oracle checks all 1,280 bits when owned. [IDCT reset evidence](idct-reset.md) binds the exact source, traces and native reports. All 1,280 mapped payload R pins are now GND, and reset/abort/input-valid ports no longer reach their CEs. Their state-decoder CE and 1,280 physical loads remain. Unit control sets measured 22→11; LUTs 8,835→8,822; FFs 5,159→5,165; DSPs stay 17. This is measured unit synthesis connectivity/area, not routed parent timing.

### Dequant1027: completed independent experiment

The measured baseline [dequant](../../fpga/experiments/cu66-v69/inverse/cu66_dequant.sv#L48) clears private coefficients1024, chroma1 and scale_code2 on reset/abort. Every MULTIPLY entry follows a complete IDLE accepted-input capture. input_bad uses external input fields, not these private registers. Bad/zero shortcuts write public out_dequantized=0 and bypass MULTIPLY. Consequently the private payload may be overwritten in unowned IDLE while all public state/data/error resets remain unchanged.

Independent review covers in_valid held through reset/abort (in_ready is low), immediate retry, invalid scale/range, all-zero input, arbitrary external input changes during MULTIPLY/HOLD_TILE and held output. Private products are combinational and are consumed only in MULTIPLY; no public debug port exposes the private coefficient/parameter storage. Public inverse_dequantized reads out_dequantized, whose reset remains mandatory for exact public behavior in this experiment.

The [dequant experiment](payload-reset.md) is complete and frozen. Three actual seeds pass 121,728 public cycles, including every invalid-cycle/partial/held/reset output bit; independent trace replay and integer arithmetic checks pass. Every one of the 1,027 mapped payload FDRE reset pins is directly GND. Baseline CE fanin contains `abort_i in_valid rst`; the candidate CE is driven by registered IDLE state with no external-port fanin. The 1,027 CE pins remain. The full unit reset-register endpoints reached by either reset or abort fall 2,352→1,324, while LUTs change 1,580→1,578, FFs 2,352→2,351 and DSPs remain eight. Do not infer a unit control-set count: that report was not collected for this dequant unit. The [corrective mapped fanin query](../../experiments/python-gamebub-v107/payload-reset/native/query/20261108T053716594951Z/receipt.json) is authoritative; the first query returned empty columns for both variants and is explicitly excluded from CE evidence.

## Completed parent comparison: fewer reset consumers is not fewer global sets

The two payload variants passed [exact full canonical composition](../../experiments/python-gamebub-v107/payload-pipeline/results.json). The TABLES→payload source manifests differ only in those two production modules. At the same part, recipe and fixed 10 ns clock, the completed decoder routes report:

| Measured routed property | TABLES | TABLES + payload reset/CE changes |
| --- | ---: | ---: |
| Unique control sets | 1,137 | 1,160 |
| Slices | 13,642 | 13,075 |
| LUTs | 36,152 | 34,990 |
| FFs | 34,473 | 34,399 |
| WNS | −3.076 ns | −2.735 ns |
| TNS | −23,648.034 ns | −20,649.870 ns |
| Setup failing endpoints | 21,608 | 21,836 |
| WHS | 0.088 ns | 0.098 ns |

[TABLES reports](../../experiments/python-gamebub-v107/native/20261108T052651848340Z/receipt.json), [payload reports](../../experiments/python-gamebub-v107/native/20261108T055414848485Z/receipt.json), [actual payload control sets](../../experiments/python-gamebub-v107/native/20261108T055414848485Z/reports/route-control-sets.rpt). Hashes in both receipts match the retained reports. The 2,307 individually verified payload reset pins are removed, but the global set count **increases by 23** while occupied slices fall by 567 and WNS improves by 0.341 ns. Failing endpoint count rises. Synthesis/placement regrouping and replication mean neither fewer reset dependencies nor the IDCT unit's 22→11 result predicts the complete decoder's control-set count.

Remaining control loads are real: the payload route still reports scratch cancellation at 7,141 total / 7,128 SR loads, and the dequant state-driven payload CE net at 1,037 total / 1,027 CE loads. [Payload high-fanout report](../../experiments/python-gamebub-v107/native/20261108T055414848485Z/reports/route-high-fanout.rpt). Reset removal did not solve scratch cancellation, telemetry controls or the live owner/metadata/write-enable cones. The −2.735 ns route remains a timing failure; positive hold slack does not qualify setup or board I/O.

## Payload reset inventory: next candidates and exclusions

| Storage | Present behavior | Reset-removal assessment |
| --- | --- | --- |
| Elastic130-bit payload |No payload reset; full/fence ownership reset |Already follows the pattern; retain full/done/final-owner flushes |
| Inverse2×64×16 coefficient payload |No payload reset; bank ownership reset |Already reset-free; do not clear fewer owner bits to manufacture an improvement |
| Header caches /qbuffer /packet RAM /scale and mode backing stores |No blanket backing reset |Preserve live-init/lookup/collision semantics; TABLES addresses inference separately |
| IDCT operand_samples/basis/products |Reset, but selected use follows prefetch/MUL |Possible later phase; prove every MUL operand is freshly prefetched and DSP pipeline reset behavior stays equivalent before removing any |
| IDCT even_sum/odd_sum/dc_middle |Reset plus explicit job/group initialization |Potential internal-only candidates, but accumulation/DC transitions must be proved separately; not part of the first source_tile-only trial |
| IDCT out_tile/out_id/out_error |Public outputs reset immediately |Keep in exact-public-cycle trial; out_tile also feeds unqualified combinational output/debug views |
| Reconstruction residual1536/reference_pixels512 |Reset and fresh per-tile initialization |Potential global-reset duplication removal, but per-mode zero semantics must remain: copy/constant tiles cannot consume stale residual/reference data |
| Physical memory/reference pending owners |Survive appropriate warm cancellation/drain |Do not reset away accepted ownership; keep pending addr/epoch/generation until matching ACK |

The [reconstruction source](../../fpga/experiments/cu66-v104-control/cu66_reconstruct_stream_v91k.sv#L121) deliberately preserves ref_pending through warm reset/cancel and retires it only on a matching physical response. Global reset removal guidance does not authorize changing that protocol. Current reconstruction also zeros residual/reference data at MODE_WAIT before selecting copy/constant/residual mode; removing those per-tile semantics would be incorrect even if a global-reset assignment is redundant.

## Status that can be delayed, and control that cannot

The child pipeline has a large [telemetry reset bank](../../fpga/experiments/cu66-v106-telemetry/br88_pipeline_v91h.sv#L210):16 packet-state counters,32 scratch-state counters,4 emitter-state counters, event counts, high-water marks and first/last timestamps. The child-parent hierarchy has7,141 FFs in the utilization report, and the large cancelled SR groups include this observability. This is a concrete place to investigate local telemetry controls; it is not a license to delete counters.

Potential delayed **observability copies** include state-display/debug mirrors, counter/histogram snapshots, timestamps, maximum-occupancy reports and a display copy of error/busy. A new snapshot contract should carry frame epoch, valid/completion state and a defined capture edge. It may be one cycle delayed or serialized if explicitly versioned. Preserve the internal operational signals and exact original event definitions.

Do **not** delay the operational busy/start_ready/cache_ready, in/out ready-valid, error/kill/cancel, bank-state/full flags, done fences or physical pending/ACK owner. For example the [top](../../fpga/experiments/cu66-v107-elastic/cs88_pipeline_v91k.sv#L207) uses inverse/reconstruction errors to abort the producer and block publication; a delayed control copy could admit extra traffic or lose ownership. A display-only copy is a different signal and must not feed that logic.

A registered output snapshot alone leaves the original counter-bank reset and CE fanout intact. To reduce that load, a separate telemetry experiment should register the **telemetry event/time/clear bundle together**, distribute identical-latency local clear registers to logical counter banks and define the output snapshot at that delayed event boundary. Delaying clear alone while consuming current events corrupts reset/start/final-edge counts and timestamps. First-event comparisons and timestamp timebase must remain aligned. The existing V106 treatment explicitly counts the store_done observation edge and preserves parent totals across an internal child cancel; keep those definitions in the new epoch/snapshot oracle.

If live52-way histogram readout is replaced by a serialized snapshot, RAM-backed histograms with epoch tags become possible, but they need same-bin consecutive-cycle forwarding, exact64-bit wrap and reset/start/abort generation handling. They cannot silently replace the current parallel live outputs. This is a later separate interface/resource experiment, not the small payload prototype.

## Fanout localization versus tiny CE cleanup

For critical high-fanout operational control, first reduce unnecessary payload loads, then inspect the remaining mapped driver/load groups. If replication is justified, use equivalent **same-cycle** local drivers fed from the same state/event; do not insert an extra operational reset/abort cycle. A balanced local registered tree is safe only when the protocol already permits that latency or the complete control/data bundle is retimed together. Keep CDC synchronizers protected and do not duplicate their stages.

For tiny control sets, inspect actual four-/six-/eight-bit groups such as reconstruction residual slices and state-counter carry enables. Candidate experiments include local D-input hold muxes/control-set remapping on named low-fanout groups, or sharing compatible update controls. A syntactic `counter<=counter+event` rewrite may be re-extracted into the same CE and is not measured evidence. Moving CE logic to D can consume LUTs and lengthen the data path; it is not automatically desirable at the earlier elastic snapshot's 75.12% LUT and 96.45% slice occupancy (later snapshots differ). Do not apply global MAX_FANOUT or blanket KEEP/DONT_TOUCH to every control.

A follow-up comparison must separately report: critical-net SR/CE/data fanout and delay; load-cell ownership; unique control-set histogram and unused locations; occupied slices/LUT/FF/DSP/BRAM; setup/hold/pulse and endpoint counts. A reduced set count without better timing/fit is not success, and a lower fanout on a noncritical net does not establish100 MHz closure.

## Completed control precomputation and deferred work

The [META flag experiment](metadata-control-next.md) registers only pure tuple geometry/domain predicates alongside the already existing coefficient token; live fill index, exact owner equality, done fence and token exhaustion remain at acceptance. Focused and [full canonical](../../experiments/python-gamebub-v107/meta-pipeline/results.json) checks preserve the original public schedule. Its completed META7 route also includes the local ×43 guard variant and reports WNS −3.146 ns, 25,263 setup failing endpoints, 1,222 control sets and 13,429 slices. [META7 timing](../../experiments/python-gamebub-v107/native/20261108T062626721920Z/reports/route-timing-summary.rpt), [capacity](../../experiments/python-gamebub-v107/native/20261108T062626721920Z/reports/route-capacity.rpt). This is a failing composite trial, not an isolated timing win for the flags.

[Count-prefix precomputation](plan-prefix.md) uses existing header fetch time to cache only modulo-32 count-derived sums. Complete four-body synchronous/legacy pairs and actual capture/owner/cancel/retry tests pass without extra public cycles; complete pixel composition and new native timing remain separate. The subsequent count-threshold candidate is still undergoing actual qualification at this review; its integer model and source review are not RTL or timing PASS.

Telemetry snapshots, event/time/clear retiming, histogram RAMs, local operational-driver replication, CE-to-D remapping, and further operand/accumulator/output reset changes in the inventory above are **deferred ideas**. No such interface change, blanket reset tree, global fanout attribute or control-set remapping is claimed as implemented. An observation copy can be delayed only after its consumers are shown not to need the original next-cycle value; current public cycle-exact outputs remain unchanged.

## Selection and safety gates

1. Keep completed proof/source hashes and failed or scheduling-cancelled attempts intact. HEADER-only and guard-only scheduling cancellations without checkpoints/reports supply no timing result or tool-hang diagnosis.
2. Retain the completed dequant/IDCT private ownership and exact public-cycle proofs. Do not remove reset from state, public outputs, outstanding physical owners or required per-mode initialization by analogy.
3. Compose only passing candidates and retain complete same-seed canonical bytes, events, counters, cancellation and owner obligations. Delayed snapshots would require their own explicit API and final-event accounting proof.
4. Compare mapped SR/CE dependencies, actual control-set histograms, fanout/load ownership, fit and complete routed setup/hold/pulse results. A local unit reduction or source declaration does not establish global timing closure. Count-threshold and any further native candidate need their own completed qualifications.

TABLES' `prepare_block/R` initialization on metadata acceptance is required first-tile state initialization. It is not redundant blanket reset. Likewise, status-looking error/busy/done nets can drive abort, write-enable and publication decisions on the next edge. Keep those operational consumers immediate; do not hide their critical paths with multicycle exceptions or pipeline only a status bit.

# Next control cut: tuple checks at the existing coefficient register

This historical proposal was implemented as [META flags](meta-flags.md) and passed unit/full canonical qualification. Its combined route was −3.146 ns and remains unselected. The final frontier is recorded in [the comparison](vendor-comparison.md); the proposal below preserves the original rationale.

This is a read-only source/report analysis and a proposed follow-up. No RTL, runner, qualified receipt or source map was changed, and no compile, simulation or vendor job was launched for this plan. Static tuple validation can be registered alongside the existing coefficient token without adding a public cycle. Checks involving the inverse's current fill position, owner or token counter must remain at the downstream acceptance edge. The plan is not timing-qualified.

## Actual routed evidence and exact tuple bit

The completed TABLES component route still fails the fixed 10 ns requirement. Its [worst setup path](../../experiments/python-gamebub-v107/native/20261108T052651848340Z/reports/route-setup-paths.rpt:15) is:

| Property | Measured value |
| --- | --- |
| Source | `coefficient_boundary/payload_reg[43]_rep__1/C` |
| Destination | `transform/child_epochs_reg_0_1_25_25/DP/WE` |
| Slack | −3.076 ns |
| Data delay | 12.459 ns: 2.831 ns logic, 9.628 ns route |
| Levels | 13: one CARRY4, two LUT2, one LUT5, seven LUT6, one MUXF7, one MUXF8 |
| Initial data-net fanout | 64 |
| Final WE-net fanout | 152 |

The report SHA-256 is `fdbb4f493d1418fe69b3310bfe3a574caf65216ede60810a8177caa93c395adc`, matching both the repository report and external build `v107-tables-20261108T052651767313Z-4d6323/results/route-setup-paths.rpt`. Its actual path passes through `transform/input_metadata_bad1`, error/reason logic and the owner-write enable. Synthesis-generated names under `coefficient_boundary` do not establish RTL ownership of the entire cone.

The [boundary concatenation](../../fpga/experiments/cu66-v107-elastic/cu66_coefficient_elastic.sv:36) gives these exact payload positions:

| Field | Bits |
| --- | --- |
| value | 15:0 |
| coefficient index | 21:16 |
| qcell | 32:22 |
| tile | 45:33 |
| block | 61:46 |
| qscale | 63:62 |
| plane | 65:64 |
| child epoch | 97:66 |
| frame epoch | 129:98 |

Thus payload bit 43 is tile bit 10, not coefficient-value bit 10. The measured path is a tuple-metadata-to-owner-WE path after the elastic cut.

Pinned production sources are the [boundary](../../fpga/experiments/cu66-v107-elastic/cu66_coefficient_elastic.sv), SHA `28de630dc9266ff23302ecf96155e7b4135ee26b6140682483c219791b9b61e9`; [top wiring](../../fpga/experiments/cu66-v107-elastic/cs88_pipeline_v91k.sv:214), SHA `d9441f5a4600daf48cbb201cf731c42d724bf9f0c5609bf8b9249d683cf5e57d`; and selected [inverse](../../fpga/experiments/cu66-v107-value-check/cu66_inverse_stream_v91j.sv:927), SHA `c93bec92283985070c0ef343be3377d44ffa04c513e37232d8962344fb6180c9`. The TABLES native `inputs.json` selects these sources. The ongoing payload-reset experiment is a separate source map; this analysis does not claim its future worst path.

## Pure tuple predicates versus live state

The current inverse constructs `input_metadata_bad` at lines 927–931 and prioritizes `input_fault` at lines 932–940.

| Predicate | Dependencies | Proposed location |
| --- | --- | --- |
| `plane>2` | tuple plane only | registered static-metadata flag |
| `tile >= (plane==0 ? 5400 : 1350)` | tuple plane/tile only | same static-metadata flag |
| `qcell != quant_cell(plane,tile)` | tuple plane/tile/qcell only | same static-metadata flag |
| `qscale==3` | tuple scale only | registered payload-domain flag |
| value outside inclusive −2048…2048 | tuple signed value only | same payload-domain flag |
| `index != fill_index` | tuple plus current inverse fill index | downstream, unchanged |
| FILL owner mismatch | current fill bank/state and seven stored owner fields | downstream, unchanged |
| `fill_index==0 && next_token==0xffffffff` | live index/token counter | downstream, unchanged |
| `input_done && fill_index!=0` | ordered done fence and live partial tile | downstream, unchanged |
| running, existing error, kill, readiness, finished input | operational state | downstream, unchanged |
| dequant/IDCT errors and IDs | live arithmetic result owners | downstream, unchanged |

The FILL comparison covers the full 108-bit owner projection: frame epoch, child epoch, plane, scale, block, tile and qcell. It is checked only when `bank_state[fill_bank]==FILL`; stale owner RAM contents in a FREE bank must remain irrelevant. The inverse has no separate pure bound check on block or epoch. Do not add one or assume that a first token's epoch equals some external frame state. Coefficient index has a six-bit type, but whether it is the expected index is a live comparison.

A tuple may wait in the boundary while a bank drains. During simultaneous downstream consumption and upstream replacement, the new tuple's later expected index/owner is not necessarily the inverse's pre-edge state. Capturing a live mismatch at upstream acceptance would therefore be wrong without a separate predictive-state architecture. Owner hashes or truncated comparisons would also weaken the current exact check.

## Exact helper and malformed domains

The selected `quant_cell` is the existing combinational LUT helper at inverse lines 65–916. Its complete binary domain is plane 0…3 and tile 0…8191. For plane zero it returns the low eleven bits of `((tile/90)/2)*45 + (tile%90)/2`; other planes, including invalid plane three, return `tile[10:0]`. The valid geometry is Y tiles 0…5399 and chroma tiles 0…1349. Full-domain Y helper values can reach 2069 before eleven-bit truncation; the 44 wrapped inputs remain defined even though they are outside valid geometry.

The inherited [exhaustive helper receipt](../../experiments/python-gamebub-v106/math/attempts/20261108T004859781567Z/results.json), SHA `e69f52a8b6fdc5704a28e22cca834cfd882e12b2a8af7ed18a97c617a55d2a4b`, checks all 32,768 plane/tile combinations against the independent geometry oracle. A literal source comparison confirms that the selected helper is byte-identical to the qualified V106 LUT helper; its extracted function SHA-256 is `ea6611d2d9e1cadd2d0528a8882ba8d50bbced189443f7c606b9d16cf215e7bb`. That evidence describes the existing helper, not a tested new sideband. A follow-up should move/copy the exact helper expression, retain all full-width plane/tile/qcell checks and independently verify the new composite flag across malformed domains. It must not treat out-of-geometry values as unspecified or trust the producer to supply matching metadata.

The value predicate is the already qualified exact bit test: valid when `value[15:11]==0`, or `value[15:11]==5'b11111`, or `value==16'h0800`. Scale three remains invalid independently of value.

## Proposed two-bit registered control sideband

At precisely the boundary's existing `in_valid && in_ready` capture, store the complete unchanged 130-bit tuple and two bits:

- `tuple_metadata_bad`: the OR of the three pure geometry/qcell predicates.
- `tuple_domain_bad`: invalid scale OR out-of-range signed value.

Use the same clock, capture enable and occupancy ownership as the payload. The extra two private data bits need no reset; clearing existing `full`/fence ownership already makes them unobservable. Keep them stable with the payload under backpressure. Identical capture control can share the payload control set; a separate tiny reset/enable domain is unnecessary. Expected storage cost is two bits, not another queue entry or public cycle.

Route these registered flags through explicit internal top/stage/inverse ports. Preserve external top ports and raw producer debug outputs. The inverse combines static metadata with the **live** FILL-owner comparison, then applies the original priority. The expensive helper should no longer be synthesized on the registered tuple-to-WE path; an independent simulation assertion should still compare the consumed flags against the original pure expressions. Do not retain a parallel synthesized helper as another WE qualifier, which would restore the measured cone.

Do not generate one preselected error code. The exact input priority must stay:

1. Done fence with nonzero partial fill → error 4, even without an input handshake.
2. On `in_valid && in_ready`, index mismatch → error 1.
3. Static metadata bad **or live owner mismatch** → error 2.
4. Scale/value domain bad → error 3.
5. First coefficient with exhausted token counter → error 7.

Reset/start/cancel retain their outer priority, followed by the existing `error==0 && running` gate. Any input fault prevents the normal owner/bank/math updates on that edge. It outranks arithmetic faults 5/6 because those occur inside the later `else` math case. Conversely, a later arithmetic fault may still coincide with the separate coefficient write when `input_fault==0`; preserve the original source ordering and write guards. Counters, including accepted inputs on an offending handshake, must remain exact.

The flags must never gate upstream `in_ready`, downstream `out_valid`, kill, error publication or the done fence early. Invalid tokens remain real queued tokens and produce their original fault only at the original inverse acceptance edge. A token flushed before that edge is discarded without publishing its cached fault. Existing reset/start/cancel, sticky-error retry, final-offer ownership and done-after-drain logic remain immediate and unchanged. This is preparatory control computation within an already existing stage, not a delayed operational action.

## Required qualification before selection

No implementation or new test was run for this plan. A future isolated candidate needs all of the following:

- Independently check the exact helper for all 4×8192 plane/tile inputs, static metadata flags for all 4×8192×2048 plane/tile/qcell combinations, and payload-domain flags for all 4×65536 scale/value combinations. Include invalid plane three, geometry edges, qcell 1349/1350/2047, wrapped helper results, and value −2049/−2048/2048/2049.
- Extend the independent boundary scoreboard with both expected flags, preserving the full 130-bit tuple and UP/DOWN/DISCARD conservation. Check empty capture, simultaneous pop/replacement, held valid output, arbitrary invalid-input noise, valid offers stalled before capture, final offered token with early/pulsed done, and reset/start/cancel before and after capture. Flags and payload must share exactly one owner and flush together.
- Pair the complete old boundary+inverse against the candidate with cycle-exact public/counter/state checks. Exercise both banks, fill indices 0…63, all FILL-owner fields changed independently, FREE stale metadata, token exhaustion and simultaneous fault combinations. Specifically test done4 versus every fault, index1 versus metadata/domain errors, owner2 versus domain3, and input faults versus arithmetic5/6. Prepared internal states must initialize sideband ownership explicitly; do not pretend arbitrary unreachable flags are valid.
- Retain every existing canonical golden, ownership, held-data, cancellation and 151-check pipeline obligation. This proposal adds no cycles, so require exact same-seed case cycles, ordered events, canonical bytes, errors and counters against the qualified control, rather than weakening the checker for latency.
- Measure synthesis, place and route at the same 10 ns constraint and inspect both new halves: producer `mapped_tile`/`mapped_cell`/plane registers to the sideband D pins, and registered flags plus live fill/owner logic to bank/owner WE. Inspect all worst paths, fanout, control sets and placement pressure; moving the critical path upstream is possible.

The [producer outputs](../../fpga/experiments/cu66-v106-producer-cache/cs88_coefficients_v91k.sv:1058) already expose registered mapped tile/cell/scale, so there is an identifiable upstream boundary. However, the exact LUT helper plus qcell comparison may itself be slow before the new flags. Live 108-bit owner equality and broad fault-to-WE fanout also remain downstream. The measured original path is 77.3% routing delay. Two flags therefore offer a concrete architectural cut but no promised 100 MHz gain, route success, or frame-rate improvement.

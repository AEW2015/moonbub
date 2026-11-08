# AMD guidance applied to reset, fanout and status timing

Reviewed 2026-11-08 during V107 against completed source-bound tests and native reports. Remove unnecessary reset/handshake dependencies from private payloads only after proving overwrite-before-use. Precompute stable tuple/count facts in existing stages; keep next-cycle acceptance, fault, cancellation and owner decisions immediate. Delayed diagnostic snapshots remain a separate, unimplemented interface proposal. The completed decoder routes cited below still fail the fixed 10 ns target.

## Guidance relevant to this Artix-7

AMD recommends deciding reset requirements per block, retaining resets for necessary control state while avoiding unnecessary datapath reset. This can reduce reset routing and allow better RAM/SRL/DSP mapping. Configuration initialization is not a substitute for runtime abort/retry/ownership behavior. [UG949: when and where to use a reset](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/When-and-Where-to-Use-a-Reset), [reset mapping effects](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Resets).

Removing an assignment from a reset branch can leave the register conditionally enabled by reset. Put payload storage in a separate clocked process with its intended write enable, then prove that invalid data cannot affect behavior. Reset-before-enable coding matches the primitive precedence where a reset is required. [Reset elimination coding pitfall](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Issues-When-Trying-to-Eliminate-Reset-in-HDL-Code), [reset/enable precedence](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Reset-and-Clock-Enable-Precedence).

A 7-series slice shares clock, enable and set/reset control among its registers. Distinct small enables/resets can therefore constrain packing even when the total FF count is modest. Reducing control sets is a different task from reducing one large fanout net. [UG474: control signals](https://docs.amd.com/r/en-US/ug474_7Series_CLB/Control-Signals), [UG949: reducing control sets](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Reducing-Control-Sets).

First eliminate unnecessary consumers of a high-fanout control. Then consider geographically local registered drivers or placement-aware physical replication. AMD advises against indiscriminate global `MAX_FANOUT` settings and against replicating CDC synchronizer registers; an additional ordinary register after a synchronizer has a different role. Use `KEEP` rather than freezing an entire structure with `DONT_TOUCH` when preservation is actually needed, and measure the outcome. [Reduce loads](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Reduce-Loads-in-Portions-of-the-Design-That-Do-Not-Require-It), [replicate drivers](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Replicate-High-Fanout-Net-Drivers).

Pipelining can shorten a long logic cone, but its added latency must be carried through the complete transaction. A delayed enable may sometimes avoid replicating a wide payload bus, provided the data remains stable for the full required interval. This is not blanket permission for multicycle constraints on ready/valid, abort or publication. [Pipelining considerations](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Pipelining-Considerations), [balance latency](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Balance-Latency).

## Historical elastic measurements that motivated the work

The following values are from the **elastic native routed report**, not estimates of a future variant:

| Net / condition | Measured evidence | Investigation |
| --- | --- | --- |
| Scratch `cancelled` | 7,141 loads, including 7,128 set/reset loads; worst reported slack −1.202 ns | Remove cancellation from payloads protected by invalid ownership; keep drain/outstanding-response control immediate. |
| Inverse `error_reg[1]` | 6,035 loads; worst reported slack −2.827 ns | Separate prompt fault/valid handling from delayed diagnostic status; inspect wide arithmetic/output-buffer reset cones. |
| `coefficient_boundary/running14_out` | 2,242 loads, 2,218 set/reset loads; worst reported slack −2.015 ns | Trace flattened logic back to actual producer processes before assuming the small tuple stage is responsible. |
| IDCT intermediate enable | 1,536 CE loads; worst reported slack −0.711 ns | Check local write grouping and shared enables; intermediate payload already lacks an explicit bulk reset. |
| Whole component packing | 1,201 control sets, 15,287/15,850 slices used, 47,624 LUTs / 37,218 FFs | Compare control-set histograms and routed slice occupancy, not just FF or LUT count. |

Source report: [high fanout](../../experiments/python-gamebub-v107/native/20261108T042607353046Z/reports/route-high-fanout.rpt), [control sets](../../experiments/python-gamebub-v107/native/20261108T042607353046Z/reports/route-control-sets.rpt), [capacity](../../experiments/python-gamebub-v107/native/20261108T042607353046Z/reports/route-capacity.rpt). These reports retain source/recipe/receipt hashes in the independent audit. Their net slacks cover the report’s observed loads; they are not proof every endpoint of a proposed cut will improve.

The 130-bit coefficient tuple payload and both inverse coefficient banks already avoid explicit payload resets. Repeating that optimization there would remove no reset. State/valid/occupied/done/owner controls continue to reset. The table above describes the earlier elastic route; later TABLES/payload/META snapshots have different occupancy and paths and must not inherit those figures as current measurements.

## Completed reset and control experiments

[Dequant payload reset/CE removal](payload-reset.md) and [IDCT source-payload reset/CE removal](idct-reset.md) are completed isolated experiments, with exact public-cycle tests, independent numeric/owner oracles, and per-bit mapped connectivity checks. Both now capture private payload whenever the registered state is IDLE; reset, abort and input-valid no longer enter those payload enables. Public data, errors, state and ownership resets remain unchanged, including invalid-cycle output/debug values. Idle captures may increase switching; no power benefit is claimed.

| Measured OOC unit property | Dequant original → candidate | IDCT original → candidate |
| --- | --- | --- |
| Payload FDREs | 1,027 → 1,027 | 1,280 → 1,280 |
| Payload reset pins directly tied to GND | 0 → 1,027 | 0 → 1,280 |
| Reset/abort/input-valid ports reaching payload CE | present → none | present → none |
| Remaining payload CE | registered IDLE state, 1,027 loads | local registered-state decoder, 1,280 loads |
| Reset-register endpoints reached from each reset/abort port | 2,352 → 1,324 | 3,604 → 2,321 |
| Unique control sets | no separate unit report; do not infer a count | 22 → 11 |
| LUTs / FFs / DSPs | 1,580 / 2,352 / 8 → 1,578 / 2,351 / 8 | 8,835 / 5,159 / 17 → 8,822 / 5,165 / 17 |

The exact per-bit proof covers **2,307 payload reset pins**, not removal of 2,307 FFs or all CE loads. Whole-netlist endpoint/FF deltas also include synthesis optimization/replication. Dequant's first fanin query produced empty port columns for both designs; the [corrective query](../../experiments/python-gamebub-v107/payload-reset/native/query/20261108T053716594951Z/receipt.json) uses actual `CLASS==port` startpoints and positive baseline checks. [IDCT's native summary](../../experiments/python-gamebub-v107/idct-reset/native-summary.json) uses the same meaningful checks. These are OOC synthesis measurements; their synthetic clock and missing parent clock-source/I/O constraints do not prove routed parent frequency.

The composed payload variants also passed [full canonical equality](../../experiments/python-gamebub-v107/payload-pipeline/results.json). The completed, matched fixed-10-ns decoder routes show why reset fanout and control-set count must be measured separately:

| Completed component snapshot | Control sets | Slices | LUTs / FFs | Routed WNS | Setup failing endpoints |
| --- | ---: | ---: | --- | ---: | ---: |
| TABLES, before private payload changes | 1,137 | 13,642 | 36,152 / 34,473 | −3.076 ns | 21,608 |
| TABLES + dequant/IDCT payload changes | 1,160 | 13,075 | 34,990 / 34,399 | −2.735 ns | 21,836 |
| META7, additionally local ×43 guards and registered tuple flags | 1,222 | 13,429 | 35,759 / 34,438 | −3.146 ns | 25,263 |

Sources: [TABLES capacity](../../experiments/python-gamebub-v107/native/20261108T052651848340Z/reports/route-capacity.rpt), [payload capacity/control sets](../../experiments/python-gamebub-v107/native/20261108T055414848485Z/reports/route-capacity.rpt), [payload timing](../../experiments/python-gamebub-v107/native/20261108T055414848485Z/reports/route-timing-summary.rpt), [META7 capacity](../../experiments/python-gamebub-v107/native/20261108T062626721920Z/reports/route-capacity.rpt), [META7 timing](../../experiments/python-gamebub-v107/native/20261108T062626721920Z/reports/route-timing-summary.rpt). Source-manifest comparison confirms TABLES→payload changes exactly the two private-payload modules. Its WNS improves by 0.341 ns and occupied slices fall, while global control sets and failing-endpoint count rise. The IDCT unit's lower set count is therefore not a whole-decoder claim. META7 combines multiple changes and does not isolate a causal gain from its two flags. None of these routes closes 100 MHz or qualifies board I/O.

## Pipeline preparatory work, not next-cycle actions

[Registered metadata/domain flags](metadata-control-next.md) have actual focused and [full canonical](../../experiments/python-gamebub-v107/meta-pipeline/results.json) proof. They travel with the existing 130-bit coefficient token; the original done/index/owner/domain/token fault priority and immediate operational controls remain exact. The META7 route above remains failing. [Count-only aligned prefixes](plan-prefix.md) have actual complete four-body public-cycle and capture/ownership proof, using existing header-fetch edges without an added public cycle; full pixel composition/native timing are separate gates. The newer count-threshold pipeline remains pending actual qualification and has no claimed timing result.

A signal is eligible for delay only after its **consumers and required sampling edge** are identified. A status-looking name may drive cancellation or a RAM write enable. Do not register it merely because it is called error, busy, done, status or debug. If an operational decision is required on the next edge, preserve that edge or retime its entire transaction with an explicit new contract. A timing exception cannot supply the missing protocol proof.

## Which status can tolerate delay

Candidate delayed interfaces are host-polled performance counters, debug state snapshots, FIFO high-water marks and diagnostic history. Implement them as an explicitly versioned snapshot interface with a capture request, coherent payload, epoch/sequence tag and valid response. Local functional counters remain exact; a terminal snapshot must include the last accepted event. An observational output today may have cycle-exact tests or consumers, so document any changed status contract rather than silently delaying it.

Keep ready/valid acceptance, FIFO full/empty, outstanding memory ownership, cancellation/drain, sticky fault suppression and publication checks on their required cycle. Do not delay one bit of a control/data tuple independently. A local reset tree or registered cancellation is a protocol change unless all endpoints are quiesced and release/flush ordering is proved.

## Qualification for a useful optimization

For each isolated reset/control experiment, identify every affected register and all read sites, prove overwrite-before-read or validity masking, retain reset for ownership/control, and exercise every reset/abort state plus retry, held output and stale memory response. Then run the complete canonical/golden workload. Compare actual routed WNS/TNS, failing endpoints, high-fanout loads, control sets, slices, LUTs/FFs, BRAM/SRL/DSP mapping and runtime against the exact same source/clock baseline.

A delayed-status interface is a separate API change. A physical replication or control-remapping trial belongs in the bounded strategy matrix with its own directive and source/constraint hashes. Neither may be counted as a timing fix until a completed routed comparison supports it.

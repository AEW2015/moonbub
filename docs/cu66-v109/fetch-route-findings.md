# FETCH final route: distributed ownership and cancellation now limit setup

The final routed FETCH trial does **not** meet 100 MHz: WNS −1.635 ns, TNS −8,267.052 ns and 13,122 setup-failing endpoints. Hold is +0.044 ns with zero hold failures; pulse width is +3.750 ns with zero pulse failures. Routing is complete with zero errors, and the reported internal clock/loop/unconstrained-endpoint checks are zero. The component still has the separately declared OOC I/O timing scope. This analysis uses final routed trial `20261108T121030620057Z`, not its synthesis estimate. It changes no RTL, constraints, frozen methodology note or tool recipe.

The primary cone is **quiescence/readiness through accepted-start and cancellation into an owned coefficient-write fence**. It is not coefficient arithmetic, and the error-named intermediate LUTs do not make it a path launched by an error register. A second near-worst cone is genuine fault-acknowledgement distribution into Rice storage control. Reducing wide status decoding did not eliminate either distributed ownership network.

## Actual worst full path

The launch pin is `coefficients/child/scratch/state_reg[0]/Q` (the report's Source field names its `/C` clock pin). The endpoint is `transform/coefficient_banks[1].words[49].value_reg[2]/CE`. Data delay is **11.346 ns**, consisting of **1.758 ns logic and 9.588 ns routing (84.506%)**, across **ten LUT levels**: one LUT3, four LUT5 and five LUT6. The requirement is 10.000 ns, skew −0.049 ns and uncertainty 0.035 ns.

The retained path's routed segments are:

| Net on the reported path | Fanout | Routed segment delay |
| --- | ---: | ---: |
| `scratch/state_reg[0]_4` | 37 | 1.071 ns |
| `scratch/child_busy` | 7 | 1.047 ns |
| `coefficient_boundary/start_ready_0` | 3 | 0.184 ns |
| `coefficients/final_wait_reg_0` | 8 | 0.647 ns |
| `transform/inverse_cancel` | 9 | 0.747 ns |
| `transform/coefficient_ready_INST_0_i_4_n_0` | 6 | 1.044 ns |
| `coefficient_boundary/error[2]_i_6` | 72 | 1.183 ns |
| `transform/error_reg[2]_1` | 1 | 0.151 ns |
| `transform/error[2]_i_6_n_0` | 8 | 0.517 ns |
| `coefficient_banks[1].words[0].value[15]_i_2_n_0` | 63 | 1.363 ns |
| `coefficient_banks[1].words[49].value0` | 16 | 1.632 ns |

The physical endpoints span scratch `SLICE_X60Y124` to coefficient storage `SLICE_X21Y19`. Several low/moderate-fanout nets also have more than one nanosecond of routing; the problem is distributed control/locality as well as fanout count. Names are optimized aliases: this table is the actual netlist traversal, not a claim that each LUT corresponds uniquely to one source expression.

## Source-bound control chain

All 18 current origins and their retained source snapshots were SHA-checked against this exact receipt: seventeen SV bodies and one header. In particular the scratch body here is **V108 capacity**, not the bank/prefetch experiment; the ingress is **V109 FETCH**; inverse/top/producer are the four V109 fault bodies. The IDCT historical v69 alias still selects the V108 output-mask body.

| Actual source | Source behavior on the dependency chain |
| --- | --- |
| [V108 scratch](../../fpga/experiments/cu66-v108-capacity/packed_scratch_v91g2.sv:237) | `busy = state != IDLE && state != FINISHED && state != FAILED`; DRAIN remains busy until the physical owner retires. |
| [V108 child pipeline](../../fpga/experiments/cu66-v108-capacity/br88_pipeline_v91h.sv:128) | `busy = running || store_busy`; `draining = store_busy && !running`. |
| [V109 coefficient producer](../../fpga/experiments/cu66-v109-fault/cs88_coefficients_v91k.sv:1047) | `start_ready` requires no running frame, child busy/drain or partial cache load, and no reset/abort; accepted start uses this readiness. |
| [V109 full top](../../fpga/experiments/cu66-v109-fault/cs88_pipeline_v91k.sv:196) | Top start readiness additionally requires arithmetic/reconstruction idle and an empty coefficient stage; `accepted_start = start && start_ready`. Sticky peer faults cancel the inverse only when a replacement start has not been accepted. |
| [Existing coefficient boundary](../../fpga/experiments/cu66-v107-meta-flags/cu66_coefficient_elastic.sv:885) | Reset/start/cancel immediately fence output valid. The final token is retained through `done_pending`, `final_wait` and `full`; `output_done` cannot overtake that owner. |
| [V109 inverse](../../fpga/experiments/cu66-v109-fault/cu66_inverse_stream_v91j.sv:925) | Local kill includes reset/start/cancel/fault. `in_ready`, partial-final-input handling and metadata/domain/index/token checks feed `input_fault`. |
| [V109 coefficient words](../../fpga/experiments/cu66-v109-fault/cu66_inverse_stream_v91j.sv:968) | Each write requires no kill/fault, running, `input_fault == 0`, a valid accepted token, and the exact bank/index. The packed coefficient vectors remain publicly visible through debug. |

Thus scratch's current busy/decode influences restart permission; current restart permission influences start/cancel fencing; that fencing influences whether a token is currently offered/accepted and whether the exact coefficient word may be written. The timing path is a **ready/start/cancel/validation control cone**, rather than a new eight-bit error reduction. Its source is not a current dense coefficient value. This does not justify removing the acceptance fence: a replacement start, simultaneous fault and final token have deliberately different priorities.

## Remaining top-fifty families

| Launch family | Paths among 50 | Meaning |
| --- | ---: | --- |
| Scratch state | 26 | Nineteen coefficient-word CEs, six ingress fetch-index CEs, one reconstruction residual D. |
| `inverse_fault_ack` | 6 | Rice reservoir CEs. |
| Scratch `read_segment` | 2 | Scratch state D. |
| Dequantizer group index | 15 | Dequantized payload D. |
| Admission tile | 1 | Admission visibility D. |

No top-fifty path **launches** from `fetch_index_reg` or `fetch_return_reg`; the earlier initial-A header address/commit path and initial-B request/address/error path are absent from this top-fifty list. Fetch-index registers still occur as six **destinations** of scratch-state control. This is evidence of a changed worst-path distribution, not proof that every ingress address/bounds endpoint now passes or that FETCH independently improves WNS. FETCH's WNS is 0.046 ns worse than initial fault A, while its TNS and failing-endpoint count improve; the paired source/placement result must be reported as measured.

The second-worst path is `inverse_fault_ack_reg/Q` to Rice `reservoir_reg[18]/CE`, **−1.599 ns**, fourteen LUT levels, 11.310 ns data delay comprising 2.254 ns logic and 9.056 ns routing (80.071%). The path passes through `base_abort` (fanout 27), an ingress parser control net (376), another global control (272), `packet_abort` (7), and later parser control nets (1,031 and 249), before local ready/consume/storage enable. This is the surviving acknowledged-fault flush network. The already co-registered `fault_o` bits are exact, but their parent acknowledgement/start distribution remains in the operational path. The unselected availability-mask Rice contingency targets a different prefix cone and does not structurally remove this acknowledgement dependency.

## Most specific next investigation

The narrowest directly source-bound candidate for the **current primary launch** is a redundant, local **scratch busy/quiescent predicate captured on the same edge as the actual next scratch state**. Pair every original state assignment with the predicate for that exact next state, retain last-assignment priority, and preserve DRAIN, error, abort, warm-reset, final-response and FINISHED behavior. Assert the new predicate equals the original busy expression on every public cycle. Then propagate only an exactly equivalent local readiness/owner predicate where that avoids repeated decode. This is not permission to register the existing combinational `busy` one edge later. It removes a real starting decode from the reported cone, but one removed LUT does not by itself establish recovery of 1.635 ns or improved placement.

For the independent acknowledgement cone, a same-edge **owned, unacknowledged fault** bit would need the exact `fault_next` and acknowledgement-next priorities, including accepted retry and simultaneous faults. Sampling the already registered error/fault into a new flush register would delay cancellation and fail the contract. Any such proposal must first prove equality to the present `fault && !ack` expression on every cycle and preserve immediate public abort/input/output fences.

If local equivalent predicates are insufficient, the architectural candidate is an explicitly owned elastic handoff and **final-drain fence**. The existing one-slot boundary already tracks the final stalled offer; merely inserting another register can keep the same global start/cancel dependency and can move done ahead of the final coefficient. A new stage must own the complete tuple and its static fault sidebands, retain current-cycle public cancellation fencing, account for every queued/in-flight owner before start-ready/done, and use a latency-aware independent oracle if public timing changes. A private coefficient prewrite is not a shortcut: unmasked debug payloads and same-edge malformed-input/late-arithmetic-failure behavior are part of the existing observable contract. No pipeline or status delay is proposed as an exact drop-in fix.

## Bank plus REQUEST: explicit judgment

The bank cut targets a **real remaining secondary dependency** here: `read_segment_reg[1]` to scratch state has −1.580 ns and −1.553 ns slack, fourteen levels and approximately 73% routing. Its captured one-hot owner removes binary bank selection from the word/position/live-tag cone. It is therefore not merely an arbitrary placement experiment for those two paths.

It does **not** remove the current primary dependency. The bank design preserves the same scratch busy truth table and top accepted-start/cancel semantics. REQUEST precomputes owned request address/bounds at existing earlier edges and targets initial B's measured ingress bounds/error/RAM-enable cone; it likewise leaves scratch quiescence, coefficient validation and fault acknowledgement unchanged. A bank+REQUEST composition may improve those specific secondary cones or aggregate timing, but claiming it closes the current scratch-state-to-coefficient-CE or ack-to-Rice path would depend on favorable physical perturbation, not a demonstrated removed logical dependency. The initial combined B result already shows that lower TNS/fewer failures need not improve worst slack. New composition requires complete canonical qualification and native measurement before any closure claim.

The four-trial native budget is committed: two initial trials, FETCH adaptive trial 1 and REQUEST adaptive trial 2. REQUEST remains active at the time of this analysis. Any further native composition, fanout experiment or control redesign needs a separately justified budget extension; there is no silent fifth trial.

## Pinned evidence

- [receipt.json](../../experiments/python-gamebub-v109/native/20261108T121030620057Z/receipt.json), SHA-256 `d2983a44f4a464803e1552ab70a8925090e41fd58164bca713ef6b3d0a2f8347`.
- [reports/route-setup-paths.rpt](../../experiments/python-gamebub-v109/native/20261108T121030620057Z/reports/route-setup-paths.rpt), SHA-256 `483859825ba170fc84a156b71334bdf35eaa5ece8c4f6a043fef72c7dbb94be6`.
- [reports/route-timing-summary.rpt](../../experiments/python-gamebub-v109/native/20261108T121030620057Z/reports/route-timing-summary.rpt), SHA-256 `d00ea92bf33ccbb58c599bb8e196b1b437e4647d69ab5d76854da7a6c4d74f94`.
- [reports/route-check-timing.rpt](../../experiments/python-gamebub-v109/native/20261108T121030620057Z/reports/route-check-timing.rpt), SHA-256 `8a5ad6d1675490c95b1c0acfcf4ac3447a64c5f672d652a4eb4a8b6ada077e48`.
- [reports/route-status.rpt](../../experiments/python-gamebub-v109/native/20261108T121030620057Z/reports/route-status.rpt), SHA-256 `3ff83a70bdd50313e706fad77b93cca8cc4ac2c6190353aa7aa3161c706a6d0c`.

The actual source substitution map and all eighteen origin hashes are retained in the pinned receipt and its `source-snapshot/`; each was verified for this document. No existing methodology report was edited and no new tool run was performed.

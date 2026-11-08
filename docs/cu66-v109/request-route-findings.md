# REQUEST final route: global cancellation to quant-cell ROM enable

The fourth V109 native trial, REQUEST `20261108T122633998509Z`, is a **behaviorally qualified but physically negative experiment**. Final routed WNS is **−2.275 ns**, TNS **−10,280.347 ns**, with **15,277 setup-failing endpoints**. Worst hold is +0.105 ns and pulse width +3.750 ns, with zero hold/pulse failures. All routable nets are routed with zero routing errors, and reported internal clock/loop/unconstrained-endpoint checks are zero. Full-parent/OOC-boundary timing remains open. No new RTL, constraint or native run is introduced by this diagnosis.

## Qualification and regression must be separated

The exact REQUEST body (`ac7260e749ace036495a162882fdb30fdb129d2c7ddde8df67bc2a8957f8f4b1`) passed the focused request/fetch checks and the complete unchanged canonical comparison: 44 case profiles and 42 directed checks across both seeds, with exact V108 public events, cycles and canonical bytes. No functional regression is reported by those tests. That qualification does not imply improved physical timing.

| Final route | WNS | TNS | Setup-failing endpoints |
| --- | ---: | ---: | ---: |
| V108 qualified capacity + output-mask baseline | −2.020 ns | −11,717.641 ns | 16,953 |
| V109 initial fault, best V109 WNS | −1.589 ns | −8,342.999 ns | 14,204 |
| V109 FETCH | −1.635 ns | −8,267.052 ns | 13,122 |
| V109 REQUEST | −2.275 ns | −10,280.347 ns | 15,277 |

REQUEST's WNS regresses **0.255 ns against V108** and **0.686 ns against the best fault-only V109 route**; it also regresses 0.640 ns against FETCH. TNS and failing-endpoint count remain better than V108, but both regress against fault-only and FETCH. It cannot replace the best measured WNS candidate on a timing-closure claim. All four V109 routes remain negative at the unchanged 10 ns clock.

## Actual worst path and routing burden

The report Source field is `transform/fault_o_reg/C`; the data launch is its `/Q`. The endpoint is the **RAM enable pin** `producer_cell_cache_reg[0]_i_86/ENARDEN` on `RAMB36E1`, not a coefficient data D pin. Slack is −2.275 ns. Data delay is **11.748 ns = 2.192 ns logic + 9.556 ns routing (81.342%)**, across **fourteen LUT levels**: one LUT2, two LUT3, one LUT4, three LUT5 and seven LUT6.

The reported RAM-enable setup contribution is −0.443 ns, compared with the −0.205 ns FF-CE setup contribution in FETCH's worst path; the endpoint budget must therefore be retained when comparing raw data delays. The fixed-clock requirement is 10.000 ns, skew −0.049 ns and uncertainty 0.035 ns. The source is at `SLICE_X49Y122`; the RAM is at `RAMB36_X0Y8`.

| Actual routed net segment | Fanout | Delay |
| --- | ---: | ---: |
| `transform/inverse_fault` | 32 | 0.524 ns |
| `transform/base_abort` | 27 | 0.201 ns |
| parser `p_8_in` | 376 | 0.489 ns |
| ingress `state_reg[0]_0` | 268 | 0.903 ns |
| scratch `store_abort` | 6 | 0.176 ns |
| scratch `p_22_in` | 29 | 0.653 ns |
| `dbg_tile_prepare_start_INST_0_i_1_n_0` | 3 | 0.307 ns |
| `dbg_emitter_state[1]_INST_0_i_1_n_0` | 4 | 0.689 ns |
| `dbg_emitter_state[0]_INST_0_i_1_n_0` | 10 | 0.535 ns |
| scratch `child_out_valid` | 10 | 0.353 ns |
| scratch `state_reg[1]_2` | 5 | 0.523 ns |
| `expected_block[15]_i_6_n_0` | 2 | 0.323 ns |
| admission `producer_cell_cache_reg[7]_i_29` | 2 | 0.992 ns |
| mode-store `producer_cell_cache_reg[7]_i_29` | 3 | 1.534 ns |
| final `coefficients_n_484` to ENARDEN | 20 | 1.354 ns |

Both high fanout and long moderate/low-fanout segments matter. The optimized hierarchy names are mapped aliases, not a one-LUT-to-one-expression source map. In particular, `producer_cell_cache_reg[*]_i_*` is mapped RAM/ROM logic associated with the quant-cell calculation; the source does not contain a RAM primitive with that exact instance name. The actual terminal control pin is nevertheless unambiguous in the routed report.

## Causal source chain

The exact receipt's **eighteen current origins and retained source snapshots** were SHA-checked: seventeen SV bodies plus the quantization header. This trial contains the four V109 fault bodies and the V109 REQUEST ingress derived from FETCH. It retains **V108 capacity scratch**, not bank/prefetch; V107 Rice; V106 context; and V108 output-mask IDCT behind its historical v69 alias.

1. [Inverse fault production](../../fpga/experiments/cu66-v109-fault/cu66_inverse_stream_v91j.sv:921) co-registers `fault_o` with each original error next state. The raw path now launches from this real one-bit register. Repeating the original wide-status reduction cut cannot remove the remaining downstream control chain.
2. [Top cancellation](../../fpga/experiments/cu66-v109-fault/cs88_pipeline_v91k.sv:201) computes one-shot `base_abort` from inverse/reconstruction fault and acknowledgement state, plus external abort. It also preserves replacement-start priority for peer cancellation.
3. [Coefficient producer](../../fpga/experiments/cu66-v109-fault/cs88_coefficients_v91k.sv:1052) forwards abort through `local_abort`/`child_abort`; its frame, child/drain and lookup/output owner guards remain exact.
4. [Child pipeline](../../fpga/experiments/cu66-v108-capacity/br88_pipeline_v91h.sv:121) combines reset/start/abort, packet error and store error into immediate public cancellation and scratch abort. `out_valid` requires a running, nonfailed, noncancelled owner.
5. [Scratch dense publication](../../fpga/experiments/cu66-v108-capacity/packed_scratch_v91g2.sv:238) is immediately suppressed by cancel and response failure; tile ownership, sealed/error state and output mode further qualify it. This explains the mapped route through store-abort, emitter control and `child_out_valid`.
6. [Producer DISPATCH](../../fpga/experiments/cu66-v109-fault/cs88_coefficients_v91k.sv:1230) rejects wrong child epoch/block before accepting a final coefficient. On an accepted index-63 coefficient it advances the expected block; when more blocks remain it advances `tile_cursor`, updates `producer_cell_cache = quant_cell(plane, tile_cursor + 1)`, and returns to mapping. [Other owned mapping/plane transitions](../../fpga/experiments/cu66-v109-fault/cs88_coefficients_v91k.sv:1224) update the same cache using exact local state. `lookup_cell` exposes this register to the admission lookup, and the [existing ownership assertion](../../fpga/experiments/cu66-v109-fault/cs88_coefficients_v91k.sv:1250) checks its value against current plane/tile.

The causal class is therefore **registered transform fault → acknowledged global abort → scratch output publication fence → producer accepted-final-coefficient/dispatch decision → quant-cell ROM enable**. It is not launched by request-address arithmetic. Preserving the original rejection/publication/lookup contract is necessary even though the endpoint is an internal ROM enable.

## Search of all fifty final reported paths

| Path family | Count |
| --- | ---: |
| Transform fault to producer quant-cell RAM/ROM enables | 17 |
| Scratch state to ingress state/context/word/request-bound updates or counters | 13 |
| Admission tile to `active_cell` D | 17 |
| Scratch `read_segment` to scratch state D | 1 |
| Transform fault to Rice reservoir CE | 1 |
| Ingress band to context-decoder error D | 1 |

The raw source search found **zero paths launched by `fetch_index_reg` or `fetch_return_reg`** in these fifty, so the specific initial-A and initial-B launch families are absent from this limited report. It does **not** establish that every old address/bounds cone is gone or passes. In fact `prepared_request_in_bounds_reg` remains a destination on two scratch-state paths, and ingress `band_reg[0]` still launches a context-error path at −1.795 ns. The remaining scratch-bank path is −1.990 ns. These are current final observations, not counts inferred from the previous route.

## Next contract investigation, without another native trial

The surviving root issue is distributed operational control and ownership. A local **owned, unacknowledged kill predicate** is worth a source-level design/proof investigation only if it is derived from the exact original fault-next and acknowledgement-next transitions on the same edge. It must be equivalent to the existing operational cause for every reset, abort, accepted retry, sticky failure, simultaneous error and in-flight owner case. Registering already registered `fault_o` or an error status adds a cycle and breaks immediate cancellation; it is not the proposed solution. External abort and public input/output fences must remain current-cycle exact.

The scratch-state families also support investigating a redundant local **busy/quiescent decode co-registered with every original next-state assignment**, including DRAIN and last-assignment priority. This can shorten readiness/restart distribution without delaying the public busy/start-ready contract. Neither idea has been implemented or qualified by this report, and synthesis can still merge predicates or move routing pressure.

For the RAM-enable endpoint specifically, distinguish pure quant-cell calculation from the current acceptance/commit decision before changing RAM properties. An earlier private computation/shadow on an existing owned edge could be considered only with a proof that the original cache commits, lookup values, branch/failure priorities and every public cycle remain exact. Blindly enabling a ROM throughout cancel, adding `DO_REG`, retiming status or inserting an untracked elastic stage would change ownership or latency and is not a justified fix. If delayed private cleanup is required, it needs immediate public validity fencing and an explicit all-owner final-drain/start fence with a latency-aware contract.

All four allowed native trials are now terminal and negative. The measured best V109 WNS remains fault-only −1.589 ns; REQUEST is retained as a qualified negative experiment. No fifth trial, bank/REQUEST composition or fanout experiment is authorized by this diagnosis. Further native work requires a separately justified budget extension and new exact behavioral qualification for any source change.

## Pinned final evidence

- [receipt.json](../../experiments/python-gamebub-v109/native/20261108T122633998509Z/receipt.json), SHA-256 `d61f6b6ecf24ffb26c658313be5fa918c8f57e15ec54a53c1e829e4f708ed0e6`.
- [reports/route-setup-paths.rpt](../../experiments/python-gamebub-v109/native/20261108T122633998509Z/reports/route-setup-paths.rpt), SHA-256 `3f69af5853573b7fd1bdc882369375184b5c2e8110fad9e8fb7400a87b4360d4`.
- [reports/route-timing-summary.rpt](../../experiments/python-gamebub-v109/native/20261108T122633998509Z/reports/route-timing-summary.rpt), SHA-256 `7e9e7fef490678cbcecb38b6aa381f292ab2c625bf40db141ea4d5d8150392bd`.
- [reports/route-check-timing.rpt](../../experiments/python-gamebub-v109/native/20261108T122633998509Z/reports/route-check-timing.rpt), SHA-256 `5a68eb7e15cf2be5373807aa5fbde73734570283851f05346d34336d82c0eab9`.
- [reports/route-status.rpt](../../experiments/python-gamebub-v109/native/20261108T122633998509Z/reports/route-status.rpt), SHA-256 `b7d0a3fed3e04b8164998c0deb9249ffce64c66de5fabec76e13ea165528c682`.

The receipt retains the full eighteen-origin map, behavioral proof links, exact native source snapshots, settings and clock/route provenance. This supplement does not edit the frozen per-run methodology files or infer new methodology counts.

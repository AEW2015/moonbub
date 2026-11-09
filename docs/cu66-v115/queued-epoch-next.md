# Queued epoch cone: synthesis hypothesis only

The final-candidate **synthesized, unplaced** 125 MHz report has worst setup −2.160 ns from `coefficients/child/scratch/queued_epoch_reg[3]` to `coefficients/state_reg[0]/CE`: 9.874 ns data, 15 levels including three CARRY4. The corresponding 100 MHz synthesis result was reported as −0.152 ns. Neither is routed evidence, and no new source/action is selected here. Re-evaluate when actual final routed paths arrive.

The inspected report is `/home/lori/gamebub-build/cu66-v69/v115-integrated-125-20261109T035613295775Z-79cccd/results/synth-setup-paths.rpt`, SHA256 `fd12bcfa3f0d0368cd1cbaf31c63d58f51d57a93305898cd30d4437c419476ad`. Its named path passes through scratch `dbg_coef_ready` comparison logic, aliases under ingress `bank_ready`, scratch `dense_valid`, `child_out_valid`/`base_coefficient_valid`, expected-block logic and admission/state enable. These names cross hierarchy after synthesis optimization; they are not a literal module-level dependency diagram. The owner-certificate FDRE surviving synthesis is separate evidence that the earlier owner certificate was retained, not proof this new cone is closed.

## Source-level cause to verify

In the selected refined scratch body, direct uses of `queued_epoch` are:

- Registered capture of accepted `begin_epoch`.
- The combinational cancel owner selector: `cancel=reset || (abort_valid && abort_epoch==(preparing_begin ? queued_epoch : active_epoch))` (line 258).
- Registered `prepared_bad_epoch=epoch_seen && queued_epoch<=last_epoch`, consumed at BEGIN_COMMIT; the comparison result itself crosses a preparation register (lines 447, 678).
- Successful-commit assignments to `last_epoch` and `active_epoch` (line 681).
- Synthesis-off ownership/preparation assertions.

Thus the cancel owner comparison is the principal direct combinational wide-comparison hypothesis from this source register. A merged equivalent active/bank epoch register could also acquire the queued-epoch name and feed a different comparator; mapped cell input pins/fan-in are needed to exclude that. The report's first comparison has aliases `dbg_coef_ready`, consistent with scratch `coef_ready=state==INGEST&&!cancel`, but alias naming alone is not proof.

Cancellation gates scratch dense_valid. Dense output flows through `br88_pipeline_v91h` to `cs88_coefficients_v91k`, where output valid/ready require full child epoch and expected block equality (lines 1059–1060). DISPATCH explicitly faults on a foreign child epoch/block (line 1232). That produces a real upstream state/fault dependency; it must not be removed merely because ordinary generated tags match.

## Smallest semantic option to test if routing confirms cancellation

V115 already captures `active_epoch<=begin_epoch` on the original IDLE reservation edge, including invalid or subsequently aborted descriptors. On that same edge the descriptor capture stores `queued_epoch<=begin_epoch`. The selected assertion at scratch line 1010 requires `preparing_begin → active_epoch==queued_epoch` with busy and all preparation ready ports revoked.

A prospective source simplification is therefore to retain the **generic full 32-bit abort comparison** against `active_epoch` in all states, removing only the preparation selector between two equal captured owners. This is not an unconditional removal of abort qualification and is not implemented here. In the actual parent, `br88_pipeline_v91h` connects both `.abort_epoch(store_epoch)` and `.active_epoch(store_epoch)` (lines 196/198). If generic scratch compares against its active owner directly, that particular self-abort connection becomes syntactically equal and may optimize without the redundant queued-owner selector. Standalone scratch still compares its independent external abort tag and must reject every foreign tag.

This depends on the actual existing reservation contract, not an assumption that foreign inputs cannot occur. Preserve capture at E; moving active_epoch back to successful commit would break preparation cancellation. Preserve private anti-replay `last_epoch` updates only on successful commit; canceling an uncommitted reservation must not consume the epoch. Do not change any physical outstanding-response drain or publication mask.

Required proof before implementation/adoption:

1. Keep the original cancel expression as a synthesis-off reference and assert equality on every edge, including IDLE, all three pending preparation edges, invalid descriptor, error/failed/drain and immediate retry. Prove reservation establishes active==queued and no intervening permitted update can break it.
2. Run standalone scratch with independent wrong abort epochs on every pending edge and while requests/responses are outstanding; exercise neighboring, zero, wrapped and retired tags. Wrong tags must neither cancel nor retire real debt. Matching aborts must cancel on the original edge.
3. Retain real-parent tests using the actual store_epoch wiring, all original paired scratch/raw views and boundary/error cases, and same-epoch retry after uncommitted cancel versus rejection of a successfully committed replay. Do not replace real-parent wiring with a fake standalone tag.
4. Preserve every external memory response owner check, mismatch/error counter, held transfer and physical drain. No new latency or checker waiver is needed for this option if the reference equality holds; any discrepancy is a failure, not an allowed warmup.
5. Measure the actual final mapped cone and eventual routed result under a separately authorized flow. No current timing gain is claimed, and no native-budget extension follows from this hypothesis.

## If the actual cone is output owner or response qualification instead

Keep the foreign child epoch/block DISPATCH rejection and physical response comparisons. Do not transplant the owner kill certificate as a blanket “all child tags are ours” bit. A response can be foreign on the current edge regardless of internally generated request correctness.

Possible preparation must occur at a real owned boundary:

- For a held bank/output tuple, capture complete epoch/block/value/index and expected context at an existing publish/admission/queue edge, then register its match/invalid facts before downstream consumption. The fact must stay attached to the exact tuple, be revoked on owner change and be checked against the original full comparisons on every consumption. If first-appearance error latency changes, declare a new contract and retain the old checker unchanged.
- A two-entry coefficient queue can hold the full tuple and its validation flags; it cannot merely queue a value and infer owner later. It must preserve ordering, immediate public revocation, the final-input fence and credit/drain ownership. This only cuts downstream-ready dependencies if capacity is local; reset/kill paths require separate analysis.
- For external memory/reference responses, first capturing an actual response plus full tag/error/data into a bounded response slot is a different retirement protocol. The accepted request owner cannot be released before registered validation. Preserve immediate public masks and retain a drain fence until the real accepted response is disposed. This is not a same-cycle comparator deletion and needs independent stale/duplicate/error/abort tests.

The next step is reading final routed path families and mapped fan-in. No RTL, new simulation, physical flow, selected-source replacement or measured performance result was introduced by this note.

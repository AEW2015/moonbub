# Final mapped-register inspection

Read-only inspections of the exact receipt-hashed final 100/125-MHz routed
checkpoints pass. No RTL synthesis, placement, routing, clock change or
checkpoint write occurred. [Selected receipts and failed diagnostic history](../../experiments/python-gamebub-v115/final/register-inspection/results.json)
retain native DCP hashes, archived selection/source snapshots, commands,
resource samples, logs and TSVs.

Both routed netlists contain one cancellation-authorization FDRE, 32 future-
address FDREs, 32 prepared-address FDREs and one prepared-bounds FDRE. The old
private kill-owner register has zero surviving flip-flops. The queried bounds
D/CE fanin contains 720 startpoint rows, including 32 future-address startpoints
and no `fetch_index` startpoints. These are bounded mapping observations, not
an exhaustive timing census.

The two first inspection attempts stopped at my incorrect assumption that
`NAME(current_design)` equals the HDL top. The native-hashed DCP manifests name
`cs88_pipeline_v91k`; Vivado opens them under session alias `checkpoint_route`.
The corrected inspector verifies manifest Top/Part/build/product and actual
Vivado part/tool/clock, then logs the alias. Original failed receipts and exact
old input snapshots remain intact. New query snapshots are mounted read-only,
and work/cache files stay outside the repository.

The intended register cuts survive mapping. They do **not** close the complete
control paths: [final native results](native-final.md) still fail setup at both
clocks. See the [actual routed next cuts](final-routed-next.md), not the earlier
placement-only refill-queue hypothesis, for the current highest-priority paths.
